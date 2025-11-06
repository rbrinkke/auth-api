"""
Authentication service implementing login business logic.

This service encapsulates all authentication logic:
- User lookup and validation
- Password verification
- 2FA handling
- Token generation

Separates business logic from HTTP handling for better architecture and testability.
"""
import logging
from typing import NamedTuple

import asyncpg
from fastapi import Depends

from app.core.redis_client import RedisClient, get_redis
from app.core.security import verify_password
from app.core.tokens import create_access_token, create_refresh_token
from app.db.connection import get_db_connection
from app.db.procedures import sp_get_user_by_email, sp_update_last_login
from app.services.email_service import EmailService, get_email_service
from app.services.two_factor_service import TwoFactorService, get_two_factor_service

logger = logging.getLogger(__name__)


class LoginResult(NamedTuple):
    """Result of authentication operation."""
    user_id: str
    email: str
    access_token: str
    refresh_token: str
    two_factor_required: bool
    two_factor_user_id: str | None


class AuthServiceError(Exception):
    """Base exception for authentication service errors."""
    pass


class AuthService:
    """
    Service for handling user authentication business logic.

    Responsibilities:
    - User lookup and validation
    - Password verification
    - 2FA handling
    - Token generation
    - Last login timestamp update
    """

    def __init__(
        self,
        conn: asyncpg.Connection,
        redis: RedisClient,
        email_svc: EmailService
    ):
        """
        Initialize authentication service with dependencies.

        Args:
            conn: Database connection
            redis: Redis client
            email_svc: Email service for sending 2FA codes
        """
        self.conn = conn
        self.redis = redis
        self.email_svc = email_svc

    async def authenticate_user(
        self,
        email: str,
        password: str
    ) -> LoginResult:
        """
        Authenticate user with email and password.

        Flow:
        1. Find user by email
        2. Verify password
        3. Check if email is verified (hard verification)
        4. Check if account is active
        5. Handle 2FA if enabled
        6. Update last login timestamp
        7. Generate tokens

        Args:
            email: User's email address
            password: User's password

        Returns:
            LoginResult: Authentication result with tokens or 2FA requirement

        Raises:
            AuthServiceError: If authentication fails
        """
        try:
            # Step 1: Find user by email
            user = await sp_get_user_by_email(self.conn, email.lower())

            if not user:
                logger.warning(f"Login attempt with non-existent email: {email}")
                raise AuthServiceError("Invalid credentials")

            # Step 2: Verify password
            if not verify_password(password, user.hashed_password):
                logger.warning(f"Failed login attempt for user: {user.email}")
                raise AuthServiceError("Invalid credentials")

            # Step 3: Check if email is verified (Hard Verification)
            if not user.is_verified:
                logger.info(f"Login attempt by unverified user: {user.email}")
                raise AuthServiceError("Email not verified. Please check your inbox.")

            # Step 4: Check if account is active
            if not user.is_active:
                logger.warning(f"Login attempt by deactivated user: {user.email}")
                raise AuthServiceError("Account has been deactivated")

            # Step 5: Check if 2FA is enabled
            if getattr(user, 'two_factor_enabled', False):
                logger.info(f"2FA required for user: {user.email}")

                # Generate and send 2FA code
                twofa_svc = TwoFactorService(self.redis, self.email_svc)
                code = await twofa_svc.create_temp_code(
                    user_id=str(user.id),
                    purpose="login",
                    email=user.email
                )

                logger.info(f"2FA code sent to {user.email}")

                return LoginResult(
                    user_id=str(user.id),
                    email=user.email,
                    access_token="",
                    refresh_token="",
                    two_factor_required=True,
                    two_factor_user_id=str(user.id)
                )

            # Step 6: Update last login timestamp
            await sp_update_last_login(self.conn, user.id)

            # Step 7: Generate tokens
            access_token = create_access_token(user.id)
            refresh_token, _ = create_refresh_token(user.id)

            logger.info(f"User logged in successfully: {user.email} (id: {user.id})")

            return LoginResult(
                user_id=str(user.id),
                email=user.email,
                access_token=access_token,
                refresh_token=refresh_token,
                two_factor_required=False,
                two_factor_user_id=None
            )

        except AuthServiceError:
            raise
        except Exception as e:
            logger.error(f"Authentication failed for {email}: {str(e)}")
            raise AuthServiceError(
                f"Authentication failed: {str(e)}"
            )


def get_auth_service(
    conn: asyncpg.Connection = Depends(get_db_connection),
    redis: RedisClient = Depends(get_redis),
    email_svc: EmailService = Depends(get_email_service)
) -> AuthService:
    """
    Dependency injection function for AuthService.

    Args:
        conn: Database connection
        redis: Redis client
        email_svc: Email service

    Returns:
        AuthService: Configured authentication service instance

    This enables easy mocking during testing:
        app.dependency_overrides[get_auth_service] = lambda: MockAuthService()
    """
    return AuthService(
        conn=conn,
        redis=redis,
        email_svc=email_svc
    )
