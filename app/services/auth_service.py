from fastapi import Depends
import asyncpg
import redis
from uuid import UUID

from app.db.connection import get_db_connection
from app.core.utils import generate_verification_code
from app.core.redis_client import get_redis_client
from app.core.logging_config import get_logger
from app.middleware.correlation import correlation_id_var
from app.config import get_settings
from app.db import procedures
from app.core.exceptions import (
    InvalidCredentialsError,
    AccountNotVerifiedError,
    TwoFactorRequiredError,
    TwoFactorVerificationError,
    UserNotFoundError,
    InvalidTokenError
)
from app.services.password_service import PasswordService
from app.services.token_service import TokenService
from app.services.two_factor_service import TwoFactorService
from app.services.email_service import EmailService
from app.schemas.auth import TokenResponse, TwoFactorLoginRequest

logger = get_logger(__name__)

class AuthService:
    def __init__(
        self,
        db: asyncpg.Connection = Depends(get_db_connection),
        redis_client: redis.Redis = Depends(get_redis_client),
        password_service: PasswordService = Depends(PasswordService),
        token_service: TokenService = Depends(TokenService),
        two_factor_service: TwoFactorService = Depends(TwoFactorService),
        email_service: EmailService = Depends(EmailService),
        settings = Depends(get_settings)
    ):
        self.db = db
        self.redis_client = redis_client
        self.password_service = password_service
        self.token_service = token_service
        self.two_factor_service = two_factor_service
        self.email_service = email_service
        self.settings = settings

    async def login_user(self, email: str, password: str, code: str | None = None) -> dict:
        correlation_id = correlation_id_var.get()

        logger.info("login_attempt_start", email=email, has_code=(code is not None))

        user = await procedures.sp_get_user_by_email(self.db, email)

        if not user:
            logger.warning("login_failed_user_not_found", email=email)
            raise InvalidCredentialsError()

        password_ok = await self.password_service.verify_password(password, user.hashed_password)

        if not password_ok:
            logger.warning("login_failed_invalid_password", user_id=str(user.id), email=email)
            raise InvalidCredentialsError()

        if not user.is_verified:
            logger.warning("login_failed_account_not_verified", user_id=str(user.id), email=email)
            raise AccountNotVerifiedError()

        # Step 1: If no code provided, generate and send login code
        if code is None:
            login_code = generate_verification_code()
            redis_key = f"2FA:{user.id}:login"
            self.redis_client.setex(redis_key, 600, login_code)

            await self.email_service.send_2fa_code(
                user.email,
                login_code,
                purpose="login verification"
            )

            logger.info("login_code_sent", user_id=str(user.id), email=user.email)
            return {
                "message": "Login code sent to your email",
                "email": user.email,
                "user_id": str(user.id),
                "requires_code": True,
                "expires_in": 600
            }

        # Step 2: Verify provided code
        redis_key = f"2FA:{user.id}:login"
        stored_code = self.redis_client.get(redis_key)

        if not stored_code:
            logger.warning("login_failed_code_expired", user_id=str(user.id), email=email)
            raise InvalidTokenError("Login code expired or not found")

        stored_code_str = stored_code.decode('utf-8') if isinstance(stored_code, bytes) else stored_code
        if stored_code_str != code:
            logger.warning("login_failed_invalid_code", user_id=str(user.id), email=email)
            raise InvalidTokenError("Invalid login code")

        # Delete used code
        self.redis_client.delete(redis_key)
        logger.info("login_code_verified", user_id=str(user.id), email=email)

        # Step 3: Check 2FA (existing logic)
        if self.settings.TWO_FACTOR_ENABLED:
            user_totp_enabled = self.redis_client.get(f"2FA:{user.id}:totp_enabled")
            if user_totp_enabled == b"true":
                pre_auth_token = self.token_service.create_2fa_token(user.id)
                logger.info("login_requires_2fa", user_id=str(user.id), email=email)
                raise TwoFactorRequiredError(detail=pre_auth_token)

        result = await self._grant_full_tokens(user.id)
        logger.info("login_success", user_id=str(user.id), email=email)

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
                user_id = UUID(payload.get("sub"))
                await procedures.sp_revoke_refresh_token(self.db, user_id, refresh_token)
                logger.info("logout_success", user_id=str(user_id))
        except Exception as e:
            logger.warning("logout_token_revocation_failed", error=str(e))

        return {"message": "Logged out successfully"}

    async def _grant_full_tokens(self, user_id: UUID) -> TokenResponse:
        logger.info("token_grant_start", user_id=str(user_id))

        access_token = self.token_service.create_access_token(user_id)
        logger.info("access_token_created", user_id=str(user_id), token_length=len(access_token))

        refresh_token = await self.token_service.create_refresh_token(user_id)
        logger.info("refresh_token_created", user_id=str(user_id), token_length=len(refresh_token))

        response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

        logger.info("token_grant_complete", user_id=str(user_id))
        return response

