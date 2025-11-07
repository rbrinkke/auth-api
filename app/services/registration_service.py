from fastapi import Depends
import asyncpg
from uuid import UUID
from app.db.connection import get_db_connection
from app.db import procedures
from app.core.exceptions import UserAlreadyExistsError
from app.core.utils import generate_verification_code
from app.core.redis_utils import store_code_with_token, retrieve_and_verify_code, delete_code
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

    async def register_user(self, user: UserCreate) -> dict:
        logger.info("user_registration_start", email=user.email)
        logger.debug("registration_password_validation_start", email=user.email)

        existing_user = await procedures.sp_get_user_by_email(self.db, user.email)
        if existing_user:
            logger.warning("user_registration_failed",
                          email=user.email,
                          reason="duplicate_email")
            raise UserAlreadyExistsError()

        logger.debug("registration_hashing_password", email=user.email)
        hashed_password = await self.password_service.get_password_hash(user.password)
        logger.debug("registration_password_hashed", email=user.email, hash_length=len(hashed_password))

        logger.debug("registration_creating_user_in_db", email=user.email)
        new_user = await procedures.sp_create_user(self.db, user.email, hashed_password)
        logger.info("user_created",
                   user_id=str(new_user.id),
                   email=new_user.email)
        logger.debug("registration_user_created_db", user_id=str(new_user.id))

        verification_code = generate_verification_code()
        logger.debug("registration_verification_code_generated", user_id=str(new_user.id))

        # Store code with opaque token (prevents UUID enumeration)
        logger.debug("registration_storing_code_redis", user_id=str(new_user.id))
        verification_token = store_code_with_token(
            self.redis_client,
            new_user.id,
            verification_code,
            key_prefix="verify_token",
            ttl=600
        )
        logger.debug("registration_code_stored_redis", user_id=str(new_user.id), token_length=len(verification_token))

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

        # Verify code using helper (handles constant-time comparison, UUID parsing, etc.)
        user_id = retrieve_and_verify_code(
            self.redis_client,
            verification_token,
            code,
            key_prefix="verify_token"
        )

        if not user_id:
            logger.warning("account_verification_failed",
                          reason="invalid_or_expired_token_or_code")
            return {"message": "Invalid or expired verification code."}

        # Verify user email in database
        await procedures.sp_verify_user_email(self.db, user_id)
        delete_code(self.redis_client, verification_token, key_prefix="verify_token")

        logger.info("account_verification_success", user_id=str(user_id))

        return {"message": "Account verified successfully."}
