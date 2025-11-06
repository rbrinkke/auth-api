# app/routes/refresh.py
"""Token refresh endpoint with automatic rotation."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import RefreshTokenRequest, TokenResponse
from app.services.token_service import TokenService, get_token_service, TokenServiceError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Exchange refresh token for new tokens. Old token is automatically blacklisted."
)
async def refresh_tokens(
    request: RefreshTokenRequest,
    token_service: TokenService = Depends(get_token_service)
):
    """
    Refresh tokens with automatic rotation.
    
    Security: Old refresh token is immediately blacklisted (mandatory).
    """
    try:
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
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed. Please login again."
        )
