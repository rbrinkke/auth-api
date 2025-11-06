# /mnt/d/activity/auth-api/app/routes/verify.py
from fastapi import APIRouter, Depends
from app.schemas.auth import VerificationTokenRequest
from app.services.registration_service import RegistrationService

router = APIRouter()

@router.post("/verify-account", status_code=200)
async def verify_account(
    request: VerificationTokenRequest,
    reg_service: RegistrationService = Depends(RegistrationService)
):
    """
    Verifies a user's account using the token from their email.
    Raises 401 if the token is invalid or expired.
    """
    return await reg_service.verify_account(request.token)

