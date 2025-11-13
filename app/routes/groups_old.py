"""
Groups API Routes

Sprint 2: RBAC Implementation

Endpoints for group and permission management within organizations.
Thin routing layer - delegates to GroupService for business logic.

Security:
- All endpoints require authentication (get_current_user_id dependency)
- Group operations require organization membership
- Management operations require admin/owner role (enforced in service layer)
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
import asyncpg

from app.db.connection import get_db_connection
from app.core.dependencies import get_current_user_id
from app.core.oauth_resource_server import get_current_principal
from app.services.group_service import GroupService
from app.models.group import (
    GroupCreate,
    GroupUpdate,
    GroupResponse,
    GroupMemberAdd,
    GroupMemberResponse,
    GroupPermissionGrant,
    GroupPermissionResponse,
    PermissionCreate,
    PermissionResponse,
)

router = APIRouter()


# ============================================================================
# GROUP CRUD
# ============================================================================

@router.post(
    "/organizations/{org_id}/groups",
    response_model=GroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Group",
    description="Create a new group in organization (requires admin/owner role)"
)
async def create_group(
    org_id: UUID,
    group_data: GroupCreate,
    principal: dict = Depends(get_current_principal),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Create a new group in organization.

    **Security**: Requires admin or owner role.

    **Request Body**:
    - name: Group name (unique per organization)
    - description: Optional group description

    **Returns**: Created group details
    """
    service = GroupService(db)
    return await service.create_group(org_id, group_data, current_user_id)


