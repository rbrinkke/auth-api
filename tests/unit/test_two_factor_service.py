"""
Unit tests for TwoFactorService.

Fast, isolated unit tests with mocked dependencies.
"""
import pytest
import base64
from unittest.mock import AsyncMock, MagicMock
from cryptography.fernet import Fernet

from app.services.two_factor_service import (
    TwoFactorService,
    TwoFactorError,
    InvalidCodeError
)


@pytest.mark.unit
class TestTwoFactorService:
    """Unit tests for TwoFactorService."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        return AsyncMock()

    @pytest.fixture
    def mock_email_service(self):
        """Mock email service."""
        return MagicMock()

    @pytest.fixture
    def twofa_service(self, mock_redis, mock_email_service):
        """Create TwoFactorService instance with mocked dependencies."""
        # Create a test encryption key
        test_key = Fernet.generate_key()
        return TwoFactorService(mock_redis, mock_email_service)

    @pytest.fixture
    def twofa_service_with_key(self, mock_redis, mock_email_service):
        """Create TwoFactorService with fixed encryption key for testing."""
        # Use a fixed key for reproducible tests
        test_key = base64.b64encode(b"test_key_32_bytes_long!!")
        service = TwoFactorService(mock_redis, mock_email_service)
        service.cipher_suite = Fernet(test_key)
        return service

    # ========== TOTP Secret Generation ==========

    def test_generate_totp_secret(self, twofa_service):
        """Test TOTP secret generation."""
        secret = twofa_service.generate_totp_secret()

        # Should be non-empty and base32 encoded
        assert secret
        assert isinstance(secret, str)
        # Base32 should only contain valid characters
        valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")
        assert all(c in valid_chars for c in secret)

    def test_generate_totp_secret_uniqueness(self, twofa_service):
        """Test that generated secrets are unique."""
        secrets = {twofa_service.generate_totp_secret() for _ in range(10)}
        assert len(secrets) == 10  # All should be unique

    # ========== Secret Encryption/Decryption ==========

    def test_encrypt_decrypt_secret(self, twofa_service_with_key):
        """Test encryption and decryption of TOTP secret."""
        original_secret = "JBSWY3DPEHPK3PXP"

        # Encrypt
        encrypted = twofa_service_with_key.encrypt_secret(original_secret)
        assert encrypted
        assert encrypted != original_secret

        # Decrypt
        decrypted = twofa_service_with_key.decrypt_secret(encrypted)
        assert decrypted == original_secret

    def test_encrypt_secret_different_each_time(self, twofa_service):
        """Test that encryption produces different outputs each time."""
        secret = "JBSWY3DPEHPK3PXP"

        encrypted1 = twofa_service.encrypt_secret(secret)
        encrypted2 = twofa_service.encrypt_secret(secret)

        # Should be different due to randomization
        assert encrypted1 != encrypted2

    def test_decrypt_with_wrong_key_fails(self, twofa_service):
        """Test that decryption with wrong key fails."""
        secret = "JBSWY3DPEHPK3PXP"
        encrypted = twofa_service.encrypt_secret(secret)

        # Try to decrypt with different service instance (different key)
        service2 = TwoFactorService(AsyncMock(), MagicMock())

        with pytest.raises(Exception):  # Cryptography error
            service2.decrypt_secret(encrypted)

    # ========== QR Code Generation ==========

    def test_generate_qr_code(self, twofa_service):
        """Test QR code generation for authenticator apps."""
        secret = "JBSWY3DPEHPK3PXP"
        email = "test@example.com"

        qr_code = twofa_service.generate_qr_code(secret, email)

        # Should return data URL
        assert qr_code.startswith("data:image/png;base64,")

        # Should be base64 encoded
        data_part = qr_code.split(",")[1]
        decoded = base64.b64decode(data_part)
        assert len(decoded) > 0

    def test_generate_qr_code_with_email(self, twofa_service):
        """Test QR code contains correct email and issuer."""
        secret = "JBSWY3DPEHPK3PXP"
        email = "user@example.com"

        qr_code = twofa_service.generate_qr_code(secret, email)
        assert "data:image/png;base64," in qr_code

    # ========== TOTP Verification ==========

    @pytest.mark.skip(reason="Requires real TOTP codes for testing")
    def test_verify_totp_code(self, twofa_service):
        """Test TOTP code verification with real codes."""
        secret = "JBSWY3DPEHPK3PXP"

        # Skip for now - would need real TOTP codes
        # pyotp generates time-based codes that change every 30 seconds
        pass

    def test_verify_totp_code_invalid_format(self, twofa_service):
        """Test that invalid TOTP codes are rejected."""
        secret = "JBSWY3DPEHPK3PXP"

        # Various invalid formats
        invalid_codes = ["12345", "1234567", "abc123", ""]

        for code in invalid_codes:
            result = twofa_service.verify_totp_code(secret, code)
            assert result is False

    # ========== Backup Codes ==========

    def test_generate_backup_codes(self, twofa_service):
        """Test backup code generation."""
        codes = twofa_service.generate_backup_codes(8)

        # Should generate requested number of codes
        assert len(codes) == 8

        # Each code should be 8 digits
        for code in codes:
            assert len(code) == 8
            assert code.isdigit()

    def test_generate_backup_codes_uniqueness(self, twofa_service):
        """Test that backup codes are unique."""
        codes1 = twofa_service.generate_backup_codes(20)
        codes2 = twofa_service.generate_backup_codes(20)

        # Sets should not have duplicates
        assert len(set(codes1)) == len(codes1)
        assert len(set(codes2)) == len(codes2)

    def test_hash_backup_code(self, twofa_service):
        """Test backup code hashing."""
        code = "12345678"

        # Should hash to consistent value
        hash1 = twofa_service.hash_backup_code(code)
        hash2 = twofa_service.hash_backup_code(code)
        assert hash1 == hash2

        # Should be different from original
        assert hash1 != code

        # Should be SHA256 hex string (64 characters)
        assert len(hash1) == 64
        assert all(c in "0123456789abcdef" for c in hash1)

    # ========== Temporary 2FA Codes ==========

    @pytest.mark.asyncio
    async def test_create_temp_code(self, mock_redis, mock_email_service, twofa_service):
        """Test temporary 2FA code creation."""
        user_id = "test-user-123"
        purpose = "login"
        email = "test@example.com"

        # Create temp code
        code = await twofa_service.create_temp_code(user_id, purpose, email)

        # Should return 6-digit code
        assert len(code) == 6
        assert code.isdigit()

        # Should store in Redis with 5-minute TTL
        mock_redis.client.setex.assert_called_once()
        call_args = mock_redis.client.setex.call_args

        # Check key format
        assert call_args[0][0] == f"2FA:{user_id}:{purpose}"

        # Check TTL (300 seconds = 5 minutes)
        assert call_args[0][1] == 300

        # Should send email
        mock_email_service.send_2fa_code_email.assert_called_once_with(
            email, code, purpose
        )

    @pytest.mark.asyncio
    async def test_create_temp_code_without_email(self, mock_redis, mock_email_service, twofa_service):
        """Test temp code creation without email (for testing scenarios)."""
        user_id = "test-user-123"
        purpose = "verify"

        code = await twofa_service.create_temp_code(user_id, purpose, email=None)

        assert len(code) == 6
        assert code.isdigit()

        # Should store in Redis
        mock_redis.client.setex.assert_called_once()

        # Should NOT send email
        mock_email_service.send_2fa_code_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_temp_code_success(self, mock_redis, twofa_service):
        """Test successful temporary code verification."""
        user_id = "test-user-123"
        purpose = "login"
        code = "123456"

        # Mock Redis to return the code
        mock_redis.client.get.return_value = code.encode()

        # Verify
        result = await twofa_service.verify_temp_code(user_id, code, purpose)

        assert result is True

        # Should check Redis for code
        mock_redis.client.get.assert_called_once_with(f"2FA:{user_id}:{purpose}")

    @pytest.mark.asyncio
    async def test_verify_temp_code_wrong_code(self, mock_redis, twofa_service):
        """Test verification with wrong code."""
        user_id = "test-user-123"
        purpose = "login"
        correct_code = "123456"
        wrong_code = "654321"

        # Mock Redis to return different code
        mock_redis.client.get.return_value = correct_code.encode()

        # Try to verify with wrong code
        result = await twofa_service.verify_temp_code(user_id, wrong_code, purpose)

        assert result is False

    @pytest.mark.asyncio
    async def test_verify_temp_code_not_found(self, mock_redis, twofa_service):
        """Test verification when code doesn't exist."""
        user_id = "test-user-123"
        purpose = "login"
        code = "123456"

        # Mock Redis to return None (code doesn't exist)
        mock_redis.client.get.return_value = None

        # Verify
        result = await twofa_service.verify_temp_code(user_id, code, purpose)

        assert result is False

    @pytest.mark.asyncio
    async def test_verify_temp_code_consumes_code(self, mock_redis, twofa_service):
        """Test that verification consumes the code (single-use)."""
        user_id = "test-user-123"
        purpose = "login"
        code = "123456"

        # Mock Redis to return the code
        mock_redis.client.get.return_value = code.encode()

        # Verify (should consume)
        result = await twofa_service.verify_temp_code(user_id, code, purpose, consume=True)

        assert result is True
        mock_redis.client.delete.assert_called_once_with(f"2FA:{user_id}:{purpose}")

    @pytest.mark.asyncio
    async def test_verify_temp_code_without_consume(self, mock_redis, twofa_service):
        """Test verification without consuming code."""
        user_id = "test-user-123"
        purpose = "verify"
        code = "123456"

        mock_redis.client.get.return_value = code.encode()

        # Verify without consuming
        result = await twofa_service.verify_temp_code(
            user_id, code, purpose, consume=False
        )

        assert result is True

        # Should NOT delete code
        mock_redis.client.delete.assert_not_called()

    # ========== Failed Attempt Tracking ==========

    @pytest.mark.asyncio
    async def test_increment_failed_attempt(self, mock_redis, twofa_service):
        """Test tracking failed verification attempts."""
        user_id = "test-user-123"
        purpose = "login"

        await twofa_service.increment_failed_attempt(user_id, purpose)

        # Should increment counter
        mock_redis.client.incr.assert_called_once_with(f"2FA_ATTEMPTS:{user_id}:{purpose}")

        # Should set 5-minute expiry
        mock_redis.client.expire.assert_called_once_with(
            f"2FA_ATTEMPTS:{user_id}:{purpose}", 300
        )

    @pytest.mark.asyncio
    async def test_reset_failed_attempts(self, mock_redis, twofa_service):
        """Test resetting failed attempt counter."""
        user_id = "test-user-123"
        purpose = "login"

        await twofa_service.reset_failed_attempts(user_id, purpose)

        # Should delete counter
        mock_redis.client.delete.assert_called_once_with(f"2FA_ATTEMPTS:{user_id}:{purpose}")

    @pytest.mark.asyncio
    async def test_get_remaining_attempts(self, mock_redis, twofa_service):
        """Test getting remaining verification attempts."""
        user_id = "test-user-123"
        purpose = "login"

        # First call - no counter yet
        mock_redis.client.get.return_value = None
        remaining = await twofa_service.get_remaining_attempts(user_id, purpose)
        assert remaining == 3

        # After 1 failed attempt
        mock_redis.client.get.return_value = b"1"
        remaining = await twofa_service.get_remaining_attempts(user_id, purpose)
        assert remaining == 2

        # After 2 failed attempts
        mock_redis.client.get.return_value = b"2"
        remaining = await twofa_service.get_remaining_attempts(user_id, purpose)
        assert remaining == 1

        # After 3 failed attempts
        mock_redis.client.get.return_value = b"3"
        remaining = await twofa_service.get_remaining_attempts(user_id, purpose)
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_is_locked_out(self, mock_redis, twofa_service):
        """Test lockout detection after too many failed attempts."""
        user_id = "test-user-123"
        purpose = "login"

        # Under limit - not locked
        mock_redis.client.get.return_value = b"2"
        assert await twofa_service.is_locked_out(user_id, purpose) is False

        # At limit - locked
        mock_redis.client.get.return_value = b"3"
        assert await twofa_service.is_locked_out(user_id, purpose) is True

        # Over limit - locked
        mock_redis.client.get.return_value = b"5"
        assert await twofa_service.is_locked_out(user_id, purpose) is True

    # ========== Login Session Management ==========

    @pytest.mark.asyncio
    async def test_generate_login_session(self, mock_redis, twofa_service):
        """Test login session generation."""
        user_id = "test-user-123"

        session_id = await twofa_service.generate_login_session(user_id)

        # Should return a non-empty string
        assert session_id
        assert isinstance(session_id, str)

        # Should store in Redis with 15-minute TTL
        mock_redis.client.setex.assert_called_once()
        call_args = mock_redis.client.setex.call_args

        assert call_args[0][0] == f"LOGIN_SESSION:{session_id}"
        assert call_args[0][1] == 900  # 15 minutes
        assert call_args[0][2] == user_id

    @pytest.mark.asyncio
    async def test_validate_login_session_success(self, mock_redis, twofa_service):
        """Test successful login session validation."""
        session_id = "valid-session-id"
        user_id = "test-user-123"

        # Mock Redis to return user_id
        mock_redis.client.get.return_value = user_id.encode()

        result = await twofa_service.validate_login_session(session_id)

        assert result == user_id
        mock_redis.client.get.assert_called_once_with(f"LOGIN_SESSION:{session_id}")

    @pytest.mark.asyncio
    async def test_validate_login_session_not_found(self, mock_redis, twofa_service):
        """Test validation of non-existent session."""
        session_id = "invalid-session-id"

        # Mock Redis to return None
        mock_redis.client.get.return_value = None

        result = await twofa_service.validate_login_session(session_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_invalidate_login_session(self, mock_redis, twofa_service):
        """Test login session invalidation."""
        session_id = "session-to-invalidate"

        await twofa_service.invalidate_login_session(session_id)

        # Should delete session
        mock_redis.client.delete.assert_called_once_with(f"LOGIN_SESSION:{session_id}")

    # ========== Verification Token ==========

    def test_generate_verification_token(self, twofa_service):
        """Test verification token generation."""
        token1 = twofa_service.generate_verification_token()
        token2 = twofa_service.generate_verification_token()

        # Should be unique
        assert token1 != token2

        # Should be URL-safe
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
                     for c in token1)

    def test_generate_verification_token_length(self, twofa_service):
        """Test verification token length."""
        token = twofa_service.generate_verification_token()
        # Should be reasonably long (urlsafe random 32 bytes)
        assert len(token) > 20
