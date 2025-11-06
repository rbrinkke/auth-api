from fastapi import Depends
from sqlalchemy.orm import Session
import redis
from app.db.connection import get_db
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

class AuthService:
    def __init__(
        self,
        db: Session = Depends(get_db),
        redis_client: redis.Redis = Depends(get_redis_client),
        password_service: PasswordService = Depends(PasswordService),
        token_service: TokenService = Depends(TokenService),
        two_factor_service: TwoFactorService = Depends(TwoFactorService)
    ):
        self.db = db
        self.redis_client = redis_client
        self.password_service = password_service
        self.token_service = token_service
        self.two_factor_service = two_factor_service

    def login_user(self, email: str, password: str) -> dict:
        user = procedures.sp_get_user_by_email(self.db, email)

        if not user or not self.password_service.verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        if not user.is_verified:
            raise AccountNotVerifiedError()

        if user.is_2fa_enabled:
            pre_auth_token = self.token_service.create_2fa_token(user.id)
            raise TwoFactorRequiredError(detail=pre_auth_token)

        return self._grant_full_tokens(user.id)

    def login_2fa_challenge(self, request: TwoFactorLoginRequest) -> TokenResponse:
        user_id = self.token_service.get_user_id_from_token(
            request.pre_auth_token,
            "2fa_pre_auth"
        )

        self.two_factor_service.validate_2fa_challenge(user_id, request.code)

        return self._grant_full_tokens(user_id)

    def logout_user(self, refresh_token: str) -> dict:
        try:
            payload = self.token_service.token_helper.decode_token(refresh_token)
            if payload.get("type") == "refresh":
                user_id = int(payload.get("sub"))
                procedures.sp_revoke_refresh_token(self.db, user_id, refresh_token)
        except Exception:
            pass

        return {"message": "Logged out successfully"}

    def _grant_full_tokens(self, user_id: int) -> TokenResponse:
        access_token = self.token_service.create_access_token(user_id)
        refresh_token = self.token_service.create_refresh_token(user_id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

