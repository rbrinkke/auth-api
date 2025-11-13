"""
Authentication Dependencies

FastAPI dependencies for extracting and validating authentication context from JWT tokens.

Provides three levels of authentication:
1. User-level: Just user_id (for cross-org operations like listing/creating orgs)
2. Org-level: user_id + org_id (for org-scoped operations)
3. Principal-level: Supports BOTH user AND service tokens (for OAuth2 service-to-service)
"""

from typing import Optional, Literal
from uuid import UUID
from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.services.token_service import TokenService
from app.core.exceptions import InvalidTokenError
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class AuthContext(BaseModel):
    """
    Authentication context extracted from JWT token.

    Contains user_id and optionally org_id for org-scoped operations.
    """
    user_id: UUID
    org_id: Optional[UUID] = None


class PrincipalContext(BaseModel):
    """
    Principal context supporting both user and service authentication.

    For user tokens:
        - principal_type = "user"
        - user_id = UUID from token sub claim
        - client_id = None
        - scopes = []

    For service tokens (OAuth2 Client Credentials):
        - principal_type = "service"
        - user_id = None
        - client_id = client identifier from token sub claim
        - scopes = list of granted scopes (e.g., ["groups:read", "members:read"])
    """
    principal_type: Literal["user", "service"]
    user_id: Optional[UUID] = None
    client_id: Optional[str] = None
    scopes: list[str] = []
    org_id: Optional[UUID] = None


def extract_bearer_token(authorization: str) -> str:
    """
    Extract Bearer token from Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        JWT token string

    Raises:
        InvalidTokenError: If header format is invalid
    """
    if not authorization:
        logger.warning("auth_missing_authorization_header")
        raise InvalidTokenError("Missing Authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning("auth_invalid_authorization_format",
                      parts_count=len(parts),
                      scheme=parts[0] if parts else None)
        raise InvalidTokenError("Invalid Authorization header format. Expected: 'Bearer <token>'")

    return parts[1]


async def get_current_user_id(
    authorization: str = Header(..., alias="Authorization"),
    token_service: TokenService = Depends(TokenService)
) -> UUID:
    """
    Dependency to extract user_id from JWT access token.

    Use this for endpoints that don't require organization context:
    - GET /organizations (list user's orgs)
    - POST /organizations (create new org)

    Args:
        authorization: Authorization header with Bearer token
        token_service: Token service for decoding

    Returns:
        User ID from token

    Raises:
        InvalidTokenError: If token is invalid or missing

    Example:
        ```python
        @router.get("/organizations")
        async def list_orgs(user_id: UUID = Depends(get_current_user_id)):
            return await org_service.get_user_organizations(user_id)
        ```
    """
    token = extract_bearer_token(authorization)

    logger.debug("auth_extracting_user_id_from_token", token_length=len(token))

    user_id = token_service.get_user_id_from_token(token, "access")

    logger.info("auth_user_authenticated", user_id=str(user_id))

    return user_id


async def get_auth_context(
    authorization: str = Header(..., alias="Authorization"),
    token_service: TokenService = Depends(TokenService)
) -> AuthContext:
    """
    Dependency to extract full authentication context from JWT access token.

    Extracts both user_id and org_id (if present). Use this for org-scoped endpoints:
    - GET /organizations/{org_id}
    - GET /organizations/{org_id}/members
    - POST /organizations/{org_id}/members

    Args:
        authorization: Authorization header with Bearer token
        token_service: Token service for decoding

    Returns:
        AuthContext with user_id and optional org_id

    Raises:
        InvalidTokenError: If token is invalid or missing

    Example:
        ```python
        @router.get("/organizations/{org_id}/members")
        async def get_members(
            org_id: UUID,
            ctx: AuthContext = Depends(get_auth_context)
        ):
            # Verify token's org_id matches path parameter
            if ctx.org_id != org_id:
                raise InsufficientPermissionError()
            return await org_service.get_members(org_id, ctx.user_id)
        ```
    """
    token = extract_bearer_token(authorization)

    logger.debug("auth_extracting_context_from_token", token_length=len(token))

    # Get user_id
    user_id = token_service.get_user_id_from_token(token, "access")

    # Try to extract org_id from token
    try:
        payload = token_service.token_helper.decode_token(token)
        org_id_str = payload.get("org_id")
        org_id = UUID(org_id_str) if org_id_str else None
    except (ValueError, TypeError) as e:
        logger.warning("auth_invalid_org_id_in_token",
                      user_id=str(user_id),
                      error=str(e))
        org_id = None

    logger.info("auth_context_extracted",
               user_id=str(user_id),
               org_id=str(org_id) if org_id else None)

    return AuthContext(user_id=user_id, org_id=org_id)


async def get_org_context(
    authorization: str = Header(..., alias="Authorization"),
    token_service: TokenService = Depends(TokenService)
) -> AuthContext:
    """
    Dependency to extract authentication context WITH REQUIRED org_id.

    Use this for endpoints that MUST have organization context.
    Will raise error if token doesn't contain org_id.

    Args:
        authorization: Authorization header with Bearer token
        token_service: Token service for decoding

    Returns:
        AuthContext with user_id and org_id (guaranteed non-None)

    Raises:
        InvalidTokenError: If token is invalid, missing, or lacks org_id

    Example:
        ```python
        @router.get("/me/current-org")
        async def get_current_org(ctx: AuthContext = Depends(get_org_context)):
            # ctx.org_id is guaranteed to be present
            return await org_service.get_organization(ctx.org_id, ctx.user_id)
        ```
    """
    ctx = await get_auth_context(authorization, token_service)

    if not ctx.org_id:
        logger.warning("auth_missing_org_context", user_id=str(ctx.user_id))
        raise InvalidTokenError(
            "This endpoint requires an organization-scoped token. "
            "Please select an organization first."
        )

    logger.info("auth_org_context_verified",
               user_id=str(ctx.user_id),
               org_id=str(ctx.org_id))

    return ctx


async def get_current_principal(
    authorization: str = Header(..., alias="Authorization"),
    token_service: TokenService = Depends(TokenService)
) -> PrincipalContext:
    """
    Dependency to extract principal context supporting BOTH user and service tokens.

    This dependency enables OAuth2 service-to-service authentication while maintaining
    backward compatibility with user session tokens.

    **User Token Flow**:
    1. User logs in → gets access token with user_id in sub claim
    2. Token sub can be parsed as UUID → recognized as user token
    3. Returns PrincipalContext with principal_type="user" and user_id set

    **Service Token Flow** (OAuth2 Client Credentials):
    1. Service authenticates → gets access token with client_id in sub claim
    2. Token sub CANNOT be parsed as UUID → recognized as service token
    3. Returns PrincipalContext with principal_type="service" and client_id set
    4. Scopes extracted from token for authorization checks

    Args:
        authorization: Authorization header with Bearer token
        token_service: Token service for decoding

    Returns:
        PrincipalContext with principal_type, user_id/client_id, and scopes

    Raises:
        InvalidTokenError: If token is invalid or missing
        HTTPException 403: If token is valid but lacks required scope

    Example (User Token):
        ```python
        @router.get("/groups/{group_id}/members")
        async def list_members(
            group_id: UUID,
            principal: PrincipalContext = Depends(get_current_principal)
        ):
            if principal.principal_type == "user":
                # User must be org member
                return await service.get_members(group_id, principal.user_id)
            else:
                # Service token: check scope
                if "groups:read" not in principal.scopes:
                    raise HTTPException(403, "Insufficient scope")
                return await service.get_members_admin(group_id)
        ```

    Example (Service Token):
        ```python
        # Chat-API calls Auth-API:
        GET /api/auth/groups/{id}/members
        Authorization: Bearer eyJhbGc...  (service token with sub="chat-api-service")

        # This dependency extracts:
        # - principal_type: "service"
        # - client_id: "chat-api-service"
        # - scopes: ["groups:read"]
        # - user_id: None
        ```
    """
    token = extract_bearer_token(authorization)

    logger.debug("auth_extracting_principal_from_token", token_length=len(token))

    # Decode token to get payload
    try:
        payload = token_service.token_helper.decode_token(token)
    except Exception as e:
        logger.warning("auth_invalid_token", error=str(e))
        raise InvalidTokenError("Invalid or expired token")

    sub = payload.get("sub")
    if not sub:
        logger.warning("auth_missing_sub_claim")
        raise InvalidTokenError("Token missing sub claim")

    # Try parsing sub as UUID (user token)
    try:
        user_id = UUID(sub)

        # This is a USER token
        logger.info("auth_user_principal_authenticated",
                   user_id=str(user_id),
                   principal_type="user")

        # Extract org_id if present
        org_id_str = payload.get("org_id")
        org_id = UUID(org_id_str) if org_id_str else None

        return PrincipalContext(
            principal_type="user",
            user_id=user_id,
            client_id=None,
            scopes=[],
            org_id=org_id
        )

    except (ValueError, TypeError):
        # sub is NOT a UUID, this is a SERVICE token
        client_id = sub
        scope_str = payload.get("scope", "")
        scopes = scope_str.split() if scope_str else []

        logger.info("auth_service_principal_authenticated",
                   client_id=client_id,
                   scopes=scopes,
                   principal_type="service")

        return PrincipalContext(
            principal_type="service",
            user_id=None,
            client_id=client_id,
            scopes=scopes,
            org_id=None
        )
