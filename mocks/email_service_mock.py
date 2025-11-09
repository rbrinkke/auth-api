#!/usr/bin/env python3
"""
Email Service Mock Server

Production-quality mock server for email service testing.
Provides comprehensive email sending simulation with validation,
storage, and error injection capabilities.

Usage:
    python email_service_mock.py
    # or
    uvicorn email_service_mock:app --reload --port 9000

Features:
    - Template validation (2fa_code, email_verification, password_reset)
    - In-memory email storage for test inspection
    - Error injection via query parameters
    - Email retrieval by recipient
    - Test isolation via clear endpoint
"""

import asyncio
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, status, Query, Depends
from pydantic import BaseModel, Field, field_validator
import uvicorn

try:
    from base.mock_base import create_mock_app, create_health_response
    from base.error_injection import check_error_simulation
except ImportError:
    from mocks.base.mock_base import create_mock_app, create_health_response
    from mocks.base.error_injection import check_error_simulation

# Initialize FastAPI app
app = create_mock_app(
    title="Email Service Mock API",
    description="Mock server for email sending endpoints with template validation and storage",
    version="1.0.0"
)

# In-memory storage for sent emails
_sent_emails: List[Dict[str, Any]] = []
_email_counter = 0


# ============================================================================
# Pydantic Models
# ============================================================================

class EmailData2FA(BaseModel):
    """Data for 2FA code template."""
    code: str = Field(..., min_length=4, max_length=10, description="Verification code")
    purpose: str = Field(..., min_length=1, max_length=100, description="Purpose of the code")
    expires_minutes: int = Field(default=10, ge=1, le=60, description="Expiration in minutes")


class EmailDataVerification(BaseModel):
    """Data for email verification template."""
    verification_link: str = Field(..., min_length=1, description="Verification URL")
    expires_hours: int = Field(default=24, ge=1, le=72, description="Expiration in hours")


class EmailDataPasswordReset(BaseModel):
    """Data for password reset template."""
    reset_link: str = Field(..., min_length=1, description="Password reset URL")
    expires_hours: int = Field(default=1, ge=1, le=24, description="Expiration in hours")


class EmailRequest(BaseModel):
    """Email send request matching the real email service API."""
    to: str = Field(..., description="Recipient email address")
    template: str = Field(..., description="Email template name")
    subject: str = Field(..., min_length=1, max_length=200, description="Email subject")
    data: Dict[str, Any] = Field(..., description="Template data")

    @field_validator("to")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v

    @field_validator("template")
    @classmethod
    def validate_template(cls, v: str) -> str:
        """Validate template name."""
        valid_templates = ["2fa_code", "email_verification", "password_reset"]
        if v not in valid_templates:
            raise ValueError(f"Invalid template. Must be one of: {', '.join(valid_templates)}")
        return v

    def validate_template_data(self) -> None:
        """Validate that data matches the template requirements."""
        if self.template == "2fa_code":
            EmailData2FA(**self.data)
        elif self.template == "email_verification":
            EmailDataVerification(**self.data)
        elif self.template == "password_reset":
            EmailDataPasswordReset(**self.data)


class EmailResponse(BaseModel):
    """Response from email send endpoint."""
    status: str = Field(..., description="Send status")
    message_id: str = Field(..., description="Unique message identifier")
    timestamp: str = Field(..., description="ISO 8601 timestamp")


class StoredEmail(BaseModel):
    """Stored email record for testing inspection."""
    message_id: str
    to: str
    template: str
    subject: str
    data: Dict[str, Any]
    timestamp: str
    send_count: int = 1


class EmailListResponse(BaseModel):
    """Response for email listing endpoints."""
    total: int
    emails: List[StoredEmail]


# ============================================================================
# Endpoints
# ============================================================================

