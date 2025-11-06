"""
Application configuration using Pydantic Settings.
All values can be overridden via environment variables.
"""
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = "Auth API"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # PostgreSQL
    postgres_host: str = Field(default="postgres")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="activitydb")
    postgres_user: str = Field(default="activity_user")
    postgres_password: str = Field(default="")
    postgres_schema: str = Field(default="activity")
    postgres_pool_min_size: int = Field(default=5)
    postgres_pool_max_size: int = Field(default=20)
    postgres_pool_command_timeout: int = Field(default=60)

    # Redis
    redis_host: str = Field(default="redis")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    redis_password: str | None = Field(default=None)
    
    # JWT Settings
    jwt_secret_key: str = Field(default="")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=15)
    jwt_refresh_token_expire_days: int = Field(default=30)
    
    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if not v or len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v
    
    # Email Service
    email_service_url: str = Field(default="")
    email_service_timeout: int = Field(default=10)
    
    # Frontend URL (for verification links)
    frontend_url: str = Field(default="http://localhost:3000")
    
    # Token TTLs (in seconds for Redis)
    verification_token_ttl: int = Field(default=86400)  # 24 hours
    reset_token_ttl: int = Field(default=3600)  # 1 hour
    
    # Rate Limiting
    rate_limit_register_per_hour: int = Field(default=3)
    rate_limit_login_per_minute: int = Field(default=5)
    rate_limit_resend_verification_per_5min: int = Field(default=1)
    rate_limit_password_reset_per_5min: int = Field(default=1)

    # 2FA Encryption Key (for TOTP secrets)
    encryption_key: str = Field(default="")

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        if not v or len(v) < 32:
            raise ValueError("ENCRYPTION_KEY must be at least 32 characters for 2FA secret encryption")
        return v
    
    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:3000"])
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def postgres_url(self) -> str:
        """Build PostgreSQL connection URL."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    @property
    def redis_url(self) -> str:
        """Build Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


# Global settings instance
settings = Settings()
