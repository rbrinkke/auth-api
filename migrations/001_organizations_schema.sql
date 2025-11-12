-- ============================================================================
-- MIGRATION 001: Organizations Foundation
-- ============================================================================
-- Purpose: Add multi-tenancy support with organizations
-- Author: Claude Code Agent
-- Date: 2025-01-12
-- Dependencies: Existing activity.users table
-- ============================================================================

-- ORGANIZATIONS TABLE
-- Each organization is a separate tenant with isolated data
CREATE TABLE IF NOT EXISTS activity.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,  -- URL-friendly identifier (lowercase, hyphens only)
    description TEXT,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Soft delete support
    deleted_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT organizations_name_not_empty CHECK (LENGTH(TRIM(name)) > 0),
    CONSTRAINT organizations_slug_format CHECK (slug ~ '^[a-z0-9-]+$'),
    CONSTRAINT organizations_slug_length CHECK (LENGTH(slug) BETWEEN 2 AND 50)
);

-- ORGANIZATION MEMBERS TABLE
-- Links users to organizations with roles
CREATE TABLE IF NOT EXISTS activity.organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES activity.users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES activity.organizations(id) ON DELETE CASCADE,

    -- Role within organization (org-level, not group-level)
    -- "owner" = full control, "admin" = manage members/groups, "member" = regular user
    role TEXT NOT NULL DEFAULT 'member',

    -- Metadata
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    invited_by UUID REFERENCES activity.users(id) ON DELETE SET NULL,

    -- Constraints
    CONSTRAINT organization_members_unique_user_org UNIQUE(user_id, organization_id),
    CONSTRAINT organization_members_role_valid CHECK (role IN ('owner', 'admin', 'member'))
);

-- ============================================================================
-- INDEXES (Performance Optimization)
-- ============================================================================

-- Organizations
CREATE INDEX idx_organizations_slug ON activity.organizations(slug) WHERE deleted_at IS NULL;
CREATE INDEX idx_organizations_created_at ON activity.organizations(created_at);

-- Organization Members
CREATE INDEX idx_org_members_user_id ON activity.organization_members(user_id);
CREATE INDEX idx_org_members_org_id ON activity.organization_members(organization_id);
CREATE INDEX idx_org_members_role ON activity.organization_members(role);
CREATE INDEX idx_org_members_user_org ON activity.organization_members(user_id, organization_id);

-- ============================================================================
-- TRIGGER: Auto-update updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.update_organizations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_organizations_updated_at
    BEFORE UPDATE ON activity.organizations
    FOR EACH ROW
    EXECUTE FUNCTION activity.update_organizations_updated_at();

-- ============================================================================
-- STORED PROCEDURES: Organization Management
-- ============================================================================

-- ----------------------------------------------------------------------------
-- SP: Create Organization
-- Creates a new organization and adds creator as owner (atomic transaction)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_create_organization(
    p_name TEXT,
    p_slug TEXT,
    p_description TEXT,
    p_creator_user_id UUID
)
RETURNS TABLE(
    id UUID,
    name TEXT,
    slug TEXT,
    description TEXT,
    created_at TIMESTAMPTZ
) AS $$
DECLARE
    v_org_id UUID;
BEGIN
    -- Insert organization
    INSERT INTO activity.organizations (name, slug, description)
    VALUES (p_name, p_slug, p_description)
    RETURNING activity.organizations.id INTO v_org_id;

    -- Add creator as owner
    INSERT INTO activity.organization_members (user_id, organization_id, role, invited_by)
    VALUES (p_creator_user_id, v_org_id, 'owner', NULL);

    -- Return created organization
    RETURN QUERY
    SELECT
        o.id,
        o.name,
        o.slug,
        o.description,
        o.created_at
    FROM activity.organizations o
    WHERE o.id = v_org_id;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- SP: Get User's Organizations
