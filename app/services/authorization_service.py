"""
Authorization Service - Policy Decision Point (PDP)

Sprint 2: RBAC Implementation - THE CORE

This is the CENTRALIZED authorization service that all parts of the system should use
to check permissions. It provides a single source of truth for authorization decisions.

Architecture:
- Delegates to sp_user_has_permission (database enforces authorization logic)
- Checks organization membership first (security layer)
- Returns detailed authorization responses (for debugging and audit)
- Future: Redis caching for performance (add only if p95 latency > 50ms)

Design Philosophy:
- Authorization logic lives in database (sp_user_has_permission)
- Service layer is thin orchestration
- Database-first approach ensures consistency
- Measure before optimizing (no premature caching)
"""

from typing import List, Optional, Dict
from uuid import UUID
import asyncpg

from app.db.connection import get_db_connection
from app.models.group import (
    AuthorizationRequest,
    AuthorizationResponse,
    UserPermissionsResponse,
    sp_user_has_permission,
    sp_get_user_permissions,
)
from app.models.organization import sp_is_organization_member
from app.core.logging_config import get_logger
from app.core.metrics import (
    track_authz_check,
    track_permission_lookup,
    MetricsTimer,
    authz_check_duration_seconds,
)

logger = get_logger(__name__)


class AuthorizationService:
    """
    Centralized authorization service (Policy Decision Point).

    This service provides the single source of truth for all authorization decisions
    in the system. All permission checks should go through this service.

    Methods:
        authorize(): Main authorization check (THE CORE)
        get_user_permissions(): List all permissions user has in organization
        check_permission(): Convenience wrapper around authorize()

    Future Enhancements:
        - Redis caching (add only if performance testing shows need)
        - Permission change notifications (for cache invalidation)
        - Authorization audit logging (for compliance)
    """

    def __init__(self, db: asyncpg.Connection):
        self.db = db

    async def authorize(
        self,
        request: AuthorizationRequest
    ) -> AuthorizationResponse:
        """
        Check if user has permission in organization.

        This is THE CORE authorization function. All permission checks should use this.

        Algorithm:
        1. Check if user is member of organization (security gate)
        2. If not member -> deny immediately
        3. If member -> check permission via groups (sp_user_has_permission)
        4. Return detailed response with reason and matched groups

        Args:
            request: AuthorizationRequest with user_id, org_id, permission

        Returns:
            AuthorizationResponse with authorization decision

        Example:
            request = AuthorizationRequest(
                user_id=user_id,
                organization_id=org_id,
                permission="activity:update"
            )
            response = await service.authorize(request)
            if response.authorized:
                # Allow operation
            else:
                # Deny with reason: response.reason
        """
        # Parse permission string
        try:
            resource, action = request.permission.split(":", 1)
        except ValueError:
            logger.warning("authorization_invalid_permission_format",
                          permission=request.permission,
                          user_id=str(request.user_id))
            return AuthorizationResponse(
                authorized=False,
                reason="Invalid permission format (expected resource:action)"
            )

        logger.debug("authorization_check_start",
                    user_id=str(request.user_id),
                    organization_id=str(request.organization_id),
                    permission=request.permission,
                    resource_id=str(request.resource_id) if request.resource_id else None)

        # Track authorization check duration (for p95 latency monitoring)
        with MetricsTimer(authz_check_duration_seconds, resource, action):
            # Step 1: Check organization membership (security gate)
            is_member = await sp_is_organization_member(
                self.db,
                request.user_id,
                request.organization_id
            )

            if not is_member:
                logger.info("authorization_denied_not_member",
                           user_id=str(request.user_id),
                           organization_id=str(request.organization_id))

                # Track denial due to non-membership
                track_authz_check("denied_not_member", resource, action)

                return AuthorizationResponse(
                    authorized=False,
                    reason="Not a member of the organization"
                )

            # Step 2: Check permission via groups
            has_permission = await sp_user_has_permission(
                self.db,
                user_id=request.user_id,
                org_id=request.organization_id,
                resource=resource,
                action=action
            )

            if has_permission:
                # Get which groups granted the permission (for transparency)
                user_permissions = await sp_get_user_permissions(
                    self.db,
                    user_id=request.user_id,
                    org_id=request.organization_id
                )

                matched_groups = [
                    perm.via_group_name
                    for perm in user_permissions
                    if f"{perm.resource}:{perm.action}" == request.permission
                ]

                logger.info("authorization_granted",
                           user_id=str(request.user_id),
                           organization_id=str(request.organization_id),
                           permission=request.permission,
                           matched_groups=matched_groups)

                # Track successful authorization
                track_authz_check("granted", resource, action)

                return AuthorizationResponse(
                    authorized=True,
                    reason="User has permission via group membership",
                    matched_groups=matched_groups
                )
            else:
                logger.info("authorization_denied_no_permission",
                           user_id=str(request.user_id),
                           organization_id=str(request.organization_id),
                           permission=request.permission)

                # Track denial due to missing permission
                track_authz_check("denied_no_permission", resource, action)

                return AuthorizationResponse(
                    authorized=False,
                    reason=f"No permission '{request.permission}' granted"
                )

    async def get_user_permissions(
        self,
        user_id: UUID,
        organization_id: UUID
    ) -> UserPermissionsResponse:
        """
        Get all permissions user has in organization.

        Useful for:
        - Displaying user's permissions in UI
        - Admin dashboards
        - Permission debugging

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            UserPermissionsResponse with list of permissions and details

        Example:
            response = await service.get_user_permissions(user_id, org_id)
            # response.permissions = ["activity:create", "activity:read", ...]
            # response.details = [{"permission": "activity:create", "via_group": "Admins"}, ...]
        """
        logger.debug("get_user_permissions",
                    user_id=str(user_id),
                    organization_id=str(organization_id))

        try:
            # Check membership first
            is_member = await sp_is_organization_member(
                self.db,
                user_id,
                organization_id
            )

            if not is_member:
                # Not a member -> no permissions
                track_permission_lookup("success")
                return UserPermissionsResponse(
                    permissions=[],
                    details=[]
                )

            # Get all permissions
            user_perms = await sp_get_user_permissions(
                self.db,
                user_id=user_id,
                org_id=organization_id
            )

            # Build response
            permissions = []
            details = []

            # De-duplicate permissions (user might have same permission via multiple groups)
            seen_permissions = set()

            for perm in user_perms:
                permission_string = f"{perm.resource}:{perm.action}"

                if permission_string not in seen_permissions:
                    permissions.append(permission_string)
                    seen_permissions.add(permission_string)

                # Add detail for this permission grant
                details.append({
                    "permission": permission_string,
                    "resource": perm.resource,
                    "action": perm.action,
                    "description": perm.description,
                    "via_group": perm.via_group_name,
                    "via_group_id": str(perm.via_group_id),
                    "granted_at": perm.granted_at.isoformat() if perm.granted_at else None
                })

            logger.debug("user_permissions_retrieved",
                        user_id=str(user_id),
                        organization_id=str(organization_id),
                        permission_count=len(permissions),
                        total_grants=len(details))

            # Track successful permission lookup
            track_permission_lookup("success")

            return UserPermissionsResponse(
                permissions=sorted(permissions),  # Alphabetical for consistency
                details=details
            )

        except Exception as e:
            logger.error("permission_lookup_failed",
                        user_id=str(user_id),
                        organization_id=str(organization_id),
                        error=str(e))
            track_permission_lookup("failed")
            raise

    async def check_permission(
        self,
        user_id: UUID,
        organization_id: UUID,
        permission: str,
        resource_id: Optional[UUID] = None
    ) -> bool:
        """
        Convenience method for simple permission checks.

        This is a wrapper around authorize() that returns just a boolean.
        Use this when you only need a yes/no answer and don't need details.

        Args:
            user_id: User ID
            organization_id: Organization ID
            permission: Permission string (resource:action)
            resource_id: Optional specific resource ID

        Returns:
            True if authorized, False otherwise

        Example:
            if await service.check_permission(user_id, org_id, "activity:delete"):
                # User can delete activities
                delete_activity()
            else:
                # User cannot delete activities
                raise InsufficientPermissionError("activity:delete")
        """
        request = AuthorizationRequest(
            user_id=user_id,
            organization_id=organization_id,
            permission=permission,
            resource_id=resource_id
        )

        response = await self.authorize(request)
        return response.authorized

    # ========================================================================
    # Future: Cache Management (add only if needed)
    # ========================================================================
    #
    # async def invalidate_user_cache(self, user_id: UUID, org_id: UUID) -> None:
    #     """Invalidate cached permissions when user's groups or group permissions change"""
    #     pass
    #
    # async def invalidate_group_cache(self, group_id: UUID) -> None:
    #     """Invalidate cached permissions when group's permissions change"""
    #     pass


# ============================================================================
# Dependency Injection Helper
# ============================================================================

async def get_authorization_service(
    db: asyncpg.Connection = None
) -> AuthorizationService:
    """
    Get AuthorizationService instance with database connection.

    Usage in FastAPI routes:
        auth_service: AuthorizationService = Depends(get_authorization_service)
    """
    if db is None:
        db = await get_db_connection()
    return AuthorizationService(db)
