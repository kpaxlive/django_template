# 👤 Anonymous Users Guide

Allow users to use your app without registration, then convert to real accounts.

---

## 📋 Overview

Anonymous users can:
- Use app features without registration
- Save data temporarily
- Convert to real user (email or social) later
- Preserve data after conversion

**Feature is OPTIONAL** - controlled by `.env`

---

## ⚙️ Configuration

```env
# .env
ALLOW_ANONYMOUS_USERS=True        # Enable/disable feature
ANONYMOUS_USER_RETENTION_DAYS=30  # Auto-delete after N days
```

If `ALLOW_ANONYMOUS_USERS=False`:
- `/api/auth/anonymous/register/` → 403 Forbidden
- `/api/auth/anonymous/convert/` → 403 Forbidden
- Social auth merge with anon token → 403 Forbidden

---

## 🔄 Workflows

### 1. Anonymous User Registration

**Flutter:**
```dart
Future<void> registerAnonymous() async {
  final response = await dio.post('/auth/anonymous/register/');
  
  if (response.data['success']) {
    final accessToken = response.data['data']['access'];
    final refreshToken = response.data['data']['refresh'];
    
    await storage.write(key: 'access_token', value: accessToken);
    await storage.write(key: 'refresh_token', value: refreshToken);
    await storage.write(key: 'is_anonymous', value: 'true');
    
    // User can now use app
    Navigator.pushReplacementNamed(context, '/home');
  }
}
```

**API:**
```bash
POST /api/auth/anonymous/register/
Content-Type: application/json

{
  "device_id": "optional-device-id"  # Optional
}
```

**Response:**
```json
{
  "success": true,
  "code": "CREATED",
  "message": "Anonymous user created successfully.",
  "data": {
    "user": {
      "id": 5,
      "email": null,
      "is_anonymous": true,
      "auth_provider": "anonymous"
    },
    "access": "eyJ0eXAiOiJKV1Qi...",
    "refresh": "eyJ0eXAiOiJKV1Qi..."
  }
}
```

---

### 2. Convert Anonymous to Email User

**Flutter:**
```dart
Future<void> convertToEmailUser({
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
    // Get new tokens
    final newAccessToken = response.data['data']['access'];
    final newRefreshToken = response.data['data']['refresh'];
    
    await storage.write(key: 'access_token', value: newAccessToken);
    await storage.write(key: 'refresh_token', value: newRefreshToken);
    await storage.write(key: 'is_anonymous', value: 'false');
    
    // User is now a real user with same data
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Account created successfully!')),
    );
  }
}
```

**API:**
```bash
POST /api/auth/anonymous/convert/
Authorization: Bearer <anonymous_access_token>
Content-Type: application/json

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
  "code": "SUCCESS",
  "message": "Anonymous user converted successfully.",
  "data": {
    "user": {
      "id": 5,
      "email": "user@example.com",
      "is_anonymous": false,
      "auth_provider": "email"
    },
    "access": "eyJ0eXAiOiJKV1Qi...",
    "refresh": "eyJ0eXAiOiJKV1Qi..."
  }
}
```

---

### 3. Convert Anonymous to Google User

**Step 1: Login with Google (Flutter)**
```dart
import 'package:google_sign_in/google_sign_in.dart';

Future<void> convertToGoogleUser() async {
  // Get Google token
  final GoogleSignIn googleSignIn = GoogleSignIn(
    scopes: ['email', 'profile'],
  );
  
  final account = await googleSignIn.signIn();
  if (account == null) return;
  
  final authentication = await account.authentication;
  final googleAccessToken = authentication.accessToken;
  
  // Get anonymous token
  final anonAccessToken = await storage.read(key: 'access_token');
  
  // Send to backend
  final response = await dio.post(
    '/auth/google/',
    data: {
      'access_token': googleAccessToken,
    },
    options: Options(headers: {
      'Authorization': 'Bearer $anonAccessToken', // Include anon token
    }),
  );
  
  if (response.data['success']) {
    // Save new tokens
    final newAccessToken = response.data['data']['access'];
    final newRefreshToken = response.data['data']['refresh'];
    
    await storage.write(key: 'access_token', value: newAccessToken);
    await storage.write(key: 'refresh_token', value: newRefreshToken);
    await storage.write(key: 'is_anonymous', value: 'false');
  }
}
```

**API:**
```bash
POST /api/auth/google/
Authorization: Bearer <anonymous_access_token>  # Optional - for merge
Content-Type: application/json

{
  "access_token": "<google_access_token>"
}
```

---

## 📱 Flutter Complete Flow

### Main App Entry

```dart
class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: FutureBuilder<String?>(
        future: _checkAuthStatus(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return LoadingScreen();
          }
          
          if (snapshot.data != null) {
            // Has access token - go to home
            return HomeScreen();
          }
          
          // No token - show welcome
          return WelcomeScreen();
        },
      ),
    );
  }
  
  Future<String?> _checkAuthStatus() async {
    final storage = FlutterSecureStorage();
    return await storage.read(key: 'access_token');
  }
}
```

### Welcome Screen

```dart
class WelcomeScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('Welcome!', style: TextStyle(fontSize: 32)),
            SizedBox(height: 40),
            
            // Browse as guest (anonymous)
            ElevatedButton(
              onPressed: () => _registerAnonymous(context),
              child: Text('Browse as Guest'),
            ),
            
            SizedBox(height: 16),
            
            // Register with email
            OutlinedButton(
              onPressed: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => RegisterScreen()),
              ),
              child: Text('Create Account'),
            ),
            
            // Login
            TextButton(
              onPressed: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => LoginScreen()),
              ),
              child: Text('Login'),
            ),
          ],
        ),
      ),
    );
  }
  
  Future<void> _registerAnonymous(BuildContext context) async {
    final apiService = ApiService();
    await apiService.registerAnonymous();
    
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => HomeScreen()),
    );
  }
}
```

