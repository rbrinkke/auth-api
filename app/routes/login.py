from typing import Union
from fastapi import APIRouter, Depends, Request, status
from app.schemas.auth import (
    TokenResponse,
    TwoFactorLoginRequest,
    MessageResponse,
    LoginRequest,
    LoginCodeSentResponse,
    OrganizationSelectionResponse
)
from app.services.auth_service import AuthService
from app.core.rate_limiting import get_limiter, get_login_rate_limit
from app.core.logging_config import get_logger

router = APIRouter()
limiter = get_limiter()
logger = get_logger(__name__)

@router.post("/login")
@limiter.limit(lambda: get_login_rate_limit())
async def login(
    request: Request,
    login_request: LoginRequest,
    auth_service: AuthService = Depends(AuthService)
) -> Union[TokenResponse, LoginCodeSentResponse, OrganizationSelectionResponse]:
    """
    Login endpoint with organization support.

    Flow:
    1. If no code → sends 2FA verification code to email
    2. If code + single org → auto-select org, returns tokens
    3. If code + multiple orgs (no org_id) → returns org list
    4. If code + org_id → returns org-scoped tokens

    Returns:
    - LoginCodeSentResponse: If verification code sent
    - OrganizationSelectionResponse: If user needs to select org
    - TokenResponse: If login successful with tokens
    """
    logger.debug("route_login_endpoint_hit",
                username=login_request.username,
                has_code=login_request.code is not None,
                has_org_id=login_request.org_id is not None)

    result = await auth_service.login_user(
        login_request.username,
        login_request.password,
        login_request.code,
        login_request.org_id
    )

    logger.debug("route_login_service_complete",
                username=login_request.username,
                result_type=type(result).__name__)

    return result

@router.post("/login/2fa", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login_2fa(
    request: Request,
    twofa_request: TwoFactorLoginRequest,
    auth_service: AuthService = Depends(AuthService)
):
    logger.debug("route_login_2fa_endpoint_hit", token_length=len(twofa_request.pre_auth_token), code_length=len(twofa_request.code))
    result = await auth_service.login_2fa_challenge(twofa_request)
    logger.debug("route_login_2fa_service_complete", pre_auth_token_present=bool(twofa_request.pre_auth_token))
    return result
