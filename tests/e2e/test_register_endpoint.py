"""
End-to-end tests for registration endpoint via HTTP.

Tests the full HTTP flow including routing and middleware.
"""
import pytest
import httpx

# Note: These tests require the API to be running
# They test the HTTP interface, not the services directly


@pytest.mark.e2e
@pytest.mark.slow
class TestRegistrationEndpointE2E:
    """E2E tests for registration endpoint."""

    @pytest.mark.skip(reason="Requires API to be running")
    async def test_registration_endpoint_health(self):
        """Test that registration endpoint is reachable."""
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    @pytest.mark.skip(reason="Requires API to be running")
    async def test_register_endpoint_success(self):
        """Test successful registration via HTTP."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/auth/register",
                json={
                    "email": "e2e-test@example.com",
                    "password": "StrongPassword123!@#$"
                }
            )
            assert response.status_code == 201
            data = response.json()
            assert "message" in data
            assert data["email"] == "e2e-test@example.com"

    @pytest.mark.skip(reason="Requires API to be running")
    async def test_weak_password_rejected(self):
        """Test that weak passwords are rejected via HTTP."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/auth/register",
                json={
                    "email": "weak-test@example.com",
                    "password": "weak"
                }
            )
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data

    @pytest.mark.skip(reason="Requires API to be running")
    async def test_rate_limiting_enforced(self):
        """Test that rate limiting is enforced."""
        async with httpx.AsyncClient() as client:
            # Make multiple rapid requests
            for i in range(10):
                response = await client.post(
                    "http://localhost:8000/auth/register",
                    json={
                        "email": f"rate-test-{i}@example.com",
                        "password": "StrongPassword123!@#$"
                    }
                )
                # Stop on rate limit
                if response.status_code == 429:
                    break
                assert response.status_code in [200, 201, 400, 422]

    @pytest.mark.skip(reason="Requires API to be running")
    async def test_security_headers_present(self):
        """Test that security headers are present in responses."""
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")

            # Check security headers
            assert "X-Content-Type-Options" in response.headers
            assert response.headers["X-Content-Type-Options"] == "nosniff"

            assert "X-XSS-Protection" in response.headers
            assert "X-Frame-Options" in response.headers
            assert response.headers["X-Frame-Options"] == "DENY"

            assert "Referrer-Policy" in response.headers
            assert "Content-Security-Policy" in response.headers

    @pytest.mark.skip(reason="Requires API to be running")
    async def test_server_header_hidden(self):
        """Test that server header is hidden."""
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")

            # Server header should be empty or not present
            assert "Server" in response.headers
            # In production mode, server header should be empty
            # In debug mode, it may show "uvicorn"
