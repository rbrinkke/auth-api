from typing import Optional
from uuid import UUID

import asyncpg


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
        self.two_factor_enabled: bool = record.get("two_factor_enabled", False)
        self.two_factor_secret: Optional[str] = record.get("two_factor_secret")
        self.two_factor_backup_codes: Optional[list] = record.get("two_factor_backup_codes", [])


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


async def sp_verify_user(
    conn: asyncpg.Connection,
    user_id: int
) -> None:
    await conn.execute(
        "UPDATE activity.users SET is_verified = TRUE, verified_at = NOW() WHERE id = $1",
        user_id
    )


async def sp_save_refresh_token(
    conn: asyncpg.Connection,
    user_id: int,
    token: str,
    expires_delta: timedelta
) -> None:
    await conn.execute(
        "INSERT INTO activity.refresh_tokens (user_id, token, expires_at) VALUES ($1, $2, NOW() + $3)",
        user_id,
        token,
        expires_delta
    )


async def sp_validate_refresh_token(
    conn: asyncpg.Connection,
    user_id: int,
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
    user_id: int,
    token: str
) -> None:
    await conn.execute(
        "UPDATE activity.refresh_tokens SET revoked = TRUE WHERE user_id = $1 AND token = $2",
        user_id,
        token
    )


async def sp_revoke_all_refresh_tokens(
    conn: asyncpg.Connection,
    user_id: int
) -> None:
    await conn.execute(
        "UPDATE activity.refresh_tokens SET revoked = TRUE WHERE user_id = $1",
        user_id
    )


async def sp_update_user_password(
    conn: asyncpg.Connection,
    user_id: int,
    hashed_password: str
) -> None:
    await conn.execute(
        "UPDATE activity.users SET hashed_password = $1 WHERE id = $2",
        hashed_password,
        user_id
    )


async def sp_set_2fa_secret(
    conn: asyncpg.Connection,
    user_id: int,
    secret: str,
    is_verified: bool
) -> None:
    await conn.execute(
        "UPDATE activity.users SET two_factor_secret = $1, is_2fa_enabled = $2 WHERE id = $3",
        secret,
        is_verified,
        user_id
    )


async def sp_disable_2fa(
    conn: asyncpg.Connection,
    user_id: int
) -> None:
    await conn.execute(
        "UPDATE activity.users SET two_factor_secret = NULL, is_2fa_enabled = FALSE WHERE id = $1",
        user_id
    )


async def check_email_exists(
    conn: asyncpg.Connection,
    email: str
) -> bool:
    user = await sp_get_user_by_email(conn, email)
    return user is not None
