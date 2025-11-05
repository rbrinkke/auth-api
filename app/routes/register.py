"""
User registration endpoint.

Uses Service Layer pattern for business logic.
- Route handles HTTP
- RegistrationService handles business logic
- Email service for sending emails

This separation makes code testable and maintainable.
"""
import logging

import asyncpg
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.core.redis_client import RedisClient, get_redis
from app.db.connection import get_db_connection
from app.schemas.auth import RegisterRequest, RegisterResponse
from app.services.email_service import get_email_service, EmailService
from app.services.password_validation_service import get_password_validation_service, PasswordValidationService
from app.services.registration_service import (
    RegistrationService,
    UserAlreadyExistsError,
    RegistrationServiceError
)
from app.services.two_factor_service import TwoFactorService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="""
    Register a new user account.

    **Important:** Users must verify their email before they can login.
    A verification email will be sent to the provided address.

    **Rate limit:** 3 requests per hour per IP
    """
)
@limiter.limit(f"{settings.rate_limit_register_per_hour}/hour")
async def register(
    request: Request,
    data: RegisterRequest,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db_connection),
    redis: RedisClient = Depends(get_redis),
    email_svc: EmailService = Depends(get_email_service),
    password_validation_svc: PasswordValidationService = Depends(get_password_validation_service)
):
    """
    Register a new user with email verification.

    Uses Service Layer pattern:
    - Pydantic (data/schema validation only)
    - RegistrationService (business logic)
    - BackgroundTasks (sending emails asynchronously)

    Flow:
    1. Initialize RegistrationService with dependencies
    2. Call service to handle business logic (user creation)
    3. Generate 6-digit verification code
    4. Send code via email (non-blocking)
    5. Return immediate response
    """
    try:
        # Initialize service with dependencies (Service Layer pattern)
        registration_service = RegistrationService(
            conn=conn,
            redis=redis,
            password_validation_svc=password_validation_svc
        )

        # Execute business logic via service
        result = await registration_service.register_user(
            email=data.email,
            password=data.password
        )

        # Generate 6-digit verification code using TwoFactorService
        twofa_svc = TwoFactorService(redis, email_svc)
        verification_code = await twofa_svc.create_temp_code(
            user_id=result.user.id,
            purpose="verify",
            email=result.user.email
        )

        logger.info(f"Verification code generated for user: {result.user.email}")

        return RegisterResponse(
            message=f"User registered successfully. A 6-digit verification code has been sent to {result.user.email}.",
            email=result.user.email,
            user_id=str(result.user.id)
        )

    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RegistrationServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again later."
        )
