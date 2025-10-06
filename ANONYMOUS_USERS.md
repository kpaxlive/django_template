# Anonymous Users Feature

## 📋 Overview

The Anonymous Users feature allows users to start using your app without creating an account. They can browse, use features, and save data. Later, they can convert their anonymous account to a real account while preserving their data.

**This feature is OPTIONAL and can be enabled/disabled via settings.**

## 🎯 Use Cases

- Mobile games where users want to play before creating an account
- E-commerce apps allowing anonymous browsing and cart management
- Content apps where users can save preferences anonymously
- Social apps with "guest mode"
- Any app wanting to reduce friction in onboarding

## ⚙️ Configuration

### Enable/Disable Feature

Edit `.env` file:

```env
# Enable anonymous users (default: True)
ALLOW_ANONYMOUS_USERS=True

# How long to keep anonymous users (days, default: 30)
ANONYMOUS_USER_RETENTION_DAYS=30
```

**To disable:** Set `ALLOW_ANONYMOUS_USERS=False` and restart server.

When disabled, the anonymous endpoints will return:
```json
{
  "success": false,
  "code": "ANONYMOUS_FEATURE_DISABLED",
  "error": "Anonymous user feature is disabled."
}
```

## 🔧 How It Works

### 1. Anonymous Registration

User sends a unique device ID (UUID, device fingerprint, etc.)

```bash
POST /api/auth/anonymous/register/
{
  "device_id": "unique-device-id-12345"
}
```

**Response:**
```json
{
  "success": true,
  "code": "ANONYMOUS_USER_CREATED",
  "message": "Anonymous user created successfully.",
  "data": {
    "access": "jwt_access_token",
    "refresh": "jwt_refresh_token",
    "user": {
      "id": 1,
      "email": null,
      "first_name": "",
      "last_name": "",
      "auth_provider": "anonymous",
      "date_joined": "2025-10-06T12:00:00Z"
    }
  }
}
```

**Key Points:**
- If device_id already exists, returns existing user
- No email or password required
- User gets JWT tokens immediately
- Can use all authenticated endpoints

### 2. Convert to Real User

Anonymous user can convert their account to a real user account:

#### Option A: Merge Data (Recommended)
Keeps the same user ID and all associated data.

```bash
POST /api/auth/anonymous/convert/
Authorization: Bearer {anonymous_user_token}
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "password2": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "merge_data": true
}
```

**What happens:**
- Same user ID
- All user data preserved (favorites, cart, preferences, etc.)
- User can now login with email/password
- Old tokens still work
- Device ID is cleared

#### Option B: Create New Account
Creates a new user and deletes the anonymous one.

```bash
POST /api/auth/anonymous/convert/
Authorization: Bearer {anonymous_user_token}
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "password2": "SecurePass123!",
  "merge_data": false
}
```

**What happens:**
- New user ID
- Anonymous user is deleted
- You need to implement data migration logic (see below)
- Returns new user's tokens

**Response (Both Options):**
```json
{
  "success": true,
  "code": "ANONYMOUS_USER_CONVERTED",
  "message": "Anonymous user converted successfully. Data merged.",
  "data": {
    "access": "new_access_token",
    "refresh": "new_refresh_token",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "auth_provider": "email",
      "date_joined": "2025-10-06T12:00:00Z"
    }
  }
}
```

## 📱 Flutter Implementation

### 1. Generate Device ID

```dart
import 'package:device_info_plus/device_info_plus.dart';
import 'package:crypto/crypto.dart';
import 'dart:convert';

Future<String> getDeviceId() async {
  final DeviceInfoPlugin deviceInfo = DeviceInfoPlugin();
  String identifier;
  
  if (Platform.isAndroid) {
    AndroidDeviceInfo androidInfo = await deviceInfo.androidInfo;
    identifier = androidInfo.id; // Android ID
  } else if (Platform.isIOS) {
    IosDeviceInfo iosInfo = await deviceInfo.iosInfo;
    identifier = iosInfo.identifierForVendor ?? ''; // iOS UUID
  } else {
    identifier = 'web-${DateTime.now().millisecondsSinceEpoch}';
  }
  
  // Hash the identifier for privacy
  var bytes = utf8.encode(identifier);
  var digest = sha256.convert(bytes);
  
  return digest.toString();
}
```

### 2. Anonymous Login

