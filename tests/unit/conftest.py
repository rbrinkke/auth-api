"""
Unit test fixtures.

These fixtures provide mocked dependencies for fast, isolated unit testing.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_connection():
    """
    Mock database connection for unit tests.
    """
    return AsyncMock()


@pytest.fixture
def mock_redis_client():
    """
    Mock Redis client for unit tests.
    """
    mock = AsyncMock()
    mock.set_verification_token = AsyncMock(return_value=True)
    mock.get_user_id_from_verification_token = AsyncMock(return_value=None)
    mock.set_reset_token = AsyncMock(return_value=True)
    mock.get_user_id_from_reset_token = AsyncMock(return_value=None)
    mock.delete_verification_token = AsyncMock(return_value=True)
    mock.delete_reset_token = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_email_service():
    """
    Mock email service for unit tests.
    """
    class MockEmailService:
        def __init__(self):
            self.sent_emails = []
            self.call_count = 0

        async def send_verification_email(self, email: str, token: str) -> bool:
            self.call_count += 1
            self.sent_emails.append({
                "to": email,
                "token": token,
                "type": "verification"
            })
            return True

        async def send_password_reset_email(self, email: str, token: str) -> bool:
            self.call_count += 1
            self.sent_emails.append({
                "to": email,
                "token": token,
                "type": "password_reset"
            })
            return True

        async def send_welcome_email(self, email: str) -> bool:
            self.call_count += 1
            self.sent_emails.append({
                "to": email,
                "type": "welcome"
            })
            return True

        def get_sent_email_count(self) -> int:
            return self.call_count

        def get_last_email(self):
            return self.sent_emails[-1] if self.sent_emails else None

        def reset(self):
            self.sent_emails = []
            self.call_count = 0

    return MockEmailService()


@pytest.fixture
def mock_password_validation_service():
    """
    Mock password validation service for unit tests.
    """
    from app.services.password_validation_service import PasswordValidationError

    class MockPasswordValidationService:
        def __init__(self):
            self.call_count = 0
            self.validated_passwords = []

        async def validate_password(self, password: str) -> dict:
            self.call_count += 1
            self.validated_passwords.append(password)

            # Mock validation logic
            if password == "weak":
                raise PasswordValidationError("Weak password")

            return {
                "password": password,
                "strength": {"score": 4},
                "breach": {"leak_count": 0},
                "overall_passed": True
            }

        def get_call_count(self) -> int:
            return self.call_count

        def get_validated_passwords(self):
            return self.validated_passwords.copy()

        def reset(self):
            self.call_count = 0
            self.validated_passwords = []

    return MockPasswordValidationService()
