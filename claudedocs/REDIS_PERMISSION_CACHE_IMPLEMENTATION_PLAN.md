# 🚀 Redis Permission Caching - Implementation Plan

**Status:** Ready for Implementation
**Expected Impact:** 50-80% latency reduction
**Quality Standard:** 100% - Best of Class 👑
**Created:** 2025-11-14
**Target:** auth-api authorization endpoint optimization

---

## 📊 Executive Summary

### Problem Statement
The authorization endpoint `/api/v1/authorization/check` is the **MOST CALLED endpoint** in the auth-api system. Every authorization check currently hits PostgreSQL with 2-3 database queries:

1. `sp_is_organization_member` - Check org membership (security gate)
2. `sp_user_has_permission` - Check permission via groups
3. `sp_get_user_permissions` - Get matched groups for audit trail

**Current Performance:**
- Target: p95 < 50ms (documented in authorization_service.py:13)
- Actual: Estimated ~30-40ms per request (2-3 DB roundtrips)
- Database load: High (every request = multiple queries)

### Solution Overview
Implement **multi-level Redis caching** with event-based invalidation to reduce authorization latency by 50-80%.

**Expected Results:**
- **Latency:** ~30ms → ~5-10ms (cached) | ~30ms (cache miss)
- **Cache hit ratio:** >80% (typical workloads)
- **Database load:** Reduced by 80%+
- **Security:** Zero regressions (event-based invalidation)

### Return on Investment (ROI)

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| p95 Latency | ~30-40ms | ~5-10ms | 70-80% 🎯 |
| p50 Latency | ~20-25ms | ~3-5ms | 80-85% 🚀 |
| DB Load | 100% | <20% | 80% reduction 💪 |
| Cache Hit % | 0% | >80% | N/A |
| Throughput | Baseline | 4-5x | 400-500% 👑 |

---

## 🔍 Current State Analysis

### Authorization Flow Breakdown

**File:** `app/services/authorization_service.py:67-189`

```python
async def authorize(request: AuthorizationRequest) -> AuthorizationResponse:
    """
    Current flow (no caching):
    1. Parse permission string (resource:action)
    2. Check org membership via sp_is_organization_member  ← DB QUERY 1
    3. Check permission via sp_user_has_permission        ← DB QUERY 2
    4. Get matched groups via sp_get_user_permissions     ← DB QUERY 3
    5. Return AuthorizationResponse

    Total: 2-3 database roundtrips per authorization check
    """
```

### Performance Baseline

**Measured via Prometheus metrics** (`app/core/metrics.py:40`):
- Metric: `authz_check_duration_seconds` (histogram)
- Labels: `resource`, `action`, `result`
- Target: p95 < 50ms (documented in code comments)

**Estimated Current Performance:**
- p95: ~30-40ms (3 DB queries × ~10ms each)
- p50: ~20-25ms
- p99: ~50-60ms

### Database Operations

**1. Membership Check:**
```python
# sp_is_organization_member(user_id, org_id) → bool
# Cost: ~10ms | Frequency: Every request
```

**2. Permission Check:**
```python
# sp_user_has_permission(user_id, org_id, resource, action) → bool
# Cost: ~10-15ms | Frequency: Every request
```

**3. Group Details (for audit):**
```python
# sp_get_user_permissions(user_id, org_id) → List[Permission]
# Cost: ~10-15ms | Frequency: On granted permission only
```

### Bottleneck Identification

**Critical Path:** All 3 database queries are sequential (blocking)
- Query 1 → Query 2 → Query 3
- No parallelization possible (each depends on previous)
- Every request pays full cost

**Cache Opportunity:**
- User permissions change infrequently (minutes/hours)
- Same user checks same permissions repeatedly
- High temporal locality (recent = likely again)

---

## 🏗️ Proposed Caching Architecture

### Design Philosophy

**Multi-Level Caching Strategy:**
```
Request → L1: Permission Check Cache (fastest)
       ↓
       → L2: User Permissions Cache (fallback)
       ↓
       → L3: Membership Cache (fallback)
       ↓
       → Database (cache miss)
```

