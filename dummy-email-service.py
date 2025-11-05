#!/usr/bin/env python3
"""
Dummy Email Service for Development
Mimics the expected email service API that the Auth API expects.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Dummy Email Service", version="1.0.0")

class EmailRequest(BaseModel):
    to: str
    template: str
    subject: str
    data: dict

@app.post("/send")
async def send_email(request: EmailRequest):
    """Mock email sending - just logs to console."""
    print(f"\n{'='*60}")
    print(f"EMAIL SERVICE - Mock send")
    print(f"{'='*60}")
    print(f"To: {request.to}")
    print(f"Template: {request.template}")
    print(f"Subject: {request.subject}")
    print(f"Data: {request.data}")
    print(f"{'='*60}\n")

    # Simulate sending delay
    await asyncio.sleep(0.1)

    return {"status": "sent", "message_id": "mock-12345"}

@app.get("/")
async def root():
    return {"service": "Dummy Email Service", "status": "running"}

if __name__ == "__main__":
    import asyncio
    uvicorn.run(app, host="0.0.0.0", port=9000)
