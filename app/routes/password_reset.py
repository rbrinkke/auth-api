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

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/request-password-reset",
    response_model=RequestPasswordResetResponse,
    summary="Request password reset",
    description="""
    Request a password reset link to be sent via email.
    
    **Security:** Always returns success message even if email doesn't exist
    to prevent email enumeration attacks.
    
    The reset link is valid for 1 hour.
    
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
    Request password reset email.

    Uses Service Layer pattern:
    - PasswordResetService handles business logic

    Flow:
    1. Initialize PasswordResetService
    2. Call service to request reset
    3. Send email if token generated
    4. Return generic message
    """
    try:
        # Generic response (for security - don't reveal if email exists)
        generic_message = "If an account exists for this email, a password reset link has been sent."

        # Initialize service
        reset_service = PasswordResetService(
            conn=conn,
            redis=redis,
            password_validation_svc=password_validation_svc
        )

        # Request reset (returns token only if user exists)
        reset_token = await reset_service.request_password_reset(data.email)

        # If token returned, send email
        if reset_token:
            # Send reset email in background
            background_tasks.add_task(
                email_svc.send_password_reset_email,
                data.email,
                reset_token
            )
            logger.info(f"Password reset email sent to: {data.email}")

        return RequestPasswordResetResponse(message=generic_message)

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
    Reset password using the token from the reset email.

    The token is single-use and expires after 1 hour.

    Uses Service Layer pattern for business logic.
    """
)
async def reset_password(
    request: ResetPasswordRequest,
    conn: asyncpg.Connection = Depends(get_db_connection),
    redis: RedisClient = Depends(get_redis),
    password_validation_svc: PasswordValidationService = Depends(get_password_validation_service)
):
    """
    Reset user password with token.

    Uses Service Layer pattern:
    - PasswordResetService handles business logic
    - PasswordValidationService validates new password

    Flow:
    1. Initialize PasswordResetService
    2. Call service to reset password
    3. Return success message
    """
    try:
        # Initialize service
        reset_service = PasswordResetService(
            conn=conn,
            redis=redis,
            password_validation_svc=password_validation_svc
        )

        # Execute password reset via service
        result = await reset_service.reset_password(
            reset_token=request.token,
            new_password=request.new_password
        )

        logger.info(f"Password reset successfully for user")

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
