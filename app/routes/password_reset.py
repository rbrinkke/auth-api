from fastapi import APIRouter, Depends, Request, status
from app.schemas.auth import RequestPasswordResetRequest, ResetPasswordRequest
from app.services.password_reset_service import PasswordResetService
from app.core.rate_limiting import get_limiter, get_password_reset_rate_limit
from app.core.logging_config import get_logger

router = APIRouter()
limiter = get_limiter()
logger = get_logger(__name__)

@router.post("/request-password-reset", status_code=status.HTTP_200_OK)
@limiter.limit(lambda: get_password_reset_rate_limit())
async def request_password_reset(
    request: Request,
    reset_request: RequestPasswordResetRequest,
    reset_service: PasswordResetService = Depends(PasswordResetService)
):
    logger.debug("route_password_reset_request_endpoint_hit", email=reset_request.email)
    result = await reset_service.request_password_reset(reset_request)
    logger.debug("route_password_reset_request_service_complete")
    return result

@router.post("/reset-password", status_code=status.HTTP_200_OK)
@limiter.limit(lambda: get_password_reset_rate_limit())
async def confirm_password_reset(
    request: Request,
    reset_request: ResetPasswordRequest,
    reset_service: PasswordResetService = Depends(PasswordResetService)
):
    logger.debug("route_password_reset_confirm_endpoint_hit", reset_token=reset_request.reset_token)
    result = await reset_service.confirm_password_reset(reset_request)
    logger.debug("route_password_reset_confirm_service_complete")
    return result
