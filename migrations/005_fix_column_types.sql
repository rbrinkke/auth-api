-- ============================================================================
-- Migration 005: Fix column type casting in stored procedures
-- ============================================================================
-- Fixes type mismatches between varchar and text in return types
-- ============================================================================

-- Fix sp_get_user_organizations with proper type casting
CREATE OR REPLACE FUNCTION activity.sp_get_user_organizations(p_user_id uuid)
RETURNS TABLE(id uuid, name text, slug text, description text, role text, member_count bigint, joined_at timestamp with time zone)
LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    SELECT
        o.organization_id as id,
        o.name::text,
        o.slug::text,
        o.description::text,
        om.role::text,
        (SELECT COUNT(*) FROM activity.organization_members WHERE organization_id = o.organization_id) as member_count,
        om.joined_at
    FROM activity.organizations o
    INNER JOIN activity.organization_members om ON o.organization_id = om.organization_id
    WHERE om.user_id = p_user_id
    ORDER BY om.joined_at DESC;
END;
$function$;

-- Fix sp_create_organization with proper type casting
CREATE OR REPLACE FUNCTION activity.sp_create_organization(
    p_owner_user_id uuid,
    p_name text,
    p_slug text,
    p_description text DEFAULT NULL
)
RETURNS TABLE(id uuid, name text, slug text, description text, created_at timestamp with time zone)
LANGUAGE plpgsql
AS $function$
DECLARE
    v_org_id uuid;
BEGIN
    -- Insert new organization
    INSERT INTO activity.organizations (name, slug, description)
    VALUES (p_name, p_slug, p_description)
    RETURNING organization_id INTO v_org_id;

    -- Add owner as member with 'owner' role
    INSERT INTO activity.organization_members (organization_id, user_id, role)
    VALUES (v_org_id, p_owner_user_id, 'owner');

    -- Return organization details
    RETURN QUERY
    SELECT
        o.organization_id as id,
        o.name::text,
        o.slug::text,
        o.description::text,
        o.created_at
    FROM activity.organizations o
    WHERE o.organization_id = v_org_id;
END;
$function$;

-- Fix sp_get_organization_members with proper type casting
CREATE OR REPLACE FUNCTION activity.sp_get_organization_members(p_organization_id uuid)
RETURNS TABLE(user_id uuid, email text, role text, joined_at timestamp with time zone)
LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    SELECT
        u.user_id,
        u.email::text,
        om.role::text,
        om.joined_at
    FROM activity.organization_members om
    INNER JOIN activity.users u ON om.user_id = u.user_id
    WHERE om.organization_id = p_organization_id
    ORDER BY om.joined_at ASC;
END;
$function$;
