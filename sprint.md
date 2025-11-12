# Sprint Plan: Best-of-Class RBAC Multi-tenant Authorization System

## Overview
We gaan een enterprise-grade authorization systeem bouwen met **organizations**, **groups**, en **fine-grained permissions**. Elegant, simpel, snel.

**Architectuur principes:**
- Multi-tenancy first (organization_id overal)
- Resource:Action permission pattern (AWS IAM style)
- PostgreSQL stored procedures (business logic in DB)
- Redis caching layer (performance)
- Clean API design (RESTful, intuitive)

**Tech stack:**
- FastAPI (blijft zoals het is)
- PostgreSQL + asyncpg (stored procedures)
- Redis (caching)
- JWT tokens (extended met org_id)

---

## SPRINT 1: Organizations Foundation 🏢

**Goal**: Multi-tenancy basis - users kunnen tot organizations behoren.

### STEP 1.1: Database Schema - Organizations

**File**: `migrations/001_organizations_schema.sql`

```sql
-- ============================================================================
-- MIGRATION 001: Organizations Foundation
-- ============================================================================
-- Purpose: Add multi-tenancy support with organizations
-- Author: Claude Code Agent
-- Dependencies: Existing activity.users table
-- ============================================================================

-- ORGANIZATIONS TABLE
-- Each organization is a separate tenant with isolated data
CREATE TABLE IF NOT EXISTS activity.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,  -- URL-friendly identifier
    description TEXT,
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Soft delete support
    deleted_at TIMESTAMPTZ,
    
    -- Constraints
    CONSTRAINT organizations_name_not_empty CHECK (LENGTH(TRIM(name)) > 0),
    CONSTRAINT organizations_slug_format CHECK (slug ~ '^[a-z0-9-]+$'),
    CONSTRAINT organizations_slug_length CHECK (LENGTH(slug) BETWEEN 2 AND 50)
);

-- ORGANIZATION MEMBERS TABLE
-- Links users to organizations with roles
CREATE TABLE IF NOT EXISTS activity.organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES activity.users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES activity.organizations(id) ON DELETE CASCADE,
    
    -- Role within organization (org-level, not group-level)
    -- "owner" = full control, "admin" = manage members/groups, "member" = regular user
    role TEXT NOT NULL DEFAULT 'member',
    
    -- Metadata
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    invited_by UUID REFERENCES activity.users(id) ON DELETE SET NULL,
    
    -- Constraints
    CONSTRAINT organization_members_unique_user_org UNIQUE(user_id, organization_id),
    CONSTRAINT organization_members_role_valid CHECK (role IN ('owner', 'admin', 'member'))
);

-- INDEXES for performance
CREATE INDEX idx_organizations_slug ON activity.organizations(slug) WHERE deleted_at IS NULL;
CREATE INDEX idx_organizations_created_at ON activity.organizations(created_at);
CREATE INDEX idx_org_members_user_id ON activity.organization_members(user_id);
CREATE INDEX idx_org_members_org_id ON activity.organization_members(organization_id);
CREATE INDEX idx_org_members_role ON activity.organization_members(role);

-- TRIGGER: Auto-update updated_at
CREATE OR REPLACE FUNCTION activity.update_organizations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_organizations_updated_at
    BEFORE UPDATE ON activity.organizations
    FOR EACH ROW
    EXECUTE FUNCTION activity.update_organizations_updated_at();

-- ============================================================================
-- STORED PROCEDURES: Organization Management
-- ============================================================================

-- SP: Create Organization
-- Creates a new organization and adds creator as owner
CREATE OR REPLACE FUNCTION activity.sp_create_organization(
    p_name TEXT,
    p_slug TEXT,
    p_description TEXT,
    p_creator_user_id UUID
)
RETURNS TABLE(
    id UUID,
    name TEXT,
    slug TEXT,
    description TEXT,
    created_at TIMESTAMPTZ
) AS $$
DECLARE
    v_org_id UUID;
BEGIN
    -- Insert organization
    INSERT INTO activity.organizations (name, slug, description)
    VALUES (p_name, p_slug, p_description)
    RETURNING activity.organizations.id INTO v_org_id;
    
    -- Add creator as owner
    INSERT INTO activity.organization_members (user_id, organization_id, role, invited_by)
    VALUES (p_creator_user_id, v_org_id, 'owner', NULL);
    
    -- Return created organization
    RETURN QUERY
    SELECT 
        o.id,
        o.name,
        o.slug,
        o.description,
        o.created_at
    FROM activity.organizations o
    WHERE o.id = v_org_id;
END;
$$ LANGUAGE plpgsql;

-- SP: Get User's Organizations
-- Returns all organizations a user is member of
CREATE OR REPLACE FUNCTION activity.sp_get_user_organizations(
    p_user_id UUID
)
RETURNS TABLE(
    id UUID,
    name TEXT,
    slug TEXT,
    description TEXT,
    role TEXT,
    member_count BIGINT,
    joined_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o.id,
        o.name,
        o.slug,
        o.description,
        om.role,
        (SELECT COUNT(*) FROM activity.organization_members WHERE organization_id = o.id) as member_count,
        om.joined_at
    FROM activity.organizations o
    INNER JOIN activity.organization_members om ON o.id = om.organization_id
    WHERE om.user_id = p_user_id
      AND o.deleted_at IS NULL
    ORDER BY om.joined_at DESC;
END;
$$ LANGUAGE plpgsql;

-- SP: Get Organization by ID
CREATE OR REPLACE FUNCTION activity.sp_get_organization_by_id(
    p_org_id UUID
)
RETURNS TABLE(
    id UUID,
    name TEXT,
    slug TEXT,
    description TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    member_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o.id,
        o.name,
        o.slug,
        o.description,
        o.created_at,
        o.updated_at,
        (SELECT COUNT(*) FROM activity.organization_members WHERE organization_id = o.id) as member_count
    FROM activity.organizations o
    WHERE o.id = p_org_id
      AND o.deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql;

-- SP: Check if user is member of organization
CREATE OR REPLACE FUNCTION activity.sp_is_organization_member(
    p_user_id UUID,
    p_org_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    v_is_member BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1 
        FROM activity.organization_members 
        WHERE user_id = p_user_id 
          AND organization_id = p_org_id
    ) INTO v_is_member;
    
    RETURN v_is_member;
END;
$$ LANGUAGE plpgsql;

-- SP: Get user's role in organization
CREATE OR REPLACE FUNCTION activity.sp_get_user_org_role(
    p_user_id UUID,
    p_org_id UUID
)
RETURNS TEXT AS $$
DECLARE
    v_role TEXT;
BEGIN
    SELECT role INTO v_role
    FROM activity.organization_members
    WHERE user_id = p_user_id
      AND organization_id = p_org_id;
    
    RETURN v_role;
END;
$$ LANGUAGE plpgsql;

-- SP: Add member to organization
CREATE OR REPLACE FUNCTION activity.sp_add_organization_member(
    p_user_id UUID,
    p_org_id UUID,
    p_role TEXT,
    p_invited_by UUID
)
RETURNS TABLE(
    id UUID,
    user_email TEXT,
    role TEXT,
    joined_at TIMESTAMPTZ
) AS $$
BEGIN
    -- Insert membership
    INSERT INTO activity.organization_members (user_id, organization_id, role, invited_by)
    VALUES (p_user_id, p_org_id, p_role, p_invited_by)
    ON CONFLICT (user_id, organization_id) DO NOTHING;
    
    -- Return membership info
    RETURN QUERY
    SELECT 
        om.id,
        u.email,
        om.role,
        om.joined_at
    FROM activity.organization_members om
    INNER JOIN activity.users u ON om.user_id = u.id
    WHERE om.user_id = p_user_id
      AND om.organization_id = p_org_id;
END;
$$ LANGUAGE plpgsql;

-- SP: Remove member from organization
CREATE OR REPLACE FUNCTION activity.sp_remove_organization_member(
    p_user_id UUID,
    p_org_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    v_deleted BOOLEAN;
BEGIN
    DELETE FROM activity.organization_members
    WHERE user_id = p_user_id
      AND organization_id = p_org_id;
    
    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted > 0;
END;
$$ LANGUAGE plpgsql;

-- SP: Update member role
CREATE OR REPLACE FUNCTION activity.sp_update_member_role(
    p_user_id UUID,
    p_org_id UUID,
    p_new_role TEXT
)
RETURNS BOOLEAN AS $$
DECLARE
    v_updated BOOLEAN;
BEGIN
    UPDATE activity.organization_members
    SET role = p_new_role
    WHERE user_id = p_user_id
      AND organization_id = p_org_id;
    
    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RETURN v_updated > 0;
END;
$$ LANGUAGE plpgsql;

-- SP: Get organization members
CREATE OR REPLACE FUNCTION activity.sp_get_organization_members(
    p_org_id UUID,
    p_limit INT DEFAULT 100,
    p_offset INT DEFAULT 0
)
RETURNS TABLE(
    user_id UUID,
    email TEXT,
    role TEXT,
    joined_at TIMESTAMPTZ,
    invited_by_email TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        om.user_id,
        u.email,
        om.role,
        om.joined_at,
        inviter.email as invited_by_email
    FROM activity.organization_members om
    INNER JOIN activity.users u ON om.user_id = u.id
    LEFT JOIN activity.users inviter ON om.invited_by = inviter.id
    WHERE om.organization_id = p_org_id
    ORDER BY om.joined_at DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SEED DATA: Bootstrap Platform Admin Organization (optional)
-- ============================================================================
-- Uncomment below to create a platform admin organization on migration

/*
DO $$
DECLARE
    v_platform_org_id UUID;
BEGIN
    -- Create platform admin organization if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM activity.organizations WHERE slug = 'platform-admin') THEN
        INSERT INTO activity.organizations (name, slug, description)
        VALUES (
            'Platform Administration',
            'platform-admin',
            'System administration organization for platform operators'
        )
        RETURNING id INTO v_platform_org_id;
        
        RAISE NOTICE 'Created platform admin organization: %', v_platform_org_id;
    END IF;
END $$;
*/

-- ============================================================================
-- VERIFICATION QUERIES (for testing)
-- ============================================================================
-- Run these after migration to verify:
-- SELECT * FROM activity.organizations;
-- SELECT * FROM activity.organization_members;
-- SELECT activity.sp_get_user_organizations('user-uuid-here');
```

