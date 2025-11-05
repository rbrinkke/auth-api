"""
Integration test fixtures.

These fixtures provide real database and Redis connections for testing with real infrastructure.
"""
import asyncio
import os
import asyncpg
import pytest


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
