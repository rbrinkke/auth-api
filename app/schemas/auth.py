"""
Pydantic models for authentication endpoints.

IMPORTANT: These are SCHEMA-ONLY models.
- They define data structure
- They do basic type validation (email format, min length, etc.)
- They do NOT contain business logic

Business logic is in the Service Layer (app/services/).
This separation makes the code testable and maintainable.
"""
from typing import Any
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """Request body for user registration.

    Schema-only validation (no business logic):
    - Email must be valid format
    - Password must be string
    - Password minimum length (basic validation only)

    Business logic (strength, breach check) is handled in RegistrationService.
    """
    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (minimum 8 characters, strength validated in service layer)"
    )

    @field_validator("email")
    @classmethod
    def email_to_lowercase(cls, v: str) -> str:
        """Ensure email is stored in lowercase."""
        return v.lower()


class RegisterResponse(BaseModel):
    """Response for successful registration."""
    message: str
    email: str
    user_id: str


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


class VerifyCodeRequest(BaseModel):
    """Request body for verifying a 6-digit code."""
    user_id: str = Field(..., min_length=1, description="User ID")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")


class VerifyCodeResponse(BaseModel):
    """Response for successful code verification."""
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
    user_id: str = None


class ResetPasswordRequest(BaseModel):
    """Request body for resetting password.

    Schema-only validation (no business logic):
    - User ID must be non-empty string
    - Code must be 6-digit
    - Password minimum length (basic validation only)

    Business logic (strength, breach check) is handled in PasswordResetService.
    """
    user_id: str = Field(..., min_length=1, description="User ID")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit password reset code")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (minimum 8 characters, strength validated in service layer)"
    )


class ResetPasswordResponse(BaseModel):
    """Response for successful password reset."""
    message: str


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
