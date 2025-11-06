# app/routes/register.py
"""User registration endpoint."""
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.schemas.auth import RegisterRequest, RegisterResponse
from app.services.registration_service import RegistrationService, get_registration_service
from app.services.two_factor_service import TwoFactorService, get_two_factor_service

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register a new user account. Email verification required before login."
)
@limiter.limit(f"{settings.rate_limit_register_per_hour}/hour")
async def register(
    request: Request,
    data: RegisterRequest,
    registration_service: RegistrationService = Depends(get_registration_service),
    twofa_service: TwoFactorService = Depends(get_two_factor_service)
):
    """
    Register new user with email verification code.
    
    Flow:
    1. Validate and create user (service handles password validation)
    2. Generate 6-digit verification code
    3. Send code via email (async)
    4. Return success response
    """
    try:
        # Create user
        result = await registration_service.register_user(
            email=data.email,
            password=data.password
        )
        
        # Generate and send verification code
        await twofa_service.create_temp_code(
            user_id=result.user.id,
            purpose="verify",
            email=result.user.email
        )
        
        logger.info(f"User registered: {result.user.email}")
        
        return RegisterResponse(
            message=f"Registration successful. Verification code sent to {result.user.email}.",
            email=result.user.email,
            user_id=result.user.id
        )
        
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise
