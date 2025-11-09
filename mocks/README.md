# Authentication API Mock Servers

Production-quality mock servers for comprehensive testing of the authentication API. Each mock server provides realistic simulation of external dependencies with full validation, error injection, and test isolation features.

## 📦 Quick Start

### Installation

```bash
# Install mock server dependencies
cd mocks
pip install -r requirements.txt
```

### Run All Mock Servers (Docker)

```bash
# From project root
docker-compose -f docker-compose.mocks.yml up
```

### Run Individual Mock Server

```bash
# Email Service Mock (Port 9000)
python mocks/email_service_mock.py

# HIBP API Mock (Port 9001)
python mocks/hibp_mock.py

# Redis Mock (Port 9002)
python mocks/redis_mock.py
```

---

## 🎯 Available Mocks

### 1. Email Service Mock (`email_service_mock.py`)

**Port**: 9000
**Purpose**: Mock HTTP-based email sending service

**Features**:
- ✅ Template validation (2fa_code, email_verification, password_reset)
- ✅ In-memory email storage for test assertions
- ✅ Error injection via query parameters
- ✅ Email retrieval by recipient
- ✅ Test isolation (clear endpoint)

**Endpoints**:

```bash
POST   /send                 # Send email
GET    /emails               # Retrieve all sent emails
GET    /emails/{email}       # Get emails for specific recipient
POST   /clear                # Clear email history
GET    /health               # Health check
```

**Example Usage**:

```bash
# Send verification email
curl -X POST http://localhost:9000/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "user@example.com",
    "template": "2fa_code",
    "subject": "Your Verification Code",
    "data": {
      "code": "123456",
      "purpose": "login",
      "expires_minutes": 10
    }
  }'

# Retrieve sent emails
curl http://localhost:9000/emails

# Get emails for specific user
curl http://localhost:9000/emails/user@example.com

# Clear emails (test isolation)
curl -X POST http://localhost:9000/clear

# Simulate timeout error
curl -X POST "http://localhost:9000/send?simulate_error=timeout" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

**Template Requirements**:

| Template | Required Data Fields |
|----------|---------------------|
| `2fa_code` | `code`, `purpose`, `expires_minutes` |
| `email_verification` | `verification_link`, `expires_hours` |
| `password_reset` | `reset_link`, `expires_hours` |

**Error Simulation**:
- `?simulate_error=timeout` → 408 Request Timeout (after 5s)
- `?simulate_error=500` → 500 Internal Server Error
- `?simulate_error=400` → 400 Bad Request
- `?simulate_error=503` → 503 Service Unavailable

---

### 2. HIBP API Mock (`hibp_mock.py`)

**Port**: 9001
**Purpose**: Mock Have I Been Pwned password breach checking API

**Features**:
- ✅ k-anonymity API implementation (GET /range/{hash_prefix})
- ✅ Configurable breach database
- ✅ Known breached passwords for testing
- ✅ Direct password check endpoint (testing utility)
- ✅ Statistics and introspection

**Endpoints**:

```bash
GET    /range/{hash_prefix}  # k-anonymity lookup (HIBP API format)
POST   /check                # Direct password check (testing utility)
POST   /add-breached         # Add breached password (testing)
DELETE /clear-breaches       # Reset to default breach database
GET    /stats                # API statistics
GET    /health               # Health check
```

**Example Usage**:

```bash
# Check password using k-anonymity API
# SHA-1 of "password": 5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8
curl http://localhost:9001/range/5BAA6

# Direct password check (testing utility)
curl -X POST http://localhost:9001/check \
  -H "Content-Type: application/json" \
  -d '{"password": "password123"}'

# Add custom breached password
curl -X POST http://localhost:9001/add-breached \
  -H "Content-Type: application/json" \
  -d '{"password": "testpass123", "breach_count": 99999}'

# Get statistics
curl http://localhost:9001/stats

# Clear custom breaches
curl -X DELETE http://localhost:9001/clear-breaches
```

**Known Breached Passwords** (for testing):

| Password | Breach Count |
|----------|-------------|
| `password` | 10,000,000 |
| `123456` | 5,000,000 |
| `password123` | 1,000,000 |
| `qwerty` | 500,000 |
| `P@ssw0rd!` | 50,000 |

**Pytest Mock** (for unit tests):

```python
from mocks.hibp_pytest_mock import mock_pwnedpasswords_breached

