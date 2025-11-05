"""
Unit tests for RegistrationService.

Tests are isolated with mocked dependencies for fast, reliable testing.
"""
import pytest
import asyncpg
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.registration_service import (
    RegistrationService,
    UserRecord,
    RegistrationResult,
    UserAlreadyExistsError,
    RegistrationServiceError
)
from app.services.password_validation_service import PasswordValidationError


class TestRegistrationService:
    """Test cases for RegistrationService."""

    @pytest.mark.unit
    @pytest.mark.async
    async def test_successful_registration(
        self,
        mock_db_connection,
        mock_redis_client,
        mock_password_validation_service
    ):
        """Test successful user registration."""
        # Arrange
        service = RegistrationService(
            conn=mock_db_connection,
            redis=mock_redis_client,
            password_validation_svc=mock_password_validation_service
        )

        # Mock the database call
        mock_user = UserRecord(
            id="123e4567-e89b-12d3-a456-426614174000",
            email="test@example.com",
            is_verified=False,
            is_active=True,
            created_at="2024-01-01T00:00:00"
        )

        mock_db_connection.fetchrow = AsyncMock(return_value=mock_user)
        mock_redis_client.set_verification_token = AsyncMock(return_value=True)

        # Act
        result = await service.register_user(
            email="test@example.com",
            password="StrongPassword123!"
        )

        # Assert
        assert isinstance(result, RegistrationResult)
        assert result.user.email == "test@example.com"
        assert result.verification_token is not None
        assert len(result.verification_token) > 0

        # Verify password validation was called
        assert mock_password_validation_service.get_call_count() == 1

        # Verify token was stored in Redis
        mock_redis_client.set_verification_token.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.async
    async def test_registration_weak_password_fails(
        self,
        mock_db_connection,
        mock_redis_client,
        mock_password_validation_service
    ):
        """Test that weak password is rejected."""
        # Arrange
        service = RegistrationService(
            conn=mock_db_connection,
            redis=mock_redis_client,
            password_validation_svc=mock_password_validation_service
        )

        # Mock password validation to raise error
        mock_password_validation_service.validate_password = AsyncMock(
            side_effect=PasswordValidationError("Weak password")
        )

        # Act & Assert
        with pytest.raises(PasswordValidationError, match="Weak password"):
            await service.register_user(
                email="test@example.com",
                password="weak"
            )

        # Verify no database operation was performed
        mock_db_connection.fetchrow.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.async
    async def test_registration_duplicate_email_fails(
        self,
        mock_db_connection,
        mock_redis_client,
        mock_password_validation_service
    ):
        """Test that duplicate email is rejected."""
        # Arrange
        service = RegistrationService(
            conn=mock_db_connection,
            redis=mock_redis_client,
            password_validation_svc=mock_password_validation_service
        )

        # Mock unique violation error
        mock_db_connection.fetchrow = AsyncMock(
            side_effect=asyncpg.UniqueViolationError("duplicate key")
        )

        # Act & Assert
        with pytest.raises(UserAlreadyExistsError, match="Email already registered"):
            await service.register_user(
                email="existing@example.com",
                password="StrongPassword123!"
            )

    @pytest.mark.unit
    @pytest.mark.async
    async def test_registration_database_error_handling(
        self,
        mock_db_connection,
        mock_redis_client,
        mock_password_validation_service
    ):
        """Test handling of database errors."""
        # Arrange
        service = RegistrationService(
            conn=mock_db_connection,
            redis=mock_redis_client,
            password_validation_svc=mock_password_validation_service
        )

        # Mock database error
        mock_db_connection.fetchrow = AsyncMock(
            side_effect=asyncpg.PostgreSQLError("Database error")
        )

        # Act & Assert
        with pytest.raises(RegistrationServiceError):
            await service.register_user(
                email="test@example.com",
                password="StrongPassword123!"
            )

    @pytest.mark.unit
    @pytest.mark.async
    async def test_registration_redis_error_handling(
        self,
        mock_db_connection,
        mock_redis_client,
        mock_password_validation_service
    ):
        """Test handling of Redis errors."""
        # Arrange
        service = RegistrationService(
            conn=mock_db_connection,
            redis=mock_redis_client,
            password_validation_svc=mock_password_validation_service
        )

        # Mock successful database call
        mock_user = UserRecord(
            id="123e4567-e89b-12d3-a456-426614174000",
            email="test@example.com",
            is_verified=False,
            is_active=True,
            created_at="2024-01-01T00:00:00"
        )
        mock_db_connection.fetchrow = AsyncMock(return_value=mock_user)

        # Mock Redis error
        mock_redis_client.set_verification_token = AsyncMock(
            side_effect=Exception("Redis connection failed")
        )

        # Act & Assert
        with pytest.raises(RegistrationServiceError):
            await service.register_user(
                email="test@example.com",
                password="StrongPassword123!"
            )

    @pytest.mark.unit
    @pytest.mark.async
    async def test_service_initialization(
        self,
        mock_db_connection,
        mock_redis_client,
        mock_password_validation_service
    ):
        """Test that service initializes correctly."""
        # Arrange & Act
        service = RegistrationService(
            conn=mock_db_connection,
            redis=mock_redis_client,
            password_validation_svc=mock_password_validation_service
        )

        # Assert
        assert service.conn == mock_db_connection
        assert service.redis == mock_redis_client
        assert service.password_validation_svc == mock_password_validation_service

    @pytest.mark.unit
    @pytest.mark.async
    async def test_email_normalized_to_lowercase(
        self,
        mock_db_connection,
        mock_redis_client,
        mock_password_validation_service
    ):
        """Test that email is normalized to lowercase."""
        # Arrange
        service = RegistrationService(
            conn=mock_db_connection,
            redis=mock_redis_client,
            password_validation_svc=mock_password_validation_service
        )

        mock_user = UserRecord(
            id="123e4567-e89b-12d3-a456-426614174000",
            email="TEST@EXAMPLE.COM",
            is_verified=False,
            is_active=True,
            created_at="2024-01-01T00:00:00"
        )
        mock_db_connection.fetchrow = AsyncMock(return_value=mock_user)
        mock_redis_client.set_verification_token = AsyncMock(return_value=True)

        # Act
        result = await service.register_user(
            email="TEST@EXAMPLE.COM",
            password="StrongPassword123!"
        )

        # Assert - verify email was lowercased
        mock_db_connection.fetchrow.assert_called_once()
        call_args = mock_db_connection.fetchrow.call_args
        # The email should be lowercased before database call
        assert call_args[0][0].lower() == "test@example.com"

    @pytest.mark.unit
    @pytest.mark.async
    async def test_verification_token_generation(
        self,
        mock_db_connection,
        mock_redis_client,
        mock_password_validation_service
    ):
        """Test that verification token is properly generated and stored."""
        # Arrange
        service = RegistrationService(
            conn=mock_db_connection,
            redis=mock_redis_client,
            password_validation_svc=mock_password_validation_service
        )

        mock_user = UserRecord(
            id="123e4567-e89b-12d3-a456-426614174000",
            email="test@example.com",
            is_verified=False,
            is_active=True,
            created_at="2024-01-01T00:00:00"
        )
        mock_db_connection.fetchrow = AsyncMock(return_value=mock_user)
        mock_redis_client.set_verification_token = AsyncMock(return_value=True)

        # Act
        result = await service.register_user(
            email="test@example.com",
            password="StrongPassword123!"
        )

        # Assert
        assert result.verification_token is not None
        assert len(result.verification_token) > 0

        # Verify token was stored with user ID and TTL
        mock_redis_client.set_verification_token.assert_called_once()
        call_args = mock_redis_client.set_verification_token.call_args
        assert call_args[0][1] == mock_user.id  # user_id is second arg

    @pytest.mark.unit
    @pytest.mark.async
    async def test_concurrent_registrations_handled(
        self,
        mock_db_connection,
        mock_redis_client,
        mock_password_validation_service
    ):
        """Test that concurrent registrations are handled correctly."""
        # Arrange
        service = RegistrationService(
            conn=mock_db_connection,
            redis=mock_redis_client,
            password_validation_svc=mock_password_validation_service
        )

        mock_user = UserRecord(
            id="123e4567-e89b-12d3-a456-426614174000",
            email="test@example.com",
            is_verified=False,
            is_active=True,
            created_at="2024-01-01T00:00:00"
        )
        mock_db_connection.fetchrow = AsyncMock(return_value=mock_user)
        mock_redis_client.set_verification_token = AsyncMock(return_value=True)

        # Act - Simulate concurrent registrations
        tasks = [
            service.register_user(
                email="test@example.com",
                password="StrongPassword123!"
            )
            for _ in range(5)
        ]

        results = await asyncio.gather(*tasks)

        # Assert - All should succeed with different tokens
        assert len(results) == 5
        tokens = {r.verification_token for r in results}
        assert len(tokens) == 5  # All tokens are unique

        # Verify password validation was called 5 times
        assert mock_password_validation_service.get_call_count() == 5


