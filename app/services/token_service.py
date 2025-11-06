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
        expires_delta = timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return self.token_helper.create_token(
            data={"sub": str(user_id), "type": "access"},
            expires_delta=expires_delta
        )

    async def create_refresh_token(self, user_id: UUID) -> str:
        expires_delta = timedelta(days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS)
        jti = str(uuid.uuid4())
        token = self.token_helper.create_token(
            data={"sub": str(user_id), "type": "refresh", "jti": jti},
            expires_delta=expires_delta
        )
        await procedures.sp_save_refresh_token(self.db, user_id, token, expires_delta)
        return token

    def create_verification_token(self, user_id: UUID) -> str:
        expires_delta = timedelta(minutes=self.settings.VERIFICATION_TOKEN_EXPIRE_MINUTES)
        return self.token_helper.create_token(
            data={"sub": str(user_id), "type": "verification"},
            expires_delta=expires_delta
        )

    def create_password_reset_token(self, email: str) -> str:
        expires_delta = timedelta(minutes=self.settings.RESET_TOKEN_EXPIRE_MINUTES)
        return self.token_helper.create_token(
            data={"sub": email, "type": "reset"},
            expires_delta=expires_delta
        )

    def create_2fa_token(self, user_id: UUID) -> str:
        expires_delta = timedelta(minutes=5)
        return self.token_helper.create_token(
            data={"sub": str(user_id), "type": "2fa_pre_auth"},
            expires_delta=expires_delta
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        payload = self.token_helper.decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise InvalidTokenError("Invalid token type")

        user_id = payload.get("sub")

        if not await procedures.sp_validate_refresh_token(self.db, user_id, refresh_token):
            raise InvalidTokenError("Token not found or revoked")

        await procedures.sp_revoke_refresh_token(self.db, user_id, refresh_token)

        new_access_token = self.create_access_token(user_id)
        new_refresh_token = await self.create_refresh_token(user_id)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )

    def get_user_id_from_token(self, token: str, expected_type: str) -> UUID:
        payload = self.token_helper.decode_token(token)

        if payload.get("type") != expected_type:
            raise InvalidTokenError(f"Invalid token type, expected '{expected_type}'")

        try:
            user_id = UUID(payload.get("sub"))
            return user_id
        except (ValueError, TypeError):
            raise InvalidTokenError("Invalid subject in token")

    def get_email_from_token(self, token: str, expected_type: str) -> str:
        payload = self.token_helper.decode_token(token)

        if payload.get("type") != expected_type:
            raise InvalidTokenError(f"Invalid token type, expected '{expected_type}'")

        email = payload.get("sub")
        if not email:
            raise InvalidTokenError("Invalid subject in token")
        return email
