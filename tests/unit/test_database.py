"""Unit tests for Supabase client factory, repository interface, and in-memory mock."""

from typing import Any

import pytest
from pydantic import SecretStr
from src.config.settings import Settings
from src.core.exceptions import ConfigurationError
from src.database.client import SupabaseClientFactory
from src.database.repository import BaseRepository

from tests.fixtures.mock_supabase import MockSupabaseClient


def test_factory_missing_url() -> None:
    """Verify ConfigurationError raised when SUPABASE_URL is not set."""
    settings = Settings(supabase_url="", supabase_publishable_key=SecretStr("key"))
    factory = SupabaseClientFactory(settings=settings)
    with pytest.raises(ConfigurationError) as exc_info:
        factory.create_client_public()
    assert exc_info.value.details.get("field_name") == "supabase_url"


def test_factory_missing_publishable_key() -> None:
    """Verify ConfigurationError raised when publishable key is not set."""
    settings = Settings(
        supabase_url="https://test.supabase.co", supabase_publishable_key=SecretStr("")
    )
    factory = SupabaseClientFactory(settings=settings)
    with pytest.raises(ConfigurationError) as exc_info:
        factory.create_client_public()
    assert exc_info.value.details.get("field_name") == "supabase_publishable_key"


def test_factory_missing_service_key() -> None:
    """Verify ConfigurationError raised when secret key is missing for service client."""
    settings = Settings(supabase_url="https://test.supabase.co", supabase_secret_key=SecretStr(""))
    factory = SupabaseClientFactory(settings=settings)
    with pytest.raises(ConfigurationError) as exc_info:
        factory.create_client_service()
    assert exc_info.value.details.get("field_name") == "supabase_secret_key"


def test_base_repository_raises_not_implemented() -> None:
    """Verify abstract methods on BaseRepository raise NotImplementedError."""
    assert "list" in BaseRepository.__abstractmethods__
    assert "list_all" in BaseRepository.__abstractmethods__

    class IncompleteRepository(BaseRepository[dict[str, Any]]):
        def get_by_id(self, id: str) -> Any:
            return super().get_by_id(id)  # type: ignore[safe-super]

        def list_all(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
            return super().list_all(limit, offset)  # type: ignore[safe-super]

        def list(self, limit: int = 100, offset: int = 0, **filters: Any) -> list[dict[str, Any]]:
            return super().list(limit, offset, **filters)  # type: ignore[safe-super]

        def create(self, entity: dict[str, Any]) -> dict[str, Any]:
            return super().create(entity)  # type: ignore[safe-super]

        def update(self, id: str, entity: dict[str, Any]) -> dict[str, Any]:
            return super().update(id, entity)  # type: ignore[safe-super]

        def delete(self, id: str) -> bool:
            return super().delete(id)  # type: ignore[safe-super]

    repo = IncompleteRepository()
    with pytest.raises(NotImplementedError):
        repo.get_by_id("id-1")
    with pytest.raises(NotImplementedError):
        repo.list_all()
    with pytest.raises(NotImplementedError):
        repo.list()
    with pytest.raises(NotImplementedError):
        repo.create({})
    with pytest.raises(NotImplementedError):
        repo.update("id-1", {})
    with pytest.raises(NotImplementedError):
        repo.delete("id-1")


def test_mock_supabase_client_crud() -> None:
    """Verify CRUD operations against in-memory MockSupabaseClient."""
    client = MockSupabaseClient()

    # 1. Insert records
    client.table("players").insert(
        [
            {"id": "p1", "name": "Synthetic Player A", "role": "Batter"},
            {"id": "p2", "name": "Synthetic Player B", "role": "Bowler"},
            {"id": "p3", "name": "Synthetic Player C", "role": "All-rounder"},
        ]
    ).execute()

    # 2. Select with eq filter
    res = client.table("players").select().eq("id", "p1").execute()
    assert len(res.data) == 1
    assert res.data[0]["name"] == "Synthetic Player A"

    # 3. Select with in_ filter
    res_in = client.table("players").select().in_("id", ["p1", "p2"]).execute()
    assert len(res_in.data) == 2

    # 4. Update
    client.table("players").eq("id", "p2").update({"name": "Synthetic Bowler Updated"}).execute()
    res_updated = client.table("players").select().eq("id", "p2").execute()
    assert res_updated.data[0]["name"] == "Synthetic Bowler Updated"

    # 5. Delete
    client.table("players").eq("id", "p3").delete().execute()
    res_all = client.table("players").select().execute()
    assert len(res_all.data) == 2
    assert not any(p["id"] == "p3" for p in res_all.data)


def test_mock_supabase_client_order_sorting() -> None:
    """Verify MockQueryBuilder.order() properly sorts ascending and descending."""
    client = MockSupabaseClient()
    client.table("scores").insert(
        [
            {"id": "s1", "player": "Player A", "score": 50},
            {"id": "s2", "player": "Player B", "score": 90},
            {"id": "s3", "player": "Player C", "score": 10},
        ]
    ).execute()

    # Ascending
    res_asc = client.table("scores").select().order("score", desc=False).execute()
    assert [r["score"] for r in res_asc.data] == [10, 50, 90]

    # Descending
    res_desc = client.table("scores").select().order("score", desc=True).execute()
    assert [r["score"] for r in res_desc.data] == [90, 50, 10]

    # Order combined with limit
    res_top2 = client.table("scores").select().order("score", desc=True).limit(2).execute()
    assert [r["score"] for r in res_top2.data] == [90, 50]
