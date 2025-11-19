# Image Permissions Model

## Overzicht

Het image permissions model volgt een **capabilities-based RBAC** aanpak met **ownership checks in de image-api**. Dit scheidt autorisatie (RBAC) van eigenaarschap (domein logica).

## Permission Structuur

| Permission | Capability | Beschrijving | Ownership Check |
|------------|-----------|--------------|-----------------|
| `image:read` | **r** (read) | View en download images | Geen (org-wide read) |
| `image:write` | **rw** (read-write) | Upload, update, delete images | **JA** - alleen eigen images |
| `image:admin` | **x** (execute/admin) | Volledige rechten op alle images | **NEE** - bypass ownership |

## Hoe Het Werkt

### Scenario 1: Normal User met `image:write`

```
Request: DELETE /images/abc-123

1. Auth-API RBAC Check:
   ✅ User heeft `image:write` permission via group
   → Authorization response: {"allowed": true, "groups": ["Content Creators"]}

2. Image-API Ownership Check:
   ? Is user owner van image abc-123?
   → Query: SELECT user_id FROM images WHERE id = 'abc-123'

   IF owner matches user:
      ✅ DELETE allowed
   ELSE:
      ❌ 403 Forbidden: "Cannot delete images you don't own"
```

### Scenario 2: Admin met `image:admin`

```
Request: DELETE /images/xyz-789 (van andere user!)

1. Auth-API RBAC Check:
   ✅ User heeft `image:admin` permission
   → Authorization response: {"allowed": true, "groups": ["Administrators"]}

2. Image-API Ownership Check:
   ⏭️  SKIP ownership check (admin bypass)
   ✅ DELETE allowed (regardless of owner)
```

### Scenario 3: Viewer met `image:read`

```
Request: GET /images/abc-123

1. Auth-API RBAC Check:
   ✅ User heeft `image:read` permission
   → Authorization response: {"allowed": true}

2. Image-API:
   ✅ Return image data (no ownership check for read)
```

## Separation of Concerns

### Auth-API Verantwoordelijk Voor:
- ✅ **Capabilities**: Wat mag een user in principe doen?
- ✅ **Group Membership**: Via welke groups heeft user rechten?
- ✅ **Organization Scope**: User is member van org?

### Image-API Verantwoordelijk Voor:
- ✅ **Ownership**: Is user de eigenaar van dit specifieke resource?
- ✅ **Business Rules**: Quota, file types, size limits
- ✅ **Domain Logic**: Image processing, storage, metadata

## Permission Assignment Voorbeelden

### Content Creators (normale gebruikers)
```sql
-- Group: Content Creators
-- Permissions:
- image:write  → Upload, edit, delete OWN images
- image:read   → View all images in org
```

**Gedrag:**
- ✅ Upload nieuwe images
- ✅ Delete eigen images
- ❌ Delete images van anderen
- ✅ View alle images in org

### Image Moderators (moderators)
```sql
-- Group: Moderators
-- Permissions:
- image:admin  → Full rights on ALL images
- image:write  → (implied by admin)
- image:read   → (implied by admin)
```

**Gedrag:**
- ✅ Delete ANY image (moderatie)
- ✅ Update ANY image metadata
- ✅ Bypass alle ownership checks

### Viewers (read-only)
```sql
-- Group: Viewers
-- Permissions:
- image:read   → View only
```

**Gedrag:**
- ✅ View/download images
- ❌ Upload images
- ❌ Delete images
- ❌ Update images

## Implementation in Image-API

### Authorization Middleware

```python
async def check_image_permission(
    user_id: UUID,
    org_id: UUID,
    permission: str,  # "image:read" | "image:write" | "image:admin"
    image_id: Optional[UUID] = None
) -> bool:
    # 1. RBAC Check (Auth-API)
    authz_response = await auth_api.check_authorization(
        user_id=user_id,
        org_id=org_id,
        permission=permission
    )

    if not authz_response.allowed:
        raise HTTPException(403, "Insufficient permissions")

    # 2. Ownership Check (Image-API domain logic)
    if permission == "image:admin":
        # Admin bypass ownership
        return True

    if permission == "image:write" and image_id:
        # Check ownership for write operations
        image = await db.get_image(image_id)
        if image.user_id != user_id:
            raise HTTPException(403, "Cannot modify images you don't own")

    # image:read heeft geen ownership check
    return True
```

