from fastapi import Depends
import asyncpg
import redis
from uuid import UUID
from app.db.connection import get_db_connection
from app.db import procedures
from app.core.exceptions import UserNotFoundError, InvalidTokenError
from app.core.utils import generate_verification_code
from app.core.redis_utils import store_code_with_token, retrieve_and_verify_code, delete_code
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

    async def request_password_reset(self, request: RequestPasswordResetRequest) -> dict:
        logger.info("password_reset_request_start", email=request.email)

        reset_token = None
        user = await procedures.sp_get_user_by_email(self.db, request.email)
        if user:
            reset_code = generate_verification_code()

            # Store code with opaque token (prevents UUID enumeration)
            reset_token = store_code_with_token(
                self.redis_client,
                user.id,
                reset_code,
                key_prefix="reset_token",
                ttl=600
            )

            logger.info("password_reset_code_generated",
                       user_id=str(user.id),
                       email=user.email,
                       reset_token=reset_token,
                       expires_in_seconds=600)

            await self.email_service.send_password_reset_email(user.email, reset_code)
            logger.info("password_reset_email_sent", user_id=str(user.id), email=user.email)
        else:
            logger.warning("password_reset_request_user_not_found", email=request.email)

        result = {"message": "If an account with this email exists, a password reset code has been sent."}
        if reset_token:
            result["reset_token"] = reset_token
        return result

    async def confirm_password_reset(self, request: ResetPasswordRequest) -> dict:
        logger.info("password_reset_confirm_start", reset_token=request.reset_token)

        # Verify code using helper (handles constant-time comparison, UUID parsing, etc.)
        user_id = retrieve_and_verify_code(
            self.redis_client,
            request.reset_token,
            request.code,
            key_prefix="reset_token"
        )

        if not user_id:
            logger.warning("password_reset_failed",
                          reason="invalid_or_expired_token_or_code")
            raise InvalidTokenError("Reset code expired or not found")

        logger.info("password_reset_code_validated", user_id=str(user_id))

        await self.password_service.validate_password_strength(request.new_password)

        hashed_password = await self.password_service.get_password_hash(request.new_password)

        success = await procedures.sp_update_password(self.db, user_id, hashed_password)
        if not success:
            logger.error("password_reset_update_failed", user_id=str(user_id), reason="user_not_found")
            raise UserNotFoundError()

        delete_code(self.redis_client, request.reset_token, key_prefix="reset_token")

        await procedures.sp_revoke_all_refresh_tokens(self.db, user_id)

        logger.info("password_reset_complete", user_id=str(user_id))

        return {"message": "Password updated successfully."}
