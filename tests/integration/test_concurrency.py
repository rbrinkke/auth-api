"""
Concurrency and race condition integration tests.

Tests race conditions and concurrent operations with real database and Redis.
"""
import pytest
import asyncio

from app.services.registration_service import RegistrationService
from app.services.password_reset_service import PasswordResetService
from app.services.password_validation_service import PasswordValidationService


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
class TestConcurrency:
    """Integration tests for concurrent operations."""

    async def test_concurrent_registrations_same_email(
        self,
        test_db_connection,
        clean_redis
    ):
        """Test that concurrent registrations with same email are handled correctly."""
        # Arrange
        password_service = PasswordValidationService()
        registration_service = RegistrationService(
            conn=test_db_connection,
            redis=clean_redis,
            password_validation_svc=password_service
        )

        test_email = f"concurrent-test-{int(asyncio.get_event_loop().time())}@example.com"
        password = "StrongPassword123!@#$"

        # Act - Launch 10 concurrent registration attempts
        tasks = [
            registration_service.register_user(email=test_email, password=password)
            for _ in range(10)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert - Exactly one should succeed, rest should fail
        successes = [r for r in results if not isinstance(r, Exception)]
        failures = [r for r in results if isinstance(r, Exception)]

        assert len(successes) == 1, f"Expected 1 success, got {len(successes)}"
        assert len(failures) == 9, f"Expected 9 failures, got {len(failures)}"

        # Verify the successful registration
        assert successes[0].user.email == test_email.lower()
        assert successes[0].verification_token is not None

    async def test_concurrent_password_reset_same_user(
        self,
        test_db_connection,
        clean_redis
    ):
        """Test concurrent password reset requests for same user."""
        # Arrange
        password_service = PasswordValidationService()
        reset_service = PasswordResetService(
            conn=test_db_connection,
            redis=clean_redis,
            password_validation_svc=password_service
        )

        test_email = f"concurrent-reset-{int(asyncio.get_event_loop().time())}@example.com"

        # First, create a user
        registration_service = RegistrationService(
            conn=test_db_connection,
            redis=clean_redis,
            password_validation_svc=password_service
        )
        await registration_service.register_user(
            email=test_email,
            password="StrongPassword123!@#$"
        )

        # Act - Launch 5 concurrent reset requests
        tasks = [
            reset_service.request_password_reset(test_email)
            for _ in range(5)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert - All should succeed (but might have different tokens)
        tokens = [r for r in results if r and isinstance(r, str) and len(r) > 0]
        assert len(tokens) == 5, f"Expected 5 tokens, got {len(tokens)}"

        # All tokens should be valid UUID-like strings
        for token in tokens:
            assert len(token) > 20  # Basic validation

    async def test_concurrent_verification_token_verification(
        self,
        test_db_connection,
        clean_redis
    ):
        """Test concurrent verification attempts with same token."""
        # Arrange
        password_service = PasswordValidationService()
        registration_service = RegistrationService(
            conn=test_db_connection,
            redis=clean_redis,
            password_validation_svc=password_service
        )

        test_email = f"concurrent-verify-{int(asyncio.get_event_loop().time())}@example.com"
        password = "StrongPassword123!@#$"

        # Create a user
        result = await registration_service.register_user(
            email=test_email,
            password=password
        )

        verification_token = result.verification_token

        # Act - Launch concurrent verification attempts
        from app.db.procedures import sp_verify_user_email

        tasks = [
            sp_verify_user_email(test_db_connection, verification_token)
            for _ in range(5)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert - First should succeed, rest should find token already used
        successes = [r for r in results if r is True]
        already_verified = [r for r in results if r is False]

        assert len(successes) == 1, f"Expected 1 success, got {len(successes)}"
        assert len(already_verified) == 4, f"Expected 4 'already verified', got {len(already_verified)}"

    async def test_concurrent_user_lookup_duplicate_prevention(
        self,
        test_db_connection,
        clean_redis
    ):
        """Test that concurrent user lookups don't cause duplicate user creation."""
        # This tests the database-level constraints
        # Arrange - Simulate simultaneous user registration attempts

        test_email = f"concurrent-lookup-{int(asyncio.get_event_loop().time())}@example.com"
        password1 = "PasswordOne123!@#$"
        password2 = "PasswordTwo456!@#$"

        # Act - Register same email with different passwords simultaneously
        # Using raw SQL to bypass service layer validation

        import asyncpg
        from app.core.security import hash_password

        async def attempt_registration(pwd):
            conn = test_db_connection
            try:
                # Check if user exists
                existing = await conn.fetchrow(
                    "SELECT id FROM activity.users WHERE email = $1",
                    test_email.lower()
                )
                if existing:
                    return "exists"

                # Hash password
                hashed_pwd = hash_password(pwd)

                # Try to create user
                try:
                    await sp_create_user(conn, test_email.lower(), hashed_pwd)
                    return "created"
                except asyncpg.UniqueViolationError:
                    return "violation"
            except Exception as e:
                return f"error: {str(e)}"

        from app.db.procedures import sp_create_user

        tasks = [
            attempt_registration(password1),
            attempt_registration(password2)
        ]

        results = await asyncio.gather(*tasks)

        # Assert - Should handle race condition gracefully
        assert len(results) == 2
        # One should succeed, one should detect existence
        assert "created" in results
        assert ("exists" in results or "violation" in results)

    async def test_concurrent_redis_operations(
        self,
        test_db_connection,
        clean_redis
    ):
        """Test concurrent Redis operations don't interfere with each other."""
        # Arrange
        test_keys = [f"test_key_{i}" for i in range(10)]

        # Act - Concurrent set operations
        async def set_key(key, value):
            await clean_redis.client.set(key, value)
            await asyncio.sleep(0.001)  # Small delay to increase chance of race
            retrieved = await clean_redis.client.get(key)
            return retrieved == value

        tasks = [set_key(key, f"value_{key}") for key in test_keys]
        results = await asyncio.gather(*tasks)

        # Assert - All operations should succeed independently
        assert all(results), "All Redis operations should succeed"

        # Verify all values were set correctly
        for key in test_keys:
            value = await clean_redis.client.get(key)
            assert value == f"value_{key}".encode()

    async def test_concurrent_token_blacklist_operations(
        self,
        clean_redis
    ):
        """Test that concurrent token blacklist operations are safe."""
        # Arrange
        tokens = [f"token_{i}" for i in range(10)]

        # Act - Concurrent blacklist operations
        async def blacklist_token(token):
            # Add to blacklist
            await clean_redis.client.setex(
                f"blacklist:{token}",
                30 * 24 * 3600,  # 30 days
                "true"
            )
            # Check if blacklisted
            is_blacklisted = await clean_redis.client.exists(f"blacklist:{token}")
            return is_blacklisted

        tasks = [blacklist_token(token) for token in tokens]
        results = await asyncio.gather(*tasks)

        # Assert - All tokens should be blacklisted
        assert all(results), "All tokens should be blacklisted"

        # Verify no interference between operations
        for token in tokens:
            is_blacklisted = await clean_redis.client.exists(f"blacklist:{token}")
            assert is_blacklisted, f"Token {token} should be blacklisted"

    async def test_concurrent_email_verification_requests(
        self,
        test_db_connection,
        clean_redis
    ):
        """Test concurrent verification requests don't cause issues."""
        # Arrange
        password_service = PasswordValidationService()
        registration_service = RegistrationService(
            conn=test_db_connection,
            redis=clean_redis,
            password_validation_svc=password_service
        )

        test_email = f"concurrent-email-{int(asyncio.get_event_loop().time())}@example.com"
        password = "StrongPassword123!@#$"

        # Create user
        result = await registration_service.register_user(
            email=test_email,
            password=password
        )

        token = result.verification_token

        # Act - Concurrent verification attempts
        from app.db.procedures import sp_verify_user_email

        # Limit to 3 attempts to avoid overwhelming the test
        tasks = [
            sp_verify_user_email(test_db_connection, token)
            for _ in range(3)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert - First should succeed, rest should fail
        assert True in results, "First verification should succeed"
        assert False in results, "Subsequent verifications should be prevented"

    async def test_concurrent_registration_token_storage(
        self,
        test_db_connection,
        clean_redis
    ):
        """Test that tokens are stored correctly during concurrent registrations."""
        # Arrange
        password_service = PasswordValidationService()
        registration_service = RegistrationService(
            conn=test_db_connection,
            redis=clean_redis,
            password_validation_svc=password_service
        )

        base_email = int(asyncio.get_event_loop().time())
        test_email = f"token-storage-{base_email}@example.com"
        password = "StrongPassword123!@#$"

        # Act - Register same user multiple times concurrently
        tasks = [
            registration_service.register_user(email=test_email, password=password)
            for _ in range(3)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert - Only one should succeed
        successful_results = [r for r in results if hasattr(r, 'user')]
        assert len(successful_results) == 1

        # Verify token storage
        result = successful_results[0]
        stored_user_id = await clean_redis.get_user_id_from_verification_token(
            result.verification_token
        )
        assert stored_user_id == result.user.id

        # Verify token TTL is set
        ttl = await clean_redis.client.ttl(
            f"verification_token:{result.verification_token}"
        )
        assert ttl > 0  # TTL should be set
        assert ttl <= 24 * 3600  # Should be less than or equal to 24 hours

    async def test_rapid_concurrent_requests_dont_crash(
        self,
        test_db_connection,
        clean_redis
    ):
        """Test that rapid concurrent requests don't cause crashes."""
        # Arrange
        password_service = PasswordValidationService()
        registration_service = RegistrationService(
            conn=test_db_connection,
            redis=clean_redis,
            password_validation_svc=password_service
        )

        # Act - Send many concurrent requests rapidly
        async def rapid_registration(i):
            try:
                return await registration_service.register_user(
                    email=f"rapid-{i}@example.com",
                    password="StrongPassword123!@#$"
                )
            except Exception as e:
                return f"error: {type(e).__name__}"

        # Send 20 concurrent requests
        tasks = [rapid_registration(i) for i in range(20)]
        results = await asyncio.gather(*tasks)

        # Assert - No crashes, all requests handled
        assert len(results) == 20
        errors = [r for r in results if isinstance(r, str) and r.startswith("error")]
        assert len(errors) == 0, f"Should not have errors, got: {errors}"

        # All should have successful results
        successful = [r for r in results if hasattr(r, 'user')]
        assert len(successful) == 20, f"All 20 registrations should succeed"
