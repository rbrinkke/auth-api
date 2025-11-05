"""
Main FastAPI application.

Initializes the Auth API with all routes, middleware, and lifecycle hooks.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler, Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import settings
from app.core.redis_client import redis_client
from app.db.connection import db
from app.routes import (
    login,
    logout,
    password_reset,
    refresh,
    register,
    verify
)

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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
    - Rate limiting on sensitive endpoints
    
    **Security:**
    - Argon2id password hashing
    - Redis-backed token blacklist
    - Email verification required before login
    - All tokens stored in Redis with TTL
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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred"}
    )


# ========== Routes ==========

# Include all route modules
app.include_router(register.router)
app.include_router(verify.router)
app.include_router(login.router)
app.include_router(refresh.router)
app.include_router(logout.router)
app.include_router(password_reset.router)


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
        # Check database connection
        async with db.pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"
    
    try:
        # Check Redis connection
        await redis_client.client.ping()
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
        log_level="debug" if settings.debug else "info"
    )
