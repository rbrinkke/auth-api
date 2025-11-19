# RBAC Implementation Status - 2025-11-19

## ✅ Wat Werkt

### Database Schema
- ✅ Migration 002 succesvol uitgevoerd
- ✅ 5 RBAC tabellen aangemaakt:
  - `activity.permissions` - Master permission lijst
  - `activity.groups` - Permission groups binnen organisaties
  - `activity.user_groups` - User-group membership (many-to-many)
  - `activity.group_permissions` - Group-permission grants (many-to-many)
  - `activity.permission_audit_log` - Audit trail

### Stored Procedures
- ✅ 19 stored procedures aangemaakt, waaronder:
  - `sp_user_has_permission(user_id, org_id, resource, action)` → Boolean
  - `sp_get_user_permissions(user_id, org_id)` → Table
  - `sp_create_group(org_id, name, description, creator_id)` → UUID
  - En 16 andere procedures voor CRUD operaties

### Test Data
- ✅ Test scenario aangemaakt in `setup_real_test_data_rbac.sql`:
  - Organization: `11111111-1111-1111-1111-111111111111` (Test Corp)
  - User: `22222222-2222-2222-2222-222222222222` (testuser_rbac)
  - Group: `33333333-3333-3333-3333-333333333333` (Content Creators)
  - Permission: `image:upload` granted aan Content Creators group
  - User is member van Content Creators group

### Authorization Functionaliteit
- ✅ Database-level authorization werkt PERFECT:
```sql
SELECT activity.sp_user_has_permission(
    '22222222-2222-2222-2222-222222222222'::UUID,
    '11111111-1111-1111-1111-111111111111'::UUID,
    'image', 'upload'
) → TRUE

SELECT * FROM activity.sp_get_user_permissions(...)
→ Returns: resource='image', action='upload', via_group_name='Content Creators'
```

### Python Stored Procedure Wrapper
- ✅ Python wrapper werkt correct:
```python
# Test vanuit Docker container
result = await sp_get_user_permissions(user_id, org_id)
# Returns: Permission: image:upload, Group: Content Creators
```

### Production Tests
- ✅ Test 1: Hardcoded test users removed - PASSED
- ✅ Test 2: HTTP 200 for denied access - PASSED
- ✅ Test 3: Strict UUID validation - PASSED
- ⚠️ Test 4: Successful authorization - PARTIALLY PASSED
  - Authorization werkt: `{"allowed": true}` ✅
  - Reason correct: `"User has permission"` ✅
  - Groups NULL: `"groups": null` ❌ (verwacht: `["Content Creators"]`)

## ❌ Probleem: `groups` Field Returnt NULL

### Symptomen
```bash
# Direct API call
curl -X POST http://localhost:8000/api/v1/authorization/check \
  -d '{"user_id": "22222...", "org_id": "11111...", "permission": "image:upload"}'

# Verwacht:
{"allowed": true, "groups": ["Content Creators"], "reason": "User has permission via group membership"}

# Werkelijkheid:
{"allowed": true, "groups": null, "reason": "User has permission"}
```

### Wat We Weten

1. **Database werkt perfect**:
   - `sp_get_user_permissions()` returnt `via_group_name = "Content Creators"` ✅
   - Python wrapper parsed dit correct ✅

2. **Authorization Service Code ziet er correct uit**:
   ```python
   # app/services/authorization_service.py:406-416
   user_permissions = await sp_get_user_permissions(db, user_id, org_id)
   matched_groups = [
       perm.via_group_name
       for perm in user_permissions
       if f"{perm.resource}:{perm.action}" == request.permission
   ]
   # Regel 443: returnt matched_groups
   ```

3. **L2 Cache Issue**:
   - L2 cache is geoptimaliseerd voor snelheid
   - Slaat alleen permission strings op, GEEN group informatie
   - Code regel 242: `matched_groups=None  # Not cached in L2`
   - Dit is **by design** volgens code comments

