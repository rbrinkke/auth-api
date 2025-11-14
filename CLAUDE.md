# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Auth API** is a FastAPI-based authentication service for the Activity Platform. It serves as a token factory focused exclusively on authentication and JWT token issuance - no user profiles or business logic.

**Core Philosophy**: Database team owns schema through stored procedures. All database operations go through PostgreSQL stored procedures in the `activity` schema.

**Key Technologies**: FastAPI, PostgreSQL (stored procedures), Redis, asyncpg, JWT, Argon2id password hashing

## Critical Development Patterns

### 🔴 Always Rebuild Docker After Code Changes

**CRITICAL**: `docker compose restart` uses the OLD image. You MUST rebuild:

```bash
# Wrong (uses cached old code)
docker compose restart auth-api

# Right (picks up new code)
docker compose build auth-api && docker compose restart auth-api

# Force rebuild without cache (use after significant changes)
docker compose build --no-cache auth-api && docker compose restart auth-api
```

**When to rebuild:**
- After ANY Python code changes
- After requirements.txt updates
- After .env changes
- After Dockerfile modifications

This is the #1 cause of "my fix didn't work" issues. Always rebuild!

### Stored Procedure Pattern (Required)

All database operations MUST go through stored procedures in `activity` schema:

```python
# Python wrapper in app/db/procedures.py
@log_stored_procedure
async def sp_create_user(
    conn: asyncpg.Connection,
    email: str,
    hashed_password: str
) -> UserRecord:
    result = await conn.fetchrow(
        "SELECT * FROM activity.sp_create_user($1, $2)",
        email.lower(),
        hashed_password
    )
    return UserRecord(result)
```

**Why stored procedures?**
- Database team owns schema evolution
- Better for CQRS architecture
- Easier auditing and optimization
- API changes don't require schema changes

**Never write raw SQL** - only call stored procedures via `app/db/procedures.py`

### JWT Token Architecture

**Token Types:**
1. **Access Token**: 15 minutes, used for API authentication
2. **Refresh Token**: 30 days, single-use with rotation
3. **Pre-auth Token**: Temporary token for 2FA flow

**Token Issuance Pattern:**
```python
# All tokens must include org_id for multi-org support
payload = {
    "sub": str(user_id),           # User ID (UUID)
    "org_id": str(org_id),          # Organization scope
    "exp": expiration_timestamp,
    "jti": unique_token_id          # For blacklist/rotation
}
```

**Critical**: `JWT_SECRET_KEY` MUST match across all services that validate tokens (auth-api, chat-api, image-api, etc.)

### Multi-Organization Login Flow

**3-Step Login Process:**

```bash
# Step 1: Password validation → sends email code
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "Password123!"
}
# Response: { "requires_code": true, "user_id": "...", "message": "..." }

# Step 2: Code validation → org selection (if multi-org user)
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "Password123!",
  "code": "123456"
}
# Response (multi-org): { "requires_org_selection": true, "organizations": [...] }
# Response (single-org): { "access_token": "...", "refresh_token": "..." }

# Step 3: Org selection → tokens (multi-org only)
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "Password123!",
  "code": "123456",
  "org_id": "650e8400-e29b-41d4-a716-446655440001"
}
# Response: { "access_token": "...", "refresh_token": "...", "org_id": "..." }
```

**Development Shortcut**: Set `SKIP_LOGIN_CODE=true` to skip email codes (Step 2 becomes optional)

### Security Patterns

**Generic Error Messages (Prevent User Enumeration):**

```python
# ✅ Right: Generic message
raise InvalidCredentialsError()  # Returns "Invalid credentials"

# ❌ Wrong: Reveals information
raise Exception("User not found")      # User enumeration attack vector
raise Exception("Password incorrect")  # Reveals email exists
```

**Exception After Authentication:**
```python
# ✅ OK: User already authenticated
if not user.is_verified:
    raise AccountNotVerifiedError("Email not verified. Check your inbox.")

# User knows they're authenticated, specific error is safe
```

**Password Security:**
- Argon2id hashing (PHC password hashing competition winner)
- zxcvbn strength validation (detects weak passwords)
- Have I Been Pwned breach checking (optional, requires network)

## Common Commands

### Development Workflow

