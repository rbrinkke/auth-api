from fastapi import APIRouter, Depends, Request, status
from app.schemas.user import UserCreate
from app.services.registration_service import RegistrationService
from app.core.rate_limiting import get_limiter, get_register_rate_limit
from app.core.logging_config import get_logger

router = APIRouter()
limiter = get_limiter()
logger = get_logger(__name__)

@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit(lambda: get_register_rate_limit())
async def register_user(
    request: Request,
    user: UserCreate,
    reg_service: RegistrationService = Depends(RegistrationService)
):
    logger.debug("route_register_endpoint_hit", email=user.email)
    result = await reg_service.register_user(user)
    logger.debug("route_register_service_complete", email=user.email)
    return result
