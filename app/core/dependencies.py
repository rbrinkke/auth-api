"""
Authentication Dependencies

FastAPI dependencies for extracting and validating authentication context from JWT tokens.

Provides two levels of authentication:
1. User-level: Just user_id (for cross-org operations like listing/creating orgs)
2. Org-level: user_id + org_id (for org-scoped operations)
"""

from typing import Optional
from uuid import UUID
from fastapi import Depends, Header
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
