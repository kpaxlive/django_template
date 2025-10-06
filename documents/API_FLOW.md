# 🔄 API Flow & Architecture

Complete guide for implementing authentication and chat flows in Flutter.

---

## 📊 Architecture Overview

```
┌─────────────────────┐
│   Flutter App       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Django REST API    │
│  (JWT + WebSocket)  │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌────────┐   ┌────────┐
│  Auth  │   │  Chat  │
└────────┘   └────────┘
```

---

## 🔐 Authentication Flows

### 1. Email Registration Flow

```dart
// Flutter Implementation
Future<void> register() async {
  final response = await dio.post('/auth/register/', data: {
    'email': 'user@example.com',
    'password1': 'SecurePass123!',
    'password2': 'SecurePass123!',
  });
  
  if (response.data['success']) {
    final accessToken = response.data['data']['access'];
    final refreshToken = response.data['data']['refresh'];
    
    // Save tokens securely
    await storage.write(key: 'access_token', value: accessToken);
    await storage.write(key: 'refresh_token', value: refreshToken);
    
    // Navigate to home
    Navigator.pushReplacementNamed(context, '/home');
  }
}
```

**API Request:**
```bash
POST /api/auth/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "password1": "SecurePass123!",
  "password2": "SecurePass123!"
}
```

**API Response:**
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
      "bio": ""
    },
    "access": "eyJ0eXAiOiJKV1Qi...",
    "refresh": "eyJ0eXAiOiJKV1Qi..."
  }
}
```

---

### 2. Login Flow

```dart
Future<void> login() async {
  final response = await dio.post('/auth/login/', data: {
    'email': 'user@example.com',
    'password': 'SecurePass123!',
  });
  
  if (response.data['success']) {
    final accessToken = response.data['data']['access'];
    final refreshToken = response.data['data']['refresh'];
    
    await storage.write(key: 'access_token', value: accessToken);
    await storage.write(key: 'refresh_token', value: refreshToken);
    
    Navigator.pushReplacementNamed(context, '/home');
  }
}
```

---

### 3. Token Refresh Flow

```dart
Future<String?> refreshAccessToken() async {
  final refreshToken = await storage.read(key: 'refresh_token');
  
  if (refreshToken == null) return null;
  
  try {
    final response = await dio.post('/auth/token/refresh/', data: {
      'refresh': refreshToken,
    });
    
    if (response.data['success']) {
      final newAccessToken = response.data['data']['access'];
      await storage.write(key: 'access_token', value: newAccessToken);
      return newAccessToken;
    }
  } catch (e) {
    // Refresh token expired, logout user
    await logout();
  }
  
  return null;
}
```

**Dio Interceptor (Auto Refresh):**
```dart
dio.interceptors.add(
  InterceptorsWrapper(
    onError: (error, handler) async {
      if (error.response?.statusCode == 401) {
        final newToken = await refreshAccessToken();
        
        if (newToken != null) {
          // Retry original request
          error.requestOptions.headers['Authorization'] = 'Bearer $newToken';
          return handler.resolve(await dio.fetch(error.requestOptions));
        }
      }
      
      return handler.next(error);
    },
  ),
);
```

---

### 4. Anonymous User Flow

**Register Anonymous:**
```dart
Future<void> registerAnonymous() async {
  // Optional: Generate device ID
  final deviceId = await getDeviceId(); // Or let backend generate
  
  final response = await dio.post('/auth/anonymous/register/', data: {
    'device_id': deviceId, // Optional
  });
  
  if (response.data['success']) {
    final accessToken = response.data['data']['access'];
    final refreshToken = response.data['data']['refresh'];
    
    await storage.write(key: 'access_token', value: accessToken);
    await storage.write(key: 'refresh_token', value: refreshToken);
    await storage.write(key: 'is_anonymous', value: 'true');
  }
}
```

**Convert to Real User:**
```dart
Future<void> convertAnonymous({
  required String email,
  required String password,
}) async {
  final accessToken = await storage.read(key: 'access_token');
  
  final response = await dio.post(
    '/auth/anonymous/convert/',
    data: {
      'email': email,
      'password1': password,
      'password2': password,
    },
    options: Options(headers: {
      'Authorization': 'Bearer $accessToken',
    }),
  );
  
  if (response.data['success']) {
    await storage.write(key: 'is_anonymous', value: 'false');
    
    // New tokens after conversion
    final newAccessToken = response.data['data']['access'];
    final newRefreshToken = response.data['data']['refresh'];
    
    await storage.write(key: 'access_token', value: newAccessToken);
    await storage.write(key: 'refresh_token', value: newRefreshToken);
  }
}
```

---

### 5. Google OAuth Flow

**Step 1: Get Google Access Token (Flutter)**
```dart
// Using google_sign_in package
import 'package:google_sign_in/google_sign_in.dart';

