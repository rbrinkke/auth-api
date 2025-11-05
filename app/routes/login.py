"""
User login endpoint.

Implements hard verification: users MUST verify email before login.
Supports 2FA/TOTP for enhanced security.
"""
import logging

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.core.security import verify_password
from app.core.tokens import create_access_token, create_refresh_token
from app.core.redis_client import RedisClient, get_redis
from app.db.connection import get_db_connection
from app.db.procedures import sp_get_user_by_email, sp_update_last_login
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.email_service import EmailService
from app.services.two_factor_service import TwoFactorService

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
    - If 2FA is enabled, a 6-digit code will be sent to your email

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
    conn: asyncpg.Connection = Depends(get_db_connection),
    redis: RedisClient = Depends(get_redis),
    email_svc: EmailService = Depends(EmailService)
):
    """
    Authenticate user and return JWT tokens.

    Flow with 2FA:
    1. Find user by email
    2. Verify password
    3. CHECK: is_verified = TRUE (CRITICAL!)
    4. CHECK: is_active = TRUE
    5. CHECK: two_factor_enabled
       - If TRUE: Generate 6-digit code, send via email, return 202
       - If FALSE: Continue to step 6
    6. Update last_login_at
    7. Generate and return tokens
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

        # 5. CHECK: Is 2FA enabled?
        if getattr(user, 'two_factor_enabled', False):
            logger.info(f"2FA required for user: {user.email}")

            # Generate and send 2FA code
            twofa_svc = TwoFactorService(redis, email_svc)
            code = await twofa_svc.create_temp_code(
                user_id=user.id,
                purpose="login",
                email=user.email
            )

            logger.info(f"2FA code sent to {user.email} for login")

            # Return 202 Accepted with message to check email
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail={
                    "message": "Two-factor authentication required. Check your email for a 6-digit code.",
                    "two_factor_required": True,
                    "user_id": str(user.id)
                }
            )

        # 6. Update last login timestamp
        await sp_update_last_login(conn, user.id)

        # 7. Generate tokens
        access_token = create_access_token(user.id)
        refresh_token, _ = create_refresh_token(user.id)

        logger.info(f"User logged in successfully: {user.email} (id: {user.id})")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions (including our 202 for 2FA)
        if http_exc.status_code == status.HTTP_202_ACCEPTED:
            raise http_exc
        # Convert 202 to a proper response format
        raise http_exc
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again later."
        )


@router.post(
    "/login-2fa",
    response_model=TokenResponse,
    summary="Complete login with 2FA code",
    description="""
    Complete the login flow using the 6-digit 2FA code sent to your email.

    This endpoint is used after /auth/login when 2FA is enabled.
    """
)
async def login_with_2fa(
    user_id: str,
    code: str,
    conn: asyncpg.Connection = Depends(get_db_connection),
    redis: RedisClient = Depends(get_redis)
):
    """
    Verify 2FA code and complete login.

    Flow:
    1. Verify 2FA code
    2. Get user from database
    3. Validate user (verified, active)
    4. Update last_login_at
    5. Generate and return tokens
    """
    try:
        # 1. Verify 2FA code
        twofa_svc = TwoFactorService(redis, None)

        if not await twofa_svc.verify_temp_code(user_id, code, "login"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired 2FA code"
            )

        # 2. Get user from database
        # Note: In production, you'd fetch by ID. For now, fetch all and filter.
        # This is a simplified approach - in real implementation, create sp_get_user_by_id
        user = None
        # TODO: Implement sp_get_user_by_id procedure

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # 3. Validate user
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been deactivated"
            )

        # 4. Update last login timestamp
        await sp_update_last_login(conn, user.id)

        # 5. Generate tokens
        access_token = create_access_token(user.id)
        refresh_token, _ = create_refresh_token(user.id)

        logger.info(f"User logged in with 2FA: {user.email} (id: {user.id})")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during 2FA login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again later."
        )
