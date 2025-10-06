from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiResponse
import requests

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    TokenResponseSerializer,
    LogoutSerializer,
    UserSerializer,
    GoogleLoginSerializer,
    AppleLoginSerializer,
)
from .responses import success_response, error_response, ResponseCodes

User = get_user_model()


@extend_schema(
    tags=['Authentication'],
    request=RegisterSerializer,
    responses={
        201: TokenResponseSerializer,
        400: OpenApiResponse(description='Bad Request'),
    },
    auth=[],  # No authentication required
)
class RegisterView(generics.CreateAPIView):
    """
    Register a new user with email and password.
    Returns access and refresh tokens upon successful registration.
    """
    
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        response_data, http_status = success_response(
            message='User registered successfully.',
            data={
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
            },
            code=ResponseCodes.CREATED,
            http_status=status.HTTP_201_CREATED
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
    auth=[],  # No authentication required
)
class GoogleLoginView(APIView):
    """
    Login or register using Google OAuth.
    Provide the Google access token to authenticate.
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
            
            # Get or create user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': user_info.get('given_name', ''),
                    'last_name': user_info.get('family_name', ''),
                    'auth_provider': 'google',
                }
            )
            
            # If user exists but was created with email, update auth_provider
            if not created and user.auth_provider == 'email':
                user.auth_provider = 'google'
                user.save()
            
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
    auth=[],  # No authentication required
)
class AppleLoginView(APIView):
    """
    Login or register using Apple Sign In.
    Provide the Apple ID token to authenticate.
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
            
            # Get or create user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'auth_provider': 'apple',
                }
            )
            
            # If user exists but was created with email, update auth_provider
            if not created and user.auth_provider == 'email':
                user.auth_provider = 'apple'
                user.save()
            
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
