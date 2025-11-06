from pwdlib import PasswordHash
from fastapi import Depends
from app.config import get_settings
import asyncio

class PasswordManager:
    def __init__(self, settings = Depends(get_settings)):
        self.pwd_context = PasswordHash.recommended()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    async def get_password_hash(self, password: str) -> str:
        return await asyncio.to_thread(self.pwd_context.hash, password)
