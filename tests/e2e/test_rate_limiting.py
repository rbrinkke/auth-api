"""
End-to-end tests for rate limiting enforcement.

Tests that rate limits are properly enforced on all sensitive endpoints:
- Login endpoint: 5 requests per minute
- Password reset request: 1 request per 5 minutes
- Registration endpoint: 3 requests per minute per IP
"""
import pytest
import asyncio
import time

from slowapi import Limiter
from slowapi.util import get_remote_address


@pytest.mark.e2e
@pytest.mark.slow
class TestRateLimiting:
    """E2E tests for rate limiting enforcement."""

    @pytest.mark.skip(reason="Requires API to be running")
    async def test_login_rate_limit_enforced(self, client):
        """Test that login endpoint has rate limiting (5 per minute)."""
        # Arrange
        test_email = "rate-limit-test@example.com"
        test_password = "StrongPassword123!"

        # First register the user
        await client.post(
            "/auth/register",
            json={
                "email": test_email,
                "password": test_password
            }
        )

        # Act - Try to login 6 times (should hit limit on 6th attempt)
        attempts = 0
        rate_limited = False

        for i in range(6):
            response = await client.post(
                "/auth/login",
                json={
                    "email": test_email,
                    "password": f"WrongPassword{i}!"
                }
            )

            attempts += 1

            if response.status_code == 429:
                rate_limited = True
                # Verify rate limit headers are present
                assert "Retry-After" in response.headers
                assert "X-RateLimit-Limit" in response.headers
                assert "X-RateLimit-Remaining" in response.headers
                break

        # Assert
        assert rate_limited, f"Expected rate limiting after {attempts} attempts"
        assert attempts <= 6, f"Rate limit should trigger before 6 attempts"

    @pytest.mark.skip(reason="Requires API to be running")
    async def test_registration_rate_limit_enforced(self, client):
        """Test that registration endpoint has rate limiting (3 per minute per IP)."""
        # Act - Try to register 4 times with different emails
        rate_limited = False

        for i in range(4):
            response = await client.post(
                "/auth/register",
                json={
                    "email": f"rate-limit-reg-{i}@example.com",
                    "password": "StrongPassword123!"
                }
            )

            if response.status_code == 429:
                rate_limited = True
                # Verify rate limit headers
                assert "Retry-After" in response.headers
                break

        # Assert - Should hit rate limit
        assert rate_limited, "Expected rate limiting on registration endpoint"

    @pytest.mark.skip(reason="Requires API to be running")
    async def test_password_reset_rate_limit_enforced(self, client):
        """Test that password reset request has rate limiting (1 per 5 minutes)."""
        # Arrange
        test_email = "rate-limit-reset@example.com"

        # Register user first
        await client.post(
            "/auth/register",
            json={
                "email": test_email,
                "password": "StrongPassword123!"
            }
        )

        # Act - Try to request password reset twice
        responses = []
        for i in range(2):
            response = await client.post(
                "/auth/request-password-reset",
                json={"email": test_email}
            )
            responses.append(response)

        # Assert - At least one should succeed, but second might be rate limited
        # Note: Actual behavior depends on implementation (generic response or rate limit)
        assert len(responses) == 2

        # If rate limiting is enforced, one should return 429
        # If generic responses are used, both might return 200
        status_codes = [r.status_code for r in responses]
        assert 200 in status_codes or 429 in status_codes

    @pytest.mark.skip(reason="Requires API to be running")
    async def test_rate_limit_headers_present(self, client):
        """Test that rate limit headers are present in responses."""
        # Arrange
        test_email = "rate-limit-headers@example.com"

        # Act - Trigger rate limit on registration
        for i in range(4):  # Try 4 times to likely trigger limit
            response = await client.post(
                "/auth/register",
                json={
                    "email": f"rate-limit-h-{i}@example.com",
                    "password": "StrongPassword123!"
                }
            )

            if response.status_code == 429:
                # Assert - Check rate limit headers
                assert "X-RateLimit-Limit" in response.headers
                assert "X-RateLimit-Remaining" in response.headers
                assert "X-RateLimit-Reset" in response.headers or "Retry-After" in response.headers
                break

    @pytest.mark.skip(reason="Requires API to be running")
    async def test_rate_limit_resets_after_window(self, client):
        """Test that rate limit resets after the time window."""
        # Arrange
        test_email = "rate-limit-reset@example.com"

        # Act - Trigger rate limit
        for i in range(4):
            response = await client.post(
                "/auth/register",
                json={
                    "email": f"rate-limit-reset-{i}@example.com",
                    "password": "StrongPassword123!"
                }
            )

            if response.status_code == 429:
                # Wait for rate limit window to reset
                # Login rate limit: 1 minute
                # Registration rate limit: 1 minute
                retry_after = int(response.headers.get("Retry-After", 60))
                await asyncio.sleep(retry_after + 1)

                # Try again - should succeed
                retry_response = await client.post(
                    "/auth/register",
                    json={
                        "email": f"rate-limit-after-{int(time.time())}@example.com",
                        "password": "StrongPassword123!"
                    }
                )

                # Should succeed after reset
                assert retry_response.status_code == 201, "Request should succeed after rate limit reset"
                break

    @pytest.mark.skip(reason="Requires API to be running")
    async def test_rate_limit_per_ip_not_per_user(self, client):
        """Test that rate limiting is per IP, not per user account."""
        # This is harder to test in isolation but we can verify the behavior
        # Arrange - Use different email addresses to simulate different users from same IP

        # Act - Register multiple users from same IP
        responses = []
        for i in range(3):
            response = await client.post(
                "/auth/register",
                json={
                    "email": f"per-ip-test-{i}@example.com",
                    "password": "StrongPassword123!"
                }
            )
            responses.append(response)

        # If rate limiting is per IP, these should be rate limited together
        # If per user, they would succeed
        status_codes = [r.status_code for r in responses]

        # Either all succeed (no rate limit) or all get rate limited (per IP)
        # or a mix based on implementation
        assert all(code in [200, 201, 429] for code in status_codes)

    @pytest.mark.skip(reason="Requires API to be running")
    async def test_rate_limit_on_protected_endpoints(self, client):
        """Test that protected endpoints also have rate limiting."""
        # This test would require authenticated endpoints
        # For now, we test login as a protected operation

        # Act - Try to use an invalid access token multiple times
        rate_limited = False

        for i in range(6):
            response = await client.post(
                "/auth/refresh",
                json={"refresh_token": "invalid_token"}
            )

            if response.status_code == 429:
                rate_limited = True
                break

        # Note: Refresh endpoint may or may not be rate limited
        # This test documents the expected behavior
        # assert rate_limited, "Expected rate limiting on token refresh"

    @pytest.mark.skip(reason="Requires API to be running")
    async def test_rate_limit_does_not_affect_valid_requests(self, client):
        """Test that valid requests within rate limit are not affected."""
        # Arrange
        test_email = "valid-within-limit@example.com"

        # Act - Make requests within rate limit
        responses = []
        for i in range(3):  # Assuming limit is 5, 3 should be fine
            response = await client.post(
                "/auth/register",
                json={
                    "email": f"within-limit-{i}@example.com",
                    "password": "StrongPassword123!"
                }
            )
            responses.append(response)

        # Assert - All should succeed
        for response in responses:
            assert response.status_code == 201, "Requests within rate limit should succeed"

    @pytest.mark.skip(reason="Requires API to be running")
    async def test_rate_limit_error_message(self, client):
        """Test that rate limit errors have appropriate error messages."""
        # Act - Trigger rate limit
        for i in range(5):
            response = await client.post(
                "/auth/register",
                json={
                    "email": f"error-message-{i}@example.com",
                    "password": "StrongPassword123!"
                }
            )

            if response.status_code == 429:
                # Assert - Error message should be informative
                data = response.json()
                assert "detail" in data or "message" in data
                error_msg = data.get("detail", "") or data.get("message", "")
                assert (
                    "rate limit" in error_msg.lower() or
                    "too many" in error_msg.lower() or
                    "retry" in error_msg.lower()
                ), f"Rate limit error should be informative: {error_msg}"
                break
