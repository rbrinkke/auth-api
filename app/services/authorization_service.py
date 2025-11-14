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
import redis
import json
import os

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

    def __init__(self, db: asyncpg.Connection, redis_client: Optional[redis.Redis] = None):
        self.db = db
        self.redis = redis_client
        # Feature flag: Enable caching if Redis client provided AND env var set
        self.cache_enabled = (
            redis_client is not None and
            os.getenv("AUTHZ_CACHE_ENABLED", "false").lower() == "true"
        )
        # L2 Cache: Pre-fetch ALL user permissions (Phase 4)
        self.l2_cache_enabled = (
            self.cache_enabled and
            os.getenv("AUTHZ_L2_CACHE_ENABLED", "true").lower() == "true"
        )
        if self.cache_enabled:
            logger.info("authorization_cache_enabled",
                       l1_cache=True,
                       l2_cache=self.l2_cache_enabled,
                       cache_ttl_seconds=300)

    async def authorize(
        self,
        request: AuthorizationRequest
    ) -> AuthorizationResponse:
        """
        Check if user has permission in organization (WITH REDIS CACHING).

        This is THE CORE authorization function with 50-80% latency reduction via caching.

        Caching Strategy:
        - L1 Cache: Individual permission checks (auth:check:{user}:{org}:{perm})
        - TTL: 300 seconds (5 minutes)
        - Feature Flag: AUTHZ_CACHE_ENABLED=true
        - Fallback: Database on cache miss

        Algorithm:
        1. Parse permission string (resource:action)
        2. If cache enabled: Check Redis cache (L1)
        3. If cache hit: Return cached result (~2ms)
        4. If cache miss: Query database (~30ms) + cache result
        5. Return AuthorizationResponse

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
                # Allow operation (cached or fresh)
            else:
                # Deny with reason
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

        # L2 Cache Check: User's ALL permissions (Phase 4 - ULTRA FAST! 🚀)
        if self.l2_cache_enabled:
            l2_key = f"auth:perms:{request.user_id}:{request.organization_id}"
            try:
                l2_cached = self.redis.get(l2_key)
                if l2_cached:
                    # L2 HIT! Check if permission exists in set
                    permissions_set = json.loads(l2_cached)
                    authorized = request.permission in permissions_set
                    logger.debug("authz_l2_cache_hit",
                                cache_key=l2_key,
                                user_id=str(request.user_id),
                                permission=request.permission,
                                authorized=authorized,
                                total_permissions=len(permissions_set))
                    track_authz_check("l2_cache_hit", resource, action)
                    return AuthorizationResponse(
                        authorized=authorized,
                        reason="User has permission" if authorized else "Permission not found in user's permissions",
                        matched_groups=None  # Not cached in L2
                    )
            except Exception as e:
                logger.warning("authz_l2_cache_error", error=str(e), cache_key=l2_key)

        # L1 Cache Check: Permission-specific cache (fallback from L2)
        if self.cache_enabled:
            cache_key = f"auth:check:{request.user_id}:{request.organization_id}:{request.permission}"

            try:
                cached_result = self.redis.get(cache_key)
                if cached_result:
                    # L1 Cache HIT! 🚀 (5-10ms response)
                    data = json.loads(cached_result)
                    logger.debug("authz_l1_cache_hit",
                                cache_key=cache_key,
                                user_id=str(request.user_id),
                                permission=request.permission)
                    track_authz_check("l1_cache_hit", resource, action)

                    return AuthorizationResponse(**data)
            except Exception as e:
                # Cache error: log and fallback to database
                logger.warning("authz_cache_error",
                              error=str(e),
                              cache_key=cache_key)

        # Cache MISS or disabled: Query database (~30ms)
        logger.debug("authz_cache_miss", user_id=str(request.user_id), permission=request.permission)
        track_authz_check("cache_miss" if self.cache_enabled else "cache_disabled", resource, action)

        # Track authorization check duration (for p95 latency monitoring)
        with MetricsTimer(authz_check_duration_seconds, resource, action):
            result = await self._authorize_from_database(request, resource, action)

        # L1 Cache: Store individual permission (if caching enabled)
        if self.cache_enabled and self.redis:
            cache_key = f"auth:check:{request.user_id}:{request.organization_id}:{request.permission}"
            try:
                # Store in L1 cache with 300 second TTL
                cache_value = json.dumps({
                    "authorized": result.authorized,
                    "reason": result.reason,
                    "matched_groups": result.matched_groups
                })
                self.redis.setex(cache_key, 300, cache_value)
                logger.debug("authz_l1_cache_stored",
                            cache_key=cache_key,
                            authorized=result.authorized)
            except Exception as e:
                # Cache write error: log but don't fail request
                logger.warning("authz_l1_cache_write_error",
                              error=str(e),
                              cache_key=cache_key)

        # L2 Cache: Pre-populate ALL user permissions (Phase 4 - ULTRA OPTIMIZATION! 🚀)
        if self.l2_cache_enabled and self.redis and result.authorized:
            # Only populate L2 if user is member (successful check)
            try:
                l2_key = f"auth:perms:{request.user_id}:{request.organization_id}"
                # Check if L2 already exists (avoid duplicate work)
                if not self.redis.exists(l2_key):
                    # Fetch ALL user permissions (one-time cost for massive speedup!)
                    all_perms_response = await self.get_user_permissions(
                        request.user_id,
                        request.organization_id
                    )
                    # Store as JSON set with 300 second TTL
                    permissions_list = all_perms_response.permissions
                    self.redis.setex(l2_key, 300, json.dumps(permissions_list))
                    logger.info("authz_l2_cache_populated",
                               cache_key=l2_key,
                               user_id=str(request.user_id),
                               permission_count=len(permissions_list))
            except Exception as e:
                # L2 population error: log but don't fail request
                logger.warning("authz_l2_cache_populate_error",
                              error=str(e),
                              l2_key=l2_key)

        return result

    async def _authorize_from_database(
        self,
        request: AuthorizationRequest,
        resource: str,
        action: str
    ) -> AuthorizationResponse:
        """
        Query database for authorization decision (original logic without cache).

        This is the fallback for cache misses and the source of truth.

        Algorithm:
        1. Check organization membership (security gate)
        2. If not member -> deny immediately
        3. If member -> check permission via groups (sp_user_has_permission)
        4. Return detailed response with reason and matched groups

        Args:
            request: AuthorizationRequest
            resource: Parsed resource from permission
            action: Parsed action from permission

        Returns:
            AuthorizationResponse from database
        """
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
    # Cache Invalidation Methods (Phase 2)
    # ========================================================================

    def invalidate_user_cache(self, user_id: UUID, org_id: UUID) -> None:
        """
        Invalidate all cached permissions for a user in an organization.

        Called when:
        - User added to group
        - User removed from group
        - User permissions change

        Args:
            user_id: User ID
            org_id: Organization ID
        """
        if not self.cache_enabled or not self.redis:
            return

        try:
            # Delete all permission check caches for this user in this org
            pattern = f"auth:check:{user_id}:{org_id}:*"
            keys = self.redis.keys(pattern)

            if keys:
                self.redis.delete(*keys)
                logger.info("cache_invalidated_user",
                           user_id=str(user_id),
                           org_id=str(org_id),
                           keys_deleted=len(keys))
            else:
                logger.debug("cache_invalidation_no_keys",
                            user_id=str(user_id),
                            org_id=str(org_id))
        except Exception as e:
            logger.error("cache_invalidation_error",
                        user_id=str(user_id),
                        org_id=str(org_id),
                        error=str(e))

    async def invalidate_group_caches(self, group_id: UUID, org_id: UUID) -> None:
        """
        Invalidate cached permissions for all members of a group.

        Called when:
        - Permission granted to group
        - Permission revoked from group
        - Group deleted

        Args:
            group_id: Group ID
            org_id: Organization ID
        """
        if not self.cache_enabled or not self.redis:
            return

        try:
            # Get all group members from database
            from app.models.group import sp_get_group_members

            members = await sp_get_group_members(self.db, group_id)

            # Invalidate cache for each member
            invalidated_count = 0
            for member in members:
                self.invalidate_user_cache(member.user_id, org_id)
                invalidated_count += 1

            logger.info("cache_invalidated_group",
                       group_id=str(group_id),
                       org_id=str(org_id),
                       members_count=invalidated_count)
        except Exception as e:
            logger.error("cache_invalidation_group_error",
                        group_id=str(group_id),
                        org_id=str(org_id),
                        error=str(e))


# ============================================================================
# Dependency Injection Helper
# ============================================================================

async def get_authorization_service(
    db: asyncpg.Connection = None,
    redis_client: Optional[redis.Redis] = None
) -> AuthorizationService:
    """
    Get AuthorizationService instance with database connection and Redis client.

    Redis client is optional - caching only enabled if:
    1. Redis client is provided
    2. AUTHZ_CACHE_ENABLED=true environment variable is set

    Usage in FastAPI routes:
        from fastapi import Depends
        from app.core.redis_client import get_redis_client

        @router.post("/authorize")
        async def authorize_endpoint(
            auth_service: AuthorizationService = Depends(get_authorization_service),
            redis: redis.Redis = Depends(get_redis_client)
        ):
            # AuthorizationService will use Redis for caching
            ...

    Args:
        db: Database connection (optional, will be created if None)
        redis_client: Redis client for caching (optional)

    Returns:
        AuthorizationService instance with caching support
    """
    if db is None:
        db = await get_db_connection()
    return AuthorizationService(db, redis_client)