```bash
# Start infrastructure (PostgreSQL, Redis - required first!)
cd /path/to/activity
./scripts/start-infra.sh

# Start auth-api
cd auth-api
docker compose up -d

# Watch logs
docker compose logs -f auth-api

# Rebuild after code changes (CRITICAL!)
docker compose build auth-api && docker compose restart auth-api

# Access container shell
docker exec -it auth-api bash

# Stop service
docker compose down
```

### Testing

```bash
# Run all tests
make test

# Run specific test types
make test-unit           # Fast, mocked tests (no DB/Redis)
make test-integration    # Real DB/Redis tests
make test-e2e           # Full HTTP flow tests

# Coverage report
make test-cov           # Terminal report (85% minimum)
make test-html          # HTML report → htmlcov/index.html

# Specific test file
make test-file FILE=tests/unit/test_password_validation_service.py

# Single test
make test-single TEST=tests/unit/test_auth_service.py::TestAuthService::test_login_success

# Test markers
make test-marker MARKER=unit
make test-marker MARKER=slow

# Clean test artifacts
make clean
```

### Database Operations

```bash
# Connect to PostgreSQL
docker exec -it activity-postgres-db psql -U postgres -d activitydb

# Inside psql:
\dn                                    # List schemas
\dt activity.*                         # List tables in activity schema
\df activity.*                         # List stored procedures
SELECT COUNT(*) FROM activity.users;   # Query users
```

### Redis Operations

```bash
# Connect to Redis
docker exec -it auth-redis redis-cli

# Inside redis-cli:
KEYS *                    # List all keys (dev only!)
GET verification:email:<email>
TTL verification:email:<email>
DEL verification:email:<email>
```

### Local Development (Without Docker)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For testing

# Set environment variables
export $(cat .env | xargs)

# Run locally
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access API
curl http://localhost:8000/health
open http://localhost:8000/docs  # Swagger UI
```

## Architecture

### Directory Structure

```
auth-api/
├── app/
│   ├── core/              # Core utilities
│   │   ├── security.py    # JWT, password hashing
│   │   ├── tokens.py      # Token generation/validation
│   │   ├── redis_client.py
│   │   ├── rate_limiting.py
│   │   └── exceptions.py
│   ├── db/
│   │   ├── connection.py  # PostgreSQL connection pool
│   │   └── procedures.py  # Stored procedure wrappers (CRITICAL)
│   ├── middleware/
│   │   ├── correlation.py # X-Correlation-ID tracking
│   │   ├── security.py    # Security headers
│   │   └── request_size_limit.py
│   ├── models/            # Pydantic models for stored procedure results
│   ├── routes/            # FastAPI route handlers
│   │   ├── login.py
│   │   ├── register.py
│   │   ├── organizations.py
│   │   ├── groups.py      # RBAC groups
│   │   ├── permissions.py # RBAC permissions
│   │   ├── oauth_*.py     # OAuth 2.0 endpoints
│   │   └── ...
│   ├── schemas/           # Request/response schemas
│   ├── services/          # Business logic
│   │   ├── auth_service.py
│   │   ├── organization_service.py
│   │   ├── authorization_service.py  # THE CORE - RBAC checks
│   │   ├── password_validation_service.py
│   │   └── ...
│   ├── config.py          # Settings (pydantic-settings)
│   └── main.py            # FastAPI app initialization
├── tests/
│   ├── unit/              # Fast, mocked tests
│   ├── integration/       # Real DB/Redis tests
│   └── e2e/               # Full HTTP flow tests
├── frontend-mocks/        # MSW mock handlers for frontend dev
├── Dockerfile             # Production-ready multi-stage build
├── docker-compose.yml     # Service + Redis
├── Makefile              # Test commands
└── requirements.txt       # Python dependencies
```

### Service Dependencies

**Required Infrastructure** (must start first):
- PostgreSQL (`activity-postgres-db` on port 5441)
- Redis (`activity-redis` on port 6379)
- Docker network: `activity-network`

**Optional Dependencies**:
- Email service (for verification codes - can skip in dev with `SKIP_LOGIN_CODE=true`)

### Key Architectural Decisions

**1. Stored Procedures Only**
- All database operations through `app/db/procedures.py`
- Database team owns schema evolution
- API remains stable even with schema changes

**2. Multi-Organization Scoping**
- Every token includes `org_id` claim
- Users can belong to multiple organizations
- Authorization checks are org-scoped

**3. RBAC Authorization**
- Groups contain users
- Permissions are granted to groups
- Authorization service checks: user → groups → permissions
- Core endpoint: `POST /api/v1/authorization/authorize`

**4. Token Rotation**
- Refresh tokens are single-use
- Each refresh returns new access + refresh tokens
- Old refresh token is blacklisted via JTI

**5. Generic Error Messages**
- Prevents user enumeration attacks
- Pre-authentication: Always generic ("Invalid credentials")
- Post-authentication: Can be specific (user already verified)

## Configuration

### Environment Variables (.env)

**Critical Settings (MUST configure):**
```bash
# JWT Secret (MUST match across all services!)
JWT_SECRET_KEY=your_very_long_secret_key_at_least_32_characters

