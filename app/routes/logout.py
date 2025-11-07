from fastapi import APIRouter, Depends
from app.schemas.auth import RefreshTokenRequest
from app.services.auth_service import AuthService
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/logout", status_code=200)
async def logout(
    token_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(AuthService)
):
    logger.debug("route_logout_endpoint_hit")
    result = await auth_service.logout_user(token_data.refresh_token)
    logger.debug("route_logout_service_complete")
    return result
