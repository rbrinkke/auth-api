from fastapi import Depends
import asyncpg
import random
import redis
from app.db.connection import get_db_connection
from app.db import procedures
from app.core.exceptions import UserNotFoundError, InvalidTokenError
from app.services.password_service import PasswordService
from app.services.email_service import EmailService
from app.core.redis_client import get_redis_client
from app.schemas.auth import RequestPasswordResetRequest, ResetPasswordRequest

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
        all_keys = self.redis_client.keys("2FA:*:reset")

        user_id = None
        for key in all_keys:
            stored_code = self.redis_client.get(key)
            if stored_code == request.code:
                key_str = key.decode() if isinstance(key, bytes) else key
                user_id_str = key_str.split(":")[1]
                user_id = user_id_str
                break

        if not user_id:
            return {"message": "Invalid or expired reset code."}

        self.redis_client.delete(f"2FA:{user_id}:reset")

        user = await procedures.sp_get_user_by_id(self.db, user_id)
        if not user:
            raise UserNotFoundError()

        hashed_password = await self.password_service.get_password_hash(request.new_password)

        updated = await procedures.sp_update_password(self.db, user.id, hashed_password)
        if not updated:
            raise UserNotFoundError()

        self.redis_client.delete(f"2FA:{user_id}:reset")

        await procedures.sp_revoke_all_refresh_tokens(self.db, user.id)

        return {"message": "Password updated successfully."}

