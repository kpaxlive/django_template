# 🚀 Django Clean Architecture Template

Production-ready Django REST API template with **Authentication**, **Chat System**, and **WebSocket** support. Perfect for Flutter mobile apps.

---

## ✨ Features

### 🔐 Authentication System
- Email/Password registration & login
- JWT tokens (access & refresh)
- Google OAuth & Apple Sign In
- Anonymous users (optional)
- Profile management (name, bio, profile picture URL)
- User deletion

### 💬 Chat System (Optional)
- **REST API**: Create, list, archive, delete chats
- **WebSocket**: Real-time messaging, typing indicators, read receipts
- Text, image, file messages
- Per-user message clearing
- Unread message counts

### 📊 API Standards
- Standardized responses (`success`, `code`, `message`/`error`)
- Complete Swagger documentation
- CORS enabled
- Clean architecture

### 🎛️ Feature Flags
All systems are **optional** - enable/disable via `.env`:
```env
ENABLE_AUTH_SYSTEM=True       # Authentication on/off
ALLOW_ANONYMOUS_USERS=True    # Anonymous users on/off
ENABLE_CHAT_SYSTEM=True       # Chat system on/off
```

---

## 🛠️ Tech Stack

| Package | Version | Purpose |
|---------|---------|---------|
| Django | 5.2.7 | Web framework |
| DRF | 3.15.2 | REST API |
| Simple JWT | 5.4.0 | JWT auth |
| Django Channels | 4.0.0 | WebSocket |
| drf-spectacular | 0.28.0 | Swagger docs |
| Redis | - | WebSocket channel layer |

---

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Run Migrations
```bash
python manage.py migrate
```

### 4. Create Superuser
```bash
python manage.py createsuperuser
```

### 5. Start Redis (for WebSocket)
```bash
redis-server
```

### 6. Run Server
```bash
python manage.py runserver
```

### 7. Access
- **Swagger UI**: http://localhost:8000/api/docs/
- **Admin**: http://localhost:8000/admin/
- **WebSocket**: ws://localhost:8000/ws/chat/{id}/?token=xxx

---

## 📚 Documentation

| File | Description |
|------|-------------|
| **QUICKSTART.md** | Quick setup guide |
| **API_FLOW.md** | API architecture & flows |
| **API_RESPONSE_STANDARD.md** | Response format |
| **ANONYMOUS_USER_SCENARIOS.md** | Anonymous users guide |
| **GOOGLE_AUTH_TESTING.md** | OAuth testing |
| **CHAT_SYSTEM.md** | Chat REST API |
| **WEBSOCKET_CHAT.md** | WebSocket real-time chat |

---

## 🔌 API Endpoints

### Authentication
```
POST   /api/auth/register/              # Register with email/password
POST   /api/auth/login/                 # Login
POST   /api/auth/logout/                # Logout
POST   /api/auth/token/refresh/         # Refresh token
GET    /api/auth/user/                  # Get current user
DELETE /api/auth/user/delete/           # Delete account
PATCH  /api/auth/user/update/           # Update profile
POST   /api/auth/google/                # Google OAuth
POST   /api/auth/apple/                 # Apple Sign In
POST   /api/auth/anonymous/register/    # Anonymous user
POST   /api/auth/anonymous/convert/     # Convert anonymous to real user
```

### Chat (REST)
```
GET    /api/chat/                       # List chats
POST   /api/chat/create/                # Create chat
GET    /api/chat/{id}/                  # Chat detail
DELETE /api/chat/{id}/                  # Delete chat
POST   /api/chat/{id}/archive/          # Archive chat
DELETE /api/chat/{id}/archive/          # Unarchive chat
GET    /api/chat/{id}/messages/         # Get messages
POST   /api/chat/{id}/messages/send/    # Send message
POST   /api/chat/{id}/messages/read/    # Mark as read
POST   /api/chat/{id}/messages/clear/   # Clear messages
DELETE /api/chat/messages/{id}/delete/  # Delete message
```

### Chat (WebSocket)
```
ws://localhost:8000/ws/chat/{id}/?token=<jwt_access_token>
```

---

## 📱 Flutter Integration

### 1. Install Packages
```yaml
dependencies:
  dio: ^5.4.0
  flutter_secure_storage: ^9.0.0
  web_socket_channel: ^2.4.0
```