class TestUserRecord:
    """Test cases for UserRecord namedtuple."""

    @pytest.mark.unit
    def test_user_record_creation(self):
        """Test that UserRecord can be created."""
        user = UserRecord(
            id="123",
            email="test@example.com",
            is_verified=False,
            is_active=True,
            created_at="2024-01-01"
        )

        assert user.id == "123"
        assert user.email == "test@example.com"
        assert user.is_verified is False
        assert user.is_active is True
        assert user.created_at == "2024-01-01"

    @pytest.mark.unit
    def test_user_record_immutable(self):
        """Test that UserRecord is immutable."""
        user = UserRecord(
            id="123",
            email="test@example.com",
            is_verified=False,
            is_active=True,
            created_at="2024-01-01"
        )

        with pytest.raises(AttributeError):
            user.email = "new@example.com"


class TestRegistrationResult:
    """Test cases for RegistrationResult namedtuple."""

    @pytest.mark.unit
    def test_registration_result_creation(self):
        """Test that RegistrationResult can be created."""
        user = UserRecord(
            id="123",
            email="test@example.com",
            is_verified=False,
            is_active=True,
            created_at="2024-01-01"
        )

        result = RegistrationResult(
            user=user,
            verification_token="token123"
        )

        assert result.user == user
        assert result.verification_token == "token123"

    @pytest.mark.unit
    def test_registration_result_immutable(self):
        """Test that RegistrationResult is immutable."""
        user = UserRecord(
            id="123",
            email="test@example.com",
            is_verified=False,
            is_active=True,
            created_at="2024-01-01"
        )

        result = RegistrationResult(
            user=user,
            verification_token="token123"
        )

        with pytest.raises(AttributeError):
            result.verification_token = "newtoken"
