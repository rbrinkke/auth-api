"""
Organization Models and Database Procedures

This module provides Python interfaces to organization-related database operations.
All business logic resides in PostgreSQL stored procedures for:
- Data consistency
- Transaction safety
- Performance (DB-side joins)
- Single source of truth

Architecture:
- Thin Python layer (just types and DB calls)
- Thick database layer (stored procedures with business logic)
- Redis caching on top (added later in Sprint 2)
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
import asyncpg
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# PYDANTIC SCHEMAS (for API request/response)
# ============================================================================

class OrganizationCreate(BaseModel):
    """Request schema for creating an organization."""
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    slug: str = Field(
        ...,
        min_length=2,
        max_length=50,
        pattern="^[a-z0-9-]+$",
        description="URL-friendly identifier (lowercase, hyphens allowed)"
    )
    description: Optional[str] = Field(None, max_length=1000, description="Organization description")

    @field_validator('slug')
    @classmethod
    def slug_must_be_lowercase(cls, v: str) -> str:
        """Ensure slug is lowercase"""
        return v.lower()

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "name": "Acme Corporation",
                "slug": "acme-corp",
                "description": "Leading provider of innovative solutions"
            }]
        }
    }


class OrganizationUpdate(BaseModel):
    """Request schema for updating an organization."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class OrganizationResponse(BaseModel):
    """Response schema for organization data."""
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    member_count: Optional[int] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [{
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Acme Corporation",
                "slug": "acme-corp",
                "description": "Leading provider of innovative solutions",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "member_count": 5
            }]
        }
    }


class OrganizationMembershipResponse(BaseModel):
    """Response schema for user's organization membership."""
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    role: str  # owner, admin, member
    member_count: int
    joined_at: datetime

    model_config = {"from_attributes": True}


class OrganizationMemberAdd(BaseModel):
    """Request schema for adding a member to organization."""
    user_id: UUID = Field(..., description="User ID to add")
    role: str = Field("member", pattern="^(owner|admin|member)$", description="Member role")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "role": "member"
            }]
        }
    }


class OrganizationMemberUpdate(BaseModel):
    """Request schema for updating member role."""
    role: str = Field(..., pattern="^(owner|admin|member)$", description="New role")


class OrganizationMemberResponse(BaseModel):
    """Response schema for organization member data."""
    user_id: UUID
    email: str
    role: str
    joined_at: datetime
    invited_by_email: Optional[str] = None

    model_config = {"from_attributes": True}


# ============================================================================
# DATABASE RECORD WRAPPERS
# ============================================================================

class OrganizationRecord:
    """Wrapper for organization database record."""

    def __init__(self, record: asyncpg.Record):
        self.id: UUID = record["id"]
        self.name: str = record["name"]
        self.slug: str = record["slug"]
        self.description: Optional[str] = record.get("description")
        self.created_at: datetime = record["created_at"]
        self.updated_at: Optional[datetime] = record.get("updated_at")
        self.member_count: Optional[int] = record.get("member_count")


class OrganizationMembershipRecord:
    """Wrapper for organization membership record (user's orgs)."""

    def __init__(self, record: asyncpg.Record):
        self.id: UUID = record["id"]
        self.name: str = record["name"]
        self.slug: str = record["slug"]
        self.description: Optional[str] = record.get("description")
        self.role: str = record["role"]
        self.member_count: int = record["member_count"]
        self.joined_at: datetime = record["joined_at"]


class OrganizationMemberRecord:
    """Wrapper for organization member record."""

    def __init__(self, record: asyncpg.Record):
        self.user_id: UUID = record["user_id"]
        self.email: str = record["email"]
        self.role: str = record["role"]
        self.joined_at: datetime = record["joined_at"]
        self.invited_by_email: Optional[str] = record.get("invited_by_email")


# ============================================================================
# DATABASE PROCEDURES (Python -> PostgreSQL SP calls)
# ============================================================================

async def sp_create_organization(
    conn: asyncpg.Connection,
    name: str,
    slug: str,
    description: Optional[str],
    creator_user_id: UUID
) -> OrganizationRecord:
    """
    Create a new organization with creator as owner.

    Args:
        conn: Database connection
        name: Organization name
        slug: URL-friendly identifier
        description: Optional description
        creator_user_id: User ID who creates the org (becomes owner)

    Returns:
        OrganizationRecord with created organization data

    Raises:
        asyncpg.UniqueViolationError: If slug already exists
    """
    result = await conn.fetchrow(
        """
        SELECT * FROM activity.sp_create_organization($1, $2, $3, $4)
        """,
        name,
        slug,
        description,
        creator_user_id
    )

    if not result:
        raise RuntimeError("sp_create_organization returned no data")

    return OrganizationRecord(result)


