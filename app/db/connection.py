from typing import Optional

import asyncpg

from app.config import settings


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
            database=settings.postgres_db,
            min_size=settings.postgres_pool_min_size,
            max_size=settings.postgres_pool_max_size,
            command_timeout=settings.postgres_pool_command_timeout,
            server_settings={
                'search_path': settings.postgres_schema
            }
        )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def acquire(self) -> asyncpg.Connection:
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        return await self.pool.acquire()

    async def ping(self) -> None:
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        async with self.pool.acquire() as conn:
            await conn.fetchval("SELECT 1")


db = Database()


async def get_db_connection() -> asyncpg.Connection:
    if not db.pool:
        raise RuntimeError("Database pool not initialized")

    async with db.pool.acquire() as connection:
        yield connection
