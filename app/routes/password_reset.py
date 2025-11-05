"""
Password reset endpoints.

Implements secure password reset flow with time-limited tokens.
"""
import logging

import asyncpg
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.core.redis_client import RedisClient, get_redis
from app.core.security import hash_password
from app.core.tokens import generate_reset_token
from app.db.connection import get_db_connection
from app.db.procedures import sp_get_user_by_email, sp_update_password
from app.schemas.auth import (
    RequestPasswordResetRequest,
    RequestPasswordResetResponse,
    ResetPasswordRequest,
    ResetPasswordResponse
)
from app.services.email_service import email_service

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
    request: RequestPasswordResetRequest,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db_connection),
    redis: RedisClient = Depends(get_redis)
):
    """
    Send password reset email.
    
    Flow:
    1. Look up user by email
    2. Generate reset token
    3. Store in Redis (with reverse lookup)
    4. Send reset email in background
    5. Return generic success message
    """
    try:
        # Generic response (for security)
        generic_message = "If an account exists for this email, a password reset link has been sent."
        
        # 1. Find user
        user = await sp_get_user_by_email(conn, request.email)
        
        # Return generic message even if user doesn't exist
        if not user:
            logger.info(f"Password reset requested for non-existent email: {request.email}")
            return RequestPasswordResetResponse(message=generic_message)
        
        # 2. Generate reset token
        reset_token = generate_reset_token()
        
        # 3. Store in Redis (replaces old token via reverse lookup)
        await redis.set_reset_token(reset_token, user.id)
        
        # 4. Send reset email (async)
        background_tasks.add_task(
            email_service.send_password_reset_email,
            user.email,
            reset_token
        )
        
        logger.info(f"Password reset email sent to: {user.email}")
        
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
    """
)
async def reset_password(
    request: ResetPasswordRequest,
    conn: asyncpg.Connection = Depends(get_db_connection),
    redis: RedisClient = Depends(get_redis)
):
    """
    Reset user password with token.
    
    Flow:
    1. Look up token in Redis
    2. Hash new password
    3. Update password in database
    4. Delete token from Redis
    5. Return success message
    """
    try:
        # 1. Get user_id from token
        user_id = await redis.get_user_id_from_reset_token(request.token)
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # 2. Hash new password
        new_hashed_password = hash_password(request.new_password)
        
        # 3. Update password in database
        success = await sp_update_password(conn, user_id, new_hashed_password)
        
        if not success:
            logger.error(f"Failed to reset password for user {user_id} - user not found")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        # 4. Delete token from Redis (one-time use)
        await redis.delete_reset_token(request.token, user_id)
        
        logger.info(f"Password reset successfully for user {user_id}")
        
        return ResetPasswordResponse(
            message="Password updated successfully. You can now login with your new password."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed. Please try again later."
        )
