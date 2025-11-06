from typing import Optional
from uuid import UUID
from datetime import timedelta, datetime, timezone

import asyncpg
from jose import jwt


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


async def sp_get_user_by_email(
    conn: asyncpg.Connection,
    email: str
) -> Optional[UserRecord]:
    result = await conn.fetchrow(
        "SELECT * FROM activity.sp_get_user_by_email($1)",
        email.lower()
    )

    return UserRecord(result) if result else None


async def sp_get_user_by_id(
    conn: asyncpg.Connection,
    user_id: UUID
) -> Optional[UserRecord]:
    result = await conn.fetchrow(
        "SELECT * FROM activity.sp_get_user_by_id($1)",
        user_id
    )

    return UserRecord(result) if result else None


async def sp_verify_user_email(
    conn: asyncpg.Connection,
    user_id: UUID
) -> bool:
    result = await conn.fetchval(
        "SELECT activity.sp_verify_user_email($1)",
        user_id
    )

    return bool(result)


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
    expires_at = now_utc + expires_delta

    result = await conn.fetchval(
        "SELECT activity.sp_save_refresh_token($1, $2, $3, $4)",
        user_id,
        token,
        jti,
        expires_at
    )
    return bool(result)


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


async def sp_revoke_all_refresh_tokens(
    conn: asyncpg.Connection,
    user_id: UUID
) -> None:
    await conn.execute(
        "UPDATE activity.refresh_tokens SET revoked = TRUE WHERE user_id = $1",
        user_id
    )


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




async def check_email_exists(
    conn: asyncpg.Connection,
    email: str
) -> bool:
    user = await sp_get_user_by_email(conn, email)
    return user is not None
