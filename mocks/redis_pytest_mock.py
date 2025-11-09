"""
Pytest fixtures for mocking Redis client.

Provides fixtures and utilities for mocking Redis operations in unit tests
without requiring a Redis server or HTTP mock server.

Usage:
    # In conftest.py or test file
    from mocks.redis_pytest_mock import mock_redis_client

    @pytest.mark.asyncio
    async def test_token_storage(mock_redis_client):
        # Use mock Redis client
        mock_redis_client.setex("token:abc", 600, "user:123")
        value = mock_redis_client.get("token:abc")
        assert value == "user:123"
"""

import pytest
import time
from typing import Dict, Optional
from unittest.mock import Mock


class MockRedisClient:
    """
    Mock Redis client with TTL simulation.

    Provides in-memory implementation of Redis operations used in the auth API.
    """

    def __init__(self):
        """Initialize mock Redis client."""
        self._storage: Dict[str, tuple[str, Optional[float]]] = {}
        # Format: {key: (value, expires_at)}

    def _is_expired(self, key: str) -> bool:
        """Check if a key has expired."""
        if key not in self._storage:
            return True

        value, expires_at = self._storage[key]
        if expires_at is None:
            return False

        return time.time() >= expires_at

    def _cleanup_expired(self):
        """Remove expired keys."""
        expired = [key for key in self._storage if self._is_expired(key)]
        for key in expired:
            del self._storage[key]

    def set(self, key: str, value: str) -> bool:
        """
        SET operation - set key to value without expiration.

        Args:
            key: Redis key
            value: Value to store

        Returns:
            True on success
        """
        self._storage[key] = (value, None)
        return True

    def setex(self, key: str, seconds: int, value: str) -> bool:
        """
        SETEX operation - set key to value with expiration.

        Args:
            key: Redis key
            seconds: TTL in seconds
            value: Value to store

        Returns:
            True on success
        """
        expires_at = time.time() + seconds
        self._storage[key] = (value, expires_at)
        return True

    def get(self, key: str) -> Optional[str]:
        """
        GET operation - get value of key.

        Args:
            key: Redis key

        Returns:
            Value if key exists and not expired, None otherwise
        """
        self._cleanup_expired()

        if key not in self._storage:
            return None

        if self._is_expired(key):
            del self._storage[key]
            return None

        value, _ = self._storage[key]
        return value

    def delete(self, key: str) -> int:
        """
        DELETE operation - delete a key.

        Args:
            key: Redis key to delete

        Returns:
            1 if key was deleted, 0 if key didn't exist
        """
        if key in self._storage:
            del self._storage[key]
            return 1
        return 0

    def exists(self, key: str) -> int:
        """
        EXISTS operation - check if key exists.

        Args:
            key: Redis key to check

        Returns:
            1 if key exists, 0 otherwise
        """
        self._cleanup_expired()
        return 1 if (key in self._storage and not self._is_expired(key)) else 0

    def ttl(self, key: str) -> int:
        """
        TTL operation - get remaining time to live.

        Args:
            key: Redis key to check

        Returns:
            Seconds until expiration, -1 if no expiry, -2 if doesn't exist
        """
        self._cleanup_expired()

        if key not in self._storage:
            return -2

        if self._is_expired(key):
            del self._storage[key]
            return -2

        value, expires_at = self._storage[key]
        if expires_at is None:
            return -1

        return int(expires_at - time.time())

    def keys(self, pattern: str = "*") -> list[str]:
        """
        KEYS operation - find all keys matching pattern.

        Args:
            pattern: Key pattern (* for wildcard)

        Returns:
            List of matching keys
        """
        self._cleanup_expired()

        all_keys = list(self._storage.keys())

        if pattern == "*":
            return all_keys

        # Simple pattern matching
        import re
        regex_pattern = pattern.replace("*", ".*").replace("?", ".")
        regex = re.compile(f"^{regex_pattern}$")
        return [key for key in all_keys if regex.match(key)]

    def flushdb(self) -> bool:
        """
        FLUSHDB operation - clear all keys.

        Returns:
            True
        """
        self._storage.clear()
        return True

    def clear(self):
        """Alias for flushdb() for test isolation."""
        self.flushdb()


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture
def mock_redis_client():
    """
    Mock Redis client for unit tests.

    Returns a MockRedisClient instance with full TTL simulation.
    Automatically clears between tests.

    Example:
        def test_token_storage(mock_redis_client):
            mock_redis_client.setex("token:abc", 600, "user_id:123")
            value = mock_redis_client.get("token:abc")
            assert value == "user_id:123"
    """
    client = MockRedisClient()
    yield client
    client.clear()


@pytest.fixture
def mock_redis_with_data():
    """
    Mock Redis client pre-populated with test data.

    Use this when you need some initial data in Redis.

    Example:
        def test_with_existing_data(mock_redis_with_data):
            # Pre-populated with test tokens
            value = mock_redis_with_data.get("test:token")
            assert value is not None
    """
    client = MockRedisClient()

    # Pre-populate with common test data
    client.setex("verify_token:test123", 3600, "user_id:test-user-id")
    client.setex("reset_token:reset456", 3600, "user_id:test-user-id")
    client.set("2FA:test-user-id:totp_enabled", "true")
    client.set("2FA:test-user-id:totp_secret", "BASE32SECRET")

    yield client
    client.clear()


@pytest.fixture
def mock_redis_factory():
    """
    Factory fixture for creating multiple Redis clients.

    Use this when you need to test interactions between multiple Redis clients.

    Example:
        def test_multiple_clients(mock_redis_factory):
            client1 = mock_redis_factory()
            client2 = mock_redis_factory()
            client1.set("key", "value1")
            # Same underlying storage
            assert client2.get("key") == "value1"
    """
    storage = {}

    def create_client():
        client = MockRedisClient()
        client._storage = storage
        return client

    yield create_client

    # Cleanup
    storage.clear()


@pytest.fixture
def mock_redis_dependency(mock_redis_client):
    """
    Mock Redis client as FastAPI dependency.

    Use this to replace get_redis_client() dependency in route tests.

    Example:
        def test_endpoint(client, mock_redis_dependency):
            app.dependency_overrides[get_redis_client] = mock_redis_dependency
            response = client.post("/auth/login", ...)
            assert response.status_code == 200
    """
    def get_mock_redis():
        yield mock_redis_client

    return get_mock_redis
