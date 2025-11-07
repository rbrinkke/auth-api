from fastapi import APIRouter, Depends, status, Header
from uuid import UUID
from app.services.two_factor_service import TwoFactorService
from app.services.token_service import TokenService
from app.schemas.auth import TwoFactorVerifyRequest
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

async def get_current_user_id(
    authorization: str = Header(),
    token_service: TokenService = Depends(TokenService)
) -> UUID:
    token = authorization.split(" ")[1]
    user_id = token_service.get_user_id_from_token(token, "access")
    return user_id


@router.post("/setup", status_code=status.HTTP_200_OK)
async def setup_2fa(
    user_id: UUID = Depends(get_current_user_id),
    two_factor_service: TwoFactorService = Depends(TwoFactorService)
):
    logger.debug("route_2fa_setup_endpoint_hit", user_id=str(user_id))
    result = await two_factor_service.setup_2fa(user_id)
    logger.debug("route_2fa_setup_service_complete", user_id=str(user_id))
    return result


@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_2fa_setup(
    request: TwoFactorVerifyRequest,
    user_id: UUID = Depends(get_current_user_id),
    two_factor_service: TwoFactorService = Depends(TwoFactorService)
):
    logger.debug("route_2fa_verify_endpoint_hit", user_id=str(user_id))
    result = await two_factor_service.verify_and_enable_2fa(user_id, request.code)
    logger.debug("route_2fa_verify_service_complete", user_id=str(user_id))
    return result


@router.post("/disable", status_code=status.HTTP_200_OK)
async def disable_2fa(
    user_id: UUID = Depends(get_current_user_id),
    two_factor_service: TwoFactorService = Depends(TwoFactorService)
):
    logger.debug("route_2fa_disable_endpoint_hit", user_id=str(user_id))
    result = await two_factor_service.disable_2fa(user_id)
    logger.debug("route_2fa_disable_service_complete", user_id=str(user_id))
    return result
