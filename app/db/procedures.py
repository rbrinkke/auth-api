"""
Wrapper functions for calling PostgreSQL stored procedures.

All database interactions go through these functions.
Each function corresponds to a stored procedure that YOU will create.
"""
from typing import Optional
from uuid import UUID

import asyncpg


class UserRecord:
    """Represents a user record returned from stored procedures."""

    def __init__(self, record: asyncpg.Record):
        self.id: UUID = record["id"]
        self.email: str = record["email"]
        # hashed_password is optional - only returned by get procedures, not create
        self.hashed_password: Optional[str] = record.get("hashed_password")
        self.is_verified: bool = record["is_verified"]
        self.is_active: bool = record["is_active"]
        self.created_at = record["created_at"]
        self.verified_at = record.get("verified_at")
        self.last_login_at = record.get("last_login_at")
        # 2FA fields
        self.two_factor_enabled: bool = record.get("two_factor_enabled", False)
        self.two_factor_secret: Optional[str] = record.get("two_factor_secret")
        self.two_factor_backup_codes: Optional[list] = record.get("two_factor_backup_codes", [])


# ========== User Management Procedures ==========

async def sp_create_user(
    conn: asyncpg.Connection,
    email: str,
    hashed_password: str
) -> UserRecord:
    """
    Call sp_create_user stored procedure.
    
    Expected SP signature:
        sp_create_user(p_email VARCHAR, p_hashed_password VARCHAR)
        RETURNS TABLE(id, email, is_verified, is_active, created_at)
    
    Args:
        conn: Database connection
        email: User's email (will be lowercased)
        hashed_password: Argon2id hashed password
        
    Returns:
        UserRecord with the created user data
        
    Raises:
        asyncpg.UniqueViolationError: If email already exists
    """
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
    """
    Call sp_get_user_by_email stored procedure.
    
    Expected SP signature:
        sp_get_user_by_email(p_email VARCHAR)
        RETURNS TABLE(id, email, hashed_password, is_verified, is_active, 
                      created_at, verified_at, last_login_at)
    
    Args:
        conn: Database connection
        email: User's email
        
    Returns:
        UserRecord if found, None otherwise
    """
    result = await conn.fetchrow(
        "SELECT * FROM activity.sp_get_user_by_email($1)",
        email.lower()
    )
    
    return UserRecord(result) if result else None


async def sp_get_user_by_id(
    conn: asyncpg.Connection,
    user_id: UUID
) -> Optional[UserRecord]:
    """
    Call sp_get_user_by_id stored procedure.
    
    Expected SP signature:
        sp_get_user_by_id(p_user_id UUID)
        RETURNS TABLE(id, email, hashed_password, is_verified, is_active,
                      created_at, verified_at, last_login_at)
    
    Args:
        conn: Database connection
        user_id: User's UUID
        
    Returns:
        UserRecord if found, None otherwise
    """
    result = await conn.fetchrow(
        "SELECT * FROM activity.sp_get_user_by_id($1)",
        user_id
    )
    
    return UserRecord(result) if result else None


async def sp_verify_user_email(
    conn: asyncpg.Connection,
    user_id: UUID
) -> bool:
    """
    Call sp_verify_user_email stored procedure.
    
    Expected SP signature:
        sp_verify_user_email(p_user_id UUID)
        RETURNS BOOLEAN
    
    Sets is_verified = TRUE and verified_at = NOW()
    
    Args:
        conn: Database connection
        user_id: User's UUID
        
    Returns:
        True if successful, False if user not found
    """
    result = await conn.fetchval(
        "SELECT activity.sp_verify_user_email($1)",
        user_id
    )
    
    return bool(result)


async def sp_update_last_login(
    conn: asyncpg.Connection,
    user_id: UUID
) -> None:
    """
    Call sp_update_last_login stored procedure.
    
    Expected SP signature:
        sp_update_last_login(p_user_id UUID)
        RETURNS VOID
    
    Updates last_login_at = NOW()
    
    Args:
        conn: Database connection
        user_id: User's UUID
    """
    await conn.execute(
        "SELECT activity.sp_update_last_login($1)",
        user_id
    )


async def sp_update_password(
    conn: asyncpg.Connection,
    user_id: UUID,
    new_hashed_password: str
) -> bool:
    """
    Call sp_update_password stored procedure.
    
    Expected SP signature:
        sp_update_password(p_user_id UUID, p_new_hashed_password VARCHAR)
        RETURNS BOOLEAN
    
    Args:
        conn: Database connection
        user_id: User's UUID
        new_hashed_password: New Argon2id hashed password
        
    Returns:
        True if successful, False if user not found
    """
    result = await conn.fetchval(
        "SELECT activity.sp_update_password($1, $2)",
        user_id,
        new_hashed_password
    )
    
    return bool(result)


async def sp_deactivate_user(
    conn: asyncpg.Connection,
    user_id: UUID
) -> bool:
    """
    Call sp_deactivate_user stored procedure (soft delete).
    
    Expected SP signature:
        sp_deactivate_user(p_user_id UUID)
        RETURNS BOOLEAN
    
    Sets is_active = FALSE
    
    Args:
        conn: Database connection
        user_id: User's UUID
        
    Returns:
        True if successful, False if user not found
    """
    result = await conn.fetchval(
        "SELECT activity.sp_deactivate_user($1)",
        user_id
    )
    
    return bool(result)


# ========== Helper Function ==========

async def check_email_exists(
    conn: asyncpg.Connection,
    email: str
) -> bool:
    """
    Check if an email already exists in the database.
    
    This is a convenience function that uses sp_get_user_by_email.
    
    Args:
        conn: Database connection
        email: Email to check
        
    Returns:
        True if email exists, False otherwise
    """
    user = await sp_get_user_by_email(conn, email)
    return user is not None
