-- ============================================================================
-- RBAC Core Functionality Test
-- ============================================================================
-- This script tests the core authorization function sp_user_has_permission
-- ============================================================================

\echo '===================================================================='
\echo 'RBAC CORE TEST: Testing sp_user_has_permission function'
\echo '===================================================================='

DO $$
DECLARE
    v_user_id UUID;
    v_org_id UUID;
    v_group_id UUID;
    v_permission_id UUID;
    v_has_permission BOOLEAN;
    v_test_passed INTEGER := 0;
    v_test_failed INTEGER := 0;
BEGIN
    \echo '--- Step 1: Creating test user ---'
    INSERT INTO activity.users (email, hashed_password, is_verified)
    VALUES ('rbac_test_user@test.com', '$argon2id$v=19$m=65536,t=3,p=4$test', TRUE)
    RETURNING id INTO v_user_id;
    RAISE NOTICE '✅ Created test user: %', v_user_id;

    \echo '--- Step 2: Creating test organization ---'
    INSERT INTO activity.organizations (name, slug, owner_user_id)
    VALUES ('RBAC Test Org', 'rbac-test-org', v_user_id)
    RETURNING id INTO v_org_id;
    RAISE NOTICE '✅ Created test organization: %', v_org_id;

    \echo '--- Step 3: Adding user to organization ---'
    INSERT INTO activity.organization_members (user_id, organization_id, role)
    VALUES (v_user_id, v_org_id, 'member');
    RAISE NOTICE '✅ User added to organization as member';

    \echo '--- Step 4: Creating test group ---'
    v_group_id := activity.sp_create_group(
        v_org_id,
        'Test Activity Managers',
        'Can manage activities',
        v_user_id
    );
    RAISE NOTICE '✅ Created group: %', v_group_id;

    \echo '--- Step 5: Getting activity:create permission ---'
    SELECT id INTO v_permission_id
    FROM activity.permissions
    WHERE resource = 'activity' AND action = 'create';
    RAISE NOTICE '✅ Found permission ID: %', v_permission_id;

    \echo '--- Step 6: Granting permission to group ---'
    PERFORM activity.sp_grant_permission_to_group(
        v_group_id,
        v_permission_id,
        v_user_id
    );
    RAISE NOTICE '✅ Permission granted to group';

    \echo '--- Step 7: Adding user to group ---'
    PERFORM activity.sp_add_user_to_group(v_user_id, v_group_id, v_user_id);
    RAISE NOTICE '✅ User added to group';

    \echo ''
    \echo '===================================================================='
    \echo 'RUNNING TESTS'
    \echo '===================================================================='

    -- TEST 1: User should have activity:create permission
    \echo '--- Test 1: Check activity:create permission (should be TRUE) ---'
    v_has_permission := activity.sp_user_has_permission(
        v_user_id,
        v_org_id,
        'activity',
        'create'
    );

    IF v_has_permission THEN
        RAISE NOTICE '✅ TEST 1 PASSED: User has activity:create permission';
        v_test_passed := v_test_passed + 1;
    ELSE
        RAISE WARNING '❌ TEST 1 FAILED: Expected TRUE, got FALSE';
        v_test_failed := v_test_failed + 1;
    END IF;

    -- TEST 2: User should NOT have activity:delete permission
    \echo '--- Test 2: Check activity:delete permission (should be FALSE) ---'
    v_has_permission := activity.sp_user_has_permission(
        v_user_id,
        v_org_id,
        'activity',
        'delete'
    );

    IF NOT v_has_permission THEN
        RAISE NOTICE '✅ TEST 2 PASSED: User does not have activity:delete permission';
        v_test_passed := v_test_passed + 1;
    ELSE
        RAISE WARNING '❌ TEST 2 FAILED: Expected FALSE, got TRUE';
        v_test_failed := v_test_failed + 1;
    END IF;

    -- TEST 3: Non-member should not have any permissions
    \echo '--- Test 3: Check permission for non-member (should be FALSE) ---'
    DECLARE
        v_non_member_id UUID;
    BEGIN
        INSERT INTO activity.users (email, hashed_password, is_verified)
        VALUES ('non_member@test.com', '$argon2id$v=19$m=65536,t=3,p=4$test', TRUE)
        RETURNING id INTO v_non_member_id;

        v_has_permission := activity.sp_user_has_permission(
            v_non_member_id,
            v_org_id,
            'activity',
            'create'
        );

        IF NOT v_has_permission THEN
            RAISE NOTICE '✅ TEST 3 PASSED: Non-member correctly denied';
            v_test_passed := v_test_passed + 1;
        ELSE
            RAISE WARNING '❌ TEST 3 FAILED: Non-member should not have permission';
            v_test_failed := v_test_failed + 1;
        END IF;

        DELETE FROM activity.users WHERE id = v_non_member_id;
    END;

    -- TEST 4: Get all user permissions
    \echo '--- Test 4: Get all user permissions ---'
    DECLARE
        v_perm_count INTEGER;
    BEGIN
        SELECT COUNT(*) INTO v_perm_count
        FROM activity.sp_get_user_permissions(v_user_id, v_org_id);

        IF v_perm_count > 0 THEN
            RAISE NOTICE '✅ TEST 4 PASSED: Found % permission(s)', v_perm_count;
            v_test_passed := v_test_passed + 1;
        ELSE
            RAISE WARNING '❌ TEST 4 FAILED: Expected permissions, found none';
            v_test_failed := v_test_failed + 1;
        END IF;
    END;

    -- TEST 5: Test audit logging
    \echo '--- Test 5: Verify audit logging ---'
    DECLARE
        v_audit_count INTEGER;
    BEGIN
        SELECT COUNT(*) INTO v_audit_count
        FROM activity.permission_audit_log
        WHERE organization_id = v_org_id;

        IF v_audit_count >= 3 THEN
            RAISE NOTICE '✅ TEST 5 PASSED: Audit log has % entries', v_audit_count;
            v_test_passed := v_test_passed + 1;
        ELSE
            RAISE WARNING '❌ TEST 5 FAILED: Expected audit entries, found %', v_audit_count;
            v_test_failed := v_test_failed + 1;
        END IF;
    END;

    \echo ''
    \echo '===================================================================='
    \echo 'TEST RESULTS'
    \echo '===================================================================='
    RAISE NOTICE 'Tests Passed: %', v_test_passed;
    RAISE NOTICE 'Tests Failed: %', v_test_failed;

    IF v_test_failed = 0 THEN
        RAISE NOTICE '🎉 ALL TESTS PASSED! RBAC system is working correctly!';
    ELSE
        RAISE WARNING '⚠️  Some tests failed. Please review the output above.';
    END IF;

    \echo ''
    \echo '--- Cleanup: Removing test data ---'
    DELETE FROM activity.organizations WHERE id = v_org_id;
    DELETE FROM activity.users WHERE id = v_user_id;
    RAISE NOTICE '🧹 Test data cleaned up successfully';

END $$;

\echo ''
\echo '===================================================================='
\echo 'DATABASE STATE SUMMARY'
\echo '===================================================================='

SELECT
    'Total Permissions' as metric,
    COUNT(*)::text as value
FROM activity.permissions
UNION ALL
SELECT
    'Total Groups',
    COUNT(*)::text
FROM activity.groups
UNION ALL
SELECT
    'Total Audit Entries',
    COUNT(*)::text
FROM activity.permission_audit_log;

\echo '===================================================================='
\echo 'RBAC Core Test Complete! 🚀'
\echo '===================================================================='
