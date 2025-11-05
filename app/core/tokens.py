"""
JWT token generation and validation.

Access Token: Short-lived (15 min), used for API requests
Refresh Token: Long-lived (30 days), used to get new access tokens
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt
from fastapi import HTTPException, status

from app.config import settings


def create_access_token(user_id: UUID) -> str:
    """
    Create a short-lived JWT access token.
    
    Args:
        user_id: The user's UUID
        
    Returns:
        Encoded JWT string
        
    Payload structure:
        {
            "sub": "user-uuid",
            "exp": timestamp,
            "iat": timestamp,
            "type": "access"
        }
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "type": "access"
    }
    
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )


def create_refresh_token(user_id: UUID) -> tuple[str, str]:
    """
    Create a long-lived refresh token.
    
    Args:
        user_id: The user's UUID
        
    Returns:
        Tuple of (encoded_token, jti)
        jti is the unique token ID used for blacklisting
        
    Payload structure:
        {
            "sub": "user-uuid",
            "exp": timestamp,
            "iat": timestamp,
            "jti": "unique-token-id",
            "type": "refresh"
        }
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.jwt_refresh_token_expire_days)
    
    # Generate unique JTI (JWT ID) for blacklisting
    jti = secrets.token_urlsafe(32)
    
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "jti": jti,
        "type": "refresh"
    }
    
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return token, jti


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: The JWT string to decode
        expected_type: Expected token type ("access" or "refresh")
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid, expired, or wrong type
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Validate token type
        token_type = payload.get("type")
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}",
            )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def get_user_id_from_token(token: str, expected_type: str = "access") -> UUID:
    """
    Extract user ID from a token.
    
    Args:
        token: The JWT string
        expected_type: Expected token type
        
    Returns:
        User UUID
        
    Raises:
        HTTPException: If token is invalid or doesn't contain valid user ID
    """
    payload = decode_token(token, expected_type)
    
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
        )
    
    try:
        return UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
        )


def get_jti_from_refresh_token(token: str) -> str:
    """
    Extract the JTI (JWT ID) from a refresh token.
    
    This is used for token blacklisting during logout and refresh.
    
    Args:
        token: The refresh token JWT string
        
    Returns:
        The jti claim value
        
    Raises:
        HTTPException: If token is invalid or missing jti
    """
    payload = decode_token(token, expected_type="refresh")
    
    jti = payload.get("jti")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing jti claim",
        )
    
    return jti


def generate_verification_token() -> str:
    """
    Generate a cryptographically secure random token for email verification.
    
    Returns:
        URL-safe base64 encoded random string (32 bytes = ~43 chars)
    """
    return secrets.token_urlsafe(32)


def generate_reset_token() -> str:
    """
    Generate a cryptographically secure random token for password reset.
    
    Returns:
        URL-safe base64 encoded random string (32 bytes = ~43 chars)
    """
    return secrets.token_urlsafe(32)
