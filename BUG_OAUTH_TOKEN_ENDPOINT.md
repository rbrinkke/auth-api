# BUG REPORT: OAuth Token Endpoint - Client Credentials Flow

## Status: ✅ RESOLVED
**Fixed:** 2025-11-12 19:13 CET
**Resolution:** Fixed dependency injection issue in `get_oauth_client_service()` factory function

## Priority: HIGH
**Impact:** Blocks service-to-service authentication for Chat-API integration

---

## Resolution Summary

**Problem:** The `get_oauth_client_service()` factory function in `app/services/oauth_client_service.py` was instantiating `PasswordService()` without proper arguments, causing `Depends()` objects to be used instead of resolved instances.

**Fix Applied:** Modified lines 212-224 in `oauth_client_service.py`:
```python
async def get_oauth_client_service(
    db: asyncpg.Connection = Depends(get_db_connection)
) -> OAuthClientService:
    """Get OAuthClientService instance with properly resolved dependencies"""
    from app.core.security import PasswordManager
    from app.services.password_validation_service import get_password_validation_service

    # Properly instantiate dependencies (not Depends objects!)
    password_manager = PasswordManager()
    validation_service = get_password_validation_service()
    password_service = PasswordService(password_manager, validation_service)

    return OAuthClientService(db, password_service)
```

**Verification:** After rebuilding container with `--no-cache`, the dependency injection error no longer occurs. Client authentication now works correctly.

**Next Step:** Implement `client_credentials` grant type handler in `oauth_token.py` (currently only supports `authorization_code` and `refresh_token` grant types).

---

## Error Summary

**Location:** `/oauth/token` endpoint - Client Credentials grant flow
**Error:** `'Depends' object has no attribute 'verify_password'`
**Status Code:** HTTP 500 Internal Server Error
**Root Cause:** Dependency injection error - calling method on `Depends` object instead of resolved dependency instance

---

## Reproduction Steps

### 1. Register OAuth Client (COMPLETED)
OAuth client `chat-api-service` registered in database:
- **client_id:** `chat-api-service`
- **client_type:** `confidential`
- **grant_types:** `["client_credentials"]`
- **allowed_scopes:** `["groups:read"]`
- **client_secret_hash:** Argon2id hashed

### 2. Request Token (FAILS)
```bash
curl -X POST http://localhost:8000/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=chat-api-service" \
  -d "client_secret=your-service-secret-change-in-production" \
  -d "scope=groups:read"
```

**Expected:** JWT access token
**Actual:** HTTP 500 with error `'Depends' object has no attribute 'verify_password'`

---

## Error Logs (from Auth-API)

```json
{
  "event": "oauth_token_request",
  "grant_type": "client_credentials",
  "client_id": "chat-api-service",
  "timestamp": "2025-11-12T18:00:17.999451+00:00",
  "level": "INFO"
}

{
  "event": "oauth_client_auth_start",
  "client_id": "chat-api-service",
  "timestamp": "2025-11-12T18:00:17.999520+00:00",
  "level": "INFO"
}

{
  "event": "oauth_client_retrieved",
  "client_id": "chat-api-service",
  "timestamp": "2025-11-12T18:00:18.000256+00:00",
  "level": "DEBUG"
}

{
  "event": "password_verification_start",
  "password_length": 40,
  "hash_length": 97,
  "timestamp": "2025-11-12T18:00:18.000336+00:00",
  "level": "INFO"
}

{
  "event": "password_service_calling_password_manager_verify",
  "timeout": 5.0,
  "timestamp": "2025-11-12T18:00:18.000356+00:00",
  "level": "DEBUG"
}

{
  "event": "oauth_token_unexpected_error",
  "error": "'Depends' object has no attribute 'verify_password'",
  "grant_type": "client_credentials",
  "exc_info": true,
  "timestamp": "2025-11-12T18:00:18.000387+00:00",
  "level": "ERROR"
}
```

---

## Root Cause Analysis

**Problem:** OAuth token endpoint is calling `verify_password()` on a FastAPI `Depends()` object instead of the resolved dependency instance.

