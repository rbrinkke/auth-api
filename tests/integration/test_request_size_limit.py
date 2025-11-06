"""Integration tests for request size limits.

Tests request size limit enforcement with real API endpoints.
"""

import pytest
import json
from httpx import AsyncClient
from app.main import app


class TestRequestSizeLimitIntegration:
    """Integration tests for request size limit middleware."""

    @pytest.mark.asyncio
    async def test_register_with_valid_size_payload(self):
        """Test registration endpoint accepts valid size payload."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            payload = {
                "email": "test@example.com",
                "password": "Test@1234567",
            }

            response = await client.post("/api/auth/register", json=payload)

            # Should not return 413
            assert response.status_code != 413

    @pytest.mark.asyncio
    async def test_register_with_oversized_payload_returns_413(self):
        """Test that register endpoint rejects oversized payload."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create payload exceeding 10 KB limit
            large_data = "a" * 15000  # 15 KB

            payload = {
                "email": "test@example.com",
                "password": large_data,
            }

            response = await client.post("/api/auth/register", json=payload)

            # Should return 413 Payload Too Large
            assert response.status_code == 413
            assert "too large" in response.text.lower()

    @pytest.mark.asyncio
    async def test_login_with_valid_size_payload(self):
        """Test login endpoint accepts valid size payload."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            payload = {
                "email": "test@example.com",
                "password": "Test@1234567",
            }

            response = await client.post("/api/auth/login", json=payload)

            # Should not return 413 (may return 401 due to invalid creds)
            assert response.status_code != 413

    @pytest.mark.asyncio
    async def test_login_with_oversized_payload_returns_413(self):
        """Test that login endpoint rejects oversized payload."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create oversized payload
            large_data = "a" * 15000

            # Send raw oversized JSON
            response = await client.post(
                "/api/auth/login",
                content=json.dumps({
                    "email": "test@example.com",
                    "password": large_data,
                }),
                headers={"Content-Type": "application/json"},
            )

            # Should return 413
            assert response.status_code == 413

    @pytest.mark.asyncio
    async def test_password_reset_request_with_valid_payload(self):
        """Test password reset request accepts valid payload."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            payload = {"email": "test@example.com"}

            response = await client.post(
                "/api/auth/request-password-reset", json=payload
            )

            # Should not return 413
            assert response.status_code != 413

    @pytest.mark.asyncio
    async def test_password_reset_request_with_oversized_payload_returns_413(self):
        """Test that password reset request rejects oversized payload."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create oversized email (exceeds 5 KB limit)
            large_email = "a" * 8000 + "@example.com"

            response = await client.post(
                "/api/auth/request-password-reset",
                content=json.dumps({"email": large_email}),
                headers={"Content-Type": "application/json"},
            )

            # Should return 413
            assert response.status_code == 413

    @pytest.mark.asyncio
    async def test_refresh_token_with_valid_payload(self):
        """Test token refresh accepts valid size payload."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            payload = {"refresh_token": "test_token_string"}

            response = await client.post("/api/auth/refresh", json=payload)

            # Should not return 413 (may return 401 for invalid token)
            assert response.status_code != 413

    @pytest.mark.asyncio
    async def test_refresh_token_with_oversized_payload_returns_413(self):
        """Test that refresh endpoint rejects oversized payload."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create oversized token (exceeds 5 KB limit)
            large_token = "a" * 8000

            response = await client.post(
                "/api/auth/refresh",
                content=json.dumps({"refresh_token": large_token}),
                headers={"Content-Type": "application/json"},
            )

            # Should return 413
            assert response.status_code == 413

    @pytest.mark.asyncio
    async def test_logout_with_oversized_payload_returns_413(self):
        """Test that logout rejects oversized payload."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create oversized token
            large_token = "a" * 8000

            response = await client.post(
                "/api/auth/logout",
                content=json.dumps({"refresh_token": large_token}),
                headers={"Content-Type": "application/json"},
            )

            # Should return 413
            assert response.status_code == 413

    @pytest.mark.asyncio
    async def test_2fa_setup_with_valid_payload(self):
        """Test 2FA setup accepts valid size payload."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = {"Authorization": "Bearer invalid_token"}

            response = await client.post(
                "/api/auth/2fa/setup",
                headers=headers,
                json={},
            )

            # Should not return 413 (may return 401 for auth)
            assert response.status_code != 413

    @pytest.mark.asyncio
    async def test_2fa_setup_with_oversized_payload_returns_413(self):
        """Test that 2FA setup rejects oversized payload."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create oversized payload (exceeds 5 KB limit)
            large_data = "a" * 8000

            headers = {"Authorization": "Bearer invalid_token"}

            response = await client.post(
                "/api/auth/2fa/setup",
                headers=headers,
                content=json.dumps({"data": large_data}),
                headers_={"Content-Type": "application/json"},
            )

            # Should return 413
            assert response.status_code == 413

    @pytest.mark.asyncio
    async def test_health_check_not_restricted(self):
        """Test that health check endpoint works normally."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/health")

            # Should return 200, not 413
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_request_at_exact_limit_passes(self):
        """Test that request at exact limit boundary passes."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create payload at exactly 10 KB limit for login
            # Each character is ~1 byte, so create payload close to 10240 bytes
            payload_size = 10240 - 100  # Leave room for JSON structure
            large_data = "a" * payload_size

            payload = {
                "email": "test@example.com",
                "password": large_data,
            }

            response = await client.post("/api/auth/login", json=payload)

            # Should not return 413 at exact limit
            assert response.status_code != 413

    @pytest.mark.asyncio
    async def test_multiple_consecutive_requests_with_large_payloads(self):
        """Test that multiple oversized requests all return 413."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            large_data = "a" * 15000

            for _ in range(3):
                payload = {
                    "email": "test@example.com",
                    "password": large_data,
                }

                response = await client.post("/api/auth/register", json=payload)

                # All should return 413
                assert response.status_code == 413

    @pytest.mark.asyncio
    async def test_reset_password_confirm_with_valid_payload(self):
        """Test password reset confirm accepts valid payload."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            payload = {
                "reset_token": "valid_token",
                "code": "123456",
                "new_password": "NewPass@1234",
            }

            response = await client.post(
                "/api/auth/reset-password", json=payload
            )

            # Should not return 413
            assert response.status_code != 413

    @pytest.mark.asyncio
    async def test_reset_password_confirm_with_oversized_payload_returns_413(self):
        """Test password reset confirm rejects oversized payload."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create oversized token
            large_token = "a" * 8000

            response = await client.post(
                "/api/auth/reset-password",
                content=json.dumps({
                    "reset_token": large_token,
                    "code": "123456",
                    "new_password": "NewPass@1234",
                }),
                headers={"Content-Type": "application/json"},
            )

            # Should return 413
            assert response.status_code == 413
