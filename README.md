# Django Authentication API

A complete, production-ready Django REST API authentication system with JWT tokens, Google OAuth, and Apple Sign In. Perfect template for Flutter applications and other mobile/web clients.

## Features

- ✅ Email/Password Registration & Login
- ✅ JWT Token Authentication (Access & Refresh Tokens)
- ✅ Token Refresh & Blacklisting
- ✅ Google OAuth Login
- ✅ Apple Sign In
- ✅ User Management (Get Profile, Delete Account)
- ✅ Complete Swagger/OpenAPI Documentation
- ✅ CORS Support for Mobile/Web Clients
- ✅ Clean Architecture & Best Practices
- ✅ Custom User Model with Email as Username
- ✅ **Standardized API Responses** (see `API_RESPONSE_STANDARD.md`)

## Tech Stack

- **Django 5.2.7** - Web framework
- **Django REST Framework** - API toolkit
- **Simple JWT** - JWT authentication
- **drf-spectacular** - OpenAPI 3.0 schema generation
- **django-allauth** - Social authentication
- **django-cors-headers** - CORS handling

## Quick Start

### 1. Clone and Setup Virtual Environment

```bash
cd clean_arch
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the root directory (use `.env.example` as template):

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=*

# Google OAuth (Optional)
GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret

# Apple Sign In (Optional)
APPLE_CLIENT_ID=your-apple-client-id
APPLE_TEAM_ID=your-apple-team-id
APPLE_KEY_ID=your-apple-key-id
APPLE_PRIVATE_KEY=your-apple-private-key
```

### 4. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## API Endpoints

### Authentication

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/auth/register/` | POST | Register new user | No |
| `/api/auth/login/` | POST | Login with email/password | No |
| `/api/auth/logout/` | POST | Logout (blacklist refresh token) | Yes |
| `/api/auth/token/refresh/` | POST | Refresh access token | No |

### User Management

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/auth/user/` | GET | Get current user profile | Yes |
| `/api/auth/user/delete/` | DELETE | Delete user account | Yes |

### Social Authentication

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/auth/login/google/` | POST | Login/Register with Google | No |
| `/api/auth/login/apple/` | POST | Login/Register with Apple | No |

## Usage Examples

### 1. Register

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "auth_provider": "email",
    "date_joined": "2025-10-05T12:00:00Z"
  }
}
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "auth_provider": "email",
    "date_joined": "2025-10-05T12:00:00Z"
  }
}
```

### 3. Get Current User

```bash
curl -X GET http://localhost:8000/api/auth/user/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Refresh Token

```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

### 5. Logout

```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

### 6. Google Login

```bash
curl -X POST http://localhost:8000/api/auth/login/google/ \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "GOOGLE_ACCESS_TOKEN"
  }'
```

### 7. Apple Login

```bash
curl -X POST http://localhost:8000/api/auth/login/apple/ \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "APPLE_ID_TOKEN"
  }'
```

### 8. Delete User

```bash
curl -X DELETE http://localhost:8000/api/auth/user/delete/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "confirm": true
  }'
```

## Flutter Integration

### Setup Dio Client

```dart
import 'package:dio/dio.dart';

class ApiClient {
  final Dio _dio;
  String? _accessToken;
  String? _refreshToken;

  ApiClient() : _dio = Dio(BaseOptions(
    baseUrl: 'http://localhost:8000/api',
    headers: {'Content-Type': 'application/json'},
  )) {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        if (_accessToken != null) {
          options.headers['Authorization'] = 'Bearer $_accessToken';
        }
        return handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401 && _refreshToken != null) {
          // Try to refresh token
          await _refreshAccessToken();
          return handler.resolve(await _retry(error.requestOptions));
        }
        return handler.next(error);
      },
    ));
  }

  Future<void> _refreshAccessToken() async {
    final response = await _dio.post('/auth/token/refresh/', 
      data: {'refresh': _refreshToken}
    );
    _accessToken = response.data['access'];
  }

  Future<Response> _retry(RequestOptions requestOptions) async {
    return _dio.request(
      requestOptions.path,
      data: requestOptions.data,
      queryParameters: requestOptions.queryParameters,
    );
  }

  Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String password2,
    String? firstName,
    String? lastName,
  }) async {
    final response = await _dio.post('/auth/register/', data: {
      'email': email,
      'password': password,
      'password2': password2,
      'first_name': firstName,
      'last_name': lastName,
    });
    
    _accessToken = response.data['access'];
    _refreshToken = response.data['refresh'];
    
    return response.data;
  }

  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    final response = await _dio.post('/auth/login/', data: {
      'email': email,
      'password': password,
    });
    
    _accessToken = response.data['access'];
    _refreshToken = response.data['refresh'];
    
    return response.data;
  }

  Future<void> logout() async {
    await _dio.post('/auth/logout/', data: {
      'refresh': _refreshToken,
    });
    
    _accessToken = null;
    _refreshToken = null;
  }

  Future<Map<String, dynamic>> getCurrentUser() async {
    final response = await _dio.get('/auth/user/');
    return response.data;
  }

  Future<void> deleteUser() async {
    await _dio.delete('/auth/user/delete/', data: {
      'confirm': true,
    });
    
    _accessToken = null;
    _refreshToken = null;
  }
}
```

## Social Authentication Setup

### Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs
6. Copy Client ID and Client Secret to `.env`

### Apple Sign In

1. Go to [Apple Developer Portal](https://developer.apple.com/)
2. Register your App ID
3. Enable Sign in with Apple capability
4. Create a Service ID
5. Generate a private key
6. Add credentials to `.env`

## Project Structure

```
clean_arch/
├── core/                      # Project settings
│   ├── settings.py           # Django settings with all configs
│   ├── urls.py              # Main URL configuration
│   └── wsgi.py              # WSGI configuration
├── src/
│   └── accounts/            # Authentication app
│       ├── models.py        # Custom User model
│       ├── serializers.py   # API serializers
│       ├── views.py         # API views
│       ├── urls.py          # App URLs
│       └── admin.py         # Admin interface
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .gitignore             # Git ignore file
└── manage.py              # Django management script
```

## Security Best Practices

- ✅ JWT tokens with expiration (60 min access, 7 days refresh)
- ✅ Refresh token rotation and blacklisting
- ✅ Password validation with Django validators
- ✅ CORS configuration for specific origins
- ✅ Environment variables for sensitive data
- ✅ HTTPS recommended for production
- ✅ Rate limiting (add in production)

## Production Deployment Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Use strong `SECRET_KEY`
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set up proper CORS origins (not `*`)
- [ ] Enable HTTPS
- [ ] Add rate limiting (e.g., django-ratelimit)
- [ ] Set up proper logging
- [ ] Configure media and static files serving
- [ ] Set up backup strategy
- [ ] Add monitoring and error tracking (e.g., Sentry)
- [ ] Review and update security settings

## Customization

### Change Token Lifetime

Edit `SIMPLE_JWT` settings in `core/settings.py`:

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),  # Change here
    'REFRESH_TOKEN_LIFETIME': timedelta(days=14),    # Change here
    # ... other settings
}
```

### Add Custom Fields to User Model

Edit `src/accounts/models.py` and add your fields to the `User` model:

```python
class User(AbstractBaseUser, PermissionsMixin):
    # ... existing fields
    phone_number = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    # ... rest of the model
```

Then run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

## Testing

Test all endpoints using Swagger UI at `http://localhost:8000/api/docs/`

## Support

For issues and questions, please check the Django and DRF documentation:
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/)

## License

This project is free to use as a template for your applications.

