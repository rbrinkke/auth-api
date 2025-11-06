"""
Password reset service implementing password reset business logic.

This service handles password reset operations:
- Validate new password strength
- Update user password in database
- Token management

Separates business logic from HTTP handling.
"""
import logging
from typing import NamedTuple

import asyncpg
from fastapi import Depends

from app.core.redis_client import RedisClient, get_redis
from app.core.security import hash_password
from app.core.tokens import generate_reset_token
from app.db.connection import get_db_connection
from app.db.procedures import sp_get_user_by_email, sp_update_password
from app.services.password_validation_service import PasswordValidationService, get_password_validation_service

logger = logging.getLogger(__name__)


def get_password_reset_service(
    conn: asyncpg.Connection = Depends(get_db_connection),
    redis: RedisClient = Depends(get_redis),
    password_validation_svc: PasswordValidationService = Depends(get_password_validation_service)
) -> "PasswordResetService":
    """
    Dependency injection function for PasswordResetService.

    Args:
        conn: Database connection
        redis: Redis client
        password_validation_svc: Password validation service

    Returns:
        PasswordResetService: Configured password reset service instance

    This enables easy mocking during testing:
        app.dependency_overrides[get_password_reset_service] = lambda: MockPasswordResetService()
    """
    return PasswordResetService(
        conn=conn,
        redis=redis,
        password_validation_svc=password_validation_svc
    )


class PasswordResetResult(NamedTuple):
    """Result of password reset operation."""
    user_email: str
    password_updated: bool


class PasswordResetServiceError(Exception):
    """Base exception for password reset service errors."""
    pass


class PasswordResetService:
    """
    Service for handling password reset business logic.

    Responsibilities:
    - Validate new password strength
    - Update user password in database
    - Token validation and management
    """

    def __init__(
        self,
        conn: asyncpg.Connection,
        redis: RedisClient,
        password_validation_svc
    ):
        """
        Initialize password reset service with dependencies.

        Args:
            conn: Database connection
            redis: Redis client for token storage
            password_validation_svc: Service for password validation
        """
        self.conn = conn
        self.redis = redis
        self.password_validation_svc = password_validation_svc

    async def check_user_exists(self, email: str) -> str:
        """
        Check if user exists and return user_id.

        Args:
            email: User's email address

        Returns:
            str: User ID if exists, empty string otherwise
        """
        user = await sp_get_user_by_email(self.conn, email.lower())

        if user:
            logger.info(f"Password reset requested for: {email} (user: {user.id})")
            return str(user.id)
        else:
            logger.info(f"Password reset requested for non-existent email: {email}")
            return ""

    async def reset_password(
        self,
        reset_token: str,
        new_password: str
    ) -> PasswordResetResult:
        """
        Reset user password using reset token.

        Flow:
        1. Validate token
        2. Validate new password
        3. Update password in database
        4. Delete token from Redis

        Args:
            reset_token: Password reset token from email
            new_password: New password to set

        Returns:
            PasswordResetResult: Operation result

        Raises:
            PasswordResetServiceError: If reset fails
        """
        try:
            # Step 1: Get user_id from token
            user_id = await self.redis.get_user_id_from_reset_token(reset_token)

            if not user_id:
                logger.error("Password reset failed - invalid token")
                raise PasswordResetServiceError("Invalid or expired reset token")

            # Step 2: Look up user
            user = await sp_get_user_by_email(self.conn, None)  # We'll use user_id lookup

            # Step 3: Validate new password using service (async)
            logger.info(f"Validating new password for user {user_id}")
            await self.password_validation_svc.validate_password(new_password)

            # Step 4: Hash new password
            hashed_password = hash_password(new_password)

            # Step 5: Update password in database
            success = await sp_update_password(self.conn, user_id, hashed_password)

            if not success:
                logger.error(f"Password reset failed - user not found: {user_id}")
                raise PasswordResetServiceError("Invalid reset token")

            # Step 6: Delete token from Redis (one-time use)
            await self.redis.delete_reset_token(reset_token, user_id)

            logger.info(f"Password reset successful for user {user_id}")

            # Get user email for result
            user_email = "user@example.com"  # We'll need to get this properly

            return PasswordResetResult(
                user_email=user_email,
                password_updated=True
            )

        except PasswordResetServiceError:
            raise
        except Exception as e:
            logger.error(f"Password reset failed: {str(e)}")
            raise PasswordResetServiceError(
                f"Password reset failed: {str(e)}"
            )

    async def reset_password_with_user_id(
        self,
        user_id: str,
        new_password: str
    ) -> PasswordResetResult:
        """
        Reset user password using user_id (code-based flow).

        Flow:
        1. Validate new password
        2. Update password in database

        Args:
            user_id: User ID
            new_password: New password to set

        Returns:
            PasswordResetResult: Operation result

        Raises:
            PasswordResetServiceError: If reset fails
        """
        try:
            # Step 1: Validate new password using service (async)
            logger.info(f"Validating new password for user {user_id}")
            await self.password_validation_svc.validate_password(new_password)

            # Step 2: Hash new password
            hashed_password = hash_password(new_password)

            # Step 3: Update password in database
            success = await sp_update_password(self.conn, user_id, hashed_password)

            if not success:
                logger.error(f"Password reset failed - user not found: {user_id}")
                raise PasswordResetServiceError("User not found")

            logger.info(f"Password reset successful for user {user_id}")

            # Get user email for result
            user_email = "user@example.com"  # We'll need to get this properly

            return PasswordResetResult(
                user_email=user_email,
                password_updated=True
            )

        except PasswordResetServiceError:
            raise
        except Exception as e:
            logger.error(f"Password reset failed: {str(e)}")
            raise PasswordResetServiceError(
                f"Password reset failed: {str(e)}"
            )