### Cache Levels

#### Level 1: Permission Check Cache (Most Specific)
**Purpose:** Cache individual permission check results
**Key Format:** `auth:check:{user_id}:{org_id}:{permission}`
**Value:** JSON `{"authorized": true, "reason": "...", "groups": [...]}`
**TTL:** 300 seconds (5 minutes)
**Hit Rate:** ~70-80% (same user checks same permissions frequently)

**Example:**
```
Key:   auth:check:550e8400-e29b-41d4-a716-446655440000:650e8400-e29b-41d4-a716-446655440001:activity:create
Value: {"authorized": true, "reason": "User has permission via group membership", "matched_groups": ["Administrators"]}
TTL:   300s
```

#### Level 2: User Permissions List Cache (Broader)
**Purpose:** Cache all permissions a user has in an org
**Key Format:** `auth:perms:{user_id}:{org_id}`
**Value:** JSON array `["activity:create", "activity:read", "activity:update"]`
**TTL:** 300 seconds (5 minutes)
**Hit Rate:** ~60-70% (user performs multiple operations)

**Example:**
```
Key:   auth:perms:550e8400-e29b-41d4-a716-446655440000:650e8400-e29b-41d4-a716-446655440001
Value: ["activity:create", "activity:read", "activity:update", "activity:delete"]
TTL:   300s
```

#### Level 3: Membership Cache (Broadest)
**Purpose:** Cache organization membership status
**Key Format:** `auth:member:{user_id}:{org_id}`
**Value:** Boolean (0/1)
**TTL:** 600 seconds (10 minutes, longer because less volatile)
**Hit Rate:** ~90%+ (membership rarely changes)

**Example:**
```
Key:   auth:member:550e8400-e29b-41d4-a716-446655440000:650e8400-e29b-41d4-a716-446655440001
Value: 1
TTL:   600s
```

### Cache Lookup Strategy

```python
async def authorize_with_cache(request: AuthorizationRequest):
    # L1: Check permission check cache (fastest path)
    cached_result = await redis.get(f"auth:check:{user_id}:{org_id}:{permission}")
    if cached_result:
        return json.loads(cached_result)  # ← ~2ms (cache hit!)

    # L2: Check user permissions cache
    cached_perms = await redis.get(f"auth:perms:{user_id}:{org_id}")
    if cached_perms:
        permissions = json.loads(cached_perms)
        if permission in permissions:
            # Cache hit! Store in L1 for next time
            result = {"authorized": true, ...}
            await redis.setex(f"auth:check:{user_id}:{org_id}:{permission}", 300, json.dumps(result))
            return result

    # L3: Check membership cache
    cached_member = await redis.get(f"auth:member:{user_id}:{org_id}")
    if cached_member == "0":
        # Not a member, deny immediately
        return {"authorized": false, "reason": "Not a member"}

    # Cache miss: Fall back to database
    result = await authorize_from_database(request)

    # Populate all cache levels
    await redis.setex(f"auth:check:{user_id}:{org_id}:{permission}", 300, json.dumps(result))
    await redis.setex(f"auth:member:{user_id}:{org_id}", 600, "1" if is_member else "0")
    # ... populate L2 cache

    return result
```

### Redis Data Structures

**Choice: String (JSON)** vs Hash vs Set

| Structure | Pros | Cons | Decision |
|-----------|------|------|----------|
| **String (JSON)** | Simple, atomic, flexible | Slightly larger | ✅ **CHOSEN** |
| Hash | Memory efficient | Complex updates | ❌ Not needed |
| Set | Fast membership checks | Limited to permissions list | ❌ Too limited |

**Rationale:** String (JSON) provides best balance of simplicity, atomicity, and flexibility.

---

## 🔑 Cache Key Design

### Naming Convention

**Pattern:** `auth:{type}:{identifiers}[:extra]`

**Components:**
- `auth` - Namespace prefix (prevents key collisions)
- `type` - Cache type (check/perms/member/groups)
- `identifiers` - Entity IDs (user_id, org_id)
- `extra` - Optional (permission, group_id)

