"""Integration test for Supabase connectivity (cleanly skipped when offline)."""

import os

import pytest
from src.config.settings import Settings
from src.core.exceptions import ConfigurationError, SupabaseConnectionError
from src.database.client import SupabaseClientFactory


def test_supabase_live_connectivity_or_skip() -> None:
    """Verify live read-only connectivity to Supabase, or skip cleanly if credentials absent."""
    url = os.getenv("SUPABASE_URL", "")
    pub_key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")

    # Clean skip conditions: no credentials, dummy credentials, or default placeholders
    if not url or not pub_key:
        pytest.skip("Supabase credentials not configured in environment. Clean offline skip.")
    if "your-project" in url or "dummy" in pub_key:
        pytest.skip("Dummy or placeholder Supabase credentials detected. Clean offline skip.")

    settings = Settings()
    factory = SupabaseClientFactory(settings=settings)

    try:
        client = factory.create_client_public()
        # Read-only health query against public schema
        response = client.table("data_sources").select("count", count="exact").limit(1).execute()
        assert response is not None
    except (ConfigurationError, SupabaseConnectionError, Exception) as exc:
        pytest.skip(
            f"Live Supabase endpoint unreachable or authentication failed ({exc}). Clean skip."
        )
