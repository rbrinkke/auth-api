"""
Group and Permission Models

Python interfaces for groups, permissions, and authorization operations.
Follows same pattern as organizations - thin Python layer over DB stored procedures.

Sprint 2: RBAC Implementation
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
import asyncpg
from pydantic import BaseModel, Field


# ============================================================================
# PYDANTIC SCHEMAS - Permissions
# ============================================================================

class PermissionCreate(BaseModel):
    """Request schema for creating a permission."""
    resource: str = Field(..., min_length=1, max_length=50, pattern="^[a-z_]+$",
                         description="Resource name (lowercase, underscores)")
    action: str = Field(..., min_length=1, max_length=50, pattern="^[a-z_]+$",
                       description="Action name (lowercase, underscores)")
    description: Optional[str] = Field(None, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "resource": "activity",
                "action": "create",
                "description": "Create new activities"
            }
        }


class PermissionResponse(BaseModel):
    """Response schema for permission data."""
    id: UUID
    resource: str
    action: str
    permission_string: str  # e.g., "activity:create"
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "resource": "activity",
                "action": "create",
                "permission_string": "activity:create",
                "description": "Create new activities"
            }
        }


# ============================================================================
# PYDANTIC SCHEMAS - Groups
# ============================================================================

class GroupCreate(BaseModel):
    """Request schema for creating a group."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Content Creators",
                "description": "Users who can create and publish activities"
            }
        }


class GroupUpdate(BaseModel):
    """Request schema for updating a group."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)


class GroupResponse(BaseModel):
    """Response schema for group data."""
    id: UUID
    organization_id: UUID
    name: str
    description: Optional[str] = None
    member_count: int = 0
    created_by: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GroupMemberAdd(BaseModel):
    """Request schema for adding member to group."""
    user_id: UUID

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class GroupMemberResponse(BaseModel):
    """Response schema for group member."""
    user_id: UUID
    email: str
    added_at: datetime
    added_by: UUID

    class Config:
        from_attributes = True


class GroupPermissionGrant(BaseModel):
    """Request schema for granting permission to group."""
    permission_id: UUID

    class Config:
        json_schema_extra = {
            "example": {
                "permission_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class GroupPermissionResponse(BaseModel):
    """Response schema for group permission."""
    permission_id: UUID
    resource: str
    action: str
    permission_string: str
    description: Optional[str] = None
    granted_at: datetime
    granted_by: UUID

    class Config:
        from_attributes = True


# ============================================================================
# PYDANTIC SCHEMAS - Authorization
# ============================================================================

class AuthorizationRequest(BaseModel):
    """Request schema for authorization check."""
    user_id: UUID
    organization_id: UUID
    permission: str = Field(..., pattern="^[a-z_]+:[a-z_]+$",
                           description="Permission string (resource:action)")
    resource_id: Optional[UUID] = Field(None, description="Optional specific resource ID")
    request_id: Optional[UUID] = Field(None, description="Correlation ID for request tracing (X-Correlation-ID)")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "organization_id": "660e8400-e29b-41d4-a716-446655440001",
                "permission": "activity:update",
                "resource_id": "770e8400-e29b-41d4-a716-446655440002",
                "request_id": "880e8400-e29b-41d4-a716-446655440003"
            }
        }


class AuthorizationResponse(BaseModel):
    """Response schema for authorization check."""
    authorized: bool
    reason: Optional[str] = None
    matched_groups: Optional[List[str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "authorized": True,
                "reason": "User has permission via group membership",
                "matched_groups": ["Admins", "Content Creators"]
            }
        }


class UserPermissionsResponse(BaseModel):
    """Response schema for user's permissions list."""
    permissions: List[str]  # List of "resource:action" strings
    details: Optional[List[dict]] = None  # Optional detailed breakdown

    class Config:
        json_schema_extra = {
            "example": {
                "permissions": ["activity:create", "activity:read", "activity:update"],
                "details": [
                    {
                        "permission": "activity:create",
                        "via_group": "Content Creators",
                        "via_group_id": "550e8400-e29b-41d4-a716-446655440000"
                    }
                ]
            }
        }


# ============================================================================
# DATABASE RECORD WRAPPERS
# ============================================================================

class PermissionRecord:
    """Wrapper for permission database record."""

    def __init__(self, record: asyncpg.Record):
        self.id: UUID = record["id"]
        self.resource: str = record["resource"]
        self.action: str = record["action"]
        self.permission_string: str = f"{record['resource']}:{record['action']}"
        self.description: Optional[str] = record.get("description")
        self.created_at: Optional[datetime] = record.get("created_at")


