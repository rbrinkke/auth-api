"""
Main FastAPI application.

Initializes the Auth API with all routes, middleware, and lifecycle hooks.

Production-ready with:
- Structured JSON logging
- Security headers
- Hardened exception handling
- API documentation protection
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response
from slowapi import _rate_limit_exceeded_handler, Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import settings
from app.core.logging_config import get_logger
from app.core.redis_client import redis_client
from app.db.connection import db
from app.routes import (
    login,
    logout,
    password_reset,
    refresh,
    register,
    verify,
    twofa as twofa_router
)
from app.services.password_validation_service import PasswordValidationError
from app.services.registration_service import (
    RegistrationServiceError,
    UserAlreadyExistsError
)
from app.services.password_reset_service import PasswordResetServiceError
from app.services.two_factor_service import TwoFactorError

# Initialize structured logging
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events:
    - Startup: Initialize database pool and Redis connection
    - Shutdown: Close all connections gracefully
    """
    # Startup
    logger.info("Starting Auth API...")
    
    try:
        # Connect to PostgreSQL
        logger.info("Connecting to PostgreSQL...")
        await db.connect()
        logger.info("PostgreSQL connection established")
        
        # Connect to Redis
        logger.info("Connecting to Redis...")
        await redis_client.connect()
        logger.info("Redis connection established")
        
        logger.info("Auth API started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start Auth API: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Auth API...")
    
    try:
        # Close database connections
        logger.info("Closing database connections...")
        await db.disconnect()
        
        # Close Redis connection
        logger.info("Closing Redis connection...")
        await redis_client.disconnect()
        
        logger.info("Auth API shut down successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


# Create FastAPI app
app = FastAPI(
    title="Auth API",
    description="""
    Authentication API for the Activity App.
    
    **Features:**
    - User registration with hard email verification
    - JWT-based authentication (access + refresh tokens)
    - Refresh token rotation (mandatory security feature)
    - Password reset with time-limited tokens
    - Two-Factor Authentication (2FA/TOTP) with email codes
    - Rate limiting on sensitive endpoints
    
    **Security:**
    - Argon2id password hashing
    - Redis-backed token blacklist
    - Email verification required before login
    - All tokens stored in Redis with TTL
    - 2FA/TOTP with encrypted secrets and backup codes
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# ========== SlowAPI Limiter ==========
# Create limiter instance for rate limiting
limiter = Limiter(key_func=get_remote_address)
# Attach limiter to app state for SlowAPI middleware
app.state.limiter = limiter

# ========== Middleware ==========

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Enable XSS protection
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # Referrer policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Content Security Policy (basic)
    response.headers["Content-Security-Policy"] = "default-src 'self'"

    # HSTS (only on HTTPS - only add if not in debug and using HTTPS)
    if not settings.debug:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Hide server details
    response.headers["Server"] = ""  # Remove server header

    return response


# Trusted host middleware (prevent host header attacks)
# In production, replace with your actual domain(s)
trusted_hosts = ["localhost", "127.0.0.1"]
if not settings.debug:
    trusted_hosts.append(settings.frontend_url.replace("https://", "").replace("http://", ""))

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=trusted_hosts
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.add_middleware(SlowAPIMiddleware)

# ========== Exception Handlers ==========

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "retry_after": exc.retry_after if hasattr(exc, 'retry_after') else None
        }
    )


@app.exception_handler(UserAlreadyExistsError)
async def user_already_exists_handler(request: Request, exc: UserAlreadyExistsError):
    """Handle user already exists error."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc) or "Email already registered"}
    )


@app.exception_handler(PasswordValidationError)
async def password_validation_handler(request: Request, exc: PasswordValidationError):
    """Handle password validation error."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.exception_handler(RegistrationServiceError)
async def registration_error_handler(request: Request, exc: RegistrationServiceError):
    """Handle general registration service error."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.exception_handler(PasswordResetServiceError)
async def password_reset_error_handler(request: Request, exc: PasswordResetServiceError):
    """Handle password reset service error."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.exception_handler(TwoFactorError)
async def two_factor_error_handler(request: Request, exc: TwoFactorError):
    """Handle two-factor authentication error."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected errors without leaking sensitive information.

    SECURITY BEST PRACTICE:
    - In production: Never expose exception details to clients
    - Log full error with stack trace for debugging
    - Return generic message to client
    """
    # Log full error for debugging (internal only)
    logger.error(
        "Unhandled exception occurred",
        exc_info=exc,
        error_type=type(exc).__name__,
        request_url=str(request.url),
        request_method=request.method,
        client_ip=get_remote_address(request)
    )

    # In production, return generic message (don't leak details)
    # In debug mode, you might want to include more details for development
    error_message = (
        "An unexpected internal error occurred."
        if not settings.debug
        else f"Internal error: {str(exc)}"
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": error_message}
    )


# ========== Routes ==========

# Include all route modules
app.include_router(register)
app.include_router(verify)
app.include_router(login)
app.include_router(refresh)
app.include_router(logout)
app.include_router(password_reset)
app.include_router(twofa_router)


# Health check endpoint
@app.get(
    "/health",
    tags=["health"],
    summary="Health check",
    description="Check if the API is running and database connections are healthy"
)
async def health_check():
    """
    Health check endpoint for monitoring.

    Returns:
        Status of the API and its dependencies
    """
    try:
        # Check database connection using ping method
        await db.ping()
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"

    try:
        # Check Redis connection using ping method
        await redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        redis_status = "unhealthy"

    overall_status = "healthy" if db_status == "healthy" and redis_status == "healthy" else "unhealthy"

    return {
        "status": overall_status,
        "service": "auth-api",
        "version": "1.0.0",
        "dependencies": {
            "database": db_status,
            "redis": redis_status
        }
    }


# Root endpoint
@app.get(
    "/",
    tags=["root"],
    summary="API information",
    description="Get basic information about the Auth API"
)
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Auth API",
        "version": "1.0.0",
        "description": "Authentication service for Activity App",
        "docs": "/docs" if settings.debug else "Documentation disabled in production"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
        # Hide server header for security
        server_header=False,
        # Additional security headers
        headers=[("X-Content-Type-Options", "nosniff")]
    )
