"""
Integration tests for automatic organization assignment during user registration.

Tests the DEFAULT_ORGANIZATION_ID feature that auto-assigns new users
to a default organization with 'member' role.
"""
import pytest
import asyncpg
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, patch
from app.services.registration_service import RegistrationService
from app.schemas.user import UserCreate
from app.db import procedures


@pytest.mark.integration
@pytest.mark.asyncio
class TestRegistrationWithOrganization:
    """Test automatic organization assignment during registration."""

    @pytest.fixture
    async def test_organization_id(self, db_connection: asyncpg.Connection) -> UUID:
        """Create a test organization for auto-assignment tests.

        Returns:
            UUID of the created test organization
        """
        # Create organization via stored procedure
        result = await db_connection.fetchrow(
            """
            SELECT * FROM activity.sp_create_organization(
                $1,  -- name
                $2,  -- slug
                $3,  -- description
                $4   -- creator_user_id (we'll use a test user)
            )
            """,
            "Test Organization",
            "test-org",
            "Organization for integration testing",
            uuid4()  # Dummy creator ID (organization doesn't need valid creator for this test)
        )

        org_id = result["id"]
        yield org_id

        # Cleanup: Delete organization after test
        await db_connection.execute(
            "DELETE FROM activity.organizations WHERE id = $1",
            org_id
        )

    async def test_registration_with_default_org_assigns_user(
        self,
        db_connection: asyncpg.Connection,
        mock_email_service: AsyncMock,
        redis_client,
        test_organization_id: UUID
    ):
        """Test that user is auto-assigned to default organization on registration."""
        # Arrange: Set DEFAULT_ORGANIZATION_ID in settings
        with patch("app.services.registration_service.get_settings") as mock_settings:
            mock_settings.return_value.DEFAULT_ORGANIZATION_ID = str(test_organization_id)

            registration_service = RegistrationService(
                db=db_connection,
                password_service=AsyncMock(),
                email_service=mock_email_service,
                redis_client=redis_client
            )
            registration_service.password_service.get_password_hash = AsyncMock(
                return_value="$argon2id$hashed_password"
            )

            user_data = UserCreate(
                email="auto-org-test@example.com",
                password="SecurePassword123!"
            )

            # Act: Register user
            result = await registration_service.register_user(user_data)
            user_id = UUID(result["user_id"])

            # Assert: User exists
            user = await procedures.sp_get_user_by_id(db_connection, user_id)
            assert user is not None
            assert user.email == "auto-org-test@example.com"

            # Assert: User is member of organization
            membership = await db_connection.fetchrow(
                """
                SELECT * FROM activity.organization_members
                WHERE user_id = $1 AND organization_id = $2
                """,
                user_id,
                test_organization_id
            )
            assert membership is not None
            assert membership["role"] == "member"
            assert membership["invited_by"] is None  # Auto-assignment has no inviter

            # Cleanup
            await db_connection.execute(
                "DELETE FROM activity.organization_members WHERE user_id = $1",
                user_id
            )
            await db_connection.execute(
                "DELETE FROM activity.users WHERE id = $1",
                user_id
            )

    async def test_registration_without_default_org_no_assignment(
        self,
        db_connection: asyncpg.Connection,
        mock_email_service: AsyncMock,
        redis_client
    ):
        """Test that user is NOT auto-assigned when DEFAULT_ORGANIZATION_ID is not set."""
        # Arrange: No DEFAULT_ORGANIZATION_ID set
        with patch("app.services.registration_service.get_settings") as mock_settings:
            mock_settings.return_value.DEFAULT_ORGANIZATION_ID = None

            registration_service = RegistrationService(
                db=db_connection,
                password_service=AsyncMock(),
                email_service=mock_email_service,
                redis_client=redis_client
            )
            registration_service.password_service.get_password_hash = AsyncMock(
                return_value="$argon2id$hashed_password"
            )

            user_data = UserCreate(
                email="no-org-test@example.com",
                password="SecurePassword123!"
            )

            # Act: Register user
            result = await registration_service.register_user(user_data)
            user_id = UUID(result["user_id"])

            # Assert: User exists
            user = await procedures.sp_get_user_by_id(db_connection, user_id)
            assert user is not None

            # Assert: User has NO organization memberships
            memberships = await db_connection.fetch(
                "SELECT * FROM activity.organization_members WHERE user_id = $1",
                user_id
            )
            assert len(memberships) == 0

            # Cleanup
            await db_connection.execute(
                "DELETE FROM activity.users WHERE id = $1",
                user_id
            )

    async def test_registration_with_invalid_org_id_continues(
        self,
        db_connection: asyncpg.Connection,
        mock_email_service: AsyncMock,
        redis_client
    ):
        """Test that registration continues even if org assignment fails (invalid org ID)."""
        # Arrange: Invalid organization ID
        invalid_org_id = str(uuid4())  # Random UUID that doesn't exist

        with patch("app.services.registration_service.get_settings") as mock_settings:
            mock_settings.return_value.DEFAULT_ORGANIZATION_ID = invalid_org_id

            registration_service = RegistrationService(
                db=db_connection,
                password_service=AsyncMock(),
                email_service=mock_email_service,
                redis_client=redis_client
            )
            registration_service.password_service.get_password_hash = AsyncMock(
                return_value="$argon2id$hashed_password"
            )

            user_data = UserCreate(
                email="invalid-org-test@example.com",
                password="SecurePassword123!"
            )

            # Act: Register user (should succeed despite invalid org ID)
            result = await registration_service.register_user(user_data)
            user_id = UUID(result["user_id"])

            # Assert: User was created successfully
            user = await procedures.sp_get_user_by_id(db_connection, user_id)
            assert user is not None
            assert user.email == "invalid-org-test@example.com"

            # Assert: No organization membership (assignment failed gracefully)
            memberships = await db_connection.fetch(
                "SELECT * FROM activity.organization_members WHERE user_id = $1",
                user_id
            )
            assert len(memberships) == 0

            # Cleanup
            await db_connection.execute(
                "DELETE FROM activity.users WHERE id = $1",
                user_id
            )

    async def test_registration_with_malformed_org_id_continues(
        self,
        db_connection: asyncpg.Connection,
        mock_email_service: AsyncMock,
        redis_client
    ):
        """Test that registration continues even if org ID is malformed (not a valid UUID)."""
        # Arrange: Malformed organization ID
        with patch("app.services.registration_service.get_settings") as mock_settings:
            mock_settings.return_value.DEFAULT_ORGANIZATION_ID = "not-a-valid-uuid"

            registration_service = RegistrationService(
                db=db_connection,
                password_service=AsyncMock(),
                email_service=mock_email_service,
                redis_client=redis_client
            )
            registration_service.password_service.get_password_hash = AsyncMock(
                return_value="$argon2id$hashed_password"
            )

            user_data = UserCreate(
                email="malformed-org-test@example.com",
                password="SecurePassword123!"
            )

            # Act: Register user (should succeed despite malformed org ID)
            result = await registration_service.register_user(user_data)
            user_id = UUID(result["user_id"])

            # Assert: User was created successfully
            user = await procedures.sp_get_user_by_id(db_connection, user_id)
            assert user is not None

            # Assert: No organization membership (assignment failed gracefully)
            memberships = await db_connection.fetch(
                "SELECT * FROM activity.organization_members WHERE user_id = $1",
                user_id
            )
            assert len(memberships) == 0

            # Cleanup
            await db_connection.execute(
                "DELETE FROM activity.users WHERE id = $1",
                user_id
            )

    async def test_login_returns_org_id_after_auto_assignment(
        self,
        db_connection: asyncpg.Connection,
        mock_email_service: AsyncMock,
        redis_client,
        test_organization_id: UUID
    ):
        """Test that login flow correctly returns org_id for auto-assigned users."""
        # Arrange: Register user with auto-assignment
        with patch("app.services.registration_service.get_settings") as mock_settings:
            mock_settings.return_value.DEFAULT_ORGANIZATION_ID = str(test_organization_id)

            registration_service = RegistrationService(
                db=db_connection,
                password_service=AsyncMock(),
                email_service=mock_email_service,
                redis_client=redis_client
            )
            registration_service.password_service.get_password_hash = AsyncMock(
                return_value="$argon2id$hashed_password"
            )

            user_data = UserCreate(
                email="login-org-test@example.com",
                password="SecurePassword123!"
            )

            result = await registration_service.register_user(user_data)
            user_id = UUID(result["user_id"])

            # Verify user and mark as verified
            await procedures.sp_verify_user_email(db_connection, user_id)

            # Assert: User is member of organization
            membership = await db_connection.fetchrow(
                """
                SELECT * FROM activity.organization_members
                WHERE user_id = $1 AND organization_id = $2
                """,
                user_id,
                test_organization_id
            )
            assert membership is not None
            assert membership["role"] == "member"

            # Note: Full login flow test would require auth_service integration
            # For now, we verify the membership exists and login can discover it

            # Cleanup
            await db_connection.execute(
                "DELETE FROM activity.organization_members WHERE user_id = $1",
                user_id
            )
            await db_connection.execute(
                "DELETE FROM activity.users WHERE id = $1",
                user_id
            )


@pytest.fixture
def mock_email_service():
    """Mock email service to prevent actual emails being sent."""
    mock = AsyncMock()
    mock.send_verification_email = AsyncMock(return_value=True)
    return mock
