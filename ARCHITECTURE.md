# Auth API Architecture

## 🎯 Design Philosophy

**Ultra-Minimalistic Token Factory**

The Auth API has ONE job: manage user identity and issue tokens. Nothing more.

- ❌ No user profile management
- ❌ No roles or permissions
- ❌ No business logic
- ✅ ONLY authentication and token issuance

## 🏗️ Architecture Overview

```
┌────────────────────────────────────────────────────────┐
│                   Auth API (FastAPI)                   │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │              Route Layer                          │ │
│  │  /register  /login  /verify  /refresh  /logout   │ │
│  │  /resend-verification  /reset-password           │ │
│  └──────────────────────────────────────────────────┘ │
│                         │                              │
│  ┌──────────────────────▼───────────────────────────┐ │
│  │           Service Layer                          │ │
│  │  - AuthService                                   │ │
│  │  - EmailService (HTTP client)                    │ │
│  │  - VerificationService                           │ │
│  └──────────────────────────────────────────────────┘ │
│                         │                              │
│  ┌──────────────────────▼───────────────────────────┐ │
│  │           Core Components                        │ │
│  │  - Security (Argon2id hashing)                   │ │
│  │  - Tokens (JWT generation/validation)            │ │
│  │  - RedisClient (token storage)                   │ │
│  └──────────────────────────────────────────────────┘ │
│                         │                              │
│  ┌──────────────────────▼───────────────────────────┐ │
│  │        Database Layer (Stored Procedures)        │ │
│  │  - sp_create_user                                │ │
│  │  - sp_get_user_by_email                          │ │
│  │  - sp_verify_user_email                          │ │
│  │  - sp_update_password                            │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
                      │                    │
          ┌───────────┴───────┐   ┌────────┴─────────┐
          ▼                   ▼   ▼                  ▼
    ┌──────────┐        ┌──────────┐        ┌──────────┐
    │PostgreSQL│        │  Redis   │        │  Email   │
    │  (SP's)  │        │ (tokens) │        │ Service  │
    └──────────┘        └──────────┘        └──────────┘
```

## 🔐 Security Architecture

### 1. Password Security

```
Plain Password → Argon2id Hash → PostgreSQL
                 (pwdlib)       (stored procedure)
```

**Key Points:**
- Argon2id = PHC winner, GPU/side-channel resistant
- Hashing happens in Python, NOT in database
- No password ever sent to database unhashed

### 2. Token Architecture

```
User Login → Generate Tokens → Return to User
             │
             ├─ Access Token (JWT, 15 min)
             │  Payload: {sub: user_id, exp: timestamp}
             │
             └─ Refresh Token (JWT, 30 days)
                Payload: {sub: user_id, jti: unique_id, exp: timestamp}
```

**Token Flow:**

```
1. Login Success
   └─> Generate: Access Token + Refresh Token
   └─> Return both to client

2. Access Token Expires (15 min)
   └─> Client calls /refresh with Refresh Token
   └─> Check: is JTI blacklisted?
       └─> NO: Generate new tokens + Blacklist old JTI
       └─> YES: Return 401 Unauthorized

3. Logout
   └─> Client calls /logout with Refresh Token
   └─> Extract JTI → Add to Redis blacklist
   └─> Token can no longer be used
```

### 3. Redis Token Storage

**Key Pattern:**

```
Purpose              | Key                    | Value    | TTL
---------------------|------------------------|----------|--------
Email Verification   | verify_token:{token}   | user_id  | 24h
Verification Lookup  | verify_user:{user_id}  | token    | 24h
Password Reset       | reset_token:{token}    | user_id  | 1h
Reset Lookup         | reset_user:{user_id}   | token    | 1h
Token Blacklist      | blacklist_jti:{jti}    | "1"      | 30d
```

**Why Reverse Lookup?**

```
Problem: User requests verification email 3 times
         → 3 active tokens exist
         → Confusing UX

Solution: verify_user:{user_id} → token
          When new token created, delete old one
          → Only 1 active token per user
```

## 📊 Data Flow Examples

### Example 1: Registration Flow

