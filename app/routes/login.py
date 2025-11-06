from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.auth import TokenResponse, TwoFactorLoginRequest
from app.services.auth_service import AuthService

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(AuthService)
):
    return await auth_service.login_user(form_data.username, form_data.password)

@router.post("/login/2fa", response_model=TokenResponse)
async def login_2fa(
    request: TwoFactorLoginRequest,
    auth_service: AuthService = Depends(AuthService)
):
    return await auth_service.login_2fa_challenge(request)
