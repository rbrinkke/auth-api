from fastapi import Depends
import asyncpg
import secrets
from datetime import timedelta
from uuid import UUID
from app.db.connection import get_db_connection
from app.db import procedures
from app.core.exceptions import UserAlreadyExistsError
from app.core.utils import generate_verification_code
from app.services.password_service import PasswordService
from app.services.email_service import EmailService
from app.core.redis_client import get_redis_client
import redis
from app.schemas.user import UserCreate
from app.core.logging_config import get_logger
from app.middleware.correlation import correlation_id_var

logger = get_logger(__name__)

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

    def _generate_verification_token(self) -> str:
        """Generate cryptographically secure opaque verification token."""
        return secrets.token_hex(16)  # 32-character hex token

    async def register_user(self, user: UserCreate) -> dict:
        logger.info("user_registration_start", email=user.email)

        existing_user = await procedures.sp_get_user_by_email(self.db, user.email)
        if existing_user:
            logger.warning("user_registration_failed",
                          email=user.email,
                          reason="duplicate_email")
            raise UserAlreadyExistsError()

        hashed_password = await self.password_service.get_password_hash(user.password)

        new_user = await procedures.sp_create_user(self.db, user.email, hashed_password)
        logger.info("user_created",
                   user_id=str(new_user.id),
                   email=new_user.email)

        verification_code = generate_verification_code()
        verification_token = self._generate_verification_token()

        # Store verification token → {user_id}:{code} mapping in Redis
        # This prevents account takeover by guessing user_ids
        redis_key = f"verify_token:{verification_token}"
        redis_value = f"{str(new_user.id)}:{verification_code}"
        self.redis_client.setex(redis_key, 600, redis_value)

        logger.info("verification_code_generated",
                   user_id=str(new_user.id),
                   verification_token=verification_token,
                   expires_in_seconds=600)

        await self.email_service.send_verification_email(new_user.email, verification_code)
        logger.info("verification_email_sent",
                   user_id=str(new_user.id),
                   email=new_user.email)

        logger.info("user_registration_complete",
                   user_id=str(new_user.id),
                   email=new_user.email)

        return {
            "message": "User registered successfully",
            "email": new_user.email,
            "user_id": str(new_user.id),
            "verification_token": verification_token
        }

    async def verify_account_by_code(self, verification_token: str, code: str) -> dict:
        logger.info("account_verification_start", verification_token=verification_token)

        # Lookup verification token → extract user_id and stored code
        redis_key = f"verify_token:{verification_token}"
        stored_token_data = self.redis_client.get(redis_key)

        if not stored_token_data:
            logger.warning("account_verification_failed",
                          reason="invalid_or_expired_token")
            return {"message": "Invalid or expired verification code."}

        # Extract user_id and stored_code from Redis value
        token_data_str = stored_token_data.decode('utf-8') if isinstance(stored_token_data, bytes) else stored_token_data
        try:
            stored_user_id_str, stored_code = token_data_str.split(':')
            user_id = UUID(stored_user_id_str)
        except (ValueError, IndexError):
            logger.error("account_verification_failed",
                        reason="malformed_token_data",
                        token_data=token_data_str)
            return {"message": "Invalid or expired verification code."}

        # Validate code matches
        if stored_code != code:
            logger.warning("account_verification_failed",
                          user_id=str(user_id),
                          reason="invalid_code")
            return {"message": "Invalid or expired verification code."}

        # Verify user email in database
        await procedures.sp_verify_user_email(self.db, user_id)
        self.redis_client.delete(redis_key)

        logger.info("account_verification_success", user_id=str(user_id))

        return {"message": "Account verified successfully."}
