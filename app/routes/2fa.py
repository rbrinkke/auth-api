"""
Two-Factor Authentication endpoints.

Provides endpoints for enabling, disabling, and verifying 2FA.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
import asyncpg

from app.core.redis_client import get_redis, RedisClient
from app.services.email_service import EmailService
from app.services.two_factor_service import (
    TwoFactorService,
    InvalidCodeError
)
from app.db.connection import get_db_connection

router = APIRouter(prefix="/auth", tags=["2FA"])
logger = logging.getLogger(__name__)


# Pydantic models
class Enable2FARequest(BaseModel):
    """Request to enable 2FA (requires authentication)."""
    pass


class Enable2FAResponse(BaseModel):
    """Response for enabling 2FA."""
    qr_code_url: str = Field(..., description="QR code image for authenticator app")
    backup_codes: list[str] = Field(..., description="Backup codes (store securely!)")
    secret: str = Field(..., description="TOTP secret (for manual entry)")
    message: str = "2FA setup initiated. Scan QR code with authenticator app."


class Verify2FARequest(BaseModel):
    """Request to verify 2FA code."""
    user_identifier: str = Field(..., description="Email or session ID")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit code")
    purpose: str = Field(..., description="Purpose: login, reset, or verify")
    session_id: str | None = Field(None, description="Session ID from login flow")


class Verify2FAResponse(BaseModel):
    """Response for verifying 2FA code."""
    verified: bool
    session_id: str | None = None
    message: str = "Code verified successfully"


class Disable2FARequest(BaseModel):
    """Request to disable 2FA."""
    password: str = Field(..., description="Current password")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")


class Disable2FAResponse(BaseModel):
    """Response for disabling 2FA."""
    disabled: bool = True
    message: str = "2FA disabled successfully"


class Confirm2FASetupRequest(BaseModel):
    """Request to confirm 2FA setup after scanning QR code."""
    code: str = Field(..., min_length=6, max_length=6, description="Code from authenticator app")


@router.post("/enable-2fa", response_model=Enable2FAResponse)
async def enable_2fa(
    request: Enable2FARequest,
    conn: asyncpg.Connection = Depends(get_db_connection),
    redis: RedisClient = Depends(get_redis),
    email_svc: EmailService = Depends(EmailService),
    # TODO: Add authentication - get current user from JWT
    # current_user: User = Depends(get_current_user)
):
    """
    Enable 2FA for authenticated user.

    Returns QR code for authenticator app setup and backup codes.
    """
    try:
        # For now, use a dummy user ID - in real implementation, get from JWT
        # user_id = current_user.id
        # user_email = current_user.email
        user_id = "dummy-user-id"  # TODO: Replace with actual user from JWT
        user_email = "user@example.com"  # TODO: Replace with actual user email

        # Create 2FA service
        twofa_svc = TwoFactorService(redis, email_svc)

        # Generate TOTP secret
        secret = twofa_svc.generate_totp_secret()

        # Generate QR code
        qr_code_url = twofa_svc.generate_qr_code(secret, user_email)

        # Generate backup codes
        backup_codes = twofa_svc.generate_backup_codes(8)

        # Hash backup codes for storage
        hashed_codes = [twofa_svc.hash_backup_code(code) for code in backup_codes]

        # Encrypt TOTP secret for storage
        encrypted_secret = twofa_svc.encrypt_secret(secret)

        # Store in database
        await conn.execute(
            """
                UPDATE activity.users
                SET two_factor_enabled = FALSE,
                    two_factor_secret = $1,
                    two_factor_backup_codes = $2
                WHERE id = $3
            """,
            encrypted_secret,
            hashed_codes,  # Store as JSON array
            user_id
        )

        logger.info(f"2FA setup initiated for user {user_id}")

        return Enable2FAResponse(
            qr_code_url=qr_code_url,
            backup_codes=backup_codes,
            secret=secret
        )

    except Exception as e:
        logger.error(f"Error enabling 2FA: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable 2FA"
        )


@router.post("/verify-2fa-setup", response_model=Verify2FAResponse)
async def verify_2fa_setup(
    request: Confirm2FASetupRequest,
    conn: asyncpg.Connection = Depends(get_db_connection),
    redis: RedisClient = Depends(get_redis),
    # current_user: User = Depends(get_current_user)
):
    """
    Verify 2FA setup after scanning QR code.

    This confirms that the authenticator app is working correctly.
    """
    try:
        # user_id = current_user.id
        user_id = "dummy-user-id"  # TODO: Replace with actual user from JWT

        # Get user's TOTP secret
        row = await conn.fetchrow(
            "SELECT two_factor_secret FROM activity.users WHERE id = $1",
            user_id
        )

        if not row or not row["two_factor_secret"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA not initialized"
            )

        # Decrypt secret
        twofa_svc = TwoFactorService(redis, None)  # No email service needed for verification
        secret = twofa_svc.decrypt_secret(row["two_factor_secret"])

        # Verify TOTP code
        if not twofa_svc.verify_totp_code(secret, request.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )

        # Enable 2FA
        await conn.execute(
            "UPDATE activity.users SET two_factor_enabled = TRUE WHERE id = $1",
            user_id
        )

        logger.info(f"2FA enabled for user {user_id}")

        return Verify2FAResponse(
            verified=True,
            message="2FA enabled successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying 2FA setup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify 2FA setup"
        )


@router.post("/verify-2fa", response_model=Verify2FAResponse)
async def verify_2fa_code(
    request: Verify2FARequest,
    conn: asyncpg.Connection = Depends(get_db_connection),
    redis: RedisClient = Depends(get_redis),
    email_svc: EmailService = Depends(EmailService)
):
    """
    Verify 2FA code during login or other flows.

    This endpoint is used by the login flow when 2FA is enabled.
    """
    try:
        twofa_svc = TwoFactorService(redis, email_svc)

        # Check if user is locked out
        if await twofa_svc.is_locked_out(request.user_identifier, request.purpose):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Please try again later."
            )

        # Get user_id from email or use provided session_id
        user_id = None

        if request.session_id:
            # Validate login session
            user_id = await twofa_svc.validate_login_session(request.session_id)
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired session"
                )
        else:
            # Get user by email
            row = await conn.fetchrow(
                "SELECT id FROM activity.users WHERE email = $1",
                request.user_identifier.lower()
            )
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User not found"
                )
            user_id = row["id"]

        # Verify the code
        if not await twofa_svc.verify_temp_code(user_id, request.code, request.purpose):
            await twofa_svc.increment_failed_attempt(user_id, request.purpose)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )

        # Reset failed attempts on success
        await twofa_svc.reset_failed_attempts(user_id, request.purpose)

        # For login flow, create session
        session_id = None
        if request.purpose == "login":
            session_id = await twofa_svc.generate_login_session(user_id)

        logger.info(f"2FA verified successfully for user {user_id}, purpose: {request.purpose}")

        return Verify2FAResponse(
            verified=True,
            session_id=session_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying 2FA code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify code"
        )


@router.post("/disable-2fa", response_model=Disable2FAResponse)
async def disable_2fa(
    request: Disable2FARequest,
    conn: asyncpg.Connection = Depends(get_db_connection),
    redis: RedisClient = Depends(get_redis),
    # current_user: User = Depends(get_current_user)
):
    """
    Disable 2FA for authenticated user.

    Requires current password + TOTP code.
    """
    try:
        # user_id = current_user.id
        user_id = "dummy-user-id"  # TODO: Replace with actual user from JWT

        # Get user's TOTP secret
        row = await conn.fetchrow(
            "SELECT two_factor_secret FROM activity.users WHERE id = $1",
            user_id
        )

        if not row or not row["two_factor_secret"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is not enabled"
            )

        # Decrypt secret
        twofa_svc = TwoFactorService(redis, None)
        secret = twofa_svc.decrypt_secret(row["two_factor_secret"])

        # Verify TOTP code
        if not twofa_svc.verify_totp_code(secret, request.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )

        # TODO: Verify current password
        # For now, skip password verification

        # Disable 2FA
        await conn.execute(
            """
                UPDATE activity.users
                SET two_factor_enabled = FALSE,
                    two_factor_secret = NULL,
                    two_factor_backup_codes = NULL,
                    backup_codes_used = 0
                WHERE id = $1
            """,
            user_id
        )

        # Cleanup Redis keys
        await redis.client.delete(f"2FA:{user_id}:login")
        await redis.client.delete(f"2FA:{user_id}:reset")
        await redis.client.delete(f"2FA:{user_id}:verify")
        await redis.client.delete(f"2FA_ATTEMPTS:{user_id}:login")
        await redis.client.delete(f"2FA_ATTEMPTS:{user_id}:reset")

        logger.info(f"2FA disabled for user {user_id}")

        return Disable2FAResponse()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling 2FA: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable 2FA"
        )


@router.get("/2fa-status")
async def get_2fa_status(
    conn: asyncpg.Connection = Depends(get_db_connection),
    # current_user: User = Depends(get_current_user)
):
    """
    Get 2FA status for authenticated user.

    Returns whether 2FA is enabled and setup is complete.
    """
    try:
        # user_id = current_user.id
        user_id = "dummy-user-id"  # TODO: Replace with actual user from JWT

        row = await conn.fetchrow(
            "SELECT two_factor_enabled FROM activity.users WHERE id = $1",
            user_id
        )

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {
            "two_factor_enabled": row["two_factor_enabled"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting 2FA status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get 2FA status"
        )