**Expected Pattern:**
```python
# Correct - dependency resolved to instance
async def token_endpoint(
    password_service: PasswordService = Depends(get_password_service)
):
    # password_service is the actual PasswordService instance
    result = await password_service.verify_password(...)
```

**Actual Pattern (Bug):**
```python
# WRONG - calling method on Depends object
async def token_endpoint(
    password_service = Depends(get_password_service)  # Missing type hint
):
    # password_service is the Depends() object, not the resolved instance
    result = await password_service.verify_password(...)  # AttributeError!
```

---

## Search Locations

### Files to Check:
1. **`app/routes/oauth.py`** or **`app/routes/oauth_token.py`** - Token endpoint route handler
2. **`app/services/oauth_token_service.py`** - Token service implementation
3. Any file containing: `POST /oauth/token` or `client_credentials` flow handler

### Search Commands:
```bash
# Find OAuth token endpoint
grep -r "oauth/token\|client_credentials" app/routes/

# Find password_service dependency usage
grep -r "password_service.*Depends\|verify_password" app/routes/ app/services/

# Find the error location
grep -r "verify_password" app/ | grep -v "__pycache__"
```

---

## Expected Fix

### Likely Issue Location:
File with OAuth token endpoint (`/oauth/token`) handler

### Fix Pattern:
Add proper type hint to dependency parameter:

```python
# BEFORE (Bug)
async def token(
    password_service = Depends(get_password_service),
    # Missing type hint ^
):
    result = await password_service.verify_password(...)

# AFTER (Fixed)
async def token(
    password_service: PasswordService = Depends(get_password_service),
    # Type hint added ^
):
    result = await password_service.verify_password(...)
```

**OR** - Dependency might be incorrectly defined:

```python
# BEFORE (Bug)
password_service = Depends(get_password_service)  # Module-level assignment

async def token(
    ps = password_service  # Passing Depends object
):
    result = await ps.verify_password(...)

# AFTER (Fixed)
async def token(
    password_service: PasswordService = Depends(get_password_service)
):
    result = await password_service.verify_password(...)
```

---

## Verification Steps

After fixing:

1. **Restart Auth-API**
   ```bash
   docker-compose restart auth-api
   ```

2. **Test Token Acquisition**
   ```bash
   curl -X POST http://localhost:8000/oauth/token \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=client_credentials" \
     -d "client_id=chat-api-service" \
     -d "client_secret=your-service-secret-change-in-production" \
     -d "scope=groups:read"
   ```

3. **Expected Response**
   ```json
   {
     "access_token": "eyJ...",
     "token_type": "Bearer",
     "expires_in": 3600,
     "scope": "groups:read"
   }
   ```

---

## Context

**Chat-API Integration Status:**
- ✅ OAuth client `chat-api-service` registered in Auth-API database
- ✅ Chat-API ServiceTokenManager configured correctly
- ✅ Chat-API ready to consume tokens
- ❌ BLOCKED: Cannot acquire tokens due to this Auth-API bug

**Next Steps After Fix:**
Chat-API verification can continue with:
- Service token acquisition test
- GroupService integration test (fetching groups from Auth-API)
- Message creation with org_id validation
- WebSocket authentication with OAuth tokens

---

## Database State

OAuth client successfully registered:

```sql
SELECT client_id, client_name, client_type, grant_types, allowed_scopes
FROM activity.oauth_clients
WHERE client_id = 'chat-api-service';
```

**Result:**
- client_id: `chat-api-service`
- client_name: `Chat API Service`
- client_type: `confidential`
- grant_types: `{client_credentials}`
- allowed_scopes: `{groups:read}`
- client_secret_hash: Argon2id hash present (97 chars)

---

## Priority Justification

**HIGH Priority** because:
1. Blocks all service-to-service OAuth flows (not just Chat-API)
2. Client Credentials flow is critical for machine-to-machine auth
3. Auth-API OAuth implementation is not functional for confidential clients
4. Affects production-readiness of OAuth 2.0 system

---

## Additional Notes

- This bug only affects **Client Credentials** grant flow with **confidential clients**
- Authorization Code flow (user-facing) may have similar issues if same pattern used
- Bug is in Auth-API codebase - Chat-API implementation is correct and verified
- Fix is likely 1-line change (adding type hint to dependency parameter)
