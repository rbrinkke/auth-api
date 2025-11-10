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
from app.core.logging_config import get_logger
from app.middleware.correlation import trace_id_var

logger = get_logger(__name__)

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
        logger.info("2fa_setup_start", user_id=str(user_id))
        logger.debug("2fa_fetching_user", user_id=str(user_id))

        user = await procedures.sp_get_user_by_id(self.db, user_id)
        if not user:
            logger.warning("2fa_setup_failed", user_id=str(user_id), reason="user_not_found")
            raise UserNotFoundError()
        logger.debug("2fa_user_found", user_id=str(user_id), email=user.email)

        totp_enabled_key = f"2FA:{user_id}:totp_enabled"
        logger.debug("2fa_checking_enabled_status", user_id=str(user_id), redis_key=totp_enabled_key)
        if self.redis_client.get(totp_enabled_key) == "true":
            logger.warning("2fa_setup_failed", user_id=str(user_id), reason="already_enabled")
            raise TwoFactorSetupError("2FA is already enabled.")

        logger.debug("2fa_generating_secret", user_id=str(user_id))
        secret = self.generate_2fa_secret()
        logger.debug("2fa_secret_generated_local", user_id=str(user_id), secret_length=len(secret))
        setup_pending_key = f"2FA:{user_id}:setup_pending"
        logger.debug("2fa_storing_secret_redis", user_id=str(user_id), redis_key=setup_pending_key, ttl=600)
        self.redis_client.setex(setup_pending_key, 600, secret)
        logger.debug("2fa_secret_stored", user_id=str(user_id))

        logger.info("2fa_secret_generated",
                   user_id=str(user_id),
                   expires_in_seconds=600)

        logger.debug("2fa_generating_totp_uri", user_id=str(user_id), email=user.email)
        uri = self.get_totp_uri(user.email, secret)
        logger.debug("2fa_uri_generated", user_id=str(user_id), uri_length=len(uri))
        logger.debug("2fa_generating_qr_code", user_id=str(user_id))
        qr_svg = self.generate_qr_code_svg(uri)
        logger.debug("2fa_qr_code_generated", user_id=str(user_id), qr_svg_length=len(qr_svg))

        logger.info("2fa_setup_complete", user_id=str(user_id), email=user.email)

        return {"qr_code_svg": qr_svg, "secret": secret}

    async def verify_and_enable_2fa(self, user_id: UUID, code: str) -> dict:
        logger.info("2fa_enable_start", user_id=str(user_id))
        logger.debug("2fa_enable_fetching_user", user_id=str(user_id))

        user = await procedures.sp_get_user_by_id(self.db, user_id)
        if not user:
            logger.warning("2fa_enable_failed", user_id=str(user_id), reason="user_not_found")
            raise UserNotFoundError()
        logger.debug("2fa_enable_user_found", user_id=str(user_id))

        setup_pending_key = f"2FA:{user_id}:setup_pending"
        logger.debug("2fa_enable_fetching_pending_secret", user_id=str(user_id), redis_key=setup_pending_key)
        pending_secret = self.redis_client.get(setup_pending_key)

        if not pending_secret:
            logger.warning("2fa_enable_failed",
                          user_id=str(user_id),
                          reason="setup_not_initiated_or_expired")
            raise TwoFactorSetupError("2FA setup not initiated or expired.")
        logger.debug("2fa_enable_secret_found", user_id=str(user_id))

        logger.debug("2fa_enable_verifying_code", user_id=str(user_id), code_length=len(code))
        if self.verify_2fa_code(pending_secret, code):
            logger.debug("2fa_enable_code_verified", user_id=str(user_id))
            totp_secret_key = f"2FA:{user_id}:totp_secret"
            totp_enabled_key = f"2FA:{user_id}:totp_enabled"

            logger.debug("2fa_enable_storing_permanent_secret", user_id=str(user_id))
            self.redis_client.set(totp_secret_key, pending_secret)
            self.redis_client.set(totp_enabled_key, "true")
            self.redis_client.delete(setup_pending_key)
            logger.debug("2fa_enable_redis_updated", user_id=str(user_id))

            logger.info("2fa_enable_success", user_id=str(user_id))

            return {"message": "2FA enabled successfully."}
        else:
            logger.debug("2fa_enable_code_invalid", user_id=str(user_id))
            logger.warning("2fa_enable_failed",
                          user_id=str(user_id),
                          reason="invalid_code")
            raise TwoFactorVerificationError("Invalid 2FA code.")

    async def disable_2fa(self, user_id: UUID) -> dict:
        logger.info("2fa_disable_start", user_id=str(user_id))

        totp_secret_key = f"2FA:{user_id}:totp_secret"
        totp_enabled_key = f"2FA:{user_id}:totp_enabled"
        logger.debug("2fa_disable_deleting_keys", user_id=str(user_id), keys=[totp_secret_key, totp_enabled_key])

        self.redis_client.delete(totp_secret_key)
        self.redis_client.delete(totp_enabled_key)
        logger.debug("2fa_disable_keys_deleted", user_id=str(user_id))

        logger.info("2fa_disable_success", user_id=str(user_id))

        return {"message": "2FA disabled successfully."}

    async def validate_2fa_challenge(self, user_id: UUID, code: str):
        logger.info("2fa_challenge_start", user_id=str(user_id))

        totp_enabled_key = f"2FA:{user_id}:totp_enabled"
        totp_secret_key = f"2FA:{user_id}:totp_secret"

        logger.debug("2fa_challenge_checking_enabled", user_id=str(user_id), redis_key=totp_enabled_key)
        if self.redis_client.get(totp_enabled_key) != "true":
            logger.warning("2fa_challenge_failed",
                          user_id=str(user_id),
                          reason="2fa_not_enabled")
            raise TwoFactorVerificationError("2FA not enabled for this user.")
        logger.debug("2fa_challenge_enabled_confirmed", user_id=str(user_id))

        logger.debug("2fa_challenge_fetching_secret", user_id=str(user_id), redis_key=totp_secret_key)
        secret = self.redis_client.get(totp_secret_key)
        if not secret:
            logger.warning("2fa_challenge_failed",
                          user_id=str(user_id),
                          reason="configuration_missing")
            raise TwoFactorVerificationError("2FA configuration missing.")
        logger.debug("2fa_challenge_secret_found", user_id=str(user_id))

        logger.debug("2fa_challenge_verifying_code", user_id=str(user_id), code_length=len(code))
        if not self.verify_2fa_code(secret, code):
            logger.debug("2fa_challenge_code_invalid", user_id=str(user_id))
            logger.warning("2fa_challenge_failed",
                          user_id=str(user_id),
                          reason="invalid_code")
            raise TwoFactorVerificationError("Invalid 2FA code.")
        logger.debug("2fa_challenge_code_verified", user_id=str(user_id))

        logger.info("2fa_challenge_success", user_id=str(user_id))
