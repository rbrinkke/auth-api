"""
Authorization API - Image-API Compatible Endpoint

Wrapper endpoint that provides image-api compatible authorization checking.
Maps image-api's expected format to auth-api's existing authorization service.

Key Endpoint:
- POST /api/v1/authorization/check: Image-API compatible authorization

This wraps the existing POST /api/auth/authorize endpoint.
"""

import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import asyncpg
import redis

from app.db.connection import get_db_connection
from app.core.redis_client import get_redis_client
from app.services.authorization_service import AuthorizationService
from app.models.group import AuthorizationRequest

router = APIRouter()
logger = logging.getLogger(__name__)

# ============================================================================
# Data Models (Image-API Compatible Format)
# ============================================================================

class ImageAPIAuthorizationRequest(BaseModel):
    """Authorization request in image-api format."""
    org_id: str # Organization UUID string
    user_id: str # User UUID string
    permission: str # Permission string (e.g., "image:upload")


class ImageAPIAuthorizationResponse(BaseModel):
    """Authorization response in image-api format."""
    allowed: bool
    groups: list[str] | None = None
    reason: str | None = None


# ============================================================================
# IMAGE-API COMPATIBLE ENDPOINT
# ============================================================================

@router.post(
    "/check",
    response_model=ImageAPIAuthorizationResponse,
    summary="Authorization Check (Image-API Compatible)",
    description="Check if user has permission using strict UUIDs and centralized RBAC logic."
)
async def check_authorization(
    request: ImageAPIAuthorizationRequest,
    db: asyncpg.Connection = Depends(get_db_connection),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    Check if user has permission in organization (Image-API compatible format).

    Production behavior:
    1. Validates that org_id and user_id are valid UUIDs.
    2. Checks Redis cache / Database via AuthorizationService.
    3. Returns 200 OK with {"allowed": true/false} (no 403 exceptions for logic denials).
    """
    try:
        # 1. Strict UUID Validation
        try:
            user_uuid = UUID(request.user_id)
            org_uuid = UUID(request.org_id)
        except ValueError:
            logger.warning(
                "Invalid UUID format received",
                extra={"user_id": request.user_id, "org_id": request.org_id}
            )
            return ImageAPIAuthorizationResponse(
                allowed=False,
                reason="Invalid ID format: UUID required"
            )

        # 2. Create internal authorization request
        auth_request = AuthorizationRequest(
            user_id=user_uuid,
            organization_id=org_uuid,
            permission=request.permission
        )

        # 3. Call Authorization Service (Handles Cache & DB)
        service = AuthorizationService(db, redis_client)
        result = await service.authorize(auth_request)

        # 4. Return Response (Always 200 OK)
        return ImageAPIAuthorizationResponse(
            allowed=result.authorized,
            groups=result.matched_groups,
            reason=result.reason
        )

    except Exception as e:
        logger.error(
            f"Authorization check failed: {e}",
            extra={
                "org_id": request.org_id,
                "user_id": request.user_id,
                "permission": request.permission,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authorization service error"
        )
