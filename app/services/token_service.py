# /mnt/d/activity/auth-api/app/services/token_service.py
from datetime import timedelta
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.connection import get_db
from app.db import procedures
from app.config import Settings, get_settings
from app.core.tokens import TokenHelper
from app.core.exceptions import UserNotFoundError, InvalidTokenError, TokenExpiredError
from app.schemas.auth import TokenResponse

class TokenService:
    """Service for managing token creation and refresh."""
    
    def __init__(
        self,
        settings: Settings = Depends(get_settings),
        token_helper: TokenHelper = Depends(TokenHelper),
        db: Session = Depends(get_db)
    ):
        self.settings = settings
        self.token_helper = token_helper
        self.db = db

    def create_access_token(self, user_id: int) -> str:
        """Creates a new access token for a user."""
        expires_delta = timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return self.token_helper.create_token(
            data={"sub": str(user_id), "type": "access"}, 
            expires_delta=expires_delta
        )

    def create_refresh_token(self, user_id: int) -> str:
        """Creates a new refresh token and stores it."""
        expires_delta = timedelta(days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS)
        token = self.token_helper.create_token(
            data={"sub": str(user_id), "type": "refresh"}, 
            expires_delta=expires_delta
        )
        procedures.sp_save_refresh_token(self.db, user_id, token, expires_delta)
        return token

    def create_verification_token(self, user_id: int) -> str:
        """Creates a one-time verification token."""
        expires_delta = timedelta(minutes=self.settings.VERIFICATION_TOKEN_EXPIRE_MINUTES)
        return self.token_helper.create_token(
            data={"sub": str(user_id), "type": "verification"},
            expires_delta=expires_delta
        )

    def create_password_reset_token(self, email: str) -> str:
        """Creates a one-time password reset token."""
        expires_delta = timedelta(minutes=self.settings.RESET_TOKEN_EXPIRE_MINUTES)
        return self.token_helper.create_token(
            data={"sub": email, "type": "reset"},
            expires_delta=expires_delta
        )

    def create_2fa_token(self, user_id: int) -> str:
        """Creates a short-lived token for 2FA verification step."""
        expires_delta = timedelta(minutes=5)
        return self.token_helper.create_token(
            data={"sub": str(user_id), "type": "2fa_pre_auth"},
            expires_delta=expires_delta
        )

    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Validates a refresh token and issues new tokens."""
        payload = self.token_helper.decode_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise InvalidTokenError("Invalid token type")

        user_id = int(payload.get("sub"))
        
        if not procedures.sp_validate_refresh_token(self.db, user_id, refresh_token):
            raise InvalidTokenError("Token not found or revoked")
        
        # Invalidate old refresh token (making it single-use)
        procedures.sp_revoke_refresh_token(self.db, user_id, refresh_token)
        
        # Issue new tokens
        new_access_token = self.create_access_token(user_id)
        new_refresh_token = self.create_refresh_token(user_id)
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )

    def get_user_id_from_token(self, token: str, expected_type: str) -> int:
        """Decodes a token and validates its type."""
        payload = self.token_helper.decode_token(token)
        
        if payload.get("type") != expected_type:
            raise InvalidTokenError(f"Invalid token type, expected '{expected_type}'")
            
        try:
            user_id = int(payload.get("sub"))
            return user_id
        except (ValueError, TypeError):
            raise InvalidTokenError("Invalid subject in token")

    def get_email_from_token(self, token: str, expected_type: str) -> str:
        """Decodes a token and validates its type, returning email subject."""
        payload = self.token_helper.decode_token(token)
        
        if payload.get("type") != expected_type:
            raise InvalidTokenError(f"Invalid token type, expected '{expected_type}'")

        email = payload.get("sub")
        if not email:
            raise InvalidTokenError("Invalid subject in token")
        return email