class GroupRecord:
    """Wrapper for group database record."""

    def __init__(self, record: asyncpg.Record):
        self.id: UUID = record["id"]
        self.organization_id: UUID = record["organization_id"]
        self.name: str = record["name"]
        self.description: Optional[str] = record.get("description")
        self.member_count: int = record.get("member_count", 0)
        self.created_by: UUID = record["created_by"]
        self.created_at: datetime = record["created_at"]
        self.updated_at: Optional[datetime] = record.get("updated_at")


class GroupMemberRecord:
    """Wrapper for group member database record."""

    def __init__(self, record: asyncpg.Record):
        self.user_id: UUID = record["user_id"]
        self.email: str = record["email"]
        self.added_at: datetime = record["added_at"]
        self.added_by: UUID = record["added_by"]


class GroupPermissionRecord:
    """Wrapper for group permission database record."""

    def __init__(self, record: asyncpg.Record):
        self.permission_id: UUID = record["permission_id"]
        self.resource: str = record["resource"]
        self.action: str = record["action"]
        self.permission_string: str = f"{record['resource']}:{record['action']}"
        self.description: Optional[str] = record.get("description")
        self.granted_at: datetime = record["granted_at"]
        self.granted_by: UUID = record["granted_by"]


class UserPermissionRecord:
    """Wrapper for user permission database record."""

    def __init__(self, record: asyncpg.Record):
        self.permission_id: UUID = record["permission_id"]
        self.resource: str = record["resource"]
        self.action: str = record["action"]
        self.permission_string: str = f"{record['resource']}:{record['action']}"
        self.description: Optional[str] = record.get("description")
        self.via_group_id: UUID = record["via_group_id"]
        self.via_group_name: str = record["via_group_name"]
        self.granted_at: datetime = record["granted_at"]


# ============================================================================
# DATABASE PROCEDURES - Permissions
# ============================================================================

async def sp_create_permission(
    conn: asyncpg.Connection,
    resource: str,
    action: str,
    description: Optional[str] = None
) -> UUID:
    """Create a new permission (or return existing ID)."""
    result = await conn.fetchval(
        "SELECT activity.sp_create_permission($1, $2, $3)",
        resource.lower(), action.lower(), description
    )

    if not result:
        raise RuntimeError("sp_create_permission returned no data")

    return result


async def sp_get_permission_by_id(
    conn: asyncpg.Connection,
    permission_id: UUID
) -> Optional[PermissionRecord]:
    """Get permission by ID."""
    result = await conn.fetchrow(
        "SELECT * FROM activity.sp_get_permission_by_id($1)",
        permission_id
    )

    return PermissionRecord(result) if result else None


async def sp_get_permission_by_resource_action(
    conn: asyncpg.Connection,
    resource: str,
    action: str
) -> Optional[PermissionRecord]:
    """Get permission by resource:action."""
    result = await conn.fetchrow(
        "SELECT * FROM activity.sp_get_permission_by_resource_action($1, $2)",
        resource.lower(), action.lower()
    )

    return PermissionRecord(result) if result else None


async def sp_list_permissions(
    conn: asyncpg.Connection
) -> List[PermissionRecord]:
    """List all permissions."""
    results = await conn.fetch(
        "SELECT * FROM activity.sp_list_permissions()"
    )

    return [PermissionRecord(r) for r in results]


# ============================================================================
# DATABASE PROCEDURES - Groups
# ============================================================================

async def sp_create_group(
    conn: asyncpg.Connection,
    org_id: UUID,
    name: str,
    description: Optional[str],
    creator_user_id: UUID
) -> UUID:
    """Create a new group."""
    result = await conn.fetchval(
        "SELECT activity.sp_create_group($1, $2, $3, $4)",
        org_id, name, description, creator_user_id
    )

    if not result:
        raise RuntimeError("sp_create_group returned no data")

    return result


async def sp_get_group_by_id(
    conn: asyncpg.Connection,
    group_id: UUID
) -> Optional[GroupRecord]:
    """Get group by ID."""
    result = await conn.fetchrow(
        "SELECT * FROM activity.sp_get_group_by_id($1)",
        group_id
    )

    return GroupRecord(result) if result else None


async def sp_list_organization_groups(
    conn: asyncpg.Connection,
    org_id: UUID
) -> List[GroupRecord]:
    """List all groups in organization."""
    results = await conn.fetch(
        "SELECT * FROM activity.sp_list_organization_groups($1)",
        org_id
    )

    return [GroupRecord(r) for r in results]


