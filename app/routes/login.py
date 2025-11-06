from fastapi import APIRouter, Depends, status
from app.schemas.auth import TokenResponse, TwoFactorLoginRequest, MessageResponse, LoginRequest
from app.services.auth_service import AuthService

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(AuthService)
):
    return await auth_service.login_user(request.username, request.password)

@router.post("/login/2fa", response_model=TokenResponse)
async def login_2fa(
    request: TwoFactorLoginRequest,
    auth_service: AuthService = Depends(AuthService)
):
    return await auth_service.login_2fa_challenge(request)
