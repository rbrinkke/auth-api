from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.connection import get_db
from app.db import procedures
from app.core.exceptions import UserAlreadyExistsError
from app.services.password_service import PasswordService
from app.services.email_service import EmailService
from app.services.token_service import TokenService
from app.schemas.user import UserCreate

class RegistrationService:
    """Service voor gebruikersregistratie en verificatie."""
    
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

    async def register_user(self, user: UserCreate) -> dict:
        """Registreert een nieuwe gebruiker en stuurt verificatie e-mail."""
        
        existing_user = procedures.sp_get_user_by_email(self.db, user.email)
        if existing_user:
            raise UserAlreadyExistsError()
            
        # Wacht op de (nu async) password hash functie
        hashed_password = await self.password_service.get_password_hash(user.password)
        
        new_user = procedures.sp_create_user(self.db, user.email, hashed_password)
        
        verification_token = self.token_service.create_verification_token(new_user.id)
        
        self.email_service.send_verification_email(new_user.email, verification_token)
        
        return {"message": "Registration successful. Please check your email to verify your account."}

    async def verify_account(self, token: str) -> dict:
        """Verifieert een gebruikersaccount met de opgegeven token."""
        user_id = self.token_service.get_user_id_from_token(token, "verification")
        procedures.sp_verify_user(self.db, user_id)
        return {"message": "Account verified successfully."}
