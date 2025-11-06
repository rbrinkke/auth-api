import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import Depends
from app.config import Settings, get_settings

class EmailService:
    def __init__(self, settings: Settings = Depends(get_settings)):
        self.settings = settings

    def send_email(self, to_email: str, subject: str, html_content: str):
        msg = MIMEMultipart()
        msg['From'] = self.settings.EMAIL_FROM
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))

        try:
            with smtplib.SMTP(self.settings.EMAIL_HOST, self.settings.EMAIL_PORT) as server:
                server.starttls()
                server.login(self.settings.EMAIL_USERNAME, self.settings.EMAIL_PASSWORD)
                server.sendmail(self.settings.EMAIL_FROM, to_email, msg.as_string())
        except Exception as e:
            print(f"Failed to send email: {e}")
            pass

    def send_verification_email(self, email: str, token: str):
        verification_url = f"{self.settings.FRONTEND_URL}/verify?token={token}"
        subject = "Verify Your Account"
        html_content = f"""
        <html>
        <body>
            <p>Hi,</p>
            <p>Thanks for registering. Please click the link below to verify your account:</p>
            <p><a href="{verification_url}">{verification_url}</a></p>
            <p>This link will expire in 24 hours.</p>
        </body>
        </html>
        """
        self.send_email(email, subject, html_content)

    def send_password_reset_email(self, email: str, token: str):
        reset_url = f"{self.settings.FRONTEND_URL}/reset-password?token={token}"
        subject = "Reset Your Password"
        html_content = f"""
        <html>
        <body>
            <p>Hi,</p>
            <p>You requested a password reset. Click the link below to reset your password:</p>
            <p><a href="{reset_url}">{reset_url}</a></p>
            <p>This link will expire in 1 hour. If you did not request this, please ignore this email.</p>
        </body>
        </html>
        """
        self.send_email(email, subject, html_content)