```
1. POST /auth/register
   Input: {email, password}
   │
   ├─> Hash password (Argon2id)
   ├─> Call sp_create_user(email, hashed_password)
   │   └─> PostgreSQL: INSERT INTO users (is_verified=FALSE)
   │
   ├─> Generate verification_token (random 32 bytes)
   ├─> Store in Redis:
   │   ├─> SET verify_token:{token} = user_id (TTL 24h)
   │   └─> SET verify_user:{user_id} = token (TTL 24h)
   │
   ├─> Send email (background task)
   │   └─> POST to Email Service
   │       Body: {to: email, template: "verification", data: {link}}
   │
   └─> Return: {message: "Check your email"}
       (NO TOKENS RETURNED!)
```

### Example 2: Login Flow (Hard Verification)

```
1. POST /auth/login
   Input: {username: email, password}
   │
   ├─> Call sp_get_user_by_email(email)
   │   └─> PostgreSQL: SELECT * FROM users WHERE email = ...
   │
   ├─> Verify password
   │   └─> pwdlib.verify(plain, hashed_password)
   │       └─> NO MATCH: Return 401 "Invalid credentials"
   │
   ├─> CHECK: is_verified = TRUE?
   │   └─> FALSE: Return 403 "Email not verified"
   │
   ├─> CHECK: is_active = TRUE?
   │   └─> FALSE: Return 403 "Account deactivated"
   │
   ├─> Update last_login_at
   │   └─> Call sp_update_last_login(user_id)
   │
   ├─> Generate tokens
   │   ├─> Access Token: {sub: user_id, exp: +15min}
   │   └─> Refresh Token: {sub: user_id, jti: random, exp: +30d}
   │
   └─> Return: {access_token, refresh_token, token_type: "bearer"}
```

### Example 3: Token Refresh Flow (with Rotation)

```
1. POST /auth/refresh
   Input: {refresh_token}
   │
   ├─> Decode token
   │   ├─> Extract: user_id, jti
   │   └─> Validate: signature, expiration
   │
   ├─> CHECK: Is JTI blacklisted?
   │   └─> GET blacklist_jti:{jti} from Redis
   │       └─> EXISTS: Return 401 "Token revoked"
   │
   ├─> Call sp_get_user_by_id(user_id)
   │   └─> Verify: is_active AND is_verified
   │       └─> FALSE: Return 403
   │
   ├─> BLACKLIST OLD TOKEN (critical!)
   │   └─> SET blacklist_jti:{jti} = "1" (TTL 30d)
   │
   ├─> Generate NEW tokens
   │   ├─> New Access Token (15 min)
   │   └─> New Refresh Token (30 days, NEW JTI)
   │
   └─> Return: {access_token, refresh_token}
```

## 🚦 Rate Limiting Strategy

```
Endpoint                      | Limit      | Rationale
------------------------------|------------|---------------------------
POST /auth/register           | 3/hour     | Prevent spam accounts
POST /auth/login              | 5/minute   | Brute-force protection
POST /auth/resend-verification| 1/5min     | Prevent email spam
POST /auth/request-reset      | 1/5min     | Prevent email spam
Others                        | None       | Low risk
```

**Implementation:**
- SlowAPI middleware (Redis-backed)
- Rate limits per IP address
- Returns 429 with retry_after header

## 🔄 Integration Points

### 1. PostgreSQL (Stored Procedures)

**Contract:**
- Auth API ONLY calls stored procedures
- No raw SQL queries allowed
- Database team maintains SP implementation
- Auth API expects specific signatures (see README)

### 2. Redis

**Usage:**
- Temporary token storage (verification, reset)
- Refresh token blacklist
- Rate limiting state

**Why Redis?**
- Automatic TTL cleanup
- O(1) lookups
- High throughput for token checks

### 3. Email Service

**Contract:**
```http
POST {EMAIL_SERVICE_URL}/send
Content-Type: application/json

{
  "to": "user@example.com",
  "template": "email_verification",
  "subject": "Verify your email",
  "data": {
    "verification_link": "https://app.com/verify?token=xxx"
  }
}
```

**Templates Used:**
- `email_verification`: Sent on registration
- `password_reset`: Sent on reset request
- `welcome` (optional): Sent after verification

