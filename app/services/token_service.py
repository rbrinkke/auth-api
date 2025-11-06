"""
Token service implementing token management business logic.

This service encapsulates all token operations:
- Token validation
- Token blacklisting (logout)
- Token refresh with rotation

Separates business logic from HTTP handling for better architecture and testability.
"""
import logging
from typing import NamedTuple

import asyncpg
from fastapi import Depends

from app.core.redis_client import RedisClient, get_redis
from app.core.tokens import (
    create_access_token,
    create_refresh_token,
    get_jti_from_refresh_token,
    get_user_id_from_token
)
from app.db.connection import get_db_connection
from app.db.procedures import sp_get_user_by_id

logger = logging.getLogger(__name__)


class TokenRefreshResult(NamedTuple):
    """Result of token refresh operation."""
    access_token: str
    refresh_token: str
    user_email: str


class TokenServiceError(Exception):
    """Base exception for token service errors."""
    pass


class TokenService:
    """
    Service for handling token management business logic.

    Responsibilities:
    - Token validation
    - Token blacklisting (logout)
    - Token refresh with rotation
    """

    def __init__(
        self,
        conn: asyncpg.Connection,
        redis: RedisClient
    ):
        """
        Initialize token service with dependencies.

        Args:
            conn: Database connection
            redis: Redis client for token storage and blacklisting
        """
        self.conn = conn
        self.redis = redis

    async def refresh_tokens(
        self,
        refresh_token: str
    ) -> TokenRefreshResult:
        """
        Refresh access token with automatic rotation.

        Flow:
        1. Decode and validate refresh token
        2. Extract JTI (JWT ID)
        3. Check if token is blacklisted
        4. Extract user_id
        5. Verify user still exists and is valid
        6. Blacklist the old refresh token (Token Rotation)
        7. Generate new access + refresh tokens

        Args:
            refresh_token: The refresh token to exchange

        Returns:
            TokenRefreshResult: New access and refresh tokens

        Raises:
            TokenServiceError: If refresh fails
        """
        try:
            # Step 1 & 2. Decode token and get JTI
            jti = get_jti_from_refresh_token(refresh_token)

            # Step 3. Check if token is blacklisted
            if await self.redis.is_token_blacklisted(jti):
                logger.warning(f"Attempted use of blacklisted refresh token: {jti}")
                raise TokenServiceError("Token has been revoked")

            # Step 4. Get user_id from token
            user_id = get_user_id_from_token(refresh_token, expected_type="refresh")

            # Step 5. Verify user still exists and is valid
            user = await sp_get_user_by_id(self.conn, user_id)

            if not user:
                logger.error(f"Refresh token for non-existent user: {user_id}")
                raise TokenServiceError("Invalid token")

            if not user.is_active:
                logger.warning(f"Refresh attempt by deactivated user: {user.email}")
                raise TokenServiceError("Account has been deactivated")

            if not user.is_verified:
                logger.warning(f"Refresh attempt by unverified user: {user.email}")
                raise TokenServiceError("Email not verified")

            # Step 6. Blacklist the old refresh token (Token Rotation)
            await self.redis.blacklist_refresh_token(jti)

            # Step 7. Generate new tokens
            new_access_token = create_access_token(user.id)
            new_refresh_token, new_jti = create_refresh_token(user.id)

            logger.info(f"Tokens refreshed for user: {user.email} (id: {user.id})")
            logger.debug(f"Old JTI blacklisted: {jti}, New JTI: {new_jti}")

            return TokenRefreshResult(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                user_email=user.email
            )

        except TokenServiceError:
            raise
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise TokenServiceError(
                f"Token refresh failed: {str(e)}"
            )

    async def logout(
        self,
        refresh_token: str
    ) -> bool:
        """
        Logout user by blacklisting refresh token.

        Args:
            refresh_token: The refresh token to blacklist

        Returns:
            bool: True if logout successful

        Raises:
            TokenServiceError: If logout fails
        """
        try:
            # Get JTI from token
            jti = get_jti_from_refresh_token(refresh_token)

            # Blacklist the token
            await self.redis.blacklist_refresh_token(jti)

            logger.info(f"User logged out, JTI blacklisted: {jti}")

            return True

        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            raise TokenServiceError(
                f"Logout failed: {str(e)}"
            )


def get_token_service(
    conn: asyncpg.Connection = Depends(get_db_connection),
    redis: RedisClient = Depends(get_redis)
) -> TokenService:
    """
    Dependency injection function for TokenService.

    Args:
        conn: Database connection
        redis: Redis client

    Returns:
        TokenService: Configured token service instance

    This enables easy mocking during testing:
        app.dependency_overrides[get_token_service] = lambda: MockTokenService()
    """
    return TokenService(
        conn=conn,
        redis=redis
    )
