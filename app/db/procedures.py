from typing import Optional
from uuid import UUID
from datetime import timedelta, datetime, timezone

import asyncpg
from jose import jwt

from app.db.logging import log_stored_procedure


class UserRecord:
    def __init__(self, record: asyncpg.Record):
        self.id: UUID = record["id"]
        self.email: str = record["email"]
        self.hashed_password: Optional[str] = record.get("hashed_password")
        self.is_verified: bool = record["is_verified"]
        self.is_active: bool = record["is_active"]
        self.created_at = record["created_at"]
        self.verified_at = record.get("verified_at")
        self.last_login_at = record.get("last_login_at")


class OrganizationMemberRecord:
    """Record representing a user's membership in an organization."""
    def __init__(self, record: asyncpg.Record):
        self.id: UUID = record["id"]
        self.user_id: UUID = record["user_id"]
        self.organization_id: UUID = record["organization_id"]
        self.role: str = record["role"]  # 'owner', 'admin', or 'member'
        self.joined_at = record["joined_at"]
        self.invited_by: Optional[UUID] = record.get("invited_by")


@log_stored_procedure
async def sp_create_user(
    conn: asyncpg.Connection,
    email: str,
    hashed_password: str
) -> UserRecord:
    result = await conn.fetchrow(
        "SELECT * FROM activity.sp_create_user($1, $2)",
        email.lower(),
        hashed_password
    )

    if not result:
        raise RuntimeError("sp_create_user returned no data")

    return UserRecord(result)


@log_stored_procedure
async def sp_get_user_by_email(
    conn: asyncpg.Connection,
    email: str
) -> Optional[UserRecord]:
    result = await conn.fetchrow(
        "SELECT * FROM activity.sp_get_user_by_email($1)",
        email.lower()
    )

    return UserRecord(result) if result else None


@log_stored_procedure
async def sp_get_user_by_id(
    conn: asyncpg.Connection,
    user_id: UUID
) -> Optional[UserRecord]:
    result = await conn.fetchrow(
        "SELECT * FROM activity.sp_get_user_by_id($1)",
        user_id
    )

    return UserRecord(result) if result else None


@log_stored_procedure
async def sp_verify_user_email(
    conn: asyncpg.Connection,
    user_id: UUID
) -> bool:
    result = await conn.fetchval(
        "SELECT activity.sp_verify_user_email($1)",
        user_id
    )

    return bool(result)


@log_stored_procedure
async def sp_save_refresh_token(
    conn: asyncpg.Connection,
    user_id: UUID,
    token: str,
    expires_delta: timedelta
) -> bool:
    payload = jwt.get_unverified_claims(token)
    jti = payload.get("jti")

    if not jti:
        raise ValueError("Token does not have a jti claim")

    # Calculate expiration with explicit timezone awareness
    now_utc = datetime.now(timezone.utc)
    expires_at = (now_utc + expires_delta).replace(tzinfo=None)

    result = await conn.fetchval(
        "SELECT activity.sp_save_refresh_token($1, $2, $3, $4)",
        user_id,
        token,
        jti,
        expires_at
    )
    return bool(result)


@log_stored_procedure
async def sp_validate_refresh_token(
    conn: asyncpg.Connection,
    user_id: UUID,
    token: str
) -> bool:
    result = await conn.fetchval(
        "SELECT 1 FROM activity.refresh_tokens WHERE user_id = $1 AND token = $2 AND revoked = FALSE AND expires_at > NOW()",
        user_id,
        token
    )
    return result is not None


@log_stored_procedure
async def sp_revoke_refresh_token(
    conn: asyncpg.Connection,
    user_id: UUID,
    token: str
) -> None:
    await conn.execute(
        "UPDATE activity.refresh_tokens SET revoked = TRUE WHERE user_id = $1 AND token = $2",
        user_id,
        token
    )


@log_stored_procedure
async def sp_revoke_all_refresh_tokens(
    conn: asyncpg.Connection,
    user_id: UUID
) -> None:
    await conn.execute(
        "UPDATE activity.refresh_tokens SET revoked = TRUE WHERE user_id = $1",
        user_id
    )


@log_stored_procedure
async def sp_update_password(
    conn: asyncpg.Connection,
    user_id: UUID,
    hashed_password: str
) -> bool:
    result = await conn.fetchval(
        "SELECT activity.sp_update_password($1, $2)",
        user_id,
        hashed_password
    )
    return bool(result)




@log_stored_procedure
async def check_email_exists(
    conn: asyncpg.Connection,
    email: str
) -> bool:
    user = await sp_get_user_by_email(conn, email)
    return user is not None


@log_stored_procedure
async def sp_add_organization_member(
    conn: asyncpg.Connection,
    user_id: UUID,
    organization_id: UUID,
    role: str = "member",
    invited_by: Optional[UUID] = None
) -> OrganizationMemberRecord:
    """Add a user to an organization with specified role.

    Args:
        conn: Database connection
        user_id: UUID of the user to add
        organization_id: UUID of the organization
        role: Role to assign ('owner', 'admin', or 'member'). Defaults to 'member'
        invited_by: UUID of the user who invited this member (DEPRECATED - not used by v2 procedure)

    Returns:
        OrganizationMemberRecord with membership details

    Note:
        This procedure is idempotent (uses ON CONFLICT DO NOTHING).
        Calling it multiple times with the same user_id and organization_id is safe.

        Uses sp_add_organization_member_v2 which doesn't require the invited_by parameter
        since the database table doesn't have that column.
    """
    result = await conn.fetchrow(
        "SELECT * FROM activity.sp_add_organization_member_v2($1, $2, $3)",
        user_id,
        organization_id,
        role
    )

    if not result:
        raise RuntimeError("sp_add_organization_member_v2 returned no data")

    return OrganizationMemberRecord(result)
