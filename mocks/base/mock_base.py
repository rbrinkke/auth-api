"""
Base utilities for creating standardized mock FastAPI applications.

Provides factory functions and common patterns for all mock servers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Dict, Any


def create_mock_app(
    title: str,
    description: str,
    version: str = "1.0.0",
    enable_cors: bool = True
) -> FastAPI:
    """
    Factory for creating standardized mock FastAPI applications.

    Args:
        title: Application title for OpenAPI docs
        description: Application description
        version: API version
        enable_cors: Whether to enable CORS middleware

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    if enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    return app


def create_health_response(service_name: str, additional_info: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create standardized health check response.

    Args:
        service_name: Name of the service
        additional_info: Optional additional health information

    Returns:
        Health check response dictionary
    """
    response = {
        "status": "healthy",
        "service": service_name,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    if additional_info:
        response.update(additional_info)

    return response
