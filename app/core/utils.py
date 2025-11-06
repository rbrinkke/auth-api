"""Utility functions for authentication service."""
import secrets


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
    return ''.join(secrets.choice('0123456789') for _ in range(length))
