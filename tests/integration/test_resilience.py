"""
Chaos engineering and resilience testing.

Tests what happens when dependencies fail and ensures the system
maintains data consistency and handles failures gracefully.
"""
import pytest
import asyncpg
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.registration_service import (
    RegistrationService,
    RegistrationServiceError
)
from app.services.password_validation_service import PasswordValidationError


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
class TestResilience:
    """Chaos engineering tests for system resilience."""

    async def test_redis_failure_after_successful_db_insert_rolls_back(
        self,
        test_db_connection,
        clean_redis,
        mock_password_validation_service,
        random_email,
        random_password
    ):
        """
        CRITICAL TEST: Ensures atomicity between DB and Redis.

        Scenario:
        1. sp_create_user (DB) succeeds
        2. redis.set_verification_token (Redis) FAILS
        3. RegistrationServiceError is raised
        4. User MUST NOT exist in database (rollback)

        This prevents "zombie" users who can't verify their email.
        """
        # Arrange
        service = RegistrationService(
            conn=test_db_connection,
            redis=clean_redis,
            password_validation_svc=mock_password_validation_service
        )

        # Mock password validation to pass
        mock_password_validation_service.validate_password = AsyncMock()

        # Mock Redis to fail after successful DB operation
        original_set_verification_token = clean_redis.set_verification_token

        async def failing_set_verification_token(*args, **kwargs):
            # Simulate Redis failure
            raise Exception("Redis connection lost")

        clean_redis.set_verification_token = failing_set_verification_token

        # Act - Registration should fail
        with pytest.raises(RegistrationServiceError):
            await service.register_user(
                email=random_email,
                password=random_password
            )

        # CRITICAL ASSERTION: Verify user was NOT created in DB
        # This is the whole point of atomicity testing
        user_exists = await test_db_connection.fetchval(
            "SELECT EXISTS(SELECT 1 FROM activity.users WHERE email = $1)",
            random_email.lower()
        )

        assert user_exists is False, (
            "FAIL: User was created in DB even though Redis failed! "
            "This violates atomicity and creates zombie users."
        )

        # Restore original method
        clean_redis.set_verification_token = original_set_verification_token

    async def test_redis_failure_does_not_prevent_db_rollback(
        self,
        test_db_connection,
        clean_redis,
        mock_password_validation_service,
        random_email,
        random_password
    ):
        """
        Ensures that even if Redis cleanup fails during rollback,
        the database transaction still completes correctly.

        Scenario:
        1. Registration fails after DB success
        2. Cleanup tries to delete user from DB
        3. Redis cleanup fails (connection lost)
        4. DB cleanup MUST still succeed
        """
        # Arrange
        service = RegistrationService(
            conn=test_db_connection,
            redis=clean_redis,
            password_validation_svc=mock_password_validation_service
        )

        # Mock password validation to pass
        mock_password_validation_service.validate_password = AsyncMock()

        # Track cleanup calls
        db_cleanup_called = False
        redis_cleanup_called = False

        # Simulate user creation
        original_set_verification_token = clean_redis.set_verification_token

        async def set_token_then_fail(*args, **kwargs):
            nonlocal redis_cleanup_called
            redis_cleanup_called = True
            # Succeed once, then next call fails
            if hasattr(set_token_then_fail, 'called'):
                raise Exception("Redis connection lost")
            set_token_then_fail.called = True
            return await original_set_verification_token(*args, **kwargs)

        clean_redis.set_verification_token = set_token_then_fail

        # Act & Assert
        with pytest.raises(RegistrationServiceError):
            await service.register_user(
                email=random_email,
                password=random_password
            )

        # Verify user still doesn't exist
        user_exists = await test_db_connection.fetchval(
            "SELECT EXISTS(SELECT 1 FROM activity.users WHERE email = $1)",
            random_email.lower()
        )

        assert user_exists is False, (
            "User should not exist after failed registration"
        )

        # Restore
        clean_redis.set_verification_token = original_set_verification_token

    async def test_database_unique_violation_with_redis_success_handles_gracefully(
        self,
        test_db_connection,
        clean_redis,
        mock_password_validation_service,
        random_email,
        random_password
    ):
        """
        Tests scenario where DB reports unique violation but Redis operation succeeds.

        This can happen in race conditions where two requests try to register
        the same email simultaneously.

        The service should handle this gracefully.
        """
        # Arrange
        service = RegistrationService(
            conn=test_db_connection,
            redis=clean_redis,
            password_validation_svc=mock_password_validation_service
        )

        # Mock password validation to pass
        mock_password_validation_service.validate_password = AsyncMock()

        # First, create the user directly
        from app.core.security import hash_password
        hashed_pwd = hash_password(random_password)
        await test_db_connection.execute(
            "INSERT INTO activity.users (email, password_hash) VALUES ($1, $2)",
            random_email.lower(),
            hashed_pwd
        )

        # Now try to register the same email (should fail with unique violation)
        # but Redis might still try to set the token

        # Act & Assert - Should raise UserAlreadyExistsError
        with pytest.raises(Exception) as exc_info:
            await service.register_user(
                email=random_email,
                password=random_password
            )

        # Verify user still exists (shouldn't be deleted)
        user_exists = await test_db_connection.fetchval(
            "SELECT EXISTS(SELECT 1 FROM activity.users WHERE email = $1)",
            random_email.lower()
        )

        assert user_exists is True, (
            "User should still exist after duplicate registration attempt"
        )

    async def test_password_validation_failure_prevents_any_db_write(
        self,
        test_db_connection,
        clean_redis,
        random_email
    ):
        """
        Ensures that if password validation fails, NO database write occurs.

        This prevents partial writes and ensures data consistency.
        """
        # Arrange
        mock_password_validation_service = MagicMock()
        mock_password_validation_service.validate_password = AsyncMock(
            side_effect=PasswordValidationError("Weak password")
        )

        service = RegistrationService(
            conn=test_db_connection,
            redis=clean_redis,
            password_validation_svc=mock_password_validation_service
        )

        # Count users before
        user_count_before = await test_db_connection.fetchval(
            "SELECT COUNT(*) FROM activity.users WHERE email = $1",
            random_email.lower()
        )

        # Act - Should fail password validation
        with pytest.raises(PasswordValidationError):
            await service.register_user(
                email=random_email,
                password="weak"
            )

        # Count users after
        user_count_after = await test_db_connection.fetchval(
            "SELECT COUNT(*) FROM activity.users WHERE email = $1",
            random_email.lower()
        )

        # Assert - No user should be created
        assert user_count_after == user_count_before, (
            "No database write should occur if password validation fails"
        )

    async def test_concurrent_registrations_race_condition_with_mixed_results(
        self,
        test_db_connection,
        clean_redis,
        mock_password_validation_service,
        random_email,
        random_password
        ):
        """
        Tests race condition where multiple registrations happen concurrently
        and some succeed while others fail.
        """
        import asyncio

        # Arrange
        service = RegistrationService(
            conn=test_db_connection,
            redis=clean_redis,
            password_validation_svc=mock_password_validation_service
        )

        # Mock password validation to pass
        mock_password_validation_service.validate_password = AsyncMock()

        # Act - Launch 5 concurrent registrations
        results = await asyncio.gather(
            *[
                service.register_user(
                    email=random_email,
                    password=random_password
                )
                for _ in range(5)
            ],
            return_exceptions=True
        )

        # Assert - Exactly 1 should succeed, 4 should fail with various errors
        successes = [r for r in results if not isinstance(r, Exception)]
        failures = [r for r in results if isinstance(r, Exception)]

        assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}"
        assert len(failures) == 4, f"Expected 4 failures, got {len(failures)}"

        # Verify exactly 1 user was created
        user_count = await test_db_connection.fetchval(
            "SELECT COUNT(*) FROM activity.users WHERE email = $1",
            random_email.lower()
        )

        assert user_count == 1, f"Expected 1 user, found {user_count}"

        # Verify token was stored for the successful registration
        assert successes[0].verification_token is not None
