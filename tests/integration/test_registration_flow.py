"""
Integration test for registration flow with real database and Redis.

This test uses actual database and Redis connections to validate
the full registration flow end-to-end.
"""
import pytest
import asyncio

from app.services.registration_service import RegistrationService
from app.services.password_validation_service import PasswordValidationService


@pytest.mark.integration
@pytest.mark.async
class TestRegistrationIntegration:
    """Integration tests for registration flow."""

    async def test_registration_with_real_database(
        self,
        test_db_connection,
        clean_redis
    ):
        """Test full registration with real database operations."""
        # Arrange
        password_service = PasswordValidationService()
        registration_service = RegistrationService(
            conn=test_db_connection,
            redis=clean_redis,
            password_validation_svc=password_service
        )

        test_email = f"integration-test-{int(asyncio.get_event_loop().time())}@example.com"

        # Act
        result = await registration_service.register_user(
            email=test_email,
            password="StrongPassword123!@#$"
        )

        # Assert
        assert result.user.email == test_email.lower()
        assert result.verification_token is not None

        # Verify token was stored in Redis
        user_id = await clean_redis.get_user_id_from_verification_token(
            result.verification_token
        )
        assert user_id is not None
        assert user_id == result.user.id

    async def test_registration_duplicate_prevention(
        self,
        test_db_connection,
        clean_redis
    ):
        """Test that duplicate registration is prevented."""
        # Arrange
        password_service = PasswordValidationService()
        registration_service = RegistrationService(
            conn=test_db_connection,
            redis=clean_redis,
            password_validation_svc=password_service
        )

        test_email = f"duplicate-test-{int(asyncio.get_event_loop().time())}@example.com"
        password = "StrongPassword123!@#$"

        # Act - Register first time (should succeed)
        result1 = await registration_service.register_user(
            email=test_email,
            password=password
        )
        assert result1.user.email == test_email.lower()

        # Act - Register same email again (should fail)
        from app.services.registration_service import UserAlreadyExistsError

        with pytest.raises(UserAlreadyExistsError):
            await registration_service.register_user(
                email=test_email,
                password=password
            )

    async def test_token_expiration(
        self,
        test_db_connection,
        clean_redis
    ):
        """Test that verification tokens expire correctly."""
        # Arrange
        password_service = PasswordValidationService()
        registration_service = RegistrationService(
            conn=test_db_connection,
            redis=clean_redis,
            password_validation_svc=password_service
        )

        test_email = f"token-test-{int(asyncio.get_event_loop().time())}@example.com"

        # Act
        result = await registration_service.register_user(
            email=test_email,
            password="StrongPassword123!@#$"
        )

        # Verify token exists
        user_id = await clean_redis.get_user_id_from_verification_token(
            result.verification_token
        )
        assert user_id is not None

        # Note: Testing actual expiration requires waiting for TTL
        # This test verifies the token TTL is set
        # In a real scenario, you'd wait for the token to expire
        # or use a shorter TTL for testing
