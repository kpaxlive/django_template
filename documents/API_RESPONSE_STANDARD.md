# 📊 API Response Standard

All API responses follow a standardized format for consistency.

---

## 🎯 Response Structure

### Success Response
```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "Operation successful",
  "data": {
    // Response data here
  }
}
```

### Error Response
```json
{
  "success": false,
  "code": "VALIDATION_ERROR",
  "error": "Error message",
  "errors": {
    "field_name": ["Error detail"]
  }
}
```

---

## 📋 Response Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `SUCCESS` | Operation successful | 200 |
| `CREATED` | Resource created | 201 |
| `UPDATED` | Resource updated | 200 |
| `DELETED` | Resource deleted | 200 |
| `NOT_FOUND` | Resource not found | 404 |
| `VALIDATION_ERROR` | Validation failed | 400 |
| `AUTHENTICATION_ERROR` | Auth failed | 401 |
| `PERMISSION_ERROR` | No permission | 403 |
| `CONFLICT` | Resource conflict | 409 |
| `SERVER_ERROR` | Internal error | 500 |

---

## 📱 Flutter Implementation

### 1. Response Models

```dart
// Base Response
class ApiResponse<T> {
  final bool success;
  final String code;
  final String? message;
  final String? error;
  final T? data;
  final Map<String, List<String>>? errors;
  
  ApiResponse({
    required this.success,
    required this.code,
    this.message,
    this.error,
    this.data,
    this.errors,
  });
  
  factory ApiResponse.fromJson(
    Map<String, dynamic> json,
    T Function(dynamic)? fromJsonT,
  ) {
    return ApiResponse<T>(
      success: json['success'],
      code: json['code'],
      message: json['message'],
      error: json['error'],
      data: json['data'] != null && fromJsonT != null
          ? fromJsonT(json['data'])
          : json['data'],
      errors: json['errors'] != null
          ? (json['errors'] as Map<String, dynamic>).map(
              (key, value) => MapEntry(key, List<String>.from(value)),
            )
          : null,
    );
  }
}
```

### 2. API Service

```dart
import 'package:dio/dio.dart';

class ApiService {
  final Dio dio;
  
  ApiService(this.dio);
  
  Future<ApiResponse<T>> request<T>({
    required String method,
    required String path,
    Map<String, dynamic>? data,
    Map<String, dynamic>? queryParameters,
    T Function(dynamic)? fromJson,
  }) async {
    try {
      final response = await dio.request(
        path,
        data: data,
        queryParameters: queryParameters,
        options: Options(method: method),
      );
      
      return ApiResponse<T>.fromJson(response.data, fromJson);
    } on DioException catch (e) {
      if (e.response != null) {
        return ApiResponse<T>.fromJson(e.response!.data, fromJson);
      }
      
      return ApiResponse<T>(
        success: false,
        code: 'NETWORK_ERROR',
        error: 'Network error: ${e.message}',
      );
    }
  }
}
```

### 3. Usage Example

```dart
// Register user
final response = await apiService.request<User>(
  method: 'POST',
  path: '/auth/register/',
  data: {
    'email': 'user@example.com',
    'password1': 'SecurePass123!',
    'password2': 'SecurePass123!',
  },
  fromJson: (json) => User.fromJson(json['user']),
);

if (response.success) {
  final user = response.data;
  print('User registered: ${user?.email}');
} else {
  print('Error: ${response.error}');
  
  // Show field-specific errors
  if (response.errors != null) {
    response.errors!.forEach((field, errors) {
      print('$field: ${errors.join(', ')}');
    });
  }
}
```

---

## 📝 Example Responses

### 1. Successful Registration

**Request:**
```bash
POST /api/auth/register/
{
  "email": "user@example.com",
  "password1": "SecurePass123!",
  "password2": "SecurePass123!"
}
```

**Response:**
```json
{
  "success": true,
  "code": "CREATED",
  "message": "User registered successfully.",
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "first_name": "",
      "last_name": "",
      "profile_picture_url": null,
      "bio": "",
      "auth_provider": "email",
      "date_joined": "2025-10-06T12:34:56.789Z"
    },
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**Flutter:**
```dart
final response = await apiService.request<Map<String, dynamic>>(
  method: 'POST',
  path: '/auth/register/',
  data: {
    'email': 'user@example.com',
    'password1': 'SecurePass123!',
    'password2': 'SecurePass123!',
  },
);

