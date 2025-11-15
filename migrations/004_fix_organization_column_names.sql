-- ============================================================================
-- Migration 004: Fix organization stored procedures for correct column names
-- ============================================================================
-- After database restore, organizations table uses organization_id not id
-- This fixes all stored procedures to use the correct column names
-- ============================================================================

-- Fix sp_get_user_organizations
CREATE OR REPLACE FUNCTION activity.sp_get_user_organizations(p_user_id uuid)
RETURNS TABLE(id uuid, name text, slug text, description text, role text, member_count bigint, joined_at timestamp with time zone)
LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    SELECT
        o.organization_id as id,
        o.name,
        o.slug,
        o.description,
        om.role,
        (SELECT COUNT(*) FROM activity.organization_members WHERE organization_id = o.organization_id) as member_count,
        om.joined_at
    FROM activity.organizations o
    INNER JOIN activity.organization_members om ON o.organization_id = om.organization_id
    WHERE om.user_id = p_user_id
    ORDER BY om.joined_at DESC;
END;
$function$;

-- Fix other organization functions that reference o.id
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
        o.name,
        o.slug,
        o.description,
        o.created_at
    FROM activity.organizations o
    WHERE o.organization_id = v_org_id;
END;
$function$;

-- Fix sp_get_organization_members
CREATE OR REPLACE FUNCTION activity.sp_get_organization_members(p_organization_id uuid)
RETURNS TABLE(user_id uuid, email text, role text, joined_at timestamp with time zone)
LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    SELECT
        u.user_id,
        u.email,
        om.role,
        om.joined_at
    FROM activity.organization_members om
    INNER JOIN activity.users u ON om.user_id = u.user_id
    WHERE om.organization_id = p_organization_id
    ORDER BY om.joined_at ASC;
END;
$function$;

-- Fix sp_get_user_role_in_organization
CREATE OR REPLACE FUNCTION activity.sp_get_user_role_in_organization(
    p_user_id uuid,
    p_organization_id uuid
)
RETURNS text
LANGUAGE plpgsql
AS $function$
DECLARE
    v_role text;
BEGIN
    SELECT role INTO v_role
    FROM activity.organization_members
    WHERE user_id = p_user_id AND organization_id = p_organization_id;

    RETURN v_role;
END;
$function$;
