import httpx
import asyncio
from fastapi import Depends
from app.config import get_settings
from app.core.logging_config import get_logger
from app.middleware.correlation import trace_id_var

logger = get_logger(__name__)

class EmailService:
    def __init__(self, settings = Depends(get_settings)):
        self.settings = settings
        self.email_service_url = settings.EMAIL_SERVICE_URL
        self.service_token = settings.SERVICE_AUTH_TOKEN
        self.timeout = settings.EMAIL_SERVICE_TIMEOUT

    async def send_email(self, recipients: str, template: str, data: dict, priority: str = 'high'):
        """Send email via centralized email-api service.

        Args:
            recipients: Email address of recipient
            template: Template name (e.g., 'verification_code', 'password_reset')
            data: Template data (varies per template)
            priority: Email priority ('high', 'medium', 'low')
        """
        logger.info("email_send_attempt",
                   recipients=recipients,
                   template=template,
                   priority=priority)
        logger.debug("email_constructing_payload", recipients=recipients, template=template, data_keys=list(data.keys()))

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "recipients": recipients,
                "template": template,
                "data": data,
                "priority": priority,
                "provider": "smtp"
            }

            headers = {
                "Content-Type": "application/json",
                "X-Service-Token": self.service_token
            }

            logger.debug("email_payload_constructed", recipients=recipients, payload_size=len(str(payload)))
            logger.debug("email_sending_http_request", url=f"{self.email_service_url}/send", timeout=self.timeout)

            try:
                response = await client.post(
                    f"{self.email_service_url}/send",
                    json=payload,
                    headers=headers
                )
                logger.debug("email_http_response_received", status_code=response.status_code, recipients=recipients)
                response.raise_for_status()
                result = response.json()
                logger.debug("email_response_parsed", recipients=recipients, result_keys=list(result.keys()) if isinstance(result, dict) else "non-dict")

                logger.info("email_send_success",
                           recipients=recipients,
                           template=template,
                           job_id=result.get('job_id'),
                           status_code=response.status_code)

                return result
            except httpx.HTTPStatusError as e:
                logger.error("email_send_http_error",
                            recipients=recipients,
                            template=template,
                            status_code=e.response.status_code,
                            error=str(e),
                            exc_info=True)
                return {"status": "error", "message": str(e)}
            except Exception as e:
                logger.error("email_send_failed",
                            recipients=recipients,
                            template=template,
                            error=str(e),
                            exc_info=True)
                return {"status": "error", "message": str(e)}

    async def send_verification_email(self, email: str, code: str):
        """Send email verification code to user.

        Args:
            email: User's email address
            code: 6-digit verification code
        """
        logger.debug("email_preparing_verification", email=email, code_length=len(code))

        # Extract name from email as fallback (username part)
        name = email.split('@')[0]

        data = {
            "code": code,
            "name": name,
            "purpose": "email verification",
            "purpose_description": "to verify your email address and activate your account",
            "expiry_minutes": 10
        }
        logger.info("verification_email_prepare", email=email, purpose="email_verification")
        logger.debug("email_calling_send_email", email=email, template="verification_code")
        return await self.send_email(
            recipients=email,
            template="verification_code",
            data=data,
            priority="high"
        )

    async def send_password_reset_email(self, email: str, code: str):
        """Send password reset code to user.

        Args:
            email: User's email address
            code: 6-digit reset code
        """
        # Extract name from email as fallback
        name = email.split('@')[0]

        data = {
            "code": code,
            "name": name,
            "purpose": "password reset",
            "purpose_description": "to reset your password securely",
            "expiry_minutes": 10
        }
        logger.info("password_reset_email_prepare", email=email, purpose="password_reset")
        return await self.send_email(
            recipients=email,
            template="verification_code",
            data=data,
            priority="high"
        )

    async def send_2fa_code(self, email: str, code: str, purpose: str = "two-factor authentication"):
        """Send 2FA code to user for login verification.

        Args:
            email: User's email address
            code: 6-digit 2FA code
            purpose: Purpose description (default: "two-factor authentication")
        """
        # Extract name from email as fallback
        name = email.split('@')[0]

        data = {
            "code": code,
            "name": name,
            "purpose": purpose,
            "purpose_description": f"to complete your {purpose} securely",
            "expiry_minutes": 5  # Shorter expiry for 2FA codes
        }
        logger.info("2fa_code_email_prepare", email=email, purpose=purpose)
        return await self.send_email(
            recipients=email,
            template="verification_code",
            data=data,
            priority="high"
        )
