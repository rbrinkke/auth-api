# Authorization Audit Log - CLI Debugging Tool

Quick command-line access to audit logs for debugging authorization issues.

---

## 🚀 Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip install asyncpg tabulate

# Or use virtual environment
cd auth-api
source .venv/bin/activate  # If using venv
pip install asyncpg tabulate
```

### Basic Usage

```bash
cd auth-api/scripts

# Make executable (first time only)
chmod +x audit_debug.py

# Run command
./audit_debug.py <command> [arguments]
```

---

## 📋 Available Commands

### 1. User Activity Timeline

**What**: Shows all authorization checks for a specific user.

```bash
./audit_debug.py user <user_id> <org_id> [hours]

# Example
./audit_debug.py user c0a61eba-5805-494c-bc1b-563d3ca49126 1ab0e9fa-b4ec-4a8b-9cfa-7f2bb57db87e
./audit_debug.py user c0a61eba-5805-494c-bc1b-563d3ca49126 1ab0e9fa-b4ec-4a8b-9cfa-7f2bb57db87e 48
```

**Output**: Table with timestamp, permission, granted, reason, cache source.

**Use case**: "Why can't user X do Y?" - See all recent authorization attempts.

---

### 2. Specific Permission Check

**What**: Shows attempts for a specific permission.

```bash
./audit_debug.py permission <user_id> <org_id> <permission> [hours]

# Example
./audit_debug.py permission c0a61eba... 1ab0e9fa... activity:update
./audit_debug.py permission c0a61eba... 1ab0e9fa... activity:delete 12
```

**Output**: Table with attempts + summary (granted vs denied).

**Use case**: Debug specific permission issues: "User says they can't update activities."

---

### 3. Failed Authorization Attempts

**What**: Shows all failed authorization attempts (security monitoring).

```bash
./audit_debug.py failed [hours]

# Example
./audit_debug.py failed           # Last 1 hour
./audit_debug.py failed 24        # Last 24 hours
```

**Output**: Table with failed attempts (user, permission, reason, IP).

**Use case**: Security monitoring - detect unauthorized access attempts.

---

### 4. Brute-Force Detection

**What**: Detects users with multiple failed attempts (potential attacks).

```bash
./audit_debug.py brute-force [minutes] [threshold]

# Example
./audit_debug.py brute-force                # Last 60 min, threshold 5
./audit_debug.py brute-force 15 10          # Last 15 min, threshold 10
```

**Output**: Users with failures >= threshold.

**Use case**: Security alerts - detect brute-force attacks.

---

### 5. Resource Access History

**What**: Shows who accessed a specific resource.

```bash
./audit_debug.py resource <resource_id> [hours]

# Example
./audit_debug.py resource 770e8400-e29b-41d4-a716-446655440002
./audit_debug.py resource 770e8400-e29b-41d4-a716-446655440002 48
```

**Output**: Table with users, permissions, granted, IP addresses.

**Use case**: Compliance - "Who accessed sensitive resource Z?"

---

### 6. Permission Usage Statistics

**What**: Shows most-used permissions in organization (compliance reporting).

```bash
./audit_debug.py stats <org_id> [days]

# Example
./audit_debug.py stats 1ab0e9fa-b4ec-4a8b-9cfa-7f2bb57db87e
./audit_debug.py stats 1ab0e9fa-b4ec-4a8b-9cfa-7f2bb57db87e 30
```

**Output**: Top 20 permissions with usage stats (total checks, granted, denied, unique users).

**Use case**: Compliance reporting (SOC2, ISO27001) or permission cleanup.

---

### 7. Verify Audit Log Integrity

**What**: Verifies hash chain integrity (tamper detection).

```bash
./audit_debug.py integrity [hours]

# Example
./audit_debug.py integrity           # Last 24 hours
./audit_debug.py integrity 168       # Last 7 days
```

**Output**:
- ✅ VALID: No tampering detected
- 🚨 COMPROMISED: Shows first broken entry ID

**Use case**: Security audit - ensure audit log hasn't been tampered with.

---

### 8. Cache Performance Analysis

**What**: Shows cache hit rates (L1, L2, database).

```bash
./audit_debug.py cache [hours]

# Example
./audit_debug.py cache           # Last 1 hour
./audit_debug.py cache 24        # Last 24 hours
```

**Output**: Distribution of cache sources + hit rates.

**Use case**: Performance analysis - verify cache is working effectively.

---

### 9. Request Correlation Trace

**What**: Traces a request across services using correlation ID.

```bash
./audit_debug.py correlation <request_id>