### Home Screen (with conversion prompt)

```dart
class HomeScreen extends StatefulWidget {
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool isAnonymous = false;
  
  @override
  void initState() {
    super.initState();
    _checkAnonymous();
  }
  
  Future<void> _checkAnonymous() async {
    final storage = FlutterSecureStorage();
    final isAnon = await storage.read(key: 'is_anonymous');
    setState(() {
      isAnonymous = isAnon == 'true';
    });
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Home'),
        actions: [
          if (isAnonymous)
            TextButton(
              onPressed: _showConversionDialog,
              child: Text('Create Account', style: TextStyle(color: Colors.white)),
            ),
        ],
      ),
      body: Column(
        children: [
          if (isAnonymous)
            Card(
              margin: EdgeInsets.all(16),
              color: Colors.orange[100],
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Column(
                  children: [
                    Text('You\'re browsing as a guest'),
                    SizedBox(height: 8),
                    Text('Create an account to save your data permanently'),
                    SizedBox(height: 8),
                    ElevatedButton(
                      onPressed: _showConversionDialog,
                      child: Text('Create Account'),
                    ),
                  ],
                ),
              ),
            ),
          
          // Your app content
          Expanded(child: AppContent()),
        ],
      ),
    );
  }
  
  void _showConversionDialog() {
    showModalBottomSheet(
      context: context,
      builder: (context) => ConversionSheet(),
    );
  }
}
```

### Conversion Sheet

```dart
class ConversionSheet extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text('Create Your Account', style: TextStyle(fontSize: 24)),
          SizedBox(height: 8),
          Text('Save your data permanently'),
          SizedBox(height: 24),
          
          // Email registration
          ElevatedButton.icon(
            onPressed: () {
              Navigator.pop(context);
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => ConvertEmailScreen()),
              );
            },
            icon: Icon(Icons.email),
            label: Text('Continue with Email'),
          ),
          
          SizedBox(height: 12),
          
          // Google sign in
          ElevatedButton.icon(
            onPressed: () => _convertToGoogle(context),
            icon: Icon(Icons.g_mobiledata),
            label: Text('Continue with Google'),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
          ),
        ],
      ),
    );
  }
  
  Future<void> _convertToGoogle(BuildContext context) async {
    final apiService = ApiService();
    await apiService.convertToGoogleUser();
    
    Navigator.pop(context);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Account created!')),
    );
  }
}
```

### Convert Email Screen

```dart
class ConvertEmailScreen extends StatefulWidget {
  @override
  State<ConvertEmailScreen> createState() => _ConvertEmailScreenState();
}

class _ConvertEmailScreenState extends State<ConvertEmailScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Create Account')),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _emailController,
              decoration: InputDecoration(labelText: 'Email'),
              keyboardType: TextInputType.emailAddress,
            ),
            SizedBox(height: 16),
            TextField(
              controller: _passwordController,
              decoration: InputDecoration(labelText: 'Password'),
              obscureText: true,
            ),
            SizedBox(height: 24),
            ElevatedButton(
              onPressed: _convert,
              child: Text('Create Account'),
            ),
          ],
        ),
      ),
    );
  }
  
  Future<void> _convert() async {
    final apiService = ApiService();
    await apiService.convertToEmailUser(
      email: _emailController.text,
      password: _passwordController.text,
    );
    
    Navigator.pop(context);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Account created!')),
    );
  }
}
```

---

## 🎯 Key Points

### 1. Device ID (Optional)
```dart
// You can provide device ID or let backend generate it
import 'package:device_info_plus/device_info_plus.dart';

Future<String> getDeviceId() async {
  final deviceInfo = DeviceInfoPlugin();
  if (Platform.isAndroid) {
    final androidInfo = await deviceInfo.androidInfo;
    return androidInfo.id;
  } else {
    final iosInfo = await deviceInfo.iosInfo;
    return iosInfo.identifierForVendor ?? '';
  }
}
```

### 2. Data Persistence
- Anonymous user data is **automatically preserved** after conversion
- Same user ID is kept
- All chat messages, preferences, etc. remain

### 3. Email Conflict
- If email already exists: Error returned
- User must use different email or login

### 4. Token Management
```dart
// Always update tokens after conversion
await storage.write(key: 'access_token', value: newAccessToken);
await storage.write(key: 'refresh_token', value: newRefreshToken);
await storage.write(key: 'is_anonymous', value: 'false');
```

---

## ❌ Error Scenarios

### 1. Feature Disabled
```json
{
  "success": false,
  "code": "FORBIDDEN",
  "error": "Anonymous users feature is disabled"
}
```

### 2. Email Already Exists
```json
{
  "success": false,
  "code": "VALIDATION_ERROR",
  "error": "Email already in use",
  "errors": {
    "email": ["User with this email already exists."]
  }
}
```

### 3. Already Converted
```json
{
  "success": false,
  "code": "VALIDATION_ERROR",
  "error": "User is not anonymous"
}
```

---

## 📚 Summary

| Action | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| Register Anonymous | `POST /auth/anonymous/register/` | No | Create anonymous user |
| Convert to Email | `POST /auth/anonymous/convert/` | Yes (Anon) | Convert to email user |
| Convert to Google | `POST /auth/google/` | Yes (Anon) | Convert to Google user |
| Convert to Apple | `POST /auth/apple/` | Yes (Anon) | Convert to Apple user |

**All data is preserved during conversion!**

---

For more details, see:
- **API_FLOW.md** - Complete API flows
- **GOOGLE_AUTH_TESTING.md** - OAuth implementation
- **README.md** - Main documentation
