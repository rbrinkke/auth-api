# Integration Testing Guide - Auth API Authorization Endpoint

Complete guide for testing the production authorization endpoint (`POST /api/v1/authorization/check`).

## Quick Start

```bash
# 1. Setup test data in database
docker exec -i activity-postgres-db psql -U postgres -d activitydb < setup_real_test_data.sql

# 2. Run complete test suite
./test_production_auth_endpoint.sh
```

## Test Coverage

This test suite validates **4 critical scenarios**:

### ✅ Test 1: Security - Hardcoded Test Users Removed
- **OLD behavior:** Accepted hardcoded `test-user` / `test-org` credentials
- **NEW behavior:** Rejects with `"Invalid ID format: UUID required"`
- **Validates:** Production security hardening

### ✅ Test 2: Protocol - HTTP 200 for Denied Access
- **OLD behavior:** Returned HTTP 403 Forbidden on denial
- **NEW behavior:** Always returns HTTP 200 with `{"allowed": false}`
- **Validates:** Consistent API protocol (no 403 exceptions)

### ✅ Test 3: Validation - Strict UUID Format
- **OLD behavior:** Auto-converted invalid strings to MD5 hashes
- **NEW behavior:** Rejects immediately with validation error
- **Validates:** Input validation and data integrity

### ✅ Test 4: Integration - Successful Authorization
- **Tests:** Real user with database-backed permissions
- **Validates:** Complete authorization chain (user → org → group → permission)
- **Verifies:** `allowed: true` with `groups: ["Content Creators"]`

## Prerequisites

### Required Services
```bash
# Ensure PostgreSQL is running
docker ps | grep activity-postgres-db

# Ensure auth-api is running
docker ps | grep auth-api
```

### Database Schema
- Migration 001: Organizations
- Migration 002: RBAC (groups, permissions)
- Schema: `activity` with all stored procedures

## Setup Test Data

### Step 1: Run SQL Script

```bash
docker exec -i activity-postgres-db psql -U postgres -d activitydb < setup_real_test_data.sql
```

### Step 2: Verify Data Was Created

```bash
docker exec -i activity-postgres-db psql -U postgres -d activitydb -c "
SELECT
    u.email,
    o.name as org_name,
    g.name as group_name,
    p.resource || ':' || p.action as permission
FROM activity.users u
JOIN activity.organization_members om ON u.id = om.user_id
JOIN activity.organizations o ON om.organization_id = o.id
JOIN activity.user_groups ug ON u.id = ug.user_id
JOIN activity.groups g ON ug.group_id = g.id
JOIN activity.group_permissions gp ON g.id = gp.group_id
JOIN activity.permissions p ON gp.permission_id = p.id
WHERE u.id = '22222222-2222-2222-2222-222222222222';
"
```

**Expected output:**
```
      email       |  org_name  |   group_name    | permission
------------------+------------+-----------------+-------------
 test@example.com | Test Corp  | Content Creators| image:upload
```

## Test Data Reference

All test entities use **hardcoded UUIDs** for predictable testing:

| Entity | UUID | Name/Description |
|--------|------|------------------|
| **Organization** | `11111111-1111-1111-1111-111111111111` | Test Corp |
| **User** | `22222222-2222-2222-2222-222222222222` | test@example.com |
| **Group** | `33333333-3333-3333-3333-333333333333` | Content Creators |
| **Permission** | `44444444-4444-4444-4444-444444444444` | image:upload |

### Authorization Chain

```
User (test@example.com)
  └─> Member of Organization (Test Corp)
      └─> Member of Group (Content Creators)
          └─> Has Permission (image:upload)
```

## Running Tests

### Full Test Suite

```bash
./test_production_auth_endpoint.sh
```

**Expected output:**
```
========================================
Testing Production Auth Endpoint
========================================

========================================
TEST 1: Hardcoded Test Users Removed
========================================
✅ PASSED

========================================
TEST 2: HTTP 200 for Denied Access
========================================
✅ PASSED

========================================
TEST 3: Strict UUID Validation
========================================
✅ PASSED (3 sub-tests)

========================================
TEST 4: Successful Authorization
========================================
✅ PASSED
✓ Group 'Content Creators' verified in response

========================================
TEST SUMMARY
========================================
All production auth endpoint tests passed!

Validated:
✅ 1. Hardcoded test users removed (test-user rejected)
✅ 2. HTTP 200 returned for denied access (no 403)
✅ 3. Strict UUID validation (invalid strings rejected)
✅ 4. Successful authorization with group membership verification
```

### Individual Test Cases

You can test the endpoint manually using curl:

