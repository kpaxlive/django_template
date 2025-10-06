# Google Auth Test Rehberi

## 🤔 Sorun: "access_token may not be blank" Hatası

Bu hata, Google'dan aldığın access token'ı backend'e göndermen gerektiği anlamına gelir. Backend, **kendi token'ını** değil, **Google'ın token'ını** bekler.

## 🔄 Google OAuth Flow

```
FRONTEND (Flutter/Web)
    ↓
1. Google Sign-In butonu
    ↓
2. Google OAuth sayfası açılır
    ↓
3. Kullanıcı Google hesabını seçer
    ↓
4. Google, Frontend'e access_token verir
    ↓
BACKEND'E GÖNDERİLİR
    ↓
5. Backend, token'ı Google'a doğrular
    ↓
6. Backend, kendi JWT token'ını üretir
    ↓
7. Frontend, JWT token ile API çağrıları yapar
```

## 📝 Anonymous User İle İlgisi Yok

Anonymous user'ın optional olması **sadece şunları etkiler:**
- Anonymous register endpoint'i açık/kapalı
- Anonymous merge işlemi açık/kapalı

**Google Auth için:**
- Anonymous user olsun veya olmasın
- `ALLOW_ANONYMOUS_USERS=True` veya `False` olsun
- **Her zaman Google'dan bir access token almak gerekir!**

Google token, Google'ın sana kullanıcının bilgilerini verme izni.

---

## 🧪 Swagger'da Test Etmek

### Seçenek 1: Google OAuth Playground (Önerilen)

1. **Google OAuth Playground'a git:**
   https://developers.google.com/oauthplayground/

2. **Sol taraftan OAuth scopes seç:**
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`

3. **"Authorize APIs" butonuna tıkla**
   - Google hesabını seç
   - İzinleri onayla

4. **"Exchange authorization code for tokens" butonuna tıkla**

5. **Access Token'ı kopyala**
   ```json
   {
     "access_token": "ya29.a0AfB_byDxxx...",
     "expires_in": 3599,
     "token_type": "Bearer"
   }
   ```

6. **Swagger'da kullan:**
   ```json
   {
     "access_token": "ya29.a0AfB_byDxxx..."
   }
   ```

### Seçenek 2: Google Cloud Console (Production için gerekli)

1. **Google Cloud Console'a git:**
   https://console.cloud.google.com/

2. **Yeni proje oluştur veya mevcut projeyi seç**

3. **"APIs & Services" → "Credentials"**

4. **"Create Credentials" → "OAuth 2.0 Client ID"**
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8000/auth/callback` (test için)
   - Authorized JavaScript origins: `http://localhost:8000`

5. **Client ID ve Client Secret'ı kaydet**

6. **Test için basit HTML sayfası kullan:**

```html
<!DOCTYPE html>
<html>
<head>
    <title>Google Auth Test</title>
    <script src="https://accounts.google.com/gsi/client" async defer></script>
</head>
<body>
    <h1>Google Auth Test</h1>
    
    <div id="g_id_onload"
         data-client_id="YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
         data-callback="handleCredentialResponse">
    </div>
    
    <div class="g_id_signin" data-type="standard"></div>
    
    <script>
        function handleCredentialResponse(response) {
            console.log("Google ID Token: " + response.credential);
            
            // Test backend
            fetch('http://localhost:8000/api/auth/login/google/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    access_token: response.credential
                })
            })
            .then(res => res.json())
            .then(data => {
                console.log('Backend response:', data);
                alert('Login successful! Check console for tokens.');
            })
            .catch(err => {
                console.error('Error:', err);
                alert('Login failed! Check console for details.');
            });
        }
    </script>
</body>
</html>
```

---

## 🔍 Backend Ne Yapıyor?