### 4. Activity API (Consumer)

**How Activity API Uses Auth API:**

```python
# 1. User logs in via Auth API
response = POST /auth/login → {access_token, refresh_token}

# 2. Activity API validates token
from jose import jwt

payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])
user_id = UUID(payload["sub"])

# 3. Activity API uses user_id in queries
activities = db.activities.find({"owner_id": user_id})
```

## 🎨 Design Decisions

### Why Hard Verification?

**Alternative: Soft Verification**
- User can login immediately
- Some features locked until verified
- Lower friction, but spam risk

**Our Choice: Hard Verification**
- MUST verify before login
- Clean user base
- No unverified spam accounts

**Reasoning:**
- Activity app is social → quality matters
- Email verification filters bots
- One-time friction vs ongoing spam

### Why Stored Procedures Only?

**Alternatives:**
1. ORM (SQLAlchemy, SQLModel)
2. Query Builder
3. Raw SQL

**Our Choice: Stored Procedures**

**Reasons:**
- Separation of concerns (DB team owns schema)
- Better for CQRS architecture
- Easier to audit (all DB logic in one place)
- Can optimize without changing API code
- Fits with PostgreSQL best practices

### Why Redis for Tokens?

**Alternative: Database Table**

```sql
CREATE TABLE verification_tokens (
    token VARCHAR PRIMARY KEY,
    user_id UUID,
    expires_at TIMESTAMP
);
```

**Our Choice: Redis**

**Reasons:**
- Automatic cleanup via TTL
- No need for cron jobs
- O(1) lookups (faster than DB)
- Redis already needed for rate limiting
- Tokens are ephemeral by nature

## 📈 Scalability Considerations

### Horizontal Scaling

**Stateless Design:**
- No session state in API
- All state in PostgreSQL/Redis
- Can run multiple instances

**Load Balancing:**
```
                  ┌────────┐
Internet ─────────> LB     │
                  └───┬────┘
                      │
         ┌────────────┼────────────┐
         ▼            ▼            ▼
    [Auth API]   [Auth API]   [Auth API]
         │            │            │
         └────────────┼────────────┘
                      │
         ┌────────────┼────────────┐
         ▼            ▼            ▼
    [PostgreSQL]  [Redis]   [Email Service]
```

### Database Scaling

**Read Replicas:**
- Most endpoints are reads (login, refresh)
- Can add read replicas for sp_get_user_*
- Write to primary (register, verify)

**Partitioning:**
- If > 100M users, partition by user_id range
- But unlikely for activity app

### Redis Scaling

**Current Setup:**
- Single Redis instance (sufficient for most cases)

**If Needed:**
- Redis Cluster (horizontal scaling)
- Redis Sentinel (high availability)

## 🐛 Error Handling Philosophy

### Security-First Error Messages

**Bad:**
```json
{"detail": "User not found"}          // Reveals email exists
{"detail": "Password incorrect"}      // Reveals email exists
{"detail": "Email not verified"}      // Reveals email + status
```

**Good:**
```json
{"detail": "Invalid credentials"}     // Generic for login
{"detail": "If account exists..."}    // Generic for reset
```

**Exception:** 403 after successful auth
```json
{"detail": "Email not verified. Check your inbox..."}
```

**Rationale:**
- User already authenticated (password correct)
- Can safely tell them WHY they can't proceed
- Prevents frustration ("Why can't I login?")

## 🧪 Testing Strategy

### Unit Tests
- `test_security.py`: Password hashing
- `test_tokens.py`: JWT generation/validation
- `test_redis_client.py`: Token storage

### Integration Tests
- `test_register.py`: Full registration flow
- `test_login.py`: Login with verification checks
- `test_refresh.py`: Token rotation
- `test_password_reset.py`: Reset flow

### Load Tests
- Login endpoint: 100 req/sec
- Refresh endpoint: 200 req/sec
- Redis token checks: < 5ms p99

## 📚 Further Reading

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [Argon2 RFC](https://datatracker.ietf.org/doc/html/rfc9106)
- [Redis Best Practices](https://redis.io/docs/management/optimization/)
