"""Redis utilities for code storage and verification.

Centralizes the pattern of storing verification codes with opaque tokens,
used across verification, password reset, and login flows.
"""

import secrets
import hmac
from redis import Redis
from uuid import UUID
from typing import Optional


def store_code_with_token(
    redis_client: Redis,
    user_id: UUID,
    code: str,
    key_prefix: str,
    ttl: int = 600
) -> str:
    """Store verification code with opaque token, return token.

    Creates an opaque token and stores a mapping:
      {key_prefix}:{token} → {user_id}:{code}

    This prevents account takeover by UUID enumeration. The token
    is returned to the client and must be provided to verify the code.

    Args:
        redis_client: Redis client instance
        user_id: UUID of the user
        code: Verification code (numeric string)
        key_prefix: Redis key prefix (e.g., "verify_token", "reset_token")
        ttl: Time to live in seconds (default 10 minutes)

    Returns:
        Opaque token (32-character hex string) to send to client
    """
    token = secrets.token_hex(16)  # 32-character hex token
    redis_key = f"{key_prefix}:{token}"
    redis_value = f"{str(user_id)}:{code}"
    redis_client.setex(redis_key, ttl, redis_value)
    return token


def retrieve_and_verify_code(
    redis_client: Redis,
    token: str,
    code: str,
    key_prefix: str
) -> Optional[UUID]:
    """Verify code with token, return user_id if valid.

    Retrieves stored code from Redis using the token, verifies it matches
    the provided code (using constant-time comparison), and returns the
    associated user_id.

    Args:
        redis_client: Redis client instance
        token: Opaque token from client
        code: Verification code from client
        key_prefix: Redis key prefix used in store_code_with_token

    Returns:
        UUID of the user if code is valid, None if expired/invalid
    """
    redis_key = f"{key_prefix}:{token}"
    stored_data = redis_client.get(redis_key)

    if not stored_data:
        return None  # Token expired or never existed

    # Parse stored data (format: "{user_id}:{code}")
    try:
        stored_user_id_str, stored_code = stored_data.split(":", 1)
    except ValueError:
        return None  # Malformed data

    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(code, stored_code):
        return None  # Code doesn't match

    try:
        return UUID(stored_user_id_str)
    except ValueError:
        return None  # Invalid UUID format


def delete_code(
    redis_client: Redis,
    token: str,
    key_prefix: str
) -> None:
    """Delete verification code after successful verification.

    Args:
        redis_client: Redis client instance
        token: Opaque token used in store_code_with_token
        key_prefix: Redis key prefix used in store_code_with_token
    """
    redis_key = f"{key_prefix}:{token}"
    redis_client.delete(redis_key)
