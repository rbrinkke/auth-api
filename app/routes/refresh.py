# /mnt/d/activity/auth-api/app/routes/refresh.py
from fastapi import APIRouter, Depends
from app.schemas.auth import RefreshTokenRequest, TokenResponse
from app.services.token_service import TokenService

router = APIRouter()

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    token_service: TokenService = Depends(TokenService)
):
    """
    Refreshes an access token using a valid refresh token.
    Raises 401 if the refresh token is invalid, expired, or revoked.
    """
    return await token_service.refresh_access_token(request.refresh_token)
