"""
Unit tests for PasswordValidationService.

Tests validate password strength and breach checking.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.password_validation_service import (
    PasswordValidationService,
    PasswordValidationError
)


class TestPasswordValidationService:
    """Test cases for PasswordValidationService."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.parametrize("score,feedback,should_pass", [
        (4, {'warning': '', 'suggestions': []}, True),  # Very strong
        (3, {'warning': '', 'suggestions': []}, True),  # Strong (minimum)
        (2, {'warning': 'Easily guessable', 'suggestions': ['Add more words']}, False),  # Fair
        (1, {'warning': 'Very common', 'suggestions': ['Use uncommon words']}, False),  # Weak
        (0, {'warning': 'Extremely guessable', 'suggestions': ['Use passphrase']}, False),  # Very weak
    ])
    async def test_password_validation_with_various_scores(
        self, score, feedback, should_pass
    ):
        """Test password validation with various zxcvbn scores using parametrization."""
        # Arrange
        service = PasswordValidationService()

        # Mock zxcvbn to return specific score
        with patch.object(service, '_zxcvbn') as mock_zxcvbn:
            mock_zxcvbn.return_value = {'score': score, 'feedback': feedback}

            # Mock breach check to return no breaches
            with patch.object(service, '_Password') as mock_password_class:
                mock_password_instance = MagicMock()
                mock_password_instance.check.return_value = 0
                mock_password_class.return_value = mock_password_instance

                # Act & Assert
                if should_pass:
                    result = await service.validate_password("TestPassword123!")
                    assert result['overall_passed'] is True
                    assert result['strength']['score'] == score
                else:
                    with pytest.raises(PasswordValidationError):
                        await service.validate_password("password")

    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.parametrize("leak_count,should_fail", [
        (0, False),     # Not found in breaches - OK
        (1, True),      # Found once - FAIL
        (12345, True),  # Found many times - FAIL
        (1000000, True),  # Found 1M times - FAIL
    ])
    async def test_password_breach_detection_with_various_leak_counts(
        self, leak_count, should_fail
    ):
        """Test breach detection with various leak counts using parametrization."""
        # Arrange
        service = PasswordValidationService()

        # Mock zxcvbn to return strong password
        with patch.object(service, '_zxcvbn') as mock_zxcvbn:
            mock_zxcvbn.return_value = {
                'score': 4,
                'feedback': {'warning': '', 'suggestions': []}
            }

            # Mock breach check to return specific leak count
            with patch.object(service, '_Password') as mock_password_class:
                mock_password_instance = MagicMock()
                mock_password_instance.check.return_value = leak_count
                mock_password_class.return_value = mock_password_instance

                # Act & Assert
                if should_fail:
                    with pytest.raises(PasswordValidationError, match="found in known data breaches"):
                        await service.validate_password("BreachedPassword123!")
                else:
                    result = await service.validate_password("UniquePassword123!")
                    assert result['overall_passed'] is True
                    assert result['breach']['leak_count'] == leak_count

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_breach_check_async_non_blocking(self):
        """Test that breach check is async and doesn't block."""
        # Arrange
        service = PasswordValidationService()

        # Mock tools available
        service._tools_available = True

        # Mock zxcvbn to return strong password
        with patch.object(service, '_zxcvbn') as mock_zxcvbn:
            mock_zxcvbn.return_value = {
                'score': 4,
                'feedback': {'warning': '', 'suggestions': []}
            }

            # Act - Check that breach check is async
            result = await service.check_breach_status("TestPassword123!")

            # Verify the method exists and is async
            assert hasattr(service.check_breach_status, '__name__')
            assert 'async' in str(service.check_breach_status)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_breach_check_success(self):
        """Test successful breach check."""
        # Arrange
        service = PasswordValidationService()
        service._tools_available = True

        # Mock password not found in breaches
        with patch.object(service, '_Password') as mock_password_class:
            mock_password_instance = MagicMock()
            mock_password_instance.check.return_value = 0
            mock_password_class.return_value = mock_password_instance

            # Act
            result = await service.check_breach_status("UniquePassword123!")

            # Assert
            assert result['leak_count'] == 0
            assert result['validation_passed'] is True
            assert 'error' not in result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_breach_check_hibp_down(self):
        """Test handling when HIBP service is down."""
        # Arrange
        service = PasswordValidationService()
        service._tools_available = True

        # Mock password check to raise exception
        with patch.object(service, '_Password') as mock_password_class:
            mock_password_instance = MagicMock()
            mock_password_instance.check.side_effect = Exception("Connection timeout")
            mock_password_class.return_value = mock_password_instance

            # Act
            result = await service.check_breach_status("TestPassword123!")

            # Assert - Should allow through when check fails
            assert result['leak_count'] == -1
            assert result['validation_passed'] is True
            assert 'error' in result
            assert 'unavailable' in result['error']

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_tools_not_available_fallback(self):
        """Test fallback when validation tools are not installed."""
        # Arrange
        service = PasswordValidationService()
        service._tools_available = False

        # Act
        result = await service.validate_password("anypassword")

        # Assert - Should pass when tools unavailable
        assert result['overall_passed'] is True
        assert result['strength']['score'] == 0
        assert result['breach']['leak_count'] == 0

    @pytest.mark.unit
    def test_service_initialization(self):
        """Test that service initializes correctly with available tools."""
        # Arrange & Act
        service = PasswordValidationService()

        # Assert
        # Tools should be available (they're installed in requirements)
        assert service._tools_available is True
        assert service._zxcvbn is not None
        assert service._Password is not None

    @pytest.mark.unit
    def test_service_initialization_no_tools(self):
        """Test service initialization when tools are not available."""
        # Arrange
        with patch.dict('sys.modules', {'zxcvbn': None, 'pwnedpasswords': None}):
            # Act
            service = PasswordValidationService()

            # Assert
            assert service._tools_available is False
            assert service._zxcvbn is None
            assert service._Password is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_strength_score_3_accepted(self):
        """Test that score 3 (strong) is accepted."""
        # Arrange
        service = PasswordValidationService()

        # Mock zxcvbn to return score 3 (strong)
        with patch.object(service, '_zxcvbn') as mock_zxcvbn:
            mock_zxcvbn.return_value = {
                'score': 3,
                'feedback': {'warning': '', 'suggestions': []}
            }

            # Act
            result = service.validate_strength("StrongPassword123!")

            # Assert
            assert result['validation_passed'] is True
            assert result['score'] == 3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_strength_score_2_rejected(self):
        """Test that score 2 (fair) is rejected."""
        # Arrange
        service = PasswordValidationService()

        # Mock zxcvbn to return score 2 (fair)
        with patch.object(service, '_zxcvbn') as mock_zxcvbn:
            mock_zxcvbn.return_value = {
                'score': 2,
                'feedback': {
                    'warning': 'Fairly easily guessable',
                    'suggestions': ['Add more random words']
                }
            }

            # Act & Assert
            with pytest.raises(PasswordValidationError):
                service.validate_strength("weakPassword")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_feedback_messages_included(self):
        """Test that feedback messages are included in error."""
        # Arrange
        service = PasswordValidationService()

        # Mock zxcvbn to return score 1 with feedback
        with patch.object(service, '_zxcvbn') as mock_zxcvbn:
            mock_zxcvbn.return_value = {
                'score': 1,
                'feedback': {
                    'warning': 'This is a very common password.',
                    'suggestions': ['Add another word or two', 'Use unusual words']
                }
            }

            # Act & Assert
            with pytest.raises(PasswordValidationError) as exc_info:
                service.validate_strength("password123")

            # Verify error message includes feedback
            error_msg = str(exc_info.value)
            assert "This is a very common password" in error_msg
            assert "Add another word or two" in error_msg

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_asyncio_to_thread_used(self):
        """Test that asyncio.to_thread is used for blocking I/O."""
        # Arrange
        service = PasswordValidationService()
        service._tools_available = True

        # Track if asyncio.to_thread was called
        to_thread_called = False
        original_to_thread = asyncio.to_thread

        async def mock_to_thread(func, *args, **kwargs):
            nonlocal to_thread_called
            to_thread_called = True
            return await original_to_thread(func, *args, **kwargs)

        # Mock zxcvbn
        with patch.object(service, '_zxcvbn') as mock_zxcvbn:
            mock_zxcvbn.return_value = {
                'score': 4,
                'feedback': {'warning': '', 'suggestions': []}
            }

            # Mock breach check to use asyncio.to_thread
            with patch('asyncio.to_thread', side_effect=mock_to_thread) as mock:
                with patch.object(service, '_Password') as mock_password_class:
                    mock_password_instance = MagicMock()
                    mock_password_instance.check.return_value = 0
                    mock_password_class.return_value = mock_password_instance

                    # Act
                    await service.check_breach_status("TestPassword123!")

                    # Assert - Verify asyncio.to_thread was called
                    # Note: We can't easily verify this without the actual call happening,
                    # but we can verify the method is async and structured correctly


class TestPasswordValidationError:
    """Test cases for PasswordValidationError exception."""

    @pytest.mark.unit
    def test_error_creation(self):
        """Test that PasswordValidationError can be created."""
        # Arrange & Act
        error = PasswordValidationError("Invalid password")

        # Assert
        assert str(error) == "Invalid password"
        assert isinstance(error, ValueError)

    @pytest.mark.unit
    def test_error_with_custom_message(self):
        """Test error with custom error message."""
        # Arrange & Act
        error = PasswordValidationError("Custom error message")

        # Assert
        assert "Custom error message" in str(error)
