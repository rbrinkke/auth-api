"""
Group Service - Business Logic for Groups & Permissions

Sprint 2: RBAC Implementation

Responsibilities:
- Group CRUD within organizations
- Group membership management
- Permission grants to groups
- Authorization enforcement (role-based for group management)

Security Model:
- Only owners/admins can create groups
- Only owners/admins can manage group membership
- Only owners can grant/revoke permissions
- All members can view groups and permissions
"""

from typing import List, Optional
from uuid import UUID
import asyncpg

from app.db.connection import get_db_connection
from app.models.group import (
    GroupCreate,
    GroupUpdate,
    GroupResponse,
    GroupMemberAdd,
    GroupMemberResponse,
    GroupPermissionGrant,
    GroupPermissionResponse,
    PermissionCreate,
    PermissionResponse,
    sp_create_group,
    sp_get_group_by_id,
    sp_list_organization_groups,
    sp_update_group,
    sp_delete_group,
    sp_add_user_to_group,
    sp_remove_user_from_group,
    sp_list_group_members,
    sp_list_user_groups,
    sp_grant_permission_to_group,
    sp_revoke_permission_from_group,
    sp_list_group_permissions,
    sp_create_permission,
    sp_get_permission_by_id,
    sp_get_permission_by_resource_action,
    sp_list_permissions,
)
from app.core.metrics import (
    track_group_operation,
    track_permission_operation,
    track_permission_grant,
    track_permission_revocation,
)
from app.models.organization import (
    sp_is_organization_member,
    sp_get_user_org_role,
)
from app.core.exceptions import (
    GroupNotFoundError,
    DuplicateGroupNameError,
    NotGroupMemberError,
    GroupMemberAlreadyExistsError,
    PermissionNotFoundError,
    DuplicatePermissionError,
    GroupPermissionAlreadyGrantedError,
    GroupPermissionNotGrantedError,
    InsufficientPermissionError,
    UserNotOrganizationMemberError,
    InsufficientOrganizationPermissionError,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class GroupService:
    """
    Service for group and permission management.

    Follows Sprint 1 pattern: thin service layer over stored procedures with custom exceptions.
    """

    def __init__(self, db: asyncpg.Connection):
        self.db = db

    # ========================================================================
    # GROUP CRUD
    # ========================================================================

    async def create_group(
        self,
        org_id: UUID,
        group_data: GroupCreate,
        creator_user_id: UUID
    ) -> GroupResponse:
        """
        Create a new group in organization.

        Security: Requires admin or owner role.

        Args:
            org_id: Organization ID
            group_data: Group creation data
            creator_user_id: User creating the group

        Returns:
            GroupResponse with created group

        Raises:
            InsufficientOrganizationPermissionError: If not admin/owner
            DuplicateGroupNameError: If group name already exists
        """
        logger.info("group_create_start",
                   org_id=str(org_id),
                   name=group_data.name,
                   creator_user_id=str(creator_user_id))

        # Check creator has permission (must be admin or owner)
        creator_role = await sp_get_user_org_role(self.db, creator_user_id, org_id)
        if creator_role not in ['owner', 'admin']:
            logger.warning("group_create_forbidden",
                          org_id=str(org_id),
                          creator_user_id=str(creator_user_id),
                          creator_role=creator_role)
            raise InsufficientOrganizationPermissionError(
                "Only owners and admins can create groups"
            )

        try:
            group_id = await sp_create_group(
                self.db,
                org_id=org_id,
                name=group_data.name,
                description=group_data.description,
                creator_user_id=creator_user_id
            )

            logger.info("group_created",
                       group_id=str(group_id),
                       org_id=str(org_id),
                       name=group_data.name)

            # Track successful group creation
            track_group_operation("create", "success")

            # Fetch full group details
            group_record = await sp_get_group_by_id(self.db, group_id)

            return GroupResponse(
                id=group_record.id,
                organization_id=group_record.organization_id,
                name=group_record.name,
                description=group_record.description,
                member_count=0,  # Newly created
                created_by=group_record.created_by,
                created_at=group_record.created_at,
                updated_at=group_record.updated_at
            )

        except asyncpg.UniqueViolationError:
            logger.warning("group_create_failed_duplicate_name",
                          org_id=str(org_id),
                          name=group_data.name)
            track_group_operation("create", "failed")
            raise DuplicateGroupNameError(group_data.name)

    async def get_organization_groups(
        self,
        org_id: UUID,
        user_id: Optional[UUID]
    ) -> List[GroupResponse]:
        """
        Get all groups in organization.

        Security: Requires organization membership (or service token with proper scope).

        Args:
            org_id: Organization ID
            user_id: Requesting user ID (for auth check), None for service tokens

        Returns:
            List of GroupResponse

        Raises:
            UserNotOrganizationMemberError: If not member (user tokens only)
        """
        logger.debug("get_organization_groups",
                    org_id=str(org_id),
                    user_id=str(user_id) if user_id else "service_token")

        # Service tokens (user_id=None) bypass membership check - scope validated in route
        if user_id is not None:
            # Check membership for user tokens
            is_member = await sp_is_organization_member(self.db, user_id, org_id)
            if not is_member:
                logger.warning("get_groups_forbidden",
                              org_id=str(org_id),
                              user_id=str(user_id))
                raise UserNotOrganizationMemberError()

        group_records = await sp_list_organization_groups(self.db, org_id)

        return [
            GroupResponse(
                id=record.id,
                organization_id=record.organization_id,
                name=record.name,
                description=record.description,
                member_count=record.member_count,
                created_by=record.created_by,
                created_at=record.created_at,
                updated_at=record.updated_at
            )
            for record in group_records
        ]

    async def get_group(
        self,
        group_id: UUID,
        user_id: Optional[UUID]
    ) -> GroupResponse:
        """
        Get group by ID.

        Security: Requires membership in group's organization (or service token with proper scope).

        Args:
            group_id: Group ID
            user_id: Requesting user ID (for auth check), None for service tokens

        Returns:
            GroupResponse

        Raises:
            GroupNotFoundError: If group doesn't exist
            UserNotOrganizationMemberError: If not member (user tokens only)
        """
        logger.debug("get_group",
                    group_id=str(group_id),
                    user_id=str(user_id) if user_id else "service_token")

        group_record = await sp_get_group_by_id(self.db, group_id)
        if not group_record:
            raise GroupNotFoundError()

        # Service tokens (user_id=None) bypass membership check - scope validated in route
        if user_id is not None:
            # Check membership in group's organization for user tokens
            is_member = await sp_is_organization_member(
                self.db,
                user_id,
                group_record.organization_id
            )
            if not is_member:
                logger.warning("get_group_forbidden",
                              group_id=str(group_id),
                              user_id=str(user_id))
                raise UserNotOrganizationMemberError()

        return GroupResponse(
            id=group_record.id,
            organization_id=group_record.organization_id,
            name=group_record.name,
            description=group_record.description,
            member_count=group_record.member_count,
            created_by=group_record.created_by,
            created_at=group_record.created_at,
            updated_at=group_record.updated_at
        )

    async def update_group(
        self,
        group_id: UUID,
        group_data: GroupUpdate,
        updater_user_id: UUID
    ) -> GroupResponse:
        """
        Update group details.

        Security: Requires admin or owner role in group's organization.

        Args:
            group_id: Group ID
            group_data: Update data
            updater_user_id: User updating the group

        Returns:
            Updated GroupResponse

        Raises:
            GroupNotFoundError: If group doesn't exist
            InsufficientOrganizationPermissionError: If not admin/owner
            DuplicateGroupNameError: If new name already exists
        """
        logger.info("group_update_start",
                   group_id=str(group_id),
                   updater_user_id=str(updater_user_id))

        # Get group
        group_record = await sp_get_group_by_id(self.db, group_id)
        if not group_record:
            raise GroupNotFoundError()

        # Check updater has permission
        updater_role = await sp_get_user_org_role(
            self.db,
            updater_user_id,
            group_record.organization_id
        )
        if updater_role not in ['owner', 'admin']:
            logger.warning("group_update_forbidden",
                          group_id=str(group_id),
                          updater_user_id=str(updater_user_id),
                          updater_role=updater_role)
            raise InsufficientOrganizationPermissionError(
                "Only owners and admins can update groups"
            )

        try:
            success = await sp_update_group(
                self.db,
                group_id=group_id,
                name=group_data.name,
                description=group_data.description
            )

            if not success:
                raise GroupNotFoundError()

            logger.info("group_updated", group_id=str(group_id))

            # Track successful group update
            track_group_operation("update", "success")

            # Fetch updated group
            updated_record = await sp_get_group_by_id(self.db, group_id)

            return GroupResponse(
                id=updated_record.id,
                organization_id=updated_record.organization_id,
                name=updated_record.name,
                description=updated_record.description,
                member_count=updated_record.member_count,
                created_by=updated_record.created_by,
                created_at=updated_record.created_at,
                updated_at=updated_record.updated_at
            )

        except asyncpg.UniqueViolationError:
            logger.warning("group_update_failed_duplicate_name",
                          group_id=str(group_id),
                          name=group_data.name)
            track_group_operation("update", "failed")
            raise DuplicateGroupNameError(group_data.name)

    async def delete_group(
        self,
        group_id: UUID,
        deleter_user_id: UUID
    ) -> None:
        """
        Delete group.

        Security: Requires owner role in group's organization.

        Args:
            group_id: Group ID
            deleter_user_id: User deleting the group

        Raises:
            GroupNotFoundError: If group doesn't exist
            InsufficientOrganizationPermissionError: If not owner
        """
        logger.info("group_delete_start",
                   group_id=str(group_id),
                   deleter_user_id=str(deleter_user_id))

        # Get group
        group_record = await sp_get_group_by_id(self.db, group_id)
        if not group_record:
            raise GroupNotFoundError()

        # Check deleter has permission (owner only for deletion)
        deleter_role = await sp_get_user_org_role(
            self.db,
            deleter_user_id,
            group_record.organization_id
        )
        if deleter_role != 'owner':
            logger.warning("group_delete_forbidden",
                          group_id=str(group_id),
                          deleter_user_id=str(deleter_user_id),
                          deleter_role=deleter_role)
            raise InsufficientOrganizationPermissionError(
                "Only owners can delete groups"
            )

        success = await sp_delete_group(self.db, group_id, deleter_user_id)
        if not success:
            track_group_operation("delete", "failed")
            raise GroupNotFoundError()

        logger.info("group_deleted",
                   group_id=str(group_id),
                   deleter_user_id=str(deleter_user_id))

        # Track successful group deletion
        track_group_operation("delete", "success")

    # ========================================================================
    # GROUP MEMBERSHIP
    # ========================================================================

    async def add_member_to_group(
        self,
        group_id: UUID,
        member_data: GroupMemberAdd,
        adder_user_id: UUID
    ) -> GroupMemberResponse:
        """
        Add user to group.

        Security: Requires admin or owner role in group's organization.

        Args:
            group_id: Group ID
            member_data: Member data (user_id)
            adder_user_id: User adding the member

        Returns:
            GroupMemberResponse

        Raises:
            GroupNotFoundError: If group doesn't exist
            UserNotOrganizationMemberError: If user being added is not org member
            InsufficientOrganizationPermissionError: If not admin/owner
            GroupMemberAlreadyExistsError: If already a member
        """
        logger.info("group_add_member_start",
                   group_id=str(group_id),
                   user_id=str(member_data.user_id),
                   adder_user_id=str(adder_user_id))

        # Get group
        group_record = await sp_get_group_by_id(self.db, group_id)
        if not group_record:
            raise GroupNotFoundError()

        # Check adder has permission
        adder_role = await sp_get_user_org_role(
            self.db,
            adder_user_id,
            group_record.organization_id
        )
        if adder_role not in ['owner', 'admin']:
            logger.warning("group_add_member_forbidden",
                          group_id=str(group_id),
                          adder_user_id=str(adder_user_id),
                          adder_role=adder_role)
            raise InsufficientOrganizationPermissionError(
                "Only owners and admins can manage group members"
            )

        # Check user being added is org member
        is_member = await sp_is_organization_member(
            self.db,
            member_data.user_id,
            group_record.organization_id
        )
        if not is_member:
            logger.warning("group_add_member_not_org_member",
                          group_id=str(group_id),
                          user_id=str(member_data.user_id))
            raise UserNotOrganizationMemberError(
                "User must be an organization member to join a group"
            )

        try:
            success = await sp_add_user_to_group(
                self.db,
                user_id=member_data.user_id,
                group_id=group_id,
                adder_user_id=adder_user_id
            )

            if not success:
                # Already a member (ON CONFLICT DO NOTHING in stored procedure)
                track_group_operation("add_member", "failed")
                raise GroupMemberAlreadyExistsError()

            logger.info("group_member_added",
                       group_id=str(group_id),
                       user_id=str(member_data.user_id))

            # Track successful member addition
            track_group_operation("add_member", "success")

            # Fetch member details
            members = await sp_list_group_members(self.db, group_id)
            added_member = next(
                (m for m in members if m.user_id == member_data.user_id),
                None
            )

            if not added_member:
                # Fallback if fetch fails
                from datetime import datetime
                return GroupMemberResponse(
                    user_id=member_data.user_id,
                    email="",  # Unknown
                    added_at=datetime.utcnow(),
                    added_by=adder_user_id
                )

            return GroupMemberResponse(
                user_id=added_member.user_id,
                email=added_member.email,
                added_at=added_member.added_at,
                added_by=added_member.added_by
            )

        except asyncpg.ForeignKeyViolationError:
            track_group_operation("add_member", "failed")
            raise GroupMemberAlreadyExistsError()

    async def remove_member_from_group(
        self,
        group_id: UUID,
        user_id: UUID,
        remover_user_id: UUID
    ) -> None:
        """
        Remove user from group.

        Security: Requires admin or owner role in group's organization.

        Args:
            group_id: Group ID
            user_id: User to remove
            remover_user_id: User removing the member

        Raises:
            GroupNotFoundError: If group doesn't exist
            NotGroupMemberError: If user not in group
            InsufficientOrganizationPermissionError: If not admin/owner
        """
        logger.info("group_remove_member_start",
                   group_id=str(group_id),
                   user_id=str(user_id),
                   remover_user_id=str(remover_user_id))

        # Get group
        group_record = await sp_get_group_by_id(self.db, group_id)
        if not group_record:
            raise GroupNotFoundError()

        # Check remover has permission
        remover_role = await sp_get_user_org_role(
            self.db,
            remover_user_id,
            group_record.organization_id
        )
        if remover_role not in ['owner', 'admin']:
            logger.warning("group_remove_member_forbidden",
                          group_id=str(group_id),
                          remover_user_id=str(remover_user_id),
                          remover_role=remover_role)
            raise InsufficientOrganizationPermissionError(
                "Only owners and admins can manage group members"
            )

        success = await sp_remove_user_from_group(
            self.db,
            user_id=user_id,
            group_id=group_id,
            remover_user_id=remover_user_id
        )

        if not success:
            track_group_operation("remove_member", "failed")
            raise NotGroupMemberError()

        logger.info("group_member_removed",
                   group_id=str(group_id),
                   user_id=str(user_id))

        # Track successful member removal
        track_group_operation("remove_member", "success")

    async def get_group_members(
        self,
        group_id: UUID,
        user_id: Optional[UUID]
    ) -> List[GroupMemberResponse]:
        """
        Get members of a group.

        Security: Requires membership in group's organization (or service token with proper scope).

        Args:
            group_id: Group ID
            user_id: Requesting user ID (for auth check), None for service tokens

        Returns:
            List of GroupMemberResponse

        Raises:
            GroupNotFoundError: If group doesn't exist
            UserNotOrganizationMemberError: If not org member (user tokens only)
        """
        logger.debug("get_group_members",
                    group_id=str(group_id),
                    user_id=str(user_id) if user_id else "service_token")

        # Get group
        group_record = await sp_get_group_by_id(self.db, group_id)
        if not group_record:
            raise GroupNotFoundError()

        # Service tokens (user_id=None) bypass membership check - scope validated in route
        if user_id is not None:
            # Check membership for user tokens
            is_member = await sp_is_organization_member(
                self.db,
                user_id,
                group_record.organization_id
            )
            if not is_member:
                raise UserNotOrganizationMemberError()

        member_records = await sp_list_group_members(self.db, group_id)

        return [
            GroupMemberResponse(
                user_id=record.user_id,
                email=record.email,
                added_at=record.added_at,
                added_by=record.added_by
            )
            for record in member_records
        ]

    # ========================================================================
    # GROUP PERMISSIONS
    # ========================================================================

    async def grant_permission(
        self,
        group_id: UUID,
        permission_data: GroupPermissionGrant,
        granter_user_id: UUID
    ) -> GroupPermissionResponse:
        """
        Grant permission to group.

        Security: Requires owner role (most sensitive operation).

        Args:
            group_id: Group ID
            permission_data: Permission grant data
            granter_user_id: User granting permission

        Returns:
            GroupPermissionResponse

        Raises:
            GroupNotFoundError: If group doesn't exist
            PermissionNotFoundError: If permission doesn't exist
            InsufficientOrganizationPermissionError: If not owner
            GroupPermissionAlreadyGrantedError: If already granted
        """
        logger.info("group_grant_permission_start",
                   group_id=str(group_id),
                   permission_id=str(permission_data.permission_id),
                   granter_user_id=str(granter_user_id))

        # Get group
        group_record = await sp_get_group_by_id(self.db, group_id)
        if not group_record:
            raise GroupNotFoundError()

        # Check granter has permission (owner only for security)
        granter_role = await sp_get_user_org_role(
            self.db,
            granter_user_id,
            group_record.organization_id
        )
        if granter_role != 'owner':
            logger.warning("group_grant_permission_forbidden",
                          group_id=str(group_id),
                          granter_user_id=str(granter_user_id),
                          granter_role=granter_role)
            raise InsufficientOrganizationPermissionError(
                "Only owners can grant permissions to groups"
            )

        # Check permission exists
        permission = await sp_get_permission_by_id(
            self.db,
            permission_data.permission_id
        )
        if not permission:
            raise PermissionNotFoundError()

        try:
            success = await sp_grant_permission_to_group(
                self.db,
                group_id=group_id,
                permission_id=permission_data.permission_id,
                granter_user_id=granter_user_id
            )

            if not success:
                # Already granted (ON CONFLICT DO NOTHING)
                track_permission_operation("grant", "failed")
                raise GroupPermissionAlreadyGrantedError()

            logger.info("group_permission_granted",
                       group_id=str(group_id),
                       permission=f"{permission.resource}:{permission.action}")

            # Track successful permission grant (operation + grant by type)
            track_permission_operation("grant", "success")
            track_permission_grant(permission.resource, permission.action)

            # Fetch granted permission details
            permissions = await sp_list_group_permissions(self.db, group_id)
            granted_perm = next(
                (p for p in permissions if p.permission_id == permission_data.permission_id),
                None
            )

            if not granted_perm:
                # Fallback
                from datetime import datetime
                return GroupPermissionResponse(
                    permission_id=permission.id,
                    resource=permission.resource,
                    action=permission.action,
                    permission_string=permission.permission_string,
                    description=permission.description,
                    granted_at=datetime.utcnow(),
                    granted_by=granter_user_id
                )

            return GroupPermissionResponse(
                permission_id=granted_perm.permission_id,
                resource=granted_perm.resource,
                action=granted_perm.action,
                permission_string=granted_perm.permission_string,
                description=granted_perm.description,
                granted_at=granted_perm.granted_at,
                granted_by=granted_perm.granted_by
            )

        except asyncpg.ForeignKeyViolationError:
            raise GroupPermissionAlreadyGrantedError()

    async def revoke_permission(
        self,
        group_id: UUID,
        permission_id: UUID,
        revoker_user_id: UUID
    ) -> None:
        """
        Revoke permission from group.

        Security: Requires owner role.

        Args:
            group_id: Group ID
            permission_id: Permission ID to revoke
            revoker_user_id: User revoking permission

        Raises:
            GroupNotFoundError: If group doesn't exist
            GroupPermissionNotGrantedError: If permission not granted
            InsufficientOrganizationPermissionError: If not owner
        """
        logger.info("group_revoke_permission_start",
                   group_id=str(group_id),
                   permission_id=str(permission_id),
                   revoker_user_id=str(revoker_user_id))

        # Get group
        group_record = await sp_get_group_by_id(self.db, group_id)
        if not group_record:
            raise GroupNotFoundError()

        # Check revoker has permission (owner only)
        revoker_role = await sp_get_user_org_role(
            self.db,
            revoker_user_id,
            group_record.organization_id
        )
        if revoker_role != 'owner':
            logger.warning("group_revoke_permission_forbidden",
                          group_id=str(group_id),
                          revoker_user_id=str(revoker_user_id),
                          revoker_role=revoker_role)
            raise InsufficientOrganizationPermissionError(
                "Only owners can revoke permissions from groups"
            )

        # Get permission details for metrics (before revoking)
        permission = await sp_get_permission_by_id(self.db, permission_id)

        success = await sp_revoke_permission_from_group(
            self.db,
            group_id=group_id,
            permission_id=permission_id,
            revoker_user_id=revoker_user_id
        )

        if not success:
            track_permission_operation("revoke", "failed")
            raise GroupPermissionNotGrantedError()

        logger.info("group_permission_revoked",
                   group_id=str(group_id),
                   permission_id=str(permission_id))

        # Track successful permission revocation
        track_permission_operation("revoke", "success")
        if permission:
            track_permission_revocation(permission.resource, permission.action)

    async def get_group_permissions(
        self,
        group_id: UUID,
        user_id: Optional[UUID]
    ) -> List[GroupPermissionResponse]:
        """
        Get permissions granted to a group.

        Security: Requires membership in group's organization (or service token with proper scope).

        Args:
            group_id: Group ID
            user_id: Requesting user ID (for auth check), None for service tokens

        Returns:
            List of GroupPermissionResponse

        Raises:
            GroupNotFoundError: If group doesn't exist
            UserNotOrganizationMemberError: If not org member (user tokens only)
        """
        logger.debug("get_group_permissions",
                    group_id=str(group_id),
                    user_id=str(user_id) if user_id else "service_token")

        # Get group
        group_record = await sp_get_group_by_id(self.db, group_id)
        if not group_record:
            raise GroupNotFoundError()

        # Service tokens (user_id=None) bypass membership check - scope validated in route
        if user_id is not None:
            # Check membership for user tokens
            is_member = await sp_is_organization_member(
                self.db,
                user_id,
                group_record.organization_id
            )
            if not is_member:
                raise UserNotOrganizationMemberError()

        permission_records = await sp_list_group_permissions(self.db, group_id)

        return [
            GroupPermissionResponse(
                permission_id=record.permission_id,
                resource=record.resource,
                action=record.action,
                permission_string=record.permission_string,
                description=record.description,
                granted_at=record.granted_at,
                granted_by=record.granted_by
            )
            for record in permission_records
        ]

    # ========================================================================
    # PERMISSIONS MANAGEMENT
    # ========================================================================

    async def create_permission(
        self,
        permission_data: PermissionCreate,
        creator_user_id: UUID
    ) -> PermissionResponse:
        """
        Create a new permission (admin-only operation).

        Security: Requires superadmin (future enhancement).
        For now, any authenticated user can create system-wide permissions.

        Args:
            permission_data: Permission creation data
            creator_user_id: User creating permission

        Returns:
            PermissionResponse

        Raises:
            DuplicatePermissionError: If permission already exists
        """
        logger.info("permission_create_start",
                   resource=permission_data.resource,
                   action=permission_data.action,
                   creator_user_id=str(creator_user_id))

        try:
            permission_id = await sp_create_permission(
                self.db,
                resource=permission_data.resource,
                action=permission_data.action,
                description=permission_data.description
            )

            logger.info("permission_created",
                       permission_id=str(permission_id),
                       permission=f"{permission_data.resource}:{permission_data.action}")

            # Track successful permission creation
            track_permission_operation("create", "success")

            # Fetch full permission details
            permission = await sp_get_permission_by_id(self.db, permission_id)

            return PermissionResponse(
                id=permission.id,
                resource=permission.resource,
                action=permission.action,
                permission_string=permission.permission_string,
                description=permission.description,
                created_at=permission.created_at
            )

        except asyncpg.UniqueViolationError:
            logger.warning("permission_create_failed_duplicate",
                          resource=permission_data.resource,
                          action=permission_data.action)
            track_permission_operation("create", "failed")
            raise DuplicatePermissionError(
                f"{permission_data.resource}:{permission_data.action}"
            )

    async def list_permissions(self) -> List[PermissionResponse]:
        """
        List all available permissions.

        Security: Public (permissions are not sensitive information).

        Returns:
            List of PermissionResponse
        """
        logger.debug("list_permissions")

        permission_records = await sp_list_permissions(self.db)

        return [
            PermissionResponse(
                id=record.id,
                resource=record.resource,
                action=record.action,
                permission_string=record.permission_string,
                description=record.description,
                created_at=record.created_at
            )
            for record in permission_records
        ]


# ============================================================================
# Dependency Injection Helper
# ============================================================================

async def get_group_service(
    db: asyncpg.Connection = None
) -> GroupService:
    """
    Get GroupService instance with database connection.

    Usage in FastAPI routes:
        group_service: GroupService = Depends(get_group_service)
    """
    if db is None:
        db = await get_db_connection()
    return GroupService(db)
