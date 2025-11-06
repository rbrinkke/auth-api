# /mnt/d/activity/auth-api/app/routes/login.py
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
    """
    Handles user login.
    Raises 401 for bad credentials, 403 if unverified.
    Raises 402 (custom) if 2FA is required, returning a pre-auth token.
    """
    return await auth_service.login_user(form_data.username, form_data.password)

@router.post("/login/2fa", response_model=TokenResponse)
async def login_2fa(
    request: TwoFactorLoginRequest,
    auth_service: AuthService = Depends(AuthService)
):
    """
    Handles the 2FA challenge step of login.
    Requires the pre_auth_token from the /login endpoint and the 2FA code.
    """
    return await auth_service.login_2fa_challenge(request)
