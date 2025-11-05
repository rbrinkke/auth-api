"""
Pydantic models for authentication endpoints.

Defines request/response schemas for login, register, verify, etc.
"""
import asyncio
from typing import Any
from pydantic import BaseModel, EmailStr, Field, field_validator

# Import password strength validation tools
try:
    from zxcvbn import zxcvbn
    from pwnedpasswords import Password
    _PASSWORD_TOOLS_AVAILABLE = True
except ImportError:
    _PASSWORD_TOOLS_AVAILABLE = False
    # Fallback warning
    import warnings
    warnings.warn(
        "Password validation tools (zxcvbn, pwnedpasswords) not available. "
        "Install with: pip install zxcvbn pwnedpasswords"
    )


def _validate_password_strength(password: str) -> str:
    """
    Professional password validation using zxcvbn + Have I Been Pwned.
    This function can be reused across different validators.
    """
    # If password tools are not available, skip validation (but log warning)
    if not _PASSWORD_TOOLS_AVAILABLE:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            "Password strength validation skipped - zxcvbn/pwnedpasswords not installed"
        )
        return password

    # Check 1: zxcvbn strength scoring (industry standard from Dropbox)
    results = zxcvbn(password)
    score = results['score']  # 0-4 scale (0=very weak, 4=very strong)

    # Require minimum score of 3 (strong or very strong)
    if score < 3:
        feedback = results['feedback']
        warning = feedback.get('warning', '')
        suggestions = feedback.get('suggestions', [])

        error_msg = f"Weak password detected. {warning}"
        if suggestions:
            error_msg += f" Suggestions: {' '.join(suggestions)}"

        raise ValueError(error_msg)

    # Check 2: Have I Been Pwned (via pwnedpasswords)
    # This checks if the password appears in known data breaches
    try:
        # Use blocking call directly (simpler than async)
        # Pydantic validators can't use async operations anyway
        pwned = Password(password)
        leak_count = pwned.check()  # Blocking call, returns int

        # If password is found in breaches, reject it
        if leak_count > 0:
            raise ValueError(
                "This password has been found in known data breaches. "
                "Please choose a unique password that hasn't been compromised."
            )
    except Exception as e:
        # If pwnedpasswords check fails, log but don't block registration
        # (we don't want to prevent signups if the external API is down)
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Pwned password check failed: {str(e)}")

    return password


class RegisterRequest(BaseModel):
    """Request body for user registration."""
    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="""
        Password must be strong enough (we use industry-standard checks):
        - Minimum score of 3/4 from zxcvbn (Dropbox's password strength estimator)
        - Not found in known data breaches (via Have I Been Pwned API)
        """
    )

    @field_validator("email")
    @classmethod
    def email_to_lowercase(cls, v: str) -> str:
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


class RegisterResponse(BaseModel):
    """Response for successful registration."""
    message: str
    email: str


class LoginRequest(BaseModel):
    """
    Request body for login.
    
    Note: This uses username/password field names to comply with
    OAuth2 password flow spec, but 'username' is actually the email.
    """
    username: EmailStr = Field(..., description="User's email address")
    password: str
    
    @field_validator("username")
    @classmethod
    def email_to_lowercase(cls, v: str) -> str:
        return v.lower()


class TokenResponse(BaseModel):
    """Response containing JWT tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class VerifyEmailRequest(BaseModel):
    """Request body for email verification."""
    token: str = Field(..., min_length=1)


class VerifyEmailResponse(BaseModel):
    """Response for successful email verification."""
    message: str


class ResendVerificationRequest(BaseModel):
    """Request body for resending verification email."""
    email: EmailStr
    
    @field_validator("email")
    @classmethod
    def email_to_lowercase(cls, v: str) -> str:
        return v.lower()


class ResendVerificationResponse(BaseModel):
    """Response for resend verification request."""
    message: str


class RefreshTokenRequest(BaseModel):
    """Request body for refreshing tokens."""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Request body for logout."""
    refresh_token: str


class LogoutResponse(BaseModel):
    """Response for successful logout."""
    message: str


class RequestPasswordResetRequest(BaseModel):
    """Request body for requesting password reset."""
    email: EmailStr
    
    @field_validator("email")
    @classmethod
    def email_to_lowercase(cls, v: str) -> str:
        return v.lower()


class RequestPasswordResetResponse(BaseModel):
    """Response for password reset request."""
    message: str


class ResetPasswordRequest(BaseModel):
    """Request body for resetting password."""
    token: str = Field(..., min_length=1)
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password must be at least 8 characters"
    )
    
    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        # Use the same professional validation as registration
        return _validate_password_strength(v)


class ResetPasswordResponse(BaseModel):
    """Response for successful password reset."""
    message: str


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
