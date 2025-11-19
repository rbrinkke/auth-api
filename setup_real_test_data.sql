-- ============================================================================
-- Test Data Setup for Authorization Integration Tests
-- ============================================================================
-- Purpose: Create realistic test data for positive authorization tests
-- Author: QA Team / Claude Code
-- Date: 2025-11-19
--
-- Test Scenario:
-- - Organization: "Test Corp" (11111111-1111-1111-1111-111111111111)
-- - User: integration-test@example.com (22222222-2222-2222-2222-222222222222)
-- - User is MEMBER of organization → Should have access
--
-- Expected Result: User can access org resources (allowed: true)
-- ============================================================================

\echo '========================================='
\echo 'Setting up integration test data...'
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
    'test-corp-auth-api-integration',
    'Test organization for auth-api integration testing',
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
    'testuser_integration',
    'integration-test@example.com',
    '$argon2id$v=19$m=65536,t=3,p=4$dGVzdHNhbHR0ZXN0c2FsdHRlc3Q$xYZ123DummyHashForTestingOnly456',
    'Test',
    'User',
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
-- STEP 3: Add User to Organization (This is the KEY for authorization!)
-- ============================================================================
\echo 'Step 3: Adding user to organization as member...'

INSERT INTO activity.organization_members (
    organization_id,
    user_id,
    role,
    joined_at,
    created_at,
    updated_at
)
VALUES (
    '11111111-1111-1111-1111-111111111111'::UUID,
    '22222222-2222-2222-2222-222222222222'::UUID,
    'member',
    NOW(),
    NOW(),
    NOW()
)
ON CONFLICT (organization_id, user_id) DO UPDATE
SET
    role = EXCLUDED.role,
    updated_at = NOW();

\echo '✅ User added to organization'
\echo ''

-- ============================================================================
-- VERIFICATION
-- ============================================================================
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
\echo '3. Verify organization membership (THE KEY TEST!):'
SELECT
    u.username,
    u.email,
    o.name as organization_name,
    om.role,
    om.joined_at
FROM activity.users u
JOIN activity.organization_members om ON u.user_id = om.user_id
JOIN activity.organizations o ON om.organization_id = o.organization_id
WHERE u.user_id = '22222222-2222-2222-2222-222222222222'
  AND o.organization_id = '11111111-1111-1111-1111-111111111111';

\echo ''
\echo '========================================='
\echo '✅ Test data setup complete!'
\echo '========================================='
\echo ''
\echo 'Expected authorization result:'
\echo '  POST /api/v1/authorization/check'
\echo '  {"user_id": "22222222-...", "org_id": "11111111-...", "permission": "any"}'
\echo '  → {"allowed": true, "reason": "User is member of organization"}'
\echo ''
\echo 'Ready to run: ./test_production_auth_endpoint.sh'
\echo ''
