"""
Request Intent Extraction Middleware - Intention Model Foundation
==================================================================

This middleware extracts operational intent from requests, enabling the system
to understand WHY something is happening, not just WHAT is happening.

Intent Dimensions:
- Operation Intent: WHY is this operation being performed?
- Session Mode: HOW is this request being made?
- Request Purpose: WHAT business goal does this serve?
- Context Flags: Test mode, batch operations, criticality

Headers:
- X-Operation-Intent: manual|automation|test|migration|incident_response|scheduled
- X-Session-Mode: interactive|api|batch|scheduled|system
- X-Request-Purpose: Free-form description of business goal
- X-Batch-ID: Correlation ID for batch operations
- X-Is-Test: true|false (marks test vs production traffic)
- X-Criticality: critical|standard|low (operation priority)
- X-Client-Type: web|mobile|api|cli (client identification)

Usage:
    The extracted intent is stored in context vars and can be accessed by:
    - Authorization service (for intent-aware decisions)
    - Audit service (for operational context logging)
    - Metrics service (for intent-bucketed metrics)
    - Any service needing operational context

Example:
    from app.middleware.intent import get_request_intent

    # In a service/route:
    intent = get_request_intent()
    logger.info("processing_request",
                operation_intent=intent.operation_intent,
                session_mode=intent.session_mode)
"""

from contextvars import ContextVar
from dataclasses import dataclass, asdict
from typing import Optional
from fastapi import Request

from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class RequestIntent:
    """
    Structured representation of request operational intent.

    This captures WHY a request is being made from multiple dimensions:
    - Operation level (manual, automation, test, etc.)
    - Session level (interactive, batch, scheduled, etc.)
    - Business purpose (free-form description)
    - Operational flags (test mode, criticality, etc.)
    """

    # Core intent dimensions
    operation_intent: str = "standard"  # Why this operation? (manual, automation, test, migration, incident, scheduled)
    session_mode: str = "interactive"   # How made? (interactive, api, batch, scheduled, system)
    request_purpose: Optional[str] = None  # Business goal (free-form)

    # Operational context
    batch_id: Optional[str] = None      # Batch operation correlation
    is_test: bool = False                # Test vs production traffic
    criticality: str = "standard"        # critical, standard, low
    client_type: Optional[str] = None    # web, mobile, api, cli

    # Request metadata
    client_version: Optional[str] = None  # Client version (from User-Agent)
    idempotency_key: Optional[str] = None  # Idempotency tracking

    def to_dict(self) -> dict:
        """Convert to dictionary for logging/storage."""
        return asdict(self)

    def is_automated(self) -> bool:
        """Check if request is automated (not human-initiated)."""
        return self.operation_intent in ["automation", "scheduled", "system"] or \
               self.session_mode in ["batch", "scheduled", "system"]

    def is_production(self) -> bool:
        """Check if request is production traffic (not test)."""
        return not self.is_test and self.operation_intent != "test"

    def is_high_priority(self) -> bool:
        """Check if request is high priority."""
        return self.criticality == "critical"


# Context variable for storing request intent
request_intent_var: ContextVar[RequestIntent] = ContextVar("request_intent", default=None)


