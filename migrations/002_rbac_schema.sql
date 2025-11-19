-- ============================================================================
-- Migration 002: RBAC (Role-Based Access Control) Schema
-- ============================================================================
-- Description: Implements fine-grained permissions system with groups
-- Author: Claude Code
-- Date: 2025-11-12
-- Dependencies: 001_organizations_schema.sql
-- ============================================================================

-- ============================================================================
-- PART 1: CREATE TABLES
-- ============================================================================

-- Table: permissions
-- Stores available permissions in resource:action format (e.g., "activity:create")
-- This is the master list of what actions are possible in the system
CREATE TABLE IF NOT EXISTS activity.permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource VARCHAR(50) NOT NULL CHECK (resource ~ '^[a-z_]+$'),
    action VARCHAR(50) NOT NULL CHECK (action ~ '^[a-z_]+$'),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_permission_resource_action UNIQUE (resource, action)
);

COMMENT ON TABLE activity.permissions IS 'Master list of available permissions (resource:action pairs)';
COMMENT ON COLUMN activity.permissions.resource IS 'Resource type (e.g., activity, user, group)';
COMMENT ON COLUMN activity.permissions.action IS 'Action on resource (e.g., create, read, update, delete)';

-- Table: groups
-- Organizational groups for permission management
-- Groups belong to organizations and contain users
CREATE TABLE IF NOT EXISTS activity.groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES activity.organizations(organization_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_by UUID NOT NULL REFERENCES activity.users(user_id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_group_name_per_org UNIQUE (organization_id, name),
    CONSTRAINT chk_group_name_length CHECK (LENGTH(TRIM(name)) > 0)
);

COMMENT ON TABLE activity.groups IS 'Permission groups within organizations';
COMMENT ON COLUMN activity.groups.organization_id IS 'Organization this group belongs to';
COMMENT ON COLUMN activity.groups.created_by IS 'User who created the group (must be owner/admin)';

-- Table: user_groups (many-to-many)
-- Links users to groups (users inherit permissions from their groups)
CREATE TABLE IF NOT EXISTS activity.user_groups (
    user_id UUID NOT NULL REFERENCES activity.users(user_id) ON DELETE CASCADE,
    group_id UUID NOT NULL REFERENCES activity.groups(id) ON DELETE CASCADE,
    added_by UUID NOT NULL REFERENCES activity.users(user_id) ON DELETE RESTRICT,
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, group_id)
);

COMMENT ON TABLE activity.user_groups IS 'Many-to-many: Users belong to groups';
COMMENT ON COLUMN activity.user_groups.added_by IS 'User who added this member to the group';

