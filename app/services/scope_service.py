"""
Scope Service

Maps permissions to OAuth 2.0 scopes and validates scope requests.
This is the bridge between the existing RBAC permission system and OAuth scopes.

Key Insight: Our permission format (resource:action) is IDENTICAL to OAuth scope format!
Example: "activity:create" is both a permission AND an OAuth scope.
"""

from typing import List, Set, Optional
from uuid import UUID
import asyncpg
from fastapi import Depends

from app.db.connection import get_db_connection
from app.services.authorization_service import AuthorizationService
from app.core.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# SCOPE DESCRIPTIONS (for consent screen)
# ============================================================================

SCOPE_DESCRIPTIONS = {
    # Activity scopes
    "activity:create": "Create new activities on your behalf",
    "activity:read": "View your activities and activity history",
    "activity:update": "Modify your existing activities",
    "activity:delete": "Delete your activities",

    # Image scopes
    "image:upload": "Upload images to your account",
    "image:read": "View your uploaded images",
    "image:delete": "Delete your images",

    # User scopes
    "user:read": "View your profile information",
    "user:update": "Update your profile information",

    # Group management scopes
    "group:create": "Create new groups in your organizations",
    "group:read": "View groups and their members",
    "group:update": "Modify group details",
    "group:delete": "Delete groups",
    "group:manage_members": "Add or remove group members",
    "group:manage_permissions": "Grant or revoke group permissions",

    # Organization scopes
    "organization:read": "View organization details",
    "organization:update": "Modify organization settings",
    "organization:manage_members": "Add or remove organization members",
}


