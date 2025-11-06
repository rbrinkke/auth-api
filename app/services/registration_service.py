from fastapi import Depends
import asyncpg
import random
from datetime import timedelta
from uuid import UUID
from app.db.connection import get_db_connection
from app.db import procedures
from app.core.exceptions import UserAlreadyExistsError
from app.services.password_service import PasswordService
from app.services.email_service import EmailService
from app.core.redis_client import get_redis_client
import redis
from app.schemas.user import UserCreate

class RegistrationService:
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

    async def register_user(self, user: UserCreate) -> dict:
        existing_user = await procedures.sp_get_user_by_email(self.db, user.email)
        if existing_user:
            raise UserAlreadyExistsError()

        hashed_password = await self.password_service.get_password_hash(user.password)

        new_user = await procedures.sp_create_user(self.db, user.email, hashed_password)

        verification_code = self._generate_6_digit_code()

        self.redis_client.setex(
            f"2FA:{new_user.id}:verify",
            600,
            verification_code
        )

        await self.email_service.send_verification_email(new_user.email, verification_code)

        return {
            "message": "User registered successfully",
            "email": new_user.email,
            "user_id": str(new_user.id)
        }

    async def verify_account_by_code(self, user_id: UUID, code: str) -> dict:
        redis_key = f"2FA:{user_id}:verify"
        stored_code = self.redis_client.get(redis_key)
        if not stored_code or stored_code != code:
            return {"message": "Invalid or expired verification code."}

        await procedures.sp_verify_user_email(self.db, UUID(user_id))
        self.redis_client.delete(redis_key)
        return {"message": "Account verified successfully."}

