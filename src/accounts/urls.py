from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    CustomTokenRefreshView,
    CurrentUserView,
    DeleteUserView,
    GoogleLoginView,
    AppleLoginView,
)

app_name = 'accounts'

urlpatterns = [
    # Email/Password Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    
    # User Management
    path('user/', CurrentUserView.as_view(), name='current_user'),
    path('user/delete/', DeleteUserView.as_view(), name='delete_user'),
    
    # Social Authentication
    path('login/google/', GoogleLoginView.as_view(), name='google_login'),
    path('login/apple/', AppleLoginView.as_view(), name='apple_login'),
]