Future<void> signInWithGoogle() async {
  final GoogleSignIn googleSignIn = GoogleSignIn(
    scopes: ['email', 'profile'],
  );
  
  final account = await googleSignIn.signIn();
  if (account == null) return;
  
  final authentication = await account.authentication;
  final googleAccessToken = authentication.accessToken;
  
  // Send to backend
  await loginWithGoogle(googleAccessToken!);
}
```

**Step 2: Send to Backend**
```dart
Future<void> loginWithGoogle(String googleAccessToken) async {
  final response = await dio.post('/auth/google/', data: {
    'access_token': googleAccessToken,
  });
  
  if (response.data['success']) {
    final accessToken = response.data['data']['access'];
    final refreshToken = response.data['data']['refresh'];
    
    await storage.write(key: 'access_token', value: accessToken);
    await storage.write(key: 'refresh_token', value: refreshToken);
    
    Navigator.pushReplacementNamed(context, '/home');
  }
}
```

---

### 6. Logout Flow

```dart
Future<void> logout() async {
  final refreshToken = await storage.read(key: 'refresh_token');
  
  try {
    await dio.post('/auth/logout/', data: {
      'refresh': refreshToken,
    });
  } catch (e) {
    // Continue logout even if API fails
  }
  
  // Clear local storage
  await storage.deleteAll();
  
  // Navigate to login
  Navigator.pushReplacementNamed(context, '/login');
}
```

---

## 💬 Chat Flows

### 1. Create Chat

```dart
Future<int?> createChat(int otherUserId) async {
  final accessToken = await storage.read(key: 'access_token');
  
  final response = await dio.post(
    '/chat/create/',
    data: {
      'other_user_id': otherUserId,
    },
    options: Options(headers: {
      'Authorization': 'Bearer $accessToken',
    }),
  );
  
  if (response.data['success']) {
    return response.data['data']['id'];
  }
  
  return null;
}
```

---

### 2. Get Chat List

```dart
Future<List<Chat>> getChatList() async {
  final accessToken = await storage.read(key: 'access_token');
  
  final response = await dio.get(
    '/chat/',
    options: Options(headers: {
      'Authorization': 'Bearer $accessToken',
    }),
  );
  
  if (response.data['success']) {
    final chatList = (response.data['data'] as List)
        .map((json) => Chat.fromJson(json))
        .toList();
    return chatList;
  }
  
  return [];
}

// Chat Model
class Chat {
  final int id;
  final User otherParticipant;
  final String? lastMessage;
  final DateTime? lastMessageTime;
  final int unreadCount;
  
  Chat({
    required this.id,
    required this.otherParticipant,
    this.lastMessage,
    this.lastMessageTime,
    required this.unreadCount,
  });
  
  factory Chat.fromJson(Map<String, dynamic> json) {
    return Chat(
      id: json['id'],
      otherParticipant: User.fromJson(json['other_participant']),
      lastMessage: json['last_message']?['content'],
      lastMessageTime: json['last_message']?['created_at'] != null
          ? DateTime.parse(json['last_message']['created_at'])
          : null,
      unreadCount: json['unread_count'],
    );
  }
}
```

---

### 3. Send Message (REST)

```dart
Future<void> sendMessage({
  required int chatId,
  required String message,
}) async {
  final accessToken = await storage.read(key: 'access_token');
  
  final response = await dio.post(
    '/chat/$chatId/messages/send/',
    data: {
      'message_type': 'text',
      'content': message,
    },
    options: Options(headers: {
      'Authorization': 'Bearer $accessToken',
    }),
  );
  
  if (response.data['success']) {
    print('Message sent!');
  }
}
```

---

### 4. WebSocket Real-time Chat

```dart
import 'package:web_socket_channel/web_socket_channel.dart';

