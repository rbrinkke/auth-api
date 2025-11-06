# /mnt/d/activity/auth-api/app/core/security.py
from passlib.context import CryptContext
from fastapi import Depends
from app.config import Settings, get_settings

class PasswordManager:
    """Manages password hashing and verification."""
    def __init__(self, settings: Settings = Depends(get_settings)):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifies a plain password against a hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hashes a plain password."""
        return self.pwd_context.hash(password)
