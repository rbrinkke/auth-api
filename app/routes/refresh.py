"""
Token refresh endpoint with rotation.

Implements refresh token rotation: old token is blacklisted when new tokens are issued.
This is a MANDATORY security feature for production.
"""
import logging

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.redis_client import RedisClient, get_redis
from app.core.tokens import (
    create_access_token,
    create_refresh_token,
    get_jti_from_refresh_token,
    get_user_id_from_token
)
from app.db.connection import get_db_connection
from app.db.procedures import sp_get_user_by_id
from app.schemas.auth import RefreshTokenRequest, TokenResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="""
    Exchange a refresh token for new access and refresh tokens.
    
    **Security - Token Rotation:**
    The old refresh token is immediately blacklisted after use.
    This prevents replay attacks if a token is stolen.
    
    **Requirements:**
    - Valid, non-blacklisted refresh token
    - User must still be active and verified
    """
)
async def refresh_tokens(
    request: RefreshTokenRequest,
    conn: asyncpg.Connection = Depends(get_db_connection),
    redis: RedisClient = Depends(get_redis)
):
    """
    Refresh tokens with automatic rotation.
    
    Flow:
    1. Decode and validate refresh token
    2. Extract JTI (JWT ID)
    3. CHECK: Is token blacklisted?
    4. Extract user_id
    5. CHECK: User still active and verified?
    6. ROTATE: Blacklist old token
    7. Generate new access + refresh tokens
    8. Return new tokens
    """
    try:
        # 1 & 2. Decode token and get JTI
        jti = get_jti_from_refresh_token(request.refresh_token)
        
        # 3. Check if token is blacklisted
        if await redis.is_token_blacklisted(jti):
            logger.warning(f"Attempted use of blacklisted refresh token: {jti}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
        # 4. Get user_id from token
        user_id = get_user_id_from_token(request.refresh_token, expected_type="refresh")
        
        # 5. Verify user still exists and is valid
        user = await sp_get_user_by_id(conn, user_id)
        
        if not user:
            logger.error(f"Refresh token for non-existent user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        if not user.is_active:
            logger.warning(f"Refresh attempt by deactivated user: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been deactivated"
            )
        
        if not user.is_verified:
            logger.warning(f"Refresh attempt by unverified user: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified"
            )
        
        # 6. CRITICAL: Blacklist the old refresh token (Token Rotation)
        await redis.blacklist_refresh_token(jti)
        
        # 7. Generate new tokens
        new_access_token = create_access_token(user.id)
        new_refresh_token, new_jti = create_refresh_token(user.id)
        
        logger.info(f"Tokens refreshed for user: {user.email} (id: {user.id})")
        logger.debug(f"Old JTI blacklisted: {jti}, New JTI: {new_jti}")
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during token refresh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed. Please login again."
        )
