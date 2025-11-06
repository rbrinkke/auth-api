"""
Password reset endpoints.

Uses Dependency Injection pattern for clean architecture:
- Routes handle HTTP concerns only
- Services are injected via FastAPI's Depends
- All business logic is in services

PasswordResetService handles password reset business logic.
PasswordValidationService handles password validation.
"""
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.schemas.auth import (
    RequestPasswordResetRequest,
    RequestPasswordResetResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    VerifyTempCodeRequest,
    VerifyTempCodeResponse
)
from app.services.password_reset_service import PasswordResetService, get_password_reset_service, PasswordResetServiceError
from app.services.two_factor_service import TwoFactorService, get_two_factor_service

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
    reset_service: PasswordResetService = Depends(get_password_reset_service),
    twofa_svc: TwoFactorService = Depends(get_two_factor_service)
):
    """
    Request password reset code.

    Uses Dependency Injection pattern:
    - PasswordResetService handles business logic
    - Route only handles HTTP concerns

    Flow:
    1. Call service to check if user exists
    2. Generate 6-digit reset code if user exists
    3. Return generic message
    """
    try:
        # Generic response (for security - don't reveal if email exists)
        generic_message = "If an account exists for this email, a password reset code has been sent."

        # Check if user exists
        user_id = await reset_service.check_user_exists(data.email)

        # If user exists, generate and send reset code
        if user_id:
            # Generate 6-digit reset code using TwoFactorService
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
    twofa_svc: TwoFactorService = Depends(get_two_factor_service),
    reset_service: PasswordResetService = Depends(get_password_reset_service)
):
    """
    Reset user password with 6-digit code.

    Uses Dependency Injection pattern:
    - PasswordResetService handles business logic
    - TwoFactorService verifies the code
    - Route only handles HTTP concerns

    Flow:
    1. Verify code using TwoFactorService
    2. Reset password using PasswordResetService
    3. Return success message
    """
    try:
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


@router.post(
    "/verify-temp-code",
    response_model=VerifyTempCodeResponse,
    summary="Verify temporary code",
    description="""
    Verify a temporary code (email verification, password reset, etc.).

    This is a generic endpoint that verifies codes without modifying the database.
    It can be used for both email verification and password reset flows.

    The purpose parameter determines which code to verify ('verify', 'reset', etc.).
    """
)
async def verify_temp_code(
    data: VerifyTempCodeRequest,
    twofa_svc: TwoFactorService = Depends(get_two_factor_service)
):
    """
    Verify temporary code without database modification.

    Uses Dependency Injection pattern:
    - TwoFactorService handles all 2FA logic
    - Route only handles HTTP concerns

    This is a pure verification function that:
    1. Verifies the code using TwoFactorService
    2. Tracks failed attempts
    3. Returns verification status
    4. Does NOT modify the database

    Can be used for email verification, password reset, etc.
    """
    try:
        # Verify the code (consume=False means don't consume yet)
        is_valid = await twofa_svc.verify_temp_code(
            user_id=data.user_id,
            code=data.code,
            purpose=data.purpose,
            consume=False
        )

        if not is_valid:
            # Increment failed attempts
            await twofa_svc.increment_failed_attempt(data.user_id, data.purpose)

            # Check if locked out
            if await twofa_svc.is_locked_out(data.user_id, data.purpose):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed attempts. Please try again later."
                )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired code"
            )

        # Reset failed attempts on success
        await twofa_svc.reset_failed_attempts(data.user_id, data.purpose)

        return VerifyTempCodeResponse(
            message="Code verified successfully",
            verified=True
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying temp code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify code. Please try again later."
        )
