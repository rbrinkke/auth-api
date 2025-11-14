# DEBUG Mode Best Practices

**Date**: 2025-11-14
**Status**: Recommended Guidelines

## TL;DR

✅ **Keep DEBUG=True as default** for excellent developer experience
✅ **Use LOG_LEVEL** to control logging verbosity
✅ **Production secrets validation** prevents unsafe deployments
✅ **ENVIRONMENT variable** triggers warnings for production-like envs

---

## Philosophy

The auth-api uses a **two-layer security strategy** instead of defaulting DEBUG to False:

1. **Layer 1**: Production secrets validation (blocks deployment with dev secrets)
2. **Layer 2**: Environment-based warnings (alerts on DEBUG=True in prod-like environments)

This approach provides:
- **Safety**: Production deployments are protected by secrets validation
- **Developer Experience**: Local development works out-of-the-box
- **Flexibility**: LOG_LEVEL controls verbosity independently

---

## What DEBUG Controls

### When DEBUG=True (Development)

**Logging:**
- Audit logs: FULL detail (100% of all authorization checks)
- Structured logs: Verbose debug information
- Error messages: Detailed stack traces and internal errors

**Security:**
- HSTS header: Disabled (no HTTPS required)
- Error responses: Detailed error messages exposed
- Swagger UI: Enabled (if ENABLE_DOCS=true)

**Behavior:**
- Audit sampling: 100% (log everything)
- Log level: Can use DEBUG level
- Performance: Less optimized (more logging overhead)

### When DEBUG=False (Production)

**Logging:**
- Audit logs: ESSENTIAL only (denied 100%, allowed 10% sample)
- Structured logs: INFO level or higher
- Error messages: Generic ("An unexpected error occurred")

**Security:**
- HSTS header: Enabled (enforce HTTPS)
- Error responses: Generic error messages
- Swagger UI: Disabled (ENABLE_DOCS should be false)
- Production secrets: Validated at startup

**Behavior:**
- Audit sampling: 10% for allowed, 100% for denied
- Log level: INFO or WARNING recommended
- Performance: Optimized (reduced logging)

---

## Configuration Matrix

### Development (Local)

```bash
# .env file
DEBUG=true
LOG_LEVEL=DEBUG
ENABLE_DOCS=true
SKIP_LOGIN_CODE=true  # Optional: faster testing
ENVIRONMENT=development
```

**What you get:**
- ✅ Verbose logging for debugging
- ✅ Detailed error messages
- ✅ Full audit trail
- ✅ Swagger UI available
- ✅ No production secret checks

### Staging Environment

```bash
# .env file
DEBUG=false  # Production-like behavior
LOG_LEVEL=INFO
ENABLE_DOCS=true  # Still useful for testing
SKIP_LOGIN_CODE=false
ENVIRONMENT=staging

# Secure secrets required!
JWT_SECRET_KEY=<cryptographically-random-64-chars>
ENCRYPTION_KEY=<cryptographically-random-64-chars>
POSTGRES_PASSWORD=<secure-password>
SERVICE_AUTH_TOKEN=<secure-token>
```

**What you get:**
- ✅ Production security behavior
- ✅ Sampled audit logs (reduced volume)
- ✅ Generic error messages
- ✅ HSTS enforced
- ⚠️ Warning if DEBUG=True detected

### Production

```bash
# .env file
DEBUG=false  # REQUIRED for production
LOG_LEVEL=INFO  # Or WARNING
ENABLE_DOCS=false  # Disable Swagger for security
SKIP_LOGIN_CODE=false
ENVIRONMENT=production

# Secure secrets MANDATORY!
JWT_SECRET_KEY=<cryptographically-random-64-chars>
ENCRYPTION_KEY=<cryptographically-random-64-chars>
POSTGRES_PASSWORD=<secure-password>
SERVICE_AUTH_TOKEN=<secure-token>
```

**What you get:**
- ✅ Maximum security
- ✅ Generic error messages
- ✅ 10% audit sampling (reduced cost)
- ✅ HSTS enforced
- ✅ Production secrets validated
- 🚨 Deployment blocked if secrets unsafe

