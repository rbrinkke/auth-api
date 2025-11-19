-- ============================================================================
-- Cleanup Test Data for Authorization Integration Tests
-- ============================================================================
-- Purpose: Remove test data created by setup_real_test_data.sql
-- Author: QA Team / Claude Code
-- Date: 2025-11-19
--
-- IMPORTANT: Delete in REVERSE order of foreign key dependencies
-- ============================================================================

\echo '========================================='
\echo 'Cleaning up integration test data...'
\echo '========================================='
\echo ''

-- ============================================================================
-- STEP 1: Remove User from Group
-- ============================================================================
\echo 'Step 1: Removing user from group...'

DELETE FROM activity.user_groups
WHERE user_id = '22222222-2222-2222-2222-222222222222'::UUID
  AND group_id = '33333333-3333-3333-3333-333333333333'::UUID;

\echo '✅ User removed from group'
\echo ''

-- ============================================================================
-- STEP 2: Remove Permission from Group
-- ============================================================================
\echo 'Step 2: Removing permission from group...'

DELETE FROM activity.group_permissions
WHERE group_id = '33333333-3333-3333-3333-333333333333'::UUID
  AND permission_id = '44444444-4444-4444-4444-444444444444'::UUID;

\echo '✅ Permission removed from group'
\echo ''

-- ============================================================================
-- STEP 3: Delete Group
-- ============================================================================
\echo 'Step 3: Deleting group...'

DELETE FROM activity.groups
WHERE id = '33333333-3333-3333-3333-333333333333'::UUID;

\echo '✅ Group deleted'
\echo ''

-- ============================================================================
-- STEP 4: Delete Permission
-- ============================================================================
\echo 'Step 4: Deleting permission...'

DELETE FROM activity.permissions
WHERE id = '44444444-4444-4444-4444-444444444444'::UUID;

\echo '✅ Permission deleted'
\echo ''

-- ============================================================================
-- STEP 5: Remove User from Organization
-- ============================================================================
\echo 'Step 5: Removing user from organization...'

DELETE FROM activity.organization_members
WHERE organization_id = '11111111-1111-1111-1111-111111111111'::UUID
  AND user_id = '22222222-2222-2222-2222-222222222222'::UUID;

\echo '✅ User removed from organization'
\echo ''

-- ============================================================================
-- STEP 6: Delete Organization
-- ============================================================================
\echo 'Step 6: Deleting organization...'

DELETE FROM activity.organizations
WHERE id = '11111111-1111-1111-1111-111111111111'::UUID;

\echo '✅ Organization deleted'
\echo ''

-- ============================================================================
-- STEP 7: Delete User
-- ============================================================================
\echo 'Step 7: Deleting user...'

DELETE FROM activity.users
WHERE id = '22222222-2222-2222-2222-222222222222'::UUID;

\echo '✅ User deleted'
\echo ''

-- ============================================================================
-- VERIFICATION
-- ============================================================================
\echo '========================================='
\echo 'VERIFICATION CHECKS'
\echo '========================================='
\echo ''

\echo '1. Verify user deleted:'
SELECT COUNT(*) as user_count
FROM activity.users
WHERE id = '22222222-2222-2222-2222-222222222222'::UUID;

\echo ''
\echo '2. Verify organization deleted:'
SELECT COUNT(*) as org_count
FROM activity.organizations
WHERE id = '11111111-1111-1111-1111-111111111111'::UUID;

\echo ''
\echo '3. Verify group deleted:'
SELECT COUNT(*) as group_count
FROM activity.groups
WHERE id = '33333333-3333-3333-3333-333333333333'::UUID;

\echo ''
\echo '4. Verify permission deleted:'
SELECT COUNT(*) as permission_count
FROM activity.permissions
WHERE id = '44444444-4444-4444-4444-444444444444'::UUID;

\echo ''
\echo '========================================='
\echo '✅ Test data cleanup complete!'
\echo '========================================='
\echo ''
\echo 'All counts should be 0 (zero)'
\echo ''
