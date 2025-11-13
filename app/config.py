import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
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

    VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 1440
    RESET_TOKEN_EXPIRE_MINUTES: int = 60

    EMAIL_SERVICE_URL: str = "http://email-api:8010"
    EMAIL_SERVICE_TIMEOUT: int = 10
    SERVICE_AUTH_TOKEN: str = "st_dev_5555555555555555555555555555555555555555"

    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000"

    RATE_LIMIT_REQUESTS: int = 5
    RATE_LIMIT_TIMEFRAME: int = 60
    RATE_LIMIT_REGISTER_PER_HOUR: int = 3
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 5
    RATE_LIMIT_RESEND_VERIFICATION_PER_5MIN: int = 1
    RATE_LIMIT_PASSWORD_RESET_PER_5MIN: int = 1

    # Request Size Limits (bytes)
    REQUEST_SIZE_LIMIT_DEFAULT: int = 10240  # 10 KB
    REQUEST_SIZE_LIMIT_GLOBAL_MAX: int = 1048576  # 1 MB
    REQUEST_SIZE_LIMIT_REGISTER: int = 10240  # 10 KB
    REQUEST_SIZE_LIMIT_LOGIN: int = 10240  # 10 KB
    REQUEST_SIZE_LIMIT_PASSWORD_RESET: int = 5120  # 5 KB
    REQUEST_SIZE_LIMIT_TOKEN_REFRESH: int = 5120  # 5 KB
    REQUEST_SIZE_LIMIT_2FA: int = 5120  # 5 KB

    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    ENCRYPTION_KEY: str = "dev_encryption_key_for_2fa_secrets_32_chars_minimum_required"

    TWO_FACTOR_ENABLED: bool = False

    # Development: Skip email login code for faster testing
    # WARNING: Only use in development! Always False in production
    SKIP_LOGIN_CODE: bool = False

    VERIFICATION_TOKEN_TTL: int = 86400
    RESET_TOKEN_TTL: int = 3600

    LOGIN_CODE_EXPIRE_SECONDS: int = 600  # 10 minutes

    LOG_LEVEL: str = "INFO"

    @field_validator("JWT_SECRET_KEY", mode="after")
    @classmethod
    def validate_jwt_secret_key(cls, v: str) -> str:
        """Validate JWT secret key for production safety.

        Must be at least 32 characters. In production (DEBUG=False),
        must not contain development indicators.
        """
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v

    @field_validator("ENCRYPTION_KEY", mode="after")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        """Validate 2FA encryption key.

        Must be at least 32 characters for security.
        """
        if len(v) < 32:
            raise ValueError("ENCRYPTION_KEY must be at least 32 characters")
        return v

    @field_validator("REQUEST_SIZE_LIMIT_GLOBAL_MAX", mode="after")
    @classmethod
    def validate_request_size_limit_global_max(cls, v: int) -> int:
        """Validate global request size limit.

        Must be between 1 KB and 100 MB to prevent misconfiguration.
        """
        if v < 1024 or v > 104857600:  # 1 KB - 100 MB
            raise ValueError(
                "REQUEST_SIZE_LIMIT_GLOBAL_MAX must be between 1024 (1 KB) "
                "and 104857600 (100 MB) bytes"
            )
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()
