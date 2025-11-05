# Auth API

Ultra-minimalistic authentication service for the Activity App. Built with FastAPI, PostgreSQL (stored procedures only), and Redis.

## 🎯 Features

- **Hard Email Verification**: Users MUST verify email before login
- **JWT Authentication**: Access tokens (15 min) + Refresh tokens (30 days)
- **Refresh Token Rotation**: Old tokens are immediately blacklisted (mandatory security)
- **Argon2id Password Hashing**: Industry-standard PHC winner
- **Redis Token Storage**: All temporary tokens with automatic TTL
- **Rate Limiting**: Protection against brute-force attacks
- **Password Reset**: Time-limited reset tokens (1 hour)

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│      Auth API (FastAPI)         │
│                                 │
│  - JWT generation               │
│  - Password hashing (Argon2)    │
│  - Token management             │
│  - Rate limiting                │
└─────────────────────────────────┘
         │           │
         │           └──────────────┐
         ▼                          ▼
  ┌──────────┐              ┌──────────┐
  │PostgreSQL│              │  Redis   │
  │  (SP's)  │              │ (tokens) │
  └──────────┘              └──────────┘
```

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Create .env file from example
cp .env.example .env

# CRITICAL: Edit .env and set JWT_SECRET_KEY
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 2. Start Services

```bash
# Start PostgreSQL + Redis + Auth API
docker-compose up -d

# View logs
docker-compose logs -f auth-api
```

### 3. Create Stored Procedures

**IMPORTANT**: The Auth API expects these stored procedures to exist in your database.

See the "Required Stored Procedures" section below for complete specifications.

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/health

# View API documentation
open http://localhost:8000/docs
```

## 📋 API Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/auth/register` | Register new user | 3/hour |
| GET | `/auth/verify?token=xxx` | Verify email | - |
| POST | `/auth/resend-verification` | Resend verification email | 1/5min |
| POST | `/auth/login` | Login with email/password | 5/min |
| POST | `/auth/refresh` | Refresh access token | - |
| POST | `/auth/logout` | Logout (blacklist token) | - |
| POST | `/auth/request-password-reset` | Request password reset | 1/5min |
| POST | `/auth/reset-password` | Reset password | - |
| GET | `/health` | Health check | - |

## 🗄️ Required Stored Procedures

You must create these stored procedures in your PostgreSQL database:

### 1. sp_create_user

```sql
CREATE OR REPLACE FUNCTION activity.sp_create_user(
    p_email VARCHAR,
    p_hashed_password VARCHAR
) RETURNS TABLE(
    id UUID,
    email VARCHAR,
    is_verified BOOLEAN,
    is_active BOOLEAN,
    created_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    INSERT INTO activity.users (email, hashed_password, is_verified, is_active)
    VALUES (LOWER(p_email), p_hashed_password, FALSE, TRUE)
    RETURNING id, email, is_verified, is_active, created_at;
END;
$$ LANGUAGE plpgsql;
```

**Notes:**
- Email must be stored as lowercase
- `is_verified` defaults to FALSE
- Throws exception if email already exists (UNIQUE constraint)

### 2. sp_get_user_by_email

```sql
CREATE OR REPLACE FUNCTION activity.sp_get_user_by_email(
    p_email VARCHAR
) RETURNS TABLE(
    id UUID,
    email VARCHAR,
    hashed_password VARCHAR,
    is_verified BOOLEAN,
    is_active BOOLEAN,
    created_at TIMESTAMP,
    verified_at TIMESTAMP,
    last_login_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT u.id, u.email, u.hashed_password, u.is_verified, u.is_active,
           u.created_at, u.verified_at, u.last_login_at
    FROM activity.users u
    WHERE u.email = LOWER(p_email);
END;
$$ LANGUAGE plpgsql;
```

**Notes:**
- Returns NULL if user not found
- Includes `hashed_password` for authentication

### 3. sp_get_user_by_id

```sql
CREATE OR REPLACE FUNCTION activity.sp_get_user_by_id(
    p_user_id UUID
) RETURNS TABLE(
    id UUID,
    email VARCHAR,
    hashed_password VARCHAR,
    is_verified BOOLEAN,
    is_active BOOLEAN,
    created_at TIMESTAMP,
    verified_at TIMESTAMP,
    last_login_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT u.id, u.email, u.hashed_password, u.is_verified, u.is_active,
           u.created_at, u.verified_at, u.last_login_at
    FROM activity.users u
    WHERE u.id = p_user_id;
END;
$$ LANGUAGE plpgsql;
```

### 4. sp_verify_user_email

```sql
CREATE OR REPLACE FUNCTION activity.sp_verify_user_email(
    p_user_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    UPDATE activity.users
    SET is_verified = TRUE,
        verified_at = NOW()
    WHERE id = p_user_id;
    
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected > 0;
END;
$$ LANGUAGE plpgsql;
```

**Notes:**
- Sets `is_verified` = TRUE
- Sets `verified_at` = NOW()
- Returns TRUE if user found, FALSE otherwise

### 5. sp_update_last_login

```sql
CREATE OR REPLACE FUNCTION activity.sp_update_last_login(
    p_user_id UUID
) RETURNS VOID AS $$
BEGIN
    UPDATE activity.users
    SET last_login_at = NOW()
    WHERE id = p_user_id;
END;
$$ LANGUAGE plpgsql;
```

### 6. sp_update_password

```sql
CREATE OR REPLACE FUNCTION activity.sp_update_password(
    p_user_id UUID,
    p_new_hashed_password VARCHAR
) RETURNS BOOLEAN AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    UPDATE activity.users
    SET hashed_password = p_new_hashed_password
    WHERE id = p_user_id;
    
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected > 0;
END;
$$ LANGUAGE plpgsql;
```

### 7. sp_deactivate_user

```sql
CREATE OR REPLACE FUNCTION activity.sp_deactivate_user(
    p_user_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    UPDATE activity.users
    SET is_active = FALSE
    WHERE id = p_user_id;
    
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected > 0;
END;
$$ LANGUAGE plpgsql;
```

## 🔐 Redis Key Structure

The Auth API uses Redis for all temporary tokens:

```
# Email Verification
verify_token:{token} → user_id (TTL: 24h)
verify_user:{user_id} → token (TTL: 24h)

# Password Reset
reset_token:{token} → user_id (TTL: 1h)
reset_user:{user_id} → token (TTL: 1h)

# Refresh Token Blacklist
blacklist_jti:{jti} → "1" (TTL: 30d)
```

## 🔧 Configuration

All configuration is via environment variables. See `.env.example` for all options.

**Critical Settings:**

```bash
# MUST be changed in production (minimum 32 characters)
JWT_SECRET_KEY=your-secure-random-key-here

# Database connection
POSTGRES_HOST=postgres
POSTGRES_PASSWORD=secure-password

# Frontend URL (for email links)
FRONTEND_URL=https://your-app.com
```

## 📊 Database Schema

The stored procedures expect this `users` table structure:

```sql
CREATE TABLE activity.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    verified_at TIMESTAMP,
    last_login_at TIMESTAMP,
    
    CONSTRAINT email_lowercase CHECK (email = LOWER(email))
);

CREATE INDEX idx_users_email ON activity.users(email);
CREATE INDEX idx_users_verified ON activity.users(is_verified) 
    WHERE is_verified = TRUE;
```

## 🧪 Testing

```bash
# Example: Register a user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234"}'

# Check verification token in Redis
docker exec auth-redis redis-cli KEYS "verify_token:*"

# Example: Login (will fail until email is verified)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test@example.com","password":"Test1234"}'
```

## 📝 Development

```bash
# Install dependencies locally
pip install -r requirements.txt

# Run without Docker
export $(cat .env | xargs)
python -m uvicorn app.main:app --reload

# View logs
docker-compose logs -f auth-api
```

## 🔒 Security Features

1. **Argon2id Hashing**: Passwords hashed with PHC winner algorithm
2. **Token Rotation**: Refresh tokens are single-use
3. **Rate Limiting**: Brute-force protection on sensitive endpoints
4. **Hard Verification**: Email must be verified before login
5. **Token Blacklisting**: Logout immediately revokes refresh tokens
6. **TTL on All Tokens**: Automatic cleanup via Redis expiration
7. **Secure Defaults**: No debug mode in production

## 📚 Email Service Integration

The Auth API expects an email service at `EMAIL_SERVICE_URL` with this interface:

```bash
POST /send
{
  "to": "user@example.com",
  "template": "email_verification",
  "subject": "Verify your email",
  "data": {
    "verification_link": "https://app.com/verify?token=xxx"
  }
}
```

For development, you can use MailHog (included in docker-compose, commented out).

## 🐛 Troubleshooting

**Database connection errors:**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres
```

**Redis connection errors:**
```bash
# Check if Redis is running
docker-compose ps redis

# Test Redis connection
docker exec auth-redis redis-cli ping
```

**Stored procedure not found:**
```bash
# Connect to PostgreSQL
docker exec -it auth-postgres psql -U activity_user -d activity_db

# List functions in schema
\df activity.*
```

## 📄 License

MIT

## 🤝 Contributing

This is a microservice for the Activity App. See main repository for contribution guidelines.
