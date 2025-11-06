from fastapi import APIRouter, Depends
from app.schemas.auth import VerifyEmailRequest
from app.services.registration_service import RegistrationService

router = APIRouter()

@router.post("/verify-code", status_code=200)
async def verify_code(
    request: VerifyEmailRequest,
    reg_service: RegistrationService = Depends(RegistrationService)
):
    return await reg_service.verify_account_by_code(request.verification_token, request.code)

