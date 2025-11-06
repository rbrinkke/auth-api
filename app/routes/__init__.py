# app/routes/__init__.py
"""Unified authentication routes."""
from fastapi import APIRouter

from app.routes.register import router as register_router
from app.routes.verify import router as verify_router
from app.routes.login import router as login_router
from app.routes.refresh import router as refresh_router
from app.routes.logout import router as logout_router
from app.routes.password_reset import router as password_reset_router
from app.routes.twofa import router as twofa_router

# Create main auth router
auth_router = APIRouter()

# Include all sub-routers
auth_router.include_router(register_router)
auth_router.include_router(verify_router)
auth_router.include_router(login_router)
auth_router.include_router(refresh_router)
auth_router.include_router(logout_router)
auth_router.include_router(password_reset_router)
auth_router.include_router(twofa_router)

__all__ = ["auth_router"]
