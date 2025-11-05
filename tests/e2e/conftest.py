"""
E2E test fixtures.

These fixtures provide real HTTP client and API connections for end-to-end testing.
"""
import asyncio
import os
import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def client():
    """
    Create an HTTP client for testing API endpoints.
    This requires the API server to be running.
    """
    from httpx import AsyncClient

    base_url = os.getenv("TEST_API_URL", "http://localhost:8000")

    async with AsyncClient(base_url=base_url, timeout=30.0) as client:
        yield client


@pytest.fixture
async def authenticated_client(client, test_user_credentials):
    """
    Create an authenticated HTTP client with a logged-in user.
    This fixture assumes there's a test user available.
    """
    # Login to get tokens
    login_response = await client.post(
        "/auth/login",
        json=test_user_credentials
    )

    if login_response.status_code == 200:
        tokens = login_response.json()
        # Set authorization header
        client.headers.update({
            "Authorization": f"Bearer {tokens['access_token']}"
        })

    yield client

    # Cleanup: remove auth header
    client.headers.pop("Authorization", None)


@pytest.fixture
def test_user_credentials():
    """
    Provide test user credentials for E2E tests.
    These should be valid credentials for a test user.
    """
    return {
        "email": os.getenv("TEST_USER_EMAIL", "test@example.com"),
        "password": os.getenv("TEST_USER_PASSWORD", "StrongPassword123!")
    }
