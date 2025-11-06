import httpx
import asyncio
from fastapi import Depends
from app.config import get_settings
from app.core.logging_config import get_logger
from app.middleware.correlation import correlation_id_var

logger = get_logger(__name__)

class EmailService:
    def __init__(self, settings = Depends(get_settings)):
        self.settings = settings
        self.email_service_url = settings.EMAIL_SERVICE_URL
        self.timeout = settings.EMAIL_SERVICE_TIMEOUT

    async def send_email(self, to_email: str, template: str, subject: str, data: dict):
        logger.info("email_send_attempt",
                   to_email=to_email,
                   template=template,
                   subject=subject)

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
                result = response.json()

                logger.info("email_send_success",
                           to_email=to_email,
                           template=template,
                           status_code=response.status_code)

                return result
            except httpx.HTTPStatusError as e:
                logger.error("email_send_http_error",
                            to_email=to_email,
                            template=template,
                            status_code=e.response.status_code,
                            error=str(e),
                            exc_info=True)
                return {"status": "error", "message": str(e)}
            except Exception as e:
                logger.error("email_send_failed",
                            to_email=to_email,
                            template=template,
                            error=str(e),
                            exc_info=True)
                return {"status": "error", "message": str(e)}

    async def send_verification_email(self, email: str, code: str):
        subject = "Verify Your Account"
        data = {
            "code": code,
            "purpose": "email verification",
            "expires_minutes": 10
        }
        logger.info("verification_email_prepare", email=email, purpose="email_verification")
        return await self.send_email(email, "2fa_code", subject, data)

    async def send_password_reset_email(self, email: str, code: str):
        subject = "Reset Your Password"
        data = {
            "code": code,
            "purpose": "reset",
            "expires_minutes": 10
        }
        logger.info("password_reset_email_prepare", email=email, purpose="password_reset")
        return await self.send_email(email, "2fa_code", subject, data)

    async def send_2fa_code(self, email: str, code: str, purpose: str = "verification"):
        subject = f"Your {purpose.title()} Code"
        data = {
            "code": code,
            "purpose": purpose,
            "expires_minutes": 10
        }
        logger.info("2fa_code_email_prepare", email=email, purpose=purpose)
        return await self.send_email(email, "2fa_code", subject, data)
