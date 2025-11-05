"""
Pydantic models for authentication endpoints.

Defines request/response schemas for login, register, verify, etc.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """Request body for user registration."""
    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password must be at least 8 characters"
    )
    
    @field_validator("email")
    @classmethod
    def email_to_lowercase(cls, v: str) -> str:
        return v.lower()
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


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
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class ResetPasswordResponse(BaseModel):
    """Response for successful password reset."""
    message: str


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
