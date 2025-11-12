"""Prometheus metrics for authentication API.

Provides custom metrics for tracking authentication events, security incidents,
and system performance.
"""

from prometheus_client import Counter, Histogram, Gauge
import time

# ========== Request Metrics ==========

# HTTP request counters (supplementing auto-instrumentation)
http_requests_total = Counter(
    'auth_api_http_requests_total',
    'Total HTTP requests by method, endpoint, and status',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'auth_api_http_request_duration_seconds',
    'HTTP request latency by endpoint',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# ========== Authentication Metrics ==========

# User registrations
registrations_total = Counter(
    'auth_api_registrations_total',
    'Total user registrations',
    ['status']  # success, failed_duplicate, failed_validation
)

# Login attempts
login_attempts_total = Counter(
    'auth_api_login_attempts_total',
    'Total login attempts',
    ['status']  # success, failed_credentials, failed_not_verified, failed_2fa
)

# Email verifications
email_verifications_total = Counter(
    'auth_api_email_verifications_total',
    'Total email verifications',
    ['status']  # success, failed_invalid_code, failed_expired
)

# Password resets
password_resets_total = Counter(
    'auth_api_password_resets_total',
    'Total password reset requests',
    ['stage']  # requested, completed, failed
)

# 2FA operations
twofa_operations_total = Counter(
    'auth_api_2fa_operations_total',
    'Total 2FA operations',
    ['operation', 'status']  # operation: setup, verify, disable; status: success, failed
)

# Token operations
token_operations_total = Counter(
    'auth_api_token_operations_total',
    'Total token operations',
    ['operation', 'status']  # operation: create, refresh, revoke; status: success, failed
)

# ========== Security Metrics ==========

# Rate limit hits
rate_limit_hits_total = Counter(
    'auth_api_rate_limit_hits_total',
    'Total rate limit hits by endpoint',
    ['endpoint', 'ip']
)

# Invalid credentials attempts (potential brute force)
invalid_credentials_total = Counter(
    'auth_api_invalid_credentials_total',
    'Total invalid credential attempts',
    ['email_hash']  # SHA256 hash of email for privacy
)

# Request size limit violations
request_size_violations_total = Counter(
    'auth_api_request_size_violations_total',
    'Total request size limit violations',
    ['endpoint']
)

# Password validation failures
password_validation_failures_total = Counter(
    'auth_api_password_validation_failures_total',
    'Total password validation failures',
    ['reason']  # weak, breached, format
)

# ========== Database & Redis Metrics ==========

# Database queries (legacy - kept for backward compatibility)
db_queries_total = Counter(
    'auth_api_db_queries_total',
    'Total database queries',
    ['operation', 'status']  # operation: select, insert, update; status: success, failed
)

db_query_duration_seconds = Histogram(
    'auth_api_db_query_duration_seconds',
    'Database query latency',
    ['operation'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

# Stored procedure metrics (new - used by database logging decorator)
db_query_duration_histogram = Histogram(
    'auth_api_db_stored_procedure_duration_seconds',
    'Stored procedure execution duration',
    ['operation', 'status'],  # operation: sp_create_user, sp_get_user_by_email, etc.; status: success, error
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

db_query_total_counter = Counter(
    'auth_api_db_stored_procedure_total',
    'Total stored procedure executions',
    ['operation', 'status']  # operation: sp_create_user, etc.; status: success, error
)

db_slow_query_counter = Counter(
    'auth_api_db_slow_queries_total',
    'Total slow database queries (>1s)',
    ['operation', 'severity']  # operation: sp_name; severity: slow (>1s), very_slow (>5s)
)

# Redis operations
redis_operations_total = Counter(
    'auth_api_redis_operations_total',
    'Total Redis operations',
    ['operation', 'status']  # operation: get, set, delete; status: success, failed
)

redis_operation_duration_seconds = Histogram(
    'auth_api_redis_operation_duration_seconds',
    'Redis operation latency',
    ['operation'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5)
)

# Connection pool status
db_pool_active_connections = Gauge(
    'auth_api_db_pool_active_connections',
    'Number of active database connections'
)

db_pool_idle_connections = Gauge(
    'auth_api_db_pool_idle_connections',
    'Number of idle database connections'
)

# ========== Email Service Metrics ==========

# Email operations
email_operations_total = Counter(
    'auth_api_email_operations_total',
    'Total email operations',
    ['type', 'status']  # type: verification, reset, 2fa; status: success, failed
)

email_operation_duration_seconds = Histogram(
    'auth_api_email_operation_duration_seconds',
    'Email operation latency',
    ['type'],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0)
)

# ========== Business Metrics ==========

# Active users (verified)
active_users_total = Gauge(
    'auth_api_active_users_total',
    'Total number of active verified users'
)

# Active sessions
active_sessions_total = Gauge(
    'auth_api_active_sessions_total',
    'Total number of active sessions (non-revoked refresh tokens)'
)

# 2FA adoption rate
twofa_enabled_users_total = Gauge(
    'auth_api_2fa_enabled_users_total',
    'Total number of users with 2FA enabled'
)

# ========== RBAC Authorization Metrics (Sprint 2) ==========

# Authorization checks (THE CORE - Policy Decision Point)
authz_checks_total = Counter(
    'auth_api_authz_checks_total',
    'Total authorization checks via THE CORE /authorize endpoint',
    ['result', 'resource', 'action']  # result: granted, denied_not_member, denied_no_permission
)

authz_check_duration_seconds = Histogram(
    'auth_api_authz_check_duration_seconds',
    'Authorization check latency (p50/p95/p99 - target: p95 < 50ms)',
    ['resource', 'action'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

# Permission lookup operations (get user permissions)
permission_lookups_total = Counter(
    'auth_api_permission_lookups_total',
    'Total permission lookup operations',
    ['status']  # success, failed
)

# Group operations
group_operations_total = Counter(
    'auth_api_group_operations_total',
    'Total group management operations',
    ['operation', 'status']  # operation: create, update, delete, add_member, remove_member; status: success, failed
)

# Permission management operations
permission_operations_total = Counter(
    'auth_api_permission_operations_total',
    'Total permission management operations',
    ['operation', 'status']  # operation: grant, revoke, create; status: success, failed
)

# Permission grants by type (analytics)
permission_grants_by_type = Counter(
    'auth_api_permission_grants_by_type_total',
    'Permission grants breakdown by resource:action',
    ['resource', 'action']
)

# Permission revocations by type (analytics)
permission_revocations_by_type = Counter(
    'auth_api_permission_revocations_by_type_total',
    'Permission revocations breakdown by resource:action',
    ['resource', 'action']
)

# RBAC business metrics
total_groups = Gauge(
    'auth_api_total_groups',
    'Total number of groups across all organizations'
)

total_permissions = Gauge(
    'auth_api_total_permissions',
    'Total number of system-wide permissions'
)

total_group_memberships = Gauge(
    'auth_api_total_group_memberships',
    'Total number of user-group memberships'
)

total_permission_grants = Gauge(
    'auth_api_total_permission_grants',
    'Total number of group-permission grants'
)


# ========== Helper Functions ==========

class MetricsTimer:
    """Context manager for timing operations."""

    def __init__(self, histogram, *labels):
        self.histogram = histogram
        self.labels = labels
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.histogram.labels(*self.labels).observe(duration)
        return False


def track_registration(status: str):
    """Track user registration event."""
    registrations_total.labels(status=status).inc()


def track_login(status: str):
    """Track login attempt."""
    login_attempts_total.labels(status=status).inc()


def track_email_verification(status: str):
    """Track email verification."""
    email_verifications_total.labels(status=status).inc()


def track_password_reset(stage: str):
    """Track password reset operation."""
    password_resets_total.labels(stage=stage).inc()


def track_2fa_operation(operation: str, status: str):
    """Track 2FA operation."""
    twofa_operations_total.labels(operation=operation, status=status).inc()


def track_token_operation(operation: str, status: str):
    """Track token operation."""
    token_operations_total.labels(operation=operation, status=status).inc()


def track_rate_limit_hit(endpoint: str, ip: str):
    """Track rate limit hit."""
    # Truncate IP to first 3 octets for privacy
    ip_prefix = '.'.join(ip.split('.')[:3]) + '.xxx' if '.' in ip else 'unknown'
    rate_limit_hits_total.labels(endpoint=endpoint, ip=ip_prefix).inc()


def track_request_size_violation(endpoint: str):
    """Track request size limit violation."""
    request_size_violations_total.labels(endpoint=endpoint).inc()


def track_password_validation_failure(reason: str):
    """Track password validation failure."""
    password_validation_failures_total.labels(reason=reason).inc()


def track_db_query(operation: str, status: str):
    """Track database query."""
    db_queries_total.labels(operation=operation, status=status).inc()


def track_redis_operation(operation: str, status: str):
    """Track Redis operation."""
    redis_operations_total.labels(operation=operation, status=status).inc()


def track_email_operation(email_type: str, status: str):
    """Track email operation."""
    email_operations_total.labels(type=email_type, status=status).inc()


# ========== RBAC Helper Functions (Sprint 2) ==========

def track_authz_check(result: str, resource: str, action: str):
    """
    Track authorization check via THE CORE /authorize endpoint.

    Args:
        result: 'granted', 'denied_not_member', or 'denied_no_permission'
        resource: Resource being accessed (e.g., 'activity', 'user')
        action: Action being performed (e.g., 'create', 'read', 'update', 'delete')

    Example:
        track_authz_check('granted', 'activity', 'create')
        track_authz_check('denied_no_permission', 'activity', 'delete')
    """
    authz_checks_total.labels(result=result, resource=resource, action=action).inc()


def track_permission_lookup(status: str):
    """
    Track permission lookup operation (get user permissions).

    Args:
        status: 'success' or 'failed'
    """
    permission_lookups_total.labels(status=status).inc()


def track_group_operation(operation: str, status: str):
    """
    Track group management operation.

    Args:
        operation: 'create', 'update', 'delete', 'add_member', 'remove_member'
        status: 'success' or 'failed'

    Example:
        track_group_operation('create', 'success')
        track_group_operation('add_member', 'failed')
    """
    group_operations_total.labels(operation=operation, status=status).inc()


def track_permission_operation(operation: str, status: str):
    """
    Track permission management operation.

    Args:
        operation: 'grant', 'revoke', 'create'
        status: 'success' or 'failed'

    Example:
        track_permission_operation('grant', 'success')
        track_permission_operation('revoke', 'success')
    """
    permission_operations_total.labels(operation=operation, status=status).inc()


def track_permission_grant(resource: str, action: str):
    """
    Track permission grant by type (for analytics).

    Args:
        resource: Resource (e.g., 'activity', 'user')
        action: Action (e.g., 'create', 'read')

    Example:
        track_permission_grant('activity', 'create')
    """
    permission_grants_by_type.labels(resource=resource, action=action).inc()


def track_permission_revocation(resource: str, action: str):
    """
    Track permission revocation by type (for analytics).

    Args:
        resource: Resource (e.g., 'activity', 'user')
        action: Action (e.g., 'create', 'read')

    Example:
        track_permission_revocation('activity', 'delete')
    """
    permission_revocations_by_type.labels(resource=resource, action=action).inc()
