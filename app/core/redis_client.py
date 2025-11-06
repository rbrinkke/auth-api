import redis
from fastapi import Depends
from app.config import Settings, get_settings

def get_redis_client(settings: Settings = Depends(get_settings)) -> redis.Redis:
    try:
        client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True
        )
        client.ping()
        yield client
    finally:
        client.close()
