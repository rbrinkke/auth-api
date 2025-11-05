"""
Unit tests for PasswordResetService.

Tests password reset flow with mocked dependencies.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.password_reset_service import (
    PasswordResetService,
    PasswordResetResult,
    PasswordResetServiceError
)
from app.services.password_validation_service import PasswordValidationError


class TestPasswordResetService:
    """Test cases for PasswordResetService."""

    @pytest.mark.unit
    @pytest.mark.async
    async def test_request_password_reset_existing_user(
        self,
        mock_db_connection,
        mock_redis_client,
        mock_password_validation_service
    ):
        """Test password reset request for existing user."""
        # Arrange
        service = PasswordResetService(
            conn=mock_db_connection,
            redis=mock_redis_client,
            password_validation_svc=mock_password_validation_service
        )

        # Mock user found
        mock_user = MagicMock()
        mock_user.id = "123e4567-e89b-12d3-a456-426614174000"
        mock_user.email = "test@example.com"
        mock_db_connection.fetchrow = AsyncMock(return_value=mock_user)
        mock_redis_client.set_reset_token = AsyncMock(return_value=True)

        # Act
        reset_token = await service.request_password_reset("test@example.com")

        # Assert
        assert reset_token is not None
        assert len(reset_token) > 0
        mock_redis_client.set_reset_token.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.async
    async def test_request_password_reset_nonexistent_user(
        self,
        mock_db_connection,
        mock_redis_client,
        mock_password_validation_service
    ):
        """Test password reset request for non-existent user."""
        # Arrange
        service = PasswordResetService(
            conn=mock_db_connection,
            redis=mock_redis_client,
            password_validation_svc=mock_password_validation_service
        )

        # Mock user not found
        mock_db_connection.fetchrow = AsyncMock(return_value=None)

        # Act
        reset_token = await service.request_password_reset("nonexistent@example.com")

        # Assert - Should return empty string for security
        assert reset_token == ""
        mock_redis_client.set_reset_token.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.async
    async def test_reset_password_success(
        self,
        mock_db_connection,
        mock_redis_client,
        mock_password_validation_service
    ):
        """Test successful password reset."""
        # Arrange
        service = PasswordResetService(
            conn=mock_db_connection,
            redis=mock_redis_client,
            password_validation_svc=mock_password_validation_service
        )

        # Mock valid token
        mock_redis_client.get_user_id_from_reset_token = AsyncMock(
            return_value="123e4567-e89b-12d3-a456-426614174000"
        )

        # Mock user found
        mock_user = MagicMock()
        mock_user.id = "123e4567-e89b-12d3-a456-426614174000"
        mock_db_connection.fetchrow = AsyncMock(return_value=mock_user)

        # Mock password update success
        mock_db_connection.fetchval = AsyncMock(return_value=True)
        mock_redis_client.delete_reset_token = AsyncMock(return_value=True)

        # Act
        result = await service.reset_password(
            reset_token="valid_token_123",
            new_password="NewStrongPassword123!"
        )

        # Assert
        assert result.password_updated is True
        mock_redis_client.delete_reset_token.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.async
    @pytest.mark.parametrize("token_value,user_id_result,should_fail", [
        ("valid_token_123", "123e4567-e89b-12d3-a456-426614174000", False),  # Valid token
        ("invalid_token", None, True),  # Invalid token
        ("expired_token", None, True),  # Expired token
        ("malformed_token", None, True),  # Malformed token
        ("", None, True),  # Empty token
    ])
    async def test_reset_password_token_validation(
        self,
        token_value,
        user_id_result,
        should_fail,
        mock_db_connection,
        mock_redis_client,
        mock_password_validation_service
    ):
        """Test password reset token validation using parametrization."""
        # Arrange
        service = PasswordResetService(
            conn=mock_db_connection,
            redis=mock_redis_client,
            password_validation_svc=mock_password_validation_service
        )

        # Mock token lookup result
        mock_redis_client.get_user_id_from_reset_token = AsyncMock(
            return_value=user_id_result
        )

        # Mock password validation to pass
        mock_password_validation_service.validate_password = AsyncMock()

        # Mock successful password update if token is valid
        if not should_fail:
            mock_user = MagicMock()
            mock_user.id = user_id_result
            mock_db_connection.fetchrow = AsyncMock(return_value=mock_user)
            mock_db_connection.fetchval = AsyncMock(return_value=True)
            mock_redis_client.delete_reset_token = AsyncMock(return_value=True)

        # Act & Assert
        if should_fail:
            with pytest.raises(PasswordResetServiceError):
                await service.reset_password(
                    reset_token=token_value,
                    new_password="NewStrongPassword123!"
                )
            # Verify password update was not called
            mock_db_connection.fetchval.assert_not_called()
        else:
            result = await service.reset_password(
                reset_token=token_value,
                new_password="NewStrongPassword123!"
            )
            assert result.password_updated is True

    @pytest.mark.unit
    @pytest.mark.async
    async def test_reset_password_weak_password_rejected(
        self,
        mock_db_connection,
        mock_redis_client,
        mock_password_validation_service
    ):
        """Test that weak passwords are rejected during reset."""
        # Arrange
        service = PasswordResetService(
            conn=mock_db_connection,
            redis=mock_redis_client,
            password_validation_svc=mock_password_validation_service
        )

        # Mock valid token
        mock_redis_client.get_user_id_from_reset_token = AsyncMock(
            return_value="123e4567-e89b-12d3-a456-426614174000"
        )

        # Mock password validation to raise error
        mock_password_validation_service.validate_password = AsyncMock(
            side_effect=PasswordValidationError("Weak password")
        )

        # Act & Assert
        with pytest.raises(PasswordResetServiceError, match="Password validation failed"):
            await service.reset_password(
                reset_token="valid_token",
                new_password="weak"
            )

        # Verify password was not updated
        mock_db_connection.fetchval.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.async
    async def test_reset_password_user_not_found(
        self,
        mock_db_connection,
        mock_redis_client,
        mock_password_validation_service
    ):
        """Test password reset when user is not found."""
        # Arrange
        service = PasswordResetService(
            conn=mock_db_connection,
            redis=mock_redis_client,
            password_validation_svc=mock_password_validation_service
        )

        # Mock valid token but user not found
        mock_redis_client.get_user_id_from_reset_token = AsyncMock(
            return_value="123e4567-e89b-12d3-a456-426614174000"
        )
        mock_db_connection.fetchrow = AsyncMock(return_value=None)
        mock_db_connection.fetchval = AsyncMock(return_value=False)

        # Act & Assert
        with pytest.raises(PasswordResetServiceError, match="Invalid reset token"):
            await service.reset_password(
                reset_token="valid_token",
                new_password="NewPassword123!"
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
        service = PasswordResetService(
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
    @pytest.mark.parametrize("input_email,expected_stored_email", [
        ("TEST@EXAMPLE.COM", "test@example.com"),  # Uppercase
        ("Test@Example.Com", "test@example.com"),  # Mixed case
        ("user@DOMAIN.COM", "user@domain.com"),  # Domain uppercase
        ("USER@DOMAIN.COM", "user@domain.com"),  # All uppercase
    ])
    async def test_email_normalized_to_lowercase(
        self,
        input_email,
        expected_stored_email,
        mock_db_connection,
        mock_redis_client,
        mock_password_validation_service
    ):
        """Test that email is normalized to lowercase using parametrization."""
        # Arrange
        service = PasswordResetService(
            conn=mock_db_connection,
            redis=mock_redis_client,
            password_validation_svc=mock_password_validation_service
        )

        # Mock user found
        mock_user = MagicMock()
        mock_user.id = "123e4567-e89b-12d3-a456-426614174000"
        mock_db_connection.fetchrow = AsyncMock(return_value=mock_user)
        mock_redis_client.set_reset_token = AsyncMock(return_value=True)

        # Act
        reset_token = await service.request_password_reset(input_email)

        # Assert - Verify email was lowercased
        mock_db_connection.fetchrow.assert_called_once()
        call_args = mock_db_connection.fetchrow.call_args
        # The email should be lowercased
        assert expected_stored_email in str(call_args)

    @pytest.mark.unit
    @pytest.mark.async
    async def test_reset_token_stored_with_ttl(
        self,
        mock_db_connection,
        mock_redis_client,
        mock_password_validation_service
    ):
        """Test that reset token is stored with TTL."""
        # Arrange
        service = PasswordResetService(
            conn=mock_db_connection,
            redis=mock_redis_client,
            password_validation_svc=mock_password_validation_service
        )

        # Mock user found
        mock_user = MagicMock()
        mock_user.id = "123e4567-e89b-12d3-a456-426614174000"
        mock_db_connection.fetchrow = AsyncMock(return_value=mock_user)
        mock_redis_client.set_reset_token = AsyncMock(return_value=True)

        # Act
        reset_token = await service.request_password_reset("test@example.com")

        # Assert - Verify token was stored with TTL
        mock_redis_client.set_reset_token.assert_called_once()
        call_args = mock_redis_client.set_reset_token.call_args
        assert call_args[0][1] == mock_user.id  # user_id is second arg

    @pytest.mark.unit
    @pytest.mark.async
    async def test_reset_token_single_use(
        self,
        mock_db_connection,
        mock_redis_client,
        mock_password_validation_service
    ):
        """Test that reset token is deleted after use (single-use)."""
        # Arrange
        service = PasswordResetService(
            conn=mock_db_connection,
            redis=mock_redis_client,
            password_validation_svc=mock_password_validation_service
        )

        # Mock valid token and successful password update
        mock_redis_client.get_user_id_from_reset_token = AsyncMock(
            return_value="123e4567-e89b-12d3-a456-426614174000"
        )
        mock_user = MagicMock()
        mock_user.id = "123e4567-e89b-12d3-a456-426614174000"
        mock_db_connection.fetchrow = AsyncMock(return_value=mock_user)
        mock_db_connection.fetchval = AsyncMock(return_value=True)
        mock_redis_client.delete_reset_token = AsyncMock(return_value=True)

        # Act
        await service.reset_password(
            reset_token="valid_token",
            new_password="NewPassword123!"
        )

        # Assert - Token should be deleted after use
        mock_redis_client.delete_reset_token.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.async
    async def test_database_error_handling(
        self,
        mock_db_connection,
        mock_redis_client,
        mock_password_validation_service
    ):
        """Test handling of database errors."""
        # Arrange
        service = PasswordResetService(
            conn=mock_db_connection,
            redis=mock_redis_client,
            password_validation_svc=mock_password_validation_service
        )

        # Mock database error
        mock_db_connection.fetchrow = AsyncMock(
            side_effect=Exception("Database connection error")
        )

        # Act & Assert
        with pytest.raises(PasswordResetServiceError):
            await service.request_password_reset("test@example.com")

    @pytest.mark.unit
    @pytest.mark.async
    async def test_redis_error_handling(
        self,
        mock_db_connection,
        mock_redis_client,
        mock_password_validation_service
    ):
        """Test handling of Redis errors."""
        # Arrange
        service = PasswordResetService(
            conn=mock_db_connection,
            redis=mock_redis_client,
            password_validation_svc=mock_password_validation_service
        )

        # Mock user found but Redis error
        mock_user = MagicMock()
        mock_user.id = "123e4567-e89b-12d3-a456-426614174000"
        mock_db_connection.fetchrow = AsyncMock(return_value=mock_user)
        mock_redis_client.set_reset_token = AsyncMock(
            side_effect=Exception("Redis connection failed")
        )

        # Act & Assert
        with pytest.raises(PasswordResetServiceError):
            await service.request_password_reset("test@example.com")


class TestPasswordResetResult:
    """Test cases for PasswordResetResult namedtuple."""

    @pytest.mark.unit
    def test_password_reset_result_creation(self):
        """Test that PasswordResetResult can be created."""
        result = PasswordResetResult(
            user_email="test@example.com",
            password_updated=True
        )

        assert result.user_email == "test@example.com"
        assert result.password_updated is True

    @pytest.mark.unit
    def test_password_reset_result_immutable(self):
        """Test that PasswordResetResult is immutable."""
        result = PasswordResetResult(
            user_email="test@example.com",
            password_updated=True
        )

        with pytest.raises(AttributeError):
            result.user_email = "new@example.com"


class TestPasswordResetServiceError:
    """Test cases for PasswordResetServiceError exception."""

    @pytest.mark.unit
    def test_error_creation(self):
        """Test that PasswordResetServiceError can be created."""
        # Arrange & Act
        error = PasswordResetServiceError("Reset failed")

        # Assert
        assert str(error) == "Reset failed"
        assert isinstance(error, Exception)

    @pytest.mark.unit
    def test_error_with_custom_message(self):
        """Test error with custom error message."""
        # Arrange & Act
        error = PasswordResetServiceError("Custom error message")

        # Assert
        assert "Custom error message" in str(error)