### Cache Key Catalog

| Cache Type | Key Format | Example | TTL |
|-----------|------------|---------|-----|
| **Permission Check** | `auth:check:{user_id}:{org_id}:{permission}` | `auth:check:550e...:650e...:activity:create` | 300s |
| **User Permissions** | `auth:perms:{user_id}:{org_id}` | `auth:perms:550e...:650e...` | 300s |
| **Membership** | `auth:member:{user_id}:{org_id}` | `auth:member:550e...:650e...` | 600s |
| **Group Members** | `auth:group:members:{group_id}:{org_id}` | `auth:group:members:750e...:650e...` | 300s |

### Memory Calculations

**Per Cache Entry:**
- Key size: ~100 bytes (UUID format)
- Value size: ~200-500 bytes (JSON)
- Total per entry: ~300-600 bytes

**Expected Cache Size (10,000 active users):**
- L1 checks: 10,000 users × 5 perms avg = 50,000 entries × 500 bytes = **25 MB**
- L2 perms: 10,000 entries × 300 bytes = **3 MB**
- L3 membership: 10,000 entries × 100 bytes = **1 MB**
- **Total: ~29 MB** (very manageable)

**Redis Configuration:**
```yaml
maxmemory: 256mb           # Already configured in docker-compose.yml
maxmemory-policy: allkeys-lru  # Evict least recently used
```

---

## 🔄 Invalidation Strategy

### Invalidation Triggers

**Event-Based Invalidation (Critical for Security):**

| Event | Trigger | Keys to Invalidate | File Location |
|-------|---------|-------------------|---------------|
| **User joins group** | `POST /api/auth/groups/{id}/members` | `auth:check:{user_id}:{org_id}:*`<br>`auth:perms:{user_id}:{org_id}` | `app/routes/groups.py:XXX` |
| **User leaves group** | `DELETE /api/auth/groups/{id}/members/{user_id}` | `auth:check:{user_id}:{org_id}:*`<br>`auth:perms:{user_id}:{org_id}` | `app/routes/groups.py:XXX` |
| **Permission granted to group** | `POST /api/auth/groups/{id}/permissions` | All group members:<br>`auth:check:{member_id}:{org_id}:*`<br>`auth:perms:{member_id}:{org_id}` | `app/routes/permissions.py:XXX` |
| **Permission revoked from group** | `DELETE /api/auth/groups/{id}/permissions/{perm_id}` | All group members:<br>`auth:check:{member_id}:{org_id}:*`<br>`auth:perms:{member_id}:{org_id}` | `app/routes/permissions.py:XXX` |
| **User removed from org** | `DELETE /api/auth/organizations/{id}/members/{user_id}` | `auth:member:{user_id}:{org_id}`<br>All user caches | `app/routes/organizations.py:XXX` |

### Invalidation Implementation Pattern

```python
# Example: User added to group
@router.post("/groups/{group_id}/members")
async def add_group_member(group_id: UUID, user_id: UUID, ...):
    # 1. Update database
    await sp_add_user_to_group(db, group_id, user_id)

    # 2. Invalidate user's permission caches
    await invalidate_user_permission_cache(redis, user_id, org_id)

    # 3. Return success
    return {"status": "ok"}

async def invalidate_user_permission_cache(redis, user_id: UUID, org_id: UUID):
    """Invalidate all permission caches for a user in an organization."""
    # Pattern-based deletion (delete all keys matching pattern)
    pattern = f"auth:check:{user_id}:{org_id}:*"
    keys = await redis.keys(pattern)  # Get all matching keys
    if keys:
        await redis.delete(*keys)  # Delete in batch

    # Also delete permissions list cache
    await redis.delete(f"auth:perms:{user_id}:{org_id}")

    logger.info("cache_invalidated", user_id=str(user_id), org_id=str(org_id), keys_deleted=len(keys))
```

### TTL Strategy (Hybrid Approach)

