"""
Password reset endpoints.

Uses Service Layer pattern for business logic.
- Route handles HTTP
- PasswordResetService handles business logic
- PasswordValidationService handles password validation

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
from app.schemas.auth import (
    RequestPasswordResetRequest,
    RequestPasswordResetResponse,
    ResetPasswordRequest,
    ResetPasswordResponse
)
from app.services.email_service import get_email_service, EmailService
from app.services.password_validation_service import get_password_validation_service, PasswordValidationService
from app.services.password_reset_service import PasswordResetService, PasswordResetServiceError
from app.services.two_factor_service import TwoFactorService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/request-password-reset",
    response_model=RequestPasswordResetResponse,
    summary="Request password reset",
    description="""
    Request a password reset code to be sent via email.

    **Security:** Always returns success message even if email doesn't exist
    to prevent email enumeration attacks.

    The reset code is valid for 5 minutes.

    **Rate limit:** 1 request per 5 minutes per IP
    """
)
@limiter.limit(f"{settings.rate_limit_password_reset_per_5min}/5minutes")
async def request_password_reset(
    request: Request,
    data: RequestPasswordResetRequest,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db_connection),
    redis: RedisClient = Depends(get_redis),
    email_svc: EmailService = Depends(get_email_service),
    password_validation_svc: PasswordValidationService = Depends(get_password_validation_service)
):
    """
    Request password reset code.

    Uses Service Layer pattern:
    - PasswordResetService handles business logic

    Flow:
    1. Initialize PasswordResetService
    2. Call service to check if user exists
    3. Generate 6-digit reset code if user exists
    4. Send code via email
    5. Return generic message
    """
    try:
        # Generic response (for security - don't reveal if email exists)
        generic_message = "If an account exists for this email, a password reset code has been sent."

        # Initialize service
        reset_service = PasswordResetService(
            conn=conn,
            redis=redis,
            password_validation_svc=password_validation_svc
        )

        # Check if user exists
        user_id = await reset_service.check_user_exists(data.email)

        # If user exists, generate and send reset code
        if user_id:
            # Generate 6-digit reset code using TwoFactorService
            twofa_svc = TwoFactorService(redis, email_svc)
            reset_code = await twofa_svc.create_temp_code(
                user_id=user_id,
                purpose="reset",
                email=data.email
            )
            logger.info(f"Password reset code generated for: {data.email}")

        return RequestPasswordResetResponse(
            message=generic_message,
            user_id=user_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting password reset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset request. Please try again later."
        )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    summary="Reset password",
    description="""
    Reset password using the 6-digit code from the reset email.

    The code is single-use and expires after 5 minutes.

    Uses Service Layer pattern for business logic.
    """
)
async def reset_password(
    request: ResetPasswordRequest,
    conn: asyncpg.Connection = Depends(get_db_connection),
    redis_client: RedisClient = Depends(get_redis),
    password_validation_svc: PasswordValidationService = Depends(get_password_validation_service),
    email_svc: EmailService = Depends(get_email_service)
):
    """
    Reset user password with 6-digit code.

    Uses Service Layer pattern:
    - PasswordResetService handles business logic
    - PasswordValidationService validates new password
    - TwoFactorService verifies the code

    Flow:
    1. Verify code using TwoFactorService
    2. Initialize PasswordResetService
    3. Call service to reset password
    4. Return success message
    """
    try:
        # Initialize services
        twofa_svc = TwoFactorService(redis_client, email_svc)
        reset_service = PasswordResetService(
            conn=conn,
            redis=redis_client,
            password_validation_svc=password_validation_svc
        )

        # Step 1: Verify the code
        is_valid = await twofa_svc.verify_temp_code(
            user_id=request.user_id,
            code=request.code,
            purpose="reset",
            consume=True
        )

        if not is_valid:
            # Increment failed attempts
            await twofa_svc.increment_failed_attempt(request.user_id, "reset")

            # Check if locked out
            if await twofa_svc.is_locked_out(request.user_id, "reset"):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed attempts. Please try again later."
                )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset code"
            )

        # Step 2: Reset failed attempts on success
        await twofa_svc.reset_failed_attempts(request.user_id, "reset")

        # Step 3: Reset password using the service
        result = await reset_service.reset_password_with_user_id(
            user_id=request.user_id,
            new_password=request.new_password
        )

        logger.info(f"Password reset successfully for user {request.user_id}")

        return ResetPasswordResponse(
            message="Password updated successfully. You can now login with your new password."
        )

    except PasswordResetServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed. Please try again later."
        )
