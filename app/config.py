import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "activitydb"
    POSTGRES_USER: str = "activity_user"
    POSTGRES_PASSWORD: str = "dev_password_change_in_prod"

    DATABASE_URL: str = "postgresql://activity_user:dev_password_change_in_prod@postgres:5432/activitydb"

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    JWT_SECRET_KEY: str = "dev_secret_key_change_in_production_min_32_chars_required"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    SECRET_KEY: str = "dev_secret_key_change_in_production_min_32_chars_required"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 1440
    RESET_TOKEN_EXPIRE_MINUTES: int = 60

    EMAIL_SERVICE_URL: str = "http://dummy-email:9000"
    EMAIL_SERVICE_TIMEOUT: int = 10

    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000"

    RATE_LIMIT_REQUESTS: int = 5
    RATE_LIMIT_TIMEFRAME: int = 60
    RATE_LIMIT_REGISTER_PER_HOUR: int = 3
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 5
    RATE_LIMIT_RESEND_VERIFICATION_PER_5MIN: int = 1
    RATE_LIMIT_PASSWORD_RESET_PER_5MIN: int = 1

    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    ENCRYPTION_KEY: str = "dev_encryption_key_for_2fa_secrets_32_chars_minimum_required"

    TWO_FACTOR_ENABLED: bool = False

    VERIFICATION_TOKEN_TTL: int = 86400
    RESET_TOKEN_TTL: int = 3600

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()
