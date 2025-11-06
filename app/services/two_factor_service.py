import pyotp
import qrcode
import qrcode.image.svg
from io import BytesIO
from uuid import UUID
from fastapi import Depends
import asyncpg
import redis
from app.db.connection import get_db_connection
from app.core.redis_client import get_redis_client
from app.db import procedures
from app.core.exceptions import (
    UserNotFoundError,
    TwoFactorSetupError,
    TwoFactorVerificationError
)

class TwoFactorService:
    def __init__(
        self,
        db: asyncpg.Connection = Depends(get_db_connection),
        redis_client: redis.Redis = Depends(get_redis_client)
    ):
        self.db = db
        self.redis_client = redis_client

    def generate_2fa_secret(self) -> str:
        return pyotp.random_base32()

    def get_totp_uri(self, email: str, secret: str) -> str:
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name="AuthApp"
        )

    def generate_qr_code_svg(self, uri: str) -> str:
        img = qrcode.make(uri, image_factory=qrcode.image.svg.SvgPathImage)
        stream = BytesIO()
        img.save(stream)
        return stream.getvalue().decode('utf-8')

    def verify_2fa_code(self, secret: str, code: str) -> bool:
        totp = pyotp.TOTP(secret)
        return totp.verify(code)

    async def setup_2fa(self, user_id: UUID) -> dict:
        user = await procedures.sp_get_user_by_id(self.db, user_id)
        if not user:
            raise UserNotFoundError()

        totp_enabled_key = f"2FA:{user_id}:totp_enabled"
        if self.redis_client.get(totp_enabled_key) == b"true":
            raise TwoFactorSetupError("2FA is already enabled.")

        secret = self.generate_2fa_secret()
        setup_pending_key = f"2FA:{user_id}:setup_pending"
        self.redis_client.setex(setup_pending_key, 600, secret)

        uri = self.get_totp_uri(user.email, secret)
        qr_svg = self.generate_qr_code_svg(uri)

        return {"qr_code_svg": qr_svg, "secret": secret}

    async def verify_and_enable_2fa(self, user_id: UUID, code: str) -> dict:
        user = await procedures.sp_get_user_by_id(self.db, user_id)
        if not user:
            raise UserNotFoundError()

        setup_pending_key = f"2FA:{user_id}:setup_pending"
        pending_secret = self.redis_client.get(setup_pending_key)

        if not pending_secret:
            raise TwoFactorSetupError("2FA setup not initiated or expired.")

        pending_secret_str = pending_secret.decode('utf-8') if isinstance(pending_secret, bytes) else pending_secret

        if self.verify_2fa_code(pending_secret_str, code):
            totp_secret_key = f"2FA:{user_id}:totp_secret"
            totp_enabled_key = f"2FA:{user_id}:totp_enabled"

            self.redis_client.set(totp_secret_key, pending_secret_str)
            self.redis_client.set(totp_enabled_key, "true")
            self.redis_client.delete(setup_pending_key)

            return {"message": "2FA enabled successfully."}
        else:
            raise TwoFactorVerificationError("Invalid 2FA code.")

    async def disable_2fa(self, user_id: UUID) -> dict:
        totp_secret_key = f"2FA:{user_id}:totp_secret"
        totp_enabled_key = f"2FA:{user_id}:totp_enabled"

        self.redis_client.delete(totp_secret_key)
        self.redis_client.delete(totp_enabled_key)

        return {"message": "2FA disabled successfully."}

    async def validate_2fa_challenge(self, user_id: UUID, code: str):
        totp_enabled_key = f"2FA:{user_id}:totp_enabled"
        totp_secret_key = f"2FA:{user_id}:totp_secret"

        if self.redis_client.get(totp_enabled_key) != b"true":
            raise TwoFactorVerificationError("2FA not enabled for this user.")

        secret = self.redis_client.get(totp_secret_key)
        if not secret:
            raise TwoFactorVerificationError("2FA configuration missing.")

        secret_str = secret.decode('utf-8') if isinstance(secret, bytes) else secret

        if not self.verify_2fa_code(secret_str, code):
            raise TwoFactorVerificationError("Invalid 2FA code.")
