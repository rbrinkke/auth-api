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
    POSTGRES_SCHEMA: str = "activity"
    POSTGRES_POOL_MIN_SIZE: int = 10
    POSTGRES_POOL_MAX_SIZE: int = 20

    DATABASE_URL: str = "postgresql://activity_user:dev_password_change_in_prod@postgres:5432/activitydb"

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Authorization Caching (NEW! 🚀)
    AUTHZ_CACHE_ENABLED: bool = True  # Enable Redis caching for authorization checks
    AUTHZ_L2_CACHE_ENABLED: bool = True  # Enable L2 cache (ALL user permissions)
    AUTHZ_CACHE_TTL: int = 300  # Cache TTL in seconds (5 minutes)

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

    # Debug Mode Configuration
    # Development: DEBUG=True (verbose logging, detailed errors, full audit logs)
    # Production: DEBUG=False (security-first, generic errors, sampled audit logs)
    # IMPORTANT: Production deployment with DEBUG=True is blocked by startup validation
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

    # API Documentation Settings
    ENABLE_DOCS: bool = True
    API_VERSION: str = "1.0.0"
    PROJECT_NAME: str = "Activity Platform - Authentication API"

    # Testing UI (Development/Testing only)
    ENABLE_TESTING_UI: bool = True  # Set to False in production

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

def validate_production_secrets(settings: Settings) -> None:
    """Validate that production secrets don't contain development patterns.

    This function prevents deploying to production with unsafe development secrets.
    Called during application startup when DEBUG=False.

    Args:
        settings: The Settings instance to validate

    Raises:
        RuntimeError: If any unsafe secrets are detected in production mode

    Example unsafe patterns:
        - JWT_SECRET_KEY = "dev_secret_key_change_in_production..."
        - POSTGRES_PASSWORD = "dev_password_change_in_prod"
        - ENCRYPTION_KEY = "dev_encryption_key_for_2fa..."
    """
    # Only validate in production mode (DEBUG=False)
    if settings.DEBUG:
        # Extra safety: Warn if DEBUG=True in production-like environments
        import os
        env = os.getenv("ENVIRONMENT", "").lower()
        if env in ["production", "prod", "staging", "stage"]:
            import warnings
            warnings.warn(
                f"⚠️  WARNING: DEBUG=True in {env.upper()} environment! "
                "This enables verbose logging and detailed error messages. "
                "Set DEBUG=False for production deployments.",
                stacklevel=2
            )
        return

    # Define secrets to validate and their names for error messages
    secrets_to_check = {
        "JWT_SECRET_KEY": settings.JWT_SECRET_KEY,
        "ENCRYPTION_KEY": settings.ENCRYPTION_KEY,
        "POSTGRES_PASSWORD": settings.POSTGRES_PASSWORD,
        "SERVICE_AUTH_TOKEN": settings.SERVICE_AUTH_TOKEN,
    }

    # Patterns that indicate development/unsafe secrets
    unsafe_patterns = [
        "dev_",
        "change_in_prod",
        "example",
        "test_",
        "demo_",
        "localhost",
        "password",  # Common weak password
        "secret",    # Too generic
        "default",
    ]

    # Check each secret for unsafe patterns
    unsafe_secrets = []
    for secret_name, secret_value in secrets_to_check.items():
        secret_lower = secret_value.lower()

        # Check for each unsafe pattern
        for pattern in unsafe_patterns:
            if pattern in secret_lower:
                unsafe_secrets.append({
                    "name": secret_name,
                    "pattern": pattern,
                    "preview": secret_value[:20] + "..." if len(secret_value) > 20 else secret_value
                })
                break  # Only report first match per secret

    # If any unsafe secrets found, raise error with details
    if unsafe_secrets:
        error_messages = [
            "🚨 PRODUCTION DEPLOYMENT BLOCKED - UNSAFE SECRETS DETECTED 🚨",
            "",
            "The following secrets contain development/unsafe patterns:",
            ""
        ]

        for unsafe in unsafe_secrets:
            error_messages.append(
                f"  ❌ {unsafe['name']}: Contains pattern '{unsafe['pattern']}'"
            )
            error_messages.append(
                f"     Preview: {unsafe['preview']}"
            )
            error_messages.append("")

        error_messages.extend([
            "Production secrets MUST:",
            "  1. Be cryptographically random (use: python -c \"import secrets; print(secrets.token_urlsafe(64))\")",
            "  2. Not contain patterns like: dev_, test_, example, change_in_prod, password, secret",
            "  3. Be set via environment variables (.env file), never hardcoded",
            "",
            "Fix these secrets in your .env file before deploying to production!",
            ""
        ])

        raise RuntimeError("\n".join(error_messages))


@lru_cache()
def get_settings() -> Settings:
    return Settings()
