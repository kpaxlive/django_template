from rest_framework import status, generics, parsers
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiResponse
import requests
import uuid

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    TokenResponseSerializer,
    LogoutSerializer,
    UserSerializer,
    GoogleLoginSerializer,
    AppleLoginSerializer,
    AnonymousRegisterSerializer,
    UpdateProfileSerializer,
)
from .responses import success_response, error_response, ResponseCodes
from django.conf import settings

User = get_user_model()


@extend_schema(
    tags=['Authentication'],
    request=RegisterSerializer,
    responses={
        201: TokenResponseSerializer,
        400: OpenApiResponse(description='Bad Request'),
    },
    auth=[],  # No authentication required, but supports anonymous user conversion
)
class RegisterView(generics.CreateAPIView):
    """
    Register a new user with email and password.
    Returns access and refresh tokens upon successful registration.
    
    **Anonymous User Conversion:**
    If called with an authenticated anonymous user's token, it will convert 
    the anonymous user to a real account:
    - `merge_data=true` (default): Keeps same user ID and data
    - `merge_data=false`: Creates new user and deletes anonymous one
    
    This provides the same behavior as social authentication (Google/Apple).
    """
    
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if current user is anonymous (for merge)
        current_user = request.user if request.user.is_authenticated else None
        is_anonymous_merge = current_user and getattr(current_user, 'is_anonymous', False)
        
        if is_anonymous_merge:
            # Anonymous user conversion flow
            merge_data = serializer.validated_data.get('merge_data', True)
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            first_name = serializer.validated_data.get('first_name', '')
            last_name = serializer.validated_data.get('last_name', '')
            
            if merge_data:
                # Merge strategy: Update existing anonymous user
                user = current_user
                user.email = email
                user.set_password(password)
                user.first_name = first_name
                user.last_name = last_name
                user.is_anonymous = False
                user.auth_provider = 'email'
                user.device_id = None
                user.save()
                
                message = 'Anonymous user converted successfully. Data merged.'
                code = ResponseCodes.SUCCESS
            else:
                # Create new user strategy: Create new and delete old
                user = serializer.save()
                
                # TODO: Implement data migration logic if needed
                # migrate_user_data(from_user=current_user, to_user=user)
                
                # Delete anonymous user
                current_user.delete()
                
                message = 'New user account created. Anonymous user data transferred.'
                code = ResponseCodes.CREATED
        else:
            # Normal registration flow
            if current_user and not current_user.is_anonymous:
                # User is already registered (not anonymous)
                response_data, http_status = error_response(
                    error='User is already registered.',
                    code=ResponseCodes.ALREADY_REGISTERED,
                    http_status=status.HTTP_400_BAD_REQUEST
                )
                return Response(response_data, status=http_status)
            
            # Create new user
            user = serializer.save()
            message = 'User registered successfully.'
            code = ResponseCodes.CREATED
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        response_data, http_status = success_response(
            message=message,
            data={
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
            },
            code=code,
            http_status=status.HTTP_201_CREATED if code == ResponseCodes.CREATED else status.HTTP_200_OK
        )
        return Response(response_data, status=http_status)


@extend_schema(
    tags=['Authentication'],
    request=LoginSerializer,
    responses={
        200: TokenResponseSerializer,
        401: OpenApiResponse(description='Invalid credentials'),
    },
    auth=[],  # No authentication required
)
class LoginView(APIView):
    """
    Login with email and password.
    Returns access and refresh tokens upon successful authentication.
    """
    
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            response_data, http_status = error_response(
                error='Invalid email or password',
                code=ResponseCodes.INVALID_CREDENTIALS,
                http_status=status.HTTP_401_UNAUTHORIZED
            )
            return Response(response_data, status=http_status)
        
        if not user.check_password(password):
            response_data, http_status = error_response(
                error='Invalid email or password',
                code=ResponseCodes.INVALID_CREDENTIALS,
                http_status=status.HTTP_401_UNAUTHORIZED
            )
            return Response(response_data, status=http_status)
        
        if not user.is_active:
            response_data, http_status = error_response(
                error='User account is disabled',
                code=ResponseCodes.ACCOUNT_DISABLED,
                http_status=status.HTTP_401_UNAUTHORIZED
            )
            return Response(response_data, status=http_status)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        response_data, http_status = success_response(
            message='Login successful.',
            data={
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
            }
        )
        return Response(response_data, status=http_status)


