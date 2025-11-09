"""
Database Stored Procedures Mock

Provides pytest fixtures and mock implementations for all database stored procedures.
Includes realistic data generation using Faker and proper state management.

Usage:
    # In conftest.py or test file
    from mocks.db_procedures_mock import mock_db_procedures

    @pytest.mark.asyncio
    async def test_user_creation(mock_db_procedures):
        user = await mock_db_procedures.sp_create_user(
            "test@example.com",
            "hashed_password_here"
        )
        assert user.email == "test@example.com"
        assert user.is_verified is False
"""

import pytest
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from unittest.mock import AsyncMock
from faker import Faker

fake = Faker()


# ============================================================================
# User Record Mock
# ============================================================================

@dataclass
class MockUserRecord:
    """Mock for UserRecord from database procedures."""
    id: UUID
    email: str
    hashed_password: Optional[str]
    is_verified: bool
    is_active: bool
    created_at: datetime
    verified_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None

    @classmethod
    def create_fake(
        cls,
        email: Optional[str] = None,
        is_verified: bool = False,
        is_active: bool = True,
        hashed_password: Optional[str] = None
    ) -> "MockUserRecord":
        """Create a fake user record for testing."""
        return cls(
            id=uuid4(),
            email=email or fake.email().lower(),
            hashed_password=hashed_password or fake.sha256(),
            is_verified=is_verified,
            is_active=is_active,
            created_at=fake.date_time_this_year(tzinfo=timezone.utc),
            verified_at=fake.date_time_this_month(tzinfo=timezone.utc) if is_verified else None,
            last_login_at=None
        )


# ============================================================================
# Refresh Token Storage
# ============================================================================

@dataclass
class MockRefreshToken:
    """Mock for refresh token database record."""
    user_id: UUID
    token: str
    jti: str
    expires_at: datetime
    revoked: bool = False
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def is_valid(self) -> bool:
        """Check if token is valid (not revoked and not expired)."""
        now = datetime.now(timezone.utc)
        # Convert to naive for comparison if needed
        expires_at_naive = self.expires_at.replace(tzinfo=None) if self.expires_at.tzinfo else self.expires_at
        now_naive = now.replace(tzinfo=None)
        return not self.revoked and expires_at_naive > now_naive


# ============================================================================
# Mock Database Procedures Class
# ============================================================================