```python
# views.py - GoogleLoginView

def post(self, request):
    access_token = request.data['access_token']  # Frontend'den geliyor
    
    # Google'a doğrulama isteği
    google_response = requests.get(
        'https://www.googleapis.com/oauth2/v3/userinfo',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    
    user_info = google_response.json()
    # {
    #   "email": "user@gmail.com",
    #   "name": "John Doe",
    #   "given_name": "John",
    #   "family_name": "Doe",
    #   "picture": "..."
    # }
    
    # User oluştur veya bul
    user = get_or_create_user(email=user_info['email'])
    
    # BACKEND JWT token üret
    refresh = RefreshToken.for_user(user)
    
    return {
        'access': str(refresh.access_token),  # Backend token
        'refresh': str(refresh),              # Backend token
    }
```

---

## 📱 Flutter Implementation (Production)

### 1. Dependencies

```yaml
# pubspec.yaml
dependencies:
  google_sign_in: ^6.1.5
  dio: ^5.3.3
  flutter_secure_storage: ^9.0.0
```

### 2. Google Sign In Service

```dart
import 'package:google_sign_in/google_sign_in.dart';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AuthService {
  final Dio dio;
  final FlutterSecureStorage storage;
  
  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: [
      'email',
      'profile',
    ],
  );
  
  AuthService({
    required this.dio,
    required this.storage,
  });
  
  /// Google Sign In (Direkt - Anonymous değil)
  Future<User> loginWithGoogle() async {
    try {
      // 1. Google Sign In popup'ı göster
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
      
      if (googleUser == null) {
        throw 'Google sign in cancelled by user';
      }
      
      // 2. Google access token al
      final GoogleSignInAuthentication googleAuth = 
          await googleUser.authentication;
      
      print('Google Access Token: ${googleAuth.accessToken}');
      
      // 3. Backend'e gönder
      final response = await dio.post(
        '/api/auth/login/google/',
        data: {
          'access_token': googleAuth.accessToken,  // ← Google token
        },
      );
      
      // 4. Backend JWT token'larını kaydet
      await storage.write(
        key: 'access_token',
        value: response.data['data']['access'],  // ← Backend token
      );
      await storage.write(
        key: 'refresh_token',
        value: response.data['data']['refresh'],  // ← Backend token
      );
      
      return User.fromJson(response.data['data']['user']);
      
    } on DioException catch (e) {
      print('Dio error: ${e.response?.data}');
      rethrow;
    } catch (e) {
      print('Google Sign In error: $e');
      rethrow;
    }
  }
  
  /// Anonymous user'ı Google'a convert et
  Future<User> convertAnonymousToGoogle() async {
    try {
      // 1. Mevcut anonymous token'ı al
      final anonToken = await storage.read(key: 'access_token');
      
      if (anonToken == null) {
        throw 'No anonymous user found';
      }
      
      // 2. Google Sign In
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
      
      if (googleUser == null) {
        throw 'Google sign in cancelled';
      }
      
      // 3. Google access token al
      final GoogleSignInAuthentication googleAuth = 
          await googleUser.authentication;
      
      // 4. Backend'e gönder (anonymous token header'da)
      final response = await dio.post(
        '/api/auth/login/google/',
        data: {
          'access_token': googleAuth.accessToken,
        },
        options: Options(
          headers: {
            'Authorization': 'Bearer $anonToken',  // ← Anonymous token
          },
        ),
      );
      
      // 5. Yeni backend token'ları kaydet
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
      
      print('✅ Anonymous user converted to Google account');
      print('✅ Same user ID: ${user.id}');
      
      return user;
      
    } catch (e) {
      print('Convert to Google error: $e');
      rethrow;
    }
  }
}
```

### 3. UI Example

```dart
class LoginScreen extends StatelessWidget {
  final AuthService authService;
  
  const LoginScreen({required this.authService});
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Login')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Google Sign In Button
            ElevatedButton.icon(
              onPressed: () async {
                try {
                  final user = await authService.loginWithGoogle();
                  
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Welcome ${user.email}!'),
                    ),
                  );
                  
                  // Navigate to home
                  Navigator.pushReplacementNamed(context, '/home');
                  
                } catch (e) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Login failed: $e'),
                      backgroundColor: Colors.red,
                    ),
                  );
                }
              },
              icon: Icon(Icons.g_mobiledata),
              label: Text('Sign in with Google'),
            ),
            
            SizedBox(height: 20),
            
            // Convert Anonymous to Google
            TextButton(
              onPressed: () async {
                try {
                  final user = await authService.convertAnonymousToGoogle();
                  
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Account secured with Google!'),
                    ),
                  );
                  
                } catch (e) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Conversion failed: $e'),
                      backgroundColor: Colors.red,
                    ),
                  );
                }
              },
              child: Text('Secure anonymous account with Google'),
            ),
          ],
        ),
      ),
    );
  }
}
```

