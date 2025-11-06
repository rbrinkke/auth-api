import pyotp
import qrcode
import qrcode.image.svg
from io import BytesIO
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.connection import get_db
from app.db import procedures
from app.core.exceptions import (
    UserNotFoundError,
    TwoFactorSetupError,
    TwoFactorVerificationError
)

class TwoFactorService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

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

    def setup_2fa(self, user_id: int) -> dict:
        user = procedures.sp_get_user_by_id(self.db, user_id)
        if not user:
            raise UserNotFoundError()

        if user.is_2fa_enabled:
            raise TwoFactorSetupError("2FA is already enabled.")

        secret = self.generate_2fa_secret()
        procedures.sp_set_2fa_secret(self.db, user_id, secret, is_verified=False)

        uri = self.get_totp_uri(user.email, secret)
        qr_svg = self.generate_qr_code_svg(uri)

        return {"qr_code_svg": qr_svg, "secret": secret}

    def verify_and_enable_2fa(self, user_id: int, code: str) -> dict:
        user = procedures.sp_get_user_by_id(self.db, user_id)
        if not user or not user.two_factor_secret:
            raise TwoFactorSetupError("2FA setup not initiated or user not found.")

        if user.is_2fa_enabled:
            raise TwoFactorSetupError("2FA is already enabled.")

        if self.verify_2fa_code(user.two_factor_secret, code):
            procedures.sp_set_2fa_secret(self.db, user_id, user.two_factor_secret, is_verified=True)
            return {"message": "2FA enabled successfully."}
        else:
            raise TwoFactorVerificationError("Invalid 2FA code.")

    def disable_2fa(self, user_id: int) -> dict:
        procedures.sp_disable_2fa(self.db, user_id)
        return {"message": "2FA disabled successfully."}

    def validate_2fa_challenge(self, user_id: int, code: str):
        user = procedures.sp_get_user_by_id(self.db, user_id)
        if not user or not user.is_2fa_enabled or not user.two_factor_secret:
            raise TwoFactorVerificationError("2FA not enabled for this user.")

        if not self.verify_2fa_code(user.two_factor_secret, code):
            raise TwoFactorVerificationError("Invalid 2FA code.")