class ChatWebSocket {
  WebSocketChannel? _channel;
  final Function(Message) onMessageReceived;
  
  ChatWebSocket({required this.onMessageReceived});
  
  void connect(int chatId, String accessToken) {
    final uri = Uri.parse(
      'ws://localhost:8000/ws/chat/$chatId/?token=$accessToken',
    );
    
    _channel = WebSocketChannel.connect(uri);
    
    _channel!.stream.listen(
      (data) {
        final json = jsonDecode(data);
        
        if (json['type'] == 'chat_message') {
          final message = Message.fromJson(json['message']);
          onMessageReceived(message);
        } else if (json['type'] == 'typing_indicator') {
          // Handle typing indicator
          print('${json['user_name']} is typing...');
        }
      },
      onError: (error) {
        print('WebSocket error: $error');
      },
    );
  }
  
  void sendMessage(String message) {
    _channel?.sink.add(jsonEncode({
      'type': 'chat_message',
      'message': message,
      'message_type': 'text',
    }));
  }
  
  void sendTypingIndicator(bool isTyping) {
    _channel?.sink.add(jsonEncode({
      'type': 'typing',
      'is_typing': isTyping,
    }));
  }
  
  void dispose() {
    _channel?.sink.close();
  }
}
```

**Usage:**
```dart
class ChatScreen extends StatefulWidget {
  final int chatId;
  
  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  late ChatWebSocket _ws;
  final List<Message> _messages = [];
  
  @override
  void initState() {
    super.initState();
    
    _ws = ChatWebSocket(
      onMessageReceived: (message) {
        setState(() {
          _messages.add(message);
        });
      },
    );
    
    _loadAccessToken().then((token) {
      _ws.connect(widget.chatId, token);
    });
  }
  
  @override
  void dispose() {
    _ws.dispose();
    super.dispose();
  }
  
  void _sendMessage(String text) {
    _ws.sendMessage(text);
  }
}
```

---

## 🎯 Common Patterns

### 1. Authenticated Request Helper

```dart
class ApiService {
  final Dio dio;
  final FlutterSecureStorage storage;
  
  ApiService(this.dio, this.storage);
  
  Future<Response> authenticatedGet(String path) async {
    final token = await storage.read(key: 'access_token');
    
    return dio.get(
      path,
      options: Options(headers: {
        'Authorization': 'Bearer $token',
      }),
    );
  }
  
  Future<Response> authenticatedPost(String path, dynamic data) async {
    final token = await storage.read(key: 'access_token');
    
    return dio.post(
      path,
      data: data,
      options: Options(headers: {
        'Authorization': 'Bearer $token',
      }),
    );
  }
}
```

### 2. Response Handler

```dart
T? handleResponse<T>(
  Response response,
  T Function(dynamic) fromJson,
) {
  if (response.data['success']) {
    return fromJson(response.data['data']);
  } else {
    throw ApiException(
      response.data['code'],
      response.data['error'],
    );
  }
}

// Usage
final user = handleResponse(response, (data) => User.fromJson(data));
```

---

## 📚 Summary

| Flow | Endpoint | Method | Auth Required |
|------|----------|--------|---------------|
| Register | `/auth/register/` | POST | No |
| Login | `/auth/login/` | POST | No |
| Logout | `/auth/logout/` | POST | Yes |
| Refresh Token | `/auth/token/refresh/` | POST | No |
| Get User | `/auth/user/` | GET | Yes |
| Google OAuth | `/auth/google/` | POST | No |
| Anonymous Register | `/auth/anonymous/register/` | POST | No |
| Convert Anonymous | `/auth/anonymous/convert/` | POST | Yes (Anon) |
| Chat List | `/chat/` | GET | Yes |
| Create Chat | `/chat/create/` | POST | Yes |
| Send Message | `/chat/{id}/messages/send/` | POST | Yes |
| WebSocket | `ws://...` | WS | Yes (token param) |

---

For more details, see:
- **API_RESPONSE_STANDARD.md** - Response format
- **ANONYMOUS_USER_SCENARIOS.md** - Anonymous user flows
- **CHAT_SYSTEM.md** - Chat REST API
- **WEBSOCKET_CHAT.md** - WebSocket implementation