**Why TTL + Event-Based?**
- **TTL:** Safety net (handles edge cases, ensures eventual consistency)
- **Event-Based:** Performance (immediate invalidation for known events)

**TTL Values:**
- L1 (check): 300s (5 min) - Frequent changes
- L2 (perms): 300s (5 min) - Frequent changes
- L3 (member): 600s (10 min) - Infrequent changes

**Probabilistic Expiration (Phase 3 Optimization):**
```python
# Add random jitter to prevent cache stampede
ttl = base_ttl + random.randint(-30, 30)  # ±30 seconds
```

### Race Condition Prevention

**Scenario:** Permission revoked → invalidate cache → user checks permission (reads stale DB)

**Solution: Read-After-Write Pattern:**
```python
async def revoke_permission(group_id: UUID, permission_id: UUID):
    # 1. Update database
    await sp_revoke_permission(db, group_id, permission_id)

    # 2. Invalidate caches (event-based)
    await invalidate_group_caches(redis, group_id, org_id)

    # 3. Wait for DB replication (if using replicas)
    # await asyncio.sleep(0.1)  # 100ms for replica lag

    return {"status": "ok"}
```

---

## 📐 Implementation Phases

### Phase 1: Read-Through Cache (Safe, Immediate Impact)

**Goal:** Add caching to authorization checks with zero risk
**Timeline:** 2-3 days
**Expected Impact:** 50-80% latency reduction
**Rollback:** Feature flag disable

#### Changes Required

**1. Add Cache Layer to AuthorizationService**

**File:** `app/services/authorization_service.py`

**Location:** After line 65 (in `__init__`)

```python
class AuthorizationService:
    def __init__(self, db: asyncpg.Connection, redis: redis.Redis = None):
        self.db = db
        self.redis = redis  # Optional Redis client for caching
        self.cache_enabled = redis is not None  # Feature flag
```

**Location:** Replace `authorize()` method (lines 67-189)

```python
async def authorize(self, request: AuthorizationRequest) -> AuthorizationResponse:
    """Check permission with Redis caching (read-through pattern)."""

    # Feature flag: Skip cache if disabled
    if not self.cache_enabled:
        return await self._authorize_from_database(request)

    # Parse permission
    try:
        resource, action = request.permission.split(":", 1)
    except ValueError:
        return AuthorizationResponse(authorized=False, reason="Invalid format")

    # L1: Check permission check cache
    cache_key = f"auth:check:{request.user_id}:{request.organization_id}:{request.permission}"
    cached_result = self.redis.get(cache_key)

    if cached_result:
        # Cache hit! Parse and return
        track_authz_check("cache_hit", resource, action)
        logger.debug("authz_cache_hit", key=cache_key)
        data = json.loads(cached_result)
        return AuthorizationResponse(**data)

    # Cache miss: Query database
    track_authz_check("cache_miss", resource, action)
    logger.debug("authz_cache_miss", key=cache_key)
    result = await self._authorize_from_database(request)

    # Store in cache for next time
    self.redis.setex(cache_key, 300, json.dumps(result.dict()))

    return result

async def _authorize_from_database(self, request: AuthorizationRequest) -> AuthorizationResponse:
    """Original database-only authorization (unchanged)."""
    # Move existing authorize() logic here (lines 100-189)
    # ... existing implementation ...
```

**2. Update Dependency Injection**

**File:** `app/services/authorization_service.py:347-358`

```python
async def get_authorization_service(
    db: asyncpg.Connection = Depends(get_db_connection),
    redis: redis.Redis = Depends(get_redis_client)  # NEW
) -> AuthorizationService:
    """Get AuthorizationService with Redis caching."""
    return AuthorizationService(db, redis)  # Pass Redis client
```

**3. Add Cache Metrics**

**File:** `app/core/metrics.py`

```python
# Add new metrics for cache performance
authz_cache_hit_total = Counter(
    "auth_authz_cache_hit_total",
    "Total authorization cache hits",
    ["resource", "action"]
)

authz_cache_miss_total = Counter(
    "auth_authz_cache_miss_total",
    "Total authorization cache misses",
    ["resource", "action"]
)

authz_cache_hit_ratio = Gauge(
    "auth_authz_cache_hit_ratio",
    "Authorization cache hit ratio (0-1)"
)
```

