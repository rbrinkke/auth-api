-- Migration 004: Add Group-Specific Permission Check
-- Purpose: Ultrathin authorization for microservices (chat-api, etc.)
-- Created: 2025-01-20

-- Function: Check if user has permission in specific group
-- This is the ultrathin version - returns simple boolean for fast microservice checks
CREATE OR REPLACE FUNCTION activity.sp_user_has_permission_in_group(
    p_user_id UUID,
    p_org_id UUID,
    p_group_id UUID,
    p_resource VARCHAR,
    p_action VARCHAR
) RETURNS BOOLEAN AS $$
BEGIN
    -- Check all conditions in single query:
    -- 1. User is member of organization
    -- 2. User is member of specific group
    -- 3. That group has the requested permission
    RETURN EXISTS (
        SELECT 1
        FROM activity.organization_members om
        JOIN activity.user_groups ug ON ug.user_id = om.user_id
        JOIN activity.group_permissions gp ON gp.group_id = ug.group_id
        JOIN activity.permissions perm ON perm.id = gp.permission_id
        WHERE om.user_id = p_user_id
          AND om.organization_id = p_org_id
          AND ug.group_id = p_group_id
          AND perm.resource = p_resource
          AND perm.action = p_action
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- Grant execute permission to application role
GRANT EXECUTE ON FUNCTION activity.sp_user_has_permission_in_group(UUID, UUID, UUID, VARCHAR, VARCHAR) TO postgres;

-- Test the function (should return true for our test user in vrienden group)
DO $$
DECLARE
    v_result BOOLEAN;
BEGIN
    -- Test: user 019a8b88-28cf-71db-a73e-18e49a21fc16 in vrienden group with chat:read
    v_result := activity.sp_user_has_permission_in_group(
        '019a8b88-28cf-71db-a73e-18e49a21fc16'::UUID,
        '99999999-9999-9999-9999-999999999999'::UUID,
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::UUID,
        'chat',
        'read'
    );

    IF v_result THEN
        RAISE NOTICE 'sp_user_has_permission_in_group TEST PASSED: User has chat:read in vrienden group';
    ELSE
        RAISE WARNING 'sp_user_has_permission_in_group TEST FAILED: Expected true, got false';
    END IF;

    -- Negative test: wrong group
    v_result := activity.sp_user_has_permission_in_group(
        '019a8b88-28cf-71db-a73e-18e49a21fc16'::UUID,
        '99999999-9999-9999-9999-999999999999'::UUID,
        'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'::UUID,  -- Non-existent group
        'chat',
        'read'
    );

    IF NOT v_result THEN
        RAISE NOTICE 'sp_user_has_permission_in_group NEGATIVE TEST PASSED: User does not have permission in wrong group';
    ELSE
        RAISE WARNING 'sp_user_has_permission_in_group NEGATIVE TEST FAILED: Expected false, got true';
    END IF;
END $$;
