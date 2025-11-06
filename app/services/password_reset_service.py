from fastapi import Depends
import asyncpg
import secrets
import redis
from uuid import UUID
from app.db.connection import get_db_connection
from app.db import procedures
from app.core.exceptions import UserNotFoundError, InvalidTokenError
from app.core.utils import generate_verification_code
from app.services.password_service import PasswordService
from app.services.email_service import EmailService
from app.core.redis_client import get_redis_client
from app.schemas.auth import RequestPasswordResetRequest, ResetPasswordRequest
from app.core.logging_config import get_logger
from app.middleware.correlation import correlation_id_var

logger = get_logger(__name__)

class PasswordResetService:
    def __init__(
        self,
        db: asyncpg.Connection = Depends(get_db_connection),
        password_service: PasswordService = Depends(PasswordService),
        email_service: EmailService = Depends(EmailService),
        redis_client: redis.Redis = Depends(get_redis_client)
    ):
        self.db = db
        self.password_service = password_service
        self.email_service = email_service
        self.redis_client = redis_client

    def _generate_reset_token(self) -> str:
        """Generate cryptographically secure opaque reset token."""
        return secrets.token_hex(16)  # 32-character hex token

    async def request_password_reset(self, request: RequestPasswordResetRequest) -> dict:
        logger.info("password_reset_request_start", email=request.email)

        user = await procedures.sp_get_user_by_email(self.db, request.email)
        if user:
            reset_code = generate_verification_code()
            reset_token = self._generate_reset_token()

            # Store reset token → {user_id}:{code} mapping in Redis
            # This prevents account takeover by guessing user_ids
            redis_key = f"reset_token:{reset_token}"
            redis_value = f"{str(user.id)}:{reset_code}"
            self.redis_client.setex(redis_key, 600, redis_value)

            logger.info("password_reset_code_generated",
                       user_id=str(user.id),
                       email=user.email,
                       reset_token=reset_token,
                       expires_in_seconds=600)

            await self.email_service.send_password_reset_email(user.email, reset_code)
            logger.info("password_reset_email_sent", user_id=str(user.id), email=user.email)
        else:
            logger.warning("password_reset_request_user_not_found", email=request.email)

        return {"message": "If an account with this email exists, a password reset code has been sent."}

    async def confirm_password_reset(self, request: ResetPasswordRequest) -> dict:
        logger.info("password_reset_confirm_start", reset_token=request.reset_token)

        # Lookup reset token → extract user_id and stored code
        redis_key = f"reset_token:{request.reset_token}"
        stored_token_data = self.redis_client.get(redis_key)

        if not stored_token_data:
            logger.warning("password_reset_failed", reason="invalid_or_expired_token")
            raise InvalidTokenError("Reset code expired or not found")

        # Extract user_id and stored_code from Redis value
        token_data_str = stored_token_data
        try:
            stored_user_id_str, stored_code = token_data_str.split(':')
            user_id = UUID(stored_user_id_str)
        except (ValueError, IndexError):
            logger.error("password_reset_failed",
                        reason="malformed_token_data",
                        token_data=token_data_str)
            raise InvalidTokenError("Invalid reset code")

        # Validate code matches
        if stored_code != request.code:
            logger.warning("password_reset_code_invalid", user_id=str(user_id))
            raise InvalidTokenError("Invalid reset code")

        logger.info("password_reset_code_validated", user_id=str(user_id))

        await self.password_service.validate_password_strength(request.new_password)

        hashed_password = await self.password_service.get_password_hash(request.new_password)

        success = await procedures.sp_update_password(self.db, user_id, hashed_password)
        if not success:
            logger.error("password_reset_update_failed", user_id=str(user_id), reason="user_not_found")
            raise UserNotFoundError()

        self.redis_client.delete(redis_key)

        await procedures.sp_revoke_all_refresh_tokens(self.db, user_id)

        logger.info("password_reset_complete", user_id=str(user_id))

        return {"message": "Password updated successfully."}
