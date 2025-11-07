"""Utility functions for authentication service."""
import secrets
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def generate_verification_code(length: int = 6) -> str:
    """Generate a cryptographically secure numeric verification code.

    Args:
        length: Length of the code (default 6 digits)

    Returns:
        A random numeric code as a string (e.g., "123456")

    Note:
        Uses secrets module (cryptographically strong random) instead of random module.
        Suitable for verification codes, reset codes, and 2FA codes.
    """
    logger.debug("utils_generating_verification_code", length=length)
    code = ''.join(secrets.choice('0123456789') for _ in range(length))
    logger.debug("utils_code_generated", code_length=len(code))
    return code
