from typing import Any
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
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
        return v.lower()


class RegisterResponse(BaseModel):
    message: str
    email: str
    user_id: str


class LoginRequest(BaseModel):
    username: EmailStr = Field(..., description="User's email address")
    password: str

    @field_validator("username")
    @classmethod
    def email_to_lowercase(cls, v: str) -> str:
        return v.lower()


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=1)


class VerifyEmailResponse(BaseModel):
    message: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def email_to_lowercase(cls, v: str) -> str:
        return v.lower()


class ResendVerificationResponse(BaseModel):
    message: str


class VerifyCodeRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="User ID")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")


class VerifyCodeResponse(BaseModel):
    message: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class LogoutResponse(BaseModel):
    message: str


class RequestPasswordResetRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def email_to_lowercase(cls, v: str) -> str:
        return v.lower()


class RequestPasswordResetResponse(BaseModel):
    message: str
    user_id: str = None


class ResetPasswordRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="User ID")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit password reset code")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (minimum 8 characters, strength validated in service layer)"
    )


class ResetPasswordResponse(BaseModel):
    message: str


class VerifyTempCodeRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="User ID")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit code")
    purpose: str = Field(..., description="Purpose: 'verify', 'reset', etc.")


class VerifyTempCodeResponse(BaseModel):
    message: str
    verified: bool = True


class MessageResponse(BaseModel):
    message: str