---

## LOG_LEVEL vs DEBUG

These are **independent** settings that work together:

| DEBUG | LOG_LEVEL | Result |
|-------|-----------|--------|
| True | DEBUG | Maximum verbosity (development) |
| True | INFO | Moderate verbosity (development with less noise) |
| True | WARNING | Minimal verbosity (unusual, but allowed) |
| False | DEBUG | ⚠️ Not recommended (production with verbose logs) |
| False | INFO | ✅ Recommended production setting |
| False | WARNING | ✅ Production with minimal logging |

**Recommendation**: Use DEBUG to control **behavior** (security, error messages), use LOG_LEVEL to control **verbosity**.

---

## Environment Variable

The `ENVIRONMENT` variable provides extra safety:

```bash
ENVIRONMENT=production  # or prod, staging, stage
```

**Behavior:**
- If `DEBUG=True` AND `ENVIRONMENT` is production-like → Warning logged
- Warning doesn't block startup, but alerts operators
- Visible in startup logs

**Example warning:**
```
⚠️  WARNING: DEBUG=True in PRODUCTION environment!
This enables verbose logging and detailed error messages.
Set DEBUG=False for production deployments.
```

---

## Migration Guide

### Current Setup (no changes needed)

If you're already using:
```bash
DEBUG=true  # Development
```

Nothing changes! Keep working as before.

### Deploying to Production

**Step 1**: Set DEBUG=False
```bash
DEBUG=false
```

**Step 2**: Set secure secrets (use generator)
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

**Step 3**: Update .env file
```bash
JWT_SECRET_KEY=<generated-secure-secret>
ENCRYPTION_KEY=<generated-secure-secret>
POSTGRES_PASSWORD=<secure-password>
SERVICE_AUTH_TOKEN=<generated-secure-token>
```

**Step 4**: Set ENVIRONMENT variable (optional, for extra safety)
```bash
ENVIRONMENT=production
```

**Step 5**: Deploy

The startup validation will:
- ✅ Pass if DEBUG=False and secrets are secure
- ❌ Block if DEBUG=False and secrets contain dev patterns
- ⚠️ Warn if DEBUG=True and ENVIRONMENT=production

---

## Testing Your Configuration

### Test 1: Development Mode

```bash
# .env
DEBUG=true

# Start app
uvicorn app.main:app --reload

# Expected log:
# INFO:     Validating production secrets...
# INFO:     ⚠️  Running in DEBUG mode - production secret validation skipped
```

### Test 2: Production Mode with Secure Secrets

```bash
# .env
DEBUG=false
JWT_SECRET_KEY=aB3dE5fG7hI9jK1lM2nO4pQ6rS8tU0vW2xY4zA6bC8dE0fG2hI4jK6lM8nO0pQ2
# ... other secure secrets

# Start app
uvicorn app.main:app

# Expected log:
# INFO:     Validating production secrets...
# INFO:     ✅ Production secrets validation passed - all secrets are secure
```

### Test 3: Production Mode with Unsafe Secrets (Should FAIL)

```bash
# .env
DEBUG=false
JWT_SECRET_KEY=dev_secret_key_change_in_production_min_32_chars_required

# Start app
uvicorn app.main:app

# Expected: App crashes with error message
# 🚨 PRODUCTION DEPLOYMENT BLOCKED - UNSAFE SECRETS DETECTED 🚨
```

### Test 4: Production Environment with DEBUG=True (Warning)

```bash
# .env
DEBUG=true
ENVIRONMENT=production

# Start app
uvicorn app.main:app

# Expected log:
# WARNING: ⚠️  WARNING: DEBUG=True in PRODUCTION environment!
#          This enables verbose logging and detailed error messages.
#          Set DEBUG=False for production deployments.
```

---

## Common Mistakes & Solutions

### Mistake 1: DEBUG=False but forgot to change secrets

**Problem:**
```bash
DEBUG=false
JWT_SECRET_KEY=dev_secret_key_change_in_production...  # Still dev secret!
```

**Result:** ❌ Deployment blocked with clear error message