-- Table: group_permissions (many-to-many)
-- Links groups to permissions (groups grant permissions to their members)
CREATE TABLE IF NOT EXISTS activity.group_permissions (
    group_id UUID NOT NULL REFERENCES activity.groups(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES activity.permissions(id) ON DELETE CASCADE,
    granted_by UUID NOT NULL REFERENCES activity.users(user_id) ON DELETE RESTRICT,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (group_id, permission_id)
);

COMMENT ON TABLE activity.group_permissions IS 'Many-to-many: Groups have permissions';
COMMENT ON COLUMN activity.group_permissions.granted_by IS 'User who granted this permission (must be owner)';

-- Table: permission_audit_log
-- Audit trail for permission changes (security and compliance)
CREATE TABLE IF NOT EXISTS activity.permission_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_type VARCHAR(20) NOT NULL CHECK (action_type IN ('grant', 'revoke', 'group_created', 'group_deleted', 'member_added', 'member_removed')),
    organization_id UUID NOT NULL REFERENCES activity.organizations(organization_id) ON DELETE CASCADE,
    group_id UUID REFERENCES activity.groups(id) ON DELETE SET NULL,
    permission_id UUID REFERENCES activity.permissions(id) ON DELETE SET NULL,
    user_id UUID REFERENCES activity.users(user_id) ON DELETE SET NULL,
    actor_user_id UUID NOT NULL REFERENCES activity.users(user_id) ON DELETE RESTRICT,
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE activity.permission_audit_log IS 'Audit trail for all permission-related changes';
COMMENT ON COLUMN activity.permission_audit_log.actor_user_id IS 'User who performed the action';
COMMENT ON COLUMN activity.permission_audit_log.details IS 'Additional context (JSON)';

-- ============================================================================
-- PART 2: CREATE INDEXES FOR PERFORMANCE
-- ============================================================================

-- Indexes for groups table
CREATE INDEX IF NOT EXISTS idx_groups_organization_id ON activity.groups(organization_id);
CREATE INDEX IF NOT EXISTS idx_groups_created_by ON activity.groups(created_by);

-- Indexes for user_groups table (critical for permission lookups)
CREATE INDEX IF NOT EXISTS idx_user_groups_user_id ON activity.user_groups(user_id);
CREATE INDEX IF NOT EXISTS idx_user_groups_group_id ON activity.user_groups(group_id);
CREATE INDEX IF NOT EXISTS idx_user_groups_user_group ON activity.user_groups(user_id, group_id);

-- Indexes for group_permissions table (critical for permission lookups)
CREATE INDEX IF NOT EXISTS idx_group_permissions_group_id ON activity.group_permissions(group_id);
CREATE INDEX IF NOT EXISTS idx_group_permissions_permission_id ON activity.group_permissions(permission_id);

-- Indexes for permissions table (critical for permission resolution)
CREATE INDEX IF NOT EXISTS idx_permissions_resource_action ON activity.permissions(resource, action);

-- Indexes for audit log
CREATE INDEX IF NOT EXISTS idx_audit_log_organization_id ON activity.permission_audit_log(organization_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON activity.permission_audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_actor_user_id ON activity.permission_audit_log(actor_user_id);

-- ============================================================================
-- PART 3: STORED PROCEDURES - PERMISSIONS
-- ============================================================================

-- sp_create_permission: Create a new permission
CREATE OR REPLACE FUNCTION activity.sp_create_permission(
    p_resource VARCHAR(50),
    p_action VARCHAR(50),
    p_description TEXT DEFAULT NULL
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    v_permission_id UUID;
BEGIN
    INSERT INTO activity.permissions (resource, action, description)
    VALUES (LOWER(p_resource), LOWER(p_action), p_description)
    RETURNING id INTO v_permission_id;

    RETURN v_permission_id;
END;
$$;

COMMENT ON FUNCTION activity.sp_create_permission IS 'Create a new permission (admin-only operation)';

-- sp_get_permission_by_id: Get permission by ID
CREATE OR REPLACE FUNCTION activity.sp_get_permission_by_id(
    p_permission_id UUID
)
RETURNS TABLE (
    id UUID,
    resource VARCHAR(50),
    action VARCHAR(50),
    description TEXT,
    created_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT p.id, p.resource, p.action, p.description, p.created_at
    FROM activity.permissions p
    WHERE p.id = p_permission_id;
END;
$$;

-- sp_get_permission_by_resource_action: Get permission by resource:action
CREATE OR REPLACE FUNCTION activity.sp_get_permission_by_resource_action(
    p_resource VARCHAR(50),
    p_action VARCHAR(50)
)
RETURNS TABLE (
    id UUID,
    resource VARCHAR(50),
    action VARCHAR(50),
    description TEXT,
    created_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT p.id, p.resource, p.action, p.description, p.created_at
    FROM activity.permissions p
    WHERE p.resource = LOWER(p_resource) AND p.action = LOWER(p_action);
END;
$$;

-- sp_list_permissions: List all available permissions
CREATE OR REPLACE FUNCTION activity.sp_list_permissions()
RETURNS TABLE (
    id UUID,
    resource VARCHAR(50),
    action VARCHAR(50),
    description TEXT,
    created_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT p.id, p.resource, p.action, p.description, p.created_at
    FROM activity.permissions p
    ORDER BY p.resource, p.action;
END;
$$;

-- ============================================================================
-- PART 4: STORED PROCEDURES - GROUPS
-- ============================================================================

-- sp_create_group: Create a new group within an organization
CREATE OR REPLACE FUNCTION activity.sp_create_group(
    p_organization_id UUID,
    p_name VARCHAR(100),
    p_description TEXT,
    p_creator_user_id UUID
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    v_group_id UUID;
BEGIN
    -- Insert group
    INSERT INTO activity.groups (organization_id, name, description, created_by)
    VALUES (p_organization_id, p_name, p_description, p_creator_user_id)
    RETURNING id INTO v_group_id;

    -- Audit log
    INSERT INTO activity.permission_audit_log (
        action_type, organization_id, group_id, actor_user_id, details
    ) VALUES (
        'group_created', p_organization_id, v_group_id, p_creator_user_id,
        jsonb_build_object('group_name', p_name)
    );

    RETURN v_group_id;
END;
$$;

COMMENT ON FUNCTION activity.sp_create_group IS 'Create a new group (owner/admin only)';

-- sp_get_group_by_id: Get group details by ID
CREATE OR REPLACE FUNCTION activity.sp_get_group_by_id(
    p_group_id UUID
)
RETURNS TABLE (
    id UUID,
    organization_id UUID,
    name VARCHAR(100),
    description TEXT,
    created_by UUID,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT g.id, g.organization_id, g.name, g.description, g.created_by, g.created_at, g.updated_at
    FROM activity.groups g
    WHERE g.id = p_group_id;
END;
$$;

-- sp_list_organization_groups: List all groups in an organization
CREATE OR REPLACE FUNCTION activity.sp_list_organization_groups(
    p_organization_id UUID
)
RETURNS TABLE (
    id UUID,
    organization_id UUID,
    name VARCHAR(100),
    description TEXT,
    created_by UUID,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    member_count BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        g.id,
        g.organization_id,
        g.name,
        g.description,
        g.created_by,
        g.created_at,
        g.updated_at,
        COUNT(DISTINCT ug.user_id) AS member_count
    FROM activity.groups g
    LEFT JOIN activity.user_groups ug ON g.id = ug.group_id
    WHERE g.organization_id = p_organization_id
    GROUP BY g.id, g.organization_id, g.name, g.description, g.created_by, g.created_at, g.updated_at
    ORDER BY g.name;
END;
$$;

-- sp_update_group: Update group details
CREATE OR REPLACE FUNCTION activity.sp_update_group(
    p_group_id UUID,
    p_name VARCHAR(100) DEFAULT NULL,
    p_description TEXT DEFAULT NULL
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE activity.groups
    SET
        name = COALESCE(p_name, name),
        description = COALESCE(p_description, description),
        updated_at = NOW()
    WHERE id = p_group_id;

    RETURN FOUND;
END;
$$;

-- sp_delete_group: Delete a group (cascade deletes memberships and permissions)
CREATE OR REPLACE FUNCTION activity.sp_delete_group(
    p_group_id UUID,
    p_deleter_user_id UUID
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_org_id UUID;
    v_group_name VARCHAR(100);
BEGIN
    -- Get group info for audit log
    SELECT organization_id, name INTO v_org_id, v_group_name
    FROM activity.groups
    WHERE id = p_group_id;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    -- Audit log before deletion
    INSERT INTO activity.permission_audit_log (
        action_type, organization_id, group_id, actor_user_id, details
    ) VALUES (
        'group_deleted', v_org_id, p_group_id, p_deleter_user_id,
        jsonb_build_object('group_name', v_group_name)
    );

    -- Delete group (cascades to user_groups and group_permissions)
    DELETE FROM activity.groups WHERE id = p_group_id;

    RETURN TRUE;
END;
$$;

COMMENT ON FUNCTION activity.sp_delete_group IS 'Delete a group and all its memberships/permissions (owner only)';

-- ============================================================================
-- PART 5: STORED PROCEDURES - GROUP MEMBERSHIP
-- ============================================================================

-- sp_add_user_to_group: Add a user to a group
CREATE OR REPLACE FUNCTION activity.sp_add_user_to_group(
    p_user_id UUID,
    p_group_id UUID,
    p_adder_user_id UUID
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_org_id UUID;
BEGIN
    -- Get organization ID
    SELECT organization_id INTO v_org_id
    FROM activity.groups
    WHERE id = p_group_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Group not found';
    END IF;

    -- Insert membership (ON CONFLICT DO NOTHING to handle duplicates gracefully)
    INSERT INTO activity.user_groups (user_id, group_id, added_by)
    VALUES (p_user_id, p_group_id, p_adder_user_id)
    ON CONFLICT (user_id, group_id) DO NOTHING;

    -- Audit log
    INSERT INTO activity.permission_audit_log (
        action_type, organization_id, group_id, user_id, actor_user_id
    ) VALUES (
        'member_added', v_org_id, p_group_id, p_user_id, p_adder_user_id
    );

    RETURN TRUE;
END;
$$;

COMMENT ON FUNCTION activity.sp_add_user_to_group IS 'Add a user to a group (admin/owner only)';

-- sp_remove_user_from_group: Remove a user from a group
CREATE OR REPLACE FUNCTION activity.sp_remove_user_from_group(
    p_user_id UUID,
    p_group_id UUID,
    p_remover_user_id UUID
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_org_id UUID;
BEGIN
    -- Get organization ID
    SELECT organization_id INTO v_org_id
    FROM activity.groups
    WHERE id = p_group_id;

    -- Delete membership
    DELETE FROM activity.user_groups
    WHERE user_id = p_user_id AND group_id = p_group_id;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    -- Audit log
    INSERT INTO activity.permission_audit_log (
        action_type, organization_id, group_id, user_id, actor_user_id
    ) VALUES (
        'member_removed', v_org_id, p_group_id, p_user_id, p_remover_user_id
    );

    RETURN TRUE;
END;
$$;

-- sp_list_group_members: List all members of a group
CREATE OR REPLACE FUNCTION activity.sp_list_group_members(
    p_group_id UUID
)
RETURNS TABLE (
    user_id UUID,
    email VARCHAR(255),
    added_by UUID,
    added_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT ug.user_id, u.email, ug.added_by, ug.added_at
    FROM activity.user_groups ug
    JOIN activity.users u ON ug.user_id = u.user_id
    WHERE ug.group_id = p_group_id
    ORDER BY ug.added_at DESC;
END;
$$;

-- sp_list_user_groups: List all groups a user belongs to in an organization
CREATE OR REPLACE FUNCTION activity.sp_list_user_groups(
    p_user_id UUID,
    p_organization_id UUID
)
RETURNS TABLE (
    group_id UUID,
    group_name VARCHAR(100),
    group_description TEXT,
    added_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT g.id, g.name, g.description, ug.added_at
    FROM activity.user_groups ug
    JOIN activity.groups g ON ug.group_id = g.id
    WHERE ug.user_id = p_user_id AND g.organization_id = p_organization_id
    ORDER BY g.name;
END;
$$;

-- ============================================================================
-- PART 6: STORED PROCEDURES - GROUP PERMISSIONS
-- ============================================================================

-- sp_grant_permission_to_group: Grant a permission to a group
CREATE OR REPLACE FUNCTION activity.sp_grant_permission_to_group(
    p_group_id UUID,
    p_permission_id UUID,
    p_granter_user_id UUID
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_org_id UUID;
BEGIN
    -- Get organization ID
    SELECT organization_id INTO v_org_id
    FROM activity.groups
    WHERE id = p_group_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Group not found';
    END IF;

    -- Insert permission (ON CONFLICT DO NOTHING to handle duplicates)
    INSERT INTO activity.group_permissions (group_id, permission_id, granted_by)
    VALUES (p_group_id, p_permission_id, p_granter_user_id)
    ON CONFLICT (group_id, permission_id) DO NOTHING;

    -- Audit log
    INSERT INTO activity.permission_audit_log (
        action_type, organization_id, group_id, permission_id, actor_user_id
    ) VALUES (
        'grant', v_org_id, p_group_id, p_permission_id, p_granter_user_id
    );

    RETURN TRUE;
END;
$$;

COMMENT ON FUNCTION activity.sp_grant_permission_to_group IS 'Grant a permission to a group (owner only)';

-- sp_revoke_permission_from_group: Revoke a permission from a group
CREATE OR REPLACE FUNCTION activity.sp_revoke_permission_from_group(
    p_group_id UUID,
    p_permission_id UUID,
    p_revoker_user_id UUID
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_org_id UUID;
BEGIN
    -- Get organization ID
    SELECT organization_id INTO v_org_id
    FROM activity.groups
    WHERE id = p_group_id;

    -- Delete permission
    DELETE FROM activity.group_permissions
    WHERE group_id = p_group_id AND permission_id = p_permission_id;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    -- Audit log
    INSERT INTO activity.permission_audit_log (
        action_type, organization_id, group_id, permission_id, actor_user_id
    ) VALUES (
        'revoke', v_org_id, p_group_id, p_permission_id, p_revoker_user_id
    );

    RETURN TRUE;
END;
$$;

-- sp_list_group_permissions: List all permissions granted to a group
CREATE OR REPLACE FUNCTION activity.sp_list_group_permissions(
    p_group_id UUID
)
RETURNS TABLE (
    permission_id UUID,
    resource VARCHAR(50),
    action VARCHAR(50),
    description TEXT,
    granted_by UUID,
    granted_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT p.id, p.resource, p.action, p.description, gp.granted_by, gp.granted_at
    FROM activity.group_permissions gp
    JOIN activity.permissions p ON gp.permission_id = p.id
    WHERE gp.group_id = p_group_id
    ORDER BY p.resource, p.action;
END;
$$;

-- ============================================================================
-- PART 7: STORED PROCEDURES - AUTHORIZATION (THE CORE!)
-- ============================================================================

-- sp_user_has_permission: Check if user has a specific permission in an organization
-- THIS IS THE HEART OF THE RBAC SYSTEM
CREATE OR REPLACE FUNCTION activity.sp_user_has_permission(
    p_user_id UUID,
    p_organization_id UUID,
    p_resource VARCHAR(50),
    p_action VARCHAR(50)
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_is_member BOOLEAN;
    v_has_permission BOOLEAN;
BEGIN
    -- Step 1: Check if user is a member of the organization
    SELECT EXISTS (
        SELECT 1
        FROM activity.organization_members om
        WHERE om.user_id = p_user_id AND om.organization_id = p_organization_id
    ) INTO v_is_member;

    IF NOT v_is_member THEN
        RETURN FALSE;
    END IF;

    -- Step 2: Check if user has the permission via any group
    SELECT EXISTS (
        SELECT 1
        FROM activity.user_groups ug
        JOIN activity.groups g ON ug.group_id = g.id
        JOIN activity.group_permissions gp ON g.id = gp.group_id
        JOIN activity.permissions p ON gp.permission_id = p.id
        WHERE ug.user_id = p_user_id
          AND g.organization_id = p_organization_id
          AND p.resource = LOWER(p_resource)
          AND p.action = LOWER(p_action)
    ) INTO v_has_permission;

    RETURN v_has_permission;
END;
$$;

COMMENT ON FUNCTION activity.sp_user_has_permission IS 'Check if user has permission (THE CORE authorization function)';

-- sp_get_user_permissions: Get all permissions a user has in an organization
CREATE OR REPLACE FUNCTION activity.sp_get_user_permissions(
    p_user_id UUID,
    p_organization_id UUID
)
RETURNS TABLE (
    permission_id UUID,
    resource VARCHAR(50),
    action VARCHAR(50),
    description TEXT,
    via_group_id UUID,
    via_group_name VARCHAR(100),
    granted_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id AS permission_id,
        p.resource,
        p.action,
        p.description,
        g.id AS via_group_id,
        g.name AS via_group_name,
        gp.granted_at
    FROM activity.user_groups ug
    JOIN activity.groups g ON ug.group_id = g.id
    JOIN activity.group_permissions gp ON g.id = gp.group_id
    JOIN activity.permissions p ON gp.permission_id = p.id
    WHERE ug.user_id = p_user_id
      AND g.organization_id = p_organization_id
    ORDER BY p.resource, p.action, g.name;
END;
$$;

COMMENT ON FUNCTION activity.sp_get_user_permissions IS 'Get all permissions user has via groups (for UI display)';

-- ============================================================================
-- PART 8: SEED DEFAULT PERMISSIONS
-- ============================================================================

-- Insert default permissions for the Activity App
-- These are the baseline permissions that all organizations can use
INSERT INTO activity.permissions (resource, action, description) VALUES
    -- Activity permissions
    ('activity', 'create', 'Create new activities'),
    ('activity', 'read', 'View activities'),
    ('activity', 'update', 'Modify existing activities'),
    ('activity', 'delete', 'Delete activities'),

    -- User permissions
    ('user', 'read', 'View user profiles'),
    ('user', 'update', 'Modify user profiles'),

    -- Group management permissions
    ('group', 'create', 'Create new groups'),
    ('group', 'read', 'View groups'),
    ('group', 'update', 'Modify groups'),
    ('group', 'delete', 'Delete groups'),
    ('group', 'manage_members', 'Add/remove group members'),
    ('group', 'manage_permissions', 'Grant/revoke group permissions'),

    -- Organization permissions
    ('organization', 'read', 'View organization details'),
    ('organization', 'update', 'Modify organization settings'),
    ('organization', 'manage_members', 'Add/remove organization members')
ON CONFLICT (resource, action) DO NOTHING;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify tables were created
DO $$
DECLARE
    v_table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_table_count
    FROM information_schema.tables
    WHERE table_schema = 'activity'
      AND table_name IN ('permissions', 'groups', 'user_groups', 'group_permissions', 'permission_audit_log');

    IF v_table_count = 5 THEN
        RAISE NOTICE 'Migration 002: Successfully created 5 RBAC tables';
    ELSE
        RAISE WARNING 'Migration 002: Expected 5 tables, found %', v_table_count;
    END IF;
END $$;

-- Verify stored procedures were created
DO $$
DECLARE
    v_proc_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_proc_count
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'activity'
      AND p.proname LIKE 'sp_%permission%' OR p.proname LIKE 'sp_%group%';

    RAISE NOTICE 'Migration 002: Created % RBAC stored procedures', v_proc_count;
    RAISE NOTICE 'Migration 002: RBAC schema migration completed successfully! 🚀';
END $$;
