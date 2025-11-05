"""
Email verification endpoints.

Handles both verification and resending verification emails.
"""
import logging

import asyncpg
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status, Query
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.core.redis_client import RedisClient, get_redis
from app.core.tokens import generate_verification_token
from app.db.connection import get_db_connection
from app.db.procedures import sp_get_user_by_email, sp_verify_user_email
from app.schemas.auth import (
    ResendVerificationRequest,
    ResendVerificationResponse,
    VerifyEmailResponse
)
from app.services.email_service import get_email_service, EmailService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/verify",
    response_model=VerifyEmailResponse,
    summary="Verify email address",
    description="""
    Verify a user's email address using the token from the verification email.
    
    After successful verification, the user can login.
    """
)
async def verify_email(
    token: str = Query(..., description="Verification token from email"),
    conn: asyncpg.Connection = Depends(get_db_connection),
    redis: RedisClient = Depends(get_redis)
):
    """
    Verify user email with token from email link.
    
    Flow:
    1. Look up token in Redis
    2. If valid, update user in database
    3. Delete token from Redis
    4. Return success message
    """
    try:
        # 1. Get user_id from token
        user_id = await redis.get_user_id_from_verification_token(token)
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        # 2. Mark user as verified in database
        success = await sp_verify_user_email(conn, user_id)
        
        if not success:
            logger.error(f"Failed to verify user {user_id} - user not found")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
        
        # 3. Delete token from Redis (one-time use)
        await redis.delete_verification_token(token, user_id)
        
        logger.info(f"Email verified successfully for user {user_id}")
        
        return VerifyEmailResponse(
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
    summary="Resend verification email",
    description="""
    Request a new verification email.
    
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
    redis: RedisClient = Depends(get_redis),
    email_svc: EmailService = Depends(get_email_service)
):
    """
    Resend verification email to user.
    
    Flow:
    1. Look up user by email
    2. Check if already verified
    3. Generate new token (invalidates old one)
    4. Send new verification email
    5. Return generic success message
    """
    try:
        # Generic response message (for security)
        generic_message = "If an unverified account exists for this email, a verification link has been sent."
        
        # 1. Find user
        user = await sp_get_user_by_email(conn, data.email)
        
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
        
        # 3. Generate new verification token
        verification_token = generate_verification_token()
        
        # 4. Store in Redis (replaces old token via reverse lookup)
        await redis.set_verification_token(verification_token, user.id)

        # 5. Send verification email (async)
        background_tasks.add_task(
            email_svc.send_verification_email,
            user.email,
            verification_token
        )
        
        logger.info(f"Verification email resent to: {user.email}")
        
        return ResendVerificationResponse(message=generic_message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification email. Please try again later."
        )
