"""
Registration service implementing user registration business logic.

This service encapsulates all business logic for user registration:
- Password validation
- User creation
- Token generation

Email sending is handled by the route via BackgroundTasks for better performance.

Separates business logic from HTTP handling for better architecture and testability.
"""
import logging
from typing import NamedTuple

import asyncpg

from app.core.redis_client import RedisClient
from app.core.security import hash_password
from app.core.tokens import generate_verification_token
from app.db.procedures import sp_create_user

logger = logging.getLogger(__name__)


class UserRecord(NamedTuple):
    """User record from database."""
    id: str
    email: str
    is_verified: bool
    is_active: bool
    created_at: str


class RegistrationResult(NamedTuple):
    """Result of registration operation."""
    user: UserRecord
    verification_token: str


class RegistrationServiceError(Exception):
    """Base exception for registration service errors."""
    pass


class UserAlreadyExistsError(RegistrationServiceError):
    """Raised when user with email already exists."""
    pass


class RegistrationService:
    """
    Service for handling user registration business logic.

    Responsibilities:
    - Validate password strength and breach status
    - Create user in database
    - Generate and store verification token
    - Send verification email

    All database and external service calls are handled here,
    making it easy to test and maintain.
    """

    def __init__(
        self,
        conn: asyncpg.Connection,
        redis: RedisClient,
        password_validation_svc
    ):
        """
        Initialize registration service with dependencies.

        Args:
            conn: Database connection
            redis: Redis client for token storage
            password_validation_svc: Service for password validation
        """
        self.conn = conn
        self.redis = redis
        self.password_validation_svc = password_validation_svc

    async def register_user(
        self,
        email: str,
        password: str
    ) -> RegistrationResult:
        """
        Register a new user with email verification.

        Business logic flow:
        1. Validate password (strength + breach check)
        2. Hash password
        3. Create user in database
        4. Generate verification token
        5. Store token in Redis
        6. Email sending is handled by the route via BackgroundTasks

        Args:
            email: User's email address
            password: User's password

        Returns:
            RegistrationResult: User record and verification token

        Raises:
            RegistrationServiceError: If registration fails
            UserAlreadyExistsError: If email already registered
        """
        try:
            # Step 1: Validate password using dedicated service
            logger.info(f"Validating password for {email}")
            self.password_validation_svc.validate_password(password)

            # Step 2: Hash password
            logger.info(f"Hashing password for {email}")
            hashed_password = hash_password(password)

            # Step 3: Create user in database via stored procedure
            logger.info(f"Creating user in database: {email}")
            try:
                user = await sp_create_user(self.conn, email.lower(), hashed_password)
            except asyncpg.UniqueViolationError:
                logger.warning(f"Registration failed - email already exists: {email}")
                raise UserAlreadyExistsError("Email already registered")

            # Step 4: Generate verification token
            verification_token = generate_verification_token()

            # Step 5: Store token in Redis (with TTL)
            logger.info(f"Storing verification token for user {user.id}")
            await self.redis.set_verification_token(verification_token, user.id)

            # Convert to namedtuple for consistency
            user_record = UserRecord(
                id=str(user.id),
                email=user.email,
                is_verified=user.is_verified,
                is_active=user.is_active,
                created_at=str(user.created_at)
            )

            result = RegistrationResult(
                user=user_record,
                verification_token=verification_token
            )

            logger.info(f"Registration successful: {email} (id: {user.id})")
            return result

        except UserAlreadyExistsError:
            raise
        except Exception as e:
            logger.error(f"Registration failed for {email}: {str(e)}")
            raise RegistrationServiceError(
                f"Registration failed: {str(e)}"
            )


class MockRegistrationService(RegistrationService):
    """
    Mock registration service for testing.

    Simulates registration without actual database or email operations.
    """

    def __init__(self):
        """Initialize mock service."""
        self.users = []  # In-memory storage
        self.verification_tokens = {}  # In-memory token storage

    async def register_user(self, email: str, password: str) -> RegistrationResult:
        """Mock registration - no database or email operations."""
        # Validate password
        self.password_validation_svc.validate_password(password)

        # Create mock user
        user = UserRecord(
            id=f"mock-{len(self.users)}",
            email=email.lower(),
            is_verified=False,
            is_active=True,
            created_at="2024-01-01T00:00:00"
        )

        # Generate token
        token = f"mock-token-{len(self.verification_tokens)}"

        self.users.append(user)
        self.verification_tokens[token] = user.id

        logger.info(f"Mock registration successful: {email}")
        return RegistrationResult(
            user=user,
            verification_token=token
        )
