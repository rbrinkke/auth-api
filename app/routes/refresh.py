"""
Token refresh endpoint with rotation.

Uses Dependency Injection pattern:
- TokenService handles all business logic
- Route only handles HTTP concerns
- Implements refresh token rotation: old token is blacklisted when new tokens are issued

This is a MANDATORY security feature for production.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import RefreshTokenRequest, TokenResponse
from app.services.token_service import TokenService, get_token_service, TokenServiceError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="""
    Exchange a refresh token for new access and refresh tokens.

    **Security - Token Rotation:**
    The old refresh token is immediately blacklisted after use.
    This prevents replay attacks if a token is stolen.

    **Requirements:**
    - Valid, non-blacklisted refresh token
    - User must still be active and verified
    """
)
async def refresh_tokens(
    request: RefreshTokenRequest,
    token_service: TokenService = Depends(get_token_service)
):
    """
    Refresh tokens with automatic rotation.

    Uses Dependency Injection pattern:
    - TokenService handles all business logic
    - Route only handles HTTP concerns
    """
    try:
        # Refresh tokens via service
        result = await token_service.refresh_tokens(request.refresh_token)

        return TokenResponse(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            token_type="bearer"
        )

    except TokenServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during token refresh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed. Please login again."
        )
