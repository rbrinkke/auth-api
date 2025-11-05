"""
User logout endpoint.

Blacklists the refresh token to prevent further use.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.redis_client import RedisClient, get_redis
from app.core.tokens import get_jti_from_refresh_token
from app.schemas.auth import LogoutRequest, LogoutResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout and revoke refresh token",
    description="""
    Logout by blacklisting the refresh token.
    
    After logout, the refresh token can no longer be used to obtain
    new access tokens. The user must login again.
    
    **Note:** Access tokens remain valid until they expire (15 min).
    For immediate revocation, implement a token blacklist check
    in your API gateway or activity service.
    """
)
async def logout(
    request: LogoutRequest,
    redis: RedisClient = Depends(get_redis)
):
    """
    Logout user by blacklisting refresh token.
    
    Flow:
    1. Decode refresh token to get JTI
    2. Add JTI to Redis blacklist
    3. Return success message
    """
    try:
        # 1. Get JTI from token
        jti = get_jti_from_refresh_token(request.refresh_token)
        
        # 2. Blacklist the token
        await redis.blacklist_refresh_token(jti)
        
        logger.info(f"User logged out, JTI blacklisted: {jti}")
        
        return LogoutResponse(
            message="Logged out successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed. Please try again."
        )
