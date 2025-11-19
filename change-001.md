echnical Specification: RBAC Implementation (Database-Level)
Doel: Implementatie van een Role-Based Access Control (RBAC) systeem direct in de database. Huidige situatie: Rechten worden gecontroleerd op basis van hardcoded rollen (owner, admin, member). Nieuwe situatie: Rollen worden gekoppeld aan granulaire permissies (bijv. activity:delete). De API checkt permissies, geen rollen.

Stap 1: Database Schema Migratie
Voer de volgende SQL uit om de structuur aan te maken. Dit moet in een nieuw migratiebestand (bijv. migrations/006_rbac_implementation.sql).

SQL

-- 1. Create Permissions Table
-- Defines all granular actions available in the system
CREATE TABLE IF NOT EXISTS activity.permissions (
    permission_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    resource VARCHAR(50) NOT NULL, -- e.g. 'activity', 'user', 'finance'
    action VARCHAR(50) NOT NULL,   -- e.g. 'create', 'read', 'delete_any'
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_permissions_resource_action UNIQUE (resource, action)
);

-- 2. Create Role-Permissions Mapping Table
-- Maps the existing hardcoded roles (owner, admin, member) to specific permissions
CREATE TABLE IF NOT EXISTS activity.role_permissions (
    role TEXT NOT NULL, -- Matches activity.organization_members.role check constraint
    permission_id UUID NOT NULL REFERENCES activity.permissions(permission_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (role, permission_id)
);

-- 3. Create Indexes for Performance
CREATE INDEX idx_permissions_lookup ON activity.permissions(resource, action);
CREATE INDEX idx_role_permissions_role ON activity.role_permissions(role);

-- 4. Grant permissions (Adjust 'auth_api_user' to your actual DB user if different)
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE activity.permissions TO auth_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE activity.role_permissions TO auth_api_user;
Stap 2: Data Seeding (Initiële Rechten)
Vul de tabellen met de standaardregels. Dit zorgt ervoor dat de applicatie direct werkt na de migratie.

SQL

-- A. Define standard permissions
INSERT INTO activity.permissions (resource, action, description) VALUES 
    ('activity', 'create', 'Create new activities'),
    ('activity', 'read', 'View activities'),
    ('activity', 'update_own', 'Update own activities'),
    ('activity', 'delete_own', 'Delete own activities'),
    ('activity', 'update_any', 'Update any activity in organization'),
    ('activity', 'delete_any', 'Delete any activity in organization'),
    ('user', 'invite', 'Invite new users to organization'),
    ('user', 'remove', 'Remove users from organization')
ON CONFLICT (resource, action) DO NOTHING;

-- B. Map permissions to Roles
-- MEMBER Permissions
INSERT INTO activity.role_permissions (role, permission_id)
SELECT 'member', permission_id FROM activity.permissions 
WHERE (resource = 'activity' AND action IN ('read', 'create', 'update_own', 'delete_own'));

-- ADMIN Permissions (Inherits member + management rights)
INSERT INTO activity.role_permissions (role, permission_id)
SELECT 'admin', permission_id FROM activity.permissions 
WHERE (resource = 'activity' AND action IN ('read', 'create', 'update_own', 'delete_own', 'update_any', 'delete_any'))
OR (resource = 'user' AND action IN ('invite'));

-- OWNER Permissions (Everything)
INSERT INTO activity.role_permissions (role, permission_id)
SELECT 'owner', permission_id FROM activity.permissions;
Stap 3: Stored Procedures (De Logica)
Voeg deze functies toe aan app/db/procedures.py of direct in SQL. Deze vervangen complexe queries in de backend code.

A. Check Permission (The Core Check)
Geeft TRUE als de gebruiker de actie mag uitvoeren op basis van zijn rol in die specifieke organisatie.

SQL

CREATE OR REPLACE FUNCTION activity.sp_user_has_permission(
    p_user_id UUID,
    p_org_id UUID,
    p_resource VARCHAR,
    p_action VARCHAR
) RETURNS BOOLEAN
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
    v_has_permission BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM activity.organization_members om
        JOIN activity.role_permissions rp ON om.role = rp.role
        JOIN activity.permissions p ON rp.permission_id = p.permission_id
        WHERE om.user_id = p_user_id
          AND om.organization_id = p_org_id
          AND p.resource = p_resource
          AND p.action = p_action
    ) INTO v_has_permission;

    RETURN COALESCE(v_has_permission, FALSE);
END;
$$;

ALTER FUNCTION activity.sp_user_has_permission(UUID, UUID, VARCHAR, VARCHAR) OWNER TO postgres;
GRANT EXECUTE ON FUNCTION activity.sp_user_has_permission TO auth_api_user;
B. Get All Permissions (Voor Frontend UI)
Haalt een lijst op van alles wat de gebruiker mag doen in de huidige context.

SQL

CREATE OR REPLACE FUNCTION activity.sp_get_user_permissions(
    p_user_id UUID,
    p_org_id UUID
) RETURNS TABLE(resource VARCHAR, action VARCHAR)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT p.resource, p.action
    FROM activity.organization_members om
    JOIN activity.role_permissions rp ON om.role = rp.role
    JOIN activity.permissions p ON rp.permission_id = p.permission_id
    WHERE om.user_id = p_user_id
      AND om.organization_id = p_org_id;
END;
$$;

ALTER FUNCTION activity.sp_get_user_permissions(UUID, UUID) OWNER TO postgres;
GRANT EXECUTE ON FUNCTION activity.sp_get_user_permissions TO auth_api_user;
Stap 4: Backend Implementatie Instructies
In de Python code (app/services/authorization_service.py of waar de logica zit) moeten de harde rol-checks vervangen worden.

Oude Code (Te verwijderen):

Python

# DO NOT USE THIS ANYMORE
if user_role not in ['admin', 'owner']:
    raise ForbiddenException("Only admins can delete activities")
Nieuwe Implementatie:

Roep de SP activity.sp_user_has_permission aan.

Gebruik de cache (Redis) als die beschikbaar is, anders DB call.

Voorbeeld (Python/FastAPI):

Python

async def check_permission(self, user_id: UUID, org_id: UUID, resource: str, action: str) -> bool:
    """
    Checks if user has permission using DB Stored Procedure.
    Should be cached in Redis for performance.
    """
    # 1. Try Cache (Pseudo-code)
    # cache_key = f"perm:{user_id}:{org_id}:{resource}:{action}"
    # if cached := redis.get(cache_key): return cached

    # 2. DB Call
    query = """
        SELECT activity.sp_user_has_permission($1, $2, $3, $4)
    """
    has_permission = await self.db.fetchval(query, user_id, org_id, resource, action)
    
    # 3. Set Cache (e.g., 5 minutes)
    # redis.set(cache_key, has_permission, ex=300)
    
    return has_permission

# Usage in Route
async def delete_activity(activity_id, user_id, org_id):
    # Check: activity:delete_any
    if not await auth_service.check_permission(user_id, org_id, 'activity', 'delete_any'):
        # Fallback: Check if owner (activity:delete_own) AND is author
        is_author = await check_if_author(activity_id, user_id)
        if not (is_author and await auth_service.check_permission(user_id, org_id, 'activity', 'delete_own')):
             raise HTTPException(403, "Insufficient permissions")
             
    # Perform deletion...
