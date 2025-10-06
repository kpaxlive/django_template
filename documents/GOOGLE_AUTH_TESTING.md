# 🔐 Google OAuth Integration

Complete guide for Google Sign In implementation.

---

## 📋 Overview

Google OAuth allows users to sign in with their Google account. The flow:
1. User signs in with Google (Flutter)
2. Get Google access token
3. Send token to backend
4. Backend creates/authenticates user
5. Return JWT tokens

---

## ⚙️ Setup

### 1. Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable **Google+ API**
4. Create OAuth 2.0 credentials:
   - **Android**: Package name + SHA-1 fingerprint
   - **iOS**: Bundle ID + App Store ID
   - **Web**: Authorized redirect URIs

### 2. Configure Backend

Edit `.env`:
```env
GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret
```

---

## 📱 Flutter Implementation

### 1. Add Dependencies

```yaml
# pubspec.yaml
dependencies:
  google_sign_in: ^6.2.1
  dio: ^5.4.0
  flutter_secure_storage: ^9.0.0
```

### 2. Configure Google Sign In

#### Android (`android/app/build.gradle`)
```gradle
dependencies {
    implementation 'com.google.android.gms:play-services-auth:20.7.0'
}
```

#### iOS (`ios/Runner/Info.plist`)
```xml
<key>CFBundleURLTypes</key>
<array>
    <dict>
        <key>CFBundleTypeRole</key>
        <string>Editor</string>
        <key>CFBundleURLSchemes</key>
        <array>
            <string>com.googleusercontent.apps.YOUR-CLIENT-ID</string>
        </array>
    </dict>
</array>
```

### 3. Implement Sign In

```dart
import 'package:google_sign_in/google_sign_in.dart';
import 'package:dio/dio.dart';

class GoogleAuthService {
  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: ['email', 'profile'],
  );
  
  final Dio dio = Dio(BaseOptions(
    baseUrl: 'http://localhost:8000/api',
  ));
  
  Future<Map<String, dynamic>?> signInWithGoogle() async {
    try {
      // 1. Sign in with Google
      final GoogleSignInAccount? account = await _googleSignIn.signIn();
      
      if (account == null) {
        print('User cancelled sign in');
        return null;
      }
      
      // 2. Get authentication tokens
      final GoogleSignInAuthentication auth = await account.authentication;
      final String? accessToken = auth.accessToken;
      
      if (accessToken == null) {
        print('Failed to get access token');
        return null;
      }
      
      // 3. Send to backend
      final response = await dio.post('/auth/google/', data: {
        'access_token': accessToken,
      });
      
      if (response.data['success']) {
        return response.data['data'];
      }
      
      return null;
    } catch (e) {
      print('Google sign in error: $e');
      return null;
    }
  }
  
  Future<void> signOut() async {
    await _googleSignIn.signOut();
  }
}
```

### 4. Usage in Login Screen

```dart
class LoginScreen extends StatelessWidget {
  final GoogleAuthService _googleAuth = GoogleAuthService();
  final FlutterSecureStorage storage = FlutterSecureStorage();
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Google Sign In Button
            ElevatedButton.icon(
              onPressed: () => _handleGoogleSignIn(context),
              icon: Icon(Icons.g_mobiledata),
              label: Text('Sign in with Google'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red,
                minimumSize: Size(250, 50),
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Future<void> _handleGoogleSignIn(BuildContext context) async {
    // Show loading
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => Center(child: CircularProgressIndicator()),
    );
    
    final result = await _googleAuth.signInWithGoogle();
    
    Navigator.pop(context); // Close loading
    
    if (result != null) {
      // Save tokens
      await storage.write(key: 'access_token', value: result['access']);
      await storage.write(key: 'refresh_token', value: result['refresh']);
      
      // Navigate to home
      Navigator.pushReplacementNamed(context, '/home');
    } else {
      // Show error
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Sign in failed')),
      );
    }
  }
}
```

---

## 🔄 API Flow

### 1. New User (First Time)

```dart
// Flutter sends
final response = await dio.post('/auth/google/', data: {
  'access_token': '<google_access_token>',
});

// Backend response
{
  "success": true,
  "code": "CREATED",
  "message": "User logged in with Google successfully.",
  "data": {
    "user": {
      "id": 10,
      "email": "user@gmail.com",
      "first_name": "John",
      "last_name": "Doe",
      "auth_provider": "google",
      "is_anonymous": false
    },
    "access": "eyJ0eXAiOiJKV1Qi...",
    "refresh": "eyJ0eXAiOiJKV1Qi..."
  }
}
```

### 2. Existing User (Login)

Same request, backend recognizes email and returns existing user.

### 3. Anonymous User Conversion

```dart
// Include anonymous token in header
final anonToken = await storage.read(key: 'access_token');

final response = await dio.post(
  '/auth/google/',
  data: {
    'access_token': '<google_access_token>',
  },
  options: Options(headers: {
    'Authorization': 'Bearer $anonToken',
  }),
);

// Backend merges anonymous data with Google account
```

---

## 🧪 Testing

### Option 1: Using Flutter App

Run your Flutter app and click "Sign in with Google" button.

### Option 2: Get Token Manually (for API testing)

