# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ultra-minimalistic authentication service for the Activity App. Built with **FastAPI** (Python), **PostgreSQL** (stored procedures only), **Redis**, and integrated with centralized observability stack (Prometheus, Loki, Grafana).

**Core Philosophy**: Token factory only - no user profiles, no business logic, ONLY authentication and token issuance.

## Common Commands

### Development

```bash
# Start all services (auth-api connects to external PostgreSQL + Redis)
docker compose up -d

# View API logs
docker compose logs -f auth-api

# Rebuild after code changes (CRITICAL - restart alone doesn't update code)
docker compose build auth-api && docker compose restart auth-api

# Run backend locally (without Docker)
cd /mnt/d/activity/auth-api
export $(cat .env | xargs)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run all tests
make test

# Run by test type
make test-unit          # Fast, mocked tests (~5s)
make test-integration   # Real DB/Redis tests (~30s)
make test-e2e           # Full API tests (~60s, requires API running)

# Run with coverage (enforces 85% minimum)
make test-cov

# Run specific test file
make test-file FILE=tests/unit/test_auth_service.py

# Run specific test method
make test-single TEST=tests/unit/test_auth_service.py::TestAuthService::test_login

# Run tests in parallel (faster)
make test-parallel

# Security & resilience tests
make test-security      # JWT forgery, replay attacks
make test-resilience    # Chaos engineering, DB atomicity

# Reset test database (clean state)
make test-reset

# Clean test artifacts
make clean
```

### Code Quality

```bash
# Format code
black app/ tests/
isort app/ tests/

# Type checking
mypy app/
```

## Architecture Overview

### Database-First Design (Stored Procedures Only)

**ALL** database operations go through PostgreSQL stored procedures in the `activity` schema:

```
Python Service → sp_create_user() → PostgreSQL
Python Service → sp_get_user_by_email() → PostgreSQL
Python Service → sp_verify_user_email() → PostgreSQL
```

**Why stored procedures?**
- Database team owns schema and business logic
- Better for CQRS architecture
- Easier to audit (all DB logic centralized)
- Can optimize without changing API code
- Separation of concerns

**Required stored procedures:**
- `sp_create_user(email, hashed_password)` - Create user (is_verified=FALSE)
- `sp_get_user_by_email(email)` - Fetch user by email
- `sp_get_user_by_id(user_id)` - Fetch user by ID
- `sp_verify_user_email(user_id)` - Mark email verified
- `sp_update_password(user_id, hashed_password)` - Update password
- `sp_save_refresh_token()` - Store refresh token
- `sp_validate_refresh_token()` - Check token validity
- `sp_revoke_refresh_token()` - Blacklist token

See `app/db/procedures.py` for Python wrappers around stored procedures.

### Code Organization

```
app/
├── main.py              # FastAPI app, middleware, exception handlers
├── config.py            # Environment configuration (Pydantic settings)
│
├── core/                # Reusable utilities
│   ├── security.py      # Argon2id password hashing (pwdlib)
│   ├── tokens.py        # JWT generation/validation (jose)
│   ├── redis_client.py  # Redis connection + token storage
│   ├── logging_config.py # Structlog JSON logging
│   ├── rate_limiting.py # SlowAPI rate limiter setup
│   ├── metrics.py       # Prometheus metrics
│   └── exceptions.py    # Custom exception classes
│
├── db/                  # Database layer
│   ├── connection.py    # PostgreSQL connection pool (asyncpg)
│   └── procedures.py    # Stored procedure Python wrappers
│
├── middleware/          # Request/response middleware
│   ├── correlation.py   # Trace ID injection (X-Trace-ID header)
│   ├── security.py      # Security headers (CSP, HSTS, etc.)
│   └── request_size_limit.py # Request body size limits
│
├── routes/              # API endpoints (thin routing layer)
│   ├── register.py      # POST /auth/register
│   ├── login.py         # POST /auth/login
│   ├── refresh.py       # POST /auth/refresh (token rotation)
│   ├── logout.py        # POST /auth/logout (blacklist)
│   ├── verify.py        # GET /auth/verify?token=xxx
│   ├── password_reset.py # POST /auth/request-password-reset, /auth/reset-password
│   ├── twofa.py         # POST /auth/2fa/* (2FA/TOTP endpoints)
│   └── dashboard.py     # GET /dashboard (admin metrics)
│
├── services/            # Business logic layer
│   ├── auth_service.py          # Login, logout, token refresh
│   ├── registration_service.py  # User registration flow
│   ├── password_service.py      # Password hashing
│   ├── password_validation_service.py  # zxcvbn + HIBP breach check
│   ├── password_reset_service.py # Password reset flow
│   ├── token_service.py         # JWT token management
│   ├── email_service.py         # Email service HTTP client
│   └── two_factor_service.py    # 2FA/TOTP management
│
└── schemas/             # Pydantic models for API requests/responses
    ├── auth.py          # LoginRequest, TokenResponse, etc.
    └── user.py          # UserCreate, UserResponse
```

### Key Architectural Patterns

