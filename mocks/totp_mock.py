"""
TOTP/2FA Mock for Deterministic Testing

Provides pytest fixtures and mock implementations for TOTP (Time-based One-Time Password)
operations to enable deterministic 2FA testing without time dependencies.

Usage:
    # In conftest.py or test file
    from mocks.totp_mock import mock_totp_deterministic

    @pytest.mark.asyncio
    async def test_2fa_setup(mock_totp_deterministic):
        service = TwoFactorService()
        result = await service.setup_2fa(user_id)
        # Predictable secret and codes
        assert result["secret"] == "JBSWY3DPEHPK3PXP"
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Optional


# ============================================================================
# Mock TOTP Implementation
# ============================================================================

class MockTOTP:
    """
    Mock TOTP (Time-based One-Time Password) implementation.

    Provides deterministic behavior for testing 2FA flows.
    """

    # Default test secret (Base32 encoded "Hello!")
    DEFAULT_SECRET = "JBSWY3DPEHPK3PXP"

    # Default test code (always valid for testing)
    DEFAULT_CODE = "123456"

    def __init__(self, secret: str = None):
        """
        Initialize mock TOTP.

        Args:
            secret: Base32 secret (uses default if not provided)
        """
        self.secret = secret or self.DEFAULT_SECRET

    def verify(self, code: str, valid_window: int = 1) -> bool:
        """
        Verify a TOTP code (deterministic mock).

        Args:
            code: 6-digit TOTP code
            valid_window: Time window for code validity (ignored in mock)

        Returns:
            True if code matches DEFAULT_CODE, False otherwise
        """
        return code == self.DEFAULT_CODE

    def now(self) -> str:
        """
        Generate current TOTP code (deterministic mock).

        Returns:
            Always returns DEFAULT_CODE for testing
        """
        return self.DEFAULT_CODE

    def provisioning_uri(self, name: str, issuer_name: str = None) -> str:
        """
        Generate provisioning URI for QR code.

        Args:
            name: Account name (usually email)
            issuer_name: Service name

        Returns:
            otpauth:// URI for QR code generation
        """
        uri = f"otpauth://totp/{issuer_name}:{name}?secret={self.secret}&issuer={issuer_name}"
        return uri

    def at(self, for_time: int) -> str:
        """
        Generate TOTP code for specific time (deterministic mock).

        Args:
            for_time: Unix timestamp

        Returns:
            Always returns DEFAULT_CODE for testing
        """
        return self.DEFAULT_CODE


class MockPyOTP:
    """Mock for pyotp module."""

    TOTP = MockTOTP

    @staticmethod
    def random_base32() -> str:
        """
        Generate random Base32 secret (deterministic for testing).

        Returns:
            Always returns DEFAULT_SECRET for predictable tests
        """
        return MockTOTP.DEFAULT_SECRET


# ============================================================================
# Configurable Mock TOTP
# ============================================================================

class ConfigurableMockTOTP:
    """
    Configurable mock TOTP for advanced testing scenarios.

    Allows customization of secret, valid codes, and failure scenarios.
    """

    def __init__(self):
        """Initialize configurable mock."""
        self.secrets: dict[str, str] = {}
        self.valid_codes: dict[str, list[str]] = {}
        self.always_valid = False
        self.always_invalid = False
        self.default_code = "123456"

    def set_secret(self, user_id: str, secret: str):
        """Set secret for a specific user."""
        self.secrets[user_id] = secret

    def set_valid_codes(self, secret: str, codes: list[str]):
        """Set valid codes for a specific secret."""
        self.valid_codes[secret] = codes

    def set_always_valid(self, value: bool = True):
        """Configure to always accept any code."""
        self.always_valid = value

    def set_always_invalid(self, value: bool = True):
        """Configure to always reject any code."""
        self.always_invalid = value

    def create_totp(self, secret: str) -> MockTOTP:
        """Create TOTP instance with custom configuration."""
        totp = MockTOTP(secret)

        # Override verify method with custom logic
        original_verify = totp.verify

        def custom_verify(code: str, valid_window: int = 1) -> bool:
            if self.always_valid:
                return True
            if self.always_invalid:
                return False
            if secret in self.valid_codes:
                return code in self.valid_codes[secret]
            return original_verify(code, valid_window)

        totp.verify = custom_verify
        return totp


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture
def mock_totp_deterministic():
    """
    Mock pyotp with deterministic behavior.

    All TOTP operations return predictable values:
    - Secret: "JBSWY3DPEHPK3PXP"
    - Valid code: "123456"

    Example:
        def test_2fa_setup(mock_totp_deterministic):
            import pyotp
            secret = pyotp.random_base32()
            assert secret == "JBSWY3DPEHPK3PXP"

            totp = pyotp.TOTP(secret)
            assert totp.verify("123456") is True
            assert totp.verify("000000") is False
    """
    with patch('pyotp.random_base32', return_value=MockTOTP.DEFAULT_SECRET):
        with patch('pyotp.TOTP', MockTOTP):
            yield MockPyOTP


@pytest.fixture
def mock_totp_always_valid():
    """
    Mock pyotp that accepts any code as valid.

    Useful for testing flows where 2FA verification should always succeed.

    Example:
        def test_2fa_always_succeeds(mock_totp_always_valid):
            import pyotp
            totp = pyotp.TOTP("ANY_SECRET")
            assert totp.verify("000000") is True
            assert totp.verify("999999") is True
    """
    def always_valid_verify(code: str, valid_window: int = 1) -> bool:
        return True

    mock_totp = MockTOTP()
    mock_totp.verify = always_valid_verify

    with patch('pyotp.random_base32', return_value=MockTOTP.DEFAULT_SECRET):
        with patch('pyotp.TOTP', return_value=mock_totp):
            yield MockPyOTP


@pytest.fixture
def mock_totp_always_invalid():
    """
    Mock pyotp that rejects all codes as invalid.

    Useful for testing error handling when 2FA verification fails.

    Example:
        def test_2fa_fails(mock_totp_always_invalid):
            import pyotp
            totp = pyotp.TOTP("ANY_SECRET")
            assert totp.verify("123456") is False
            assert totp.verify("000000") is False
    """
    def always_invalid_verify(code: str, valid_window: int = 1) -> bool:
        return False

    mock_totp = MockTOTP()
    mock_totp.verify = always_invalid_verify

    with patch('pyotp.random_base32', return_value=MockTOTP.DEFAULT_SECRET):
        with patch('pyotp.TOTP', return_value=mock_totp):
            yield MockPyOTP


@pytest.fixture
def mock_totp_configurable():
    """
    Configurable mock pyotp for advanced testing scenarios.

    Provides full control over secrets, valid codes, and behavior.

    Example:
        def test_custom_codes(mock_totp_configurable):
            # Configure specific valid codes
            mock_totp_configurable.set_valid_codes(
                "SECRET123",
                ["111111", "222222", "333333"]
            )

            import pyotp
            totp = pyotp.TOTP("SECRET123")
            assert totp.verify("111111") is True
            assert totp.verify("999999") is False
    """
    config = ConfigurableMockTOTP()

    def create_totp_wrapper(secret: str):
        return config.create_totp(secret)

    with patch('pyotp.random_base32', return_value=MockTOTP.DEFAULT_SECRET):
        with patch('pyotp.TOTP', side_effect=create_totp_wrapper):
            yield config


@pytest.fixture
def mock_totp_with_secret(request):
    """
    Parameterizable mock pyotp with custom secret.

    Use with pytest.mark.parametrize to test different secrets.

    Example:
        @pytest.mark.parametrize("mock_totp_with_secret", ["SECRET1"], indirect=True)
        def test_with_secret(mock_totp_with_secret):
            import pyotp
            secret = pyotp.random_base32()
            assert secret == "SECRET1"
    """
    secret = request.param if hasattr(request, 'param') else MockTOTP.DEFAULT_SECRET

    with patch('pyotp.random_base32', return_value=secret):
        with patch('pyotp.TOTP', MockTOTP):
            yield secret


@pytest.fixture
def mock_qrcode():
    """
    Mock qrcode library for testing QR code generation.

    Prevents actual QR code image generation in tests.

    Example:
        def test_qr_generation(mock_qrcode):
            import qrcode
            img = qrcode.make("test_data")
            # No actual image generated
    """
    mock_img = Mock()
    mock_img.save = Mock()

    with patch('qrcode.make', return_value=mock_img):
        yield mock_img


# ============================================================================
# Helper Functions
# ============================================================================

def create_mock_totp(
    secret: Optional[str] = None,
    valid_codes: Optional[list[str]] = None,
    always_valid: bool = False,
    always_invalid: bool = False
) -> MockTOTP:
    """
    Create a mock TOTP instance with custom configuration.

    Args:
        secret: Base32 secret (uses default if not provided)
        valid_codes: List of codes that should verify as valid
        always_valid: If True, all codes verify as valid
        always_invalid: If True, all codes verify as invalid

    Returns:
        Configured MockTOTP instance

    Example:
        # Create TOTP that only accepts specific codes
        totp = create_mock_totp(
            secret="MYSECRET",
            valid_codes=["111111", "222222"]
        )
        assert totp.verify("111111") is True
        assert totp.verify("999999") is False
    """
    totp = MockTOTP(secret)

    if always_valid:
        totp.verify = lambda code, valid_window=1: True
    elif always_invalid:
        totp.verify = lambda code, valid_window=1: False
    elif valid_codes:
        totp.verify = lambda code, valid_window=1: code in valid_codes

    return totp


def get_test_totp_data() -> dict:
    """
    Get standard test data for TOTP testing.

    Returns:
        Dictionary with test secret, codes, and URIs

    Example:
        data = get_test_totp_data()
        secret = data["secret"]
        valid_code = data["valid_codes"][0]
    """
    return {
        "secret": MockTOTP.DEFAULT_SECRET,
        "valid_codes": [MockTOTP.DEFAULT_CODE, "654321"],
        "invalid_codes": ["000000", "999999"],
        "provisioning_uri": f"otpauth://totp/AuthApp:test@example.com?secret={MockTOTP.DEFAULT_SECRET}&issuer=AuthApp"
    }