@pytest.mark.asyncio
async def test_breached_password(mock_pwnedpasswords_breached):
    service = PasswordValidationService()

    # Will raise PasswordValidationError
    with pytest.raises(PasswordValidationError):
        await service.check_breach_status("password123")
```

---

### 3. Redis Mock (`redis_mock.py`)

**Port**: 9002
**Purpose**: Mock Redis server with TTL simulation

**Features**:
- ✅ Full Redis-like operations (get, set, setex, delete, exists, ttl)
- ✅ Automatic TTL expiration with background cleanup (every 5s)
- ✅ Key pattern matching for queries
- ✅ Statistics and introspection
- ✅ Test isolation (clear endpoint)

**Endpoints**:

```bash
POST   /set            # SET operation
POST   /setex          # SETEX operation (with TTL)
GET    /get/{key}      # GET operation
DELETE /delete/{key}   # DELETE operation
GET    /exists/{key}   # EXISTS operation
GET    /ttl/{key}      # TTL operation
GET    /keys           # KEYS operation (pattern matching)
GET    /info/{key}     # Detailed key information
POST   /clear          # Clear all keys
GET    /stats          # Server statistics
GET    /health         # Health check
```

**Example Usage**:

```bash
# Set key without expiration
curl -X POST http://localhost:9002/set \
  -H "Content-Type: application/json" \
  -d '{"key": "user:123", "value": "john@example.com"}'

# Set key with expiration (600 seconds)
curl -X POST http://localhost:9002/setex \
  -H "Content-Type: application/json" \
  -d '{"key": "verify_token:abc", "seconds": 600, "value": "user_id:123"}'

# Get value
curl http://localhost:9002/get/user:123

# Check if key exists
curl http://localhost:9002/exists/user:123

# Get remaining TTL
curl http://localhost:9002/ttl/verify_token:abc

# Delete key
curl -X DELETE http://localhost:9002/delete/user:123

# List keys matching pattern
curl http://localhost:9002/keys?pattern=verify_token:*

# Get detailed key info
curl http://localhost:9002/info/user:123

# Clear all keys (test isolation)
curl -X POST http://localhost:9002/clear

# Get statistics
curl http://localhost:9002/stats
```

**Pytest Mock** (for unit tests):

```python
from mocks.redis_pytest_mock import mock_redis_client

def test_token_storage(mock_redis_client):
    # Set with expiration
    mock_redis_client.setex("token:abc", 600, "user:123")

    # Get value
    value = mock_redis_client.get("token:abc")
    assert value == "user:123"

    # Check TTL
    ttl = mock_redis_client.ttl("token:abc")
    assert ttl > 0 and ttl <= 600
```

---

### 4. Database Procedures Mock (`db_procedures_mock.py`)

**Type**: Pytest fixtures (no HTTP server)
**Purpose**: Mock PostgreSQL stored procedures with in-memory storage

**Features**:
- ✅ All stored procedures from `app/db/procedures.py`
- ✅ In-memory user and token storage
- ✅ Realistic data generation with Faker
- ✅ Proper error handling (duplicate email, user not found)
- ✅ Automatic test isolation

**Available Fixtures**:

| Fixture | Description |
|---------|-------------|
| `mock_db_procedures` | Empty mock database |
| `mock_db_with_users` | Pre-populated with test users |
| `mock_db_connection` | Mock connection with procedure overrides |

**Example Usage**:

```python
from mocks.db_procedures_mock import mock_db_procedures, create_mock_user
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_user_creation(mock_db_procedures):
    conn = AsyncMock()

    # Create user
    user = await mock_db_procedures.sp_create_user(
        conn, "test@example.com", "hashed_password"
    )

    assert user.email == "test@example.com"
    assert user.is_verified is False
    assert user.is_active is True

    # Retrieve user
    retrieved = await mock_db_procedures.sp_get_user_by_email(
        conn, "test@example.com"
    )
    assert retrieved.id == user.id

@pytest.mark.asyncio
async def test_with_existing_users(mock_db_with_users):
    conn = AsyncMock()

    # Pre-populated users available
    user = await mock_db_with_users.sp_get_user_by_email(
        conn, "verified@example.com"
    )
    assert user.is_verified is True