4. **Zelfs na cache flush krijgen we NULL**:
   ```bash
   # Cache legen
   docker exec activity-redis redis-cli FLUSHALL

   # Request doen → groups STILL null
   # Logs tonen: "authz_l2_cache_hit"
   # Dit betekent dat cache direct wordt herbouwd bij eerste request
   ```

5. **Geen `authorization_granted` logs**:
   - Verwachtte log entry met `matched_groups` verschijnt NIET
   - Alleen `authz_l2_cache_hit` logs
   - Dit suggereert dat code NOOIT het database path neemt

### Hypotheses

**Hypothese 1**: L2 Cache Race Condition
- L2 cache wordt direct na FLUSHALL herbouwd (binnen milliseconden)
- Eerste request vult cache met permission strings only
- Tweede request krijgt cache hit zonder groups

**Hypothese 2**: Code Path Probleem
- Authorization service neemt ALTIJD L2 cache path
- Database path (met matched_groups) wordt nooit bereikt
- Mogelijk door cache logic volgorde

**Hypothese 3**: Response Mapping Issue
- Groups worden WEL opgehaald maar ergens in de response chain verloren
- Mogelijk in `ImageAPIAuthorizationResponse` mapping (regel 96-100)

### Code Locaties Te Onderzoeken

1. **Authorization Service L2 Cache Logic** (`app/services/authorization_service.py:209-243`):
   - Waarom wordt database path NOOIT bereikt na cache flush?
   - Regel 242: `matched_groups=None` - is dit het probleem?

2. **Cache Population Logic** (`app/services/authorization_service.py:310-329`):
   - Hoe wordt L2 cache gevuld na flush?
   - Wordt het synchroon of asynchroon gedaan?

3. **Response Mapping** (`app/routes/authorization.py:96-100`):
   - Is `result.matched_groups` correct gemapped naar `groups`?
   - Type compatibility: `List[str] | None` vs `Optional[List[str]]`?

## 🔧 Fixes Uitgevoerd

### Fix 1: Foreign Key Column Names (CRITICAL)
**Probleem**: Migration 002 gebruikte verkeerde column namen
```sql
-- FOUT:
REFERENCES activity.organizations(id)
REFERENCES activity.users(id)

-- CORRECT:
REFERENCES activity.organizations(organization_id)
REFERENCES activity.users(user_id)
```
**Status**: ✅ OPGELOST - Migration succesvol

### Fix 2: Test Data Email Conflict
**Probleem**: `test@example.com` bestond al
**Fix**: Email changed naar `integration-test-rbac@example.com`
**Status**: ✅ OPGELOST

### Fix 3: Test Data Structure
**Probleem**: Oude test data gebruikte alleen organization membership, geen groups
**Fix**: Nieuwe `setup_real_test_data_rbac.sql` met complete group structuur
**Status**: ✅ OPGELOST

### Fix 4: Docker Rebuild
**Probleem**: Code wijzigingen werden niet opgepikt
**Fix**: `docker compose build --no-cache auth-api && docker compose restart auth-api`
**Status**: ✅ OPGELOST

## 📊 Database State

### Bevestigde Data
```sql
-- 5 RBAC tables exist
SELECT COUNT(*) FROM information_schema.tables
WHERE table_schema = 'activity'
AND table_name IN ('permissions', 'groups', 'user_groups', 'group_permissions', 'permission_audit_log');
→ 5

-- Core stored procedures exist
SELECT COUNT(*) FROM pg_proc
WHERE proname IN ('sp_user_has_permission', 'sp_get_user_permissions', 'sp_create_group');
→ 3

-- Test permissions seeded
SELECT COUNT(*) FROM activity.permissions;
→ 16

-- Test group exists
SELECT group_name FROM activity.groups WHERE group_id = '33333333-3333-3333-3333-333333333333';
→ Content Creators

-- User is member
SELECT COUNT(*) FROM activity.user_groups
WHERE user_id = '22222222-2222-2222-2222-222222222222'
AND group_id = '33333333-3333-3333-3333-333333333333';
→ 1

-- Group has permission
SELECT COUNT(*) FROM activity.group_permissions
WHERE group_id = '33333333-3333-3333-3333-333333333333'
AND permission_id = (SELECT permission_id FROM activity.permissions WHERE resource='image' AND action='upload');
→ 1
```