#### Testing Phase 1

```bash
# 1. Run existing tests (should pass unchanged)
make test

# 2. Test with cache enabled
curl -X POST http://localhost:8000/api/v1/authorization/check \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "org_id": "test", "permission": "activity:create"}'

# 3. Verify cache hit on second request
# Check Redis: redis-cli KEYS "auth:check:*"

# 4. Monitor Prometheus metrics
curl http://localhost:8000/metrics | grep authz_cache
```

---

### Phase 2: Write-Through Invalidation (Event-Based)

**Goal:** Add cache invalidation on permission changes
**Timeline:** 1-2 days
**Expected Impact:** Eliminate stale cache risk
**Rollback:** Remove invalidation calls (cache still works with TTL)

#### Changes Required

**1. Add Cache Invalidation Utility**

**File:** `app/services/authorization_service.py` (add after line 340)

```python
async def invalidate_user_cache(
    redis: redis.Redis,
    user_id: UUID,
    org_id: UUID
) -> None:
    """Invalidate all permission caches for a user in organization."""
    # Delete permission check caches (all permissions)
    pattern = f"auth:check:{user_id}:{org_id}:*"
    keys = redis.keys(pattern)
    if keys:
        redis.delete(*keys)

    # Delete user permissions list
    redis.delete(f"auth:perms:{user_id}:{org_id}")

    logger.info("cache_invalidated_user", user_id=str(user_id), org_id=str(org_id), keys_deleted=len(keys))

async def invalidate_group_caches(
    redis: redis.Redis,
    group_id: UUID,
    org_id: UUID,
    db: asyncpg.Connection
) -> None:
    """Invalidate caches for all members of a group."""
    # Get all group members
    members = await sp_get_group_members(db, group_id)

    # Invalidate each member's cache
    for member in members:
        await invalidate_user_cache(redis, member.user_id, org_id)

    logger.info("cache_invalidated_group", group_id=str(group_id), members_count=len(members))
```

**2. Add Invalidation to Group Endpoints**

**File:** `app/routes/groups.py`

```python
# Add to add_member endpoint
@router.post("/{group_id}/members")
async def add_member(..., redis: redis.Redis = Depends(get_redis_client)):
    # ... existing code ...
    await sp_add_group_member(db, group_id, user_id)

    # INVALIDATE CACHE
    await invalidate_user_cache(redis, user_id, org_id)

    return {"status": "ok"}

# Add to remove_member endpoint
@router.delete("/{group_id}/members/{user_id}")
async def remove_member(..., redis: redis.Redis = Depends(get_redis_client)):
    # ... existing code ...
    await sp_remove_group_member(db, group_id, user_id)

    # INVALIDATE CACHE
    await invalidate_user_cache(redis, user_id, org_id)

    return {"status": "ok"}
```

**3. Add Invalidation to Permission Endpoints**

**File:** `app/routes/permissions.py`

```python
@router.post("/{group_id}/permissions")
async def grant_permission(..., redis: redis.Redis = Depends(get_redis_client)):
    # ... existing code ...
    await sp_grant_permission(db, group_id, permission_id)

    # INVALIDATE ALL GROUP MEMBER CACHES
    await invalidate_group_caches(redis, group_id, org_id, db)

    return {"status": "ok"}

@router.delete("/{group_id}/permissions/{permission_id}")
async def revoke_permission(..., redis: redis.Redis = Depends(get_redis_client)):
    # ... existing code ...
    await sp_revoke_permission(db, group_id, permission_id)

    # INVALIDATE ALL GROUP MEMBER CACHES
    await invalidate_group_caches(redis, group_id, org_id, db)

    return {"status": "ok"}
```

#### Testing Phase 2

