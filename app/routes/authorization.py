"""
Authorization API - Generic RBAC Endpoint

Provides RBAC-compliant authorization checking for all microservices.
Supports both detailed checks (with groups array) and ultrathin group-specific checks.

Key Endpoints:
- POST /api/v1/authorization/check: Detailed authorization (returns groups array)
- POST /api/v1/authorization/check-group: Ultrathin group-specific check (simple boolean)
"""

import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from pydantic import BaseModel
import asyncpg
import redis

from app.db.connection import get_db_connection
from app.core.redis_client import get_redis_client
from app.services.authorization_service import AuthorizationService
from app.models.group import AuthorizationRequest
from app.core.oauth_resource_server import get_current_principal
from app.config import get_settings
from app.core.rate_limiting import get_limiter

router = APIRouter()
logger = logging.getLogger(__name__)
limiter = get_limiter()

# ============================================================================
# Data Models (Generic RBAC Format)
# ============================================================================

class RBACAuthorizationRequest(BaseModel):
    """Authorization request for generic RBAC system (detailed check)."""
    org_id: str # Organization UUID string
    user_id: str # User UUID string
    permission: str # Permission string (e.g., "chat:read", "activity:create")
    resource_id: Optional[str] = None # Optional resource UUID (legacy field)


class RBACAuthorizationResponse(BaseModel):
    """Authorization response with detailed information (groups array, reason)."""
    allowed: bool
    groups: list[str] | None = None
    reason: str | None = None


class RBACGroupAuthorizationRequest(BaseModel):
    """Ultrathin group-specific authorization request."""
    org_id: str       # Organization UUID string
    user_id: str      # User UUID string
    group_id: str     # Group UUID string (specific group to check)
    permission: str   # Permission string (e.g., "chat:read")


class RBACGroupAuthorizationResponse(BaseModel):
    """Ultrathin authorization response (boolean only)."""
    allowed: bool     # Simple yes/no answer


# ============================================================================
# SERVICE AUTHENTICATION
# ============================================================================

async def verify_service_authentication(
    x_service_token: Optional[str] = Header(None, alias="X-Service-Token"),
    authorization: Optional[str] = Header(None)
) -> dict:
    """
    Hybrid service authentication supporting both API Key and OAuth.

    Method 1 (Primary): API Key via X-Service-Token header
    - Simple shared secret authentication
    - Fast and efficient for internal microservices

    Method 2 (Optional): OAuth Bearer token
    - Full OAuth2 client credentials flow
    - Requires service token with "authz:check" scope

    Returns:
        dict: Authentication metadata {"method": "api_key" | "oauth", ...}

    Raises:
        HTTPException 401: No authentication provided or invalid credentials
        HTTPException 403: OAuth token lacks required scope
    """
    settings = get_settings()

    # Method 1: API Key (primary for immediate security fix)
    if x_service_token:
        if x_service_token != settings.SERVICE_AUTH_TOKEN:
            logger.warning(
                "authz_invalid_service_token",
                extra={"token_preview": x_service_token[:10] + "..."}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid service token"
            )

        logger.debug("authz_service_authenticated", extra={"method": "api_key"})
        return {"method": "api_key", "authenticated": True}

    # Method 2: OAuth (future-ready, optional)
    if authorization:
        try:
            # Import here to avoid circular dependency
            from fastapi.security import HTTPAuthorizationCredentials

            # Validate OAuth token using existing infrastructure
            principal = await get_current_principal(
                HTTPAuthorizationCredentials(
                    scheme="Bearer",
                    credentials=authorization.replace("Bearer ", "")
                )
            )

            # Verify this is a SERVICE token (not user token)
            if principal["type"] != "service":
                logger.warning(
                    "authz_invalid_principal_type",
                    extra={"expected": "service", "got": principal["type"]}
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Service token required (not user token)"
                )

            # Verify service has required scope
            if "authz:check" not in principal["scopes"]:
                logger.warning(
                    "authz_insufficient_scope",
                    extra={"required": "authz:check", "available": principal["scopes"]}
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient scope: authz:check required"
                )

            logger.debug(
                "authz_service_authenticated",
                extra={"method": "oauth", "client_id": principal["client_id"]}
            )
            return {
                "method": "oauth",
                "principal": principal,
                "authenticated": True
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "authz_oauth_validation_failed",
                extra={"error": str(e)}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="OAuth token validation failed"
            )

    # No authentication provided
    logger.warning("authz_no_authentication")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Service authentication required (X-Service-Token or Bearer token)"
    )


# ============================================================================
# RBAC AUTHORIZATION ENDPOINTS
# ============================================================================