**Instructions for Claude Code:**
1. Save this as `migrations/001_organizations_schema.sql`
2. Apply migration: `docker exec activity-postgres-db psql -U auth_api_user -d activitydb -f /path/to/001_organizations_schema.sql`
3. Verify tables exist: `\dt activity.organizations` and `\dt activity.organization_members`
4. Test stored procedures work

---

### STEP 1.2: Python Models & Schemas

**File**: `app/models/organization.py`

```python
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
- Redis caching on top (added later)
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
import asyncpg
from pydantic import BaseModel, Field


# ============================================================================
# PYDANTIC SCHEMAS (for API request/response)
# ============================================================================

class OrganizationCreate(BaseModel):
    """Request schema for creating an organization."""
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    slug: str = Field(..., min_length=2, max_length=50, pattern="^[a-z0-9-]+$", 
                     description="URL-friendly identifier (lowercase, hyphens allowed)")
    description: Optional[str] = Field(None, max_length=1000, description="Organization description")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Acme Corporation",
                "slug": "acme-corp",
                "description": "Leading provider of innovative solutions"
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

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Acme Corporation",
                "slug": "acme-corp",
                "description": "Leading provider of innovative solutions",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "member_count": 5
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

    class Config:
        from_attributes = True


class OrganizationMemberAdd(BaseModel):
    """Request schema for adding a member to organization."""
    user_id: UUID = Field(..., description="User ID to add")
    role: str = Field("member", pattern="^(owner|admin|member)$", description="Member role")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "role": "member"
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

    class Config:
        from_attributes = True


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
```

