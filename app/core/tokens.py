# /mnt/d/activity/auth-api/app/core/tokens.py
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends
from app.config import Settings, get_settings
from app.core.exceptions import TokenExpiredError, InvalidTokenError

class TokenHelper:
    """Manages JWT token creation and decoding."""
    
    def __init__(self, settings: Settings = Depends(get_settings)):
        self.settings = settings
        self.SECRET_KEY = settings.SECRET_KEY
        self.ALGORITHM = settings.ALGORITHM

    def create_token(self, data: dict, expires_delta: timedelta) -> str:
        """Creates a JWT token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def decode_token(self, token: str) -> dict:
        """Decodes a JWT token, handling errors."""
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError:
            raise InvalidTokenError("Invalid token")
