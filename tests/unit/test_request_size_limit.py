"""Unit tests for request size limit middleware.

Tests Pure ASGI middleware logic with mocked ASGI events.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.middleware.request_size_limit import RequestSizeLimitMiddleware
from app.config import Settings


class TestRequestSizeLimitMiddleware:
    """Tests for RequestSizeLimitMiddleware."""

    @pytest.fixture
    def settings(self):
        """Create test settings with default size limits."""
        return Settings(
            REQUEST_SIZE_LIMIT_DEFAULT=10240,  # 10 KB
            REQUEST_SIZE_LIMIT_GLOBAL_MAX=1048576,  # 1 MB
            REQUEST_SIZE_LIMIT_REGISTER=10240,
            REQUEST_SIZE_LIMIT_LOGIN=10240,
            REQUEST_SIZE_LIMIT_PASSWORD_RESET=5120,
            REQUEST_SIZE_LIMIT_TOKEN_REFRESH=5120,
            REQUEST_SIZE_LIMIT_2FA=5120,
        )

    @pytest.fixture
    def middleware(self, settings):
        """Create middleware instance with mock app."""
        app = AsyncMock()
        return RequestSizeLimitMiddleware(app, settings)

    def test_middleware_initialized_with_correct_route_limits(self, middleware):
        """Test that route limits are correctly compiled from settings."""
        assert len(middleware.route_limits) == 7  # 7 route patterns defined
        assert middleware.settings.REQUEST_SIZE_LIMIT_DEFAULT == 10240
        assert middleware.settings.REQUEST_SIZE_LIMIT_GLOBAL_MAX == 1048576

    def test_get_size_limit_for_register_route(self, middleware):
        """Test that register route gets correct size limit."""
        limit = middleware._get_size_limit_for_path("/api/auth/register")
        assert limit == 10240

    def test_get_size_limit_for_login_route(self, middleware):
        """Test that login route gets correct size limit."""
        limit = middleware._get_size_limit_for_path("/api/auth/login")
        assert limit == 10240

    def test_get_size_limit_for_password_reset_route(self, middleware):
        """Test that password reset route gets correct size limit."""
        limit = middleware._get_size_limit_for_path("/api/auth/request-password-reset")
        assert limit == 5120

    def test_get_size_limit_for_token_refresh_route(self, middleware):
        """Test that token refresh route gets correct size limit."""
        limit = middleware._get_size_limit_for_path("/api/auth/refresh")
        assert limit == 5120

    def test_get_size_limit_for_2fa_route(self, middleware):
        """Test that 2FA routes get correct size limit."""
        limit = middleware._get_size_limit_for_path("/api/auth/2fa/setup")
        assert limit == 5120

    def test_get_size_limit_for_2fa_verify_route(self, middleware):
        """Test that 2FA verify route gets correct size limit."""
        limit = middleware._get_size_limit_for_path("/api/auth/2fa/verify")
        assert limit == 5120

    def test_get_size_limit_for_unknown_route_uses_default(self, middleware):
        """Test that unknown routes get default size limit."""
        limit = middleware._get_size_limit_for_path("/api/unknown")
        assert limit == 10240  # DEFAULT

    def test_get_size_limit_respects_global_maximum(self, middleware):
        """Test that size limits never exceed global maximum."""
        # Manually set a route limit higher than global max
        middleware.settings.REQUEST_SIZE_LIMIT_GLOBAL_MAX = 5120

        limit = middleware._get_size_limit_for_path("/api/auth/login")

        # Should be capped by global max
        assert limit == 5120

    @pytest.mark.asyncio
    async def test_non_http_scope_passes_through(self, middleware):
        """Test that non-HTTP scopes pass through without checking."""
        # Create WebSocket scope
        scope = {"type": "websocket", "path": "/ws"}
        receive = AsyncMock()
        send = AsyncMock()

        await middleware(scope, receive, send)

        # App should be called with original receive/send
        middleware.app.assert_called_once()

    @pytest.mark.asyncio
    async def test_small_request_passes_through(self, middleware, settings):
        """Test that requests under size limit pass through."""
        scope = {"type": "http", "path": "/api/auth/register", "method": "POST"}

        # Small body (100 bytes)
        small_body = b"a" * 100
        messages = [
            {"type": "http.request", "body": small_body, "more_body": False},
        ]

        message_index = [0]

        async def receive():
            if message_index[0] < len(messages):
                msg = messages[message_index[0]]
                message_index[0] += 1
                return msg
            return {"type": "http.disconnect"}

        send = AsyncMock()

        # Mock the app to simulate normal processing
        async def mock_app(scope, receive_inner, send_inner):
            # Call receive to get message
            message = await receive_inner()
            # Forward message through
            pass

        middleware.app = mock_app

        # Should not raise or send error response
        await middleware(scope, receive, send)

    @pytest.mark.asyncio
    async def test_request_exceeding_limit_returns_413(self, middleware, settings):
        """Test that requests exceeding size limit return HTTP 413."""
        scope = {"type": "http", "path": "/api/auth/register", "method": "POST"}

        # Large body exceeding 10 KB limit
        large_body = b"a" * 15000  # 15 KB
        messages = [
            {"type": "http.request", "body": large_body, "more_body": False},
        ]

        message_index = [0]

        async def receive():
            if message_index[0] < len(messages):
                msg = messages[message_index[0]]
                message_index[0] += 1
                return msg
            return {"type": "http.disconnect"}

        sent_messages = []

        async def send(message):
            sent_messages.append(message)

        # Mock the app - should not be called
        middleware.app = AsyncMock()

        await middleware(scope, receive, send)

        # Check that 413 response was sent
        assert len(sent_messages) >= 1
        assert sent_messages[0]["type"] == "http.response.start"
        assert sent_messages[0]["status"] == 413

    @pytest.mark.asyncio
    async def test_chunked_request_exceeding_limit_returns_413(self, middleware):
        """Test that chunked requests exceeding limit are rejected."""
        scope = {"type": "http", "path": "/api/auth/login", "method": "POST"}

        # Simulate chunked request where total exceeds 10 KB
        messages = [
            {"type": "http.request", "body": b"a" * 5000, "more_body": True},
            {"type": "http.request", "body": b"b" * 5000, "more_body": True},
            {"type": "http.request", "body": b"c" * 2000, "more_body": False},  # 12 KB total
        ]

        message_index = [0]

        async def receive():
            if message_index[0] < len(messages):
                msg = messages[message_index[0]]
                message_index[0] += 1
                return msg
            return {"type": "http.disconnect"}

        sent_messages = []

        async def send(message):
            sent_messages.append(message)

        middleware.app = AsyncMock()

        await middleware(scope, receive, send)

        # Should receive 413 response
        assert len(sent_messages) >= 1
        assert sent_messages[0]["status"] == 413

    def test_global_max_caps_all_route_limits(self, settings):
        """Test that global maximum caps all route-specific limits."""
        # Create middleware with very small global max
        settings.REQUEST_SIZE_LIMIT_GLOBAL_MAX = 1024  # 1 KB
        settings.REQUEST_SIZE_LIMIT_REGISTER = 10240  # 10 KB - should be capped

        app = AsyncMock()
        middleware = RequestSizeLimitMiddleware(app, settings)

        limit = middleware._get_size_limit_for_path("/api/auth/register")

        # Should be capped by global max
        assert limit == 1024

    @pytest.mark.parametrize(
        "path,expected_limit",
        [
            ("/api/auth/register", 10240),
            ("/api/auth/login", 10240),
            ("/api/auth/request-password-reset", 5120),
            ("/api/auth/reset-password", 5120),
            ("/api/auth/refresh", 5120),
            ("/api/auth/logout", 5120),
            ("/api/auth/2fa/setup", 5120),
            ("/api/auth/2fa/verify", 5120),
            ("/unknown/path", 10240),  # default
        ],
    )
    def test_multiple_route_limits(self, middleware, path, expected_limit):
        """Test correct limits for all routes."""
        limit = middleware._get_size_limit_for_path(path)
        assert limit == expected_limit

    def test_middleware_route_patterns_are_compiled(self, middleware):
        """Test that route patterns are compiled as regex."""
        import re

        for pattern in middleware.route_limits.keys():
            assert isinstance(pattern, type(re.compile("")))

    @pytest.mark.asyncio
    async def test_request_with_no_body_passes(self, middleware):
        """Test that GET requests with no body pass through."""
        scope = {"type": "http", "path": "/api/health", "method": "GET"}

        messages = [
            {"type": "http.request", "body": b"", "more_body": False},
        ]

        message_index = [0]

        async def receive():
            if message_index[0] < len(messages):
                msg = messages[message_index[0]]
                message_index[0] += 1
                return msg
            return {"type": "http.disconnect"}

        send = AsyncMock()

        async def mock_app(scope, receive_inner, send_inner):
            pass

        middleware.app = mock_app

        await middleware(scope, receive, send)

        # Should not return 413
        for call in send.call_args_list:
            if call[0][0]["type"] == "http.response.start":
                assert call[0][0]["status"] != 413