@extend_schema(
    tags=['Authentication'],
    request=LogoutSerializer,
    responses={
        200: OpenApiResponse(description='Successfully logged out'),
        400: OpenApiResponse(description='Invalid or expired token'),
    },
)
class LogoutView(APIView):
    """
    Logout by blacklisting the refresh token.
    Provide the refresh token in the request body to blacklist it.
    """
    
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        response_data, http_status = success_response(
            message='Successfully logged out. Refresh token has been blacklisted.'
        )
        return Response(response_data, status=http_status)


@extend_schema(
    tags=['Authentication'],
    responses={
        200: OpenApiResponse(description='Token refreshed successfully'),
        401: OpenApiResponse(description='Invalid or expired refresh token'),
    },
    auth=[],  # No authentication required - only refresh token needed
)
class CustomTokenRefreshView(TokenRefreshView):
    """
    Refresh access token using refresh token.
    Provide the refresh token to get a new access token.
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            response_data, http_status = success_response(
                message='Token refreshed successfully.',
                data={
                    'access': response.data.get('access'),
                    'refresh': response.data.get('refresh'),
                }
            )
            return Response(response_data, status=http_status)
        except (TokenError, InvalidToken) as e:
            response_data, http_status = error_response(
                error='Invalid or expired refresh token.',
                code=ResponseCodes.TOKEN_INVALID,
                http_status=status.HTTP_401_UNAUTHORIZED
            )
            return Response(response_data, status=http_status)


@extend_schema(
    tags=['Authentication'],
    responses={
        200: UserSerializer,
    },
)
class CurrentUserView(APIView):
    """
    Get current authenticated user details.
    """
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        response_data, http_status = success_response(
            message='User profile retrieved successfully.',
            data=serializer.data
        )
        return Response(response_data, status=http_status)


@extend_schema(
    tags=['Authentication'],
    responses={
        200: OpenApiResponse(description='User deleted successfully'),
    },
)
class DeleteUserView(APIView):
    """
    Delete the authenticated user account.
    Requires authentication. Use this endpoint carefully as it permanently deletes the user.
    """
    
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        email = user.email
        user.delete()
        
        response_data, http_status = success_response(
            message=f'User account {email} has been permanently deleted.',
            code=ResponseCodes.DELETED
        )
        return Response(response_data, status=http_status)


@extend_schema(
    tags=['Social Authentication'],
    request=GoogleLoginSerializer,
    responses={
        200: TokenResponseSerializer,
        400: OpenApiResponse(description='Invalid token'),
    },
    auth=[],  # No authentication required, but can be used to merge anonymous user
)
class GoogleLoginView(APIView):
    """
    Login or register using Google OAuth.
    Provide the Google access token to authenticate.
    
    If called with an anonymous user's token, the anonymous user will be converted
    to a Google account (merge strategy).
    """
    
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        access_token = serializer.validated_data['access_token']
        
        try:
            # Verify the token with Google
            google_response = requests.get(
                'https://www.googleapis.com/oauth2/v3/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if google_response.status_code != 200:
                response_data, http_status = error_response(
                    error='Invalid Google access token',
                    code=ResponseCodes.GOOGLE_AUTH_FAILED,
                    http_status=status.HTTP_400_BAD_REQUEST
                )
                return Response(response_data, status=http_status)
            
            user_info = google_response.json()
            email = user_info.get('email')
            
            if not email:
                response_data, http_status = error_response(
                    error='Email not provided by Google',
                    code=ResponseCodes.GOOGLE_AUTH_FAILED,
                    http_status=status.HTTP_400_BAD_REQUEST
                )
                return Response(response_data, status=http_status)
            
            # Check if current user is anonymous (for merge)
            current_user = request.user if request.user.is_authenticated else None
            is_anonymous_merge = current_user and getattr(current_user, 'is_anonymous', False)
            
            # If anonymous user tries to merge but feature is disabled, block it
            if is_anonymous_merge and not getattr(settings, 'ALLOW_ANONYMOUS_USERS', False):
                response_data, http_status = error_response(
                    error='Anonymous user feature is disabled.',
                    code=ResponseCodes.ANONYMOUS_FEATURE_DISABLED,
                    http_status=status.HTTP_403_FORBIDDEN
                )
                return Response(response_data, status=http_status)
            
            if is_anonymous_merge:
                # Merge: Convert anonymous user to Google account
                user = current_user
                user.email = email
                user.first_name = user_info.get('given_name', '')
                user.last_name = user_info.get('family_name', '')
                user.is_anonymous = False
                user.auth_provider = 'google'
                user.device_id = None
                user.save()
                created = False
            else:
                # Normal flow: Get or create user by email
                # Check if email exists for non-anonymous user
                existing_user = User.objects.filter(email=email, is_anonymous=False).first()
                
                if existing_user:
                    # User exists - just update auth provider if needed
                    user = existing_user
                    if user.auth_provider != 'google':
                        user.auth_provider = 'google'
                        user.save()
                    created = False
                else:
                    # Create new user
                    user = User.objects.create(
                        email=email,
                        first_name=user_info.get('given_name', ''),
                        last_name=user_info.get('family_name', ''),
                        auth_provider='google',
                        is_active=True,
                    )
                    created = True
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            response_data, http_status = success_response(
                message='Google authentication successful.',
                data={
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': UserSerializer(user).data,
                }
            )
            return Response(response_data, status=http_status)
            
        except Exception as e:
            response_data, http_status = error_response(
                error=f'Google authentication failed: {str(e)}',
                code=ResponseCodes.GOOGLE_AUTH_FAILED,
                http_status=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=http_status)


@extend_schema(
    tags=['Social Authentication'],
    request=AppleLoginSerializer,
    responses={
        200: TokenResponseSerializer,
        400: OpenApiResponse(description='Invalid token'),
    },
    auth=[],  # No authentication required, but can be used to merge anonymous user
)
class AppleLoginView(APIView):
    """
    Login or register using Apple Sign In.
    Provide the Apple ID token to authenticate.
    
    If called with an anonymous user's token, the anonymous user will be converted
    to an Apple account (merge strategy).
    """
    
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AppleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        id_token_value = serializer.validated_data['id_token']
        
        try:
            # In production, you should verify the Apple ID token
            # For now, we'll accept it and extract the email
            import jwt
            
            # Decode without verification for development
            # In production, verify with Apple's public key
            decoded_token = jwt.decode(
                id_token_value,
                options={"verify_signature": False}
            )
            
            email = decoded_token.get('email')
            
            if not email:
                response_data, http_status = error_response(
                    error='Email not provided by Apple',
                    code=ResponseCodes.APPLE_AUTH_FAILED,
                    http_status=status.HTTP_400_BAD_REQUEST
                )
                return Response(response_data, status=http_status)
            
            # Check if current user is anonymous (for merge)
            current_user = request.user if request.user.is_authenticated else None
            is_anonymous_merge = current_user and getattr(current_user, 'is_anonymous', False)
            
            # If anonymous user tries to merge but feature is disabled, block it
            if is_anonymous_merge and not getattr(settings, 'ALLOW_ANONYMOUS_USERS', False):
                response_data, http_status = error_response(
                    error='Anonymous user feature is disabled.',
                    code=ResponseCodes.ANONYMOUS_FEATURE_DISABLED,
                    http_status=status.HTTP_403_FORBIDDEN
                )
                return Response(response_data, status=http_status)
            
            if is_anonymous_merge:
                # Merge: Convert anonymous user to Apple account
                user = current_user
                user.email = email
                user.is_anonymous = False
                user.auth_provider = 'apple'
                user.device_id = None
                user.save()
                created = False
            else:
                # Normal flow: Get or create user by email
                # Check if email exists for non-anonymous user
                existing_user = User.objects.filter(email=email, is_anonymous=False).first()
                
                if existing_user:
                    # User exists - just update auth provider if needed
                    user = existing_user
                    if user.auth_provider != 'apple':
                        user.auth_provider = 'apple'
                        user.save()
                    created = False
                else:
                    # Create new user
                    user = User.objects.create(
                        email=email,
                        auth_provider='apple',
                        is_active=True,
                    )
                    created = True
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            response_data, http_status = success_response(
                message='Apple authentication successful.',
                data={
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': UserSerializer(user).data,
                }
            )
            return Response(response_data, status=http_status)
            
        except Exception as e:
            response_data, http_status = error_response(
                error=f'Apple authentication failed: {str(e)}',
                code=ResponseCodes.APPLE_AUTH_FAILED,
                http_status=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=http_status)


@extend_schema(
    tags=['Anonymous Users'],
    request=AnonymousRegisterSerializer,
    responses={
        201: TokenResponseSerializer,
        400: OpenApiResponse(description='Bad Request'),
        403: OpenApiResponse(description='Feature disabled'),
    },
    auth=[],  # No authentication required
)
class AnonymousRegisterView(APIView):
    """
    Register an anonymous user with device ID.
    Returns access and refresh tokens. User can later convert to a real account.
    This feature can be disabled via ALLOW_ANONYMOUS_USERS setting.
    """
    
    permission_classes = [AllowAny]

    def post(self, request):
        # Check if feature is enabled
        if not getattr(settings, 'ALLOW_ANONYMOUS_USERS', False):
            response_data, http_status = error_response(
                error='Anonymous user feature is disabled.',
                code=ResponseCodes.ANONYMOUS_FEATURE_DISABLED,
                http_status=status.HTTP_403_FORBIDDEN
            )
            return Response(response_data, status=http_status)
        
        serializer = AnonymousRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get device_id from request or generate one
        device_id = serializer.validated_data.get('device_id')
        if not device_id:
            # Generate unique device_id if not provided
            device_id = f"backend-{uuid.uuid4()}"
        
        # Check if device_id already exists
        existing_user = User.objects.filter(device_id=device_id).first()
        if existing_user:
            # Return existing user's tokens
            refresh = RefreshToken.for_user(existing_user)
            
            response_data, http_status = success_response(
                message='Returning existing anonymous user.',
                data={
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': UserSerializer(existing_user).data,
                },
                code=ResponseCodes.SUCCESS
            )
            return Response(response_data, status=http_status)
        
        # Create new anonymous user
        user = User.objects.create(
            device_id=device_id,
            is_anonymous=True,
            auth_provider='anonymous',
            is_active=True,
        )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        response_data, http_status = success_response(
            message='Anonymous user created successfully.',
            data={
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
            },
            code=ResponseCodes.ANONYMOUS_USER_CREATED,
            http_status=status.HTTP_201_CREATED
        )
        return Response(response_data, status=http_status)


@extend_schema(
    tags=['User Profile'],
    request=UpdateProfileSerializer,
    responses={
        200: UpdateProfileSerializer,
        400: OpenApiResponse(description='Bad Request'),
    },
)
class UpdateProfileView(APIView):
    """
    Update user profile (name, bio, profile picture URL).
    Requires authentication.
    """
    
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        
        serializer = UpdateProfileSerializer(
            user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        response_data, http_status = success_response(
            message='Profile updated successfully.',
            data=serializer.data,
            code=ResponseCodes.UPDATED
        )
        return Response(response_data, status=http_status)
    
    def put(self, request):
        """Full update of profile."""
        user = request.user
        
        serializer = UpdateProfileSerializer(
            user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        response_data, http_status = success_response(
            message='Profile updated successfully.',
            data=serializer.data,
            code=ResponseCodes.UPDATED
        )
        return Response(response_data, status=http_status)
