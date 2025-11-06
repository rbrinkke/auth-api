"""Centralized exception handling for the application."""
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.services.registration_service import UserAlreadyExistsError
from app.services.password_validation_service import PasswordValidationError
from app.services.password_reset_service import PasswordResetServiceError
from app.services.two_factor_service import TwoFactorError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app."""

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Rate limit exceeded. Please try again later.",
                "retry_after": getattr(exc, 'retry_after', None)
            }
        )

    @app.exception_handler(UserAlreadyExistsError)
    async def user_exists_handler(request: Request, exc: UserAlreadyExistsError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc) or "Email already registered"}
        )

    @app.exception_handler(PasswordValidationError)
    async def password_validation_handler(request: Request, exc: PasswordValidationError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)}
        )

    @app.exception_handler(PasswordResetServiceError)
    async def password_reset_handler(request: Request, exc: PasswordResetServiceError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)}
        )

    @app.exception_handler(TwoFactorError)
    async def two_factor_handler(request: Request, exc: TwoFactorError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)}
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle unexpected errors without leaking sensitive information."""
        logger.error(
            "Unhandled exception",
            exc_info=exc,
            extra={
                "error_type": type(exc).__name__,
                "request_url": str(request.url),
                "request_method": request.method,
            }
        )

        error_message = (
            "An unexpected error occurred."
            if not settings.debug
            else f"Internal error: {str(exc)}"
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": error_message}
        )
