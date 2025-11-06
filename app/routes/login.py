from fastapi import APIRouter, Depends, Request, status
from app.schemas.auth import TokenResponse, TwoFactorLoginRequest, MessageResponse, LoginRequest, LoginCodeSentResponse
from app.services.auth_service import AuthService
from app.core.rate_limiting import get_limiter, get_login_rate_limit

router = APIRouter()
limiter = get_limiter()

@router.post("/login")
@limiter.limit(lambda: get_login_rate_limit())
async def login(
    request: Request,
    login_request: LoginRequest,
    auth_service: AuthService = Depends(AuthService)
) -> TokenResponse | LoginCodeSentResponse:
    return await auth_service.login_user(login_request.username, login_request.password, login_request.code)

@router.post("/login/2fa", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login_2fa(
    request: Request,
    twofa_request: TwoFactorLoginRequest,
    auth_service: AuthService = Depends(AuthService)
):
    return await auth_service.login_2fa_challenge(twofa_request)
