from fastapi import APIRouter, Depends
from app.schemas.auth import RefreshTokenRequest, TokenResponse
from app.services.token_service import TokenService
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    token_service: TokenService = Depends(TokenService)
):
    logger.debug("route_refresh_endpoint_hit")
    result = await token_service.refresh_access_token(request.refresh_token)
    logger.debug("route_refresh_service_complete")
    return result
