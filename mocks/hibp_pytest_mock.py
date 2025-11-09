"""
Pytest fixtures for mocking pwnedpasswords library.

Provides fixtures and utilities for mocking HIBP password breach checking
in unit tests without requiring HTTP server or network calls.

Usage:
    # In conftest.py or test file
    from mocks.hibp_pytest_mock import mock_pwnedpasswords_safe, mock_pwnedpasswords_breached

    @pytest.mark.asyncio
    async def test_safe_password(mock_pwnedpasswords_safe):
        service = PasswordValidationService()
        result = await service.check_breach_status("MyStr0ng!Password")
        assert result["leak_count"] == 0

    @pytest.mark.asyncio
    async def test_breached_password(mock_pwnedpasswords_breached):
        service = PasswordValidationService()
        with pytest.raises(PasswordValidationError):
            await service.check_breach_status("password123")
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Callable


class MockPassword:
    """Mock for pwnedpasswords.Password class."""

    def __init__(self, password: str, breach_count: int = 0):
        """
        Initialize mock Password instance.

        Args:
            password: Password being checked
            breach_count: Number of times found in breaches (0 = safe)
        """
        self.password = password
        self.breach_count = breach_count

    def check(self) -> int:
        """
        Mock the check() method.

        Returns:
            Number of times password found in breaches
        """
        return self.breach_count


class MockPasswordFactory:
    """Factory for creating MockPassword instances with configurable behavior."""

    def __init__(self):
        self.breach_database: Dict[str, int] = {
            # Common breached passwords for testing
            "password": 10000000,
            "123456": 5000000,
            "password123": 1000000,
            "qwerty": 500000,
            "P@ssw0rd!": 50000,
            "letmein": 100000,
        }
        self.should_raise = False
        self.exception_to_raise = None

    def __call__(self, password: str) -> MockPassword:
        """
        Create MockPassword instance.

        Args:
            password: Password to check

        Returns:
            MockPassword instance

        Raises:
            Exception if configured to simulate API failure
        """
        if self.should_raise:
            raise self.exception_to_raise or Exception("HIBP API unavailable")

        breach_count = self.breach_database.get(password, 0)
        return MockPassword(password, breach_count)

    def add_breached_password(self, password: str, count: int = 100000):
        """
        Add a breached password to the mock database.

        Args:
            password: Password to mark as breached
            count: Breach count
        """
        self.breach_database[password] = count

    def set_all_safe(self):
        """Configure to return 0 breaches for all passwords."""
        self.breach_database.clear()

    def set_all_breached(self, count: int = 100000):
        """
        Configure to return breaches for all passwords.

        Args:
            count: Default breach count
        """
        self.default_breach_count = count
        self.breach_database = {}

        # Override __call__ to always return breached
        def always_breached(password: str) -> MockPassword:
            if self.should_raise:
                raise self.exception_to_raise or Exception("HIBP API unavailable")
            return MockPassword(password, count)

        self.__call__ = always_breached

    def simulate_api_failure(self, exception: Exception = None):
        """
        Configure to simulate API failure.

        Args:
            exception: Exception to raise (default: generic Exception)
        """
        self.should_raise = True
        self.exception_to_raise = exception


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture
def mock_pwnedpasswords_safe():
    """
    Mock pwnedpasswords to return 0 breaches for all passwords.

    Use this fixture when testing flows where password should pass breach check.

    Example:
        async def test_registration_success(mock_pwnedpasswords_safe):
            # All passwords will pass breach check
            result = await register_user("user@example.com", "any_password")
            assert result.success
    """
    factory = MockPasswordFactory()
    factory.set_all_safe()

    with patch('app.services.password_validation_service.Password', factory):
        yield factory


@pytest.fixture
def mock_pwnedpasswords_breached():
    """
    Mock pwnedpasswords to return breaches for common weak passwords.

    Use this fixture when testing password breach detection.

    Breached passwords:
        - password (10M)
        - 123456 (5M)
        - password123 (1M)
        - qwerty (500K)
        - P@ssw0rd! (50K)
        - letmein (100K)

    Example:
        async def test_breached_password_rejected(mock_pwnedpasswords_breached):
            service = PasswordValidationService()
            with pytest.raises(PasswordValidationError):
                await service.check_breach_status("password123")
    """
    factory = MockPasswordFactory()

    with patch('app.services.password_validation_service.Password', factory):
        yield factory


@pytest.fixture
def mock_pwnedpasswords_unavailable():
    """
    Mock pwnedpasswords to simulate API unavailability.

    Use this fixture when testing graceful degradation when HIBP is down.

    Example:
        async def test_breach_check_graceful_failure(mock_pwnedpasswords_unavailable):
            service = PasswordValidationService()
            result = await service.check_breach_status("any_password")
            assert result["leak_count"] == -1  # Indicates API failure
            assert result["validation_passed"]  # Still allows password
    """
    factory = MockPasswordFactory()
    factory.simulate_api_failure()

    with patch('app.services.password_validation_service.Password', factory):
        yield factory


@pytest.fixture
def mock_pwnedpasswords_custom():
    """
    Mock pwnedpasswords with customizable breach database.

    Use this fixture when you need fine-grained control over breach data.

    Example:
        async def test_custom_breach_scenario(mock_pwnedpasswords_custom):
            # Add specific passwords as breached
            mock_pwnedpasswords_custom.add_breached_password("TestPass123", 500)

            service = PasswordValidationService()
            result = await service.check_breach_status("TestPass123")
            assert result["leak_count"] == 500

            # Safe password
            result = await service.check_breach_status("UniqueP@ssw0rd!")
            assert result["leak_count"] == 0
    """
    factory = MockPasswordFactory()
    factory.set_all_safe()  # Start with all passwords safe

    with patch('app.services.password_validation_service.Password', factory):
        yield factory


# ============================================================================
# Standalone Mock Functions (for manual patching)
# ============================================================================

def create_password_mock(breach_count: int = 0) -> MockPassword:
    """
    Create a standalone MockPassword instance.

    Args:
        breach_count: Number of breaches to return

    Returns:
        MockPassword instance

    Example:
        with patch('pwnedpasswords.Password') as mock_pwd:
            mock_pwd.return_value = create_password_mock(breach_count=0)
            # Test code here
    """
    return MockPassword("", breach_count)


def create_failing_password_mock(exception: Exception = None) -> Callable:
    """
    Create a mock that raises an exception when check() is called.

    Args:
        exception: Exception to raise (default: generic Exception)

    Returns:
        Mock function that raises exception

    Example:
        with patch('pwnedpasswords.Password') as mock_pwd:
            mock_pwd.return_value.check = create_failing_password_mock()
            # Test code here - will raise exception
    """
    def failing_check():
        raise exception or Exception("HIBP API unavailable")

    mock = Mock()
    mock.check = failing_check
    return mock
