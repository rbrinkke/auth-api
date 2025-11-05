"""
Two-Factor Authentication Service.

Handles TOTP (Time-based One-Time Password) authentication,
backup codes, and temporary verification codes.
"""
import base64
import secrets
import pyotp
import qrcode
import io
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

from app.config import settings
from app.core.redis_client import RedisClient
from app.services.email_service import EmailService


class TwoFactorError(Exception):
    """Base exception for 2FA operations."""
    pass


class InvalidCodeError(TwoFactorError):
    """Raised when an invalid TOTP or backup code is provided."""
    pass


class TwoFactorService:
    """Service for handling 2FA TOTP and backup codes."""

    def __init__(self, redis: RedisClient, email_svc: EmailService):
        self.redis = redis
        self.email_svc = email_svc
        # Encryption for TOTP secrets
        self.cipher_suite = Fernet(settings.encryption_key.encode())

    def generate_totp_secret(self) -> str:
        """Generate a new TOTP secret for a user."""
        # Generate random secret
        secret = pyotp.random_base32()
        return secret

    def encrypt_secret(self, secret: str) -> str:
        """Encrypt TOTP secret before storing in database."""
        encrypted = self.cipher_suite.encrypt(secret.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt TOTP secret from database."""
        encrypted_bytes = base64.b64decode(encrypted_secret.encode())
        decrypted = self.cipher_suite.decrypt(encrypted_bytes)
        return decrypted.decode()

    def generate_qr_code(self, secret: str, email: str) -> str:
        """Generate QR code for authenticator app setup."""
        # Create TOTP URI for QR code
        issuer = "AuthAPI"
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name=issuer
        )

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(totp_uri)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"

    def verify_totp_code(self, secret: str, code: str) -> bool:
        """Verify TOTP code from authenticator app."""
        try:
            totp = pyotp.TOTP(secret)
            # Allow 1 time step skew for clock drift (30 seconds)
            return totp.verify(code, valid_window=1)
        except Exception:
            return False

    def generate_backup_codes(self, count: int = 8) -> List[str]:
        """Generate backup codes for emergency use."""
        codes = []
        for _ in range(count):
            # Generate 8-digit backup code
            code = ''.join(secrets.choice('0123456789') for _ in range(8))
            codes.append(code)
        return codes

    def hash_backup_code(self, code: str) -> str:
        """Hash backup code before storing (single-use)."""
        import hashlib
        return hashlib.sha256(code.encode()).hexdigest()

    async def create_temp_code(
        self,
        user_id: str,
        purpose: str,
        email: Optional[str] = None
    ) -> str:
        """
        Create temporary 6-digit code for 2FA verification.

        Args:
            user_id: User ID
            purpose: Purpose ('login', 'reset', 'verify')
            email: User email (for sending code)

        Returns:
            The generated 6-digit code
        """
        # Generate 6-digit code
        code = ''.join(secrets.choice('0123456789') for _ in range(6))

        # Store in Redis with 5-minute expiry
        key = f"2FA:{user_id}:{purpose}"
        await self.redis.client.setex(key, 300, code)  # 5 minutes

        # Send code via email
        if email:
            await self.email_svc.send_2fa_code_email(email, code, purpose)

        return code

    async def verify_temp_code(
        self,
        user_id: str,
        code: str,
        purpose: str,
        consume: bool = True
    ) -> bool:
        """
        Verify temporary 2FA code.

        Args:
            user_id: User ID
            code: 6-digit code to verify
            purpose: Purpose ('login', 'reset', 'verify')
            consume: Whether to consume the code (single-use)

        Returns:
            True if code is valid, False otherwise
        """
        key = f"2FA:{user_id}:{purpose}"
        stored_code = await self.redis.client.get(key)

        if not stored_code:
            return False

        # Handle both bytes and string types from Redis
        if isinstance(stored_code, bytes):
            stored_code = stored_code.decode()

        if stored_code != code:
            return False

        # If consuming, delete the code
        if consume:
            await self.redis.client.delete(key)

        return True

    async def cleanup_expired_codes(self):
        """Clean up expired codes from Redis."""
        # Redis TTL handles this automatically, but we can force cleanup
        pattern = "2FA:*"
        keys = await self.redis.client.keys(pattern)
        # Keys with TTL will expire automatically, no manual cleanup needed
        pass

    async def get_remaining_attempts(self, user_id: str, purpose: str) -> int:
        """
        Get remaining verification attempts.

        For security, we track failed attempts in Redis.
        """
        key = f"2FA_ATTEMPTS:{user_id}:{purpose}"
        attempts = await self.redis.client.get(key)
        if not attempts:
            return 3  # Max attempts
        return max(0, 3 - int(attempts.decode()))

    async def increment_failed_attempt(self, user_id: str, purpose: str):
        """Increment failed verification attempt counter."""
        key = f"2FA_ATTEMPTS:{user_id}:{purpose}"
        await self.redis.client.incr(key)
        # Set 5-minute lockout after max attempts
        await self.redis.client.expire(key, 300)

    async def reset_failed_attempts(self, user_id: str, purpose: str):
        """Reset failed attempt counter after successful verification."""
        key = f"2FA_ATTEMPTS:{user_id}:{purpose}"
        await self.redis.client.delete(key)

    async def is_locked_out(self, user_id: str, purpose: str) -> bool:
        """Check if user is locked out due to too many failed attempts."""
        remaining = await self.get_remaining_attempts(user_id, purpose)
        return remaining <= 0

    async def generate_login_session(self, user_id: str) -> str:
        """
        Generate temporary login session after successful 2FA.

        This prevents users from having to re-enter their 2FA code
        for subsequent requests in the same session.
        """
        session_id = secrets.token_urlsafe(32)
        key = f"LOGIN_SESSION:{session_id}"
        await self.redis.client.setex(key, 900, user_id)  # 15 minutes
        return session_id

    async def validate_login_session(self, session_id: str) -> Optional[str]:
        """
        Validate login session and return user_id.

        Returns None if session is invalid or expired.
        """
        key = f"LOGIN_SESSION:{session_id}"
        user_id = await self.redis.client.get(key)
        if user_id:
            return user_id.decode()
        return None

    async def invalidate_login_session(self, session_id: str):
        """Invalidate login session (logout)."""
        key = f"LOGIN_SESSION:{session_id}"
        await self.redis.client.delete(key)

    def generate_verification_token(self) -> str:
        """Generate secure verification token for email verification."""
        return secrets.token_urlsafe(32)