### Route Examples

```python
@router.delete("/images/{image_id}")
async def delete_image(
    image_id: UUID,
    user: User = Depends(get_current_user)
):
    # Check permission with ownership
    await check_image_permission(
        user_id=user.id,
        org_id=user.current_org_id,
        permission="image:write",
        image_id=image_id  # Triggers ownership check
    )

    await image_service.delete(image_id)
    return {"status": "deleted"}

@router.get("/images")
async def list_images(
    user: User = Depends(get_current_user)
):
    # No ownership check for read
    await check_image_permission(
        user_id=user.id,
        org_id=user.current_org_id,
        permission="image:read"
    )

    images = await image_service.list_for_org(user.current_org_id)
    return {"images": images}
```

## Voordelen van Dit Model

### 1. Clean Separation
- RBAC systeem hoeft niets van ownership te weten
- Image-API hoeft geen groepen/permissions te managen
- Elk systeem doet waar het goed in is

### 2. Flexibiliteit
- Admin kan altijd alle images managen (moderatie)
- Users kunnen alleen eigen images wijzigen (privacy)
- Read access kan org-wide zijn (delen binnen team)

### 3. Schaalbaarheid
- RBAC permissions blijven simpel (3 in plaats van 6+)
- Ownership checks zijn snel (indexed op user_id)
- Cache-friendly (permissions raken minder vaak stale)

### 4. Security
- Geen privilege escalation via group membership
- Defense in depth: RBAC + ownership check
- Clear audit trail (beide lagen loggen)

## Database Schema

```sql
-- Auth-API: activity.permissions
SELECT * FROM activity.permissions WHERE resource = 'image';

 resource | action |                   description
----------+--------+-------------------------------------------------
 image    | read   | View and download images
 image    | write  | Upload, update, and delete own images
 image    | admin  | Full admin rights on all images in organization

-- Image-API: images table
CREATE TABLE images (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,           -- Owner (for ownership check)
    organization_id UUID NOT NULL,   -- Org scope
    filename VARCHAR(255),
    created_at TIMESTAMP,
    ...
);

CREATE INDEX idx_images_user_id ON images(user_id);  -- Fast ownership lookup
```

## Testing

### Test Coverage

```bash
# Test 1: Normal user can delete own image
✅ User met image:write + owner → DELETE allowed

# Test 2: Normal user CANNOT delete other's image
❌ User met image:write + NOT owner → 403 Forbidden

# Test 3: Admin can delete any image
✅ User met image:admin + NOT owner → DELETE allowed

# Test 4: Viewer cannot delete
❌ User met image:read → 403 Forbidden (geen write permission)

# Test 5: Read access is org-wide
✅ User met image:read → GET all org images allowed
```

## Migration Notes

### Bestaande Data

De oude `image:upload` permission is automatisch gemigreerd naar `image:write`:

```sql
UPDATE activity.permissions
SET
    action = 'write',
    description = 'Upload, update, and delete own images'
WHERE resource = 'image' AND action = 'upload';
```

**Impact:**
- ✅ Bestaande group permissions blijven werken
- ✅ Users met `image:upload` hebben nu `image:write`
- ✅ Functioneel equivalent (ownership checks waren er al)

### Test Data Update

```sql
-- Content Creators group heeft nu image:write
SELECT
    g.name,
    p.resource,
    p.action
FROM activity.groups g
JOIN activity.group_permissions gp ON g.id = gp.group_id
JOIN activity.permissions p ON gp.permission_id = p.id
WHERE g.name = 'Content Creators';

    name         | resource | action
-----------------+----------+--------
Content Creators | image    | write
```

## Next Steps

1. **Image-API Implementation**
   - Implement ownership checks in middleware
   - Add admin bypass logic
   - Update existing routes

2. **Group Setup**
   - Create "Image Moderators" group met `image:admin`
   - Add `image:read` to appropriate groups
   - Document group assignment policy

3. **Testing**
   - Integration tests voor ownership scenarios
   - E2E tests voor admin bypass
   - Performance tests voor ownership queries

4. **Documentation**
   - API docs met permission requirements per endpoint
   - Admin guide voor group management
   - User guide voor permission meanings