```

**Supported Procedures**:

- `sp_create_user(conn, email, hashed_password)` → UserRecord
- `sp_get_user_by_email(conn, email)` → UserRecord | None
- `sp_get_user_by_id(conn, user_id)` → UserRecord | None
- `sp_verify_user_email(conn, user_id)` → bool
- `sp_save_refresh_token(conn, user_id, token, expires_delta)` → bool
- `sp_validate_refresh_token(conn, user_id, token)` → bool
- `sp_revoke_refresh_token(conn, user_id, token)` → None
- `sp_revoke_all_refresh_tokens(conn, user_id)` → None
- `sp_update_password(conn, user_id, hashed_password)` → bool
- `check_email_exists(conn, email)` → bool

---

### 5. TOTP/2FA Mock (`totp_mock.py`)

**Type**: Pytest fixtures (no HTTP server)
**Purpose**: Deterministic TOTP (Time-based One-Time Password) for 2FA testing

**Features**:
- ✅ Deterministic secret and codes
- ✅ Configurable valid codes
- ✅ Always-valid and always-invalid modes
- ✅ QR code generation mocking
- ✅ No time dependencies in tests

**Available Fixtures**:

| Fixture | Description |
|---------|-------------|
| `mock_totp_deterministic` | Predictable secret ("JBSWY3DPEHPK3PXP") and code ("123456") |
| `mock_totp_always_valid` | Accepts any code as valid |
| `mock_totp_always_invalid` | Rejects all codes |
| `mock_totp_configurable` | Full control over secrets and codes |
| `mock_qrcode` | Mock QR code generation |

**Example Usage**:

```python
from mocks.totp_mock import mock_totp_deterministic, mock_totp_always_valid

@pytest.mark.asyncio
async def test_2fa_setup(mock_totp_deterministic):
    import pyotp

    # Predictable secret
    secret = pyotp.random_base32()
    assert secret == "JBSWY3DPEHPK3PXP"

    # Predictable code
    totp = pyotp.TOTP(secret)
    assert totp.verify("123456") is True
    assert totp.verify("000000") is False

@pytest.mark.asyncio
async def test_2fa_always_succeeds(mock_totp_always_valid):
    import pyotp

    totp = pyotp.TOTP("ANY_SECRET")
    assert totp.verify("000000") is True  # Any code works
    assert totp.verify("999999") is True

@pytest.mark.asyncio
async def test_custom_codes(mock_totp_configurable):
    # Configure specific valid codes
    mock_totp_configurable.set_valid_codes(
        "SECRET123",
        ["111111", "222222"]
    )

    import pyotp
    totp = pyotp.TOTP("SECRET123")
    assert totp.verify("111111") is True
    assert totp.verify("999999") is False
```

**Test Data**:

```python
from mocks.totp_mock import get_test_totp_data

data = get_test_totp_data()
# {
#     "secret": "JBSWY3DPEHPK3PXP",
#     "valid_codes": ["123456", "654321"],
#     "invalid_codes": ["000000", "999999"],
#     "provisioning_uri": "otpauth://totp/..."
# }
```

---

## 🔧 Integration with Tests

### Unit Tests

```python
# conftest.py
from mocks.email_service_mock import mock_email_service
from mocks.redis_pytest_mock import mock_redis_client
from mocks.db_procedures_mock import mock_db_procedures
from mocks.totp_mock import mock_totp_deterministic
from mocks.hibp_pytest_mock import mock_pwnedpasswords_safe

@pytest.fixture
def setup_mocks(
    mock_email_service,
    mock_redis_client,
    mock_db_procedures,
    mock_totp_deterministic,
    mock_pwnedpasswords_safe
):
    """Setup all mocks for unit tests."""
    return {
        "email": mock_email_service,
        "redis": mock_redis_client,
        "db": mock_db_procedures,
        "totp": mock_totp_deterministic,
        "hibp": mock_pwnedpasswords_safe
    }
```

### Integration Tests

```python
# Start mock servers before tests
import subprocess
import time

def start_mock_servers():
    """Start all mock HTTP servers."""
    servers = [
        ("email", "python mocks/email_service_mock.py"),
        ("hibp", "python mocks/hibp_mock.py"),
        ("redis", "python mocks/redis_mock.py")
    ]

    processes = []
    for name, cmd in servers:
        proc = subprocess.Popen(cmd.split())
        processes.append((name, proc))

    # Wait for servers to start
    time.sleep(2)

    return processes

