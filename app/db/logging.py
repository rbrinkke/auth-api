"""
Best-of-class database logging for stored procedures.

Features:
- Automatic timing and performance monitoring
- Security-first parameter sanitization
- Prometheus metrics integration
- Error categorization with appropriate log levels
- Result metadata logging
- Slow query detection
"""
import time
import inspect
from functools import wraps
from typing import Any, Callable, Dict
from uuid import UUID

import asyncpg

from app.core.logging_config import get_logger
from app.core.metrics import (
    db_query_duration_histogram,
    db_query_total_counter,
    db_slow_query_counter
)

logger = get_logger(__name__)

# Configuration
SLOW_QUERY_THRESHOLD_MS = 1000  # 1 second
VERY_SLOW_QUERY_THRESHOLD_MS = 5000  # 5 seconds

# Sensitive parameters that should NEVER be logged
SENSITIVE_PARAMS = {
    'hashed_password',
    'password',
    'token',
    'refresh_token',
    'access_token',
    'secret',
    'jti',
    'reset_token',
    'verification_token'
}


def sanitize_params(func: Callable, args: tuple, kwargs: dict) -> Dict[str, Any]:
    """
    Extract safe parameters for logging, redacting sensitive data.

    Security policy:
    - Passwords/tokens/secrets are ALWAYS redacted
    - Connection objects are skipped
    - Safe types (UUID, email, bool, int) are logged
    - Large objects are summarized

    Args:
        func: The function being called
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Dictionary of safe parameters for logging
    """
    sig = inspect.signature(func)
    params = {}

    # Map positional args to parameter names
    param_names = list(sig.parameters.keys())
    for i, value in enumerate(args):
        if i >= len(param_names):
            break

        param_name = param_names[i]

        # Skip connection objects
        if param_name == 'conn' or isinstance(value, asyncpg.Connection):
            continue

        # Redact sensitive parameters
        if param_name in SENSITIVE_PARAMS:
            params[param_name] = "<redacted>"
            continue

        # Log safe types
        if isinstance(value, (str, int, bool, float)):
            # Truncate very long strings
            if isinstance(value, str) and len(value) > 100:
                params[param_name] = f"{value[:100]}...(truncated)"
            else:
                params[param_name] = value
        elif isinstance(value, UUID):
            params[param_name] = str(value)
        else:
            # For complex objects, just log the type
            params[param_name] = f"<{type(value).__name__}>"

    # Handle keyword arguments
    for key, value in kwargs.items():
        if key in SENSITIVE_PARAMS:
            params[key] = "<redacted>"
        elif isinstance(value, (str, int, bool, float, UUID)):
            params[key] = str(value) if isinstance(value, UUID) else value
        else:
            params[key] = f"<{type(value).__name__}>"

    return params


def get_result_metadata(result: Any, sp_name: str) -> Dict[str, Any]:
    """
    Extract safe result metadata without exposing sensitive data.

    Args:
        result: The result from the stored procedure
        sp_name: Name of the stored procedure

    Returns:
        Dictionary of result metadata
    """
    from app.db.procedures import UserRecord

    metadata = {}

    if result is None:
        metadata["result_type"] = "None"
        metadata["found"] = False
    elif isinstance(result, bool):
        metadata["result_type"] = "boolean"
        metadata["success"] = result
    elif isinstance(result, UserRecord):
        metadata["result_type"] = "UserRecord"
        metadata["user_id"] = str(result.id)
        metadata["email"] = result.email
        metadata["found"] = True
    elif isinstance(result, (list, tuple)):
        metadata["result_type"] = "list"
        metadata["row_count"] = len(result)
    elif isinstance(result, dict):
        metadata["result_type"] = "dict"
        metadata["keys"] = list(result.keys())
    else:
        metadata["result_type"] = type(result).__name__

    return metadata


