# API Response Standard

## 📋 Overview

All API endpoints follow a consistent response format for both success and error cases. This makes it easy to handle responses in the frontend application.

## ✅ Success Response Format

```json
{
  "success": true,
  "code": "SUCCESS_CODE",
  "message": "Human-readable success message",
  "data": {
    // Response data (optional)
  }
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `success` | boolean | ✅ Yes | Always `true` for successful responses |
| `code` | string | ✅ Yes | Standard success code for categorization |
| `message` | string | ✅ Yes | Human-readable success message |
| `data` | object | ❌ No | Response data (if applicable) |

### Success Codes

| Code | Description | Used In |
|------|-------------|---------|
| `SUCCESS` | General success | Login, Logout, Get User, Token Refresh |
| `CREATED` | Resource created | Register |
| `DELETED` | Resource deleted | Delete User |
| `UPDATED` | Resource updated | Update operations |

## ❌ Error Response Format

```json
{
  "success": false,
  "code": "ERROR_CODE",
  "error": "Human-readable error message"
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `success` | boolean | ✅ Yes | Always `false` for error responses |
| `code` | string | ✅ Yes | Standard error code for categorization |
| `error` | string | ✅ Yes | Human-readable error message |

### Error Codes

| Code | HTTP Status | Description | Used In |
|------|-------------|-------------|---------|
| `INVALID_CREDENTIALS` | 401 | Invalid email or password | Login |
| `ACCOUNT_DISABLED` | 401 | User account is disabled | Login |
| `TOKEN_INVALID` | 401 | Invalid or expired token | Token Refresh |
| `TOKEN_EXPIRED` | 401 | Token has expired | Token Refresh |
| `AUTHENTICATION_REQUIRED` | 401 | Authentication is required | Protected endpoints |
| `VALIDATION_ERROR` | 400 | Input validation failed | All endpoints |
| `INVALID_INPUT` | 400 | Invalid input data | All endpoints |
| `EMAIL_ALREADY_EXISTS` | 400 | Email already registered | Register |
| `GOOGLE_AUTH_FAILED` | 400 | Google OAuth failed | Google Login |
| `APPLE_AUTH_FAILED` | 400 | Apple Sign In failed | Apple Login |
| `OAUTH_ERROR` | 400 | Generic OAuth error | Social Login |
| `SERVER_ERROR` | 500 | Internal server error | Any endpoint |
| `NOT_FOUND` | 404 | Resource not found | Any endpoint |

## 📝 Examples

### Example 1: Register (Success)

**Request:**
```bash
POST /api/auth/register/
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "password2": "SecurePass123!"
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "code": "CREATED",
  "message": "User registered successfully.",
  "data": {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "first_name": "",
      "last_name": "",
      "auth_provider": "email",
      "date_joined": "2025-10-05T12:00:00Z"
    }
  }
}
```

### Example 2: Login (Error)

**Request:**
```bash
POST /api/auth/login/
{
  "email": "user@example.com",
  "password": "WrongPassword"
}
```

**Response:** `401 Unauthorized`
```json
{
  "success": false,
  "code": "INVALID_CREDENTIALS",
  "error": "Invalid email or password"
}
```

### Example 3: Login (Success)

**Request:**
```bash
POST /api/auth/login/
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "Login successful.",
  "data": {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "auth_provider": "email",
      "date_joined": "2025-10-05T12:00:00Z"
    }
  }
}
```

### Example 4: Get Current User (Success)

**Request:**
```bash
GET /api/auth/user/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:** `200 OK`
```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "User profile retrieved successfully.",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "auth_provider": "email",
    "date_joined": "2025-10-05T12:00:00Z"
  }
}
```

### Example 5: Token Refresh (Success)

**Request:**
```bash
POST /api/auth/token/refresh/
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "Token refreshed successfully.",
  "data": {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### Example 6: Token Refresh (Error)

**Request:**
```bash
POST /api/auth/token/refresh/
{
  "refresh": "invalid_or_expired_token"
}
```

**Response:** `401 Unauthorized`
```json
{
  "success": false,
  "code": "TOKEN_INVALID",
  "error": "Invalid or expired refresh token."
}
```

### Example 7: Delete User (Success)

**Request:**
```bash
DELETE /api/auth/user/delete/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:** `200 OK`
```json
{
  "success": true,
  "code": "DELETED",
  "message": "User account user@example.com has been permanently deleted."
}
```

### Example 8: Google Login (Success)

**Request:**
```bash
POST /api/auth/login/google/
{
  "access_token": "google_oauth_access_token"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "Google authentication successful.",
  "data": {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 2,
      "email": "user@gmail.com",
      "first_name": "John",
      "last_name": "Doe",
      "auth_provider": "google",
      "date_joined": "2025-10-05T12:00:00Z"
    }
  }
}
```

### Example 9: Google Login (Error)

**Request:**
```bash
POST /api/auth/login/google/
{
  "access_token": "invalid_token"
}
```

**Response:** `400 Bad Request`
```json
{
  "success": false,
  "code": "GOOGLE_AUTH_FAILED",
  "error": "Invalid Google access token"
}
```

## 🎯 Frontend Implementation

### TypeScript/JavaScript

```typescript
// Response types
interface BaseResponse {
  success: boolean;
  code: string;
}