@pytest.fixture(scope="session", autouse=True)
def mock_servers():
    """Start mock servers for integration tests."""
    processes = start_mock_servers()
    yield
    # Cleanup
    for name, proc in processes:
        proc.terminate()
```

### Environment Configuration

```bash
# .env.test
EMAIL_SERVICE_URL=http://localhost:9000
REDIS_HOST=localhost
REDIS_PORT=9002

# For HIBP mock, patch pwnedpasswords library in tests
# or configure pwnedpasswords to use mock API endpoint
```

---

## 📊 OpenAPI Documentation

All HTTP mock servers provide interactive API documentation:

- **Email Service**: http://localhost:9000/docs
- **HIBP API**: http://localhost:9001/docs
- **Redis Mock**: http://localhost:9002/docs

---

## 🧪 Testing Best Practices

### 1. Test Isolation

Always clear mock data between tests:

```python
@pytest.fixture(autouse=True)
async def clear_mocks():
    """Clear all mocks before each test."""
    # Clear email mock
    async with httpx.AsyncClient() as client:
        await client.post("http://localhost:9000/clear")
        await client.post("http://localhost:9002/clear")

    yield
```

### 2. Error Simulation

Test error handling with query parameters:

```python
async def test_email_timeout():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:9000/send?simulate_error=timeout",
            json={...}
        )
        assert response.status_code == 408
```

### 3. Realistic Data

Use provided factories for realistic test data:

```python
from mocks.db_procedures_mock import create_mock_user

user = create_mock_user(
    email="test@example.com",
    is_verified=True
)
```

### 4. Assertions on Mock Behavior

Verify emails were sent correctly:

```python
async def test_verification_email_sent():
    # Trigger registration
    await register_user("user@example.com", "password")

    # Verify email was sent
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:9000/emails/user@example.com"
        )
        emails = response.json()["emails"]

        assert len(emails) == 1
        assert emails[0]["template"] == "email_verification"
        assert emails[0]["subject"] == "Verify Your Account"
```

---

## 🐳 Docker Compose Configuration

See `docker-compose.mocks.yml` for complete Docker setup.

```yaml
services:
  email-mock:
    build:
      context: ./mocks
    ports:
      - "9000:9000"
    environment:
      - LOG_LEVEL=INFO

  hibp-mock:
    build:
      context: ./mocks
    ports:
      - "9001:9001"

  redis-mock:
    build:
      context: ./mocks
    ports:
      - "9002:9002"
```

---

## 📝 Adding New Mocks

To add a new mock server:

1. Create `mocks/{service_name}_mock.py`
2. Use `base.mock_base.create_mock_app()` for FastAPI setup
3. Use `base.error_injection.check_error_simulation` for error injection
4. Add health check endpoint
5. Document in this README
6. Add to `docker-compose.mocks.yml`
7. Create pytest fixtures if applicable

**Template**:

```python
#!/usr/bin/env python3
from fastapi import Depends
from base.mock_base import create_mock_app, create_health_response
from base.error_injection import check_error_simulation

app = create_mock_app(
    title="Service Name Mock",
    description="Description",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return create_health_response("Service Name Mock")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9003)
```

---

## 🎯 Coverage Summary

| Component | Mock Type | Port | Coverage |
|-----------|-----------|------|----------|
| Email Service | HTTP Server | 9000 | ✅ Complete |
| HIBP API | HTTP Server + Pytest | 9001 | ✅ Complete |
| Redis | HTTP Server + Pytest | 9002 | ✅ Complete |
| PostgreSQL | Pytest Fixtures | N/A | ✅ Complete |
| TOTP/2FA | Pytest Fixtures | N/A | ✅ Complete |

---

## 📚 Additional Resources

- [FastAPI Testing Documentation](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [HIBP API Documentation](https://haveibeenpwned.com/API/v3)
- [Redis Commands](https://redis.io/commands/)
- [TOTP RFC 6238](https://tools.ietf.org/html/rfc6238)

---

## 🤝 Contributing

When adding or modifying mocks:

1. Follow the existing patterns in `base/`
2. Add comprehensive docstrings
3. Include example usage in code comments
4. Update this README
5. Add tests for the mock itself
6. Ensure test isolation (clear/reset functionality)

---

## 📄 License

Same as parent project.