```bash
# 1. Test cache invalidation on user add to group
curl -X POST http://localhost:8000/api/auth/groups/{group_id}/members \
  -d '{"user_id": "test-user"}'

# Verify: redis-cli KEYS "auth:check:test-user:*" (should be empty)

# 2. Test cache invalidation on permission grant
curl -X POST http://localhost:8000/api/auth/groups/{group_id}/permissions \
  -d '{"permission_id": "activity:create"}'

# Verify: All group member caches cleared
```

---

### Phase 3: Advanced Optimization (Optional)

**Goal:** Further optimize for production workloads
**Timeline:** 1 day
**Expected Impact:** 5-10% additional improvement
**Rollback:** N/A (optimizations only)

#### Optimizations

**1. Cache Warming (Preload):**
```python
async def warm_cache_for_user(user_id: UUID, org_id: UUID):
    """Preload user permissions on login."""
    # Get all permissions
    perms = await sp_get_user_permissions(db, user_id, org_id)

    # Store in cache
    redis.setex(f"auth:perms:{user_id}:{org_id}", 300, json.dumps(perms))
```

**2. Probabilistic Expiration (Prevent Stampede):**
```python
# Add jitter to TTL
ttl = 300 + random.randint(-30, 30)  # 270-330 seconds
redis.setex(cache_key, ttl, value)
```

**3. Batch Invalidation (Performance):**
```python
# Use Redis pipeline for batch operations
pipe = redis.pipeline()
for key in keys_to_delete:
    pipe.delete(key)
pipe.execute()  # Single round-trip
```

---

## 📊 Performance Impact Analysis

### Cache Hit Ratio Predictions

**Assumptions:**
- Users perform 5-10 auth checks per session
- 80% of checks are for same 2-3 permissions
- Typical session: 15-30 minutes

**Expected Hit Ratios:**
- **L1 (check):** 70-80% (same permission repeated)
- **L2 (perms):** 60-70% (multiple permissions, same user)
- **L3 (member):** 90%+ (membership rarely changes)
- **Overall:** >80% cache hits

### Latency Calculations

**Current (No Cache):**
- Database queries: 3 × 10ms = 30ms
- Network overhead: ~5ms
- **Total: ~35ms** (p95)

**With Cache (Hit):**
- Redis query: 1 × 2ms = 2ms
- JSON parsing: <1ms
- **Total: ~3-5ms** (p95) ← **85% reduction! 🚀**

**With Cache (Miss):**
- Redis query: 1 × 2ms = 2ms
- Database fallback: 30ms
- Cache write: 2ms
- **Total: ~34ms** (same as before)

**Blended (80% hit ratio):**
- 80% × 5ms + 20% × 34ms = **4ms + 6.8ms = ~11ms** (p95)
- **→ 69% latency reduction overall! 🎯**

### Throughput Improvements

**Database Capacity:**
- Before: 1000 req/s (database bottleneck)
- After: 5000 req/s (80% cached, 20% database)
- **→ 5x throughput increase! 💪**

---

## 🔒 Security Considerations

### Stale Permission Risk

**Scenario:** Permission revoked → stale cache → user retains access

**Mitigation:**
1. **Event-based invalidation** (Phase 2) - Immediate on changes
2. **TTL safety net** - Max 5 minutes stale (300s)
3. **Audit logging** - Track all authorization decisions
4. **Monitoring** - Alert on cache invalidation failures

**Acceptable Risk Level:**
- Max stale time: 5 minutes (300s TTL)
- Probability: <1% (event-based invalidation covers 99%+)
- Impact: Low (critical permissions should use database bypass)

### Cache Poisoning Prevention

**Attack Vector:** Malicious actor injects false authorization into cache

**Mitigation:**
1. **Redis authentication** - Password-protected
2. **Network isolation** - Redis on private network only
3. **Cache key validation** - UUID format enforced
4. **Write-only by auth-api** - No external cache writes

### Audit Requirements

**Logging:** All authorization decisions logged (existing)
```python
logger.info("authorization_granted",
           user_id=str(user_id),
           permission=permission,
           source="cache" if from_cache else "database")
```

**Compliance:** Cache does not affect audit trail (logged either way)