**1. Hard Email Verification**
- Users MUST verify email before login
- Registration returns 201 but NO tokens
- Login returns 403 if not verified
- Rationale: Activity app is social → quality matters, filters bots

**2. JWT Token Architecture**
- Access Token: 15 minutes, stateless
- Refresh Token: 30 days, single-use with JTI blacklist
- Token rotation: Old refresh token blacklisted immediately on refresh
- Logout: Blacklist refresh token JTI in Redis

**3. Redis Token Storage**
```
verify_token:{token} → user_id (TTL: 24h)
verify_user:{user_id} → token (TTL: 24h)    # Reverse lookup (only 1 active token)
reset_token:{token} → user_id (TTL: 1h)
reset_user:{user_id} → token (TTL: 1h)
blacklist_jti:{jti} → "1" (TTL: 30d)
```

**4. Password Security**
- Argon2id hashing (PHC winner, GPU-resistant)
- zxcvbn strength scoring (must achieve score 3-4)
- Have I Been Pwned breach check (613M+ breached passwords)
- Minimum 8 characters

**5. Rate Limiting (Redis-backed)**
```
/auth/register → 3/hour
/auth/login → 5/minute
/auth/resend-verification → 1/5min
/auth/request-password-reset → 1/5min
```

## Critical Development Patterns

### Always Rebuild Containers After Code Changes

**CRITICAL**: `docker compose restart` uses OLD code. You MUST rebuild:

```bash
# Wrong (restart uses old image)
docker compose restart auth-api

# Right (rebuild picks up code changes)
docker compose build auth-api && docker compose restart auth-api
```

### Stored Procedure Pattern

When adding new database operations:

1. **Define stored procedure in PostgreSQL** (coordinate with DB team)
2. **Add Python wrapper in `app/db/procedures.py`**:
```python
async def sp_your_operation(
    conn: asyncpg.Connection,
    param: str
) -> Optional[UserRecord]:
    result = await conn.fetchrow(
        "SELECT * FROM activity.sp_your_operation($1)",
        param
    )
    return UserRecord(result) if result else None
```
3. **Call from service layer** (not directly from routes)

### Service Layer Pattern

Services handle business logic and call stored procedures:

```python
# ✅ Right: Service layer calls stored procedures
class AuthService:
    async def login(self, email: str, password: str):
        user = await sp_get_user_by_email(self.db, email)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        if not user.is_verified:
            raise AccountNotVerifiedError()

        # Generate tokens, update last_login, etc.
        return tokens

# ❌ Wrong: Routes directly calling stored procedures
@router.post("/login")
async def login(db: asyncpg.Connection):
    user = await sp_get_user_by_email(db, email)  # Skip this - use service
```

### Exception Handling Pattern

Use domain-specific exceptions for security:

```python
# ✅ Right: Generic error messages (no user enumeration)
raise InvalidCredentialsError()  # Returns "Invalid credentials"

# ❌ Wrong: Reveals information
raise Exception("User not found")  # Reveals email exists
raise Exception("Password incorrect")  # Reveals email exists but wrong password
```

**Exception:** After successful authentication, be specific:
```python
# ✅ OK: User already authenticated (password correct)
if not user.is_verified:
    raise AccountNotVerifiedError("Email not verified. Check your inbox...")
```

### Logging Pattern

Use structured logging with trace IDs:

```python
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# ✅ Right: Structured logging
logger.info("user_login_success",
           user_id=str(user.id),
           email=user.email,
           ip_address=request.client.host)

# ❌ Wrong: String interpolation
logger.info(f"User {user.id} logged in from {ip}")
```

**Security note:** Never log passwords, tokens, or sensitive data.

## Testing Strategy

### Test Pyramid

```
     E2E Tests (20%)
    /            \
   /   Integration  \
  /    Tests (30%)   \
 /____________________\
   Unit Tests (50%)
```

**Unit Tests** (`tests/unit/`)
- Fast (<5s total), mocked dependencies
- Test services in isolation
- Use `@pytest.mark.unit`
- Example: `test_password_validation_service.py`

**Integration Tests** (`tests/integration/`)
- Real PostgreSQL + Redis
- Full user flows
- Transaction testing, race conditions
- Use `@pytest.mark.integration`
- Example: `test_registration_flow.py`, `test_resilience.py`

**E2E Tests** (`tests/e2e/`)
- Full HTTP flow through FastAPI
- Real API endpoints
- Security validation, rate limiting
- Use `@pytest.mark.e2e`
- Example: `test_login_flow.py`, `test_2fa_flow.py`

### Key Test Files

**Security Tests:**
- `tests/unit/test_security_adversarial.py` - JWT forgery, replay attacks
- `tests/unit/test_security_edge_cases.py` - Edge cases, malformed input

**Resilience Tests:**
- `tests/integration/test_resilience.py` - DB/Redis atomicity, failure scenarios
- `tests/integration/test_concurrency.py` - Race conditions, parallel requests

**Flow Tests:**
- `tests/e2e/test_login_flow.py` - Full login flow
- `tests/e2e/test_token_refresh_flow.py` - Token rotation
- `tests/e2e/test_rate_limiting.py` - Rate limit enforcement

### Coverage Requirements

