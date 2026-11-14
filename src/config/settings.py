"""Application configuration management using Pydantic Settings."""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Platform configuration loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    supabase_url: str = Field(
        default="",
        validation_alias="SUPABASE_URL",
        description="Supabase project endpoint URL",
    )
    supabase_publishable_key: SecretStr = Field(
        default=SecretStr(""),
        validation_alias="SUPABASE_PUBLISHABLE_KEY",
        description="Supabase client/anonymous public key",
    )
    supabase_secret_key: SecretStr = Field(
        default=SecretStr(""),
        validation_alias="SUPABASE_SECRET_KEY",
        description="Supabase service-role secret key (server-side only)",
    )
    database_url: SecretStr = Field(
        default=SecretStr(""),
        validation_alias="DATABASE_URL",
        description="Direct PostgreSQL connection string",
    )
    log_level: str = Field(
        default="INFO",
        validation_alias="LOG_LEVEL",
        description="Application log verbosity level",
    )
    environment: str = Field(
        default="development",
        validation_alias="ENVIRONMENT",
        description="Deployment environment name",
    )


@lru_cache
def get_settings() -> Settings:
    """Retrieve cached singleton application settings instance."""
    return Settings()
