"""
Email service client for sending transactional emails.

Communicates with the external email service via HTTP.
"""
import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Client for the email service."""
    
    def __init__(self):
        self.base_url = settings.email_service_url
        self.timeout = settings.email_service_timeout
    
    async def send_email(
        self,
        to: str,
        template: str,
        subject: str,
        data: dict[str, Any]
    ) -> bool:
        """
        Send an email via the email service.
        
        Args:
            to: Recipient email address
            template: Template name (e.g., "email_verification")
            subject: Email subject line
            data: Template data (variables to interpolate)
            
        Returns:
            True if email was sent successfully, False otherwise
            
        Note:
            Failures are logged but don't raise exceptions to prevent
            blocking the main application flow.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/send",
                    json={
                        "to": to,
                        "template": template,
                        "subject": subject,
                        "data": data
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    logger.info(f"Email sent successfully to {to} (template: {template})")
                    return True
                else:
                    logger.error(
                        f"Failed to send email to {to}. "
                        f"Status: {response.status_code}, "
                        f"Response: {response.text}"
                    )
                    return False
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout sending email to {to} (template: {template})")
            return False
        except Exception as e:
            logger.error(f"Error sending email to {to}: {str(e)}")
            return False
    
    async def send_verification_email(self, email: str, code: str) -> bool:
        """
        Send email verification code (6-digit).

        Args:
            email: Recipient email
            code: 6-digit verification code

        Returns:
            True if sent successfully
        """
        # Use the same 2FA email template for consistency
        return await self.send_2fa_code_email(email, code, "verify")
    
    async def send_2fa_code_email(self, email: str, code: str, purpose: str) -> bool:
        """
        Send 2FA verification code via email.

        Args:
            email: Recipient email address
            code: 6-digit verification code
            purpose: Purpose of the code (login, reset, verify)

        Returns:
            True if sent successfully
        """
        # Get appropriate subject and message based on purpose
        subjects = {
            "login": "Your login verification code",
            "reset": "Password reset verification code",
            "verify": "Email verification code"
        }

        purposes = {
            "login": "login",
            "reset": "password reset",
            "verify": "email verification"
        }

        subject = subjects.get(purpose, "Verification code")
        purpose_text = purposes.get(purpose, purpose)

        return await self.send_email(
            to=email,
            template="2fa_code",
            subject=subject,
            data={
                "code": code,
                "purpose": purpose_text,
                "expires_minutes": 5
            }
        )

    async def send_password_reset_email(self, email: str, code: str) -> bool:
        """
        Send password reset code (6-digit).

        Args:
            email: Recipient email
            code: 6-digit reset code

        Returns:
            True if sent successfully
        """
        # Use the same 2FA email template for consistency
        return await self.send_2fa_code_email(email, code, "reset")
    
    async def send_welcome_email(self, email: str) -> bool:
        """
        Send welcome email after successful verification.
        
        Args:
            email: Recipient email
            
        Returns:
            True if sent successfully
        """
        return await self.send_email(
            to=email,
            template="welcome",
            subject="Welcome to our platform!",
            data={"email": email}
        )


# Global email service instance
email_service = EmailService()


def get_email_service() -> EmailService:
    """
    Dependency injection function for EmailService.

    Returns:
        EmailService: Configured email service instance

    This enables easy mocking during testing:
        app.dependency_overrides[get_email_service] = get_mock_email_service
    """
    return email_service

