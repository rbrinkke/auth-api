"""
PostgreSQL database connection management using asyncpg.

This module provides a connection pool that's initialized on startup
and shared across the application.
"""
from typing import Optional

import asyncpg

from app.config import settings


class Database:
    """Database connection pool manager."""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """
        Create and initialize the connection pool.
        
        The pool is configured to:
        - Use the schema specified in settings
        - Maintain a minimum of 5 connections
        - Allow up to 20 connections
        """
        self.pool = await asyncpg.create_pool(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
            database=settings.postgres_db,
            min_size=settings.postgres_pool_min_size,
            max_size=settings.postgres_pool_max_size,
            command_timeout=settings.postgres_pool_command_timeout,
            # Set search_path to use the activity schema by default
            server_settings={
                'search_path': settings.postgres_schema
            }
        )
    
    async def disconnect(self):
        """Close all connections in the pool."""
        if self.pool:
            await self.pool.close()
    
    async def acquire(self) -> asyncpg.Connection:
        """
        Acquire a connection from the pool.

        Usage:
            async with db.pool.acquire() as conn:
                result = await conn.fetchrow("SELECT ...")

        Returns:
            A database connection
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        return await self.pool.acquire()

    async def ping(self) -> None:
        """
        Ping the database to check connectivity.

        This method tests if the database connection is working by executing
        a simple SELECT 1 query. Used for health checks.

        Raises:
            Exception: If the database is not accessible
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        async with self.pool.acquire() as conn:
            await conn.fetchval("SELECT 1")


# Global database instance
db = Database()


async def get_db_connection() -> asyncpg.Connection:
    """
    FastAPI dependency for getting a database connection.
    
    Usage:
        @router.get("/users")
        async def get_users(conn = Depends(get_db_connection)):
            return await conn.fetch("SELECT * FROM users")
    
    Yields:
        A database connection from the pool
    """
    if not db.pool:
        raise RuntimeError("Database pool not initialized")
    
    async with db.pool.acquire() as connection:
        yield connection