class ScopeService:
    """
    Scope validation and permission mapping service.

    This service is the CORE of OAuth scope handling. It:
    1. Validates requested scopes against client's allowed scopes
    2. Validates requested scopes against user's actual permissions
    3. Computes the intersection (granted scopes)
    4. Provides scope descriptions for consent screen
    """

    def __init__(
        self,
        db: asyncpg.Connection = Depends(get_db_connection),
        authz_service: AuthorizationService = Depends(AuthorizationService)
    ):
        self.db = db
        self.authz_service = authz_service

    async def validate_and_grant_scopes(
        self,
        requested_scopes: List[str],
        client_allowed_scopes: List[str],
        user_id: UUID,
        organization_id: Optional[UUID]
    ) -> List[str]:
        """
        Validate requested scopes and return granted scopes.

        Algorithm:
        1. Validate requested scopes are in client's allowed scopes
        2. Get user's actual permissions in the organization
        3. Granted scopes = intersection(requested, client_allowed, user_permissions)

        Args:
            requested_scopes: Scopes the client is requesting
            client_allowed_scopes: Scopes the client is allowed to request
            user_id: User ID
            organization_id: Organization context (None for user-level)

        Returns:
            List of granted scopes (may be subset of requested)

        Raises:
            ValueError: If requested scopes contain invalid scopes

        Example:
            requested = ["activity:read", "activity:create", "activity:delete"]
            client_allowed = ["activity:read", "activity:create"]  # Client can't request delete
            user_perms = ["activity:read", "activity:update"]  # User doesn't have create

            granted = ["activity:read"]  # Only intersection
        """
        logger.info("scope_validation_start",
                   user_id=str(user_id),
                   org_id=str(organization_id) if organization_id else None,
                   requested_count=len(requested_scopes))

        # Step 1: Validate scope format
        for scope in requested_scopes:
            if not self._is_valid_scope_format(scope):
                logger.warning("scope_validation_failed_format",
                              scope=scope,
                              user_id=str(user_id))
                raise ValueError(f"Invalid scope format: {scope}")

        # Step 2: Filter by client allowed scopes
        requested_set = set(requested_scopes)
        client_allowed_set = set(client_allowed_scopes)

        # Scopes client is allowed to request
        client_valid_scopes = requested_set & client_allowed_set

        if len(client_valid_scopes) < len(requested_set):
            denied_by_client = requested_set - client_allowed_set
            logger.warning("scope_denied_by_client_policy",
                          denied_scopes=list(denied_by_client),
                          user_id=str(user_id))

        logger.debug("scope_client_validation_passed",
                    valid_count=len(client_valid_scopes))

        # Step 3: Filter by user permissions
        if organization_id:
            # Get user's permissions in organization
            user_permissions_response = await self.authz_service.get_user_permissions(
                user_id=user_id,
                organization_id=organization_id
            )
            user_permissions_set = set(user_permissions_response.permissions)
        else:
            # User-level token (no organization context)
            # TODO: Implement user-level permissions
            # For now, assume user has no permissions without organization
            user_permissions_set = set()

        logger.debug("scope_user_permissions_retrieved",
                    permission_count=len(user_permissions_set))

        # Step 4: Compute intersection (granted scopes)
        granted_scopes = list(client_valid_scopes & user_permissions_set)

        if len(granted_scopes) < len(client_valid_scopes):
            denied_by_permissions = client_valid_scopes - user_permissions_set
            logger.info("scope_denied_by_user_permissions",
                       denied_scopes=list(denied_by_permissions),
                       user_id=str(user_id),
                       org_id=str(organization_id) if organization_id else None)

        logger.info("scope_validation_complete",
                   user_id=str(user_id),
                   org_id=str(organization_id) if organization_id else None,
                   requested_count=len(requested_scopes),
                   granted_count=len(granted_scopes))

        return granted_scopes

    def get_scope_descriptions(self, scopes: List[str]) -> dict[str, str]:
        """
        Get human-readable descriptions for scopes (for consent screen).

        Args:
            scopes: List of scopes

        Returns:
            Dict mapping scope to description

        Example:
            >>> service.get_scope_descriptions(["activity:read", "activity:create"])
            {
                "activity:read": "View your activities and activity history",
                "activity:create": "Create new activities on your behalf"
            }
        """
        descriptions = {}
        for scope in scopes:
            descriptions[scope] = SCOPE_DESCRIPTIONS.get(
                scope,
                f"Access {scope}"  # Fallback description
            )
        return descriptions

    def _is_valid_scope_format(self, scope: str) -> bool:
        """
        Validate scope format (resource:action).

        Args:
            scope: Scope to validate

        Returns:
            True if valid format, False otherwise

        Valid examples:
            - "activity:read"
            - "image:upload"
            - "user:update"

        Invalid examples:
            - "activity" (missing action)
            - "activity:read:extra" (too many parts)
            - "activity:" (empty action)
            - ":read" (empty resource)
        """
        if not scope or not isinstance(scope, str):
            return False

        parts = scope.split(':')

        # Must have exactly 2 parts (resource:action)
        if len(parts) != 2:
            return False

        resource, action = parts

        # Both resource and action must be non-empty
        if not resource or not action:
            return False

        # Resource and action must be alphanumeric + underscores
        if not (resource.replace('_', '').isalnum() and action.replace('_', '').isalnum()):
            return False

        return True

    def parse_scope_string(self, scope_string: str) -> List[str]:
        """
        Parse space-separated scope string into list.

        Per OAuth spec, scopes are space-separated in requests and responses.

        Args:
            scope_string: Space-separated scopes (e.g., "activity:read image:upload")

        Returns:
            List of individual scopes

        Example:
            >>> service.parse_scope_string("activity:read activity:create image:upload")
            ["activity:read", "activity:create", "image:upload"]
        """
        if not scope_string:
            return []

        # Split by space, remove duplicates, preserve order
        scopes = []
        seen = set()
        for scope in scope_string.split():
            scope = scope.strip()
            if scope and scope not in seen:
                scopes.append(scope)
                seen.add(scope)

        return scopes

    def format_scope_list(self, scopes: List[str]) -> str:
        """
        Format scope list as space-separated string.

        Per OAuth spec, scopes are space-separated in tokens and responses.

        Args:
            scopes: List of scopes

        Returns:
            Space-separated scope string

        Example:
            >>> service.format_scope_list(["activity:read", "activity:create"])
            "activity:read activity:create"
        """
        return " ".join(scopes)

    async def validate_scope_downscopinng(
        self,
        original_scopes: List[str],
        requested_scopes: List[str]
    ) -> bool:
        """
        Validate that requested scopes are a subset of original scopes (downscoping).

        Used during refresh token flow when client requests fewer scopes.

        Args:
            original_scopes: Scopes from original authorization
            requested_scopes: Scopes being requested in refresh

        Returns:
            True if requested is subset of original (valid downscoping)

        Example:
            original = ["activity:read", "activity:create", "activity:update"]
            requested = ["activity:read"]  # Valid downscoping
            >>> validate_scope_downscoping(original, requested)
            True

            requested = ["activity:delete"]  # Invalid (not in original)
            >>> validate_scope_downscoping(original, requested)
            False
        """
        original_set = set(original_scopes)
        requested_set = set(requested_scopes)

        # Requested must be subset of original
        is_valid = requested_set.issubset(original_set)

        if not is_valid:
            invalid_scopes = requested_set - original_set
            logger.warning("scope_downscoping_failed",
                          invalid_scopes=list(invalid_scopes))

        return is_valid

    def get_all_available_scopes(self) -> List[str]:
        """
        Get all available scopes in the system.

        This is useful for:
        - OAuth discovery endpoint (scopes_supported)
        - Admin UI for configuring clients

        Returns:
            List of all available scopes
        """
        return sorted(SCOPE_DESCRIPTIONS.keys())


# ============================================================================
# DEPENDENCY INJECTION HELPER
# ============================================================================

async def get_scope_service(
    db: asyncpg.Connection = Depends(get_db_connection)
) -> ScopeService:
    """
    Get ScopeService instance with database connection.

    Usage in FastAPI routes:
        scope_service: ScopeService = Depends(get_scope_service)
    """
    authz_service = AuthorizationService(db)
    return ScopeService(db, authz_service)
