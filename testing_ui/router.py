"""
FastAPI router for serving the authentication testing UI.

This router serves a standalone HTML page for testing all authentication flows:
- Registration with email code
- Login with code and organization selection
- Password reset with email code
- Token management (refresh, logout)
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

# Setup templates directory
TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(
    prefix="/test",
    tags=["testing-ui"],
    include_in_schema=True,
)


@router.get("/auth", response_class=HTMLResponse, summary="Authentication Testing Page")
async def auth_testing_page(request: Request):
    """
    Serves the authentication testing interface.

    This page allows testing all authentication flows:
    - Registration (with email verification code)
    - Login (with login code and optional org selection)
    - Password reset (with reset code)
    - Token refresh and logout
    """
    return templates.TemplateResponse(
        "auth_test.html",
        {
            "request": request,
            "title": "Auth API Testing Interface",
        }
    )
