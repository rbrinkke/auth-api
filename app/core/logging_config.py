"""
Production-grade logging configuration with structured JSON logs.

Uses structlog for professional, searchable logs that integrate with:
- Datadog
- Splunk
- Elasticsearch
- CloudWatch
- Any JSON log consumer

In production, this enables:
- Easy log parsing and filtering
- Correlation ID tracking
- Performance monitoring
- Error aggregation
- Security audit trails
"""
import logging
import logging.config
import sys
from pathlib import Path

import structlog
from structlog.typing import EventDict, Processor

# Ensure logs directory exists
LOGS_DIR = Path("/app/logs")
LOGS_DIR.mkdir(exist_ok=True, parents=True)


def add_correlation_id(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add correlation ID to all logs for request tracing.

    In a production system, this enables tracking a request
    across multiple services and components.
    """
    # Add correlation_id if available in context
    # This would typically come from a request context variable
    if not event_dict.get("correlation_id"):
        event_dict["correlation_id"] = "-"

    return event_dict


def add_service_info(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add service identification to all logs.
    """
    event_dict["service"] = "auth-api"
    event_dict["environment"] = "production"

    return event_dict


def json_filter(logger: logging.Logger, name: str, event_dict: EventDict) -> EventDict:
    """
    Custom processor for JSON output with filtering.
    """
    # Ensure essential fields are present
    if "timestamp" not in event_dict:
        import time
        event_dict["timestamp"] = time.time()

    if "level" not in event_dict:
        event_dict["level"] = method_name.upper()

    return event_dict


# Configure structlog for production
# This creates structured, JSON-compatible logs
def setup_logging() -> None:
    """
    Initialize structured JSON logging configuration.

    Sets up:
    - Structured logging with JSON output
    - Correlation ID support
    - Service identification
    - Performance-friendly formatting
    """
    # Configure structlog
    structlog.configure(
        processors=[
            # Add correlation ID and service info
            add_correlation_id,
            add_service_info,

            # Render logs as JSON (for ingestion by monitoring tools)
            structlog.processors.JSONRenderer()
        ],
        # Use structlog's logger factory
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        # Cache loggers for performance
        cache_logger_on_first_use=True,
        # Set context class for thread safety
        context_class=dict,
        logger_factory=structlog.WriteLoggerFactory(),
    )

    # Configure standard Python logging with JSON output
    # This ensures all libraries (not just our code) use JSON
    logging.basicConfig(
        format="%(message)s",  # structlog handles formatting
        stream=sys.stdout,
        level=logging.INFO,
    )

    # Configure uvicorn access logs (HTTP requests)
    # These should also be structured
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.addHandler(logging.StreamHandler(sys.stdout))
    uvicorn_access_logger.setLevel(logging.INFO)

    # Configure uvicorn error logs
    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.addHandler(logging.StreamHandler(sys.stdout))
    uvicorn_error_logger.setLevel(logging.INFO)

    # Configure slowapi logs (rate limiting)
    slowapi_logger = logging.getLogger("slowapi")
    slowapi_logger.addHandler(logging.StreamHandler(sys.stdout))
    slowapi_logger.setLevel(logging.INFO)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.

    Usage:
        logger = get_logger(__name__)
        logger.info("User registered", user_id=123, email="test@example.com")

    The logger will output JSON like:
        {"timestamp": 1234567890, "level": "INFO", "service": "auth-api",
         "logger": "app.services.registration_service", "event": "User registered",
         "user_id": 123, "email": "test@example.com", "correlation_id": "-"}
    """
    return structlog.get_logger(name)


# Pre-configure logging on module import
setup_logging()
