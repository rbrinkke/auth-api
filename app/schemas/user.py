"""
Pydantic models for user-related data.

These models define the structure of data passed between
API endpoints and the application logic.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base user model with common fields."""
    email: EmailStr
    
    @field_validator("email")
    @classmethod
    def email_to_lowercase(cls, v: str) -> str:
        """Ensure email is always lowercase."""
        return v.lower()


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password must be at least 8 characters"
    )
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password strength.
        
        Requirements:
        - At least 8 characters
        - Contains at least one letter
        - Contains at least one digit
        """
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserResponse(UserBase):
    """Schema for user data in responses."""
    id: UUID
    is_verified: bool
    is_active: bool
    created_at: datetime
    verified_at: datetime | None = None
    last_login_at: datetime | None = None
    
    model_config = {"from_attributes": True}


class UserInDB(UserResponse):
    """
    Schema for user data with sensitive fields.
    
    This includes the hashed password and should NEVER
    be sent in API responses.
    """
    hashed_password: str
