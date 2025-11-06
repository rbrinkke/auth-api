from datetime import timedelta
from fastapi import Depends
import asyncpg
import uuid
from uuid import UUID
from app.db.connection import get_db_connection
from app.db import procedures
from app.config import Settings, get_settings
from app.core.tokens import TokenHelper
from app.core.exceptions import UserNotFoundError, InvalidTokenError, TokenExpiredError
from app.schemas.auth import TokenResponse
from app.core.logging_config import get_logger
from app.middleware.correlation import correlation_id_var

logger = get_logger(__name__)

class TokenService:
    def __init__(
        self,
        settings: Settings = Depends(get_settings),
        token_helper: TokenHelper = Depends(TokenHelper),
        db: asyncpg.Connection = Depends(get_db_connection)
    ):
        self.settings = settings
        self.token_helper = token_helper
        self.db = db

    def create_access_token(self, user_id: UUID) -> str:
        expires_delta = timedelta(minutes=self.settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        token = self.token_helper.create_token(
            data={"sub": str(user_id), "type": "access"},
            expires_delta=expires_delta
        )
        logger.info("access_token_created",
                   user_id=str(user_id),
                   expires_minutes=self.settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        return token

    async def create_refresh_token(self, user_id: UUID) -> str:
        expires_delta = timedelta(days=self.settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        jti = str(uuid.uuid4())
        token = self.token_helper.create_token(
            data={"sub": str(user_id), "type": "refresh", "jti": jti},
            expires_delta=expires_delta
        )
        await procedures.sp_save_refresh_token(self.db, user_id, token, expires_delta)
        logger.info("refresh_token_created",
                   user_id=str(user_id),
                   jti=jti,
                   expires_days=self.settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        return token

    def create_verification_token(self, user_id: UUID) -> str:
        expires_delta = timedelta(minutes=self.settings.VERIFICATION_TOKEN_EXPIRE_MINUTES)
        token = self.token_helper.create_token(
            data={"sub": str(user_id), "type": "verification"},
            expires_delta=expires_delta
        )
        logger.info("verification_token_created",
                   user_id=str(user_id),
                   expires_minutes=self.settings.VERIFICATION_TOKEN_EXPIRE_MINUTES)
        return token

    def create_password_reset_token(self, email: str) -> str:
        expires_delta = timedelta(minutes=self.settings.RESET_TOKEN_EXPIRE_MINUTES)
        token = self.token_helper.create_token(
            data={"sub": email, "type": "reset"},
            expires_delta=expires_delta
        )
        logger.info("password_reset_token_created",
                   email=email,
                   expires_minutes=self.settings.RESET_TOKEN_EXPIRE_MINUTES)
        return token

    def create_2fa_token(self, user_id: UUID) -> str:
        expires_delta = timedelta(minutes=5)
        token = self.token_helper.create_token(
            data={"sub": str(user_id), "type": "2fa_pre_auth"},
            expires_delta=expires_delta
        )
        logger.info("2fa_token_created",
                   user_id=str(user_id),
                   expires_minutes=5)
        return token

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        logger.info("token_refresh_start")

        payload = self.token_helper.decode_token(refresh_token)

        if payload.get("type") != "refresh":
            logger.warning("token_refresh_failed", reason="invalid_token_type", expected="refresh", got=payload.get("type"))
            raise InvalidTokenError("Invalid token type")

        user_id_str = payload.get("sub")
        user_id = UUID(user_id_str)
        old_jti = payload.get("jti")

        if not await procedures.sp_validate_refresh_token(self.db, user_id, refresh_token):
            logger.warning("token_refresh_failed", reason="token_not_found_or_revoked", user_id=str(user_id), jti=old_jti)
            raise InvalidTokenError("Token not found or revoked")

        await procedures.sp_revoke_refresh_token(self.db, user_id, refresh_token)
        logger.info("old_refresh_token_revoked", user_id=str(user_id), old_jti=old_jti)

        new_access_token = self.create_access_token(user_id)
        new_refresh_token = await self.create_refresh_token(user_id)

        logger.info("token_refresh_complete", user_id=str(user_id))

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )

    def get_user_id_from_token(self, token: str, expected_type: str) -> UUID:
        logger.info("get_user_id_from_token_start", expected_type=expected_type)

        try:
            payload = self.token_helper.decode_token(token)

            if payload.get("type") != expected_type:
                logger.warning("get_user_id_from_token_failed",
                             reason="invalid_token_type",
                             expected=expected_type,
                             got=payload.get("type"))
                raise InvalidTokenError(f"Invalid token type, expected '{expected_type}'")

            user_id = UUID(payload.get("sub"))
            logger.info("get_user_id_from_token_success",
                       user_id=str(user_id),
                       token_type=expected_type)
            return user_id
        except (ValueError, TypeError) as e:
            logger.error("get_user_id_from_token_failed",
                        reason="invalid_subject",
                        error=str(e),
                        exc_info=True)
            raise InvalidTokenError("Invalid subject in token")

    def get_email_from_token(self, token: str, expected_type: str) -> str:
        logger.info("get_email_from_token_start", expected_type=expected_type)

        try:
            payload = self.token_helper.decode_token(token)

            if payload.get("type") != expected_type:
                logger.warning("get_email_from_token_failed",
                             reason="invalid_token_type",
                             expected=expected_type,
                             got=payload.get("type"))
                raise InvalidTokenError(f"Invalid token type, expected '{expected_type}'")

            email = payload.get("sub")
            if not email:
                logger.warning("get_email_from_token_failed", reason="missing_subject")
                raise InvalidTokenError("Invalid subject in token")

            logger.info("get_email_from_token_success",
                       email=email,
                       token_type=expected_type)
            return email
        except Exception as e:
            logger.error("get_email_from_token_failed",
                        error=str(e),
                        exc_info=True)
            raise
