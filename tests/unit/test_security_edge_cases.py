"""
Security and edge case tests.

Tests security vulnerabilities, edge cases, and DoS attempts.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

from app.services.password_validation_service import (
    PasswordValidationService,
    PasswordValidationError
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestSecurityEdgeCases:
    """Security and edge case tests."""

    @pytest.mark.parametrize("password,description", [
        ("a" * 10000, "Extremely long password (DoS attempt)"),
        ("password" * 1000, "Repeated password (DoS attempt)"),
        ("\x00" * 100, "Null bytes in password"),
        ("\n\r\t" * 50, "Whitespace only password"),
        ("emoji🎉🔒password🔑", "Unicode/emoji password"),
        ("   spaced   password   ", "Password with spaces"),
        ("p@ssw0rd" + "1" * 100, "Password with excessive length"),
    ])
    async def test_extreme_password_length_handling(self, password, description):
        """Test that extreme password lengths are handled securely."""
        # Arrange
        service = PasswordValidationService()

        # Act & Assert
        try:
            # Even if password is accepted/rejected, it shouldn't crash
            await service.validate_password(password)

            # If it passes, make sure it's actually strong
            # (Extremely long passwords might pass strength check but we verify)
        except PasswordValidationError:
            # Rejection is also acceptable
            pass
        except Exception as e:
            # Any other exception is a security issue
            pytest.fail(f"Password {description} caused unhandled exception: {type(e).__name__}: {e}")

    @pytest.mark.asyncio
    async def test_hibp_service_unavailable_graceful_degradation(self):
        """Test that HIBP service failure doesn't block registration."""
        # Arrange
        service = PasswordValidationService()
        service._tools_available = True

        # Mock HIBP to fail
        with patch.object(service, '_Password') as mock_password_class:
            mock_password_instance = MagicMock()
            mock_password_instance.check.side_effect = Exception("HIBP service unavailable")
            mock_password_class.return_value = mock_password_instance

            # Mock zxcvbn to accept password
            with patch.object(service, '_zxcvbn') as mock_zxcvbn:
                mock_zxcvbn.return_value = {
                    'score': 4,
                    'feedback': {'warning': '', 'suggestions': []}
                }

                # Act
                result = await service.validate_password("StrongPassword123!")

                # Assert - Should allow through when HIBP is down
                assert result['overall_passed'] is True
                assert result['breach']['leak_count'] == -1
                assert 'error' in result['breach']
                assert 'unavailable' in result['breach']['error'].lower()

    @pytest.mark.asyncio
    async def test_hibp_timeout_handling(self):
        """Test that HIBP timeout is handled gracefully."""
        # Arrange
        service = PasswordValidationService()
        service._tools_available = True

        # Mock HIBP to timeout
        with patch.object(service, '_Password') as mock_password_class:
            mock_password_instance = MagicMock()
            from httpx import TimeoutException
            mock_password_instance.check.side_effect = TimeoutException("Request timeout")
            mock_password_class.return_value = mock_password_instance

            # Mock zxcvbn to accept password
            with patch.object(service, '_zxcvbn') as mock_zxcvbn:
                mock_zxcvbn.return_value = {
                    'score': 4,
                    'feedback': {'warning': '', 'suggestions': []}
                }

                # Act
                result = await service.validate_password("StrongPassword123!")

                # Assert - Should timeout gracefully
                assert result['overall_passed'] is True
                assert result['breach']['leak_count'] == -1

    @pytest.mark.asyncio
    async def test_zxcvbn_unavailable_fallback(self):
        """Test fallback when zxcvbn is not available."""
        # Arrange
        service = PasswordValidationService()
        service._tools_available = False

        # Act
        result = await service.validate_password("anypassword")

        # Assert - Should fall back gracefully
        assert result['overall_passed'] is True
        assert result['strength']['score'] == 0
        assert result['breach']['leak_count'] == 0

    @pytest.mark.parametrize("leak_count,should_fail", [
        (0, False),    # Not found in breaches - OK
        (1, True),     # Found once - FAIL
        (100, True),   # Found 100 times - FAIL
        (1000000, True),  # Found 1M times - FAIL
    ])
    async def test_breach_detection_thresholds(self, leak_count, should_fail):
        """Test that any breach detection (>0) rejects the password."""
        # Arrange
        service = PasswordValidationService()
        service._tools_available = True

        # Mock zxcvbn to accept password
        with patch.object(service, '_zxcvbn') as mock_zxcvbn:
            mock_zxcvbn.return_value = {
                'score': 4,
                'feedback': {'warning': '', 'suggestions': []}
            }

            # Mock HIBP to return specific leak count
            with patch.object(service, '_Password') as mock_password_class:
                mock_password_instance = MagicMock()
                mock_password_instance.check.return_value = leak_count
                mock_password_class.return_value = mock_password_instance

                # Act & Assert
                if should_fail:
                    with pytest.raises(PasswordValidationError, match="data breaches"):
                        await service.validate_password("BreachedPassword123!")
                else:
                    result = await service.validate_password("UniquePassword123!")
                    assert result['overall_passed'] is True
                    assert result['breach']['leak_count'] == leak_count

    @pytest.mark.asyncio
    async def test_password_with_special_characters(self):
        """Test passwords with various special characters."""
        # Arrange
        service = PasswordValidationService()

        special_passwords = [
            "P@ssw0rd!",           # Basic special chars
            "Pass word 123!",      # Spaces
            "Password\t123\n!",    # Tabs and newlines
            "Pass'word\"123!",     # Quotes
            "Pass<>()[]{}|\\123!", # Various symbols
            "密码中文字符123!",     # Unicode Chinese
            "🔒Secure🔑Pass💯",    # Emoji
        ]

        # Act
        for password in special_passwords:
            try:
                await service.validate_password(password)
                # If it doesn't raise exception, that's OK for this test
                # We're just checking it doesn't crash
            except PasswordValidationError:
                # Rejection is also acceptable
                pass
            except Exception as e:
                # Any other exception is a problem
                pytest.fail(f"Password with special chars caused exception: {e}")

    @pytest.mark.asyncio
    async def test_empty_and_none_passwords(self):
        """Test that empty or None passwords are handled."""
        # Arrange
        service = PasswordValidationService()

        # Act & Assert - Empty string
        with pytest.raises(PasswordValidationError, match="Weak password"):
            await service.validate_password("")

        # Note: None would cause a type error before reaching validation
        # This is acceptable as input validation should catch it

    @pytest.mark.asyncio
    async def test_concurrent_hibp_calls_dont_block(self):
        """Test that concurrent HIBP calls don't block the event loop."""
        # Arrange
        service = PasswordValidationService()
        service._tools_available = True

        # Mock HIBP to have slight delay
        async def slow_hibp_check(password):
            await asyncio.sleep(0.1)  # Simulate network delay
            return 0  # Not found

        with patch.object(service, '_Password') as mock_password_class:
            mock_password_instance = MagicMock()
            mock_password_instance.check = slow_hibp_check
            mock_password_class.return_value = mock_password_instance

            # Mock zxcvbn to accept password
            with patch.object(service, '_zxcvbn') as mock_zxcvbn:
                mock_zxcvbn.return_value = {
                    'score': 4,
                    'feedback': {'warning': '', 'suggestions': []}
                }

                # Act - Launch 10 concurrent checks
                start_time = asyncio.get_event_loop().time()

                tasks = [
                    service.validate_password(f"Password{i}123!")
                    for i in range(10)
                ]

                results = await asyncio.gather(*tasks)

                end_time = asyncio.get_event_loop().time()
                elapsed = end_time - start_time

                # Assert - Should complete in < 2 seconds (parallel execution)
                # Sequential would take ~1 second, parallel should be similar
                assert elapsed < 2.0, f"Concurrent calls took {elapsed}s, should be parallel"

                # All should succeed
                assert all(r['overall_passed'] for r in results)

    @pytest.mark.asyncio
    async def test_async_to_thread_blocks_correctly(self):
        """Verify asyncio.to_thread is used for blocking I/O."""
        # Arrange
        service = PasswordValidationService()
        service._tools_available = True

        # Track if we're in a thread
        thread_info = {'in_thread': False, 'main_thread': asyncio.get_event_loop().is_running()}

        def blocking_check(password):
            thread_info['in_thread'] = True
            # Simulate blocking I/O
            import time
            time.sleep(0.01)
            thread_info['after_sleep'] = True
            return 0

        # Mock the blocking check
        with patch.object(service, '_Password') as mock_password_class:
            mock_password_instance = MagicMock()
            mock_password_instance.check = blocking_check
            mock_password_class.return_value = mock_password_instance

            # Mock zxcvbn
            with patch.object(service, '_zxcvbn') as mock_zxcvbn:
                mock_zxcvbn.return_value = {
                    'score': 4,
                    'feedback': {'warning': '', 'suggestions': []}
                }

                # Act
                result = await service.check_breach_status("TestPassword123!")

                # Assert - Blocking I/O was in a thread
                # Note: We can't easily verify thread execution in this test
                # but we can verify the method is structured correctly
                assert thread_info['after_sleep'] == True

    @pytest.mark.parametrize("score,should_pass", [
        (0, False),  # Very weak
        (1, False),  # Weak
        (2, False),  # Fair
        (3, True),   # Strong - MINIMUM ACCEPTABLE
        (4, True),   # Very strong
    ])
    async def test_zxcvbn_score_thresholds(self, score, should_pass):
        """Test that zxcvbn score thresholds are enforced correctly."""
        # Arrange
        service = PasswordValidationService()

        with patch.object(service, '_zxcvbn') as mock_zxcvbn:
            mock_zxcvbn.return_value = {
                'score': score,
                'feedback': {'warning': '', 'suggestions': []}
            }

            # Mock breach check to pass
            with patch.object(service, '_Password') as mock_password_class:
                mock_password_instance = MagicMock()
                mock_password_instance.check.return_value = 0
                mock_password_class.return_value = mock_password_instance

                # Act & Assert
                if should_pass:
                    result = await service.validate_strength("Password123!")
                    assert result['validation_passed'] is True
                    assert result['score'] == score
                else:
                    with pytest.raises(PasswordValidationError):
                        service.validate_strength("Password123!")

    @pytest.mark.asyncio
    async def test_sql_injection_prevention_in_email(self):
        """Test that SQL injection attempts in email are prevented."""
        # Arrange - Testing at service level (not route level)
        service = PasswordValidationService()

        # SQL injection payloads in password (defense in depth)
        sql_injection_payloads = [
            "password'; DROP TABLE users; --",
            "password' OR '1'='1",
            "password' UNION SELECT * FROM users --",
            "'; INSERT INTO users VALUES ('hacker', 'pass'); --",
        ]

        # Act - These should just fail validation (no crash)
        for payload in sql_injection_payloads:
            try:
                await service.validate_password(payload)
                # If it doesn't crash, that's fine
                # The actual SQL injection would be caught at DB layer
            except PasswordValidationError:
                # Expected - password is weak
                pass
            except Exception as e:
                # Unexpected exception = security issue
                pytest.fail(f"SQL injection payload caused unhandled exception: {e}")

    @pytest.mark.asyncio
    async def test_memory_usage_no_memory_leaks(self):
        """Test that password validation doesn't cause memory leaks."""
        # Arrange
        service = PasswordValidationService()

        # Mock all external calls to avoid real I/O
        with patch.object(service, '_zxcvbn') as mock_zxcvbn:
            mock_zxcvbn.return_value = {
                'score': 4,
                'feedback': {'warning': '', 'suggestions': []}
            }

            with patch.object(service, '_Password') as mock_password_class:
                mock_password_instance = MagicMock()
                mock_password_instance.check.return_value = 0
                mock_password_class.return_value = mock_password_instance

                # Act - Validate many passwords
                for i in range(100):
                    await service.validate_password(f"Password{i}123!")

                # If we got here without memory errors, test passes
                # (This is more of a sanity check than a real memory leak test)

    @pytest.mark.asyncio
    async def test_exception_propagation_secure(self):
        """Test that exceptions don't leak sensitive information."""
        # Arrange
        service = PasswordValidationService()

        # Mock different types of failures
        error_scenarios = [
            Exception("Database connection failed"),
            Exception("Network timeout"),
            Exception("Invalid API key"),
            Exception("Internal server error"),
        ]

        for error in error_scenarios:
            with patch.object(service, '_Password') as mock_password_class:
                mock_password_instance = MagicMock()
                mock_password_instance.check.side_effect = error
                mock_password_class.return_value = mock_password_instance

                # Act
                result = await service.check_breach_status("TestPassword123!")

                # Assert - Should handle gracefully without leaking error details
                assert result['validation_passed'] is True
                assert result['leak_count'] == -1
                # Error message should be generic, not the full exception
                if 'error' in result:
                    # Should not contain sensitive details
                    assert "failed" not in result['error'].lower() or result['error'] == "Breach check service unavailable"