### 2. API Service Example
```dart
import 'package:dio/dio.dart';

class ApiService {
  final Dio dio = Dio(BaseOptions(
    baseUrl: 'http://localhost:8000/api',
  ));
  
  // Register
  Future<Map<String, dynamic>> register({
    required String email,
    required String password,
  }) async {
    final response = await dio.post('/auth/register/', data: {
      'email': email,
      'password1': password,
      'password2': password,
    });
    return response.data;
  }
  
  // Login
  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    final response = await dio.post('/auth/login/', data: {
      'email': email,
      'password': password,
    });
    return response.data;
  }
  
  // Get current user
  Future<Map<String, dynamic>> getCurrentUser(String accessToken) async {
    final response = await dio.get(
      '/auth/user/',
      options: Options(headers: {
        'Authorization': 'Bearer $accessToken',
      }),
    );
    return response.data;
  }
}
```

### 3. WebSocket Example
```dart
import 'package:web_socket_channel/web_socket_channel.dart';

class ChatWebSocket {
  late WebSocketChannel channel;
  
  void connect(int chatId, String accessToken) {
    channel = WebSocketChannel.connect(
      Uri.parse('ws://localhost:8000/ws/chat/$chatId/?token=$accessToken'),
    );
    
    channel.stream.listen((message) {
      print('Received: $message');
    });
  }
  
  void sendMessage(String message) {
    channel.sink.add(jsonEncode({
      'type': 'chat_message',
      'message': message,
      'message_type': 'text',
    }));
  }
  
  void dispose() {
    channel.sink.close();
  }
}
```

---

## 🎯 Response Format

All API responses follow this format:

### Success Response
```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "Operation successful",
  "data": {
    "id": 1,
    "email": "user@example.com"
  }
}
```

### Error Response
```json
{
  "success": false,
  "code": "VALIDATION_ERROR",
  "error": "Invalid email format",
  "errors": {
    "email": ["Enter a valid email address."]
  }
}
```

---

## 🔒 Authentication Flow

### 1. Register or Login
```bash
POST /api/auth/register/
{
  "email": "user@example.com",
  "password1": "SecurePass123!",
  "password2": "SecurePass123!"
}

Response:
{
  "success": true,
  "data": {
    "user": {...},
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

### 2. Use Access Token
```bash
GET /api/auth/user/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### 3. Refresh Token
```bash
POST /api/auth/token/refresh/
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## 🧪 Testing

### Swagger UI
1. Open http://localhost:8000/api/docs/
2. Test all endpoints interactively
3. Authorize with JWT token

### WebSocket Testing
Use Postman or browser console:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat/1/?token=YOUR_TOKEN');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
ws.send(JSON.stringify({
  type: 'chat_message',
  message: 'Hello!',
  message_type: 'text'
}));
```

---

## 📂 Project Structure

```
clean_arch/
├── core/                      # Django project settings
│   ├── settings.py           # Main config
│   ├── urls.py               # URL routing
│   ├── asgi.py               # ASGI + WebSocket
│   └── wsgi.py               # WSGI
├── src/
│   ├── accounts/             # Authentication app
│   │   ├── models.py         # Custom User model
│   │   ├── serializers.py    # API serializers
│   │   ├── views.py          # API views
│   │   └── responses.py      # Response helpers
│   └── chat/                 # Chat system app
│       ├── models.py         # Chat & Message models
│       ├── serializers.py    # API serializers
│       ├── views.py          # REST API views
│       ├── consumers.py      # WebSocket consumer
│       ├── middleware.py     # JWT auth middleware
│       └── routing.py        # WebSocket routing
├── requirements.txt          # Dependencies
├── .env.example              # Environment template
└── *.md                      # Documentation
```

---

## 🚀 Production Deployment

### 1. Environment Variables
```env
DEBUG=False
SECRET_KEY=<strong-random-string>
ALLOWED_HOSTS=yourdomain.com
```

### 2. Database
```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

### 3. Redis (for WebSocket)
```bash
# Install and start Redis
redis-server
```

### 4. Run with Daphne
```bash
daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

### 5. Nginx Configuration
```nginx
location /ws/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

---

## 🤝 Contributing

This is a template project. Feel free to:
- Fork and customize for your needs
- Report issues
- Suggest improvements

---

## 📄 License

MIT License - Use freely for personal and commercial projects.

---

## 🆘 Support

- **Swagger**: http://localhost:8000/api/docs/
- **Documentation**: See `.md` files in project root
- **Issues**: Report bugs or request features

---

**Built with ❤️ for Flutter developers**
