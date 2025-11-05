#!/usr/bin/env python3
"""
Dummy Email Service for Development
Mimics the expected email service API that the Auth API expects.
Also forwards emails via SMTP to MailHog for web UI viewing.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import smtplib
from email.message import EmailMessage
import asyncio
import os

app = FastAPI(title="Dummy Email Service", version="1.0.0")

# SMTP Configuration from environment
SMTP_HOST = os.getenv("SMTP_HOST", "mailhog")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
FROM_ADDRESS = os.getenv("FROM_ADDRESS", "noreply@activity-app.local")

class EmailRequest(BaseModel):
    to: str
    template: str
    subject: str
    data: dict

@app.post("/send")
async def send_email(request: EmailRequest):
    """Mock email sending - logs to console AND forwards to MailHog via SMTP."""
    print(f"\n{'='*60}")
    print(f"EMAIL SERVICE - Mock send")
    print(f"{'='*60}")
    print(f"To: {request.to}")
    print(f"Template: {request.template}")
    print(f"Subject: {request.subject}")
    print(f"Data: {request.data}")
    print(f"{'='*60}\n")

    # Also send to MailHog via SMTP
    try:
        msg = EmailMessage()
        msg["From"] = FROM_ADDRESS
        msg["To"] = request.to
        msg["Subject"] = request.subject

        # Create email body from template data (dynamic based on template type)
        if request.template == "email_verification":
            verification_link = request.data.get("verification_link", "")
            expires_hours = request.data.get("expires_hours", 24)
            body = f"""Please verify your email address.

Click the link below to verify:
{verification_link}

This link expires in {expires_hours} hours.
"""
        elif request.template == "password_reset":
            reset_link = request.data.get("reset_link", "")
            expires_hours = request.data.get("expires_hours", 1)
            body = f"""Password Reset Request

Click the link below to reset your password:
{reset_link}

This link expires in {expires_hours} hours.
"""
        elif request.template == "2fa_code":
            # Handle 2FA/verification code templates
            code = request.data.get("code", "")
            purpose = request.data.get("purpose", "verification")
            expires_minutes = request.data.get("expires_minutes", 5)

            purpose_messages = {
                "login": "Your login verification code",
                "reset": "Password reset verification code",
                "verify": "Email verification code",
                "email verification": "Email verification code"
            }

            purpose_text = purpose_messages.get(purpose, purpose.capitalize())

            body = f"""{purpose_text}

Your 6-digit verification code is: {code}

This code expires in {expires_minutes} minutes.

If you didn't request this, please ignore this email.
"""
        else:
            # Generic template
            body = f"""
Template: {request.template}
Subject: {request.subject}
Data: {request.data}
"""
        msg.set_content(body)

        # Send via SMTP to configured SMTP server
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.send_message(msg)
            print(f"✓ Forwarded to {SMTP_HOST}:{SMTP_PORT} via SMTP")
    except Exception as e:
        print(f"⚠ Failed to forward to SMTP: {str(e)}")

    # Simulate sending delay
    await asyncio.sleep(0.1)

    return {"status": "sent", "message_id": "mock-12345"}

@app.get("/")
async def root():
    return {"service": "Dummy Email Service", "status": "running"}

if __name__ == "__main__":
    import asyncio
    uvicorn.run(app, host="0.0.0.0", port=9000)