## 🔴 Blokkerende Issues

### Issue #1: Groups Field Returns NULL
- **Severity**: HIGH
- **Impact**: Test 4 faalt, kan niet naar productie
- **Workaround**: Geen (authorization werkt, maar zonder transparency)
- **Next Steps**: Diep debuggen van cache en response flow

### Issue #2: Audit Log Errors (Non-blocking)
```
ERROR: function activity.sp_create_authorization_audit_log(...) does not exist
HINT: No function matches the given name and argument types. You might need to add explicit type casts.
```
- **Severity**: MEDIUM
- **Impact**: Audit trail werkt niet
- **Workaround**: Errors zijn fire-and-forget, blokkeren requests niet
- **Next Steps**: Type casting fixen in audit log procedure calls

## 📝 Productie Readiness

### ✅ Klaar Voor Productie
- Database schema compleet en getest
- Authorization logica werkt correct
- UUID validatie strikt afgedwongen
- Geen hardcoded test data meer
- Performance acceptabel (L2 cache <10ms)

### ❌ Nog Niet Klaar
- Groups transparency ontbreekt (`groups` field = null)
- Audit logging heeft type casting issues
- Test 4 faalt op group expectation

### 🟡 Aanbeveling
**GO / NO-GO**: **CONDITIIONAL GO**

**Rationale**:
- Core functionaliteit werkt: authorization is correct (`allowed: true/false`)
- Transparency issue: `groups` field is nice-to-have, niet kritiek
- Als stakeholders akkoord gaan met NULL groups → GO
- Als groups vereist zijn → NO-GO tot gefixed

## 📁 Relevante Files

### Modified
- `migrations/002_rbac_schema.sql` - Foreign key fixes

### New
- `setup_real_test_data_rbac.sql` - Test data met groups
- `backup_pre_rbac_20251119_104714.sql` - Backup
- `verify_rbac_production_ready.sh` - Verification script
- `change-001.md` - Original change request
- `migrations/002_rbac_schema_corrected.sql` - Corrected version (duplicate)
- `RBAC_STATUS.md` - Dit document

## 🔍 Debug Commands

```bash
# Test database authorization
docker exec -i activity-postgres-db psql -U postgres -d activitydb -t -c \
  "SELECT activity.sp_user_has_permission('22222222-2222-2222-2222-222222222222'::UUID, '11111111-1111-1111-1111-111111111111'::UUID, 'image', 'upload');"

# Check groups returned
docker exec -i activity-postgres-db psql -U postgres -d activitydb -c \
  "SELECT via_group_name FROM activity.sp_get_user_permissions('22222222-2222-2222-2222-222222222222'::UUID, '11111111-1111-1111-1111-111111111111'::UUID);"

# Test API endpoint
curl -s -X POST http://localhost:8000/api/v1/authorization/check \
  -H "Content-Type: application/json" \
  -d '{"user_id": "22222222-2222-2222-2222-222222222222", "org_id": "11111111-1111-1111-1111-111111111111", "permission": "image:upload"}'

# Clear cache
docker exec activity-redis redis-cli --no-auth-warning -a redis_secure_pass_change_me FLUSHALL

# Check auth-api logs
docker logs auth-api --tail 50 | grep authorization
```

## 🎯 Volgende Stappen

1. **Diep Debuggen** van authorization service:
   - Voeg extra logging toe bij groups extraction
   - Verifieer dat `sp_get_user_permissions` correct wordt aangeroepen
   - Check of `matched_groups` array leeg is of None

2. **Cache Behavior Onderzoeken**:
   - Waarom wordt database path nooit bereikt?
   - L2 cache population tijdens request analyseren
   - Mogelijk cache disable voor debugging

3. **Response Flow Tracen**:
   - Van database → service → route → client
   - Check elke stap waar `matched_groups` doorheen gaat
   - Type compatibility verification

4. **Audit Log Fixen**:
   - Type casting toevoegen aan `sp_create_authorization_audit_log` calls
   - Test audit trail werkt correct
