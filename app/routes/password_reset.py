from fastapi import APIRouter, Depends, Request, status
from app.schemas.auth import RequestPasswordResetRequest, ResetPasswordRequest
from app.services.password_reset_service import PasswordResetService
from app.core.rate_limiting import get_limiter, get_password_reset_rate_limit

router = APIRouter()
limiter = get_limiter()

@router.post("/request-password-reset", status_code=status.HTTP_200_OK)
@limiter.limit(lambda: get_password_reset_rate_limit())
async def request_password_reset(
    http_request: Request,
    reset_request: RequestPasswordResetRequest,
    reset_service: PasswordResetService = Depends(PasswordResetService)
):
    return await reset_service.request_password_reset(reset_request)

@router.post("/reset-password", status_code=status.HTTP_200_OK)
@limiter.limit(lambda: get_password_reset_rate_limit())
async def confirm_password_reset(
    http_request: Request,
    reset_request: ResetPasswordRequest,
    reset_service: PasswordResetService = Depends(PasswordResetService)
):
    return await reset_service.confirm_password_reset(reset_request)
