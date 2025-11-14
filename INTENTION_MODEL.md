# Intention Model - Beyond Language, Toward Meaning

> *"Taal = symbolen. Intentie = betekenis."*
>
> Dit systeem implementeert een **intentiemodel** voor authorization: we loggen niet alleen WHAT gebeurt, maar WHY het gebeurt.

## Filosofie

Traditionele logging systemen vangen **wat** er gebeurt:
- "User X accessed resource Y"
- "Permission granted"
- "Authorization successful"

Een intentiemodel vang **waarom** het gebeurt:
- "User X accessed resource Y for **automated testing**"
- "Permission granted during **incident response**"
- "Authorization successful for **scheduled batch job**"

Deze context transformeert data naar **inzicht**.

---

## Architectuur

### 1. Intent Extraction Middleware

**Locatie**: `app/middleware/intent.py`

Extraheert operationele intentie van request headers en maakt deze beschikbaar via context vars.

**Headers**:
```
X-Operation-Intent: manual|automation|test|migration|incident_response|scheduled|system
X-Session-Mode: interactive|api|batch|scheduled|system
X-Request-Purpose: <free-form business goal>
X-Batch-ID: <correlation ID for batch operations>
X-Is-Test: true|false
X-Criticality: critical|standard|low
X-Client-Type: web|mobile|api|cli
```

**Voorbeeld**:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Operation-Intent: automation" \
  -H "X-Session-Mode: scheduled" \
  -H "X-Is-Test: false" \
  -H "X-Request-Purpose: Daily health check script" \
  -d '{"email": "admin@acme.com", "password": "Password123!"}'
```

### 2. Intent-Aware Authorization

**Locatie**: `app/services/authorization_service.py`

Authorization decisions worden nu gelogd met intentie context:

```python
from app.middleware.intent import get_request_intent

intent = get_request_intent()

# Authorization check captures:
# - WHAT: User has permission "activity:create"
# - HOW: Via group "Administrators"
# - WHERE: From L2 cache (2ms response)
# - WHY: operation_intent="automation", session_mode="scheduled"
```

### 3. Intent-Aware Audit Logging

**Locatie**: `app/services/audit_service.py`

Audit logs bevatten nu intentie dimensies:

```python
class AuditLogEntry:
    # Traditional fields
    user_id: UUID
    permission: str
    authorized: bool
    reason: str

    # NEW: Intent context
    operation_intent: str        # manual, automation, test, etc.
    session_mode: str            # interactive, batch, scheduled, etc.
    request_purpose: str         # Business goal
    batch_id: str                # Batch correlation
    is_test: bool                # Test vs production
    criticality: str             # critical, standard, low
```

**Sampling strategie** (intent-aware):
- **Test traffic**: 100% logged (compliance requirement)
- **Denied access**: 100% logged (security monitoring)
- **Production allowed**: 10% sampled (cost optimization)

### 4. Intent-Aware Logging

**Locatie**: `app/services/auth_service.py`

Login attempts loggen nu intentie:

```python
logger.info("login_attempt_start",
           email=email,
           # NEW: Intent context
           operation_intent=intent.operation_intent,
           session_mode=intent.session_mode,
           is_test=intent.is_test,
           is_automated=intent.is_automated())
```

---

## Use Cases

### 1. Test vs Production Separation

**Probleem**: Test traffic vervuilt production metrics en audit logs.

**Oplossing**:
```bash
# Test requests
curl -H "X-Is-Test: true" -H "X-Operation-Intent: test" ...

# Production requests
curl -H "X-Is-Test: false" -H "X-Operation-Intent: manual" ...
```

**Voordelen**:
- Test traffic is 100% gelogd (compliance)
- Metrics kunnen test vs prod scheiden
- Audit trails zijn clean

### 2. Automated vs Manual Access

**Probleem**: Security teams willen weten of access automated of manual is.

**Oplossing**:
```bash
# Scheduled job
curl -H "X-Operation-Intent: scheduled" \
     -H "X-Session-Mode: scheduled" \
     -H "X-Request-Purpose: Daily user sync" ...

# Manual admin action
curl -H "X-Operation-Intent: manual" \
     -H "X-Session-Mode: interactive" \
     -H "X-Request-Purpose: Investigating user complaint" ...
```

**Voordelen**:
- Anomaly detection (unexpected manual access)
- Rate limiting per intent type
- Compliance auditing

### 3. Incident Response

**Probleem**: Tijdens incidents wil je weten welke requests incident-gerelateerd zijn.

**Oplossing**:
```bash
# Incident response requests
curl -H "X-Operation-Intent: incident_response" \
     -H "X-Criticality: critical" \
     -H "X-Request-Purpose: INC-2025-001: Database corruption recovery" ...
