from fastapi import Depends
import asyncio
import uuid
import logging
from app.core.security import PasswordManager
from app.services.password_validation_service import (
    PasswordValidationService,
    get_password_validation_service,
    PasswordValidationError
)
from app.core.exceptions import InvalidPasswordError

logger = logging.getLogger(__name__)

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
            await self.validation_service.validate_password(password)
        except PasswordValidationError as e:
            raise InvalidPasswordError(str(e))

    async def get_password_hash(self, password: str) -> str:
        await self.validate_password_strength(password)
        return await self.password_manager.get_password_hash(password)

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        trace_id = str(uuid.uuid4())

        logger.debug(f"[{trace_id}] verify_password START password_length={len(plain_password)} hash_length={len(hashed_password)}")
        logger.debug(f"[{trace_id}] asyncio.to_thread DISPATCH_START timeout=5s")

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    self.password_manager.verify_password,
                    plain_password,
                    hashed_password
                ),
                timeout=5.0
            )
            logger.debug(f"[{trace_id}] asyncio.to_thread DISPATCH_END result={result}")
            logger.debug(f"[{trace_id}] verify_password END result={result}")
            return result
        except asyncio.TimeoutError:
            logger.error(f"[{trace_id}] asyncio.to_thread TIMEOUT after 5 seconds!")
            raise
