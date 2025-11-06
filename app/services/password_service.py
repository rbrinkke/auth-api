from fastapi import Depends
from app.core.security import PasswordManager
from app.services.password_validation_service import (
    PasswordValidationService, 
    get_password_validation_service,
    PasswordValidationError
)
from app.core.exceptions import InvalidPasswordError

class PasswordService:
    """Geconsolideerde service voor wachtwoordoperaties."""
    
    def __init__(
        self,
        password_manager: PasswordManager = Depends(PasswordManager),
        validation_service: PasswordValidationService = Depends(get_password_validation_service)
    ):
        self.password_manager = password_manager
        self.validation_service = validation_service

    async def validate_password_strength(self, password: str):
        """Valideert wachtwoordsterkte, gooit error indien ongeldig."""
        try:
            await self.validation_service.validate_password(password)
        except PasswordValidationError as e:
            # Vang de specifieke validatie-error op en zet om naar onze core exception
            raise InvalidPasswordError(str(e))

    async def get_password_hash(self, password: str) -> str:
        """Hasht een wachtwoord na validatie."""
        await self.validate_password_strength(password)
        return self.password_manager.get_password_hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifieert een plain wachtwoord tegen een hash."""
        return self.password_manager.verify_password(plain_password, hashed_password)