```dart
class AuthService {
  final Dio dio;
  final SecureStorage storage;
  
  Future<User> registerAnonymous() async {
    final deviceId = await getDeviceId();
    
    final response = await dio.post(
      '/api/auth/anonymous/register/',
      data: {'device_id': deviceId},
    );
    
    final apiResponse = ApiResponse.fromJson(response.data);
    
    if (apiResponse.success) {
      await storage.write(key: 'access_token', value: apiResponse.data['access']);
      await storage.write(key: 'refresh_token', value: apiResponse.data['refresh']);
      await storage.write(key: 'is_anonymous', value: 'true');
      
      return User.fromJson(apiResponse.data['user']);
    } else {
      throw Exception(apiResponse.error);
    }
  }
  
  Future<User> convertAnonymous({
    required String email,
    required String password,
    String? firstName,
    String? lastName,
    bool mergeData = true,
  }) async {
    final response = await dio.post(
      '/api/auth/anonymous/convert/',
      data: {
        'email': email,
        'password': password,
        'password2': password,
        'first_name': firstName,
        'last_name': lastName,
        'merge_data': mergeData,
      },
    );
    
    final apiResponse = ApiResponse.fromJson(response.data);
    
    if (apiResponse.success) {
      await storage.write(key: 'access_token', value: apiResponse.data['access']);
      await storage.write(key: 'refresh_token', value: apiResponse.data['refresh']);
      await storage.delete(key: 'is_anonymous');
      
      return User.fromJson(apiResponse.data['user']);
    } else {
      throw Exception(apiResponse.error);
    }
  }
}
```

### 3. App Flow

```dart
class MyApp extends StatefulWidget {
  @override
  _MyAppState createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  User? currentUser;
  
  @override
  void initState() {
    super.initState();
    _initUser();
  }
  
  Future<void> _initUser() async {
    final authService = AuthService();
    
    // Check if user has token
    final token = await storage.read(key: 'access_token');
    
    if (token == null) {
      // No token - create anonymous user
      currentUser = await authService.registerAnonymous();
    } else {
      // Has token - get user profile
      currentUser = await authService.getCurrentUser();
    }
    
    setState(() {});
  }
  
  // Show "Create Account" prompt after user engagement
  void _showCreateAccountPrompt() {
    if (currentUser?.isAnonymous == true) {
      showDialog(
        context: context,
        builder: (context) => CreateAccountDialog(
          onConvert: (email, password) async {
            currentUser = await authService.convertAnonymous(
              email: email,
              password: password,
              mergeData: true, // Keep user data
            );
            setState(() {});
          },
        ),
      );
    }
  }
}
```

## 🗄️ Database Schema

### User Model Fields

| Field | Type | Description |
|-------|------|-------------|
| `is_anonymous` | Boolean | Whether user is anonymous |
| `device_id` | String (255) | Unique device identifier (null for real users) |
| `email` | String | Email (null for anonymous users) |
| `auth_provider` | String | 'anonymous' for anonymous users |

### Indexes

- `device_id` - Unique index for fast lookup
- `is_anonymous` - Index for filtering anonymous users
- `email` - Non-unique index (allows null for anonymous users)

## 🔐 Security Considerations

### 1. Device ID Generation

**Good practices:**
- Use platform-specific identifiers (Android ID, iOS identifierForVendor)
- Hash the identifier before sending to server
- Don't use MAC address (privacy concern)
- Regenerate if user uninstalls and reinstalls

### 2. Token Security

- Anonymous users get the same JWT tokens as regular users
- Tokens work with all authenticated endpoints
- Anonymous users can be identified via `user.is_anonymous` flag
- Implement rate limiting to prevent abuse

### 3. Data Privacy

- Anonymous users have minimal personal data
- No email, phone, or name stored
- Device ID is hashed and not reversible
- Consider GDPR compliance (right to be forgotten)

### 4. Cleanup Strategy

Automatically delete old anonymous users:

```python
# management/commands/cleanup_anonymous_users.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from accounts.models import User

class Command(BaseCommand):
    help = 'Delete old anonymous users'
    
    def handle(self, *args, **options):
        retention_days = settings.ANONYMOUS_USER_RETENTION_DAYS
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        
        deleted_count = User.objects.filter(
            is_anonymous=True,
            date_joined__lt=cutoff_date
        ).delete()[0]
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Deleted {deleted_count} old anonymous users'
            )
        )
```

