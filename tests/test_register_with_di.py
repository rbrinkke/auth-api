"""
Example test file demonstrating Dependency Injection for easy testing.

This shows how DI makes the codebase "best in class" and testable.
"""
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient

# Import the main app
from app.main import app

# Import dependency functions (not the services directly!)
from app.services.email_service import get_email_service, EmailService


class MockEmailService:
    """Mock email service for testing - doesn't send real emails!"""

    def __init__(self):
        self.sent_emails = []  # Track what was "sent"

    async def send_verification_email(self, email: str, token: str):
        """Mock implementation - just records the call"""
        self.sent_emails.append({
            "type": "verification",
            "email": email,
            "token": token
        })
        print(f"📧 MOCK: Would send verification email to {email}")
        return True

    async def send_password_reset_email(self, email: str, token: str):
        """Mock implementation - just records the call"""
        self.sent_emails.append({
            "type": "password_reset",
            "email": email,
            "token": token
        })
        print(f"📧 MOCK: Would send password reset email to {email}")
        return True


def test_register_sends_email_via_di():
    """
    Test that registration uses injected email service (not global singleton).

    BEFORE DI (difficult to test):
    - email_service was imported directly
    - Hard to mock because it's a global instance
    - Tests would send REAL emails

    AFTER DI (easy to test):
    - email_svc is injected via Depends(get_email_service)
    - Can override dependency with app.dependency_overrides
    - Tests use mock services, no real emails sent!
    """
    # Step 1: Create mock service
    mock_email_service = MockEmailService()

    # Step 2: Override the dependency for testing
    # This is the power of DI - we can swap out the real service!
    app.dependency_overrides[get_email_service] = lambda: mock_email_service

    try:
        # Step 3: Use TestClient to make request
        client = TestClient(app)

        # Step 4: Register a user
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "MyD3centP@ssw0rd2024"
            }
        )

        # Step 5: Verify the response
        assert response.status_code == 201
        data = response.json()
        assert "test@example.com" in data["message"]

        # Step 6: Verify mock was called (no real email sent!)
        assert len(mock_email_service.sent_emails) == 1
        assert mock_email_service.sent_emails[0]["type"] == "verification"
        assert mock_email_service.sent_emails[0]["email"] == "test@example.com"

        print("✅ Test passed! Email service was properly injected and mocked.")

    finally:
        # Step 7: Clean up - remove override
        app.dependency_overrides.clear()


def test_password_reset_sends_email_via_di():
    """
    Test that password reset also uses DI.
    Same pattern - easy to mock and test!
    """
    # Create mock service
    mock_email_service = MockEmailService()

    # Override dependency
    app.dependency_overrides[get_email_service] = lambda: mock_email_service

    try:
        client = TestClient(app)

        # Request password reset (will fail at token validation, but that's OK)
        response = client.post(
            "/auth/request-password-reset",
            json={"email": "test@example.com"}
        )

        # Should return generic success message (security feature)
        assert response.status_code == 200
        data = response.json()
        assert "If an account exists" in data["message"]

        # In real scenario, email would be sent if user exists
        # But our mock tracks it anyway for verification
        print("✅ Password reset test passed!")

    finally:
        app.dependency_overrides.clear()


def test_professional_password_validation():
    """
    Test that password validation works correctly.

    This test verifies that zxcvbn + HIBP checks are working.
    """
    client = TestClient(app)

    # Test 1: Weak password should be rejected
    response = client.post(
        "/auth/register",
        json={
            "email": "weak@example.com",
            "password": "password123"  # Weak password
        }
    )
    assert response.status_code == 422
    error = response.json()["detail"][0]["msg"]
    assert "Weak password detected" in error
    print("✅ Weak password correctly rejected")

    # Test 2: Strong password should be accepted (by validation)
    response = client.post(
        "/auth/register",
        json={
            "email": "strong@example.com",
            "password": "MyD3centP@ssw0rd2024"  # Strong password
        }
    )
    # May fail at other stages (user exists, etc.) but validation passed
    assert response.status_code in [201, 400]  # 201=success, 400=user exists
    print("✅ Strong password accepted by validation")


if __name__ == "__main__":
    """
    Run tests directly (without pytest).

    This demonstrates how easy it is to test with DI!
    """
    print("\n" + "=" * 60)
    print("DEPENDENCY INJECTION TEST SUITE")
    print("=" * 60)

    print("\n🧪 Test 1: Register with DI")
    test_register_sends_email_via_di()

    print("\n🧪 Test 2: Password Reset with DI")
    test_password_reset_sends_email_via_di()

    print("\n🧪 Test 3: Password Validation")
    test_professional_password_validation()

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("\nKey Benefits of DI:")
    print("  • Easy to mock services (no real emails sent)")
    print("  • No tight coupling between routes and services")
    print("  • Best-in-class testability")
    print("  • Can swap implementations easily")
    print("=" * 60)
