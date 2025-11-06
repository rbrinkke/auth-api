"""Rate limiting configuration and utilities."""
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional
from app.config import get_settings

# Global limiter instance
limiter: Optional[Limiter] = None


def init_limiter() -> Limiter:
    """Initialize and return the global limiter instance."""
    global limiter
    if limiter is None:
        limiter = Limiter(key_func=get_remote_address)
    return limiter


def get_limiter() -> Limiter:
    """Get the global limiter instance."""
    global limiter
    if limiter is None:
        limiter = init_limiter()
    return limiter


def get_login_rate_limit() -> str:
    """Get login rate limit string based on config."""
    settings = get_settings()
    return f"{settings.RATE_LIMIT_LOGIN_PER_MINUTE}/minute"


def get_register_rate_limit() -> str:
    """Get register rate limit string based on config."""
    settings = get_settings()
    return f"{settings.RATE_LIMIT_REGISTER_PER_HOUR}/hour"


def get_password_reset_rate_limit() -> str:
    """Get password reset rate limit string based on config."""
    settings = get_settings()
    return f"{settings.RATE_LIMIT_PASSWORD_RESET_PER_5MIN}/5minutes"


def get_verify_code_rate_limit() -> str:
    """Get verify code rate limit string based on config."""
    # Prevent code brute force: 10 attempts per minute
    return "10/minute"


def get_reset_password_rate_limit() -> str:
    """Get reset password (confirm) rate limit string based on config."""
    # Prevent brute force on reset confirmation: 10 attempts per minute
    return "10/minute"
