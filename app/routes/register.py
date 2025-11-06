# /mnt/d/activity/auth-api/app/routes/register.py
from fastapi import APIRouter, Depends, status
from app.schemas.user import UserCreate
from app.services.registration_service import RegistrationService

router = APIRouter()

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    user: UserCreate,
    reg_service: RegistrationService = Depends(RegistrationService)
):
    """
    Registers a new user.
    Raises 409 if the email already exists.
    Raises 400 if the password is invalid.
    """
    return await reg_service.register_user(user)
