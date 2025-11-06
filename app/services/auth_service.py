from fastapi import Depends
import asyncpg
import redis
import uuid
import logging
from app.db.connection import get_db_connection
from app.core.redis_client import get_redis_client
from app.db import procedures
from app.core.exceptions import (
    InvalidCredentialsError,
    AccountNotVerifiedError,
    TwoFactorRequiredError,
    TwoFactorVerificationError,
    UserNotFoundError
)
from app.services.password_service import PasswordService
from app.services.token_service import TokenService
from app.services.two_factor_service import TwoFactorService
from app.schemas.auth import TokenResponse, TwoFactorLoginRequest
from app.config import get_settings

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(
        self,
        db: asyncpg.Connection = Depends(get_db_connection),
        redis_client: redis.Redis = Depends(get_redis_client),
        password_service: PasswordService = Depends(PasswordService),
        token_service: TokenService = Depends(TokenService),
        two_factor_service: TwoFactorService = Depends(TwoFactorService),
        settings = Depends(get_settings)
    ):
        self.db = db
        self.redis_client = redis_client
        self.password_service = password_service
        self.token_service = token_service
        self.two_factor_service = two_factor_service
        self.settings = settings

    async def login_user(self, email: str, password: str) -> dict:
        trace_id = str(uuid.uuid4())

        logger.info(f"[{trace_id}] LOGIN_START email={email}")

        logger.info(f"[{trace_id}] DB_QUERY_START")
        user = await procedures.sp_get_user_by_email(self.db, email)
        logger.info(f"[{trace_id}] DB_QUERY_END user_id={str(user.id) if user else 'None'}")

        if not user:
            logger.info(f"[{trace_id}] USER_NOT_FOUND - raising InvalidCredentialsError")
            raise InvalidCredentialsError()

        logger.info(f"[{trace_id}] PASSWORD_VERIFY_START")
        password_ok = await self.password_service.verify_password(password, user.hashed_password)
        logger.info(f"[{trace_id}] PASSWORD_VERIFY_END result={password_ok}")

        if not password_ok:
            logger.info(f"[{trace_id}] PASSWORD_INVALID - raising InvalidCredentialsError")
            raise InvalidCredentialsError()

        logger.info(f"[{trace_id}] CHECK_VERIFIED_START is_verified={user.is_verified}")
        if not user.is_verified:
            logger.info(f"[{trace_id}] NOT_VERIFIED - raising AccountNotVerifiedError")
            raise AccountNotVerifiedError()

        logger.info(f"[{trace_id}] CHECK_2FA_START two_factor_enabled={getattr(self.settings, 'TWO_FACTOR_ENABLED', False)}")
        if getattr(self.settings, 'TWO_FACTOR_ENABLED', False):
            pre_auth_token = self.token_service.create_2fa_token(user.id)
            logger.info(f"[{trace_id}] 2FA_REQUIRED - raising TwoFactorRequiredError")
            raise TwoFactorRequiredError(detail=pre_auth_token)

        logger.info(f"[{trace_id}] GRANT_TOKENS_START")
        result = await self._grant_full_tokens(user.id)
        logger.info(f"[{trace_id}] GRANT_TOKENS_END success=True")

        return result

    async def login_2fa_challenge(self, request: TwoFactorLoginRequest) -> TokenResponse:
        user_id = self.token_service.get_user_id_from_token(
            request.pre_auth_token,
            "2fa_pre_auth"
        )

        await self.two_factor_service.validate_2fa_challenge(user_id, request.code)

        return await self._grant_full_tokens(user_id)

    async def logout_user(self, refresh_token: str) -> dict:
        try:
            payload = self.token_service.token_helper.decode_token(refresh_token)
            if payload.get("type") == "refresh":
                user_id = int(payload.get("sub"))
                await procedures.sp_revoke_refresh_token(self.db, user_id, refresh_token)
        except Exception:
            pass

        return {"message": "Logged out successfully"}

    async def _grant_full_tokens(self, user_id: str) -> TokenResponse:
        trace_id = str(uuid.uuid4())

        logger.info(f"[{trace_id}] _GRANT_TOKENS_START user_id={user_id}")

        logger.info(f"[{trace_id}] CREATE_ACCESS_TOKEN_START")
        access_token = self.token_service.create_access_token(user_id)
        logger.info(f"[{trace_id}] CREATE_ACCESS_TOKEN_END length={len(access_token)}")

        logger.info(f"[{trace_id}] CREATE_REFRESH_TOKEN_START")
        refresh_token = await self.token_service.create_refresh_token(user_id)
        logger.info(f"[{trace_id}] CREATE_REFRESH_TOKEN_END length={len(refresh_token)}")

        logger.info(f"[{trace_id}] BUILDING_RESPONSE")
        response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

        logger.info(f"[{trace_id}] _GRANT_TOKENS_END success=True")
        return response

