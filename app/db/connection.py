from typing import Optional

import asyncpg

from app.config import get_settings


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        settings = get_settings()
        self.pool = await asyncpg.create_pool(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            min_size=5,
            max_size=20,
            command_timeout=60
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
