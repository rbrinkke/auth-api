"""
Unit tests for EmailService.

Tests email sending with mocked HTTP client.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.email_service import EmailService


class TestEmailService:
    """Test cases for EmailService."""

    @pytest.mark.unit
    @pytest.mark.async
    async def test_send_email_success(self):
        """Test successful email sending."""
        # Arrange
        service = EmailService()

        # Mock HTTP client
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            result = await service.send_email(
                to="test@example.com",
                template="test_template",
                subject="Test Subject",
                data={"key": "value"}
            )

            # Assert
            assert result is True
            mock_client.post.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.async
    async def test_send_email_failure(self):
        """Test email sending failure."""
        # Arrange
        service = EmailService()

        # Mock HTTP client to return error
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            result = await service.send_email(
                to="test@example.com",
                template="test_template",
                subject="Test Subject",
                data={"key": "value"}
            )

            # Assert
            assert result is False

    @pytest.mark.unit
    @pytest.mark.async
    async def test_send_email_timeout(self):
        """Test email sending timeout."""
        # Arrange
        service = EmailService()

        # Mock HTTP client to timeout
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.TimeoutException("Request timeout")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            result = await service.send_email(
                to="test@example.com",
                template="test_template",
                subject="Test Subject",
                data={"key": "value"}
            )

            # Assert
            assert result is False

    @pytest.mark.unit
    @pytest.mark.async
    async def test_send_verification_email_success(self):
        """Test successful verification email sending."""
        # Arrange
        service = EmailService()

        # Mock send_email
        service.send_email = AsyncMock(return_value=True)

        # Act
        result = await service.send_verification_email(
            email="test@example.com",
            token="verification_token_123"
        )

        # Assert
        assert result is True
        service.send_email.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.async
    async def test_verification_email_content(self):
        """Test that verification email contains correct content."""
        # Arrange
        service = EmailService()

        # Track email calls
        email_calls = []

        async def mock_send_email(to, template, subject, data):
            email_calls.append({
                "to": to,
                "template": template,
                "subject": subject,
                "data": data
            })
            return True

        service.send_email = mock_send_email

        # Act
        await service.send_verification_email(
            email="test@example.com",
            token="token123"
        )

        # Assert - Verify email content
        assert len(email_calls) == 1
        email = email_calls[0]
        assert email["to"] == "test@example.com"
        assert email["template"] == "email_verification"
        assert email["subject"] == "Verify your email address"
        assert "verification_link" in email["data"]
        assert "expires_hours" in email["data"]

    @pytest.mark.unit
    @pytest.mark.async
    async def test_send_password_reset_email_success(self):
        """Test successful password reset email sending."""
        # Arrange
        service = EmailService()

        # Mock send_email
        service.send_email = AsyncMock(return_value=True)

        # Act
        result = await service.send_password_reset_email(
            email="test@example.com",
            token="reset_token_123"
        )

        # Assert
        assert result is True
        service.send_email.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.async
    async def test_password_reset_email_content(self):
        """Test that password reset email contains correct content."""
        # Arrange
        service = EmailService()

        # Track email calls
        email_calls = []

        async def mock_send_email(to, template, subject, data):
            email_calls.append({
                "to": to,
                "template": template,
                "subject": subject,
                "data": data
            })
            return True

        service.send_email = mock_send_email

        # Act
        await service.send_password_reset_email(
            email="test@example.com",
            token="token123"
        )

        # Assert - Verify email content
        assert len(email_calls) == 1
        email = email_calls[0]
        assert email["to"] == "test@example.com"
        assert email["template"] == "password_reset"
        assert email["subject"] == "Reset your password"
        assert "reset_link" in email["data"]
        assert "expires_hours" in email["data"]

    @pytest.mark.unit
    @pytest.mark.async
    async def test_send_welcome_email_success(self):
        """Test successful welcome email sending."""
        # Arrange
        service = EmailService()

        # Mock send_email
        service.send_email = AsyncMock(return_value=True)

        # Act
        result = await service.send_welcome_email(email="test@example.com")

        # Assert
        assert result is True
        service.send_email.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.async
    async def test_welcome_email_content(self):
        """Test that welcome email contains correct content."""
        # Arrange
        service = EmailService()

        # Track email calls
        email_calls = []

        async def mock_send_email(to, template, subject, data):
            email_calls.append({
                "to": to,
                "template": template,
                "subject": subject,
                "data": data
            })
            return True

        service.send_email = mock_send_email

        # Act
        await service.send_welcome_email(email="test@example.com")

        # Assert - Verify email content
        assert len(email_calls) == 1
        email = email_calls[0]
        assert email["to"] == "test@example.com"
        assert email["template"] == "welcome"
        assert email["subject"] == "Welcome to our platform!"
        assert email["data"]["email"] == "test@example.com"

    @pytest.mark.unit
    def test_service_initialization(self):
        """Test that service initializes correctly."""
        # Arrange & Act
        service = EmailService()

        # Assert
        assert service.base_url is not None
        assert service.timeout is not None
        assert service.timeout > 0

    @pytest.mark.unit
    @pytest.mark.async
    async def test_http_error_handling(self):
        """Test handling of HTTP errors."""
        # Arrange
        service = EmailService()

        # Mock HTTP client to return 4xx error
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 404
            mock_response.text = "Not Found"
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            result = await service.send_email(
                to="test@example.com",
                template="test_template",
                subject="Test Subject",
                data={}
            )

            # Assert
            assert result is False

    @pytest.mark.unit
    @pytest.mark.async
    async def test_connection_error_handling(self):
        """Test handling of connection errors."""
        # Arrange
        service = EmailService()

        # Mock HTTP client to raise connection error
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = ConnectionError("Connection failed")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            result = await service.send_email(
                to="test@example.com",
                template="test_template",
                subject="Test Subject",
                data={}
            )

            # Assert
            assert result is False

    @pytest.mark.unit
    @pytest.mark.async
    async def test_timeout_configuration(self):
        """Test that timeout is configured correctly."""
        # Arrange
        service = EmailService()

        # Mock HTTP client
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Act
            await service.send_email(
                to="test@example.com",
                template="test_template",
                subject="Test Subject",
                data={}
            )

            # Assert - Verify timeout was passed to POST
            call_args = mock_client.post.call_args
            assert 'timeout' in call_args.kwargs
            assert call_args.kwargs['timeout'] == service.timeout

    @pytest.mark.unit
    @pytest.mark.async
    async def test_multiple_emails_sequentially(self):
        """Test sending multiple emails sequentially."""
        # Arrange
        service = EmailService()

        # Track email calls
        email_calls = []
        call_count = 0

        async def mock_send_email(to, template, subject, data):
            nonlocal call_count
            call_count += 1
            email_calls.append({"to": to, "template": template})
            return True

        service.send_email = mock_send_email

        # Act - Send multiple emails
        await service.send_verification_email("user1@example.com", "token1")
        await service.send_verification_email("user2@example.com", "token2")
        await service.send_welcome_email("user3@example.com")

        # Assert
        assert call_count == 3
        assert len(email_calls) == 3
        assert email_calls[0]["to"] == "user1@example.com"
        assert email_calls[1]["to"] == "user2@example.com"
        assert email_calls[2]["to"] == "user3@example.com"

    @pytest.mark.unit
    @pytest.mark.async
    async def test_email_template_data_passed_correctly(self):
        """Test that email template data is passed correctly."""
        # Arrange
        service = EmailService()

        # Track data passed
        template_data = []

        async def mock_send_email(to, template, subject, data):
            template_data.append(data)
            return True

        service.send_email = mock_send_email

        # Act
        await service.send_verification_email(
            email="test@example.com",
            token="test_token"
        )

        # Assert
        assert len(template_data) == 1
        data = template_data[0]
        assert data["verification_link"] is not None
        assert data["expires_hours"] is not None
        assert isinstance(data["expires_hours"], int)

    @pytest.mark.unit
    @pytest.mark.async
    async def test_exception_during_send_email(self):
        """Test that exceptions during send are handled gracefully."""
        # Arrange
        service = EmailService()

        # Mock send_email to raise exception
        service.send_email = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        # Act & Assert
        with pytest.raises(Exception):
            await service.send_verification_email(
                email="test@example.com",
                token="token"
            )

    @pytest.mark.unit
    def test_get_email_service_di(self):
        """Test that get_email_service DI function works."""
        # Arrange
        from app.services.email_service import get_email_service

        # Act
        service = get_email_service()

        # Assert
        assert isinstance(service, EmailService)
        assert service.base_url is not None