@router.post(
    "/check",
    response_model=RBACAuthorizationResponse,
    summary="Authorization Check (Detailed)",
    description="Check if user has permission with detailed response (groups array, reason). Requires service authentication."
)
@limiter.limit("100/minute")
async def check_authorization(
    request_data: RBACAuthorizationRequest,
    request: Request,
    auth: dict = Depends(verify_service_authentication),
    db: asyncpg.Connection = Depends(get_db_connection),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    Check if user has permission in organization (detailed response with groups array).

    **SECURITY**: This endpoint requires service authentication (X-Service-Token or OAuth Bearer).
    Only authenticated services can call this endpoint.

    Production behavior:
    1. Validates service authentication (API Key or OAuth token with authz:check scope).
    2. Validates that org_id and user_id are valid UUIDs.
    3. Checks Redis cache / Database via AuthorizationService.
    4. Returns 200 OK with detailed response (allowed, groups, reason).
    5. Logs authentication method and request details for audit trail.

    Response Format:
    {
      "allowed": true,
      "groups": ["vrienden", "moderators"],  // Which groups grant the permission
      "reason": "User has permission via group membership"
    }
    """
    try:
        # Log authenticated service request (audit trail)
        logger.info(
            "authz_check_request",
            extra={
                "auth_method": auth["method"],
                "user_id": request_data.user_id,
                "org_id": request_data.org_id,
                "permission": request_data.permission
            }
        )
        # 1. Strict UUID Validation
        try:
            user_uuid = UUID(request_data.user_id)
            org_uuid = UUID(request_data.org_id)
        except ValueError:
            logger.warning(
                "Invalid UUID format received",
                extra={"user_id": request_data.user_id, "org_id": request_data.org_id}
            )
            return RBACAuthorizationResponse(
                allowed=False,
                reason="Invalid ID format: UUID required"
            )

        # 2. Create internal authorization request
        auth_request = AuthorizationRequest(
            user_id=user_uuid,
            organization_id=org_uuid,
            permission=request_data.permission
        )

        # 3. Call Authorization Service (Handles Cache & DB)
        service = AuthorizationService(db, redis_client)
        result = await service.authorize(auth_request)

        # 4. Return Response (Always 200 OK)
        return RBACAuthorizationResponse(
            allowed=result.authorized,
            groups=result.matched_groups,
            reason=result.reason
        )

    except Exception as e:
        logger.error(
            f"Authorization check failed: {e}",
            extra={
                "org_id": request_data.org_id,
                "user_id": request_data.user_id,
                "permission": request_data.permission,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authorization service error"
        )


@router.post(
    "/check-group",
    response_model=RBACGroupAuthorizationResponse,
    summary="Authorization Check in Group (Ultrathin)",
    description="Check if user has permission in specific group. Returns simple boolean for fast microservice checks."
)
@limiter.limit("100/minute")
async def check_authorization_in_group(
    request_data: RBACGroupAuthorizationRequest,
    request: Request,
    auth: dict = Depends(verify_service_authentication),
    db: asyncpg.Connection = Depends(get_db_connection),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    Ultrathin group-specific authorization check.

    **SECURITY**: This endpoint requires service authentication (X-Service-Token or OAuth Bearer).
    Only authenticated services can call this endpoint.

    Perfect for microservices (like chat-api) that need:
    - Fast yes/no answers (no complex response parsing)
    - Group-specific permission checks
    - Minimal latency overhead

    Production behavior:
    1. Validates service authentication
    2. Validates UUIDs (org_id, user_id, group_id)
    3. Checks permission in SPECIFIC group via database
    4. Returns simple {"allowed": true/false}
    5. Fail-closed: returns false on errors

    Response Format:
    {
      "allowed": true  // Simple boolean only - no groups array, no reason
    }

    Example Request:
    {
      "org_id": "99999999-9999-9999-9999-999999999999",
      "user_id": "019a8b88-28cf-71db-a73e-18e49a21fc16",
      "group_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
      "permission": "chat:read"
    }
    """
    try:
        # Log request
        logger.info(
            "authz_group_check_request",
            extra={
                "auth_method": auth["method"],
                "user_id": request_data.user_id,
                "org_id": request_data.org_id,
                "group_id": request_data.group_id,
                "permission": request_data.permission
            }
        )

        # Validate UUIDs
        try:
            user_uuid = UUID(request_data.user_id)
            org_uuid = UUID(request_data.org_id)
            group_uuid = UUID(request_data.group_id)
        except ValueError:
            logger.warning(
                "authz_group_check_invalid_uuid",
                extra={
                    "user_id": request_data.user_id,
                    "org_id": request_data.org_id,
                    "group_id": request_data.group_id
                }
            )
            return RBACGroupAuthorizationResponse(allowed=False)

        # Call ultrathin authorization service
        service = AuthorizationService(db, redis_client)
        allowed = await service.authorize_in_group(
            user_id=user_uuid,
            org_id=org_uuid,
            group_id=group_uuid,
            permission=request_data.permission
        )

        return RBACGroupAuthorizationResponse(allowed=allowed)

    except Exception as e:
        logger.error(
            "authz_group_check_error",
            extra={
                "error": str(e),
                "user_id": request_data.user_id,
                "org_id": request_data.org_id,
                "group_id": request_data.group_id,
                "permission": request_data.permission
            }
        )
        # Fail closed
        return RBACGroupAuthorizationResponse(allowed=False)
