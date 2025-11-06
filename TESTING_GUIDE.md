# Auth API Testing Guide

## Quick Test Commands

### Run Complete Test Suite
```bash
./test_final_verification.sh
```

### Test Specific Flows

#### 1. Basic Health Check
```bash
curl http://localhost:8000/health
```

#### 2. User Registration
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"C0mplex!P@ssw0rd#2025$Secure"}'
```

#### 3. Email Verification
```bash
# Get code from Redis
CODE=$(docker compose exec redis redis-cli GET "2FA:$(docker compose exec redis redis-cli KEYS '2FA:*:verify' | head -1 | cut -d':' -f2):verify")
USER_ID=$(docker compose exec redis redis-cli KEYS '2FA:*:verify' | head -1 | cut -d':' -f2)

# Verify
curl -X POST http://localhost:8000/auth/verify-code \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"code\":\"$CODE\"}"
```

#### 4. Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"verified_user@example.com","password":"C0mplex!P@ssw0rd#2025$Secure"}'
```

#### 5. Token Refresh
```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"YOUR_REFRESH_TOKEN"}'
```

#### 6. Logout
```bash
curl -X POST http://localhost:8000/auth/logout \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"YOUR_REFRESH_TOKEN"}'
```

## Available Test Scripts

| Script | Description |
|--------|-------------|
| `test_final_verification.sh` | Complete test suite (20 tests) |
| `test_complete_flow.sh` | End-to-end flow test |
| `test_all.sh` | Full feature test |

## Check Container Status

```bash
# View logs
docker compose logs auth-api --tail 50

# Check services
docker compose ps

# Restart with new code
docker compose restart auth-api

# Rebuild with ENV changes
docker compose up -d --force-recreate auth-api
```

## Modify Rate Limits

Edit `docker-compose.yml`:
```yaml
environment:
  - RATE_LIMIT_REGISTER_PER_HOUR=100
  - RATE_LIMIT_LOGIN_PER_MINUTE=20
```

Then rebuild:
```bash
docker compose up -d --force-recreate auth-api
```

## Test Database Directly

```bash
docker compose exec postgres psql -U activity_user -d activitydb -c "SELECT id, email, email_verified FROM activity.users ORDER BY created_at DESC LIMIT 5;"
```

## Test Redis

```bash
docker compose exec redis redis-cli KEYS "*"
docker compose exec redis redis-cli FLUSHALL
```

## Common Issues

### Rate Limit Exceeded
```bash
# Flush Redis to clear rate limits
docker compose exec redis redis-cli FLUSHALL
```

### 2FA Routes Not Found
Use correct endpoints:
- `/auth/enable-2fa` (NOT `/2fa/setup`)
- `/auth/verify-2fa-setup`
- `/auth/verify-2fa`
- `/auth/disable-2fa`
- `/auth/2fa-status`

### Container Not Starting
Check logs:
```bash
docker compose logs auth-api --tail 100
```

## Success Criteria

✅ All tests pass (20/20)
✅ Health check returns healthy
✅ Database and Redis connected
✅ User registration works
✅ Email verification works
✅ Login returns tokens
✅ Token refresh works
✅ Logout blacks tokens
✅ Rate limiting active

## Test Results Location

See `TEST_RESULTS.md` for detailed test results and coverage.
