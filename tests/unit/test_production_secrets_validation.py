"""Unit tests for production secrets validation.

Tests the validate_production_secrets() function to ensure it properly
detects unsafe development secrets in production mode.
"""
import pytest
from unittest.mock import MagicMock
from app.config import Settings, validate_production_secrets


class TestProductionSecretsValidation:
    """Test suite for production secret validation."""

    def test_validation_skipped_in_debug_mode(self):
        """Validation should be skipped when DEBUG=True (development mode)."""
        # Arrange: Settings with DEBUG=True and unsafe secrets
        settings = MagicMock(spec=Settings)
        settings.DEBUG = True
        settings.JWT_SECRET_KEY = "dev_secret_key_unsafe"
        settings.ENCRYPTION_KEY = "dev_encryption_key_unsafe"
        settings.POSTGRES_PASSWORD = "dev_password_unsafe"
        settings.SERVICE_AUTH_TOKEN = "dev_token_unsafe"

        # Act & Assert: Should NOT raise error in debug mode
        validate_production_secrets(settings)  # No exception expected

    def test_validation_passes_with_secure_secrets(self):
        """Validation should pass when all secrets are secure in production."""
        # Arrange: Production mode with secure secrets
        settings = MagicMock(spec=Settings)
        settings.DEBUG = False
        settings.JWT_SECRET_KEY = "aB3dE5fG7hI9jK1lM2nO4pQ6rS8tU0vW2xY4zA6bC8dE0"
        settings.ENCRYPTION_KEY = "zY9xW7vU5tS3rQ1pO9nM7lK5jI3hG1fE9dC7bA5zA3xW1"
        settings.POSTGRES_PASSWORD = "pG7sQ9lR3dB5nM1vF8hK2jT4wX6yZ0aC9eL1uI5oP7"
        settings.SERVICE_AUTH_TOKEN = "st_9fK2lM4nP6qR8sT0vW2xY4zA6bC8dE0fG2hI4jK6lM8"

        # Act & Assert: Should NOT raise error with secure secrets
        validate_production_secrets(settings)  # No exception expected

    def test_validation_fails_with_dev_pattern_in_jwt_secret(self):
        """Validation should fail when JWT_SECRET_KEY contains 'dev_' pattern."""
        # Arrange: Production mode with unsafe JWT secret
        settings = MagicMock(spec=Settings)
        settings.DEBUG = False
        settings.JWT_SECRET_KEY = "dev_secret_key_change_in_production_min_32_chars_required"
        settings.ENCRYPTION_KEY = "aB3dE5fG7hI9jK1lM2nO4pQ6rS8tU0vW2xY4zA6bC8dE0"
        settings.POSTGRES_PASSWORD = "pG7sQ9lR3dB5nM1vF8hK2jT4wX6yZ0aC9eL1uI5oP7"
        settings.SERVICE_AUTH_TOKEN = "st_9fK2lM4nP6qR8sT0vW2xY4zA6bC8dE0fG2hI4jK6lM8"

        # Act & Assert: Should raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            validate_production_secrets(settings)

        error_message = str(exc_info.value)
        assert "PRODUCTION DEPLOYMENT BLOCKED" in error_message
        assert "JWT_SECRET_KEY" in error_message
        assert "dev_" in error_message

    def test_validation_fails_with_change_in_prod_pattern(self):
        """Validation should fail when secrets contain 'change_in_prod' pattern."""
        # Arrange: Production mode with 'change_in_prod' pattern
        settings = MagicMock(spec=Settings)
        settings.DEBUG = False
        settings.JWT_SECRET_KEY = "aB3dE5fG7hI9jK1lM2nO4pQ6rS8tU0vW2xY4zA6bC8dE0"
        settings.ENCRYPTION_KEY = "aB3dE5fG7hI9jK1lM2nO4pQ6rS8tU0vW2xY4zA6bC8dE0"
        settings.POSTGRES_PASSWORD = "dev_password_change_in_prod"
        settings.SERVICE_AUTH_TOKEN = "st_9fK2lM4nP6qR8sT0vW2xY4zA6bC8dE0fG2hI4jK6lM8"

        # Act & Assert: Should raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            validate_production_secrets(settings)

        error_message = str(exc_info.value)
        assert "PRODUCTION DEPLOYMENT BLOCKED" in error_message
        assert "POSTGRES_PASSWORD" in error_message
        assert "change_in_prod" in error_message

    def test_validation_fails_with_test_pattern(self):
        """Validation should fail when secrets contain 'test_' pattern."""
        # Arrange: Production mode with 'test_' pattern
        settings = MagicMock(spec=Settings)
        settings.DEBUG = False
        settings.JWT_SECRET_KEY = "aB3dE5fG7hI9jK1lM2nO4pQ6rS8tU0vW2xY4zA6bC8dE0"
        settings.ENCRYPTION_KEY = "test_encryption_key_for_testing_purposes_32_chars"
        settings.POSTGRES_PASSWORD = "pG7sQ9lR3dB5nM1vF8hK2jT4wX6yZ0aC9eL1uI5oP7"
        settings.SERVICE_AUTH_TOKEN = "st_9fK2lM4nP6qR8sT0vW2xY4zA6bC8dE0fG2hI4jK6lM8"

        # Act & Assert: Should raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            validate_production_secrets(settings)

        error_message = str(exc_info.value)
        assert "PRODUCTION DEPLOYMENT BLOCKED" in error_message
        assert "ENCRYPTION_KEY" in error_message
        assert "test_" in error_message

    def test_validation_fails_with_password_pattern(self):
        """Validation should fail when secrets contain 'password' pattern."""
        # Arrange: Production mode with 'password' in secret
        settings = MagicMock(spec=Settings)
        settings.DEBUG = False
        settings.JWT_SECRET_KEY = "MyPasswordIsVerySecure123456789012345678901234"
        settings.ENCRYPTION_KEY = "aB3dE5fG7hI9jK1lM2nO4pQ6rS8tU0vW2xY4zA6bC8dE0"
        settings.POSTGRES_PASSWORD = "pG7sQ9lR3dB5nM1vF8hK2jT4wX6yZ0aC9eL1uI5oP7"
        settings.SERVICE_AUTH_TOKEN = "st_9fK2lM4nP6qR8sT0vW2xY4zA6bC8dE0fG2hI4jK6lM8"

        # Act & Assert: Should raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            validate_production_secrets(settings)

        error_message = str(exc_info.value)
        assert "PRODUCTION DEPLOYMENT BLOCKED" in error_message
        assert "JWT_SECRET_KEY" in error_message
        assert "password" in error_message

    def test_validation_fails_with_multiple_unsafe_secrets(self):
        """Validation should detect and report multiple unsafe secrets."""
        # Arrange: Production mode with multiple unsafe secrets
        settings = MagicMock(spec=Settings)
        settings.DEBUG = False
        settings.JWT_SECRET_KEY = "dev_secret_key_change_in_production_min_32_chars_required"
        settings.ENCRYPTION_KEY = "dev_encryption_key_for_2fa_secrets_32_chars_minimum_required"
        settings.POSTGRES_PASSWORD = "dev_password_change_in_prod"
        settings.SERVICE_AUTH_TOKEN = "st_dev_5555555555555555555555555555555555555555"

        # Act & Assert: Should raise RuntimeError with all unsafe secrets listed
        with pytest.raises(RuntimeError) as exc_info:
            validate_production_secrets(settings)

        error_message = str(exc_info.value)
        assert "PRODUCTION DEPLOYMENT BLOCKED" in error_message

        # All four secrets should be detected as unsafe
        assert "JWT_SECRET_KEY" in error_message
        assert "ENCRYPTION_KEY" in error_message
        assert "POSTGRES_PASSWORD" in error_message
        assert "SERVICE_AUTH_TOKEN" in error_message

    def test_error_message_includes_helpful_instructions(self):
        """Error message should include instructions for fixing the issue."""
        # Arrange: Production mode with unsafe secret
        settings = MagicMock(spec=Settings)
        settings.DEBUG = False
        settings.JWT_SECRET_KEY = "dev_secret_key_unsafe_32_chars_minimum_required"
        settings.ENCRYPTION_KEY = "aB3dE5fG7hI9jK1lM2nO4pQ6rS8tU0vW2xY4zA6bC8dE0"
        settings.POSTGRES_PASSWORD = "pG7sQ9lR3dB5nM1vF8hK2jT4wX6yZ0aC9eL1uI5oP7"
        settings.SERVICE_AUTH_TOKEN = "st_9fK2lM4nP6qR8sT0vW2xY4zA6bC8dE0fG2hI4jK6lM8"

        # Act & Assert: Error message should include helpful instructions
        with pytest.raises(RuntimeError) as exc_info:
            validate_production_secrets(settings)

        error_message = str(exc_info.value)
        assert "secrets.token_urlsafe" in error_message
        assert ".env file" in error_message
        assert "Production secrets MUST:" in error_message

    def test_validation_is_case_insensitive(self):
        """Validation should detect unsafe patterns regardless of case."""
        # Arrange: Production mode with uppercase 'DEV_' pattern
        settings = MagicMock(spec=Settings)
        settings.DEBUG = False
        settings.JWT_SECRET_KEY = "DEV_SECRET_KEY_CHANGE_IN_PRODUCTION_MIN_32_CHARS"
        settings.ENCRYPTION_KEY = "aB3dE5fG7hI9jK1lM2nO4pQ6rS8tU0vW2xY4zA6bC8dE0"
        settings.POSTGRES_PASSWORD = "pG7sQ9lR3dB5nM1vF8hK2jT4wX6yZ0aC9eL1uI5oP7"
        settings.SERVICE_AUTH_TOKEN = "st_9fK2lM4nP6qR8sT0vW2xY4zA6bC8dE0fG2hI4jK6lM8"

        # Act & Assert: Should detect uppercase pattern
        with pytest.raises(RuntimeError) as exc_info:
            validate_production_secrets(settings)

        error_message = str(exc_info.value)
        assert "JWT_SECRET_KEY" in error_message

    def test_validation_detects_example_pattern(self):
        """Validation should detect 'example' pattern in secrets."""
        # Arrange: Production mode with 'example' pattern
        settings = MagicMock(spec=Settings)
        settings.DEBUG = False
        settings.JWT_SECRET_KEY = "example_secret_key_for_documentation_32_chars_min"
        settings.ENCRYPTION_KEY = "aB3dE5fG7hI9jK1lM2nO4pQ6rS8tU0vW2xY4zA6bC8dE0"
        settings.POSTGRES_PASSWORD = "pG7sQ9lR3dB5nM1vF8hK2jT4wX6yZ0aC9eL1uI5oP7"
        settings.SERVICE_AUTH_TOKEN = "st_9fK2lM4nP6qR8sT0vW2xY4zA6bC8dE0fG2hI4jK6lM8"

        # Act & Assert: Should detect 'example' pattern
        with pytest.raises(RuntimeError) as exc_info:
            validate_production_secrets(settings)

        error_message = str(exc_info.value)
        assert "JWT_SECRET_KEY" in error_message
        assert "example" in error_message

    def test_secret_preview_is_truncated(self):
        """Secret previews in error messages should be truncated for security."""
        # Arrange: Production mode with unsafe secret
        settings = MagicMock(spec=Settings)
        settings.DEBUG = False
        settings.JWT_SECRET_KEY = "dev_this_is_a_very_long_secret_key_that_should_be_truncated_in_error_message"
        settings.ENCRYPTION_KEY = "aB3dE5fG7hI9jK1lM2nO4pQ6rS8tU0vW2xY4zA6bC8dE0"
        settings.POSTGRES_PASSWORD = "pG7sQ9lR3dB5nM1vF8hK2jT4wX6yZ0aC9eL1uI5oP7"
        settings.SERVICE_AUTH_TOKEN = "st_9fK2lM4nP6qR8sT0vW2xY4zA6bC8dE0fG2hI4jK6lM8"

        # Act & Assert: Preview should be truncated with "..."
        with pytest.raises(RuntimeError) as exc_info:
            validate_production_secrets(settings)

        error_message = str(exc_info.value)
        assert "Preview:" in error_message
        assert "..." in error_message
        # Full secret should NOT be in error message
        assert "that_should_be_truncated_in_error_message" not in error_message
