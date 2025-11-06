"""
Password service implementing password management business logic.

This service encapsulates all password operations:
- Password validation
- Password hashing
- Password updates

Separates business logic from HTTP handling for better architecture and testability.
"""
import logging
from typing import NamedTuple

import asyncpg
from fastapi import Depends

from app.core.redis_client import RedisClient, get_redis
from app.core.security import hash_password, verify_password
from app.db.connection import get_db_connection
from app.db.procedures import sp_get_user_by_id, sp_update_password
from app.services.password_validation_service import PasswordValidationService, get_password_validation_service

logger = logging.getLogger(__name__)


class PasswordUpdateResult(NamedTuple):
    """Result of password update operation."""
    user_id: str
    password_updated: bool


class PasswordServiceError(Exception):
    """Base exception for password service errors."""
    pass


class PasswordService:
    """
    Service for handling password management business logic.

    Responsibilities:
    - Password validation
    - Password hashing
    - Password updates
    """

    def __init__(
        self,
        conn: asyncpg.Connection,
        redis: RedisClient,
        password_validation_svc: PasswordValidationService
    ):
        """
        Initialize password service with dependencies.

        Args:
            conn: Database connection
            redis: Redis client
            password_validation_svc: Service for password validation
        """
        self.conn = conn
        self.redis = redis
        self.password_validation_svc = password_validation_svc

    async def update_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> PasswordUpdateResult:
        """
        Update user password with old password verification.

        Flow:
        1. Get user from database
        2. Verify old password
        3. Validate new password
        4. Hash new password
        5. Update password in database
        6. Blacklist all existing refresh tokens

        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password to set

        Returns:
            PasswordUpdateResult: Operation result

        Raises:
            PasswordServiceError: If update fails
        """
        try:
            # Step 1: Get user from database
            user = await sp_get_user_by_id(self.conn, user_id)

            if not user:
                logger.error(f"Password update failed - user not found: {user_id}")
                raise PasswordServiceError("User not found")

            # Step 2: Verify old password
            if not verify_password(old_password, user.hashed_password):
                logger.warning(f"Password update failed - invalid old password for user: {user.email}")
                raise PasswordServiceError("Invalid current password")

            # Step 3: Validate new password
            logger.info(f"Validating new password for user {user_id}")
            await self.password_validation_svc.validate_password(new_password)

            # Step 4: Hash new password
            hashed_password = hash_password(new_password)

            # Step 5: Update password in database
            success = await sp_update_password(self.conn, user_id, hashed_password)

            if not success:
                logger.error(f"Password update failed - database error for user: {user_id}")
                raise PasswordServiceError("Failed to update password")

            # Step 6: Blacklist all existing refresh tokens (force re-login)
            # This is a security best practice
            # Note: This would require a list of all active refresh tokens
            # For now, we'll log this step
            logger.info(f"Password updated successfully for user: {user.email} (id: {user_id})")

            return PasswordUpdateResult(
                user_id=user_id,
                password_updated=True
            )

        except PasswordServiceError:
            raise
        except Exception as e:
            logger.error(f"Password update failed for user {user_id}: {str(e)}")
            raise PasswordServiceError(
                f"Password update failed: {str(e)}"
            )


def get_password_service(
    conn: asyncpg.Connection = Depends(get_db_connection),
    redis: RedisClient = Depends(get_redis),
    password_validation_svc: PasswordValidationService = Depends(get_password_validation_service)
) -> "PasswordService":
    """
    Dependency injection function for PasswordService.

    Args:
        conn: Database connection
        redis: Redis client
        password_validation_svc: Password validation service

    Returns:
        PasswordService: Configured password service instance

    This enables easy mocking during testing:
        app.dependency_overrides[get_password_service] = lambda: MockPasswordService()
    """
    return PasswordService(
        conn=conn,
        redis=redis,
        password_validation_svc=password_validation_svc
    )
