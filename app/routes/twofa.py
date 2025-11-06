from fastapi import APIRouter, Depends, status, Header
from app.services.two_factor_service import TwoFactorService
from app.services.token_service import TokenService
from app.schemas.auth import TwoFactorVerifyRequest

router = APIRouter()

async def get_current_user_id(
    authorization: str = Header(),
    token_service: TokenService = Depends(TokenService)
) -> int:
    token = authorization.split(" ")[1]
    user_id = token_service.get_user_id_from_token(token, "access")
    return user_id


@router.post("/setup", status_code=status.HTTP_200_OK)
async def setup_2fa(
    user_id: int = Depends(get_current_user_id),
    two_factor_service: TwoFactorService = Depends(TwoFactorService)
):
    return await two_factor_service.setup_2fa(user_id)


@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_2fa_setup(
    request: TwoFactorVerifyRequest,
    user_id: int = Depends(get_current_user_id),
    two_factor_service: TwoFactorService = Depends(TwoFactorService)
):
    return await two_factor_service.verify_and_enable_2fa(user_id, request.code)


@router.post("/disable", status_code=status.HTTP_200_OK)
async def disable_2fa(
    user_id: int = Depends(get_current_user_id),
    two_factor_service: TwoFactorService = Depends(TwoFactorService)
):
    return await two_factor_service.disable_2fa(user_id)
