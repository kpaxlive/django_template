# API Flow & Architecture

## 🔄 Authentication Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FLUTTER APP                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Django REST API                               │
│                 (http://localhost:8000/api)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐      ┌──────────────┐
│   Email/Pw   │    │    Social    │      │     User     │
│     Auth     │    │     Auth     │      │  Management  │
└──────────────┘    └──────────────┘      └──────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
   Register              Google                  Get User
   Login                 Apple                   Delete User
   Logout
   Refresh
```

## 📊 Request/Response Flow

### 1. Registration Flow

```
Client                      Server                    Database
  │                           │                           │
  │   POST /api/auth/register/│                           │
  │   {email, password, ...}  │                           │
  ├──────────────────────────>│                           │
  │                           │   Validate data           │
  │                           ├─────────┐                 │
  │                           │         │                 │
  │                           │<────────┘                 │
  │                           │   Create user             │
  │                           ├─────────────────────────> │
  │                           │                           │
  │                           │   Generate JWT tokens     │
  │                           ├─────────┐                 │
  │                           │         │                 │
  │                           │<────────┘                 │
  │   {access, refresh, user} │                           │
  │<──────────────────────────┤                           │
  │                           │                           │
```

### 2. Login Flow

```
Client                      Server                    Database
  │                           │                           │
  │   POST /api/auth/login/   │                           │
  │   {email, password}       │                           │
  ├──────────────────────────>│                           │
  │                           │   Verify credentials      │
  │                           ├─────────────────────────> │
  │                           │<────────────────────────┤ │
  │                           │   Generate JWT tokens     │
  │                           ├─────────┐                 │
  │                           │         │                 │
  │                           │<────────┘                 │
  │   {access, refresh, user} │                           │
  │<──────────────────────────┤                           │
  │                           │                           │
```

### 3. Protected Request Flow

```
Client                      Server                    Database
  │                           │                           │
  │   GET /api/auth/user/     │                           │
  │   Header: Bearer <token>  │                           │
  ├──────────────────────────>│                           │
  │                           │   Verify JWT token        │
  │                           ├─────────┐                 │
  │                           │         │                 │
  │                           │<────────┘                 │
  │                           │   Get user data           │
  │                           ├─────────────────────────> │
  │                           │<────────────────────────┤ │
  │   {user data}             │                           │
  │<──────────────────────────┤                           │
  │                           │                           │
```

### 4. Token Refresh Flow

```
Client                      Server                    Database
  │                           │                           │
  │   POST /api/auth/token/   │                           │
  │   refresh/                │                           │
  │   {refresh: "token..."}   │                           │
  ├──────────────────────────>│                           │
  │                           │   Verify refresh token    │
  │                           ├─────────────────────────> │
  │                           │<────────────────────────┤ │
  │                           │   Generate new tokens     │
  │                           ├─────────┐                 │
  │                           │         │                 │
  │                           │<────────┘                 │
  │                           │   Blacklist old refresh   │
  │                           ├─────────────────────────> │
  │   {access, refresh}       │                           │
  │<──────────────────────────┤                           │
  │                           │                           │
```

### 5. Logout Flow

```
Client                      Server                    Database
  │                           │                           │
  │   POST /api/auth/logout/  │                           │
  │   {refresh: "token..."}   │                           │
  │   Header: Bearer <token>  │                           │
  ├──────────────────────────>│                           │
  │                           │   Verify tokens           │
  │                           ├─────────────────────────> │
  │                           │<────────────────────────┤ │
  │                           │   Blacklist refresh token │
  │                           ├─────────────────────────> │
  │   {message: "Success"}    │                           │
  │<──────────────────────────┤                           │
  │                           │                           │
```

### 6. Google OAuth Flow

```
Flutter App              Server                Google              Database
    │                      │                      │                    │
    │   User clicks        │                      │                    │
    │   "Sign in Google"   │                      │                    │
    ├──────────┐           │                      │                    │
    │          │           │                      │                    │
    │<─────────┘           │                      │                    │
    │   Open Google Auth   │                      │                    │
    ├─────────────────────────────────────────────>│                    │
    │                      │   User authenticates │                    │
    │                      │   on Google          │                    │
    │<───────────────────────────────────────────┤ │                    │
    │   Receive access     │                      │                    │
    │   token from Google  │                      │                    │
    │                      │                      │                    │
    │   POST /api/auth/    │                      │                    │
    │   login/google/      │                      │                    │
    │   {access_token}     │                      │                    │
    ├─────────────────────>│                      │                    │
    │                      │   Verify with Google │                    │
    │                      ├─────────────────────>│                    │
    │                      │<───────────────────┤ │                    │
    │                      │   Get/Create user    │                    │
    │                      ├────────────────────────────────────────> │
    │                      │   Generate JWT tokens│                    │
    │                      ├──────────┐           │                    │
    │                      │          │           │                    │
    │                      │<─────────┘           │                    │
    │   {access, refresh,  │                      │                    │
    │    user}             │                      │                    │
    │<─────────────────────┤                      │                    │
    │                      │                      │                    │
```

## 🏗️ Architecture Layers

```
┌───────────────────────────────────────────────────────────┐
│                     Presentation Layer                     │
│              (Swagger UI, API Documentation)               │
└───────────────────────────────────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────┐
│                      API Layer (Views)                     │
│   RegisterView | LoginView | LogoutView | SocialAuth      │
└───────────────────────────────────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────┐
│                   Business Logic Layer                     │
│         (Serializers - Validation & Processing)            │
│   RegisterSerializer | LoginSerializer | Validators        │
└───────────────────────────────────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────┐
│                     Data Access Layer                      │
│                    (Models & Managers)                     │
│              User Model | UserManager                      │
└───────────────────────────────────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────┐
│                      Database Layer                        │
│          (SQLite/PostgreSQL/MySQL/etc.)                    │
└───────────────────────────────────────────────────────────┘
```

## 🔐 Security Flow

```
┌────────────────────────────────────────────────────────────┐
│                      Security Measures                      │
└────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Password   │    │  JWT Tokens  │    │     CORS     │
│  Validation  │    │   & Signing  │    │   Headers    │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
    Min length          HS256 algo        Allow origins
    Common check        Secret key        Credentials
    Numeric check       Expiration        Preflight
    Similarity          Blacklist
```

## 📦 Component Relationships

```
core/settings.py
    │
    ├─── Configures ───> Django REST Framework
    │                    └── Authentication: JWT
    │                    └── Permissions: IsAuthenticated
    │                    └── Schema: drf-spectacular
    │
    ├─── Configures ───> Simple JWT
    │                    └── Token lifetime
    │                    └── Rotation & Blacklisting
    │                    └── Algorithm: HS256
    │
    ├─── Configures ───> CORS
    │                    └── Allowed origins
    │                    └── Credentials
    │
    └─── Configures ───> Social Auth
                         └── Google OAuth
                         └── Apple Sign In

src/accounts/
    │
    ├── models.py ────> Custom User Model
    │                   └── Email as username
    │                   └── Auth provider field
    │                   └── UserManager
    │
    ├── serializers.py ─> Validation & Transform
    │                     └── RegisterSerializer
    │                     └── LoginSerializer
    │                     └── SocialAuth Serializers
    │
    ├── views.py ──────> API Endpoints
    │                    └── RegisterView
    │                    └── LoginView
    │                    └── LogoutView
    │                    └── SocialAuthViews
    │
    ├── urls.py ───────> URL Routing
    │                    └── Maps URLs to views
    │
    └── admin.py ──────> Admin Interface
                         └── User management
```

## 🎯 Data Flow Summary

```
1. Client Request
   └─> Django URL Router
       └─> View (Authentication & Authorization)
           └─> Serializer (Validation)
               └─> Model (Database Operations)
                   └─> Response
                       └─> JSON with Tokens/Data
```

## 🔄 Token Rotation Strategy

```
Login/Register
    │
    ├─> Generate Access Token (60 min)
    └─> Generate Refresh Token (7 days)
             │
             ├─> Store in database (Outstanding Tokens)
             │
             └─> Client receives both tokens
                      │
                      ├─> Use Access Token for API calls
                      │
                      └─> When Access expires (60 min)
                           │
                           └─> Call /token/refresh/
                                │
                                ├─> New Access Token
                                ├─> New Refresh Token
                                └─> Old Refresh → Blacklisted
```

## 🌐 Complete Endpoint Map

```
http://localhost:8000/
│
├── /admin/                    [Django Admin Panel]
│
├── /api/
│   ├── /docs/                 [Swagger UI] ⭐
│   ├── /redoc/                [ReDoc Documentation]
│   ├── /schema/               [OpenAPI JSON Schema]
│   │
│   └── /auth/
│       ├── /register/         [POST] Register
│       ├── /login/            [POST] Login
│       ├── /logout/           [POST] Logout 🔒
│       ├── /token/refresh/    [POST] Refresh Token
│       │
│       ├── /user/             [GET] Get User 🔒
│       ├── /user/delete/      [DELETE] Delete User 🔒
│       │
│       ├── /login/google/     [POST] Google OAuth
│       └── /login/apple/      [POST] Apple Sign In

🔒 = Requires Authentication (Bearer Token)
⭐ = Start here!
```

---

## 🚀 Start Testing

Open: **http://localhost:8000/api/docs/**

All flows are documented and testable through Swagger UI!

