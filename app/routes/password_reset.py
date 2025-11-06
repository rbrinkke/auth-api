from fastapi import APIRouter, Depends, status
from app.schemas.auth import RequestPasswordResetRequest, ResetPasswordRequest
from app.services.password_reset_service import PasswordResetService

router = APIRouter()

@router.post("/request-password-reset", status_code=status.HTTP_200_OK)
async def request_password_reset(
    request: RequestPasswordResetRequest,
    reset_service: PasswordResetService = Depends(PasswordResetService)
):
    return await reset_service.request_password_reset(request)

@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    request: ResetPasswordRequest,
    reset_service: PasswordResetService = Depends(PasswordResetService)
):
    return await reset_service.confirm_password_reset(request)