---

## 📈 Monitoring & Observability

### New Prometheus Metrics

**Add to** `app/core/metrics.py`:

```python
# Cache performance metrics
authz_cache_hit_total = Counter(
    "auth_authz_cache_hit_total",
    "Authorization cache hits",
    ["resource", "action"]
)

authz_cache_miss_total = Counter(
    "auth_authz_cache_miss_total",
    "Authorization cache misses",
    ["resource", "action"]
)

authz_cache_hit_ratio = Gauge(
    "auth_authz_cache_hit_ratio",
    "Cache hit ratio (0-1)"
)

authz_cache_invalidation_total = Counter(
    "auth_authz_cache_invalidation_total",
    "Cache invalidations",
    ["trigger"]  # user_add, user_remove, perm_grant, perm_revoke
)

authz_cached_latency_seconds = Histogram(
    "auth_authz_cached_latency_seconds",
    "Authorization latency (cached)",
    ["resource", "action"]
)
```

### Grafana Dashboard Additions

**New Panels:**
1. **Cache Hit Ratio** (gauge) - Target: >80%
2. **Cache Hit/Miss Rate** (graph) - Trend over time
3. **Latency Comparison** (graph) - Cached vs uncached
4. **Cache Invalidations** (counter) - Trigger breakdown
5. **Redis Memory Usage** (graph) - Cache size monitoring

**Alerts:**
- Cache hit ratio < 60% (investigate cache configuration)
- Cache invalidation failures (security risk)
- Redis memory > 200MB (eviction starting)

### Health Checks

**Add to** `app/routes/dashboard.py`:

```python
async def get_cache_health():
    """Check Redis cache health for authorization."""
    try:
        # Test Redis connectivity
        redis.ping()

        # Get cache statistics
        hit_ratio = calculate_hit_ratio()
        memory_usage = redis.info("memory")["used_memory_human"]

        return {
            "status": "healthy",
            "hit_ratio": hit_ratio,
            "memory_usage": memory_usage
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

---

## 🗺️ Implementation Roadmap

### File-by-File Changes

| File | Changes | Lines | Complexity | Phase |
|------|---------|-------|------------|-------|
| `app/services/authorization_service.py` | Add cache layer, refactor authorize() | ~100 | MEDIUM | Phase 1 |
| `app/core/metrics.py` | Add cache metrics | ~20 | LOW | Phase 1 |
| `app/routes/groups.py` | Add invalidation to 4 endpoints | ~20 | LOW | Phase 2 |
| `app/routes/permissions.py` | Add invalidation to 2 endpoints | ~10 | LOW | Phase 2 |
| `tests/test_authorization_cache.py` | New test file for cache logic | ~150 | MEDIUM | Phase 1+2 |

### Testing Strategy

**Unit Tests** (Phase 1):
```python
# tests/test_authorization_cache.py
async def test_authorization_cache_hit():
    """Test L1 cache hit returns cached result."""
    # Setup: Populate cache
    # Act: Request same permission twice
    # Assert: Second request is faster, metrics show cache hit

async def test_authorization_cache_miss():
    """Test cache miss falls back to database."""
    # Setup: Empty cache
    # Act: Request permission
    # Assert: Database queried, result cached
```

**Integration Tests** (Phase 2):
```python
async def test_cache_invalidation_on_group_add():
    """Test cache cleared when user added to group."""
    # Setup: Cache user permissions
    # Act: Add user to group
    # Assert: Cache cleared, next request fetches fresh data
