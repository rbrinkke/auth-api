from fastapi import APIRouter, Depends
from app.schemas.auth import RefreshTokenRequest
from app.services.auth_service import AuthService

router = APIRouter()

@router.post("/logout", status_code=200)
async def logout(
    token_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(AuthService)
):
    return await auth_service.logout_user(token_data.refresh_token)