1. Go to [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)
2. Select **Google OAuth2 API v2**
3. Check:
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`
4. Click **Authorize APIs**
5. Login with Google
6. Click **Exchange authorization code for tokens**
7. Copy **Access Token**

Then test with curl:
```bash
curl -X POST http://localhost:8000/api/auth/google/ \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "ya29.a0AfB_..."
  }'
```

### Option 3: Swagger UI

1. Go to http://localhost:8000/api/docs/
2. Find `POST /api/auth/google/`
3. Click **Try it out**
4. Paste Google access token
5. Execute

---

## 🎨 Custom Google Button

```dart
class GoogleSignInButton extends StatelessWidget {
  final VoidCallback onPressed;
  
  const GoogleSignInButton({required this.onPressed});
  
  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onPressed,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        height: 50,
        padding: EdgeInsets.symmetric(horizontal: 16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: Colors.grey[300]!),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Image.asset(
              'assets/google_logo.png',
              height: 24,
              width: 24,
            ),
            SizedBox(width: 12),
            Text(
              'Sign in with Google',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w500,
                color: Colors.grey[700],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

---

## ⚠️ Error Handling

### Flutter

```dart
Future<void> signInWithGoogle() async {
  try {
    final account = await _googleSignIn.signIn();
    
    if (account == null) {
      // User cancelled
      return;
    }
    
    final auth = await account.authentication;
    final accessToken = auth.accessToken;
    
    if (accessToken == null) {
      throw Exception('Failed to get access token');
    }
    
    final response = await dio.post('/auth/google/', data: {
      'access_token': accessToken,
    });
    
    if (!response.data['success']) {
      throw Exception(response.data['error']);
    }
    
    // Success - save tokens
    await _saveTokens(response.data['data']);
    
  } on PlatformException catch (e) {
    print('Google Sign In Platform Error: ${e.message}');
    _showError('Failed to sign in with Google');
  } on DioException catch (e) {
    print('API Error: ${e.response?.data}');
    _showError('Server error. Please try again.');
  } catch (e) {
    print('Unknown error: $e');
    _showError('Something went wrong');
  }
}
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `PlatformException` | Google Play Services missing | Update Google Play Services |
| `sign_in_failed` | Invalid configuration | Check client ID in console |
| `network_error` | No internet | Check connection |
| `Invalid credentials` | Wrong client secret | Check `.env` file |

---

## 🔒 Security Best Practices

### 1. Never Store Google Access Token
```dart
// ❌ DON'T
await storage.write(key: 'google_token', value: googleAccessToken);

// ✅ DO - Store JWT tokens
await storage.write(key: 'access_token', value: jwtAccessToken);
await storage.write(key: 'refresh_token', value: jwtRefreshToken);
```

### 2. Use HTTPS in Production
```dart
// Production
final dio = Dio(BaseOptions(
  baseUrl: 'https://yourdomain.com/api',
));
```

### 3. Validate on Backend
Backend automatically validates Google token with Google servers before creating user.

---

## 🎯 Complete Example

```dart
// services/google_auth_service.dart
import 'package:google_sign_in/google_sign_in.dart';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class GoogleAuthService {
  final GoogleSignIn _googleSignIn = GoogleSignIn(scopes: ['email', 'profile']);
  final Dio dio = Dio(BaseOptions(baseUrl: 'http://localhost:8000/api'));
  final FlutterSecureStorage storage = FlutterSecureStorage();
  
  Future<bool> signInWithGoogle() async {
    try {
      // 1. Sign in with Google
      final account = await _googleSignIn.signIn();
      if (account == null) return false;
      
      // 2. Get Google access token
      final auth = await account.authentication;
      final googleToken = auth.accessToken;
      if (googleToken == null) return false;
      
      // 3. Check if user is anonymous (for merging)
      final anonToken = await storage.read(key: 'access_token');
      
      // 4. Send to backend
      final response = await dio.post(
        '/auth/google/',
        data: {'access_token': googleToken},
        options: Options(headers: {
          if (anonToken != null) 'Authorization': 'Bearer $anonToken',
        }),
      );
      
      if (response.data['success']) {
        // 5. Save JWT tokens
        await storage.write(
          key: 'access_token',
          value: response.data['data']['access'],
        );
        await storage.write(
          key: 'refresh_token',
          value: response.data['data']['refresh'],
        );
        await storage.delete(key: 'is_anonymous');
        
        return true;
      }
      
      return false;
    } catch (e) {
      print('Error: $e');
      return false;
    }
  }
  
  Future<void> signOut() async {
    await _googleSignIn.signOut();
    await storage.deleteAll();
  }
}

// screens/login_screen.dart
class LoginScreen extends StatelessWidget {
  final GoogleAuthService _authService = GoogleAuthService();
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: GoogleSignInButton(
          onPressed: () => _handleSignIn(context),
        ),
      ),
    );
  }
  
  Future<void> _handleSignIn(BuildContext context) async {
    final success = await _authService.signInWithGoogle();
    
    if (success) {
      Navigator.pushReplacementNamed(context, '/home');
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Sign in failed')),
      );
    }
  }
}
```

---

## 📚 Resources

- [Google Sign In Plugin](https://pub.dev/packages/google_sign_in)
- [Google Cloud Console](https://console.cloud.google.com/)
- [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)

---

For more details, see:
- **API_FLOW.md** - Complete authentication flows
- **ANONYMOUS_USER_SCENARIOS.md** - Anonymous user conversion
- **README.md** - Main documentation
