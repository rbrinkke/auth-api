"""
Permissions API Routes - Authorization Endpoints

Sprint 2: RBAC Implementation - THE CORE ENDPOINT

Exposes the centralized authorization service (Policy Decision Point).
All parts of the Activity App should use POST /authorize to check permissions.

Key Endpoint:
- POST /authorize: THE CORE authorization check (use this everywhere!)

Utility Endpoints:
- GET /users/{user_id}/permissions: List all user permissions
- GET /users/{user_id}/check-permission: Quick permission check (GET variant)

Architecture:
- Thin routing layer - delegates to AuthorizationService
- All authorization logic in service layer and stored procedures
- Stateless (future: Redis caching if needed)
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
import asyncpg

from app.db.connection import get_db_connection
from app.core.dependencies import get_current_user_id
from app.services.authorization_service import AuthorizationService
from app.models.group import (
    AuthorizationRequest,
    AuthorizationResponse,
    UserPermissionsResponse,
)

router = APIRouter()


# ============================================================================
# AUTHORIZATION ENDPOINT - THE CORE
# ============================================================================

@router.post(
    "/authorize",
    response_model=AuthorizationResponse,
    summary="Authorize - THE CORE",
    description="Check if user has permission in organization (Policy Decision Point)"
)
async def authorize(
    request: AuthorizationRequest,
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """
    **THE CORE AUTHORIZATION ENDPOINT** - Policy Decision Point (PDP)

    This is the centralized authorization service that ALL parts of the Activity App
    should use to check permissions. Do not implement custom authorization logic elsewhere.

    **How it works**:
    1. Checks if user is member of organization (security gate)
    2. If not member -> deny immediately
    3. If member -> checks permission via groups (sp_user_has_permission)
    4. Returns detailed response with reason and matched groups

    **Request Body**:
    - user_id: User to check
    - organization_id: Organization context
    - permission: Permission string (resource:action, e.g., "activity:update")
    - resource_id: Optional specific resource ID (for future resource-level permissions)

    **Response**:
    - authorized: Boolean (true if permitted, false otherwise)
    - reason: Human-readable reason for decision
    - matched_groups: List of group names that granted the permission (if authorized)

    **Example Usage**:
    ```python
    # Check if user can update activities
    POST /api/auth/authorize
    {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "organization_id": "660e8400-e29b-41d4-a716-446655440001",
        "permission": "activity:update"
    }

    # Response if authorized:
    {
        "authorized": true,
        "reason": "User has permission via group membership",
        "matched_groups": ["Admins", "Activity Managers"]
    }

    # Response if denied:
    {
        "authorized": false,
        "reason": "No permission 'activity:update' granted",
        "matched_groups": null
    }
    ```

    **Security**:
    - No authentication required on this endpoint itself (it checks authorization for ANY user)
    - Calling services should authenticate their own requests
    - This is a read-only operation (no state changes)

    **Performance**:
    - Currently executes database query via sp_user_has_permission
    - Future: Redis caching (add only if p95 latency > 50ms)
    - Designed for high-volume authorization checks

    **Use Cases**:
    - Activity API checks if user can create/update/delete activities
    - Frontend checks what actions to display in UI
    - Admin dashboards verify management permissions
    - Any service needs authorization decision
    """
    service = AuthorizationService(db)
    return await service.authorize(request)


# ============================================================================
# USER PERMISSIONS - UTILITY ENDPOINTS
# ============================================================================

@router.get(
    "/users/{user_id}/permissions",
    response_model=UserPermissionsResponse,
    summary="Get User Permissions",
    description="List all permissions user has in organization"
)
async def get_user_permissions(
    user_id: UUID,
    organization_id: UUID = Query(..., description="Organization ID"),
    current_user_id: UUID = Depends(get_current_user_id),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Get all permissions user has in organization.

    **Use Cases**:
    - User settings page showing "Your Permissions"
    - Admin dashboard showing what permissions users have
    - Permission debugging
    - Displaying available actions in UI

    **Query Parameters**:
    - organization_id: Organization to check permissions in

    **Response**:
    - permissions: List of permission strings (["activity:create", "activity:read", ...])
    - details: Detailed breakdown with group information

    **Example Response**:
    ```json
    {
        "permissions": [
            "activity:create",
            "activity:read",
            "activity:update",
            "user:read"
        ],
        "details": [
            {
                "permission": "activity:create",
                "resource": "activity",
                "action": "create",
                "description": "Create new activities",
                "via_group": "Content Creators",
                "via_group_id": "770e8400-e29b-41d4-a716-446655440002",
                "granted_at": "2025-11-12T10:30:00Z"
            }
        ]
    }
    ```

    **Security**:
    - Requires authentication
    - Users can view their own permissions
    - Admins can view any user's permissions (future enhancement)
    """
    # Future: Check if current_user_id is admin or querying own permissions
    service = AuthorizationService(db)
    return await service.get_user_permissions(user_id, organization_id)


@router.get(
    "/users/{user_id}/check-permission",
    response_model=AuthorizationResponse,
    summary="Check Permission (GET)",
    description="Quick permission check via GET request (convenience endpoint)"
)
async def check_permission(
    user_id: UUID,
    organization_id: UUID = Query(..., description="Organization ID"),
    permission: str = Query(..., pattern="^[a-z_]+:[a-z_]+$",
                           description="Permission string (resource:action)"),
    current_user_id: UUID = Depends(get_current_user_id),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Quick permission check via GET request.

    This is a convenience endpoint that wraps POST /authorize for situations where
    a GET request is more natural (e.g., browser pre-flight checks, simple curl commands).

    **For production use, prefer POST /authorize** as it supports more complex requests.

    **Query Parameters**:
    - organization_id: Organization context
    - permission: Permission string (e.g., "activity:delete")

    **Response**: Same as POST /authorize

    **Example**:
    ```
    GET /api/auth/users/550e8400-e29b-41d4-a716-446655440000/check-permission?organization_id=660e8400-e29b-41d4-a716-446655440001&permission=activity:update

    Response:
    {
        "authorized": true,
        "reason": "User has permission via group membership",
        "matched_groups": ["Admins"]
    }
    ```

    **Security**: Requires authentication
    """
    request = AuthorizationRequest(
        user_id=user_id,
        organization_id=organization_id,
        permission=permission
    )

    service = AuthorizationService(db)
    return await service.authorize(request)
