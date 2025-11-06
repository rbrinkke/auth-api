from fastapi import Depends
import asyncpg
import random
import redis
import logging
from uuid import UUID
from app.db.connection import get_db_connection
from app.db import procedures
from app.core.exceptions import UserNotFoundError, InvalidTokenError
from app.services.password_service import PasswordService
from app.services.email_service import EmailService
from app.core.redis_client import get_redis_client
from app.schemas.auth import RequestPasswordResetRequest, ResetPasswordRequest

logger = logging.getLogger(__name__)

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
        user = await procedures.sp_get_user_by_email(self.db, request.email)
        if user:
            reset_code = self._generate_6_digit_code()

            self.redis_client.setex(
                f"2FA:{user.id}:reset",
                600,
                reset_code
            )

            await self.email_service.send_password_reset_email(user.email, reset_code)

        return {"message": "If an account with this email exists, a password reset code has been sent."}

    async def confirm_password_reset(self, request: ResetPasswordRequest) -> dict:
        user_id = UUID(request.user_id)
        redis_key = f"2FA:{user_id}:reset"

        stored_code = self.redis_client.get(redis_key)

        if not stored_code:
            raise InvalidTokenError("Reset code expired or not found")

        stored_code_str = stored_code.decode('utf-8') if isinstance(stored_code, bytes) else stored_code
        if stored_code_str != request.code:
            raise InvalidTokenError("Invalid reset code")

        # Validate password strength
        await self.password_service.validate_password_strength(request.new_password)

        # Hash and update password
        hashed_password = await self.password_service.get_password_hash(request.new_password)

        success = await procedures.sp_update_password(self.db, user_id, hashed_password)
        if not success:
            raise UserNotFoundError()

        # Delete used code
        self.redis_client.delete(redis_key)

        # Revoke all refresh tokens (force re-login after password change)
        await procedures.sp_revoke_all_refresh_tokens(self.db, user_id)

        logger.info(f"Password reset successful for user {user_id}")
        return {"message": "Password updated successfully."}

