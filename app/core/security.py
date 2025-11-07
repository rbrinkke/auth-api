from pwdlib import PasswordHash
from fastapi import Depends
from app.config import get_settings
import asyncio
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class PasswordManager:
    def __init__(self, settings = Depends(get_settings)):
        self.pwd_context = PasswordHash.recommended()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        logger.debug("security_verifying_password", password_length=len(plain_password), hash_length=len(hashed_password))
        result = self.pwd_context.verify(plain_password, hashed_password)
        logger.debug("security_verify_complete", result=result)
        return result

    async def get_password_hash(self, password: str) -> str:
        logger.debug("security_hashing_password", password_length=len(password))
        hashed = await asyncio.to_thread(self.pwd_context.hash, password)
        logger.debug("security_hash_complete", hash_length=len(hashed))
        return hashed
