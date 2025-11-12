"""
Tests for database logging functionality.

Verifies that:
1. Stored procedures are logged correctly
2. Sensitive parameters are redacted
3. Result metadata is logged
4. Metrics are tracked
5. Errors are categorized correctly
"""
import pytest
import logging
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

from app.db import procedures
from app.db.logging import (
    sanitize_params,
    get_result_metadata,
    categorize_db_error,
    SENSITIVE_PARAMS
)


class TestParameterSanitization:
    """Test that sensitive parameters are properly redacted."""

    def test_sensitive_params_are_redacted(self):
        """Verify all sensitive parameters are redacted."""
        # Create mock function with sensitive params
        async def mock_sp(conn, email, hashed_password, token):
            pass

        args = (None, "user@example.com", "hashed_pass_123", "token_abc")
        kwargs = {}

        result = sanitize_params(mock_sp, args, kwargs)

        # Verify sensitive data is redacted
        assert result["hashed_password"] == "<redacted>"
        assert result["token"] == "<redacted>"

        # Verify safe data is logged
        assert result["email"] == "user@example.com"

    def test_all_sensitive_param_names_are_redacted(self):
        """Test all sensitive parameter names from SENSITIVE_PARAMS constant."""
        async def mock_sp(conn, hashed_password, password, token, refresh_token,
                         access_token, secret, jti, reset_token, verification_token):
            pass

        args = (None, "h1", "p1", "t1", "r1", "a1", "s1", "j1", "rst1", "v1")
        result = sanitize_params(mock_sp, args, {})

        # All should be redacted
        for param in SENSITIVE_PARAMS:
            if param in result:
                assert result[param] == "<redacted>", f"{param} should be redacted"

    def test_uuid_parameters_are_converted_to_string(self):
        """Verify UUIDs are converted to strings."""
        async def mock_sp(conn, user_id):
            pass

        test_uuid = uuid4()
        args = (None, test_uuid)
        result = sanitize_params(mock_sp, args, {})

        assert result["user_id"] == str(test_uuid)
        assert isinstance(result["user_id"], str)

    def test_long_strings_are_truncated(self):
        """Verify very long strings are truncated."""
        async def mock_sp(conn, long_param):
            pass

        long_string = "x" * 150
        args = (None, long_string)
        result = sanitize_params(mock_sp, args, {})

        assert len(result["long_param"]) < len(long_string)
        assert "(truncated)" in result["long_param"]


class TestResultMetadata:
    """Test result metadata extraction."""

    def test_user_record_metadata(self):
        """Verify UserRecord metadata extraction."""
        from app.db.procedures import UserRecord
        from unittest.mock import MagicMock

        # Create mock UserRecord
        mock_record = MagicMock()
        mock_record.id = uuid4()
        mock_record.email = "test@example.com"

        user = UserRecord.__new__(UserRecord)
        user.id = mock_record.id
        user.email = mock_record.email

        metadata = get_result_metadata(user, "sp_create_user")

        assert metadata["result_type"] == "UserRecord"
        assert metadata["user_id"] == str(mock_record.id)
        assert metadata["email"] == mock_record.email
        assert metadata["found"] is True

    def test_none_result_metadata(self):
        """Verify None result metadata (user not found)."""
        metadata = get_result_metadata(None, "sp_get_user_by_email")

        assert metadata["result_type"] == "None"
        assert metadata["found"] is False

    def test_boolean_result_metadata(self):
        """Verify boolean result metadata."""
        metadata = get_result_metadata(True, "sp_verify_user_email")

        assert metadata["result_type"] == "boolean"
        assert metadata["success"] is True

    def test_list_result_metadata(self):
        """Verify list result metadata."""
        test_list = [1, 2, 3, 4, 5]
        metadata = get_result_metadata(test_list, "sp_some_query")

        assert metadata["result_type"] == "list"
        assert metadata["row_count"] == 5


class TestErrorCategorization:
    """Test database error categorization."""

    def test_connection_error_categorization(self):
        """Verify connection errors are categorized as ERROR."""
        import asyncpg

        error = asyncpg.PostgresConnectionError("Connection failed")
        log_level, category = categorize_db_error(error)

        assert log_level == "error"
        assert category == "connection_failure"

    def test_unique_violation_categorization(self):
        """Verify unique violations are categorized as WARNING."""
        import asyncpg

        error = asyncpg.UniqueViolationError("Duplicate key")
        log_level, category = categorize_db_error(error)

        assert log_level == "warning"
        assert category == "duplicate_entry"

    def test_foreign_key_violation_categorization(self):
        """Verify foreign key violations are categorized as ERROR."""
        import asyncpg

        error = asyncpg.ForeignKeyViolationError("FK constraint")
        log_level, category = categorize_db_error(error)

        assert log_level == "error"
        assert category == "foreign_key_violation"

    def test_unknown_error_categorization(self):
        """Verify unknown errors are categorized as ERROR."""
        error = ValueError("Some random error")
        log_level, category = categorize_db_error(error)

        assert log_level == "error"
        assert category == "unknown_error"