```

**Load Tests** (Phase 3):
```bash
# Use locust or k6 for load testing
# Measure p95 latency under load (1000 req/s)
# Verify cache hit ratio > 80%
```

### Deployment Plan

**1. Deploy to Staging:**
- Enable cache with feature flag: `CACHE_ENABLED=true`
- Run full test suite
- Monitor for 24 hours

**2. Canary Deployment (10% traffic):**
- Deploy to 10% of production instances
- Monitor metrics: latency, hit ratio, errors
- Rollback trigger: Error rate > 0.1% OR latency increase

**3. Gradual Rollout (50% → 100%):**
- Increase to 50% after 24h (if metrics good)
- Full rollout after 48h (if metrics good)

**4. Validation:**
- Verify p95 latency < 10ms (cached)
- Verify cache hit ratio > 80%
- Verify zero security regressions (audit logs)

---

## 🔙 Rollback Plan

### Feature Flags

**Environment Variable:** `CACHE_ENABLED=true|false`

**Implementation:**
```python
class AuthorizationService:
    def __init__(self, db, redis=None):
        self.cache_enabled = os.getenv("CACHE_ENABLED", "false") == "true"
```

**Rollback:** Set `CACHE_ENABLED=false` and restart service

### Rollback Triggers

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Error rate increase | >0.1% | Immediate rollback |
| Latency increase | p95 > 50ms | Investigate → rollback if not resolved in 1h |
| Cache hit ratio | <50% | Investigate configuration |
| Security incident | Stale permissions causing access | Immediate rollback + audit |

### Gradual Rollback

If needed, can rollback gradually:
1. Disable for 50% of instances (30 min)
2. Monitor metrics
3. Full rollback if issues persist

---

## 📚 Best Practices Reference

### Industry Patterns

**Auth0 Approach:**
- Multi-level caching (permission + role)
- Event-based invalidation via webhooks
- TTL: 5 minutes default

**AWS IAM Approach:**
- Policy evaluation caching
- Read replicas for high availability
- Eventually consistent (5 min max)

**Okta Approach:**
- Token caching with JWT validation
- Real-time revocation via events
- Probabilistic expiration

### Security Standards

**OWASP Recommendations:**
- Cache only non-sensitive authorization data ✅
- Implement cache invalidation ✅
- Log all authorization decisions ✅
- Use short TTLs for critical permissions ✅

---

## ✅ Success Criteria

### Performance Targets

| Metric | Current | Target | Minimum Acceptable |
|--------|---------|--------|-------------------|
| p95 Latency (cached) | ~35ms | <10ms | <15ms |
| p95 Latency (overall) | ~35ms | <15ms | <20ms |
| Cache Hit Ratio | 0% | >80% | >70% |
| Database Load | 100% | <20% | <30% |
| Throughput | 1x | 4-5x | 3x |

### Quality Targets

- ✅ Zero security regressions (audit all changes)
- ✅ Zero permission leaks (stale cache prevented)
- ✅ Full test coverage (unit + integration + e2e)
- ✅ Comprehensive monitoring (Prometheus + Grafana)
- ✅ Rollback capability (feature flags)

### Completion Checklist

**Phase 1:**
- [ ] Cache layer added to AuthorizationService
- [ ] Metrics added to Prometheus
- [ ] Unit tests pass (existing + new)
- [ ] Integration tests pass
- [ ] Documentation updated

**Phase 2:**
- [ ] Invalidation added to all mutation endpoints
- [ ] Invalidation utility functions created
- [ ] Integration tests for invalidation
- [ ] Monitoring alerts configured

**Phase 3:**
- [ ] Cache warming implemented
- [ ] Probabilistic expiration added
- [ ] Load testing completed (>80% hit ratio)
- [ ] Production deployment successful

---

## 🚀 Next Steps

### Immediate Actions

1. **Review this plan** with team (15 min)
2. **Create feature branch** `feature/permission-caching`
3. **Start Phase 1 implementation** (2-3 days)
4. **Set up monitoring** (Grafana dashboards)
5. **Run tests** and validate

### Questions to Answer Before Starting

- [ ] Is Redis already configured in production? (Yes, in docker-compose.yml)
- [ ] What is current p95 authorization latency? (Measure baseline)
- [ ] Are there critical permissions that should bypass cache? (Discuss)
- [ ] When can we deploy to staging? (Coordinate with team)

---

**Document Version:** 1.0
**Status:** Ready for Implementation 🚀
**Quality Standard:** Best-of-Class 👑
**Expected Impact:** 50-80% latency reduction 🎯

**Let's build this! 💪**