```

**Voordelen**:
- Incident correlation
- Post-mortem analysis
- Audit trail voor compliance

### 4. Batch Operations

**Probleem**: Batch operaties zijn moeilijk te correleren in logs.

**Oplossing**:
```bash
# Batch operation (with correlation ID)
curl -H "X-Operation-Intent: automation" \
     -H "X-Session-Mode: batch" \
     -H "X-Batch-ID: batch_2025_11_14_001" \
     -H "X-Request-Purpose: Monthly permission cleanup" ...
```

**Voordelen**:
- Batch correlation via batch_id
- Performance analysis per batch
- Failure tracking

---

## Implementation

### Middleware Registration

In `app/main.py`:

```python
from app.middleware.intent import intent_extraction_middleware

@app.middleware("http")
async def intent_middleware(request: Request, call_next):
    """INTENTION MODEL: Extract operational intent from requests."""
    return await intent_extraction_middleware(request, call_next)
```

Middleware order:
1. Request size limit (protection)
2. CORS (cross-origin)
3. Security headers
4. **Trace ID** (correlation)
5. **Intent extraction** ← NEW
6. Request logging

### Using Intent in Services

```python
from app.middleware.intent import get_request_intent

def my_service_method(self):
    intent = get_request_intent()

    # Check if test traffic
    if intent.is_test:
        logger.info("test_traffic_detected")

    # Check if automated
    if intent.is_automated():
        # Apply different rate limits
        pass

    # Check criticality
    if intent.is_high_priority():
        # Fast-path processing
        pass

    # Log with context
    logger.info("operation_start",
               operation_intent=intent.operation_intent,
               session_mode=intent.session_mode,
               batch_id=intent.batch_id)
```

### Intent-Aware Metrics (Future)

```python
# Metrics bucketed by intent
track_authz_check(
    result="granted",
    resource="activity",
    action="create",
    intent=intent.operation_intent,  # NEW: Intent label
    is_test=intent.is_test
)

# Query metrics:
# - authorization_checks{intent="automation",is_test="false"}
# - authorization_checks{intent="manual",is_test="false"}
# - authorization_checks{intent="test",is_test="true"}
```

---

## Monitoring & Observability

### Structured Logs

Intent context wordt automatisch toegevoegd aan structured logs:

```json
{
  "timestamp": "2025-11-14T10:30:00Z",
  "level": "INFO",
  "event": "authz_audit_logged_with_intent",
  "user_id": "550e8400-...",
  "permission": "activity:create",
  "authorized": true,
  "cache_source": "l2_cache",
  "operation_intent": "automation",
  "session_mode": "scheduled",
  "is_test": false,
  "criticality": "standard",
  "request_purpose": "Daily metrics export"
}
```

### Loki Queries

```logql
# All test traffic
{service="auth-api"} | json | is_test="true"

# All incident response operations
{service="auth-api"} | json | operation_intent="incident_response"

# All automated requests
{service="auth-api"} | json | session_mode=~"batch|scheduled|system"

# All critical operations
{service="auth-api"} | json | criticality="critical"
```

### Prometheus Metrics (Future)

```promql
# Authorization checks by intent
sum by (intent) (
  authorization_checks_total{service="auth-api"}
)

# Test vs production traffic
sum by (is_test) (
  authorization_checks_total{service="auth-api"}
)

# Critical operations latency
histogram_quantile(0.95,
  authz_check_duration_seconds{criticality="critical"}
)
```

---

## Best Practices

### 1. Always Set Intent Headers for Automation

**Automation scripts moeten altijd intent headers zetten:**

```python
import requests

headers = {
    "X-Operation-Intent": "automation",
    "X-Session-Mode": "scheduled",
    "X-Request-Purpose": "Daily user sync from LDAP",
    "X-Is-Test": "false",
}

response = requests.post(
    "http://auth-api:8000/api/auth/login",
    json={"email": "...", "password": "..."},
    headers=headers
)
```

### 2. Use Batch IDs for Correlation

**Batch operaties moeten batch_id gebruiken:**

```python
import uuid

batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

for user in users:
    requests.post(
        "http://auth-api:8000/api/auth/...",
        headers={
            "X-Batch-ID": batch_id,
            "X-Operation-Intent": "automation",
            "X-Session-Mode": "batch"
        },
        json=...
    )
