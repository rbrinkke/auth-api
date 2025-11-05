"""
Pytest fixtures for database testing.
"""
import asyncio
import os
import asyncpg
import pytest
from unittest.mock import AsyncMock
from typing import AsyncGenerator, Generator


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_pool():
    """
    Create a connection pool to the test database.
    This is session-scoped and shared across all tests.
    """
    # Use test database connection string
    conn_str = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://activity_user:dev_password_change_in_prod@localhost:5433/activitydb"
    )

    # Create connection pool
    pool = await asyncpg.create_pool(
        conn_str,
        min_size=1,
        max_size=10,
        command_timeout=60
    )

    yield pool

    # Cleanup
    await pool.close()


@pytest.fixture
async def test_db_connection(test_db_pool):
    """
    Provide a database connection for a test.
    Each test gets a fresh connection from the pool.
    """
    async with test_db_pool.acquire() as conn:
        # Start a transaction for test isolation
        async with conn.transaction():
            yield conn
            # Transaction will rollback on exit


@pytest.fixture(scope="session")
async def test_redis_client():
    """
    Create a Redis client for testing.
    Session-scoped.
    """
    from app.core.redis_client import RedisClient

    redis = RedisClient(
        host=os.getenv("TEST_REDIS_HOST", "localhost"),
        port=int(os.getenv("TEST_REDIS_PORT", "6379")),
        db=int(os.getenv("TEST_REDIS_DB", "1"))  # Use db 1 for tests
    )

    await redis.connect()

    yield redis

    # Cleanup: flush test database
    try:
        await redis.client.flushdb()
    except Exception:
        pass
    await redis.disconnect()


@pytest.fixture
async def clean_redis(test_redis_client):
    """
    Ensure Redis is clean before each test.
    """
    try:
        await test_redis_client.client.flushdb()
    except Exception:
        pass
    yield test_redis_client


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
    from app.services.password_validation_service import PasswordValidationService, PasswordValidationError

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
