"""Unit tests for typed application configuration and secret masking."""

import pytest
from pydantic import SecretStr
from src.config.settings import Settings, get_settings


def test_settings_defaults() -> None:
    """Verify default values when settings are initialized without explicit env vars."""
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.log_level == "INFO"
    assert settings.environment == "development"
    assert settings.supabase_url == ""


def test_settings_custom_values() -> None:
    """Verify settings loaded with custom values."""
    settings = Settings(
        supabase_url="https://test.supabase.co",
        supabase_publishable_key=SecretStr("pub_key_123"),
        supabase_secret_key=SecretStr("sec_key_456"),
        database_url=SecretStr("postgresql://user:pass@localhost:5432/db"),
        log_level="DEBUG",
        environment="staging",
    )
    assert settings.supabase_url == "https://test.supabase.co"
    assert settings.log_level == "DEBUG"
    assert settings.environment == "staging"


def test_settings_secret_masking() -> None:
    """Verify that SecretStr prevents credential leakage in string representation."""
    secret_value = "super_confidential_service_role_key"
    settings = Settings(
        supabase_secret_key=SecretStr(secret_value),
        database_url=SecretStr("postgresql://postgres:secretpassword@localhost:5432/postgres"),
    )

    # String representation must mask the secret
    assert str(settings.supabase_secret_key) == "**********"
    assert secret_value not in str(settings.supabase_secret_key)
    assert "secretpassword" not in str(settings.database_url)

    # repr must not disclose the plain secret
    assert secret_value not in repr(settings.supabase_secret_key)

    # get_secret_value must retrieve the raw secret for backend initialization
    assert settings.supabase_secret_key.get_secret_value() == secret_value


def test_settings_environment_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that environment variables correctly override default configuration."""
    monkeypatch.setenv("SUPABASE_URL", "https://override.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "env_pub_key")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "env_secret_key")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    monkeypatch.setenv("ENVIRONMENT", "production")

    settings = Settings()
    assert settings.supabase_url == "https://override.supabase.co"
    assert settings.supabase_publishable_key.get_secret_value() == "env_pub_key"
    assert settings.supabase_secret_key.get_secret_value() == "env_secret_key"
    assert settings.log_level == "WARNING"
    assert settings.environment == "production"


def test_get_settings_cached() -> None:
    """Verify get_settings returns a cached instance."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
