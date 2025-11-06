import httpx
import asyncio
import logging
from fastapi import Depends
from app.config import get_settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self, settings = Depends(get_settings)):
        self.settings = settings
        self.email_service_url = settings.EMAIL_SERVICE_URL
        self.timeout = settings.EMAIL_SERVICE_TIMEOUT

    async def send_email(self, to_email: str, template: str, subject: str, data: dict):
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "to": to_email,
                "template": template,
                "subject": subject,
                "data": data
            }
            try:
                response = await client.post(f"{self.email_service_url}/send", json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to send email: {e}")
                return {"status": "error", "message": str(e)}

    async def send_verification_email(self, email: str, code: str):
        subject = "Verify Your Account"
        data = {
            "code": code,
            "purpose": "email verification",
            "expires_minutes": 10
        }
        return await self.send_email(email, "2fa_code", subject, data)

    async def send_password_reset_email(self, email: str, code: str):
        subject = "Reset Your Password"
        data = {
            "code": code,
            "purpose": "reset",
            "expires_minutes": 10
        }
        return await self.send_email(email, "2fa_code", subject, data)

    async def send_2fa_code(self, email: str, code: str, purpose: str = "verification"):
        subject = f"Your {purpose.title()} Code"
        data = {
            "code": code,
            "purpose": purpose,
            "expires_minutes": 10
        }
        return await self.send_email(email, "2fa_code", subject, data)
