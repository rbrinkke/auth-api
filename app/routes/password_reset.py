# /mnt/d/activity/auth-api/app/routes/password_reset.py
from fastapi import APIRouter, Depends, status
from app.schemas.auth import PasswordResetRequest, PasswordResetConfirm
from app.services.password_reset_service import PasswordResetService

router = APIRouter()

@router.post("/password-reset/request", status_code=status.HTTP_200_OK)
async def request_password_reset(
    request: PasswordResetRequest,
    reset_service: PasswordResetService = Depends(PasswordResetService)
):
    """
    Initiates a password reset request.
    Always returns 200 OK to prevent user enumeration.
    """
    return await reset_service.request_password_reset(request)

@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    request: PasswordResetConfirm,
    reset_service: PasswordResetService = Depends(PasswordResetService)
):
    """
    Confirms a password reset using the token and new password.
    Raises 401/400 for invalid/expired tokens or invalid passwords.
    """
    return await reset_service.confirm_password_reset(request)
