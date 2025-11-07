"""Request size limit middleware for DoS protection.

Pure ASGI middleware that enforces request body size limits per route.
Prevents memory exhaustion attacks via oversized payloads.
"""

import logging
import re
from typing import Callable, Dict, Pattern
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from app.config import Settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RequestSizeLimitMiddleware:
    """
    Pure ASGI middleware to enforce request body size limits.

    Features:
    - Route-specific size limits via pattern matching
    - Memory-safe streaming consumption
    - Early rejection with HTTP 413 response
    - Configurable limits via environment variables
    - Pass-through for non-HTTP scopes (WebSocket, lifespan)

    Security:
    - Prevents DoS attacks via memory exhaustion
    - Rejects oversized requests immediately
    - No buffering of request bodies
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        """Initialize middleware with size limits.

        Args:
            app: ASGI application
            settings: Application settings with size limit configuration
        """
        self.app = app
        self.settings = settings

        # Compile route patterns and their size limits
        self.route_limits: Dict[Pattern, int] = {
            re.compile(r"^/api/auth/register$"): settings.REQUEST_SIZE_LIMIT_REGISTER,
            re.compile(r"^/api/auth/login$"): settings.REQUEST_SIZE_LIMIT_LOGIN,
            re.compile(r"^/api/auth/request-password-reset$"): (
                settings.REQUEST_SIZE_LIMIT_PASSWORD_RESET
            ),
            re.compile(r"^/api/auth/reset-password$"): (
                settings.REQUEST_SIZE_LIMIT_PASSWORD_RESET
            ),
            re.compile(r"^/api/auth/refresh$"): settings.REQUEST_SIZE_LIMIT_TOKEN_REFRESH,
            re.compile(r"^/api/auth/logout$"): settings.REQUEST_SIZE_LIMIT_TOKEN_REFRESH,
            re.compile(r"^/api/auth/2fa/.*"): settings.REQUEST_SIZE_LIMIT_2FA,
        }

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI middleware entry point.

        Args:
            scope: ASGI scope dict
            receive: ASGI receive callable
            send: ASGI send callable
        """
        # Only check HTTP requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Get size limit for this route
        path = scope.get("path", "")
        size_limit = self._get_size_limit_for_path(path)
        logger.debug("size_limit_middleware_checking_request", path=path, size_limit=size_limit)

        # Track body size during streaming
        body_size = 0

        async def receive_with_size_check() -> Message:
            """Wrapper around receive that checks body size.

            Returns:
                Message from ASGI receive, or triggers 413 response if limit exceeded

            Raises:
                Closes connection if request body exceeds limit
            """
            nonlocal body_size

            message = await receive()

            # Check size for HTTP request messages with body
            if message["type"] == "http.request":
                body_chunk = message.get("body", b"")
                body_size += len(body_chunk)

                # Check if we've exceeded the limit
                if body_size > size_limit:
                    logger.debug("size_limit_middleware_limit_exceeded", path=path, body_size=body_size, limit=size_limit)
                    logger.warning(
                        "request_body_too_large",
                        path=path,
                        body_size=body_size,
                        limit=size_limit,
                    )

                    # Send HTTP 413 Payload Too Large response
                    await send(
                        {
                            "type": "http.response.start",
                            "status": 413,
                            "headers": [
                                [b"content-type", b"application/json"],
                                [
                                    b"content-length",
                                    str(len(b'{"detail":"Request body too large"}')).encode(),
                                ],
                            ],
                        }
                    )

                    await send(
                        {
                            "type": "http.response.body",
                            "body": b'{"detail":"Request body too large"}',
                        }
                    )

                    # Return empty message to signal end of processing
                    return {"type": "http.disconnect"}

            return message

        # Process request with size checking
        await self.app(scope, receive_with_size_check, send)

    def _get_size_limit_for_path(self, path: str) -> int:
        """Determine size limit for the given request path.

        Args:
            path: Request path from ASGI scope

        Returns:
            Size limit in bytes for this path, or default if no match

        Note:
            Routes are matched in order of specificity.
            All limits are capped by GLOBAL_MAX for safety.
        """
        # Check route-specific patterns
        for pattern, limit in self.route_limits.items():
            if pattern.match(path):
                # Cap by global maximum
                return min(limit, self.settings.REQUEST_SIZE_LIMIT_GLOBAL_MAX)

        # Default limit for unmatched routes
        return min(
            self.settings.REQUEST_SIZE_LIMIT_DEFAULT,
            self.settings.REQUEST_SIZE_LIMIT_GLOBAL_MAX,
        )
