from fastapi import APIRouter, Depends, status
from app.schemas.auth import PasswordResetRequest, PasswordResetConfirm
from app.services.password_reset_service import PasswordResetService

router = APIRouter()

@router.post("/password-reset/request", status_code=status.HTTP_200_OK)
async def request_password_reset(
    request: PasswordResetRequest,
    reset_service: PasswordResetService = Depends(PasswordResetService)
):
    return await reset_service.request_password_reset(request)

@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    request: PasswordResetConfirm,
    reset_service: PasswordResetService = Depends(PasswordResetService)
):
    return await reset_service.confirm_password_reset(request)
