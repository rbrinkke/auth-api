class AuthException(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(self.detail)

class InvalidCredentialsError(AuthException):
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(detail)

class UserAlreadyExistsError(AuthException):
    def __init__(self, detail: str = "Email already registered"):
        super().__init__(detail)

class UserNotFoundError(AuthException):
    def __init__(self, detail: str = "User not found"):
        super().__init__(detail)

class TokenExpiredError(AuthException):
    def __init__(self, detail: str = "Token has expired"):
        super().__init__(detail)

class InvalidTokenError(AuthException):
    def __init__(self, detail: str = "Invalid token"):
        super().__init__(detail)

class VerificationError(AuthException):
    pass

class AccountNotVerifiedError(AuthException):
    def __init__(self, detail: str = "Account not verified"):
        super().__init__(detail)

class InvalidPasswordError(AuthException):
    pass

class TwoFactorRequiredError(AuthException):
    def __init__(self, detail: str = "2FA token required"):
        super().__init__(detail)

class TwoFactorSetupError(AuthException):
    pass

class TwoFactorVerificationError(AuthException):
    def __init__(self, detail: str = "Invalid 2FA code"):
        super().__init__(detail)

class RequestEntityTooLargeError(AuthException):
    def __init__(self, detail: str = "Request body too large"):
        super().__init__(detail)
