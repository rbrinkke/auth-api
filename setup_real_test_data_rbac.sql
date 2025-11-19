-- ============================================================================
-- Test Data Setup for RBAC Authorization Testing
-- ============================================================================
-- Purpose: Create realistic test data for positive authorization tests (Test 4)
-- Author: QA Team / Claude Code
-- Date: 2025-11-19
--
-- Test Scenario (GROUP-BASED RBAC):
-- - Organization: "Test Corp" (11111111-1111-1111-1111-111111111111)
-- - User: integration-test@example.com (22222222-2222-2222-2222-222222222222)
-- - Group: "Content Creators" with image:upload permission
-- - User is MEMBER of group → Should have access via group permission
--
-- Expected Result: User can upload images (allowed: true, groups: ["Content Creators"])
-- ============================================================================

\echo '========================================='
\echo 'Setting up RBAC integration test data...'
\echo '========================================='
\echo ''

-- ============================================================================
-- STEP 1: Create Test Organization
-- ============================================================================
\echo 'Step 1: Creating test organization (Test Corp)...'

INSERT INTO activity.organizations (
    organization_id,
    name,
    slug,
    description,
    is_verified,
    status,
    created_at,
    updated_at
)
VALUES (
    '11111111-1111-1111-1111-111111111111'::UUID,
    'Test Corp',
    'test-corp-auth-api-rbac-integration',
    'Test organization for auth-api RBAC integration testing',
    TRUE,
    'active',
    NOW(),
    NOW()
)
ON CONFLICT (organization_id) DO UPDATE
SET
    name = EXCLUDED.name,
    slug = EXCLUDED.slug,
    description = EXCLUDED.description,
    is_verified = TRUE,
    status = 'active',
    updated_at = NOW();

\echo '✅ Test organization created/updated'
\echo ''

-- ============================================================================
-- STEP 2: Create Test User
-- ============================================================================
\echo 'Step 2: Creating test user (integration-test@example.com)...'

INSERT INTO activity.users (
    user_id,
    username,
    email,
    password_hash,
    first_name,
    last_name,
    is_active,
    is_verified,
    status,
    created_at,
    updated_at
)
VALUES (
    '22222222-2222-2222-2222-222222222222'::UUID,
    'testuser_rbac',
    'integration-test-rbac@example.com',
    '$argon2id$v=19$m=65536,t=3,p=4$dGVzdHNhbHR0ZXN0c2FsdHRlc3Q$xYZ123DummyHashForTestingOnly456',
    'RBAC',
    'Tester',
    TRUE,
    TRUE,
    'active',
    NOW(),
    NOW()
)
ON CONFLICT (user_id) DO UPDATE
SET
    username = EXCLUDED.username,
    email = EXCLUDED.email,
    is_active = TRUE,
    is_verified = TRUE,
    status = 'active',
    updated_at = NOW();

\echo '✅ Test user created/updated'
\echo ''

-- ============================================================================
-- STEP 3: Add User to Organization (Required for RBAC checks)
-- ============================================================================
\echo 'Step 3: Adding user to organization as member...'

INSERT INTO activity.organization_members (
    organization_id,
    user_id,
    role
)
VALUES (
    '11111111-1111-1111-1111-111111111111'::UUID,
    '22222222-2222-2222-2222-222222222222'::UUID,
    'member'
)
ON CONFLICT (organization_id, user_id) DO UPDATE
SET
    role = 'member',
    joined_at = NOW();

\echo '✅ User added to organization'
\echo ''

-- ============================================================================
-- STEP 4: Create "image:upload" Permission (if not exists)
-- ============================================================================
\echo 'Step 4: Ensuring image:upload permission exists...'

INSERT INTO activity.permissions (resource, action, description)
VALUES ('image', 'upload', 'Upload images to the system')
ON CONFLICT (resource, action) DO NOTHING;

\echo '✅ image:upload permission ensured'
\echo ''

-- ============================================================================
-- STEP 5: Create "Content Creators" Group
-- ============================================================================
\echo 'Step 5: Creating "Content Creators" group...'

INSERT INTO activity.groups (
    id,
    organization_id,
    name,
    description,
    created_by,
    created_at,
    updated_at
)
VALUES (
    '33333333-3333-3333-3333-333333333333'::UUID,
    '11111111-1111-1111-1111-111111111111'::UUID,
    'Content Creators',
    'Users who can upload and manage content',
    '22222222-2222-2222-2222-222222222222'::UUID,  -- Created by test user
    NOW(),
    NOW()
)
ON CONFLICT (organization_id, name) DO UPDATE
SET
    description = EXCLUDED.description,
    updated_at = NOW();

\echo '✅ "Content Creators" group created/updated'
\echo ''

-- ============================================================================
-- STEP 6: Grant "image:upload" Permission to Group
-- ============================================================================
\echo 'Step 6: Granting image:upload permission to Content Creators group...'