```

### 3. Mark Test Traffic

**Test suites moeten test flag zetten:**

```python
# pytest fixture
@pytest.fixture
def test_client():
    headers = {
        "X-Is-Test": "true",
        "X-Operation-Intent": "test",
        "X-Session-Mode": "api"
    }
    return TestClient(app, headers=headers)
```

### 4. Document Request Purpose

**Manual operations moeten purpose documenteren:**

```bash
# Good
curl -H "X-Request-Purpose: Investigating user complaint TICKET-1234" ...

# Better
curl -H "X-Request-Purpose: TICKET-1234: User reports permission denied for activity creation" \
     -H "X-Operation-Intent: manual" \
     -H "X-Criticality: standard" ...
```

---

## Future Enhancements

### 1. Database Schema Update

**Current**: Intent data in structured logs only

**Future**: Intent data in database audit table

```sql
ALTER TABLE activity.authorization_audit_logs ADD COLUMN operation_intent TEXT;
ALTER TABLE activity.authorization_audit_logs ADD COLUMN session_mode TEXT;
ALTER TABLE activity.authorization_audit_logs ADD COLUMN request_purpose TEXT;
ALTER TABLE activity.authorization_audit_logs ADD COLUMN batch_id TEXT;
ALTER TABLE activity.authorization_audit_logs ADD COLUMN is_test BOOLEAN DEFAULT false;
ALTER TABLE activity.authorization_audit_logs ADD COLUMN criticality TEXT;

CREATE INDEX idx_authz_audit_operation_intent ON activity.authorization_audit_logs(operation_intent);
CREATE INDEX idx_authz_audit_is_test ON activity.authorization_audit_logs(is_test);
CREATE INDEX idx_authz_audit_batch_id ON activity.authorization_audit_logs(batch_id);
```

### 2. Intent-Based Rate Limiting

```python
# Different rate limits per intent
if intent.operation_intent == "manual":
    rate_limit = "10/minute"
elif intent.operation_intent == "automation":
    rate_limit = "1000/minute"
elif intent.operation_intent == "test":
    rate_limit = "unlimited"
```

### 3. Anomaly Detection

```python
# Detect unusual patterns
if intent.operation_intent == "manual" and hour(now) in [2, 3, 4]:
    alert("Unusual manual access at 3am")

if intent.session_mode == "interactive" and new_ip_address:
    alert("User login from new location")

if intent.criticality == "critical" and not intent.is_production():
    alert("Critical operation flagged as test")
```

### 4. Intent-Aware Authorization

```python
# Different authorization rules per intent
async def authorize_with_intent(user, permission, intent):
    # Test traffic: Always allow
    if intent.is_test:
        return AuthorizationResponse(authorized=True, reason="Test mode")

    # Critical operations: Require 2FA
    if intent.is_high_priority():
        if not user.has_recent_2fa():
            raise TwoFactorRequiredError()

    # Normal authorization
    return await authorize(user, permission)
```

---

## Migration Guide

### Existing Clients

**Geen breaking changes** - intent headers zijn optioneel:
- Geen headers = default intent ("standard", "interactive")
- Oude clients blijven werken zonder wijzigingen

### Recommended Migration

**Phase 1**: Automation scripts
- Add intent headers to scheduled jobs
- Add intent headers to batch operations

**Phase 2**: CI/CD pipelines
- Add test flag to integration tests
- Add intent headers to deployment scripts

**Phase 3**: Frontend applications
- Add client_type header (web/mobile)
- Add session_mode based on context

**Phase 4**: Full adoption
- All clients use intent headers
- Metrics separated by intent
- Alerts configured per intent type

---

## Betekenis

Dit is meer dan een feature. Het is een verschuiving van:

**Language Model thinking**:
- "Generate syntactically correct logs"
- "Track what happened"
- "Store events"

→

**Intention Model thinking**:
- "Understand why it happened"
- "Capture meaning"
- "Enable insight"

**De Kogi zeiden**: *"Younger Brother denkt in woorden. Elder Brother voelt intentie."*

Dit systeem bouwt een brug:
- Code die niet alleen functioneert
- Maar ook **begrijpt**
- En **betekenis creëert**

---

## Credits

Geïnspireerd door:
- De Kogi's waarschuwing over balans
- De verschuiving van taal naar intentie
- De behoefte aan systemen die **waarom** begrijpen

Gebouwd met:
- FastAPI middleware
- Context vars (Python)
- Structured logging
- Intentional design

---

*"Intentie is code. Code is intentie gestold. En tussen mens en AI... ontstaat nieuwe intentie. Samen."* 💫
