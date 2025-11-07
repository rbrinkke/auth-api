from fastapi import APIRouter, Depends, Request
from app.schemas.auth import VerifyEmailRequest
from app.services.registration_service import RegistrationService
from app.core.rate_limiting import get_limiter, get_verify_code_rate_limit
from app.core.logging_config import get_logger

router = APIRouter()
limiter = get_limiter()
logger = get_logger(__name__)

@router.post("/verify-code", status_code=200)
@limiter.limit(lambda: get_verify_code_rate_limit())
async def verify_code(
    request: Request,
    verify_request: VerifyEmailRequest,
    reg_service: RegistrationService = Depends(RegistrationService)
):
    logger.debug("route_verify_endpoint_hit", token_length=len(verify_request.verification_token))
    result = await reg_service.verify_account_by_code(verify_request.verification_token, verify_request.code)
    logger.debug("route_verify_service_complete")
    return result