@router.get(
    "/organizations/{org_id}/groups",
    response_model=List[GroupResponse],
    summary="List Groups",
    description="List all groups in organization (OAuth Bearer or session auth)"
)
async def list_organization_groups(
    org_id: UUID,
    principal: dict = Depends(get_current_principal),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """
    List all groups in organization.

    **Security**: OAuth Bearer token (scope: groups:read) or session cookie.
    - Service tokens: Require 'groups:read' scope
    - User tokens: Require organization membership

    **Returns**: List of groups with member counts
    """
    # Scope validation for service tokens
    if principal["type"] == "service":
        if "groups:read" not in principal["scopes"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope: groups:read required"
            )
        # Service tokens bypass org membership check
        # They have global read access with proper scope
        user_id = None
    else:
        # User tokens use normal flow
        user_id = UUID(principal["user_id"])

    service = GroupService(db)
    return await service.get_organization_groups(org_id, user_id)


@router.get(
    "/groups/{group_id}",
    response_model=GroupResponse,
    summary="Get Group",
    description="Get group details (OAuth Bearer or session auth)"
)
async def get_group(
    group_id: UUID,
    principal: dict = Depends(get_current_principal),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Get group details by ID.

    **Security**: OAuth Bearer token (scope: groups:read) or session cookie.
    - Service tokens: Require 'groups:read' scope
    - User tokens: Require membership in group's organization

    **Returns**: Group details
    """
    # Scope validation for service tokens
    if principal["type"] == "service":
        if "groups:read" not in principal["scopes"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope: groups:read required"
            )
        user_id = None
    else:
        user_id = UUID(principal["user_id"])

    service = GroupService(db)
    return await service.get_group(group_id, user_id)


@router.patch(
    "/groups/{group_id}",
    response_model=GroupResponse,
    summary="Update Group",
    description="Update group details (requires admin/owner role)"
)
async def update_group(
    group_id: UUID,
    group_data: GroupUpdate,
    principal: dict = Depends(get_current_principal),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Update group details.

    **Security**: Requires admin or owner role in group's organization.

    **Request Body**:
    - name: Optional new name
    - description: Optional new description

    **Returns**: Updated group details
    """
    service = GroupService(db)
    return await service.update_group(group_id, group_data, current_user_id)


@router.delete(
    "/groups/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Group",
    description="Delete group (requires owner role)"
)
async def delete_group(
    group_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Delete group.

    **Security**: Requires owner role in group's organization.

    **Note**: Cascades to group memberships and permissions.

    **Returns**: 204 No Content on success
    """
    service = GroupService(db)
    await service.delete_group(group_id, current_user_id)


# ============================================================================
# GROUP MEMBERSHIP
# ============================================================================

@router.post(
    "/groups/{group_id}/members",
    response_model=GroupMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Member",
    description="Add user to group (requires admin/owner role)"
)
async def add_group_member(
    group_id: UUID,
    member_data: GroupMemberAdd,
    principal: dict = Depends(get_current_principal),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Add user to group.

    **Security**: Requires admin or owner role in group's organization.

    **Request Body**:
    - user_id: ID of user to add (must be organization member)

    **Returns**: Added member details
    """
    service = GroupService(db)
    return await service.add_member_to_group(group_id, member_data, current_user_id)


@router.delete(
    "/groups/{group_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove Member",
    description="Remove user from group (requires admin/owner role)"
)
async def remove_group_member(
    group_id: UUID,
    user_id: UUID,
    principal: dict = Depends(get_current_principal),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Remove user from group.

    **Security**: Requires admin or owner role in group's organization.

    **Returns**: 204 No Content on success
    """
    service = GroupService(db)
    await service.remove_member_from_group(group_id, user_id, current_user_id)


@router.get(
    "/groups/{group_id}/members",
    response_model=List[GroupMemberResponse],
    summary="List Members",
    description="List group members (requires membership in group's organization)"
)
async def list_group_members(
    group_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """
    List all members of a group.

    **Security**: Requires membership in group's organization.

    **Returns**: List of group members with join dates
    """
    service = GroupService(db)
    return await service.get_group_members(group_id, current_user_id)


# ============================================================================
# GROUP PERMISSIONS
# ============================================================================

@router.post(
    "/groups/{group_id}/permissions",
    response_model=GroupPermissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Grant Permission",
    description="Grant permission to group (requires owner role)"
)
async def grant_permission_to_group(
    group_id: UUID,
    permission_data: GroupPermissionGrant,
    principal: dict = Depends(get_current_principal),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Grant permission to group.

    **Security**: Requires owner role in group's organization (most sensitive operation).

    **Request Body**:
    - permission_id: ID of permission to grant

    **Returns**: Granted permission details
    """
    service = GroupService(db)
    return await service.grant_permission(group_id, permission_data, current_user_id)


@router.delete(
    "/groups/{group_id}/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke Permission",
    description="Revoke permission from group (requires owner role)"
)
async def revoke_permission_from_group(
    group_id: UUID,
    permission_id: UUID,
    principal: dict = Depends(get_current_principal),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Revoke permission from group.

    **Security**: Requires owner role in group's organization.

    **Returns**: 204 No Content on success
    """
    service = GroupService(db)
    await service.revoke_permission(group_id, permission_id, current_user_id)


@router.get(
    "/groups/{group_id}/permissions",
    response_model=List[GroupPermissionResponse],
    summary="List Permissions",
    description="List permissions granted to group (requires membership)"
)
async def list_group_permissions(
    group_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """
    List all permissions granted to a group.

    **Security**: Requires membership in group's organization.

    **Returns**: List of permissions with grant dates
    """
    service = GroupService(db)
    return await service.get_group_permissions(group_id, current_user_id)


# ============================================================================
# PERMISSION MANAGEMENT
# ============================================================================

@router.post(
    "/permissions",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Permission",
    description="Create a new permission (admin-only operation)"
)
async def create_permission(
    permission_data: PermissionCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Create a new permission.

    **Security**: Requires authentication.
    Future: Should require superadmin role.

    **Request Body**:
    - resource: Resource name (lowercase, underscores)
    - action: Action name (lowercase, underscores)
    - description: Optional description

    **Returns**: Created permission details with resource:action string
    """
    service = GroupService(db)
    return await service.create_permission(permission_data, current_user_id)


@router.get(
    "/permissions",
    response_model=List[PermissionResponse],
    summary="List Permissions",
    description="List all available permissions (public)"
)
async def list_permissions(
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """
    List all available permissions in the system.

    **Security**: Public (permissions are not sensitive).

    **Returns**: List of all permissions with resource:action strings
    """
    service = GroupService(db)
    return await service.list_permissions()