Run with cron:
```bash
0 2 * * * cd /path/to/project && python manage.py cleanup_anonymous_users
```

## 📊 Data Migration Strategy

When `merge_data=false`, you need to migrate user's app data.

### Example: Migrate User's Favorites

```python
# In your views.py or a utility function
def migrate_user_data(from_user, to_user):
    """Migrate data from anonymous user to real user."""
    
    # Example: Migrate favorites
    from myapp.models import Favorite
    Favorite.objects.filter(user=from_user).update(user=to_user)
    
    # Example: Migrate cart items
    from shop.models import CartItem
    CartItem.objects.filter(user=from_user).update(user=to_user)
    
    # Example: Migrate preferences
    from preferences.models import UserPreference
    UserPreference.objects.filter(user=from_user).update(user=to_user)
    
    # Add more model migrations as needed
```

Then use it in ConvertAnonymousView:
```python
# In views.py, line ~560
if not merge_data:
    # ... create new_user ...
    
    # Migrate data
    migrate_user_data(from_user=user, to_user=new_user)
    
    # Delete anonymous user
    user.delete()
```

## 🎛️ API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/auth/anonymous/register/` | POST | ❌ No | Create/retrieve anonymous user |
| `/api/auth/anonymous/convert/` | POST | ✅ Yes | Convert to real user |

## 📝 Response Codes

| Code | Description |
|------|-------------|
| `ANONYMOUS_USER_CREATED` | New anonymous user created |
| `ANONYMOUS_USER_CONVERTED` | Anonymous user converted to real user |
| `ANONYMOUS_FEATURE_DISABLED` | Feature is disabled in settings |
| `DEVICE_ID_EXISTS` | Device ID already exists (returns existing user) |
| `NOT_ANONYMOUS_USER` | Tried to convert a real user |

## ✅ Best Practices

### 1. When to Use

✅ **Good for:**
- Games and entertainment apps
- E-commerce with guest checkout
- Content consumption apps
- Apps with freemium model
- Reducing onboarding friction

❌ **Not ideal for:**
- Banking/finance apps
- Healthcare apps
- Apps requiring verified identity
- Apps with strict KYC requirements

### 2. User Experience

- Prompt conversion after user engagement (not immediately)
- Show benefits of creating account (save progress, sync devices)
- Make conversion seamless (one-click with auto-fill)
- Clearly communicate data preservation
- Allow skipping conversion multiple times

### 3. Data Management

- Use `merge_data=true` by default (preserves data)
- Implement cleanup for old anonymous users
- Consider data retention policies
- Log anonymous → real conversions for analytics

### 4. Testing

Test scenarios:
- Create anonymous user
- Use app features as anonymous
- Convert to real account
- Login with new credentials
- Verify data is preserved
- Test with feature disabled

## 🐛 Troubleshooting

### Anonymous users can't be created

**Check:**
1. `ALLOW_ANONYMOUS_USERS=True` in settings
2. Migration applied: `python manage.py migrate`
3. Device ID is at least 10 characters

### Email uniqueness error on conversion

**Cause:** Email already exists for another real user  
**Solution:** Check email before conversion, show error to user

### Data not preserved after conversion

**Cause:** Used `merge_data=false` without data migration  
**Solution:** Either use `merge_data=true` or implement `migrate_user_data()`

### Too many anonymous users

**Cause:** No cleanup strategy  
**Solution:** Run cleanup command regularly via cron

## 📚 Complete Example Flow

```
1. User opens app
   ↓
2. App checks for token
   - No token → Create anonymous user
   - Has token → Get user profile
   ↓
3. User uses app (saves data)
   ↓
4. After engagement, show "Create Account" prompt
   ↓
5. User enters email/password
   ↓
6. Convert anonymous → real user (merge_data=true)
   ↓
7. User now has real account with all data preserved
   ↓
8. User can login from any device with email/password
```

## 🎉 Conclusion

The Anonymous Users feature provides a frictionless onboarding experience while maintaining security and data integrity. It's fully optional, well-documented, and follows best practices.

**Key Benefits:**
- ✅ Zero-friction onboarding
- ✅ Data preservation on conversion
- ✅ Optional (can be disabled)
- ✅ Secure (JWT tokens)
- ✅ GDPR-friendly (minimal data)
- ✅ Production-ready

---

**Need help?** Check the main README.md or API_RESPONSE_STANDARD.md for more information.