**Instructions for Claude Code:**
1. Create `app/models/organization.py` with this content
2. This provides clean Python interface to DB stored procedures
3. No business logic here - just types and DB calls
4. Test imports work: `from app.models.organization import sp_create_organization`

---

### STEP 1.3: Organization Service Layer

**File**: `app/services/organization_service.py`

```python
"""
Organization Service - Business Logic Layer

Handles organization CRUD operations and membership management.
Thin layer over database procedures with:
- Input validation (via Pydantic)
- Authorization checks
- Error handling
- Logging

Business logic stays in PostgreSQL stored procedures.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
import asyncpg

from app.db.connection import get_db_connection
from app.models.organization import (
    OrganizationCreate,
    OrganizationUpdate,
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
    sp_add_organization_member,
    sp_remove_organization_member,
    sp_update_member_role,
    sp_get_organization_members,
)
from app.core.exceptions import (
    UserNotFoundError,
    AuthException,
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
            HTTPException: 400 if slug already exists
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
            logger.warning("organization_create_failed_duplicate_slug", slug=org_data.slug)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Organization with slug '{org_data.slug}' already exists"
            )
        except Exception as e:
            logger.error("organization_create_failed", error=str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create organization"
            )
    
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
            HTTPException: 404 if not found, 403 if not member
        """
        logger.debug("get_organization", org_id=str(org_id), user_id=str(user_id))
        
        # Check membership
        is_member = await sp_is_organization_member(self.db, user_id, org_id)
        if not is_member:
            logger.warning("get_organization_forbidden",
                          org_id=str(org_id),
                          user_id=str(user_id))
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization"
            )
        
        # Get organization
        org_record = await sp_get_organization_by_id(self.db, org_id)
        if not org_record:
            logger.warning("get_organization_not_found", org_id=str(org_id))
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
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
            HTTPException: 403 if inviter lacks permission, 400 if already member
        """
        logger.info("add_organization_member",
                   org_id=str(org_id),
                   new_member_id=str(member_data.user_id),
                   inviter_id=str(inviter_user_id))
        
        # Check inviter has permission (must be admin or owner)
        inviter_role = await sp_get_user_org_role(self.db, inviter_user_id, org_id)
        if inviter_role not in ['owner', 'admin']:
            logger.warning("add_member_forbidden",
                          org_id=str(org_id),
                          inviter_id=str(inviter_user_id),
                          inviter_role=inviter_role)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners and admins can add members"
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this organization"
            )
        
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
            HTTPException: 403 if remover lacks permission
        """
        logger.info("remove_organization_member",
                   org_id=str(org_id),
                   member_id=str(member_user_id),
                   remover_id=str(remover_user_id))
        
        # Check remover has permission (must be admin or owner)
        remover_role = await sp_get_user_org_role(self.db, remover_user_id, org_id)
        if remover_role not in ['owner', 'admin']:
            logger.warning("remove_member_forbidden",
                          org_id=str(org_id),
                          remover_id=str(remover_user_id),
                          remover_role=remover_role)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners and admins can remove members"
            )
        
        # Cannot remove the last owner
        # TODO: Add check to prevent removing last owner
        
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in organization"
            )
        
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
            HTTPException: 403 if updater lacks permission
        """
        logger.info("update_member_role",
                   org_id=str(org_id),
                   member_id=str(member_user_id),
                   new_role=role_data.role,
                   updater_id=str(updater_user_id))
        
        # Check updater has permission (must be owner)
        updater_role = await sp_get_user_org_role(self.db, updater_user_id, org_id)
        if updater_role != 'owner':
            logger.warning("update_role_forbidden",
                          org_id=str(org_id),
                          updater_id=str(updater_user_id),
                          updater_role=updater_role)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners can change member roles"
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in organization"
            )
        
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
            HTTPException: 403 if not member
        """
        logger.debug("get_organization_members",
                    org_id=str(org_id),
                    user_id=str(user_id))
        
        # Check membership
        is_member = await sp_is_organization_member(self.db, user_id, org_id)
        if not is_member:
            logger.warning("get_members_forbidden",
                          org_id=str(org_id),
                          user_id=str(user_id))
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization"
            )
        
        # Get members
        member_records = await sp_get_organization_members(
            self.db,
            org_id=org_id,
            limit=limit,
            offset=offset
        )
        
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
```

**Instructions for Claude Code:**
1. Create `app/services/organization_service.py`
2. Service layer handles authorization and error handling
3. Business logic stays in DB stored procedures
4. Test service instantiation works

---

I'll continue with the remaining steps in follow-up messages to keep it organized. Next up:
- Step 1.4: API Routes (organization endpoints)
- Step 1.5: Update JWT tokens to include org_id
- Step 1.6: Update login flow for org selection

Should I continue with Step 1.4?