class MockDBProcedures:
    """
    Mock implementation of all database stored procedures.

    Provides in-memory storage and realistic behavior for testing
    without requiring a database connection.
    """

    def __init__(self):
        """Initialize mock database with empty storage."""
        self._users: Dict[UUID, MockUserRecord] = {}
        self._users_by_email: Dict[str, UUID] = {}
        self._refresh_tokens: List[MockRefreshToken] = []

    def add_user(self, user: MockUserRecord) -> MockUserRecord:
        """
        Add a user to the mock database (testing utility).

        Args:
            user: User record to add

        Returns:
            The added user record
        """
        self._users[user.id] = user
        self._users_by_email[user.email.lower()] = user.id
        return user

    def clear(self):
        """Clear all mock data (test isolation)."""
        self._users.clear()
        self._users_by_email.clear()
        self._refresh_tokens.clear()

    # ========================================================================
    # User Creation and Retrieval
    # ========================================================================

    async def sp_create_user(
        self,
        conn: AsyncMock,  # Mock connection (not used)
        email: str,
        hashed_password: str
    ) -> MockUserRecord:
        """
        Mock sp_create_user - Create a new user.

        Args:
            conn: Mock database connection
            email: User email address
            hashed_password: Hashed password

        Returns:
            Created user record

        Raises:
            ValueError: If email already exists
        """
        email_lower = email.lower()

        # Check for duplicate email
        if email_lower in self._users_by_email:
            raise ValueError(f"User with email {email} already exists")

        # Create new user
        user = MockUserRecord(
            id=uuid4(),
            email=email_lower,
            hashed_password=hashed_password,
            is_verified=False,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            verified_at=None,
            last_login_at=None
        )

        self.add_user(user)
        return user

    async def sp_get_user_by_email(
        self,
        conn: AsyncMock,
        email: str
    ) -> Optional[MockUserRecord]:
        """
        Mock sp_get_user_by_email - Get user by email address.

        Args:
            conn: Mock database connection
            email: User email address

        Returns:
            User record if found, None otherwise
        """
        email_lower = email.lower()
        user_id = self._users_by_email.get(email_lower)

        if user_id is None:
            return None

        return self._users.get(user_id)

    async def sp_get_user_by_id(
        self,
        conn: AsyncMock,
        user_id: UUID
    ) -> Optional[MockUserRecord]:
        """
        Mock sp_get_user_by_id - Get user by ID.

        Args:
            conn: Mock database connection
            user_id: User UUID

        Returns:
            User record if found, None otherwise
        """
        return self._users.get(user_id)

    # ========================================================================
    # Email Verification
    # ========================================================================

    async def sp_verify_user_email(
        self,
        conn: AsyncMock,
        user_id: UUID
    ) -> bool:
        """
        Mock sp_verify_user_email - Verify user's email address.

        Args:
            conn: Mock database connection
            user_id: User UUID

        Returns:
            True if successful, False if user not found
        """
        user = self._users.get(user_id)

        if user is None:
            return False

        user.is_verified = True
        user.verified_at = datetime.now(timezone.utc)
        return True

    # ========================================================================
    # Refresh Token Management
    # ========================================================================

    async def sp_save_refresh_token(
        self,
        conn: AsyncMock,
        user_id: UUID,
        token: str,
        expires_delta: timedelta
    ) -> bool:
        """
        Mock sp_save_refresh_token - Save a refresh token.

        Args:
            conn: Mock database connection
            user_id: User UUID
            token: Refresh token
            expires_delta: Time until expiration

        Returns:
            True on success
        """
        # Extract JTI from token (mock - just use a UUID)
        from jose import jwt
        try:
            payload = jwt.get_unverified_claims(token)
            jti = payload.get("jti", str(uuid4()))
        except:
            jti = str(uuid4())

        # Calculate expiration
        now_utc = datetime.now(timezone.utc)
        expires_at = now_utc + expires_delta

        # Save token
        refresh_token = MockRefreshToken(
            user_id=user_id,
            token=token,
            jti=jti,
            expires_at=expires_at,
            revoked=False
        )

        self._refresh_tokens.append(refresh_token)
        return True

    async def sp_validate_refresh_token(
        self,
        conn: AsyncMock,
        user_id: UUID,
        token: str
    ) -> bool:
        """
        Mock sp_validate_refresh_token - Validate a refresh token.

        Args:
            conn: Mock database connection
            user_id: User UUID
            token: Refresh token to validate

        Returns:
            True if token is valid, False otherwise
        """
        for refresh_token in self._refresh_tokens:
            if (refresh_token.user_id == user_id and
                refresh_token.token == token and
                refresh_token.is_valid()):
                return True

        return False

    async def sp_revoke_refresh_token(
        self,
        conn: AsyncMock,
        user_id: UUID,
        token: str
    ) -> None:
        """
        Mock sp_revoke_refresh_token - Revoke a specific refresh token.

        Args:
            conn: Mock database connection
            user_id: User UUID
            token: Refresh token to revoke
        """
        for refresh_token in self._refresh_tokens:
            if refresh_token.user_id == user_id and refresh_token.token == token:
                refresh_token.revoked = True

    async def sp_revoke_all_refresh_tokens(
        self,
        conn: AsyncMock,
        user_id: UUID
    ) -> None:
        """
        Mock sp_revoke_all_refresh_tokens - Revoke all refresh tokens for a user.

        Args:
            conn: Mock database connection
            user_id: User UUID
        """
        for refresh_token in self._refresh_tokens:
            if refresh_token.user_id == user_id:
                refresh_token.revoked = True

    # ========================================================================
    # Password Management
    # ========================================================================

    async def sp_update_password(
        self,
        conn: AsyncMock,
        user_id: UUID,
        hashed_password: str
    ) -> bool:
        """
        Mock sp_update_password - Update user's password.

        Args:
            conn: Mock database connection
            user_id: User UUID
            hashed_password: New hashed password

        Returns:
            True if successful, False if user not found
        """
        user = self._users.get(user_id)

        if user is None:
            return False

        user.hashed_password = hashed_password
        return True

    # ========================================================================
    # Utility Functions
    # ========================================================================

    async def check_email_exists(
        self,
        conn: AsyncMock,
        email: str
    ) -> bool:
        """
        Mock check_email_exists - Check if email is already registered.

        Args:
            conn: Mock database connection
            email: Email address to check

        Returns:
            True if email exists, False otherwise
        """
        user = await self.sp_get_user_by_email(conn, email)
        return user is not None

    def get_user_count(self) -> int:
        """Get total number of users (testing utility)."""
        return len(self._users)

    def get_token_count(self, user_id: Optional[UUID] = None) -> int:
        """
        Get number of refresh tokens (testing utility).

        Args:
            user_id: Optional filter by user

        Returns:
            Token count
        """
        if user_id is None:
            return len(self._refresh_tokens)

        return sum(1 for t in self._refresh_tokens if t.user_id == user_id)


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture
def mock_db_procedures():
    """
    Mock database procedures for unit tests.

    Returns a MockDBProcedures instance with in-memory storage.
    Automatically clears between tests.

    Example:
        async def test_user_creation(mock_db_procedures):
            conn = AsyncMock()
            user = await mock_db_procedures.sp_create_user(
                conn, "test@example.com", "hashed_pwd"
            )
            assert user.email == "test@example.com"
    """
    mock = MockDBProcedures()
    yield mock
    mock.clear()