- Minimum: 85% (enforced by pytest.ini)
- Target: 90%+ across all critical paths
- Run `make test-cov` to check coverage

## Observability Integration

Auth API is integrated with centralized Activity App observability stack:

**Prometheus Metrics:**
- Exposed at `/metrics` endpoint
- Service discovery via Docker labels
- Metrics: request count, latency, error rate

**Structured Logging:**
- JSON format with ISO 8601 timestamps
- Trace ID injection (`X-Trace-ID` header)
- Log levels: DEBUG, INFO, WARNING, ERROR

**Health Checks:**
- Primary: `GET /health`
- Legacy: `GET /api/health` (backward compatibility)

**Monitoring Targets:**
- Login success/failure rates
- Token refresh rates
- Rate limit hits
- Password validation failures
- Email service errors

## Configuration

All configuration via environment variables (see `.env.example`).

**Critical Production Settings:**

```bash
# MUST change (generate with: python -c "import secrets; print(secrets.token_urlsafe(64))")
JWT_SECRET_KEY=your-secure-random-key-min-32-chars

# MUST change for 2FA encryption
ENCRYPTION_KEY=your-32-byte-base64-encoded-key

# Database connection (external PostgreSQL)
POSTGRES_HOST=activity-postgres-db
POSTGRES_DB=activitydb
POSTGRES_SCHEMA=activity

# Redis connection
REDIS_HOST=auth-redis

# Email service
EMAIL_SERVICE_URL=http://email-api:8010
SERVICE_AUTH_TOKEN=your-service-token

# Frontend URL (for email links)
FRONTEND_URL=https://your-app.com
```

## API Endpoints

| Method | Endpoint | Auth | Rate Limit | Description |
|--------|----------|------|------------|-------------|
| POST | `/auth/register` | No | 3/hour | Register new user |
| GET | `/auth/verify?token=xxx` | No | - | Verify email |
| POST | `/auth/resend-verification` | No | 1/5min | Resend verification email |
| POST | `/auth/login` | No | 5/min | Login (requires verified email) |
| POST | `/auth/refresh` | Refresh Token | - | Refresh access token (rotates tokens) |
| POST | `/auth/logout` | Refresh Token | - | Logout (blacklist refresh token) |
| POST | `/auth/request-password-reset` | No | 1/5min | Request password reset |
| POST | `/auth/reset-password` | No | - | Reset password with token |
| POST | `/auth/2fa/setup` | Access Token | - | Setup 2FA/TOTP |
| POST | `/auth/2fa/verify` | Access Token | - | Verify 2FA setup |
| POST | `/auth/2fa/enable` | Access Token | - | Enable 2FA |
| POST | `/auth/2fa/login` | No | - | Login with 2FA code |
| GET | `/health` | No | - | Health check |
| GET | `/metrics` | No | - | Prometheus metrics |

## Troubleshooting

**Container code not updating:**
```bash
# Always rebuild after code changes
docker compose build auth-api && docker compose restart auth-api
```

**Database connection errors:**
```bash
# Check external PostgreSQL is running
docker network inspect activity-network

# Verify stored procedures exist
docker exec activity-postgres-db psql -U activity_user -d activitydb -c "\df activity.*"
```

**Redis connection errors:**
```bash
# Check Redis is healthy
docker compose ps redis
docker exec auth-redis redis-cli ping

# Check verification tokens
docker exec auth-redis redis-cli KEYS "verify_token:*"
```

**Rate limiting not working:**
```bash
# Verify Redis connection (rate limiting requires Redis)
docker exec auth-redis redis-cli KEYS "slowapi:*"
```

**Tests failing:**
```bash
# Reset test database to clean state
make test-reset

# Run specific test type
make test-unit  # Fast tests only
```

## Security Considerations

**Token Security:**
- JWT_SECRET_KEY must be ≥32 characters
- Refresh tokens are single-use (blacklisted on refresh)
- Access tokens are stateless (15 min expiry)
- All tokens use HS256 algorithm

**Password Security:**
- Argon2id hashing (never plain text)
- zxcvbn strength validation
- HIBP breach checking
- Generic error messages (no user enumeration)

**Request Security:**
- Request size limits enforced
- Rate limiting on sensitive endpoints
- CORS configured for frontend only
- Security headers (CSP, HSTS, X-Frame-Options)

**Input Validation:**
- All inputs validated via Pydantic schemas
- Email normalization (lowercase)
- SQL injection prevented (stored procedures only)
- XSS prevented (API-only, no HTML rendering)

## External Dependencies

**PostgreSQL** (external, shared database):
- Expected schema: `activity.users` table
- Required stored procedures (see README.md)
- Connection pool: 5-20 connections

**Redis** (local to auth-api):
- Used for: token storage, rate limiting
- Persistence: AOF + RDB snapshots
- Memory limit: 256MB (LRU eviction)

**Email Service** (external):
- Expected endpoint: `POST /send`
- Templates: email_verification, password_reset, 2fa_code
- Timeout: 10 seconds

**Network** (external):
- Network name: `activity-network`
- Created by central docker compose
- Shared by: postgres, redis, email-api, auth-api