# 2FA Encryption Key
ENCRYPTION_KEY=your_very_long_secret_key_for_2FA_at_least_32_characters

# Database Connection
POSTGRES_HOST=activity-postgres-db  # Docker container name
POSTGRES_PORT=5432
POSTGRES_DB=activitydb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_secure_password_change_in_prod
POSTGRES_SCHEMA=activity

# Redis
REDIS_HOST=auth-redis  # Docker container name
REDIS_PORT=6379
REDIS_DB=0

# Email Service
EMAIL_SERVICE_URL=http://email-api:8010
SERVICE_AUTH_TOKEN=st_dev_5555555555555555555555555555555555555555
```

**Development Shortcuts:**
```bash
DEBUG=true
SKIP_LOGIN_CODE=true  # Skip email verification codes
ENABLE_DOCS=true      # Enable Swagger UI (/docs)
LOG_LEVEL=DEBUG       # Verbose logging
```

**Production Settings:**
```bash
DEBUG=false
SKIP_LOGIN_CODE=false
ENABLE_DOCS=false  # Disable Swagger (security)
LOG_LEVEL=INFO
```

### Port Allocation

- **8000**: Auth API HTTP (exposed)
- **6380**: Redis (exposed, maps to container port 6379)

## Testing Strategy

### Test Organization

**Unit Tests** (`tests/unit/`):
- Fast, mocked dependencies
- Test individual functions/classes
- No database or Redis required
- Run with: `make test-unit`

**Integration Tests** (`tests/integration/`):
- Real PostgreSQL and Redis connections
- Test service integration
- Requires running infrastructure
- Run with: `make test-integration`

**E2E Tests** (`tests/e2e/`):
- Full HTTP flow testing
- Requires running API
- Tests complete user journeys
- Run with: `make test-e2e`

### Test Markers

```python
@pytest.mark.unit           # Fast, mocked
@pytest.mark.integration    # Real DB/Redis
@pytest.mark.e2e           # Full HTTP
@pytest.mark.slow          # Tests >5 seconds
@pytest.mark.async         # Async tests
```

### Coverage Requirements

**Minimum**: 85% coverage (enforced by `make test-cov`)

```bash
# Check coverage
make test-cov

# View HTML report
make test-html
open htmlcov/index.html
```

## OAuth 2.0 Provider

Auth API acts as an **OAuth 2.0 Authorization Server** for other services.

### Supported Grant Types

1. **Authorization Code** (with PKCE)
2. **Refresh Token**
3. **Password** (Resource Owner Password Credentials - dev only)

### OAuth Endpoints

```bash
# Discovery (OpenID Connect Discovery)
GET /.well-known/oauth-authorization-server

# Authorization (user consent)
GET /oauth/authorize?response_type=code&client_id=...&redirect_uri=...&code_challenge=...

# Token exchange
POST /oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=...&redirect_uri=...&code_verifier=...&client_id=...&client_secret=...

# Token revocation
POST /oauth/revoke
Content-Type: application/x-www-form-urlencoded

token=...&client_id=...&client_secret=...
```

### Registered OAuth Clients

Clients are defined in database via stored procedures. Example:

```sql
-- Register OAuth client (done by database team)
INSERT INTO activity.oauth_clients (client_id, client_secret, redirect_uris, ...)
VALUES ('image-api-v1', 'hashed_secret', ARRAY['http://localhost:8002/callback'], ...);
```

## RBAC Authorization System

### Core Concepts

**Organizations** → **Groups** → **Permissions**

- Users belong to Organizations with a role (owner/admin/member)
- Organizations contain Groups (e.g., "Administrators", "Content Creators")
- Groups are granted Permissions (e.g., "activity:create", "activity:delete")
- Users get permissions through group membership

### Authorization Flow

```python
# THE CORE: Check if user has permission in org
POST /api/v1/authorization/authorize
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "650e8400-e29b-41d4-a716-446655440001",
  "permission": "activity:create"
}

