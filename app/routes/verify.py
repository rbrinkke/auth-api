"""
Email verification endpoints.

Handles verification and resending verification emails using 6-digit codes.
"""
import logging

import asyncpg
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.core.redis_client import RedisClient, get_redis
from app.db.connection import get_db_connection
from app.db.procedures import sp_get_user_by_email, sp_verify_user_email
from app.schemas.auth import (
    ResendVerificationRequest,
    ResendVerificationResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
    VerifyCodeRequest,
    VerifyCodeResponse
)
from app.services.email_service import get_email_service, EmailService
from app.services.two_factor_service import TwoFactorService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/verify-code",
    response_model=VerifyCodeResponse,
    summary="Verify email address with code",
    description="""
    Verify a user's email address using the 6-digit code from the verification email.

    After successful verification, the user can login.
    """
)
async def verify_code(
    data: VerifyCodeRequest,
    conn: asyncpg.Connection = Depends(get_db_connection),
    redis_client: RedisClient = Depends(get_redis),
    email_svc: EmailService = Depends(get_email_service)
):
    """
    Verify user email with 6-digit code.

    Flow:
    1. Verify code using TwoFactorService
    2. If valid, mark user as verified in database
    3. Delete code from Redis
    4. Return success message
    """
    print(f"[VERIFY-ROUTE] ====================")
    print(f"[VERIFY-ROUTE] Received verify-code request:")
    print(f"[VERIFY-ROUTE]   user_id: {data.user_id}")
    print(f"[VERIFY-ROUTE]   code: {data.code}")
    print(f"[VERIFY-ROUTE] ====================")

    try:
        # Initialize TwoFactorService
        twofa_svc = TwoFactorService(redis_client, email_svc)

        print(f"[VERIFY-ROUTE] Calling verify_temp_code...")
        # 1. Verify the code
        is_valid = await twofa_svc.verify_temp_code(
            user_id=data.user_id,
            code=data.code,
            purpose="verify",
            consume=True
        )

        print(f"[VERIFY-ROUTE] verify_temp_code returned: {is_valid}")

        if not is_valid:
            print(f"[VERIFY-ROUTE] Code INVALID - incrementing failed attempts")
            # Increment failed attempts
            await twofa_svc.increment_failed_attempt(data.user_id, "verify")

            # Check if locked out
            if await twofa_svc.is_locked_out(data.user_id, "verify"):
                print(f"[VERIFY-ROUTE] User locked out - raising 429")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed attempts. Please try again later."
                )

            print(f"[VERIFY-ROUTE] Invalid code - raising 400")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code"
            )

        # 2. Reset failed attempts on success
        print(f"[VERIFY-ROUTE] Code VALID - resetting failed attempts")
        await twofa_svc.reset_failed_attempts(data.user_id, "verify")

        # 3. Mark user as verified in database
        print(f"[VERIFY-ROUTE] Updating database - calling sp_verify_user_email")
        success = await sp_verify_user_email(conn, data.user_id)

        print(f"[VERIFY-ROUTE] Database update result: {success}")

        if not success:
            print(f"[VERIFY-ROUTE] Database update failed - user not found")
            logger.error(f"Failed to verify user {data.user_id} - user not found")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )

        print(f"[VERIFY-ROUTE] SUCCESS! Returning success response")
        logger.info(f"Email verified successfully for user {data.user_id}")

        return VerifyCodeResponse(
            message="Email verified successfully! You can now login."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during email verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed. Please try again later."
        )


@router.post(
    "/resend-verification",
    response_model=ResendVerificationResponse,
    summary="Resend verification code",
    description="""
    Request a new verification code via email.

    **Security:** Always returns success message even if email doesn't exist
    to prevent email enumeration attacks.

    **Rate limit:** 1 request per 5 minutes per IP
    """
)
@limiter.limit(f"{settings.rate_limit_resend_verification_per_5min}/5minutes")
async def resend_verification(
    request: Request,
    data: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db_connection),
    redis_client: RedisClient = Depends(get_redis),
    email_svc: EmailService = Depends(get_email_service)
):
    """
    Resend verification code to user via email.

    Flow:
    1. Look up user by email
    2. Check if already verified
    3. Generate and send new verification code
    4. Return generic success message
    """
    try:
        # Generic response message (for security)
        generic_message = "If an unverified account exists for this email, a verification code has been sent."

        # 1. Find user
        user = await sp_get_user_by_email(conn, data.email.lower())

        # Return generic message even if user doesn't exist
        if not user:
            logger.info(f"Resend verification requested for non-existent email: {data.email}")
            return ResendVerificationResponse(message=generic_message)

        # 2. Check if already verified
        if user.is_verified:
            logger.info(f"Resend verification requested for already verified user: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified. You can login now."
            )

        # 3. Generate and send verification code using TwoFactorService
        twofa_svc = TwoFactorService(redis_client, email_svc)
        await twofa_svc.create_temp_code(
            user_id=str(user.id),
            purpose="verify",
            email=user.email
        )

        logger.info(f"Verification code resent to: {user.email}")

        return ResendVerificationResponse(message=generic_message)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification code. Please try again later."
        )
