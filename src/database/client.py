"""Supabase client factory ensuring strict role and key isolation."""

from typing import Any

from src.config.settings import Settings, get_settings
from src.core.exceptions import ConfigurationError, SupabaseConnectionError

Client: Any = None
create_client: Any = None

try:
    import supabase

    Client = getattr(supabase, "Client", None)
    create_client = getattr(supabase, "create_client", None)
except (ImportError, AttributeError):
    Client = None
    create_client = None


class SupabaseClientFactory:
    """Factory for generating Supabase clients with role and key isolation."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def create_client_public(self, settings: Settings | None = None) -> Any:
        """Create public/anonymous client enforcing Row Level Security (RLS)."""
        cfg = settings or self.settings
        if not cfg.supabase_url:
            raise ConfigurationError(
                "SUPABASE_URL is not configured",
                field_name="supabase_url",
            )

        pub_key = (
            cfg.supabase_publishable_key.get_secret_value()
            if hasattr(cfg.supabase_publishable_key, "get_secret_value")
            else str(cfg.supabase_publishable_key)
        )
        if not pub_key:
            raise ConfigurationError(
                "SUPABASE_PUBLISHABLE_KEY is not configured",
                field_name="supabase_publishable_key",
            )

        if create_client is None:
            raise SupabaseConnectionError(
                "Supabase client library is not installed",
                endpoint=cfg.supabase_url,
            )

        try:
            return create_client(cfg.supabase_url, pub_key)
        except Exception as exc:
            raise SupabaseConnectionError(
                f"Failed to initialize public Supabase client: {exc}",
                endpoint=cfg.supabase_url,
            ) from exc

    def create_client_service(self, settings: Settings | None = None) -> Any:
        """Create privileged service-role client for server-side backend operations."""
        cfg = settings or self.settings
        if not cfg.supabase_url:
            raise ConfigurationError(
                "SUPABASE_URL is not configured",
                field_name="supabase_url",
            )

        sec_key = (
            cfg.supabase_secret_key.get_secret_value()
            if hasattr(cfg.supabase_secret_key, "get_secret_value")
            else str(cfg.supabase_secret_key)
        )
        if not sec_key:
            raise ConfigurationError(
                "SUPABASE_SECRET_KEY is not configured for service client",
                field_name="supabase_secret_key",
            )

        if create_client is None:
            raise SupabaseConnectionError(
                "Supabase client library is not installed",
                endpoint=cfg.supabase_url,
            )

        try:
            return create_client(cfg.supabase_url, sec_key)
        except Exception as exc:
            raise SupabaseConnectionError(
                f"Failed to initialize service-role Supabase client: {exc}",
                endpoint=cfg.supabase_url,
            ) from exc
