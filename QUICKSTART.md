# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Setup (First Time Only)

```bash
# Option A: Use the setup script
./setup.sh

# Option B: Manual setup
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

### Step 2: Run Server

```bash
python manage.py runserver
```

### Step 3: Access Swagger Documentation

Open your browser: **http://localhost:8000/api/docs/**

---

## 📝 Test the API

### Option 1: Use Swagger UI (Recommended)
1. Go to http://localhost:8000/api/docs/
2. Try each endpoint directly in the browser
3. Copy the access token and use "Authorize" button

### Option 2: Use Test Script
```bash
python test_api.py
```

### Option 3: Use cURL

#### Register
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

#### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

---

## 🔑 Important URLs

| URL | Description |
|-----|-------------|
| http://localhost:8000/api/docs/ | **Swagger UI (Start Here!)** |
| http://localhost:8000/api/redoc/ | ReDoc Documentation |
| http://localhost:8000/admin/ | Django Admin Panel |
| http://localhost:8000/api/schema/ | OpenAPI Schema (JSON) |

---

## 🎯 Available Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login
- `POST /api/auth/logout/` - Logout (requires auth)
- `POST /api/auth/token/refresh/` - Refresh token

### User Management
- `GET /api/auth/user/` - Get profile (requires auth)
- `DELETE /api/auth/user/delete/` - Delete account (requires auth)

### Social Authentication
- `POST /api/auth/login/google/` - Google OAuth
- `POST /api/auth/login/apple/` - Apple Sign In

---

## 🔐 Using Authentication

After login/register, you'll receive tokens:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {...}
}
```

**For protected endpoints, add header:**
```
Authorization: Bearer <your-access-token>
```

**In Swagger:**
1. Click "Authorize" button (🔒 icon at top)
2. Enter: `Bearer <your-access-token>`
3. Click "Authorize"
4. Now you can test protected endpoints!

---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Required for production
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com

# Optional: Google OAuth
GOOGLE_OAUTH2_CLIENT_ID=your-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-secret

# Optional: Apple Sign In
APPLE_CLIENT_ID=your-id
APPLE_TEAM_ID=your-team-id
APPLE_KEY_ID=your-key-id
APPLE_PRIVATE_KEY=your-key
```

---

## 🐛 Troubleshooting

### Server won't start?
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process
kill -9 <PID>
```

### Import errors?
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Database issues?
```bash
# Reset database (⚠️ deletes all data)
rm db.sqlite3
python manage.py migrate
```

### "Token is invalid" error?
- Token expired (default: 60 minutes)
- Use the `/api/auth/token/refresh/` endpoint
- Or login again

---

## 📱 Flutter Integration Example

```dart
// 1. Register/Login
final response = await dio.post('/api/auth/login/', data: {
  'email': 'user@example.com',
  'password': 'SecurePass123!',
});

String accessToken = response.data['access'];
String refreshToken = response.data['refresh'];

// 2. Save tokens securely
await storage.write(key: 'access_token', value: accessToken);
await storage.write(key: 'refresh_token', value: refreshToken);

// 3. Use in requests
dio.options.headers['Authorization'] = 'Bearer $accessToken';

// 4. Get user profile
final user = await dio.get('/api/auth/user/');
```

---

## ✅ Production Checklist

Before deploying:
- [ ] Set `DEBUG=False`
- [ ] Change `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use PostgreSQL (not SQLite)
- [ ] Set up HTTPS
- [ ] Configure CORS properly
- [ ] Add rate limiting
- [ ] Set up monitoring
- [ ] Configure logging
- [ ] Test all endpoints

---

## 💡 Tips

1. **Always test in Swagger first** - It's the easiest way to understand the API
2. **Save your tokens** - You'll need them for authenticated requests
3. **Use .env file** - Never commit secrets to git
4. **Read the main README.md** - It has more detailed information
5. **Check Django admin** - Great for managing users (http://localhost:8000/admin/)

---

## 🆘 Need Help?

- Check the main **README.md** for detailed documentation
- Test endpoints in **Swagger UI** (http://localhost:8000/api/docs/)
- Review **Django REST Framework** docs
- Check **Simple JWT** documentation

---

## 🎉 You're Ready!

Your authentication API is now running and ready to use with your Flutter app!

**Start testing:** http://localhost:8000/api/docs/

