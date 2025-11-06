from fastapi import APIRouter, Depends
from app.schemas.auth import VerificationTokenRequest
from app.services.registration_service import RegistrationService

router = APIRouter()

@router.post("/verify-account", status_code=200)
async def verify_account(
    request: VerificationTokenRequest,
    reg_service: RegistrationService = Depends(RegistrationService)
):
    return await reg_service.verify_account(request.token)