async def sp_get_user_organizations(
    conn: asyncpg.Connection,
    user_id: UUID
) -> List[OrganizationMembershipRecord]:
    """
    Get all organizations a user is member of.

    Args:
        conn: Database connection
        user_id: User ID

    Returns:
        List of OrganizationMembershipRecord with role and membership info
    """
    results = await conn.fetch(
        """
        SELECT * FROM activity.sp_get_user_organizations($1)
        """,
        user_id
    )

    return [OrganizationMembershipRecord(r) for r in results]


async def sp_get_organization_by_id(
    conn: asyncpg.Connection,
    org_id: UUID
) -> Optional[OrganizationRecord]:
    """
    Get organization by ID.

    Args:
        conn: Database connection
        org_id: Organization ID

    Returns:
        OrganizationRecord or None if not found
    """
    result = await conn.fetchrow(
        """
        SELECT * FROM activity.sp_get_organization_by_id($1)
        """,
        org_id
    )

    return OrganizationRecord(result) if result else None


async def sp_is_organization_member(
    conn: asyncpg.Connection,
    user_id: UUID,
    org_id: UUID
) -> bool:
    """
    Check if user is member of organization.

    Args:
        conn: Database connection
        user_id: User ID
        org_id: Organization ID

    Returns:
        True if user is member, False otherwise
    """
    result = await conn.fetchval(
        """
        SELECT activity.sp_is_organization_member($1, $2)
        """,
        user_id,
        org_id
    )

    return bool(result)


async def sp_get_user_org_role(
    conn: asyncpg.Connection,
    user_id: UUID,
    org_id: UUID
) -> Optional[str]:
    """
    Get user's role in organization.

    Args:
        conn: Database connection
        user_id: User ID
        org_id: Organization ID

    Returns:
        Role string ('owner', 'admin', 'member') or None if not member
    """
    result = await conn.fetchval(
        """
        SELECT activity.sp_get_user_org_role($1, $2)
        """,
        user_id,
        org_id
    )

    return result


async def sp_check_org_permission(
    conn: asyncpg.Connection,
    user_id: UUID,
    org_id: UUID,
    required_roles: List[str]
) -> bool:
    """
    Check if user has required permission (role) in organization.

    Efficient single-query authorization check.

    Args:
        conn: Database connection
        user_id: User ID
        org_id: Organization ID
        required_roles: List of acceptable roles (e.g., ['owner', 'admin'])

    Returns:
        True if user has one of the required roles, False otherwise
    """
    result = await conn.fetchval(
        """
        SELECT activity.sp_check_org_permission($1, $2, $3)
        """,
        user_id,
        org_id,
        required_roles
    )

    return bool(result)


async def sp_add_organization_member(
    conn: asyncpg.Connection,
    user_id: UUID,
    org_id: UUID,
    role: str,
    invited_by: UUID
) -> Optional[OrganizationMemberRecord]:
    """
    Add member to organization.

    Args:
        conn: Database connection
        user_id: User ID to add
        org_id: Organization ID
        role: Member role ('owner', 'admin', 'member')
        invited_by: User ID who invited this member

    Returns:
        OrganizationMemberRecord or None if user already member
    """
    result = await conn.fetchrow(
        """
        SELECT * FROM activity.sp_add_organization_member($1, $2, $3, $4)
        """,
        user_id,
        org_id,
        role,
        invited_by
    )

    return OrganizationMemberRecord(result) if result else None


async def sp_remove_organization_member(
    conn: asyncpg.Connection,
    user_id: UUID,
    org_id: UUID
) -> bool:
    """
    Remove member from organization.

    Args:
        conn: Database connection
        user_id: User ID to remove
        org_id: Organization ID

    Returns:
        True if member was removed, False if not found
    """
    result = await conn.fetchval(
        """
        SELECT activity.sp_remove_organization_member($1, $2)
        """,
        user_id,
        org_id
    )

    return bool(result)


async def sp_update_member_role(
    conn: asyncpg.Connection,
    user_id: UUID,
    org_id: UUID,
    new_role: str
) -> bool:
    """
    Update member's role in organization.

    Args:
        conn: Database connection
        user_id: User ID
        org_id: Organization ID
        new_role: New role ('owner', 'admin', 'member')

    Returns:
        True if role was updated, False if member not found
    """
    result = await conn.fetchval(
        """
        SELECT activity.sp_update_member_role($1, $2, $3)
        """,
        user_id,
        org_id,
        new_role
    )

    return bool(result)


async def sp_get_organization_members(
    conn: asyncpg.Connection,
    org_id: UUID,
    limit: int = 100,
    offset: int = 0
) -> List[OrganizationMemberRecord]:
    """
    Get members of an organization (paginated).

    Args:
        conn: Database connection
        org_id: Organization ID
        limit: Max number of members to return (default 100)
        offset: Pagination offset (default 0)

    Returns:
        List of OrganizationMemberRecord
    """
    results = await conn.fetch(
        """
        SELECT * FROM activity.sp_get_organization_members($1, $2, $3)
        """,
        org_id,
        limit,
        offset
    )

    return [OrganizationMemberRecord(r) for r in results]
