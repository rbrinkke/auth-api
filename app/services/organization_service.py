"""
Organization Service - Business Logic Layer

Handles organization CRUD operations and membership management.
Thin layer over database procedures with:
- Input validation (via Pydantic)
- Authorization checks
- Error handling
- Structured logging
- Metrics tracking

Business logic stays in PostgreSQL stored procedures.
"""

from typing import List
from uuid import UUID
from fastapi import Depends
import asyncpg

from app.db.connection import get_db_connection
from app.models.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationMembershipResponse,
    OrganizationMemberAdd,
    OrganizationMemberUpdate,
    OrganizationMemberResponse,
    sp_create_organization,
    sp_get_user_organizations,
    sp_get_organization_by_id,
    sp_is_organization_member,
    sp_get_user_org_role,
    sp_check_org_permission,
    sp_add_organization_member,
    sp_remove_organization_member,
    sp_update_member_role,
    sp_get_organization_members,
)
from app.core.exceptions import (
    OrganizationNotFoundError,
    OrganizationSlugExistsError,
    UserNotOrganizationMemberError,
    InsufficientOrganizationPermissionError,
    OrganizationMemberAlreadyExistsError,
    LastOwnerRemovalError,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class OrganizationService:
    """
    Service for organization management operations.

    Responsibilities:
    - Create/read/update organizations
    - Manage organization members
    - Check membership and roles
    - Authorization enforcement
    """

    def __init__(
        self,
        db: asyncpg.Connection = Depends(get_db_connection)
    ):
        self.db = db

    # ========================================================================
    # ORGANIZATION CRUD
    # ========================================================================

    async def create_organization(
        self,
        org_data: OrganizationCreate,
        creator_user_id: UUID
    ) -> OrganizationResponse:
        """
        Create a new organization with creator as owner.

        Args:
            org_data: Organization creation data
            creator_user_id: User creating the organization (becomes owner)

        Returns:
            OrganizationResponse with created organization

        Raises:
            OrganizationSlugExistsError: If slug already exists
        """
        logger.info("organization_create_start",
                   slug=org_data.slug,
                   creator_user_id=str(creator_user_id))

        try:
            org_record = await sp_create_organization(
                self.db,
                name=org_data.name,
                slug=org_data.slug,
                description=org_data.description,
                creator_user_id=creator_user_id
            )

            logger.info("organization_created",
                       org_id=str(org_record.id),
                       slug=org_record.slug,
                       creator_user_id=str(creator_user_id))

            return OrganizationResponse(
                id=org_record.id,
                name=org_record.name,
                slug=org_record.slug,
                description=org_record.description,
                created_at=org_record.created_at,
                updated_at=org_record.updated_at,
                member_count=1  # Creator is first member
            )

        except asyncpg.UniqueViolationError:
            logger.warning("organization_create_failed_duplicate_slug",
                          slug=org_data.slug,
                          creator_user_id=str(creator_user_id))
            raise OrganizationSlugExistsError(slug=org_data.slug)

        except Exception as e:
            logger.error("organization_create_failed",
                        error=str(e),
                        slug=org_data.slug,
                        creator_user_id=str(creator_user_id),
                        exc_info=True)
            raise

    async def get_user_organizations(
        self,
        user_id: UUID
    ) -> List[OrganizationMembershipResponse]:
        """
        Get all organizations a user is member of.

        Args:
            user_id: User ID

        Returns:
            List of organizations with membership info
        """
        logger.debug("get_user_organizations", user_id=str(user_id))

        membership_records = await sp_get_user_organizations(self.db, user_id)

        logger.info("user_organizations_retrieved",
                   user_id=str(user_id),
                   org_count=len(membership_records))

        return [
            OrganizationMembershipResponse(
                id=record.id,
                name=record.name,
                slug=record.slug,
                description=record.description,
                role=record.role,
                member_count=record.member_count,
                joined_at=record.joined_at
            )
            for record in membership_records
        ]

    async def get_organization(
        self,
        org_id: UUID,
        user_id: UUID
    ) -> OrganizationResponse:
        """
        Get organization by ID.

        Args:
            org_id: Organization ID
            user_id: Requesting user ID (for auth check)

        Returns:
            OrganizationResponse

        Raises:
            OrganizationNotFoundError: If not found
            UserNotOrganizationMemberError: If not member
        """
        logger.debug("get_organization",
                    org_id=str(org_id),
                    user_id=str(user_id))

        # Check membership
        is_member = await sp_is_organization_member(self.db, user_id, org_id)
        if not is_member:
            logger.warning("get_organization_forbidden",
                          org_id=str(org_id),
                          user_id=str(user_id))
            raise UserNotOrganizationMemberError()

        # Get organization
        org_record = await sp_get_organization_by_id(self.db, org_id)
        if not org_record:
            logger.warning("get_organization_not_found",
                          org_id=str(org_id),
                          user_id=str(user_id))
            raise OrganizationNotFoundError()

        logger.info("organization_retrieved",
                   org_id=str(org_id),
                   user_id=str(user_id))

        return OrganizationResponse(
            id=org_record.id,
            name=org_record.name,
            slug=org_record.slug,
            description=org_record.description,
            created_at=org_record.created_at,
            updated_at=org_record.updated_at,
            member_count=org_record.member_count
        )

    # ========================================================================
    # MEMBERSHIP MANAGEMENT
    # ========================================================================

    async def add_member(
        self,
        org_id: UUID,
        member_data: OrganizationMemberAdd,
        inviter_user_id: UUID
    ) -> OrganizationMemberResponse:
        """
        Add a member to organization.

        Args:
            org_id: Organization ID
            member_data: Member data (user_id, role)
            inviter_user_id: User ID performing the invite

        Returns:
            OrganizationMemberResponse

        Raises:
            InsufficientOrganizationPermissionError: If inviter lacks permission
            OrganizationMemberAlreadyExistsError: If already member
        """
        logger.info("add_organization_member",
                   org_id=str(org_id),
                   new_member_id=str(member_data.user_id),
                   inviter_id=str(inviter_user_id))

        # Check inviter has permission (must be admin or owner)
        has_permission = await sp_check_org_permission(
            self.db,
            inviter_user_id,
            org_id,
            ['owner', 'admin']
        )

        if not has_permission:
            inviter_role = await sp_get_user_org_role(self.db, inviter_user_id, org_id)
            logger.warning("add_member_forbidden",
                          org_id=str(org_id),
                          inviter_id=str(inviter_user_id),
                          inviter_role=inviter_role)
            raise InsufficientOrganizationPermissionError(
                "Only owners and admins can add members"
            )

        # Add member
        member_record = await sp_add_organization_member(
            self.db,
            user_id=member_data.user_id,
            org_id=org_id,
            role=member_data.role,
            invited_by=inviter_user_id
        )

        if not member_record:
            logger.warning("add_member_already_exists",
                          org_id=str(org_id),
                          user_id=str(member_data.user_id))
            raise OrganizationMemberAlreadyExistsError()

        logger.info("member_added",
                   org_id=str(org_id),
                   user_id=str(member_data.user_id),
                   role=member_data.role)

        return OrganizationMemberResponse(
            user_id=member_record.user_id,
            email=member_record.email,
            role=member_record.role,
            joined_at=member_record.joined_at,
            invited_by_email=member_record.invited_by_email
        )

    async def remove_member(
        self,
        org_id: UUID,
        member_user_id: UUID,
        remover_user_id: UUID
    ) -> dict:
        """
        Remove a member from organization.

        Args:
            org_id: Organization ID
            member_user_id: User ID to remove
            remover_user_id: User ID performing the removal

        Returns:
            Success message

        Raises:
            InsufficientOrganizationPermissionError: If remover lacks permission
            OrganizationNotFoundError: If member not found
            LastOwnerRemovalError: If attempting to remove last owner
        """
        logger.info("remove_organization_member",
                   org_id=str(org_id),
                   member_id=str(member_user_id),
                   remover_id=str(remover_user_id))

        # Check remover has permission (must be admin or owner)
        has_permission = await sp_check_org_permission(
            self.db,
            remover_user_id,
            org_id,
            ['owner', 'admin']
        )

        if not has_permission:
            logger.warning("remove_member_forbidden",
                          org_id=str(org_id),
                          remover_id=str(remover_user_id))
            raise InsufficientOrganizationPermissionError(
                "Only owners and admins can remove members"
            )

        # Check if removing last owner
        member_role = await sp_get_user_org_role(self.db, member_user_id, org_id)
        if member_role == 'owner':
            # Count total owners
            members = await sp_get_organization_members(self.db, org_id, limit=1000)
            owner_count = sum(1 for m in members if m.role == 'owner')
            if owner_count <= 1:
                logger.warning("remove_member_last_owner",
                              org_id=str(org_id),
                              member_id=str(member_user_id))
                raise LastOwnerRemovalError()

        # Remove member
        removed = await sp_remove_organization_member(
            self.db,
            user_id=member_user_id,
            org_id=org_id
        )

        if not removed:
            logger.warning("remove_member_not_found",
                          org_id=str(org_id),
                          member_id=str(member_user_id))
            raise OrganizationNotFoundError("Member not found in organization")

        logger.info("member_removed",
                   org_id=str(org_id),
                   member_id=str(member_user_id))

        return {"message": "Member removed successfully"}

    async def update_member_role(
        self,
        org_id: UUID,
        member_user_id: UUID,
        role_data: OrganizationMemberUpdate,
        updater_user_id: UUID
    ) -> dict:
        """
        Update member's role in organization.

        Args:
            org_id: Organization ID
            member_user_id: User ID to update
            role_data: New role data
            updater_user_id: User ID performing the update

        Returns:
            Success message

        Raises:
            InsufficientOrganizationPermissionError: If updater lacks permission
            OrganizationNotFoundError: If member not found
        """
        logger.info("update_member_role",
                   org_id=str(org_id),
                   member_id=str(member_user_id),
                   new_role=role_data.role,
                   updater_id=str(updater_user_id))

        # Check updater has permission (must be owner for role changes)
        has_permission = await sp_check_org_permission(
            self.db,
            updater_user_id,
            org_id,
            ['owner']
        )

        if not has_permission:
            logger.warning("update_role_forbidden",
                          org_id=str(org_id),
                          updater_id=str(updater_user_id))
            raise InsufficientOrganizationPermissionError(
                "Only owners can change member roles"
            )

        # Update role
        updated = await sp_update_member_role(
            self.db,
            user_id=member_user_id,
            org_id=org_id,
            new_role=role_data.role
        )

        if not updated:
            logger.warning("update_role_not_found",
                          org_id=str(org_id),
                          member_id=str(member_user_id))
            raise OrganizationNotFoundError("Member not found in organization")

        logger.info("member_role_updated",
                   org_id=str(org_id),
                   member_id=str(member_user_id),
                   new_role=role_data.role)

        return {"message": "Member role updated successfully"}

    async def get_members(
        self,
        org_id: UUID,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[OrganizationMemberResponse]:
        """
        Get members of an organization.

        Args:
            org_id: Organization ID
            user_id: Requesting user ID (for auth check)
            limit: Max members to return
            offset: Pagination offset

        Returns:
            List of OrganizationMemberResponse

        Raises:
            UserNotOrganizationMemberError: If not member
        """
        logger.debug("get_organization_members",
                    org_id=str(org_id),
                    user_id=str(user_id),
                    limit=limit,
                    offset=offset)

        # Check membership
        is_member = await sp_is_organization_member(self.db, user_id, org_id)
        if not is_member:
            logger.warning("get_members_forbidden",
                          org_id=str(org_id),
                          user_id=str(user_id))
            raise UserNotOrganizationMemberError()

        # Get members
        member_records = await sp_get_organization_members(
            self.db,
            org_id=org_id,
            limit=limit,
            offset=offset
        )

        logger.info("organization_members_retrieved",
                   org_id=str(org_id),
                   user_id=str(user_id),
                   member_count=len(member_records))

        return [
            OrganizationMemberResponse(
                user_id=record.user_id,
                email=record.email,
                role=record.role,
                joined_at=record.joined_at,
                invited_by_email=record.invited_by_email
            )
            for record in member_records
        ]
