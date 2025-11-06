from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.connection import get_db
from app.db import procedures
from app.core.exceptions import UserNotFoundError, InvalidTokenError
from app.services.password_service import PasswordService
from app.services.email_service import EmailService
from app.services.token_service import TokenService
from app.schemas.auth import PasswordResetRequest, PasswordResetConfirm

class PasswordResetService:
    """Service voor de wachtwoord reset flow."""
    
    def __init__(
        self,
        db: Session = Depends(get_db),
        password_service: PasswordService = Depends(PasswordService),
        email_service: EmailService = Depends(EmailService),
        token_service: TokenService = Depends(TokenService)
    ):
        self.db = db
        self.password_service = password_service
        self.email_service = email_service
        self.token_service = token_service

    async def request_password_reset(self, request: PasswordResetRequest) -> dict:
        """
        Initieert een wachtwoord reset.
        Stuurt een e-mail als de gebruiker bestaat.
        """
        user = procedures.sp_get_user_by_email(self.db, request.email)
        if user:
            reset_token = self.token_service.create_password_reset_token(user.email)
            self.email_service.send_password_reset_email(user.email, reset_token)
            
        return {"message": "If an account with this email exists, a password reset link has been sent."}

    async def confirm_password_reset(self, request: PasswordResetConfirm) -> dict:
        """Bevestigt een wachtwoord reset en update het wachtwoord."""
        
        email = self.token_service.get_email_from_token(request.token, "reset")
        
        user = procedures.sp_get_user_by_email(self.db, email)
        if not user:
            raise UserNotFoundError()
            
        # Wacht op de (nu async) password hash functie
        hashed_password = await self.password_service.get_password_hash(request.new_password)
        
        procedures.sp_update_user_password(self.db, user.id, hashed_password)
        
        procedures.sp_revoke_all_refresh_tokens(self.db, user.id)
        
        return {"message": "Password updated successfully."}