def categorize_db_error(e: Exception) -> tuple[str, str]:
    """
    Categorize database errors for appropriate logging level.

    Returns:
        Tuple of (log_level, error_category)
    """
    # Connection errors - CRITICAL
    if isinstance(e, asyncpg.PostgresConnectionError):
        return "error", "connection_failure"

    # Constraint violations - Business logic (WARNING)
    elif isinstance(e, asyncpg.UniqueViolationError):
        return "warning", "duplicate_entry"
    elif isinstance(e, asyncpg.ForeignKeyViolationError):
        return "error", "foreign_key_violation"
    elif isinstance(e, asyncpg.NotNullViolationError):
        return "error", "null_constraint_violation"

    # Query issues
    elif isinstance(e, asyncpg.QueryCanceledError):
        return "warning", "query_timeout"
    elif isinstance(e, asyncpg.PostgresError):
        return "error", "postgres_error"

    # Unknown errors
    else:
        return "error", "unknown_error"


def log_stored_procedure(func: Callable) -> Callable:
    """
    Decorator for stored procedure wrappers with comprehensive logging.

    Features:
    - Automatic entry/exit logging
    - Execution timing with slow query detection
    - Security-first parameter sanitization
    - Result metadata logging
    - Error categorization
    - Prometheus metrics integration

    Usage:
        @log_stored_procedure
        async def sp_create_user(conn, email, hashed_password):
            result = await conn.fetchrow(...)
            return UserRecord(result)
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        sp_name = func.__name__
        safe_params = sanitize_params(func, args, kwargs)

        # Entry logging
        logger.debug(f"{sp_name}_start", operation=sp_name, **safe_params)

        start_time = time.time()
        status = "success"
        result = None

        try:
            # Execute stored procedure
            result = await func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000

            # Get result metadata
            result_meta = get_result_metadata(result, sp_name)

            # Determine log level based on performance
            # Merge params and metadata to avoid duplicate keys
            log_context = {**safe_params, **result_meta}

            if duration_ms > VERY_SLOW_QUERY_THRESHOLD_MS:
                log_level = "error"
                logger.error(
                    f"{sp_name}_very_slow_query",
                    operation=sp_name,
                    duration_ms=int(duration_ms),
                    threshold_ms=VERY_SLOW_QUERY_THRESHOLD_MS,
                    **log_context
                )
                # Track slow query metric
                db_slow_query_counter.labels(operation=sp_name, severity="very_slow").inc()
            elif duration_ms > SLOW_QUERY_THRESHOLD_MS:
                log_level = "warning"
                logger.warning(
                    f"{sp_name}_slow_query",
                    operation=sp_name,
                    duration_ms=int(duration_ms),
                    threshold_ms=SLOW_QUERY_THRESHOLD_MS,
                    **log_context
                )
                # Track slow query metric
                db_slow_query_counter.labels(operation=sp_name, severity="slow").inc()
            else:
                log_level = "info"

            # Completion logging (log_context already set above)
            logger.info(
                f"{sp_name}_complete",
                operation=sp_name,
                duration_ms=int(duration_ms),
                **log_context
            )

            # Track success metrics
            db_query_duration_histogram.labels(
                operation=sp_name,
                status="success"
            ).observe(duration_ms / 1000)  # Convert to seconds for Prometheus

            db_query_total_counter.labels(
                operation=sp_name,
                status="success"
            ).inc()

            return result

        except Exception as e:
            status = "error"
            duration_ms = (time.time() - start_time) * 1000

            # Categorize error for appropriate logging
            log_level, error_category = categorize_db_error(e)

            # Error logging
            getattr(logger, log_level)(
                f"{sp_name}_failed",
                operation=sp_name,
                duration_ms=int(duration_ms),
                error_category=error_category,
                error_type=type(e).__name__,
                error=str(e),
                exc_info=True,
                **safe_params
            )

            # Track error metrics
            db_query_duration_histogram.labels(
                operation=sp_name,
                status="error"
            ).observe(duration_ms / 1000)

            db_query_total_counter.labels(
                operation=sp_name,
                status="error"
            ).inc()

            # Re-raise exception
            raise

    return wrapper