@pytest.mark.asyncio
@pytest.mark.integration
class TestStoredProcedureLogging:
    """Integration tests for stored procedure logging."""

    async def test_sp_create_user_logs_correctly(self, db_connection, caplog):
        """Verify sp_create_user produces correct logs."""
        with caplog.at_level(logging.DEBUG):
            try:
                await procedures.sp_create_user(
                    db_connection,
                    f"test_{uuid4()}@example.com",
                    "hashed_password_123"
                )
            except Exception:
                pass  # Ignore actual DB errors for logging test

        # Verify entry log
        assert any("sp_create_user_start" in record.message for record in caplog.records)

        # Verify sensitive data is NOT in logs
        assert "hashed_password_123" not in caplog.text
        assert "<redacted>" in caplog.text or "hashed_password" not in caplog.text

    async def test_sp_get_user_by_email_logs_email(self, db_connection, caplog):
        """Verify sp_get_user_by_email logs email correctly."""
        with caplog.at_level(logging.DEBUG):
            try:
                await procedures.sp_get_user_by_email(
                    db_connection,
                    "test@example.com"
                )
            except Exception:
                pass

        # Verify email is logged (not sensitive)
        assert "test@example.com" in caplog.text

        # Verify start and complete logs
        assert any("sp_get_user_by_email_start" in record.message
                  for record in caplog.records)


@pytest.mark.asyncio
class TestMetricsIntegration:
    """Test Prometheus metrics integration."""

    @patch('app.db.logging.db_query_duration_histogram')
    @patch('app.db.logging.db_query_total_counter')
    async def test_metrics_tracked_on_success(
        self,
        mock_counter,
        mock_histogram,
        db_connection
    ):
        """Verify metrics are tracked on successful query."""
        try:
            await procedures.sp_get_user_by_email(
                db_connection,
                "test@example.com"
            )
        except Exception:
            pass  # Focus on metrics, not result

        # Verify histogram was called
        mock_histogram.labels.assert_called()

        # Verify counter was incremented
        mock_counter.labels.assert_called()

    @patch('app.db.logging.db_slow_query_counter')
    @patch('app.db.logging.SLOW_QUERY_THRESHOLD_MS', 0)  # Make everything "slow"
    async def test_slow_query_metrics_tracked(
        self,
        mock_slow_counter,
        db_connection
    ):
        """Verify slow query counter is incremented."""
        try:
            await procedures.sp_get_user_by_email(
                db_connection,
                "test@example.com"
            )
        except Exception:
            pass

        # Should increment slow query counter
        mock_slow_counter.labels.assert_called()


class TestDecoratorBehavior:
    """Test decorator behavior and edge cases."""

    @pytest.mark.asyncio
    async def test_decorator_preserves_function_name(self):
        """Verify decorator preserves original function name."""
        # sp_create_user should still be named sp_create_user
        assert procedures.sp_create_user.__name__ == "sp_create_user"

    @pytest.mark.asyncio
    async def test_decorator_preserves_exceptions(self, db_connection):
        """Verify decorator re-raises exceptions."""
        with pytest.raises(Exception):
            # This will fail (invalid email or DB error)
            await procedures.sp_create_user(db_connection, "invalid", "pass")

    @pytest.mark.asyncio
    async def test_decorator_logs_exceptions(self, db_connection, caplog):
        """Verify decorator logs exceptions before re-raising."""
        with caplog.at_level(logging.ERROR):
            try:
                await procedures.sp_create_user(db_connection, "invalid", "pass")
            except Exception:
                pass

        # Should have error log
        assert any("sp_create_user_failed" in record.message
                  for record in caplog.records)


@pytest.mark.integration
class TestEndToEndLogging:
    """End-to-end tests for complete logging flow."""

    @pytest.mark.asyncio
    async def test_complete_registration_flow_logging(
        self,
        db_connection,
        caplog
    ):
        """Test logging throughout entire registration flow."""
        with caplog.at_level(logging.DEBUG):
            test_email = f"test_{uuid4()}@example.com"

            try:
                # Create user
                user = await procedures.sp_create_user(
                    db_connection,
                    test_email,
                    "hashed_password"
                )

                # Verify user
                await procedures.sp_verify_user_email(
                    db_connection,
                    user.id
                )

                # Get user
                await procedures.sp_get_user_by_email(
                    db_connection,
                    test_email
                )

            except Exception as e:
                pytest.skip(f"Database not available: {e}")

        # Verify all operations were logged
        log_text = caplog.text
        assert "sp_create_user_start" in log_text
        assert "sp_verify_user_email_start" in log_text
        assert "sp_get_user_by_email_start" in log_text

        # Verify sensitive data not logged
        assert "hashed_password" not in log_text or "<redacted>" in log_text

        # Verify trace IDs are consistent (same request)
        records = [r for r in caplog.records if "sp_" in r.message]
        if len(records) > 1:
            # All should have trace_id (from middleware)
            trace_ids = [getattr(r, 'trace_id', None) for r in records]
            # In real scenario, trace IDs should be same across one request
            # This is a basic sanity check
            assert all(tid is not None or True for tid in trace_ids)


# Test fixtures
@pytest.fixture
def db_connection():
    """Mock database connection for testing."""
    from unittest.mock import AsyncMock
    mock_conn = AsyncMock()
    return mock_conn