```bash
# Test 4: Successful authorization
curl -X POST http://localhost:8000/api/v1/authorization/check \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "22222222-2222-2222-2222-222222222222",
    "org_id": "11111111-1111-1111-1111-111111111111",
    "permission": "image:upload"
  }' | jq

# Expected response:
# {
#   "allowed": true,
#   "groups": ["Content Creators"],
#   "reason": "User has permission via group membership"
# }
```

## Troubleshooting

### Test 4 Fails with "Not a member of the organization"

**Problem:** Test data not created properly in database.

**Solution:**
```bash
# Re-run SQL script
docker exec -i activity-postgres-db psql -U postgres -d activitydb < setup_real_test_data.sql

# Verify user exists
docker exec -i activity-postgres-db psql -U postgres -d activitydb -c "
SELECT id, email FROM activity.users WHERE id = '22222222-2222-2222-2222-222222222222';
"
```

### Test 4 Fails with "Permission not found"

**Problem:** Permission not granted to group or group_permissions broken.

**Solution:**
```bash
# Check permission chain
docker exec -i activity-postgres-db psql -U postgres -d activitydb -c "
SELECT * FROM activity.sp_get_user_permissions(
    '22222222-2222-2222-2222-222222222222'::UUID,
    '11111111-1111-1111-1111-111111111111'::UUID
);
"
```

### Connection Refused Errors

**Problem:** auth-api not running or not accessible.

**Solution:**
```bash
# Check API health
curl http://localhost:8000/health

# Restart auth-api
cd /mnt/d/activity/auth-api
./rebuild.sh
```

### SQL Script Fails with Foreign Key Violations

**Problem:** Tables don't exist or migrations not applied.

**Solution:**
```bash
# Check schema exists
docker exec -i activity-postgres-db psql -U postgres -d activitydb -c "\dn"

# Check tables exist
docker exec -i activity-postgres-db psql -U postgres -d activitydb -c "\dt activity.*"
```

## Cleanup (Optional)

### Remove Test Data

```bash
docker exec -i activity-postgres-db psql -U postgres -d activitydb < cleanup_test_data.sql
```

### Manual Cleanup

```bash
docker exec -i activity-postgres-db psql -U postgres -d activitydb -c "
DELETE FROM activity.user_groups WHERE user_id = '22222222-2222-2222-2222-222222222222';
DELETE FROM activity.group_permissions WHERE group_id = '33333333-3333-3333-3333-333333333333';
DELETE FROM activity.groups WHERE id = '33333333-3333-3333-3333-333333333333';
DELETE FROM activity.organization_members WHERE user_id = '22222222-2222-2222-2222-222222222222';
DELETE FROM activity.permissions WHERE id = '44444444-4444-4444-4444-444444444444';
DELETE FROM activity.organizations WHERE id = '11111111-1111-1111-1111-111111111111';
DELETE FROM activity.users WHERE id = '22222222-2222-2222-2222-222222222222';
"
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Setup Test Data
  run: |
    docker exec -i activity-postgres-db psql -U postgres -d activitydb < setup_real_test_data.sql

- name: Run Integration Tests
  run: |
    chmod +x test_production_auth_endpoint.sh
    ./test_production_auth_endpoint.sh

- name: Cleanup Test Data
  if: always()
  run: |
    docker exec -i activity-postgres-db psql -U postgres -d activitydb < cleanup_test_data.sql
```

## Additional Testing

### Performance Testing

Test authorization endpoint latency:

```bash
# Measure response time (should be <50ms with caching)
time curl -X POST http://localhost:8000/api/v1/authorization/check \
  -H "Content-Type: application/json" \
  -d '{"user_id": "22222222-2222-2222-2222-222222222222", "org_id": "11111111-1111-1111-1111-111111111111", "permission": "image:upload"}' \
  -o /dev/null -s
```

### Cache Testing

Enable Redis caching and test performance improvement:

```bash
# Enable caching
export AUTHZ_CACHE_ENABLED=true
docker compose restart auth-api

# Run test - first call (cache miss)
time ./test_production_auth_endpoint.sh

# Run test - second call (cache hit, should be faster)
time ./test_production_auth_endpoint.sh
```

## Related Documentation

- **Main Documentation:** `../CLAUDE.md`
- **Authorization Service:** `../app/services/authorization_service.py`
- **RBAC Architecture:** `../ARCHITECTURE.md`
- **API Documentation:** http://localhost:8000/docs (when `ENABLE_DOCS=true`)

## Support

For issues or questions:
1. Check logs: `docker compose logs -f auth-api`
2. Verify health: `curl http://localhost:8000/health`
3. Check database connection: `docker exec -i activity-postgres-db psql -U postgres -d activitydb -c "SELECT 1;"`
