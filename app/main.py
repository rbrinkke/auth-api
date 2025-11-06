"""
Auth API - Main Application

A minimalistic authentication service focused on:
- User registration with email verification
- JWT-based authentication
- Token refresh with rotation
- Password reset functionality
- Two-factor authentication
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import settings
from app.core.logging_config import get_logger
from app.core.redis_client import redis_client
from app.db.connection import db
from app.middleware.security import add_security_headers
from app.routes import auth_router
from app.exceptions import register_exception_handlers

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    logger.info("Starting Auth API...")
    
    try:
        await db.connect()
        logger.info("Database connected")
        
        await redis_client.connect()
        logger.info("Redis connected")
        
        logger.info("Auth API started successfully")
        yield
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise
    finally:
        logger.info("Shutting down...")
        await db.disconnect()
        await redis_client.disconnect()
        logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Auth API",
        description="Minimalistic authentication service for Activity App",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # Configure rate limiting
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    
    # Add security headers
    app.middleware("http")(add_security_headers)
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Include routes
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    
    # Health check
    @app.get("/health")
    async def health_check():
        """Service health check."""
        try:
            await db.ping()
            await redis_client.ping()
            
            return {
                "status": "healthy",
                "service": "auth-api",
                "version": "1.0.0",
                "dependencies": {
                    "database": "healthy",
                    "redis": "healthy"
                }
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "unhealthy",
                    "error": "Service dependencies unavailable"
                }
            )
    
    return app


app = create_app()
