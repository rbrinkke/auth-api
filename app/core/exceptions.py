# /mnt/d/activity/auth-api/app/core/exceptions.py
class AuthException(Exception):
    """Base exception for authentication errors."""
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(self.detail)

class InvalidCredentialsError(AuthException):
    """Raised when login credentials are invalid."""
    def __init__(self, detail: str = "Incorrect email or password"):
        super().__init__(detail)

class UserAlreadyExistsError(AuthException):
    """Raised when trying to register an existing user."""
    def __init__(self, detail: str = "Email already registered"):
        super().__init__(detail)

class UserNotFoundError(AuthException):
    """Raised when a user is not found."""
    def __init__(self, detail: str = "User not found"):
        super().__init__(detail)

class TokenExpiredError(AuthException):
    """Raised when a token is expired."""
    def __init__(self, detail: str = "Token has expired"):
        super().__init__(detail)

class InvalidTokenError(AuthException):
    """Raised when a token is invalid."""
    def __init__(self, detail: str = "Invalid token"):
        super().__init__(detail)

class VerificationError(AuthException):
    """Raised for account verification errors."""
    pass

class AccountNotVerifiedError(AuthException):
    """Raised when an action requires a verified account."""
    def __init__(self, detail: str = "Account not verified"):
        super().__init__(detail)

class InvalidPasswordError(AuthException):
    """Raised for password validation errors."""
    pass

class TwoFactorRequiredError(AuthException):
    """Raised when 2FA is required but not provided."""
    def __init__(self, detail: str = "2FA token required"):
        super().__init__(detail)

class TwoFactorSetupError(AuthException):
    """Raised during 2FA setup."""
    pass

class TwoFactorVerificationError(AuthException):
    """Raised when 2FA verification fails."""
    def __init__(self, detail: str = "Invalid 2FA code"):
        super().__init__(detail)
