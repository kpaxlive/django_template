# Anonymous User - Detaylı Senaryolar ve Çözümler

## 📋 İçindekiler

1. [Device ID: Frontend vs Backend](#1-device-id-frontend-vs-backend)
2. [Merge Sonrası Logout Davranışı](#2-merge-sonrası-logout-davranışı)
3. [Social Auth ile Merge](#3-social-auth-ile-merge)
4. [Email/Google Aynı Email Senaryosu](#4-emailgoogle-aynı-email-senaryosu)
5. [Tüm Olası Senaryolar](#5-tüm-olası-senaryolar)

---

## 1️⃣ Device ID: Frontend vs Backend

### ❓ Neden Device ID Frontend'den Geliyor?

**Eski Yaklaşım:** Device ID zorunlu, frontend gönderir.

**Yeni Yaklaşım (✨ Güncellendi):** Device ID **OPSİYONEL**!

```json
// Frontend gönderirse
POST /api/auth/anonymous/register/
{
  "device_id": "phone-abc123..."
}

// Frontend göndermezse (boş)
POST /api/auth/anonymous/register/
{}
// Backend otomatik UUID üretir: "backend-uuid-xxxx"
```

### 🎯 Ne Zaman Hangisini Kullan?

#### Frontend Device ID (Önerilen):
```dart
// Flutter'da
final deviceId = await getDeviceId(); // UUID from device
await auth.registerAnonymous(deviceId: deviceId);
```

**Avantajları:**
- ✅ App silip yükleyince bile aynı user
- ✅ Cihaz binding (güvenlik)
- ✅ Offline-first apps için ideal
- ✅ User persistence

**Ne zaman kullan:**
- Kullanıcı verilerini cihaza bağlamak istersen
- App reinstall'da data korunmalıysa
- Oyunlarda progress kaydetme
- E-commerce'de cart persistence

#### Backend UUID (Basit):
```dart
// Flutter'da - Device ID gönderme
await auth.registerAnonymous(); // Backend üretir
```

**Avantajları:**
- ✅ Frontend basit
- ✅ Implement kolay
- ✅ Her cihazda farklı user

**Ne zaman kullan:**
- Device binding gerekmiyorsa
- Geçici session istersen
- Multi-device support istersen
- Basit use case'ler

### 💡 Hybrid Approach (En İyi):

```dart
class AuthService {
  Future<User> registerAnonymous() async {
    try {
      // Try to get device ID
      final deviceId = await getDeviceIdSafely();
      
      return await dio.post('/api/auth/anonymous/register/', data: {
        'device_id': deviceId, // Varsa gönder, yoksa boş
      });
    } catch (e) {
      // Fallback: Let backend generate
      return await dio.post('/api/auth/anonymous/register/', data: {});
    }
  }
}
```

---

## 2️⃣ Merge Sonrası Logout Davranışı

### ❓ Merge yaptıktan sonra logout yapınca ne olmalı?

**Senaryo:**
```
1. Anonymous user → token A
2. Convert to email → token B (aynı user ID)
3. Logout
4. Ne yapmalıyım?
```

### 🎯 Cevap: YENİ Anonymous User OLUŞTURMA!

**Çünkü:**
- Eski anonymous user artık "real user" oldu
- Real user'ın device_id'si NULL
- Yeni oturum = yeni anonymous user

### Flutter Implementation:

```dart
class AuthService {
  User? currentUser;
  
  // Logout
  Future<void> logout() async {
    await dio.post('/api/auth/logout/', data: {
      'refresh': refreshToken,
    });
    
    // Clear tokens
    await storage.deleteAll();
    
    // Create NEW anonymous user
    currentUser = await registerAnonymous();
    
    // UI'ı güncelle
    notifyListeners();
  }
  
  // Convert anonymous to real
  Future<User> convertAnonymous({
    required String email,
    required String password,
  }) async {
    final response = await dio.post(
      '/api/auth/anonymous/convert/',
      data: {
        'email': email,
        'password': password,
        'password2': password,
        'merge_data': true, // Aynı ID, data korunur
      },
    );
    
    // User artık real, anonymous değil
    currentUser = User.fromJson(response.data['data']['user']);
    
    // Save tokens
    await storage.write(key: 'is_anonymous', value: 'false');
    
    return currentUser!;
  }
}
```

### 📊 Flow Diagram:

```
APP START
   ↓
Token var mı?
   ├─ Hayır → Yeni Anonymous User Oluştur (1)
   └─ Evet → Token'la get user
                ↓
             User Anonymous mi?
                ├─ Evet → Anon olarak devam
                └─ Hayır → Real user olarak devam
                
CONVERT → Real User (Aynı ID)
   ↓
LOGOUT → Tokens sil
   ↓
Yeni Anonymous User Oluştur (2)  ← Farklı ID!
```

**Önemli:**
- (1) ve (2) FARKLI kullanıcılar
- Convert işlemi ID'yi korur
- Logout yeni session başlatır

---

## 3️⃣ Social Auth ile Merge

### ❓ Anonymous user Google/Apple ile giriş yaparsa ne olur?

**✨ YENİ ÖZELLİK:** Social auth artık anonymous merge destekliyor!

### 🔄 Otomatik Merge Stratejisi

```dart
// 1. Anonymous user oluştur
final anonUser = await auth.registerAnonymous();
// User ID: 123, is_anonymous: true

// 2. App'i kullan, data biriktir
await saveUserData(userId: 123, data: ...);

// 3. Google ile giriş yap (AYNI TOKEN'la)
final googleUser = await auth.loginWithGoogle(
  googleAccessToken: googleToken,
  // Authorization header'ında anonymous token var!
);

// SONUÇ:
// ✅ Aynı User ID: 123
// ✅ is_anonymous: false
// ✅ auth_provider: 'google'
// ✅ email: Google'dan gelen email
// ✅ TÜM DATA KORUNDU!
```

### Flutter Implementation:

```dart
class AuthService {
  // Google Login with Optional Merge
  Future<User> loginWithGoogle() async {
    // 1. Get Google access token
    final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
    final GoogleSignInAuthentication googleAuth = await googleUser!.authentication;
    
    // 2. Call backend WITH current token (if anonymous)
    final response = await dio.post(
      '/api/auth/login/google/',
      data: {
        'access_token': googleAuth.accessToken,
      },
      // Dio automatically sends Authorization header if token exists
    );
    
    // 3. Backend detects anonymous user and merges!
    final user = User.fromJson(response.data['data']['user']);
    
    // 4. Update tokens
    await storage.write(key: 'access_token', value: response.data['data']['access']);
    await storage.write(key: 'refresh_token', value: response.data['data']['refresh']);
    await storage.delete(key: 'is_anonymous');
    
    return user;
  }
}
```

### 🔍 Backend'de Ne Oluyor?

```python
# Google/Apple Login View'da

# 1. Token'dan mevcut user'ı al
current_user = request.user if request.user.is_authenticated else None
is_anonymous_merge = current_user and current_user.is_anonymous

if is_anonymous_merge:
    # MERGE: Anonymous user'ı Google account'a dönüştür
    user = current_user  # AYNI KULLANICI!
    user.email = email_from_google
    user.is_anonymous = False
    user.auth_provider = 'google'
    user.device_id = None
    user.save()
else:
    # Normal flow: Email'e göre get or create
    user = get_or_create_by_email(email)
```

### 📊 Merge Flow:

```
ANONYMOUS USER (ID: 123)
   ↓
   is_anonymous: true
   device_id: "abc..."
   email: null
   ↓
GOOGLE LOGIN (with anon token)
   ↓
MERGE
   ↓
SAME USER (ID: 123)  ← Aynı ID!
   ↓
   is_anonymous: false
   device_id: null
   email: "user@gmail.com"
   auth_provider: "google"
   ↓
ALL DATA PRESERVED ✅
```

---

## 4️⃣ Email/Google Aynı Email Senaryosu

### ❓ Kullanıcı önce email ile sonra Google ile (aynı email) giriş yaparsa?

### 🎯 Backend Davranışı: AKILLI MERGE

#### Senaryo A: Email → Google (Aynı Email)

```
1. user@gmail.com ile kayıt olur
   → User ID: 100
   → auth_provider: 'email'
   
2. Çıkış yapar

3. Google ile giriş yapar (user@gmail.com)
   → Backend: "Bu email zaten var!"
   → AYNI kullanıcıyı döndürür (ID: 100)
   → auth_provider: 'google' olarak günceller
   
SONUÇ: Aynı hesap, farklı login yöntemi ✅
```

#### Senaryo B: Google → Email (Aynı Email)

```
1. Google ile giriş yapar (user@gmail.com)
   → User ID: 200
   → auth_provider: 'google'
   
2. Çıkış yapar

3. Email/password ile giriş yapmaya çalışır
   → Backend: "Bu email zaten var ama Google account"
   → Login BAŞARISIZ (password yok)
   
Çözüm: "Google ile giriş yap" mesajı göster
```

### 🔍 Backend Logic:

```python
# Email Registration
def register_email(email, password):
    # Check if email exists (non-anonymous)
    existing = User.objects.filter(email=email, is_anonymous=False).first()
    
    if existing:
        if existing.auth_provider == 'google':
            return error("Bu email Google ile kayıtlı. Google ile giriş yapın.")
        elif existing.auth_provider == 'apple':
            return error("Bu email Apple ile kayıtlı. Apple ile giriş yapın.")
        else:
            return error("Bu email zaten kullanılıyor.")
    
    # Create new user
    user = create_user(email, password, auth_provider='email')
    return success(user)

# Google Login
def google_login(google_email):
    # Check existing user (non-anonymous)
    existing = User.objects.filter(email=google_email, is_anonymous=False).first()
    
    if existing:
        # User exists - update auth provider and return
        existing.auth_provider = 'google'  # Allow switching
        existing.save()
        return success(existing)
    else:
        # Create new Google user
        user = create_user(google_email, auth_provider='google')
        return success(user)
```

### 💡 Frontend Handling:

```dart
class AuthService {
  Future<User> register(String email, String password) async {
    try {
      final response = await dio.post('/api/auth/register/', data: {
        'email': email,
        'password': password,
        'password2': password,
      });
      
      return User.fromJson(response.data['data']['user']);
    } catch (e) {
      if (e.response?.data['code'] == 'EMAIL_ALREADY_EXISTS') {
        // Check auth provider from error message
        final error = e.response?.data['error'];
        
        if (error.contains('Google')) {
          throw 'Bu email Google ile kayıtlı. Google ile giriş yapın.';
        } else if (error.contains('Apple')) {
          throw 'Bu email Apple ile kayıtlı. Apple ile giriş yapın.';
        } else {
          throw 'Bu email zaten kullanılıyor.';
        }
      }
      rethrow;
    }
  }
  
  Future<User> loginWithGoogle() async {
    // Google login always works if email exists
    // Backend will merge if needed
    final response = await dio.post('/api/auth/login/google/', ...);
    return User.fromJson(response.data['data']['user']);
  }
}
```

### 🎨 UI Suggestion:

```dart
// Login screen
Widget build(BuildContext context) {
  return Column(
    children: [
      // Email/Password
      TextField(controller: emailController),
      TextField(controller: passwordController),
      ElevatedButton(
        onPressed: () async {
          try {
            await auth.login(email, password);
          } catch (e) {
            if (e.toString().contains('Google')) {
              // Show Google login button
              showDialog(
                context: context,
                builder: (context) => AlertDialog(
                  title: Text('Bu email Google ile kayıtlı'),
                  content: Text('Google ile giriş yapmak ister misiniz?'),
                  actions: [
                    TextButton(
                      onPressed: () async {
                        Navigator.pop(context);
                        await auth.loginWithGoogle();
                      },
                      child: Text('Google ile Giriş Yap'),
                    ),
                  ],
                ),
              );
            }
          }
        },
        child: Text('Giriş Yap'),
      ),
      
      // Social buttons
      GoogleSignInButton(onPressed: () => auth.loginWithGoogle()),
      AppleSignInButton(onPressed: () => auth.loginWithApple()),
    ],
  );
}
```

---

## 5️⃣ Tüm Olası Senaryolar

### Senaryo Matrix:

| Durum | Davranış | Sonuç |
|-------|----------|-------|
| **Anonymous → Email Merge** | Convert endpoint | ✅ Aynı ID, email eklenir |
| **Anonymous → Google (with token)** | Google login + anon token | ✅ Aynı ID, Google'a dönüşür |
| **Anonymous → Apple (with token)** | Apple login + anon token | ✅ Aynı ID, Apple'a dönüşür |
| **Email → Google (same email)** | Google login | ✅ Aynı user, provider güncellenir |
| **Google → Email (same email)** | Email login | ❌ Hata: "Google ile giriş yap" |
| **Email → Google (different email)** | Google login | ✅ İki ayrı hesap |
| **Anonymous → Logout** | Logout | ✅ Yeni anonymous oluştur |
| **Real user → Logout** | Logout | ✅ Yeni anonymous oluştur |

### Detaylı Flow:

```
BAŞLANGIÇ
   ↓
[1] Yeni Kullanıcı
   ↓
   Opsiyonel Seçim:
   ├─ A) Anonymous → App'i kullan
   │     ↓
   │     Daha sonra seçim:
   │     ├─ A1) Email ile merge → Real user (aynı ID)
   │     ├─ A2) Google ile merge → Real user (aynı ID)
   │     └─ A3) Apple ile merge → Real user (aynı ID)
   │
   ├─ B) Direkt Email kayıt → Real user
   │
   ├─ C) Direkt Google → Real user
   │
   └─ D) Direkt Apple → Real user

[2] Mevcut Kullanıcı
   ↓
   Token var mı?
   ├─ Evet → Get user profile
   │     ↓
   │     is_anonymous?
   │     ├─ Yes → Anonymous olarak devam
   │     └─ No → Real user olarak devam
   │
   └─ Hayır → [1]'e git

[3] Logout
   ↓
   Tokens sil
   ↓
   Yeni Anonymous oluştur
   ↓
   [1]'e git
```

### 🔐 Güvenlik Notları:

1. **Email Uniqueness:**
   - Email SADECE non-anonymous userlar için unique
   - Anonymous userlar email olmadan kaydedilir
   - Merge'de email duplicate kontrolü yapılır

2. **Device ID Security:**
   - Device ID hash'lenmeli (frontend'de)
   - Backend'de plain text saklanmaz
   - UUID v4 format kullan

3. **Auth Provider Switching:**
   - Email → Google: ✅ İzinli
   - Google → Email: ❌ Yasak (security risk)
   - Google → Apple: ✅ İzinli (email aynıysa)

4. **Anonymous User Cleanup:**
   - Eski anonymous userlar silinmeli
   - Cron job: `cleanup_anonymous_users`
   - Retention: 30 gün (varsayılan)

---

## 🎯 Best Practices Özeti

### DO ✅

1. **Device ID gönder** (mümkünse)
   ```dart
   final deviceId = await getDeviceId();
   await auth.registerAnonymous(deviceId: deviceId);
   ```

2. **Merge işlemini vurgula**
   ```dart
   showDialog(
     content: Text('Hesap oluşturarak verileriniz korunacak'),
   );
   ```

3. **Social auth için token gönder**
   ```dart
   // Anonymous token header'da olsun
   await auth.loginWithGoogle(); // Otomatik merge
   ```

4. **Logout sonrası yeni anonymous**
   ```dart
   await auth.logout();
   await auth.registerAnonymous(); // Yeni session
   ```

5. **Email conflict handle et**
   ```dart
   catch (e) {
     if (e.code == 'EMAIL_ALREADY_EXISTS') {
       showGoogleLoginOption();
     }
   }
   ```

### DON'T ❌

1. **Merge sonrası eski token kullanma**
   ```dart
   // ❌ Yanlış
   final oldToken = storage.read('old_token');
   await api.call(oldToken);
   
   // ✅ Doğru
   final newToken = storage.read('access_token');
   await api.call(newToken);
   ```

2. **Device ID'yi expose etme**
   ```dart
   // ❌ Yanlış
   final deviceId = androidInfo.id; // Plain
   
   // ✅ Doğru
   final deviceId = sha256(androidInfo.id); // Hashed
   ```

3. **Her açılışta yeni anonymous**
   ```dart
   // ❌ Yanlış
   @override
   void initState() {
     auth.registerAnonymous(); // Her seferinde yeni!
   }
   
   // ✅ Doğru
   @override
   void initState() {
     final token = storage.read('token');
     if (token == null) {
       auth.registerAnonymous();
     }
   }
   ```

4. **Merge olmadan logout**
   ```dart
   // ❌ Risk: Data kaybı
   if (user.isAnonymous) {
     showWarning('Verileriniz kaybolacak!');
     // Convert option sun
   }
   ```

---

## 🚀 Özet

### Tüm Soruların Cevapları:

1. **Device ID neden frontend'den?**
   → Artık opsiyonel! Backend de üretebilir.

2. **Merge sonrası logout ne yapar?**
   → Yeni anonymous user oluştur.

3. **Social auth merge çalışır mı?**
   → ✅ Evet! Anonymous token ile çağır.

4. **Email/Google aynı email?**
   → Backend akıllıca handle eder, conflict yok.

**Sonuç:** Her senaryo düşünülmüş, production-ready! 🎉


