from fastapi import Depends
import asyncio
import uuid
from app.core.security import PasswordManager
from app.services.password_validation_service import (
    PasswordValidationService,
    get_password_validation_service,
    PasswordValidationError
)
from app.core.exceptions import InvalidPasswordError
from app.core.logging_config import get_logger
from app.middleware.correlation import correlation_id_var

logger = get_logger(__name__)

class PasswordService:
    def __init__(
        self,
        password_manager: PasswordManager = Depends(PasswordManager),
        validation_service: PasswordValidationService = Depends(get_password_validation_service)
    ):
        self.password_manager = password_manager
        self.validation_service = validation_service

    async def validate_password_strength(self, password: str):
        try:
            logger.info("password_validation_start", password_length=len(password))
            await self.validation_service.validate_password(password)
            logger.info("password_validation_success", password_length=len(password))
        except PasswordValidationError as e:
            logger.warning("password_validation_failed", reason=str(e), password_length=len(password))
            raise InvalidPasswordError(str(e))

    async def get_password_hash(self, password: str) -> str:
        logger.info("password_hash_start", password_length=len(password))
        await self.validate_password_strength(password)
        hashed = await self.password_manager.get_password_hash(password)
        logger.info("password_hash_complete", hash_length=len(hashed))
        return hashed

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        trace_id = str(uuid.uuid4())

        logger.info("password_verification_start",
                   trace_id=trace_id,
                   password_length=len(plain_password),
                   hash_length=len(hashed_password))

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    self.password_manager.verify_password,
                    plain_password,
                    hashed_password
                ),
                timeout=5.0
            )

            if result:
                logger.info("password_verification_success", trace_id=trace_id)
            else:
                logger.warning("password_verification_failed", trace_id=trace_id, reason="password_mismatch")

            return result
        except asyncio.TimeoutError:
            logger.error("password_verification_timeout",
                        trace_id=trace_id,
                        timeout_seconds=5,
                        exc_info=True)
            raise
