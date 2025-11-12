"""
OAuth 2.0 Database Models

Database record wrappers for OAuth stored procedures.
Follows existing pattern (similar to UserRecord in procedures.py).
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
import asyncpg


class OAuthClientRecord:
    """OAuth client database record"""

    def __init__(self, record: asyncpg.Record):
        self.id: UUID = record["id"]
        self.client_id: str = record["client_id"]
        self.client_name: str = record["client_name"]
        self.client_type: str = record["client_type"]
        self.client_secret_hash: Optional[str] = record.get("client_secret_hash")
        self.redirect_uris: List[str] = record["redirect_uris"]
        self.allowed_scopes: List[str] = record["allowed_scopes"]
        self.require_pkce: bool = record["require_pkce"]
        self.require_consent: bool = record["require_consent"]
        self.is_first_party: bool = record["is_first_party"]
        self.description: Optional[str] = record.get("description")
        self.logo_uri: Optional[str] = record.get("logo_uri")
        self.created_at: datetime = record["created_at"]


class AuthorizationCodeRecord:
    """Authorization code database record"""

    def __init__(self, record: asyncpg.Record):
        self.id: UUID = record["id"]
        self.user_id: UUID = record["user_id"]
        self.organization_id: Optional[UUID] = record.get("organization_id")
        self.scopes: List[str] = record["scopes"]
        self.code_challenge: str = record["code_challenge"]
        self.code_challenge_method: str = record["code_challenge_method"]
        self.nonce: Optional[str] = record.get("nonce")


class ConsentRecord:
    """User consent database record"""

    def __init__(self, record: asyncpg.Record):
        self.has_consent: bool = record["has_consent"]
        self.granted_scopes: Optional[List[str]] = record.get("granted_scopes")
        self.needs_new_consent: bool = record["needs_new_consent"]


# ============================================================================
# STORED PROCEDURE WRAPPERS
# ============================================================================

async def sp_create_oauth_client(
    conn: asyncpg.Connection,
    client_id: str,
    client_name: str,
    client_type: str,
    redirect_uris: List[str],
    allowed_scopes: List[str],
    client_secret_hash: Optional[str] = None,
    is_first_party: bool = False,
    description: Optional[str] = None,
    logo_uri: Optional[str] = None,
    created_by: Optional[UUID] = None
) -> UUID:
    """Create OAuth client"""
    result = await conn.fetchval(
        """SELECT activity.sp_create_oauth_client(
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
        )""",
        client_id,
        client_name,
        client_type,
        redirect_uris,
        allowed_scopes,
        client_secret_hash,
        is_first_party,
        description,
        logo_uri,
        created_by
    )
    return result


async def sp_get_oauth_client(
    conn: asyncpg.Connection,
    client_id: str
) -> Optional[OAuthClientRecord]:
    """Get OAuth client by client_id"""
    result = await conn.fetchrow(
        "SELECT * FROM activity.sp_get_oauth_client($1)",
        client_id
    )
    return OAuthClientRecord(result) if result else None


async def sp_list_oauth_clients(
    conn: asyncpg.Connection
) -> List[OAuthClientRecord]:
    """List all OAuth clients"""
    results = await conn.fetch(
        "SELECT * FROM activity.sp_list_oauth_clients()"
    )
    return [OAuthClientRecord(r) for r in results]


async def sp_create_authorization_code(
    conn: asyncpg.Connection,
    code: str,
    client_id: str,
    user_id: UUID,
    organization_id: Optional[UUID],
    redirect_uri: str,
    scopes: List[str],
    code_challenge: str,
    code_challenge_method: str = "S256",
    nonce: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> UUID:
    """Create authorization code"""
    result = await conn.fetchval(
        """SELECT activity.sp_create_authorization_code(
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
        )""",
        code,
        client_id,
        user_id,
        organization_id,
        redirect_uri,
        scopes,
        code_challenge,
        code_challenge_method,
        nonce,
        ip_address,
        user_agent
    )
    return result


async def sp_validate_and_consume_authorization_code(
    conn: asyncpg.Connection,
    code: str,
    client_id: str,
    redirect_uri: str
) -> Optional[AuthorizationCodeRecord]:
    """Validate and consume authorization code (atomic, prevents replay)"""
    result = await conn.fetchrow(
        """SELECT * FROM activity.sp_validate_and_consume_authorization_code(
            $1, $2, $3
        )""",
        code,
        client_id,
        redirect_uri
    )
    return AuthorizationCodeRecord(result) if result else None


async def sp_save_user_consent(
    conn: asyncpg.Connection,
    user_id: UUID,
    client_id: str,
    organization_id: Optional[UUID],
    granted_scopes: List[str],
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> UUID:
    """Save user consent"""
    result = await conn.fetchval(
        """SELECT activity.sp_save_user_consent(
            $1, $2, $3, $4, $5, $6
        )""",
        user_id,
        client_id,
        organization_id,
        granted_scopes,
        ip_address,
        user_agent
    )
    return result


async def sp_get_user_consent(
    conn: asyncpg.Connection,
    user_id: UUID,
    client_id: str,
    organization_id: Optional[UUID],
    requested_scopes: List[str]
) -> ConsentRecord:
    """Check if user has consented to requested scopes"""
    result = await conn.fetchrow(
        """SELECT * FROM activity.sp_get_user_consent(
            $1, $2, $3, $4
        )""",
        user_id,
        client_id,
        organization_id,
        requested_scopes
    )
    return ConsentRecord(result) if result else ConsentRecord({
        "has_consent": False,
        "granted_scopes": None,
        "needs_new_consent": True
    })


async def sp_revoke_user_consent(
    conn: asyncpg.Connection,
    user_id: UUID,
    client_id: str,
    organization_id: Optional[UUID]
) -> bool:
    """Revoke user consent"""
    result = await conn.fetchval(
        """SELECT activity.sp_revoke_user_consent($1, $2, $3)""",
        user_id,
        client_id,
        organization_id
    )
    return bool(result)
