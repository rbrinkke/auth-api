import redis
from redis import ConnectionPool
from fastapi import Depends
from typing import Optional
from app.config import Settings, get_settings

# Global Redis connection pool
_redis_pool: Optional[ConnectionPool] = None

def init_redis_pool(settings: Settings) -> ConnectionPool:
    """Initialize global Redis connection pool on first use.

    Connection pooling dramatically improves performance by reusing
    connections instead of creating new ones per request.
    """
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True,
            max_connections=50  # Pool size for concurrent requests
        )
    return _redis_pool

def get_redis_client(settings: Settings = Depends(get_settings)) -> redis.Redis:
    """Get Redis client from connection pool.

    Uses a shared connection pool instead of creating new connections
    per request. This dramatically improves performance and prevents
    connection exhaustion under load.
    """
    pool = init_redis_pool(settings)
    client = redis.Redis(connection_pool=pool)
    yield client
    # Connection automatically returned to pool when client is garbage collected
