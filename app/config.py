# /mnt/d/activity/auth-api/app/config.py
import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 1440 # 1 day
    RESET_TOKEN_EXPIRE_MINUTES: int = 60
    
    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_USERNAME: str
    EMAIL_PASSWORD: str
    EMAIL_FROM: str

    FRONTEND_URL: str = "http://localhost:3000"

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 5
    RATE_LIMIT_TIMEFRAME: int = 60 # 1 minute

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

@lru_cache()
def get_settings() -> Settings:
    return Settings()
