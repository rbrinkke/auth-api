from fastapi import APIRouter

from app.routes.register import router as register_router
from app.routes.verify import router as verify_router
from app.routes.login import router as login_router
from app.routes.refresh import router as refresh_router
from app.routes.logout import router as logout_router
from app.routes.password_reset import router as password_reset_router
from app.routes.twofa import router as twofa_router

# Sprint 2: RBAC routes
from app.routes import groups
from app.routes import permissions
from app.routes import authorization

# OAuth 2.0 routes
from app.routes import oauth_authorize
from app.routes import oauth_token
from app.routes import oauth_revoke
from app.routes import oauth_discovery

auth_router = APIRouter()

auth_router.include_router(register_router)
auth_router.include_router(verify_router)
auth_router.include_router(login_router)
auth_router.include_router(refresh_router)
auth_router.include_router(logout_router)
auth_router.include_router(password_reset_router)
auth_router.include_router(twofa_router)

__all__ = [
    "auth_router",
    "groups",
    "permissions",
    "authorization",
    # OAuth 2.0
    "oauth_authorize",
    "oauth_token",
    "oauth_revoke",
    "oauth_discovery"
]