@app.post("/send", response_model=EmailResponse, status_code=status.HTTP_200_OK)
async def send_email(
    request: EmailRequest,
    error_check = Depends(check_error_simulation)
) -> EmailResponse:
    """
    Send an email (mock endpoint).

    Validates the email request, stores it in memory, and returns a success response.

    **Template Data Requirements:**

    - `2fa_code`: Requires `code`, `purpose`, `expires_minutes`
    - `email_verification`: Requires `verification_link`, `expires_hours`
    - `password_reset`: Requires `reset_link`, `expires_hours`

    **Error Simulation:**

    Use query parameter `?simulate_error=<type>` to test error scenarios:
    - `timeout`: 408 Request Timeout (after 5s delay)
    - `500`: 500 Internal Server Error
    - `400`: 400 Bad Request
    - `503`: 503 Service Unavailable

    **Example:**
    ```bash
    curl -X POST http://localhost:9000/send \
      -H "Content-Type: application/json" \
      -d '{
        "to": "user@example.com",
        "template": "2fa_code",
        "subject": "Your Verification Code",
        "data": {
          "code": "123456",
          "purpose": "login",
          "expires_minutes": 10
        }
      }'
    ```

    Args:
        request: Email request with recipient, template, subject, and data

    Returns:
        EmailResponse with status, message_id, and timestamp

    Raises:
        HTTPException: 422 if template data validation fails
        HTTPException: Various codes if error simulation is enabled
    """
    global _email_counter

    # Validate template-specific data
    try:
        request.validate_template_data()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid template data: {str(e)}"
        )

    # Generate unique message ID
    _email_counter += 1
    message_id = f"mock-{uuid.uuid4().hex[:8]}-{_email_counter}"
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Store email for testing inspection
    stored_email = {
        "message_id": message_id,
        "to": request.to,
        "template": request.template,
        "subject": request.subject,
        "data": request.data,
        "timestamp": timestamp,
        "send_count": 1
    }

    # Check if email to same recipient with same template exists
    # (simulates resending scenarios)
    existing = next(
        (email for email in _sent_emails
         if email["to"] == request.to and email["template"] == request.template),
        None
    )

    if existing:
        existing["send_count"] += 1
        existing["timestamp"] = timestamp
        existing["data"] = request.data
        existing["subject"] = request.subject
    else:
        _sent_emails.append(stored_email)

    # Simulate slight network delay
    await asyncio.sleep(0.05)

    return EmailResponse(
        status="sent",
        message_id=message_id,
        timestamp=timestamp
    )


@app.get("/emails", response_model=EmailListResponse)
async def get_all_emails(
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum emails to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination")
) -> EmailListResponse:
    """
    Retrieve all sent emails (testing utility).

    Returns all emails stored in memory, useful for test assertions.

    **Example:**
    ```bash
    curl http://localhost:9000/emails
    ```

    Args:
        limit: Maximum number of emails to return
        offset: Pagination offset

    Returns:
        EmailListResponse with total count and email list
    """
    emails = _sent_emails[offset:offset + limit]
    return EmailListResponse(
        total=len(_sent_emails),
        emails=[StoredEmail(**email) for email in emails]
    )


@app.get("/emails/{recipient_email}", response_model=EmailListResponse)
async def get_emails_by_recipient(
    recipient_email: str,
    template: Optional[str] = Query(None, description="Filter by template")
) -> EmailListResponse:
    """
    Retrieve emails sent to a specific recipient.

    Useful for testing that specific emails were sent to a user.

    **Example:**
    ```bash
    # Get all emails for user
    curl http://localhost:9000/emails/user@example.com

    # Get only 2FA emails for user
    curl http://localhost:9000/emails/user@example.com?template=2fa_code
    ```

    Args:
        recipient_email: Email address to filter by
        template: Optional template name filter

    Returns:
        EmailListResponse with filtered emails
    """
    filtered = [
        email for email in _sent_emails
        if email["to"] == recipient_email
    ]

    if template:
        filtered = [email for email in filtered if email["template"] == template]

    return EmailListResponse(
        total=len(filtered),
        emails=[StoredEmail(**email) for email in filtered]
    )


@app.post("/clear", status_code=status.HTTP_200_OK)
async def clear_emails() -> Dict[str, Any]:
    """
    Clear all stored emails (test isolation).

    Use this between tests to ensure clean state.

    **Example:**
    ```bash
    curl -X POST http://localhost:9000/clear
    ```

    Returns:
        Confirmation message with count of cleared emails
    """
    global _sent_emails, _email_counter

    cleared_count = len(_sent_emails)
    _sent_emails.clear()
    _email_counter = 0

    return {
        "status": "cleared",
        "emails_cleared": cleared_count,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns service status and statistics.

    **Example:**
    ```bash
    curl http://localhost:9000/health
    ```

    Returns:
        Health status with email statistics
    """
    return create_health_response(
        service_name="Email Service Mock",
        additional_info={
            "emails_sent": len(_sent_emails),
            "email_counter": _email_counter
        }
    )


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with service information."""
    return {
        "service": "Email Service Mock",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Email Service Mock Server")
    print("=" * 60)
    print("Starting on http://0.0.0.0:9000")
    print("API Documentation: http://0.0.0.0:9000/docs")
    print("=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000,
        log_level="info"
    )
