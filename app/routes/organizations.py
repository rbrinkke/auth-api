"""
Organization API Routes

RESTful endpoints for organization management and membership.

Architecture:
- Thin routing layer (validation + service delegation)
- Authentication via JWT dependencies
- Authorization checks in service layer
- Structured logging for all operations
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status

from app.services.organization_service import OrganizationService
from app.core.dependencies import get_current_user_id, get_auth_context, AuthContext
from app.models.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationMembershipResponse,
    OrganizationMemberAdd,
    OrganizationMemberUpdate,
    OrganizationMemberResponse,
)
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


# ============================================================================
# ORGANIZATION CRUD
# ============================================================================

@router.post(
    "/organizations",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Organization",
    description="Create a new organization. Creator becomes owner automatically."
)
async def create_organization(
    org_data: OrganizationCreate,
    user_id: UUID = Depends(get_current_user_id),
    org_service: OrganizationService = Depends(OrganizationService)
) -> OrganizationResponse:
    """
    Create a new organization.

    - **name**: Organization name (1-255 chars)
    - **slug**: URL-friendly identifier (2-50 chars, lowercase, hyphens)
    - **description**: Optional description (max 1000 chars)

    Creator automatically becomes owner of the organization.
    """
    logger.info("route_create_organization",
               user_id=str(user_id),
               slug=org_data.slug)

    result = await org_service.create_organization(org_data, user_id)

    logger.info("route_organization_created",
               user_id=str(user_id),
               org_id=str(result.id))

    return result


@router.get(
    "/organizations",
    response_model=List[OrganizationMembershipResponse],
    summary="List User's Organizations",
    description="Get all organizations the current user is a member of."
)
async def list_user_organizations(
    user_id: UUID = Depends(get_current_user_id),
    org_service: OrganizationService = Depends(OrganizationService)
) -> List[OrganizationMembershipResponse]:
    """
    List all organizations user is member of.

    Returns organization details along with user's role and membership info.
    """
    logger.debug("route_list_user_organizations", user_id=str(user_id))

    result = await org_service.get_user_organizations(user_id)

    logger.info("route_organizations_listed",
               user_id=str(user_id),
               org_count=len(result))

    return result


@router.get(
    "/organizations/{org_id}",
    response_model=OrganizationResponse,
    summary="Get Organization",
    description="Get organization details by ID. Requires membership."
)
async def get_organization(
    org_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    org_service: OrganizationService = Depends(OrganizationService)
) -> OrganizationResponse:
    """
    Get organization details.

    Requires user to be a member of the organization.
    """
    logger.debug("route_get_organization",
                org_id=str(org_id),
                user_id=str(user_id))

    result = await org_service.get_organization(org_id, user_id)

    logger.info("route_organization_retrieved",
               org_id=str(org_id),
               user_id=str(user_id))

    return result


# ============================================================================
# MEMBERSHIP MANAGEMENT
# ============================================================================

@router.get(
    "/organizations/{org_id}/members",
    response_model=List[OrganizationMemberResponse],
    summary="List Organization Members",
    description="Get list of organization members with roles."
)
async def list_organization_members(
    org_id: UUID,
    limit: int = 100,
    offset: int = 0,
    user_id: UUID = Depends(get_current_user_id),
    org_service: OrganizationService = Depends(OrganizationService)
) -> List[OrganizationMemberResponse]:
    """
    List organization members.

    - **limit**: Max results per page (default 100, max 1000)
    - **offset**: Pagination offset (default 0)

    Requires user to be a member of the organization.
    """
    logger.debug("route_list_organization_members",
                org_id=str(org_id),
                user_id=str(user_id),
                limit=limit,
                offset=offset)

    # Enforce max limit
    limit = min(limit, 1000)

    result = await org_service.get_members(org_id, user_id, limit, offset)

    logger.info("route_members_listed",
               org_id=str(org_id),
               user_id=str(user_id),
               member_count=len(result))

    return result


@router.post(
    "/organizations/{org_id}/members",
    response_model=OrganizationMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Organization Member",
    description="Add a user to the organization. Requires admin or owner role."
)
async def add_organization_member(
    org_id: UUID,
    member_data: OrganizationMemberAdd,
    user_id: UUID = Depends(get_current_user_id),
    org_service: OrganizationService = Depends(OrganizationService)
) -> OrganizationMemberResponse:
    """
    Add member to organization.

    - **user_id**: User ID to add
    - **role**: Member role (owner, admin, or member)

    Only owners and admins can add members.
    """
    logger.info("route_add_organization_member",
               org_id=str(org_id),
               inviter_id=str(user_id),
               new_member_id=str(member_data.user_id))

    result = await org_service.add_member(org_id, member_data, user_id)

    logger.info("route_member_added",
               org_id=str(org_id),
               member_id=str(member_data.user_id))

    return result


@router.delete(
    "/organizations/{org_id}/members/{member_user_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove Organization Member",
    description="Remove a user from the organization. Requires admin or owner role."
)
async def remove_organization_member(
    org_id: UUID,
    member_user_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    org_service: OrganizationService = Depends(OrganizationService)
) -> dict:
    """
    Remove member from organization.

    Only owners and admins can remove members.
    Cannot remove the last owner.
    """
    logger.info("route_remove_organization_member",
               org_id=str(org_id),
               remover_id=str(user_id),
               member_id=str(member_user_id))

    result = await org_service.remove_member(org_id, member_user_id, user_id)

    logger.info("route_member_removed",
               org_id=str(org_id),
               member_id=str(member_user_id))

    return result


@router.patch(
    "/organizations/{org_id}/members/{member_user_id}/role",
    status_code=status.HTTP_200_OK,
    summary="Update Member Role",
    description="Change a member's role in the organization. Requires owner role."
)
async def update_member_role(
    org_id: UUID,
    member_user_id: UUID,
    role_data: OrganizationMemberUpdate,
    user_id: UUID = Depends(get_current_user_id),
    org_service: OrganizationService = Depends(OrganizationService)
) -> dict:
    """
    Update member's role.

    - **role**: New role (owner, admin, or member)

    Only owners can change member roles.
    """
    logger.info("route_update_member_role",
               org_id=str(org_id),
               updater_id=str(user_id),
               member_id=str(member_user_id),
               new_role=role_data.role)

    result = await org_service.update_member_role(
        org_id,
        member_user_id,
        role_data,
        user_id
    )

    logger.info("route_member_role_updated",
               org_id=str(org_id),
               member_id=str(member_user_id),
               new_role=role_data.role)

    return result