**Solution:** Generate secure secrets (see migration guide)

### Mistake 2: Production with DEBUG=True

**Problem:**
```bash
DEBUG=true
ENVIRONMENT=production
```

**Result:** ⚠️ Warning logged, but app starts

**Solution:** Set `DEBUG=false` in production

### Mistake 3: Using LOG_LEVEL=DEBUG in production

**Problem:**
```bash
DEBUG=false
LOG_LEVEL=DEBUG  # Too verbose for production!
```

**Result:** App works but logs too much, impacts performance

**Solution:** Use `LOG_LEVEL=INFO` or `LOG_LEVEL=WARNING`

### Mistake 4: Disabling docs in development

**Problem:**
```bash
DEBUG=true
ENABLE_DOCS=false  # Why disable in dev?
```

**Result:** No Swagger UI for testing APIs

**Solution:** Keep `ENABLE_DOCS=true` in development

---

## Security Implications

### DEBUG=True Security Risks

When `DEBUG=True`, these behaviors could leak information:

1. **Detailed Error Messages**: Stack traces expose code structure
2. **Verbose Logging**: Internal state visible in logs
3. **No HSTS**: HTTPS not enforced
4. **Full Audit Logs**: Higher database write volume

**Mitigation**: Production secrets validation prevents `DEBUG=True` with dev secrets.

### Why Not Default DEBUG=False?

**Considered but rejected** because:

1. **Developer Experience**: Would break local development
2. **Existing Safety**: Secrets validation already protects production
3. **Flexibility**: DEBUG and LOG_LEVEL serve different purposes
4. **Warnings**: ENVIRONMENT variable provides extra safety layer

---

## Monitoring & Alerting

### Recommended Alerts

Set up alerts for these conditions:

**Alert 1: DEBUG=True in Production**
```
Query: {environment="production"} |= "DEBUG mode"
Action: Notify operations team
Severity: WARNING
```

**Alert 2: Production Secrets Validation Failure**
```
Query: {level="CRITICAL"} |= "PRODUCTION DEPLOYMENT BLOCKED"
Action: Block deployment, notify security team
Severity: CRITICAL
```

**Alert 3: Excessive Audit Log Volume**
```
Query: rate({service="auth-api"} |= "authz_audit_logged") > 1000
Action: Check if DEBUG=True in production
Severity: WARNING
```

---

## FAQ

### Q: Should I ever set DEBUG=False in development?

**A**: Only if you want to test production-like behavior (e.g., testing audit log sampling). For day-to-day development, keep `DEBUG=True`.

### Q: What if I need verbose logs in production for debugging?

**A**: Instead of `DEBUG=True`, use `LOG_LEVEL=DEBUG` temporarily. This gives you verbose logs without the security implications of DEBUG mode.

### Q: Can I deploy with DEBUG=True to production if I really need it?

**A**: Technically yes, but:
- You'll get warnings in startup logs
- Your audit logs will be very verbose (cost implications)
- Error messages will leak internal details
- **NOT RECOMMENDED** for security and performance reasons

### Q: Why doesn't the app just use ENVIRONMENT to set DEBUG automatically?

**A**: Explicit is better than implicit. Making DEBUG an explicit choice prevents accidental misconfigurations.

---

## Summary

The auth-api uses a **defense-in-depth** approach:

1. **DEBUG=True default**: Excellent developer experience
2. **Production secrets validation**: Prevents unsafe deployments
3. **Environment warnings**: Alerts on suspicious configurations
4. **LOG_LEVEL control**: Independent verbosity tuning

This strategy provides:
- ✅ Safety without sacrificing developer experience
- ✅ Multiple layers of validation
- ✅ Clear error messages when misconfigured
- ✅ Flexibility for different deployment scenarios

**For Production**: Set `DEBUG=False`, use secure secrets, monitor logs for warnings.

---

**Related Documentation:**
- [Production Secrets Validation](PRODUCTION_SECRETS_VALIDATION.md)
- [Code Analysis Report](CODE_ANALYSIS_REPORT.md)
- [Deployment Checklist](../CLAUDE.md#production-deployment-checklist)
