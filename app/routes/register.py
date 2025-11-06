from fastapi import APIRouter, Depends, Request, status
from app.schemas.user import UserCreate
from app.services.registration_service import RegistrationService
from app.core.rate_limiting import get_limiter, get_register_rate_limit

router = APIRouter()
limiter = get_limiter()

@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit(lambda: get_register_rate_limit())
async def register_user(
    request: Request,
    user: UserCreate,
    reg_service: RegistrationService = Depends(RegistrationService)
):
    return await reg_service.register_user(user)