if (response.success) {
  final user = User.fromJson(response.data!['user']);
  final accessToken = response.data!['access'];
  final refreshToken = response.data!['refresh'];
  
  // Save tokens
  await storage.write(key: 'access_token', value: accessToken);
  await storage.write(key: 'refresh_token', value: refreshToken);
}
```

---

### 2. Validation Error

**Request:**
```bash
POST /api/auth/register/
{
  "email": "invalid-email",
  "password1": "123",
  "password2": "456"
}
```

**Response:**
```json
{
  "success": false,
  "code": "VALIDATION_ERROR",
  "error": "Validation failed",
  "errors": {
    "email": ["Enter a valid email address."],
    "password1": [
      "This password is too short. It must contain at least 8 characters.",
      "This password is too common."
    ],
    "password2": ["Passwords do not match."]
  }
}
```

**Flutter:**
```dart
if (!response.success) {
  if (response.errors != null) {
    // Show field-specific errors
    setState(() {
      emailError = response.errors!['email']?.first;
      passwordError = response.errors!['password1']?.first;
    });
  } else {
    // Show general error
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(response.error ?? 'Unknown error')),
    );
  }
}
```

---

### 3. Authentication Error

**Request:**
```bash
GET /api/auth/user/
Authorization: Bearer invalid-token
```

**Response:**
```json
{
  "success": false,
  "code": "AUTHENTICATION_ERROR",
  "error": "Given token not valid for any token type",
  "detail": "Token is invalid or expired"
}
```

**Flutter:**
```dart
dio.interceptors.add(
  InterceptorsWrapper(
    onError: (error, handler) async {
      if (error.response?.data['code'] == 'AUTHENTICATION_ERROR') {
        // Try to refresh token
        final newToken = await refreshAccessToken();
        
        if (newToken != null) {
          // Retry request
          error.requestOptions.headers['Authorization'] = 'Bearer $newToken';
          return handler.resolve(await dio.fetch(error.requestOptions));
        } else {
          // Logout user
          await logout();
        }
      }
      
      return handler.next(error);
    },
  ),
);
```

---

### 4. Chat List

**Request:**
```bash
GET /api/chat/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "Chat list retrieved successfully.",
  "data": [
    {
      "id": 1,
      "other_participant": {
        "id": 2,
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "profile_picture_url": "https://example.com/john.jpg"
      },
      "last_message": {
        "id": 10,
        "content": "Hello!",
        "created_at": "2025-10-06T12:34:56.789Z",
        "sender_id": 2
      },
      "unread_count": 3,
      "created_at": "2025-10-01T10:00:00.000Z",
      "updated_at": "2025-10-06T12:34:56.789Z"
    }
  ]
}
```

**Flutter:**
```dart
final response = await apiService.request<List<Chat>>(
  method: 'GET',
  path: '/chat/',
  fromJson: (data) => (data as List)
      .map((json) => Chat.fromJson(json))
      .toList(),
);

if (response.success && response.data != null) {
  setState(() {
    chats = response.data!;
  });
}
```

---

## 🛠️ Error Handling

### Flutter Error Handler

```dart
class ApiErrorHandler {
  static String getMessage(ApiResponse response) {
    if (response.error != null) {
      return response.error!;
    }
    
    if (response.errors != null) {
      // Get first error message
      final firstError = response.errors!.values.first;
      return firstError.first;
    }
    
    return 'Unknown error occurred';
  }
  
  static void showSnackBar(BuildContext context, ApiResponse response) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(getMessage(response)),
        backgroundColor: response.success ? Colors.green : Colors.red,
      ),
    );
  }
  
  static Map<String, String?> getFieldErrors(ApiResponse response) {
    final fieldErrors = <String, String?>{};
    
    if (response.errors != null) {
      response.errors!.forEach((field, errors) {
        fieldErrors[field] = errors.first;
      });
    }
    
    return fieldErrors;
  }
}
```

**Usage:**
```dart
final response = await apiService.request(...);

if (!response.success) {
  // Show error snackbar
  ApiErrorHandler.showSnackBar(context, response);
  
  // Or get field-specific errors
  final fieldErrors = ApiErrorHandler.getFieldErrors(response);
  setState(() {
    emailError = fieldErrors['email'];
    passwordError = fieldErrors['password1'];
  });
}
```

---

## 🎯 Best Practices

### 1. Always Check `success` Field

```dart
if (response.success) {
  // Handle success
} else {
  // Handle error
}
```

### 2. Use Generic Types

```dart
final response = await apiService.request<User>(
  fromJson: (json) => User.fromJson(json),
);
```

### 3. Handle Network Errors

```dart
try {
  final response = await apiService.request(...);
} catch (e) {
  print('Network error: $e');
}
```

### 4. Show User-Friendly Messages

```dart
final message = response.success 
    ? response.message ?? 'Success' 
    : response.error ?? 'An error occurred';

ScaffoldMessenger.of(context).showSnackBar(
  SnackBar(content: Text(message)),
);
```

---

## 📚 Summary

| Field | Type | Description |
|-------|------|-------------|
| `success` | `boolean` | Operation success status |
| `code` | `string` | Response code |
| `message` | `string` | Success message (optional) |
| `error` | `string` | Error message (optional) |
| `data` | `any` | Response data (optional) |
| `errors` | `object` | Field-specific errors (optional) |

All responses follow this format for consistency across the API.

---

For more examples, see:
- **API_FLOW.md** - API flows with examples
- **CHAT_SYSTEM.md** - Chat API responses
- **WEBSOCKET_CHAT.md** - WebSocket messages