---

## 🔍 Token'ları Anlamak

### 1. Google Access Token
- **Kim üretir:** Google
- **Nereden gelir:** Frontend'de Google Sign-In flow'u
- **Ne işe yarar:** Backend'in Google'dan kullanıcı bilgilerini almasını sağlar
- **Ömrü:** Kısa (genellikle 1 saat)
- **Kullanım:** Sadece bir kez (backend'e gönderilir)

```
Frontend → Google Sign In → Google Access Token → Backend'e gönder
```

### 2. Backend JWT Token (Access)
- **Kim üretir:** Backend (Django)
- **Nereden gelir:** Backend response'u
- **Ne işe yarar:** Backend API'lerine erişim
- **Ömrü:** 1 saat (settings'te ayarlanabilir)
- **Kullanım:** Her API isteğinde

```
Backend → JWT Token üretir → Frontend'e döner → Her API isteğinde kullanılır
```

### 3. Backend JWT Token (Refresh)
- **Kim üretir:** Backend (Django)
- **Nereden gelir:** Backend response'u
- **Ne işe yarar:** Yeni access token almak
- **Ömrü:** 1 gün (settings'te ayarlanabilir)
- **Kullanım:** Access token expire olunca

---

## 📊 Flow Diyagramı

### Direkt Google Login (Anonymous YOK)

```
┌──────────┐                    ┌────────┐                    ┌─────────┐
│ Frontend │                    │ Google │                    │ Backend │
└────┬─────┘                    └───┬────┘                    └────┬────┘
     │                              │                              │
     │ 1. Sign In Button            │                              │
     ├─────────────────────────────>│                              │
     │                              │                              │
     │ 2. OAuth Page                │                              │
     │<─────────────────────────────┤                              │
     │                              │                              │
     │ 3. User selects account      │                              │
     ├─────────────────────────────>│                              │
     │                              │                              │
     │ 4. Google Access Token       │                              │
     │<─────────────────────────────┤                              │
     │   { access_token: "ya29..." }│                              │
     │                              │                              │
     │ 5. POST /api/auth/login/google/                             │
     │    { access_token: "ya29..." }                              │
     ├────────────────────────────────────────────────────────────>│
     │                              │                              │
     │                              │ 6. Verify token              │
     │                              │<─────────────────────────────┤
     │                              │                              │
     │                              │ 7. User info                 │
     │                              ├─────────────────────────────>│
     │                              │                              │
     │                              │                        8. Create/Get user
     │                              │                        9. Generate JWT
     │                              │                              │
     │ 10. Backend JWT tokens                                      │
     │<────────────────────────────────────────────────────────────┤
     │   { access: "eyJ...", refresh: "eyJ..." }                   │
     │                              │                              │
     │ 11. Save tokens              │                              │
     │ 12. Use JWT for API calls    │                              │
     │                              │                              │
```

### Anonymous → Google Merge

```
┌──────────┐                    ┌────────┐                    ┌─────────┐
│ Frontend │                    │ Google │                    │ Backend │
└────┬─────┘                    └───┬────┘                    └────┬────┘
     │                              │                              │
     │ 1. Anonymous register        │                              │
     ├────────────────────────────────────────────────────────────>│
     │                              │                              │
     │ 2. Anonymous JWT tokens                                     │
     │<────────────────────────────────────────────────────────────┤
     │   { access: "eyJ...", refresh: "eyJ..." }                   │
     │   User: { is_anonymous: true, id: 100 }                     │
     │                              │                              │
     │ ... User uses app with anonymous account ...                │
     │                              │                              │
     │ 3. "Secure with Google" button                              │
     ├─────────────────────────────>│                              │
     │                              │                              │
     │ 4. Google Access Token       │                              │
     │<─────────────────────────────┤                              │
     │   { access_token: "ya29..." }│                              │
     │                              │                              │
     │ 5. POST /api/auth/login/google/                             │
     │    Headers: { Authorization: "Bearer {anon_jwt}" }          │
     │    Body: { access_token: "ya29..." }                        │
     ├────────────────────────────────────────────────────────────>│
     │                              │                              │
     │                              │                        6. Detect anon user
     │                              │                        7. MERGE!
     │                              │                        8. Same user ID: 100
     │                              │                        9. Update user
     │                              │                        10. New JWT
     │                              │                              │
     │ 11. New Backend JWT tokens                                  │
     │<────────────────────────────────────────────────────────────┤
     │   { access: "eyJ...", refresh: "eyJ..." }                   │
     │   User: { is_anonymous: false, id: 100, email: "..." }      │
     │                              │                              │
```

---

## ⚠️ Yaygın Hatalar

### ❌ Hata 1: Backend JWT'yi Google'a gönderme

```dart
// YANLIŞ!
final backendToken = await storage.read(key: 'access_token');
await dio.post('/api/auth/login/google/', data: {
  'access_token': backendToken,  // ❌ Bu backend token, Google token değil!
});
```

```dart
// DOĞRU!
final googleAuth = await googleUser.authentication;
await dio.post('/api/auth/login/google/', data: {
  'access_token': googleAuth.accessToken,  // ✅ Google token
});
```

### ❌ Hata 2: Google token'ı API isteklerinde kullanma

```dart
// YANLIŞ!
final googleToken = googleAuth.accessToken;
await dio.get('/api/auth/user/', options: Options(
  headers: {'Authorization': 'Bearer $googleToken'},  // ❌
));
```

```dart
// DOĞRU!
final backendToken = await storage.read(key: 'access_token');
await dio.get('/api/auth/user/', options: Options(
  headers: {'Authorization': 'Bearer $backendToken'},  // ✅
));
```

### ❌ Hata 3: Anonymous token header'a eklemeden merge deneme

```dart
// YANLIŞ! (Merge olmaz, yeni user oluşur)
await dio.post('/api/auth/login/google/', data: {
  'access_token': googleAuth.accessToken,
  // Authorization header YOK!
});
```

```dart
// DOĞRU! (Merge olur, aynı user ID)
final anonToken = await storage.read(key: 'access_token');
await dio.post('/api/auth/login/google/', 
  data: {'access_token': googleAuth.accessToken},
  options: Options(
    headers: {'Authorization': 'Bearer $anonToken'},  // ✅
  ),
);
```

---

## 🎯 Özet

### Google Access Token nereden gelir?
- **Test:** Google OAuth Playground
- **Production:** Flutter'da `google_sign_in` package
- **Web:** Google Sign-In JavaScript library

### Backend'e ne gönderilir?
```json
{
  "access_token": "ya29.a0AfB_byD..."  // ← Google'dan gelen token
}
```

### Backend ne döndürür?
```json
{
  "success": true,
  "data": {
    "access": "eyJhbGciOi...",   // ← Backend JWT (API calls için)
    "refresh": "eyJhbGciOi...",  // ← Backend JWT (refresh için)
    "user": { ... }
  }
}
```

### Anonymous user ilgisi?
- **İlgisi YOK!** Google token her zaman gerekli.
- Anonymous user sadece **merge işlemini** etkiler.
- Merge için: Anonymous token + Google token
- Normal login için: Sadece Google token

---

## 🚀 Hızlı Test

1. Google OAuth Playground'a git: https://developers.google.com/oauthplayground/
2. Scope seç: `userinfo.email`, `userinfo.profile`
3. "Authorize APIs" → Google hesabını seç
4. "Exchange authorization code for tokens"
5. Access token'ı kopyala
6. Swagger'da test et:
   ```json
   {
     "access_token": "BURAYA_YAPIŞTIR"
   }
   ```

**NOT:** Token 1 saat geçerli, sonra yeni token al!


