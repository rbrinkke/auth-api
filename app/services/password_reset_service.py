from fastapi import Depends
import asyncpg
import random
import redis
from uuid import UUID
from app.db.connection import get_db_connection
from app.db import procedures
from app.core.exceptions import UserNotFoundError, InvalidTokenError
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

    def _generate_6_digit_code(self) -> str:
        return str(random.randint(100000, 999999))

    async def request_password_reset(self, request: RequestPasswordResetRequest) -> dict:
        logger.info("password_reset_request_start", email=request.email)

        user = await procedures.sp_get_user_by_email(self.db, request.email)
        if user:
            reset_code = self._generate_6_digit_code()

            self.redis_client.setex(
                f"2FA:{user.id}:reset",
                600,
                reset_code
            )

            logger.info("password_reset_code_generated",
                       user_id=str(user.id),
                       email=user.email,
                       expires_in_seconds=600)

            await self.email_service.send_password_reset_email(user.email, reset_code)
            logger.info("password_reset_email_sent", user_id=str(user.id), email=user.email)
        else:
            logger.warning("password_reset_request_user_not_found", email=request.email)

        return {"message": "If an account with this email exists, a password reset code has been sent."}

    async def confirm_password_reset(self, request: ResetPasswordRequest) -> dict:
        user_id = UUID(request.user_id)
        redis_key = f"2FA:{user_id}:reset"

        logger.info("password_reset_confirm_start", user_id=str(user_id))

        stored_code = self.redis_client.get(redis_key)

        if not stored_code:
            logger.warning("password_reset_code_expired", user_id=str(user_id))
            raise InvalidTokenError("Reset code expired or not found")

        stored_code_str = stored_code.decode('utf-8') if isinstance(stored_code, bytes) else stored_code
        if stored_code_str != request.code:
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
