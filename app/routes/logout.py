"""
User logout endpoint.

Uses Dependency Injection pattern:
- TokenService handles all business logic
- Route only handles HTTP concerns
- Blacklists the refresh token to prevent further use.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import LogoutRequest, LogoutResponse
from app.services.token_service import TokenService, get_token_service, TokenServiceError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout and revoke refresh token",
    description="""
    Logout by blacklisting the refresh token.

    After logout, the refresh token can no longer be used to obtain
    new access tokens. The user must login again.

    **Note:** Access tokens remain valid until they expire (15 min).
    For immediate revocation, implement a token blacklist check
    in your API gateway or activity service.
    """
)
async def logout(
    request: LogoutRequest,
    token_service: TokenService = Depends(get_token_service)
):
    """
    Logout user by blacklisting refresh token.

    Uses Dependency Injection pattern:
    - TokenService handles all business logic
    - Route only handles HTTP concerns
    """
    try:
        # Logout via service
        await token_service.logout(request.refresh_token)

        return LogoutResponse(
            message="Logged out successfully"
        )

    except TokenServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed. Please try again."
        )