-- Returns all organizations a user is member of with role and stats
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_get_user_organizations(
    p_user_id UUID
)
RETURNS TABLE(
    id UUID,
    name TEXT,
    slug TEXT,
    description TEXT,
    role TEXT,
    member_count BIGINT,
    joined_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        o.id,
        o.name,
        o.slug,
        o.description,
        om.role,
        (SELECT COUNT(*) FROM activity.organization_members WHERE organization_id = o.id) as member_count,
        om.joined_at
    FROM activity.organizations o
    INNER JOIN activity.organization_members om ON o.id = om.organization_id
    WHERE om.user_id = p_user_id
      AND o.deleted_at IS NULL
    ORDER BY om.joined_at DESC;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- SP: Get Organization by ID
-- Returns organization details with member count
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_get_organization_by_id(
    p_org_id UUID
)
RETURNS TABLE(
    id UUID,
    name TEXT,
    slug TEXT,
    description TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    member_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        o.id,
        o.name,
        o.slug,
        o.description,
        o.created_at,
        o.updated_at,
        (SELECT COUNT(*) FROM activity.organization_members WHERE organization_id = o.id) as member_count
    FROM activity.organizations o
    WHERE o.id = p_org_id
      AND o.deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- SP: Check if user is member of organization
-- Fast boolean check for membership
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_is_organization_member(
    p_user_id UUID,
    p_org_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    v_is_member BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1
        FROM activity.organization_members
        WHERE user_id = p_user_id
          AND organization_id = p_org_id
    ) INTO v_is_member;

    RETURN v_is_member;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- SP: Get user's role in organization
-- Returns role string or NULL if not member
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_get_user_org_role(
    p_user_id UUID,
    p_org_id UUID
)
RETURNS TEXT AS $$
DECLARE
    v_role TEXT;
BEGIN
    SELECT role INTO v_role
    FROM activity.organization_members
    WHERE user_id = p_user_id
      AND organization_id = p_org_id;

    RETURN v_role;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- SP: Check organization permission (NEW - for efficient authorization)
-- Returns true if user has one of the required roles in the organization
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_check_org_permission(
    p_user_id UUID,
    p_org_id UUID,
    p_required_roles TEXT[]  -- e.g., ARRAY['owner', 'admin']
)
RETURNS BOOLEAN AS $$
DECLARE
    v_user_role TEXT;
    v_has_permission BOOLEAN;
BEGIN
    -- Get user's role
    SELECT role INTO v_user_role
    FROM activity.organization_members
    WHERE user_id = p_user_id
      AND organization_id = p_org_id;

    -- Check if role is in required roles
    v_has_permission := v_user_role = ANY(p_required_roles);

    RETURN COALESCE(v_has_permission, FALSE);
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- SP: Add member to organization
-- Adds user to organization with specified role (idempotent)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_add_organization_member(
    p_user_id UUID,
    p_org_id UUID,
    p_role TEXT,
    p_invited_by UUID
)
RETURNS TABLE(
    id UUID,
    user_email TEXT,
    role TEXT,
    joined_at TIMESTAMPTZ
) AS $$
BEGIN
    -- Insert membership (ON CONFLICT DO NOTHING for idempotency)
    INSERT INTO activity.organization_members (user_id, organization_id, role, invited_by)
    VALUES (p_user_id, p_org_id, p_role, p_invited_by)
    ON CONFLICT (user_id, organization_id) DO NOTHING;

    -- Return membership info
    RETURN QUERY
    SELECT
        om.id,
        u.email,
        om.role,
        om.joined_at
    FROM activity.organization_members om
    INNER JOIN activity.users u ON om.user_id = u.id
    WHERE om.user_id = p_user_id
      AND om.organization_id = p_org_id;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- SP: Remove member from organization
-- Removes user from organization (returns true if removed, false if not found)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_remove_organization_member(
    p_user_id UUID,
    p_org_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    v_deleted BOOLEAN;
BEGIN
    DELETE FROM activity.organization_members
    WHERE user_id = p_user_id
      AND organization_id = p_org_id;

    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted > 0;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- SP: Update member role
-- Changes user's role in organization
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_update_member_role(
    p_user_id UUID,
    p_org_id UUID,
    p_new_role TEXT
)
RETURNS BOOLEAN AS $$
DECLARE
    v_updated BOOLEAN;
BEGIN
    UPDATE activity.organization_members
    SET role = p_new_role
    WHERE user_id = p_user_id
      AND organization_id = p_org_id;

    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RETURN v_updated > 0;
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- SP: Get organization members
-- Returns paginated list of members with details
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION activity.sp_get_organization_members(
    p_org_id UUID,
    p_limit INT DEFAULT 100,
    p_offset INT DEFAULT 0
)
RETURNS TABLE(
    user_id UUID,
    email TEXT,
    role TEXT,
    joined_at TIMESTAMPTZ,
    invited_by_email TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        om.user_id,
        u.email,
        om.role,
        om.joined_at,
        inviter.email as invited_by_email
    FROM activity.organization_members om
    INNER JOIN activity.users u ON om.user_id = u.id
    LEFT JOIN activity.users inviter ON om.invited_by = inviter.id
    WHERE om.organization_id = p_org_id
    ORDER BY om.joined_at DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VERIFICATION QUERIES (run after migration to verify)
-- ============================================================================
-- SELECT * FROM activity.organizations;
-- SELECT * FROM activity.organization_members;
-- SELECT activity.sp_get_user_organizations('user-uuid-here');
-- SELECT activity.sp_check_org_permission('user-uuid', 'org-uuid', ARRAY['owner', 'admin']);
