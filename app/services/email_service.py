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
    
    async def send_verification_email(self, email: str, token: str) -> bool:
        """
        Send email verification link.
        
        Args:
            email: Recipient email
            token: Verification token
            
        Returns:
            True if sent successfully
        """
        verification_url = f"{settings.frontend_url}/verify?token={token}"
        
        return await self.send_email(
            to=email,
            template="email_verification",
            subject="Verify your email address",
            data={
                "verification_link": verification_url,
                "expires_hours": settings.verification_token_ttl // 3600
            }
        )
    
    async def send_password_reset_email(self, email: str, token: str) -> bool:
        """
        Send password reset link.
        
        Args:
            email: Recipient email
            token: Reset token
            
        Returns:
            True if sent successfully
        """
        reset_url = f"{settings.frontend_url}/reset-password?token={token}"
        
        return await self.send_email(
            to=email,
            template="password_reset",
            subject="Reset your password",
            data={
                "reset_link": reset_url,
                "expires_hours": settings.reset_token_ttl // 3600
            }
        )
    
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