# Example
./audit_debug.py correlation 880e8400-e29b-41d4-a716-446655440003
```

**Output**: All authorization checks for the request (chronological).

**Use case**: Distributed tracing - follow request through multiple authorization checks.

---

## 🔧 Configuration

### Environment Variables

The tool reads database credentials from environment:

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5441
export POSTGRES_DB=activitydb
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres_secure_password_change_in_prod
```

**Or** load from .env:

```bash
export $(cat ../.env | xargs)
./audit_debug.py user ...
```

### Docker Container

If running inside Docker:

```bash
# From host
docker exec -it auth-api python /app/scripts/audit_debug.py user ...

# Or enter container
docker exec -it auth-api bash
cd /app/scripts
./audit_debug.py user ...
```

---

## 📊 Real-World Examples

### Scenario 1: User Reports "Access Denied"

**Problem**: User can't update activities.

**Steps**:
```bash
# 1. Check recent activity
./audit_debug.py user <user_id> <org_id>

# 2. Check specific permission
./audit_debug.py permission <user_id> <org_id> activity:update

# Result:
# - authorized = false → User lacks permission
# - reason = "Not a member" → User not in org
# - reason = "No permission..." → User is member but lacks specific permission
```

---

### Scenario 2: Security Alert - Multiple Failed Logins

**Problem**: Security system alerts on suspicious activity.

**Steps**:
```bash
# 1. Check failed attempts
./audit_debug.py failed 1

# 2. Detect brute-force
./audit_debug.py brute-force 15 10

# 3. If suspicious user found, check their activity
./audit_debug.py user <suspicious_user_id> <org_id> 24

# Action: Consider temporary ban or 2FA enforcement
```

---

### Scenario 3: Compliance Audit - Who Accessed Sensitive Resource?

**Problem**: Auditor asks "Who accessed patient record X in last 30 days?"

**Steps**:
```bash
# 1. Check resource access
./audit_debug.py resource <resource_id> 720  # 30 days

# 2. Export to CSV for auditor
# (Run SQL query from AUDIT_LOG_DEBUGGING_GUIDE.md)
```

---

### Scenario 4: Performance Investigation - Cache Not Working?

**Problem**: Authorization seems slow.

**Steps**:
```bash
# 1. Check cache performance
./audit_debug.py cache 1

# Expected:
# - l2_cache: 60-90% (highest)
# - l1_cache: 10-20%
# - database: 5-10% (lowest)

# If database % is high → Check Redis connection
```

---

## 🛠️ Troubleshooting

### Error: "Database connection failed"

**Cause**: Wrong credentials or database not running.

**Fix**:
```bash
# Check database is running
docker ps | grep activity-postgres-db

# Test connection manually
docker exec activity-postgres-db psql -U postgres -d activitydb -c "SELECT 1;"

# Check environment variables
echo $POSTGRES_HOST
echo $POSTGRES_PORT
```

---

### Error: "No rows returned"

**Cause**: Audit logger not initialized or no activity in time range.

**Fix**:
```bash
# Check total entries
docker exec activity-postgres-db psql -U postgres -d activitydb -c "SELECT COUNT(*) FROM activity.authorization_audit_log;"

# Check auth-api logs
docker logs auth-api | grep audit_logger_initialized

# Expand time range
./audit_debug.py user <user_id> <org_id> 168  # 7 days
```

---

### Error: "Module 'asyncpg' not found"

**Cause**: Missing Python dependencies.

**Fix**:
```bash
pip install asyncpg tabulate
```

---

## 📚 Additional Resources

- **Debugging Guide**: `claudedocs/AUDIT_LOG_DEBUGGING_GUIDE.md` - Comprehensive SQL queries
- **Database Schema**: `database/init-scripts/03-authorization-audit-log.sql` - Table definition
- **Service Code**: `app/services/audit_service.py` - Audit logger implementation

---

## 💡 Tips & Best Practices

1. **Always use time ranges**: Queries with time ranges are much faster.
2. **Start broad, then narrow**: Check user activity first, then specific permissions.
3. **Use correlation IDs**: Track requests across services for distributed debugging.
4. **Regular integrity checks**: Run `integrity` command daily for security.
5. **Monitor failed attempts**: Use `failed` and `brute-force` commands for security alerts.
6. **Export for compliance**: Use SQL COPY command for GDPR/SOC2/ISO27001 audits.

---

**Generated**: 2025-11-14
**Author**: Claude Code + SuperClaude Framework v4.0.8
**Status**: ✅ **PRODUCTION READY**
