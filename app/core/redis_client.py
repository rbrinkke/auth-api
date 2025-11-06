# /mnt/d/activity/auth-api/app/core/redis_client.py
import redis
from fastapi import Depends
from app.config import Settings, get_settings

def get_redis_client(settings: Settings = Depends(get_settings)) -> redis.Redis:
    """
    Dependency to get a Redis client.
    This will be managed by FastAPI's dependency injection system.
    """
    try:
        client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True  # Decode responses to strings
        )
        client.ping()
        yield client
    finally:
        client.close()
