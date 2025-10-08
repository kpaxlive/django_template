from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'auth_provider', 
            'date_joined', 'profile_picture_url', 'bio'
        ]
        read_only_fields = ['id', 'date_joined', 'auth_provider']


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration.
    
    Supports anonymous user conversion:
    - If authenticated as anonymous user, converts to real account (merge by default)
    - If merge_data=True, keeps same user ID and data
    - If merge_data=False, creates new user and deletes anonymous one
    """
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label='Confirm Password'
    )
    merge_data = serializers.BooleanField(
        required=False,
        default=True,
        help_text='If true and user is anonymous, keeps same user ID and data. If false, creates new user.'
    )
    
    class Meta:
        model = User
        fields = ['email', 'password', 'password2', 'first_name', 'last_name', 'merge_data']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate(self, attrs):
        """Validate that passwords match and email is unique."""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        
        # Check if email already exists (for non-anonymous users)
        email = attrs['email']
        if User.objects.filter(email=email, is_anonymous=False).exists():
            raise serializers.ValidationError({
                "email": "User with this email already exists."
            })
        
        return attrs

    def create(self, validated_data):
        """Create and return a new user."""
        validated_data.pop('password2')
        validated_data.pop('merge_data', None)  # Remove merge_data from validated_data
        
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Custom login serializer with email instead of username."""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )


class TokenResponseSerializer(serializers.Serializer):
    """Serializer for token response."""
    
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user = UserSerializer(read_only=True)


class LogoutSerializer(serializers.Serializer):
    """Serializer for logout."""
    
    refresh = serializers.CharField(required=True)
    
    def validate(self, attrs):
        """Validate the refresh token."""
        self.token = attrs['refresh']
        return attrs
    
    def save(self, **kwargs):
        """Blacklist the refresh token."""
        try:
            RefreshToken(self.token).blacklist()
        except Exception as e:
            raise serializers.ValidationError({
                'refresh': 'Invalid or expired token.'
            })


class GoogleLoginSerializer(serializers.Serializer):
    """Serializer for Google OAuth login."""
    
    access_token = serializers.CharField(required=True)
    
    def validate_access_token(self, value):
        """Validate the Google access token."""
        if not value:
            raise serializers.ValidationError('Access token is required.')
        return value


class AppleLoginSerializer(serializers.Serializer):
    """Serializer for Apple Sign In."""
    
    id_token = serializers.CharField(required=True)
    
    def validate_id_token(self, value):
        """Validate the Apple ID token."""
        if not value:
            raise serializers.ValidationError('ID token is required.')
        return value


class DeleteUserSerializer(serializers.Serializer):
    """Serializer for user deletion confirmation."""
    
    confirm = serializers.BooleanField(required=True)
    
    def validate_confirm(self, value):
        """Validate confirmation."""
        if not value:
            raise serializers.ValidationError('You must confirm deletion.')
        return value


class AnonymousRegisterSerializer(serializers.Serializer):
    """Serializer for anonymous user registration."""
    
    device_id = serializers.CharField(required=False, max_length=255, allow_blank=True)
    
    def validate_device_id(self, value):
        """Validate device_id if provided."""
        if value and len(value) < 10:
            raise serializers.ValidationError('Device ID must be at least 10 characters.')
        return value


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'bio', 'profile_picture_url']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'bio': {'required': False, 'max_length': 200},
            'profile_picture_url': {'required': False},
        }
    
    def validate_bio(self, value):
        """Validate bio length."""
        if value and len(value) > 200:
            raise serializers.ValidationError('Bio cannot exceed 200 characters.')
        return value