@pytest.fixture
def mock_db_with_users():
    """
    Mock database pre-populated with test users.

    Provides a database with several test users for testing.

    Example:
        async def test_with_existing_users(mock_db_with_users):
            conn = AsyncMock()
            user = await mock_db_with_users.sp_get_user_by_email(
                conn, "verified@example.com"
            )
            assert user.is_verified is True
    """
    mock = MockDBProcedures()

    # Create test users
    verified_user = MockUserRecord.create_fake(
        email="verified@example.com",
        is_verified=True,
        hashed_password="verified_password_hash"
    )
    mock.add_user(verified_user)

    unverified_user = MockUserRecord.create_fake(
        email="unverified@example.com",
        is_verified=False,
        hashed_password="unverified_password_hash"
    )
    mock.add_user(unverified_user)

    inactive_user = MockUserRecord.create_fake(
        email="inactive@example.com",
        is_verified=True,
        is_active=False,
        hashed_password="inactive_password_hash"
    )
    mock.add_user(inactive_user)

    yield mock
    mock.clear()


@pytest.fixture
def mock_db_connection(mock_db_procedures):
    """
    Mock database connection with procedure overrides.

    Use this to replace database connection dependency in services.

    Example:
        def test_service(mock_db_connection):
            service = RegistrationService(db=mock_db_connection)
            # Service will use mock procedures
    """
    conn = AsyncMock()

    # Override connection methods to use mock procedures
    conn.sp_create_user = mock_db_procedures.sp_create_user
    conn.sp_get_user_by_email = mock_db_procedures.sp_get_user_by_email
    conn.sp_get_user_by_id = mock_db_procedures.sp_get_user_by_id
    conn.sp_verify_user_email = mock_db_procedures.sp_verify_user_email
    conn.sp_save_refresh_token = mock_db_procedures.sp_save_refresh_token
    conn.sp_validate_refresh_token = mock_db_procedures.sp_validate_refresh_token
    conn.sp_revoke_refresh_token = mock_db_procedures.sp_revoke_refresh_token
    conn.sp_revoke_all_refresh_tokens = mock_db_procedures.sp_revoke_all_refresh_tokens
    conn.sp_update_password = mock_db_procedures.sp_update_password

    return conn


# ============================================================================
# Factory Functions
# ============================================================================

def create_mock_user(
    email: Optional[str] = None,
    is_verified: bool = False,
    is_active: bool = True,
    hashed_password: Optional[str] = None
) -> MockUserRecord:
    """
    Create a mock user record.

    Args:
        email: User email (random if not provided)
        is_verified: Whether email is verified
        is_active: Whether account is active
        hashed_password: Password hash (random if not provided)

    Returns:
        MockUserRecord instance
    """
    return MockUserRecord.create_fake(
        email=email,
        is_verified=is_verified,
        is_active=is_active,
        hashed_password=hashed_password
    )
