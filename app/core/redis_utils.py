"""Redis utilities for code storage and verification.

Centralizes the pattern of storing verification codes with opaque tokens,
used across verification, password reset, and login flows.
"""

import secrets
import hmac
from redis import Redis
from uuid import UUID
from typing import Optional
from app.core.logging_config import get_logger

logger = get_logger(__name__)


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
    logger.debug("redis_utils_generating_token", user_id=str(user_id), key_prefix=key_prefix)
    token = secrets.token_hex(16)  # 32-character hex token
    logger.debug("redis_utils_token_generated", user_id=str(user_id), token_length=len(token))
    redis_key = f"{key_prefix}:{token}"
    redis_value = f"{str(user_id)}:{code}"
    logger.debug("redis_utils_storing_redis", user_id=str(user_id), redis_key=redis_key, ttl=ttl)
    redis_client.setex(redis_key, ttl, redis_value)
    logger.debug("redis_utils_stored_successfully", user_id=str(user_id), token_length=len(token))
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
    logger.debug("redis_utils_retrieving_code", token_length=len(token), key_prefix=key_prefix)
    redis_key = f"{key_prefix}:{token}"
    stored_data = redis_client.get(redis_key)

    if not stored_data:
        logger.debug("redis_utils_code_not_found", redis_key=redis_key)
        return None  # Token expired or never existed

    logger.debug("redis_utils_code_found", redis_key=redis_key)
    # Parse stored data (format: "{user_id}:{code}")
    try:
        stored_user_id_str, stored_code = stored_data.split(":", 1)
        logger.debug("redis_utils_data_parsed", user_id=stored_user_id_str)
    except ValueError:
        logger.debug("redis_utils_malformed_data", redis_key=redis_key)
        return None  # Malformed data

    # Constant-time comparison to prevent timing attacks
    logger.debug("redis_utils_comparing_codes", code_length=len(code))
    if not hmac.compare_digest(code, stored_code):
        logger.debug("redis_utils_code_mismatch")
        return None  # Code doesn't match
    logger.debug("redis_utils_code_match")

    try:
        user_uuid = UUID(stored_user_id_str)
        logger.debug("redis_utils_verification_success", user_id=str(user_uuid))
        return user_uuid
    except ValueError:
        logger.debug("redis_utils_invalid_uuid", user_id_str=stored_user_id_str)
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
    logger.debug("redis_utils_deleting_code", token_length=len(token), key_prefix=key_prefix)
    redis_key = f"{key_prefix}:{token}"
    redis_client.delete(redis_key)
    logger.debug("redis_utils_code_deleted", redis_key=redis_key)
