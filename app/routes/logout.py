# app/routes/logout.py
"""User logout endpoint."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import LogoutRequest, LogoutResponse
from app.services.token_service import TokenService, get_token_service, TokenServiceError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout and revoke refresh token",
    description="Blacklist refresh token. Access tokens remain valid until expiry."
)
async def logout(
    request: LogoutRequest,
    token_service: TokenService = Depends(get_token_service)
):
    """
    Logout user by blacklisting refresh token.
    
    Note: Access tokens remain valid until natural expiry (15 min).
    For immediate revocation, implement token validation in your API gateway.
    """
    try:
        await token_service.logout(request.refresh_token)
        
        return LogoutResponse(message="Logged out successfully")
        
    except TokenServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed. Please try again."
        )
