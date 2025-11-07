import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends
from app.config import Settings, get_settings
from app.core.exceptions import TokenExpiredError, InvalidTokenError
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class TokenHelper:
    def __init__(self, settings: Settings = Depends(get_settings)):
        self.settings = settings
        self.SECRET_KEY = settings.JWT_SECRET_KEY
        self.ALGORITHM = settings.JWT_ALGORITHM

    def create_token(self, data: dict, expires_delta: timedelta) -> str:
        logger.debug("token_helper_creating_token", data_keys=list(data.keys()), expires_seconds=expires_delta.total_seconds())
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        logger.debug("token_helper_encoding_jwt", algorithm=self.ALGORITHM)
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        logger.debug("token_helper_token_created", token_length=len(token))
        return token

    def decode_token(self, token: str) -> dict:
        logger.debug("token_helper_decoding_token", token_length=len(token))
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            logger.debug("token_helper_decode_success", payload_keys=list(payload.keys()))
            return payload
        except jwt.ExpiredSignatureError:
            logger.debug("token_helper_token_expired")
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError:
            logger.debug("token_helper_token_invalid")
            raise InvalidTokenError("Invalid token")
