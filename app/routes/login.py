"""
User login endpoint.

Implements hard verification: users MUST verify email before login.
"""
import logging

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.core.security import verify_password
from app.core.tokens import create_access_token, create_refresh_token
from app.db.connection import get_db_connection
from app.db.procedures import sp_get_user_by_email, sp_update_last_login
from app.schemas.auth import LoginRequest, TokenResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login to get access tokens",
    description="""
    Authenticate with email and password to receive JWT tokens.
    
    **Requirements:**
    - Email must be verified (check your inbox if you just registered)
    - Account must be active
    
    **Returns:**
    - `access_token`: Short-lived token (15 min) for API requests
    - `refresh_token`: Long-lived token (30 days) to get new access tokens
    
    **Rate limit:** 5 requests per minute per IP
    """
)
@limiter.limit(f"{settings.rate_limit_login_per_minute}/minute")
async def login(
    request: Request,
    credentials: LoginRequest,
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Authenticate user and return JWT tokens.
    
    Flow:
    1. Find user by email
    2. Verify password
    3. CHECK: is_verified = TRUE (CRITICAL!)
    4. CHECK: is_active = TRUE
    5. Update last_login_at
    6. Generate and return tokens
    """
    try:
        # 1. Find user by email (username field is actually email)
        user = await sp_get_user_by_email(conn, credentials.username)
        
        if not user:
            # Generic error message to prevent email enumeration
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # 2. Verify password
        if not verify_password(credentials.password, user.hashed_password):
            logger.warning(f"Failed login attempt for user: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # 3. CRITICAL: Check if email is verified (Hard Verification)
        if not user.is_verified:
            logger.info(f"Login attempt by unverified user: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified. Please check your inbox or request a new verification email."
            )
        
        # 4. Check if account is active
        if not user.is_active:
            logger.warning(f"Login attempt by deactivated user: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been deactivated"
            )
        
        # 5. Update last login timestamp
        await sp_update_last_login(conn, user.id)
        
        # 6. Generate tokens
        access_token = create_access_token(user.id)
        refresh_token, _ = create_refresh_token(user.id)
        
        logger.info(f"User logged in successfully: {user.email} (id: {user.id})")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again later."
        )