INSERT INTO activity.group_permissions (
    group_id,
    permission_id,
    granted_by,
    granted_at
)
SELECT
    '33333333-3333-3333-3333-333333333333'::UUID,
    p.id,
    '22222222-2222-2222-2222-222222222222'::UUID,  -- Granted by test user
    NOW()
FROM activity.permissions p
WHERE p.resource = 'image' AND p.action = 'upload'
ON CONFLICT (group_id, permission_id) DO NOTHING;

\echo '✅ image:upload permission granted to group'
\echo ''

-- ============================================================================
-- STEP 7: Add User to "Content Creators" Group
-- ============================================================================
\echo 'Step 7: Adding user to Content Creators group...'

INSERT INTO activity.user_groups (
    user_id,
    group_id,
    added_by,
    added_at
)
VALUES (
    '22222222-2222-2222-2222-222222222222'::UUID,
    '33333333-3333-3333-3333-333333333333'::UUID,
    '22222222-2222-2222-2222-222222222222'::UUID,  -- Self-added (for testing)
    NOW()
)
ON CONFLICT (user_id, group_id) DO NOTHING;

\echo '✅ User added to Content Creators group'
\echo ''

-- ============================================================================
-- VERIFICATION CHECKS
-- ============================================================================
\echo ''
\echo '========================================='
\echo 'VERIFICATION CHECKS'
\echo '========================================='

\echo ''
\echo '1. Verify organization exists:'
SELECT
    organization_id,
    name,
    slug,
    is_verified,
    status
FROM activity.organizations
WHERE organization_id = '11111111-1111-1111-1111-111111111111';

\echo ''
\echo '2. Verify user exists:'
SELECT
    user_id,
    username,
    email,
    is_active,
    is_verified,
    status
FROM activity.users
WHERE user_id = '22222222-2222-2222-2222-222222222222';

\echo ''
\echo '3. Verify organization membership:'
SELECT
    om.user_id,
    u.username,
    u.email,
    om.organization_id,
    om.role,
    om.joined_at
FROM activity.organization_members om
JOIN activity.users u ON om.user_id = u.user_id
WHERE om.organization_id = '11111111-1111-1111-1111-111111111111'
  AND om.user_id = '22222222-2222-2222-2222-222222222222';

\echo ''
\echo '4. Verify group exists:'
SELECT
    id AS group_id,
    name,
    description,
    organization_id
FROM activity.groups
WHERE id = '33333333-3333-3333-3333-333333333333';

\echo ''
\echo '5. Verify group has image:upload permission:'
SELECT
    gp.group_id,
    g.name AS group_name,
    p.resource || ':' || p.action AS permission,
    p.description
FROM activity.group_permissions gp
JOIN activity.groups g ON gp.group_id = g.id
JOIN activity.permissions p ON gp.permission_id = p.id
WHERE gp.group_id = '33333333-3333-3333-3333-333333333333';

\echo ''
\echo '6. Verify user is member of group:'
SELECT
    ug.user_id,
    u.username,
    g.name AS group_name,
    ug.added_at
FROM activity.user_groups ug
JOIN activity.users u ON ug.user_id = u.user_id
JOIN activity.groups g ON ug.group_id = g.id
WHERE ug.user_id = '22222222-2222-2222-2222-222222222222'
  AND ug.group_id = '33333333-3333-3333-3333-333333333333';

\echo ''
\echo '7. TEST AUTHORIZATION (THE CRITICAL TEST!):'
\echo 'Calling sp_user_has_permission...'
SELECT activity.sp_user_has_permission(
    '22222222-2222-2222-2222-222222222222'::UUID,  -- user_id
    '11111111-1111-1111-1111-111111111111'::UUID,  -- org_id
    'image',                                        -- resource
    'upload'                                        -- action
) AS has_permission;
\echo 'Expected: true (user → group → permission)'

\echo ''
\echo '8. GET ALL USER PERMISSIONS:'
SELECT
    resource || ':' || action AS permission,
    via_group_name,
    description
FROM activity.sp_get_user_permissions(
    '22222222-2222-2222-2222-222222222222'::UUID,  -- user_id
    '11111111-1111-1111-1111-111111111111'::UUID   -- org_id
)
ORDER BY resource, action;

\echo ''
\echo '========================================='
\echo '✅ Test data setup complete!'
\echo '========================================='
\echo ''
\echo 'Expected authorization result:'
\echo '  POST /api/v1/authorization/check'
\echo '  {"user_id": "22222222-...", "org_id": "11111111-...", "permission": "image:upload"}'
\echo '  → {"allowed": true, "reason": "User has permission via group membership", "groups": ["Content Creators"]}'
\echo ''
\echo 'Ready to run: ./test_production_auth_endpoint.sh'
\echo ''