async def sp_update_group(
    conn: asyncpg.Connection,
    group_id: UUID,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> bool:
    """Update group."""
    result = await conn.fetchval(
        "SELECT activity.sp_update_group($1, $2, $3)",
        group_id, name, description
    )

    return bool(result)


async def sp_delete_group(
    conn: asyncpg.Connection,
    group_id: UUID,
    deleter_user_id: UUID
) -> bool:
    """Delete group."""
    result = await conn.fetchval(
        "SELECT activity.sp_delete_group($1, $2)",
        group_id, deleter_user_id
    )

    return bool(result)


# ============================================================================
# DATABASE PROCEDURES - Group Membership
# ============================================================================

async def sp_add_user_to_group(
    conn: asyncpg.Connection,
    user_id: UUID,
    group_id: UUID,
    adder_user_id: UUID
) -> bool:
    """Add user to group."""
    result = await conn.fetchval(
        "SELECT activity.sp_add_user_to_group($1, $2, $3)",
        user_id, group_id, adder_user_id
    )

    return bool(result)


async def sp_remove_user_from_group(
    conn: asyncpg.Connection,
    user_id: UUID,
    group_id: UUID,
    remover_user_id: UUID
) -> bool:
    """Remove user from group."""
    result = await conn.fetchval(
        "SELECT activity.sp_remove_user_from_group($1, $2, $3)",
        user_id, group_id, remover_user_id
    )

    return bool(result)


async def sp_list_group_members(
    conn: asyncpg.Connection,
    group_id: UUID
) -> List[GroupMemberRecord]:
    """List all members of a group."""
    results = await conn.fetch(
        "SELECT * FROM activity.sp_list_group_members($1)",
        group_id
    )

    return [GroupMemberRecord(r) for r in results]


async def sp_list_user_groups(
    conn: asyncpg.Connection,
    user_id: UUID,
    org_id: UUID
) -> List[GroupRecord]:
    """List all groups a user belongs to in an organization."""
    results = await conn.fetch(
        "SELECT * FROM activity.sp_list_user_groups($1, $2)",
        user_id, org_id
    )

    # Note: This stored procedure returns group_id, group_name, group_description, added_at
    # We need to fetch full group details for each
    group_records = []
    for r in results:
        group_id = r["group_id"]
        group_detail = await sp_get_group_by_id(conn, group_id)
        if group_detail:
            group_records.append(group_detail)

    return group_records


# ============================================================================
# DATABASE PROCEDURES - Group Permissions
# ============================================================================

async def sp_grant_permission_to_group(
    conn: asyncpg.Connection,
    group_id: UUID,
    permission_id: UUID,
    granter_user_id: UUID
) -> bool:
    """Grant permission to group."""
    result = await conn.fetchval(
        "SELECT activity.sp_grant_permission_to_group($1, $2, $3)",
        group_id, permission_id, granter_user_id
    )

    return bool(result)


async def sp_revoke_permission_from_group(
    conn: asyncpg.Connection,
    group_id: UUID,
    permission_id: UUID,
    revoker_user_id: UUID
) -> bool:
    """Revoke permission from group."""
    result = await conn.fetchval(
        "SELECT activity.sp_revoke_permission_from_group($1, $2, $3)",
        group_id, permission_id, revoker_user_id
    )

    return bool(result)


async def sp_list_group_permissions(
    conn: asyncpg.Connection,
    group_id: UUID
) -> List[GroupPermissionRecord]:
    """List all permissions granted to a group."""
    results = await conn.fetch(
        "SELECT * FROM activity.sp_list_group_permissions($1)",
        group_id
    )

    return [GroupPermissionRecord(r) for r in results]


# ============================================================================
# DATABASE PROCEDURES - Authorization (THE CORE)
# ============================================================================

async def sp_user_has_permission(
    conn: asyncpg.Connection,
    user_id: UUID,
    org_id: UUID,
    resource: str,
    action: str
) -> bool:
    """
    Check if user has specific permission in organization.

    This is the CORE authorization function.
    Returns True if user has the permission via any group membership.
    """
    result = await conn.fetchval(
        "SELECT activity.sp_user_has_permission($1, $2, $3, $4)",
        user_id, org_id, resource.lower(), action.lower()
    )

    return bool(result)


async def sp_get_user_permissions(
    conn: asyncpg.Connection,
    user_id: UUID,
    org_id: UUID
) -> List[UserPermissionRecord]:
    """
    Get all permissions for user in organization.

    Returns list of permissions with details about which groups grant them.
    """
    results = await conn.fetch(
        "SELECT * FROM activity.sp_get_user_permissions($1, $2)",
        user_id, org_id
    )

    return [UserPermissionRecord(r) for r in results]