# Response:
{
  "authorized": true,
  "reason": "User has permission through group membership",
  "matched_groups": ["Administrators"]
}
```

### Permission Naming Convention

Format: `resource:action`

Examples:
- `activity:create` - Create activities
- `activity:update` - Update activities
- `activity:delete` - Delete activities
- `activity:read` - View activities
- `user:manage` - Manage users

### Group Management

```bash
# Create group
POST /api/auth/organizations/{org_id}/groups
{ "name": "Content Creators", "description": "..." }

# Add user to group
POST /api/auth/groups/{group_id}/members
{ "user_id": "..." }

# Grant permission to group
POST /api/auth/groups/{group_id}/permissions
{ "permission_id": "..." }
```

## Frontend Development

### MSW Mock Handlers

Complete Mock Service Worker handlers are available in `frontend-mocks/`:

```bash
# Copy handlers to frontend project
cp frontend-mocks/src/mocks/handlers.ts <your-frontend>/src/mocks/

# 100% API coverage with realistic behavior
# See frontend-mocks/README.md for complete documentation
```

**Test Accounts** (for mock handlers):
- `test@example.com` / `Password123!` (multi-org user)
- `admin@acme.com` / `Password123!` (single org, admin)
- `unverified@example.com` / `Password123!` (unverified)

## Troubleshooting

### "Code changes not taking effect"

```bash
# ALWAYS rebuild after code changes
docker compose build auth-api && docker compose restart auth-api
```

### "Database connection failed"

```bash
# Check PostgreSQL is running
docker ps | grep activity-postgres-db

# Check connection settings
cat .env | grep POSTGRES_

# Test connection
docker exec activity-postgres-db psql -U postgres -d activitydb -c "SELECT 1;"
```

### "Redis connection failed"

```bash
# Check Redis is running
docker ps | grep auth-redis

# Test connection
docker exec auth-redis redis-cli ping
# Expected: PONG
```

### "JWT validation fails in other services"

```bash
# Check JWT_SECRET_KEY matches across all services
cat .env | grep JWT_SECRET_KEY
cat ../chat-api/.env | grep JWT_SECRET_KEY
cat ../image-api/.env | grep JWT_SECRET_KEY

# They MUST be identical!
```

### "Tests failing with database errors"

```bash
# Reset test database
make test-reset

# Ensure clean isolation
make test-isolation
```

### "Import errors in Python"

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=/path/to/auth-api

# Or use python -m
python -m pytest tests/unit/

# In Docker, PYTHONPATH=/app (already set)
```

## Production Deployment Checklist

Before deploying to production:

**Security:**
- [ ] Change `JWT_SECRET_KEY` to 64+ char random string
- [ ] Change `ENCRYPTION_KEY` to 64+ char random string
- [ ] Change all database passwords
- [ ] Change Redis password
- [ ] Set `DEBUG=false`
- [ ] Set `ENABLE_DOCS=false` (disable Swagger)
- [ ] Set `SKIP_LOGIN_CODE=false`
- [ ] Configure CORS_ORIGINS for production domains
- [ ] Review rate limiting settings

**Infrastructure:**
- [ ] Use managed PostgreSQL (e.g., AWS RDS)
- [ ] Use managed Redis (e.g., AWS ElastiCache)
- [ ] Configure HTTPS/TLS termination
- [ ] Setup monitoring (Prometheus metrics exposed at `/metrics`)
- [ ] Configure log aggregation (structured JSON logs)
- [ ] Setup automated backups

**Testing:**
- [ ] Run full test suite: `make test-all`
- [ ] Verify coverage: `make test-cov` (85%+ required)
- [ ] Load testing on token endpoints
- [ ] Security audit (penetration testing)

## Additional Documentation

- `frontend-mocks/README.md` - MSW mock handlers documentation
- `.env.example` - Complete environment variable reference
- `pytest.ini` - Test configuration
- FastAPI auto-generated docs: http://localhost:8000/docs (when ENABLE_DOCS=true)

## Need Help?

- Check logs: `docker compose logs -f auth-api`
- Check health: `curl http://localhost:8000/health`
- Access Swagger UI: http://localhost:8000/docs (if ENABLE_DOCS=true)
- Database shell: `docker exec -it activity-postgres-db psql -U postgres -d activitydb`
- Redis shell: `docker exec -it auth-redis redis-cli`
