# ⚡ Quick Start Guide

Get up and running in 5 minutes!

---

## 📋 Prerequisites

- Python 3.10+
- Redis (for WebSocket)
- Virtual environment tool

---

## 🚀 Setup Steps

### 1. Clone & Create Virtual Environment
```bash
cd clean_arch
python -m venv venv

# Activate
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
```

Edit `.env`:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=*

# Feature Flags
ENABLE_AUTH_SYSTEM=True
ALLOW_ANONYMOUS_USERS=True
ENABLE_CHAT_SYSTEM=True
```

### 4. Run Migrations
```bash
python manage.py migrate
```

### 5. Create Superuser
```bash
python manage.py createsuperuser
```

### 6. Start Redis (for Chat/WebSocket)
```bash
# macOS
brew services start redis

# Linux
sudo service redis-server start

# Or manually
redis-server
```

### 7. Run Server
```bash
python manage.py runserver
```

---

## ✅ Verify Installation

### 1. Swagger UI
Open: http://localhost:8000/api/docs/

You should see the API documentation.

### 2. Admin Panel
Open: http://localhost:8000/admin/

Login with your superuser credentials.

### 3. Test Register API
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password1": "TestPass123!",
    "password2": "TestPass123!"
  }'
```

Expected response:
```json
{
  "success": true,
  "code": "CREATED",
  "message": "User registered successfully.",
  "data": {
    "user": {
      "id": 1,
      "email": "test@example.com",
      ...
    },
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

---

## 🧪 Test WebSocket

### Using Browser Console
```javascript
const token = 'YOUR_ACCESS_TOKEN';
const ws = new WebSocket(`ws://localhost:8000/ws/chat/1/?token=${token}`);

ws.onopen = () => {
  console.log('Connected!');
  ws.send(JSON.stringify({
    type: 'chat_message',
    message: 'Hello WebSocket!',
    message_type: 'text'
  }));
};

ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};
```

---

## 📱 Flutter Integration

### 1. Add Dependencies
```yaml
dependencies:
  dio: ^5.4.0
  flutter_secure_storage: ^9.0.0
  web_socket_channel: ^2.4.0
```

### 2. Configure Base URL
```dart
class ApiConfig {
  static const String baseUrl = 'http://localhost:8000/api';
  static const String wsUrl = 'ws://localhost:8000';
}
```

### 3. Test Register
```dart
import 'package:dio/dio.dart';

final dio = Dio(BaseOptions(baseUrl: ApiConfig.baseUrl));

Future<void> testRegister() async {
  final response = await dio.post('/auth/register/', data: {
    'email': 'flutter@example.com',
    'password1': 'FlutterPass123!',
    'password2': 'FlutterPass123!',
  });
  
  print('Success: ${response.data['success']}');
  print('Access Token: ${response.data['data']['access']}');
}
```

---

## 🎯 Next Steps

1. **Authentication**: Read `API_FLOW.md` for auth flows
2. **API Responses**: Check `API_RESPONSE_STANDARD.md` for response format
3. **Anonymous Users**: See `ANONYMOUS_USER_SCENARIOS.md` if enabled
4. **Chat REST API**: Read `CHAT_SYSTEM.md` for chat endpoints
5. **WebSocket Chat**: Check `WEBSOCKET_CHAT.md` for real-time messaging
6. **OAuth**: See `GOOGLE_AUTH_TESTING.md` for social login

---

## 🛠️ Troubleshooting

### Redis Connection Error
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG
```

### Port Already in Use
```bash
# Use different port
python manage.py runserver 8001
```

### Migration Errors
```bash
# Reset migrations (development only!)
python manage.py migrate --fake-initial
```

### WebSocket Connection Failed
- Verify Redis is running
- Check JWT token is valid
- Ensure user is part of the chat

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| **README.md** | Main documentation |
| **API_FLOW.md** | API architecture & flows |
| **API_RESPONSE_STANDARD.md** | Response format |
| **ANONYMOUS_USER_SCENARIOS.md** | Anonymous users |
| **GOOGLE_AUTH_TESTING.md** | OAuth testing |
| **CHAT_SYSTEM.md** | Chat REST API |
| **WEBSOCKET_CHAT.md** | WebSocket chat |

---

## 🎉 You're Ready!

Your Django Clean Architecture Template is now running!

- **Swagger**: http://localhost:8000/api/docs/
- **Admin**: http://localhost:8000/admin/
- **WebSocket**: ws://localhost:8000/ws/chat/{id}/?token=xxx

Happy Coding! 🚀