interface SuccessResponse<T = any> extends BaseResponse {
  success: true;
  message: string;
  data?: T;
}

interface ErrorResponse extends BaseResponse {
  success: false;
  error: string;
}

type ApiResponse<T = any> = SuccessResponse<T> | ErrorResponse;

// Helper function
function handleApiResponse<T>(response: ApiResponse<T>) {
  if (response.success) {
    console.log('Success:', response.message);
    return response.data;
  } else {
    console.error('Error:', response.error, 'Code:', response.code);
    throw new Error(response.error);
  }
}

// Usage example
async function login(email: string, password: string) {
  const response = await fetch('/api/auth/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  const data: ApiResponse = await response.json();
  
  if (data.success) {
    localStorage.setItem('access_token', data.data.access);
    localStorage.setItem('refresh_token', data.data.refresh);
    return data.data.user;
  } else {
    switch (data.code) {
      case 'INVALID_CREDENTIALS':
        alert('Invalid email or password');
        break;
      case 'ACCOUNT_DISABLED':
        alert('Your account has been disabled');
        break;
      default:
        alert(data.error);
    }
    throw new Error(data.error);
  }
}
```

### Flutter/Dart

```dart
class ApiResponse<T> {
  final bool success;
  final String code;
  final String? message;
  final String? error;
  final T? data;

  ApiResponse({
    required this.success,
    required this.code,
    this.message,
    this.error,
    this.data,
  });

  factory ApiResponse.fromJson(
    Map<String, dynamic> json,
    T Function(dynamic)? fromJsonData,
  ) {
    return ApiResponse(
      success: json['success'],
      code: json['code'],
      message: json['message'],
      error: json['error'],
      data: json['data'] != null && fromJsonData != null
          ? fromJsonData(json['data'])
          : null,
    );
  }

  bool get isSuccess => success;
  bool get isError => !success;
}

// Usage example
Future<User> login(String email, String password) async {
  final response = await dio.post(
    '/api/auth/login/',
    data: {'email': email, 'password': password},
  );

  final apiResponse = ApiResponse<Map<String, dynamic>>.fromJson(
    response.data,
    (data) => data as Map<String, dynamic>,
  );

  if (apiResponse.isSuccess) {
    await storage.write(key: 'access_token', value: apiResponse.data!['access']);
    await storage.write(key: 'refresh_token', value: apiResponse.data!['refresh']);
    return User.fromJson(apiResponse.data!['user']);
  } else {
    switch (apiResponse.code) {
      case 'INVALID_CREDENTIALS':
        throw Exception('Invalid email or password');
      case 'ACCOUNT_DISABLED':
        throw Exception('Your account has been disabled');
      default:
        throw Exception(apiResponse.error);
    }
  }
}
```

## 🔑 Benefits

1. **Consistency**: All responses follow the same structure
2. **Easy Error Handling**: Frontend can check `success` field
3. **Categorized Errors**: Error codes allow specific handling
4. **Type Safety**: Easy to type in TypeScript/Dart
5. **Debugging**: Clear error messages and codes
6. **Internationalization**: Error codes can be mapped to translations

## 📚 Complete Endpoint Response Map

| Endpoint | Success Code | Possible Error Codes |
|----------|--------------|---------------------|
| `POST /register/` | `CREATED` | `EMAIL_ALREADY_EXISTS`, `VALIDATION_ERROR` |
| `POST /login/` | `SUCCESS` | `INVALID_CREDENTIALS`, `ACCOUNT_DISABLED` |
| `POST /logout/` | `SUCCESS` | `TOKEN_INVALID`, `AUTHENTICATION_REQUIRED` |
| `POST /token/refresh/` | `SUCCESS` | `TOKEN_INVALID`, `TOKEN_EXPIRED` |
| `GET /user/` | `SUCCESS` | `AUTHENTICATION_REQUIRED` |
| `DELETE /user/delete/` | `DELETED` | `AUTHENTICATION_REQUIRED` |
| `POST /login/google/` | `SUCCESS` | `GOOGLE_AUTH_FAILED`, `OAUTH_ERROR` |
| `POST /login/apple/` | `SUCCESS` | `APPLE_AUTH_FAILED`, `OAUTH_ERROR` |

---

**Last Updated:** October 5, 2025
**Version:** 1.0.0

