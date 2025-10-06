# API Flow'ları - Detaylı Kullanım Kılavuzu

## 📋 İçindekiler

1. [Anonymous User Flow](#1-anonymous-user-flow)
2. [Anonymous → Email Conversion Flow](#2-anonymous--email-conversion-flow)
3. [Anonymous → Google Conversion Flow](#3-anonymous--google-conversion-flow)
4. [Anonymous → Apple Conversion Flow](#4-anonymous--apple-conversion-flow)
5. [Direct Email Registration Flow](#5-direct-email-registration-flow)
6. [Direct Social Login Flow](#6-direct-social-login-flow)
7. [Logout Flow](#7-logout-flow)
8. [ALLOW_ANONYMOUS_USERS = False Durumu](#8-allow_anonymous_users--false-durumu)

---

## ⚙️ Settings Kontrolü

```python
# .env
ALLOW_ANONYMOUS_USERS=True  # veya False
```

**Önemli:**
- `ALLOW_ANONYMOUS_USERS=False` ise:
  - ❌ `/api/auth/anonymous/register/` → 403 Forbidden
  - ❌ `/api/auth/anonymous/convert/` → 403 Forbidden
  - ❌ Social auth merge (anon token ile) → 403 Forbidden
  - ✅ Normal email/social registration → Çalışır

---

## 1️⃣ Anonymous User Flow

### 🎯 Ne Zaman Kullanılır?
- App açıldığında kullanıcı giriş yapmamışsa
- Kullanıcı "Misafir olarak devam et" seçerse
- Kullanıcıya kayıt olmadan app'i deneme fırsatı vermek için

### 📊 Flow Diagram
```
APP AÇILDI
    ↓
Token var mı?
    ├─ HAYIR → Anonymous Register
    └─ EVET → Get Current User
```

### 🔧 API Calls

#### Option A: Frontend Device ID ile
```http
POST /api/auth/anonymous/register/
Content-Type: application/json

{
  "device_id": "your-device-id-min-10-chars"
}
```

**Response (201):**
```json
{
  "success": true,
  "code": "ANONYMOUS_USER_CREATED",
  "message": "Anonymous user created successfully.",
  "data": {
    "access": "eyJhbG...",
    "refresh": "eyJhbG...",
    "user": {
      "id": 1,
      "email": null,
      "is_anonymous": true,
      "auth_provider": "anonymous"
    }
  }
}
```

#### Option B: Backend UUID ile (Device ID yok)
```http
POST /api/auth/anonymous/register/
Content-Type: application/json

{}
```

**Response (201):** Aynı format, backend otomatik UUID üretir.

### 💻 Flutter Implementation

```dart
class AuthService {
  Future<User> initializeUser() async {
    // Check if token exists
    final accessToken = await storage.read(key: 'access_token');
    
    if (accessToken != null) {
      try {
        // Try to get current user
        return await getCurrentUser();
      } catch (e) {
        // Token expired or invalid
        await storage.deleteAll();
      }
    }
    
    // No valid token → Create anonymous user
    return await registerAnonymous();
  }
  
  Future<User> registerAnonymous() async {
    try {
      // Try to get device ID
      final deviceId = await getDeviceId();
      
      final response = await dio.post(
        '/api/auth/anonymous/register/',
        data: {'device_id': deviceId},
      );
      
      // Save tokens
      await storage.write(
        key: 'access_token',
        value: response.data['data']['access'],
      );
      await storage.write(
        key: 'refresh_token',
        value: response.data['data']['refresh'],
      );
      await storage.write(key: 'is_anonymous', value: 'true');
      
      return User.fromJson(response.data['data']['user']);
    } catch (e) {
      // Fallback: Let backend generate UUID
      final response = await dio.post(
        '/api/auth/anonymous/register/',
        data: {},
      );
      
      await storage.write(
        key: 'access_token',
        value: response.data['data']['access'],
      );
      await storage.write(
        key: 'refresh_token',
        value: response.data['data']['refresh'],
      );
      await storage.write(key: 'is_anonymous', value: 'true');
      
      return User.fromJson(response.data['data']['user']);
    }
  }
  
  Future<String> getDeviceId() async {
    final deviceInfo = DeviceInfoPlugin();
    if (Platform.isAndroid) {
      final androidInfo = await deviceInfo.androidInfo;
      return 'android-${androidInfo.id}';
    } else if (Platform.isIOS) {
      final iosInfo = await deviceInfo.iosInfo;
      return 'ios-${iosInfo.identifierForVendor}';
    }
    return 'unknown-${Uuid().v4()}';
  }
}
```

---

## 2️⃣ Anonymous → Email Conversion Flow

### 🎯 Ne Zaman Kullanılır?
- Anonymous user email/password ile kayıt olmak istediğinde
- "Hesabını güvenceye al" gibi prompt'larda
- App'i silip yüklese bile giriş yapabilmek için

### ❌ YANLIŞ Flow (Kullanma!)
```
1. Anonymous Register ❌
2. Normal Register (/api/auth/register/) ❌
3. Convert (/api/auth/anonymous/convert/) ❌

SORUN: 2 ayrı kullanıcı oluşur!
```

### ✅ DOĞRU Flow
```
1. Anonymous Register ✅
   ↓
2. Direkt Convert (/api/auth/anonymous/convert/) ✅
   ↓
   AYNI kullanıcı, sadece email/password eklendi!
```

### 📊 Flow Diagram
```
ANONYMOUS USER (ID: 100)
    ↓
    is_anonymous: true
    email: null
    ↓
CONVERT API (authenticated)
    ↓
SAME USER (ID: 100)
    ↓
    is_anonymous: false
    email: "user@example.com"
    password: hashed
```

### 🔧 API Call

**Önemli:** Bu endpoint **authenticated** endpoint! Anonymous user'ın token'ı ile çağrılır.

```http
POST /api/auth/anonymous/convert/
Authorization: Bearer {anonymous_user_access_token}
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "password2": "SecurePassword123!",
  "first_name": "John",  // Optional
  "last_name": "Doe",     // Optional
  "merge_data": true      // Optional, default: true
}
```

**merge_data Parametresi:**
- `true` (Önerilen): Aynı user ID korunur, data merge olur
- `false`: Yeni user oluşturulur, eski anonymous user silinir

**Response (200):**
```json
{
  "success": true,
  "code": "ANONYMOUS_USER_CONVERTED",
  "message": "Anonymous user converted successfully. Data merged.",
  "data": {
    "access": "eyJhbG...",  // Yeni token
    "refresh": "eyJhbG...", // Yeni token
    "user": {
      "id": 100,  // Aynı ID!
      "email": "user@example.com",
      "is_anonymous": false,
      "auth_provider": "email"
    }
  }
}
```

### 💻 Flutter Implementation

```dart
class AuthService {
  Future<User> convertAnonymousToEmail({
    required String email,
    required String password,
    String? firstName,
    String? lastName,
  }) async {
    // Check if user is anonymous
    final isAnonymous = await storage.read(key: 'is_anonymous') == 'true';
    if (!isAnonymous) {
      throw 'User is not anonymous';
    }
    
    // Get current token
    final accessToken = await storage.read(key: 'access_token');
    
    final response = await dio.post(
      '/api/auth/anonymous/convert/',
      data: {
        'email': email,
        'password': password,
        'password2': password,
        'first_name': firstName ?? '',
        'last_name': lastName ?? '',
        'merge_data': true, // Aynı ID'yi korur
      },
      options: Options(
        headers: {'Authorization': 'Bearer $accessToken'},
      ),
    );
    
    // Update tokens (YENİ tokenlar!)
    await storage.write(
      key: 'access_token',
      value: response.data['data']['access'],
    );
    await storage.write(
      key: 'refresh_token',
      value: response.data['data']['refresh'],
    );
    await storage.delete(key: 'is_anonymous');
    
    return User.fromJson(response.data['data']['user']);
  }
}
```

### 🎨 UI Example

```dart
// Show "Secure Your Account" prompt for anonymous users
class SecureAccountPrompt extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('Hesabını Güvenceye Al'),
      content: Text(
        'Email ve şifre ile kayıt olarak verilerini koruyabilirsin. '
        'App\'i silsen bile giriş yapabilirsin!',
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: Text('Daha Sonra'),
        ),
        ElevatedButton(
          onPressed: () {
            Navigator.pop(context);
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => ConvertToEmailScreen(),
              ),
            );
          },
          child: Text('Kayıt Ol'),
        ),
      ],
    );
  }
}

class ConvertToEmailScreen extends StatelessWidget {
  final emailController = TextEditingController();
  final passwordController = TextEditingController();
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Hesap Oluştur')),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: emailController,
              decoration: InputDecoration(labelText: 'Email'),
            ),
            TextField(
              controller: passwordController,
              decoration: InputDecoration(labelText: 'Şifre'),
              obscureText: true,
            ),
            ElevatedButton(
              onPressed: () async {
                try {
                  final user = await context.read<AuthService>()
                    .convertAnonymousToEmail(
                      email: emailController.text,
                      password: passwordController.text,
                    );
                  
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Hesap oluşturuldu! 🎉')),
                  );
                  
                  Navigator.pop(context);
                } catch (e) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Hata: $e')),
                  );
                }
              },
              child: Text('Hesap Oluştur'),
            ),
          ],
        ),
      ),
    );
  }
}
```

---

## 3️⃣ Anonymous → Google Conversion Flow

### 🎯 Ne Zaman Kullanılır?
- Anonymous user Google ile giriş yapmak istediğinde
- Hızlı kayıt olmak için
- Email/şifre girmeden hesap oluşturmak için

### ✅ DOĞRU Flow
```
1. Anonymous Register ✅
   ↓
2. Google Login with Anonymous Token ✅
   ↓
   Backend otomatik merge yapar!
   ↓
   AYNI user, Google account oldu!
```

### 📊 Flow Diagram
```
ANONYMOUS USER (ID: 100)
    ↓
    is_anonymous: true
    email: null
    auth_provider: "anonymous"
    ↓
GOOGLE LOGIN (with anon token)
    ↓
Backend algıladı: "Bu anonymous user!"
    ↓
SAME USER (ID: 100)
    ↓
    is_anonymous: false
    email: "user@gmail.com"
    auth_provider: "google"
```

### 🔧 API Call

**Önemli:** Anonymous user'ın token'ı Authorization header'da olmalı!

```http
POST /api/auth/login/google/
Authorization: Bearer {anonymous_user_access_token}  ← ÖNEMLİ!
Content-Type: application/json

{
  "access_token": "{google_access_token}"
}
```

**Backend Davranışı:**
1. Request'teki Authorization header'ı kontrol eder
2. User authenticated ve anonymous ise → MERGE
3. User authenticated ve real ise → Normal login
4. User yok ise → Normal login

**Response (200):**
```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "Google authentication successful.",
  "data": {
    "access": "eyJhbG...",  // Yeni token
    "refresh": "eyJhbG...", // Yeni token
    "user": {
      "id": 100,  // AYNI ID!
      "email": "user@gmail.com",
      "is_anonymous": false,
      "auth_provider": "google",
      "first_name": "John",
      "last_name": "Doe"
    }
  }
}
```

### 💻 Flutter Implementation

```dart
import 'package:google_sign_in/google_sign_in.dart';

class AuthService {
  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: ['email', 'profile'],
  );
  
  Future<User> loginWithGoogle() async {
    try {
      // 1. Google Sign In
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
      if (googleUser == null) {
        throw 'Google sign in cancelled';
      }
      
      // 2. Get Google access token
      final GoogleSignInAuthentication googleAuth =
          await googleUser.authentication;
      
      // 3. Get current token (if exists - for anonymous merge)
      final currentToken = await storage.read(key: 'access_token');
      
      // 4. Call backend
      // Dio automatically sends Authorization header if configured
      final response = await dio.post(
        '/api/auth/login/google/',
        data: {
          'access_token': googleAuth.accessToken,
        },
        // If user is anonymous, token will be sent automatically
        // Backend will detect and merge!
      );
      
      // 5. Save new tokens
      await storage.write(
        key: 'access_token',
        value: response.data['data']['access'],
      );
      await storage.write(
        key: 'refresh_token',
        value: response.data['data']['refresh'],
      );
      await storage.delete(key: 'is_anonymous');
      
      final user = User.fromJson(response.data['data']['user']);
      
      // 6. Check if merge happened
      final isAnonymous = await storage.read(key: 'is_anonymous');
      if (isAnonymous == 'true' && !user.isAnonymous) {
        print('✅ Anonymous user merged to Google account!');
        print('✅ User ID preserved: ${user.id}');
      }
      
      return user;
      
    } catch (e) {
      print('Google login error: $e');
      rethrow;
    }
  }
}
```

### 🔧 Dio Configuration (Token Interceptor)

```dart
class AuthInterceptor extends Interceptor {
  final FlutterSecureStorage storage;
  
  AuthInterceptor(this.storage);
  
  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    // Get token from storage
    final token = await storage.read(key: 'access_token');
    
    if (token != null) {
      // Add token to ALL requests (including social logins)
      options.headers['Authorization'] = 'Bearer $token';
    }
    
    handler.next(options);
  }
}

// Setup Dio
final dio = Dio()
  ..interceptors.add(AuthInterceptor(storage));
```

---

## 4️⃣ Anonymous → Apple Conversion Flow

### 🎯 Ne Zaman Kullanılır?
- Anonymous user Apple ile giriş yapmak istediğinde
- iOS cihazlarda hızlı kayıt için
- Apple'ın privacy standartlarını kullanmak için

### ✅ DOĞRU Flow
```
1. Anonymous Register ✅
   ↓
2. Apple Login with Anonymous Token ✅
   ↓
   Backend otomatik merge yapar!
   ↓
   AYNI user, Apple account oldu!
```

### 🔧 API Call

**Önemli:** Google ile tamamen aynı mantık!

```http
POST /api/auth/login/apple/
Authorization: Bearer {anonymous_user_access_token}  ← ÖNEMLİ!
Content-Type: application/json

{
  "id_token": "{apple_id_token}"
}
```

**Response (200):** Google ile aynı format.

### 💻 Flutter Implementation

```dart
import 'package:sign_in_with_apple/sign_in_with_apple.dart';

class AuthService {
  Future<User> loginWithApple() async {
    try {
      // 1. Apple Sign In
      final credential = await SignInWithApple.getAppleIDCredential(
        scopes: [
          AppleIDAuthorizationScopes.email,
          AppleIDAuthorizationScopes.fullName,
        ],
      );
      
      // 2. Call backend
      // Dio automatically sends Authorization header (anonymous token)
      final response = await dio.post(
        '/api/auth/login/apple/',
        data: {
          'id_token': credential.identityToken,
        },
      );
      
      // 3. Save new tokens
      await storage.write(
        key: 'access_token',
        value: response.data['data']['access'],
      );
      await storage.write(
        key: 'refresh_token',
        value: response.data['data']['refresh'],
      );
      await storage.delete(key: 'is_anonymous');
      
      return User.fromJson(response.data['data']['user']);
      
    } catch (e) {
      print('Apple login error: $e');
      rethrow;
    }
  }
}
```

---

## 5️⃣ Direct Email Registration Flow

### 🎯 Ne Zaman Kullanılır?
- Kullanıcı direkt email/password ile kayıt olmak isterse
- Anonymous olmadan başlamak isterse

### ✅ Flow
```
APP AÇILDI
    ↓
"Kayıt Ol" butonu
    ↓
Normal Register (/api/auth/register/)
    ↓
Yeni user oluşturuldu
```

### 🔧 API Call

```http
POST /api/auth/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "password2": "SecurePassword123!",
  "first_name": "John",  // Optional
  "last_name": "Doe"      // Optional
}
```

**Response (201):**
```json
{
  "success": true,
  "code": "CREATED",
  "message": "User registered successfully.",
  "data": {
    "access": "eyJhbG...",
    "refresh": "eyJhbG...",
    "user": {
      "id": 200,
      "email": "user@example.com",
      "is_anonymous": false,
      "auth_provider": "email"
    }
  }
}
```

### 💻 Flutter Implementation

```dart
class AuthService {
  Future<User> register({
    required String email,
    required String password,
    String? firstName,
    String? lastName,
  }) async {
    final response = await dio.post(
      '/api/auth/register/',
      data: {
        'email': email,
        'password': password,
        'password2': password,
        'first_name': firstName ?? '',
        'last_name': lastName ?? '',
      },
    );
    
    await storage.write(
      key: 'access_token',
      value: response.data['data']['access'],
    );
    await storage.write(
      key: 'refresh_token',
      value: response.data['data']['refresh'],
    );
    
    return User.fromJson(response.data['data']['user']);
  }
}
```

---

## 6️⃣ Direct Social Login Flow

### 🎯 Ne Zaman Kullanılır?
- Kullanıcı direkt Google/Apple ile giriş yapmak isterse
- Anonymous olmadan başlamak isterse

### ✅ Flow
```
APP AÇILDI
    ↓
"Google ile Giriş Yap" butonu
    ↓
Google Login (token YOK!)
    ↓
Yeni user veya mevcut user
```

### 🔧 API Call

```http
POST /api/auth/login/google/
# Authorization header YOK!
Content-Type: application/json

{
  "access_token": "{google_access_token}"
}
```

**Backend Davranışı:**
- Authorization header yok → Normal flow
- Email'e göre user bul veya oluştur
- Anonymous merge OLMAZ

---

## 7️⃣ Logout Flow

### ✅ Flow
```
LOGOUT
    ↓
Blacklist refresh token
    ↓
Clear storage
    ↓
YENİ anonymous oluştur (opsiyonel)
```

### 🔧 API Call

```http
POST /api/auth/logout/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "refresh": "{refresh_token}"
}
```

### 💻 Flutter Implementation

```dart
class AuthService {
  Future<void> logout() async {
    final refreshToken = await storage.read(key: 'refresh_token');
    
    try {
      await dio.post(
        '/api/auth/logout/',
        data: {'refresh': refreshToken},
      );
    } catch (e) {
      print('Logout error: $e');
    }
    
    // Clear storage
    await storage.deleteAll();
    
    // Create new anonymous user (if feature enabled)
    try {
      final newAnonUser = await registerAnonymous();
      print('New anonymous session started: ${newAnonUser.id}');
    } catch (e) {
      print('Anonymous feature might be disabled');
    }
  }
}
```

---

## 8️⃣ ALLOW_ANONYMOUS_USERS = False Durumu

### ⚙️ Settings
```python
# .env
ALLOW_ANONYMOUS_USERS=False
```

### ❌ Engellenen Endpoint'ler

```http
POST /api/auth/anonymous/register/
→ 403 Forbidden: "Anonymous user feature is disabled."

POST /api/auth/anonymous/convert/
→ 403 Forbidden: "Anonymous user feature is disabled."

POST /api/auth/login/google/ (with anon token)
→ 403 Forbidden: "Anonymous user feature is disabled."

POST /api/auth/login/apple/ (with anon token)
→ 403 Forbidden: "Anonymous user feature is disabled."
```

### ✅ Çalışan Endpoint'ler

```http
POST /api/auth/register/
✅ Normal email registration

POST /api/auth/login/
✅ Normal email login

POST /api/auth/login/google/ (without anon token)
✅ Normal Google login

POST /api/auth/login/apple/ (without anon token)
✅ Normal Apple login
```

### 💻 Flutter Handling

```dart
class AuthService {
  Future<User> initializeUser() async {
    final token = await storage.read(key: 'access_token');
    
    if (token != null) {
      try {
        return await getCurrentUser();
      } catch (e) {
        await storage.deleteAll();
      }
    }
    
    // Try to create anonymous user
    try {
      return await registerAnonymous();
    } catch (e) {
      if (e.response?.statusCode == 403) {
        // Feature disabled - show login/register screen
        return null; // Show auth screen
      }
      rethrow;
    }
  }
}
```

---

## 🎯 Hızlı Özet

### Anonymous → Email
```
1. POST /api/auth/anonymous/register/
2. POST /api/auth/anonymous/convert/ (with anon token)
   ✅ Aynı ID
```

### Anonymous → Google/Apple
```
1. POST /api/auth/anonymous/register/
2. POST /api/auth/login/google/ (with anon token in header)
   ✅ Otomatik merge, aynı ID
```

### Direct Register/Login
```
POST /api/auth/register/
veya
POST /api/auth/login/google/ (without token)
   ✅ Yeni user
```

### Logout
```
POST /api/auth/logout/
→ Clear storage
→ Yeni anonymous (opsiyonel)
```

---

## ⚠️ Yaygın Hatalar

### ❌ YANLIŞ: Anonymous sonrası normal register
```dart
await auth.registerAnonymous();
await auth.register(email, password); // ❌ 2 user oluşur!
```

### ✅ DOĞRU: Anonymous sonrası convert
```dart
await auth.registerAnonymous();
await auth.convertAnonymousToEmail(email, password); // ✅ Aynı user
```

---

## 🚀 Production Checklist

- [ ] `ALLOW_ANONYMOUS_USERS` setting ayarlandı
- [ ] Frontend device ID generation implement edildi
- [ ] Anonymous merge flow test edildi
- [ ] Social auth merge test edildi
- [ ] Logout sonrası yeni anonymous oluşturuluyor
- [ ] Token interceptor düzgün çalışıyor
- [ ] Error handling yapıldı
- [ ] UI/UX "Secure your account" prompt'u var