async def intent_extraction_middleware(request: Request, call_next):
    """
    Extract operational intent from request headers and store in context.

    This middleware runs early in the request lifecycle and makes intent
    available to all downstream services via context vars.

    Intent Extraction:
    1. Read intent headers (X-Operation-Intent, etc.)
    2. Apply defaults for missing headers
    3. Validate and normalize values
    4. Store in context var
    5. Log intent (if DEBUG or non-standard intent)
    6. Continue request processing

    Args:
        request: FastAPI Request object
        call_next: Next middleware/handler in chain

    Returns:
        Response from downstream handlers
    """

    # Extract intent from headers (with defaults)
    operation_intent = request.headers.get("X-Operation-Intent", "standard").lower()
    session_mode = request.headers.get("X-Session-Mode", "interactive").lower()
    request_purpose = request.headers.get("X-Request-Purpose")
    batch_id = request.headers.get("X-Batch-ID")
    is_test = request.headers.get("X-Is-Test", "false").lower() == "true"
    criticality = request.headers.get("X-Criticality", "standard").lower()
    client_type = request.headers.get("X-Client-Type")
    client_version = request.headers.get("User-Agent")
    idempotency_key = request.headers.get("Idempotency-Key")

    # Validate operation_intent
    valid_operation_intents = [
        "standard", "manual", "automation", "test",
        "migration", "incident_response", "scheduled", "system"
    ]
    if operation_intent not in valid_operation_intents:
        logger.warning("invalid_operation_intent",
                      operation_intent=operation_intent,
                      valid_values=valid_operation_intents,
                      path=request.url.path)
        operation_intent = "standard"  # Fallback to default

    # Validate session_mode
    valid_session_modes = ["interactive", "api", "batch", "scheduled", "system"]
    if session_mode not in valid_session_modes:
        logger.warning("invalid_session_mode",
                      session_mode=session_mode,
                      valid_values=valid_session_modes,
                      path=request.url.path)
        session_mode = "interactive"  # Fallback

    # Validate criticality
    valid_criticalities = ["critical", "standard", "low"]
    if criticality not in valid_criticalities:
        criticality = "standard"

    # Create intent object
    intent = RequestIntent(
        operation_intent=operation_intent,
        session_mode=session_mode,
        request_purpose=request_purpose,
        batch_id=batch_id,
        is_test=is_test,
        criticality=criticality,
        client_type=client_type,
        client_version=client_version,
        idempotency_key=idempotency_key
    )

    # Store in context var (available to all services)
    request_intent_var.set(intent)

    # Log intent if non-standard or in DEBUG mode
    from app.config import get_settings
    settings = get_settings()

    if settings.DEBUG or not intent.is_production() or intent.is_high_priority():
        logger.info("request_intent_extracted",
                   path=request.url.path,
                   method=request.method,
                   operation_intent=intent.operation_intent,
                   session_mode=intent.session_mode,
                   is_test=intent.is_test,
                   is_automated=intent.is_automated(),
                   criticality=intent.criticality,
                   batch_id=intent.batch_id,
                   request_purpose=intent.request_purpose)

    # Continue processing
    response = await call_next(request)

    # Add intent headers to response (for debugging)
    if settings.DEBUG:
        response.headers["X-Processed-Intent"] = intent.operation_intent
        response.headers["X-Processed-Session-Mode"] = intent.session_mode

    return response


def get_request_intent() -> RequestIntent:
    """
    Get current request intent from context.

    This can be called from any service to access operational intent.
    If no intent is set (e.g., in tests), returns default intent.

    Returns:
        RequestIntent object with operational context

    Example:
        intent = get_request_intent()
        if intent.is_test:
            # Handle test traffic differently
            logger.debug("test_request_detected")

        if intent.is_automated():
            # Automated request - apply different rate limits
            ...
    """
    intent = request_intent_var.get()

    if intent is None:
        # Return default intent (no headers provided)
        return RequestIntent()

    return intent


def get_intent_summary() -> dict:
    """
    Get summary of current request intent for logging.

    Returns:
        Dictionary with key intent fields (for structured logging)
    """
    intent = get_request_intent()

    return {
        "operation_intent": intent.operation_intent,
        "session_mode": intent.session_mode,
        "is_test": intent.is_test,
        "is_automated": intent.is_automated(),
        "is_production": intent.is_production(),
        "criticality": intent.criticality,
        "batch_id": intent.batch_id,
    }


def requires_production_intent():
    """
    Check if current request has production intent.

    Raises:
        ValueError if request is marked as test

    Usage:
        # In a route that should never process test traffic
        requires_production_intent()
        # Raises if X-Is-Test: true
    """
    intent = get_request_intent()

    if not intent.is_production():
        raise ValueError(
            f"This endpoint requires production intent. "
            f"Current intent: operation={intent.operation_intent}, is_test={intent.is_test}"
        )
