"""Unit tests for EventPublisher protocol and ServiceBoundary ABC."""

from typing import Any

import pytest
from src.ingestion.base import BaseIngestionService
from src.provenance.base import BaseProvenanceService
from src.quality.base import BaseDataQualityService
from src.services.base import ServiceBoundary
from src.services.publisher import EventPublisher


class MockEventPublisher:
    """Mock implementation fulfilling EventPublisher protocol."""

    def __init__(self) -> None:
        self.published: list[tuple[str, dict[str, Any]]] = []
        self.is_closed: bool = False

    def publish(self, topic: str, event: dict[str, Any]) -> None:
        self.published.append((topic, event))

    def close(self) -> None:
        self.is_closed = True


class MockService(ServiceBoundary):
    """Concrete implementation of ServiceBoundary."""

    def get_service_name(self) -> str:
        return "mock_test_service"

    def health_check(self) -> dict[str, Any]:
        return {"status": "healthy", "service": self.get_service_name()}


def test_event_publisher_protocol() -> None:
    """Verify that MockEventPublisher satisfies runtime checkable EventPublisher protocol."""
    publisher = MockEventPublisher()
    assert isinstance(publisher, EventPublisher)

    publisher.publish("events.player.created", {"player_id": "p-1"})
    assert len(publisher.published) == 1
    assert publisher.published[0][0] == "events.player.created"

    publisher.close()
    assert publisher.is_closed is True


def test_service_boundary_lifecycle() -> None:
    """Verify ServiceBoundary methods."""
    service = MockService()
    assert service.get_service_name() == "mock_test_service"
    health = service.health_check()
    assert health["status"] == "healthy"
    assert health["service"] == "mock_test_service"


def test_extension_stubs_satisfy_boundary() -> None:
    """Verify that ingestion, quality, and provenance stubs satisfy ServiceBoundary."""
    services: list[ServiceBoundary] = [
        BaseIngestionService(),
        BaseDataQualityService(),
        BaseProvenanceService(),
    ]

    expected_names = [
        "data_ingestion_service",
        "data_quality_service",
        "provenance_service",
    ]

    for svc, expected_name in zip(services, expected_names, strict=False):
        assert svc.get_service_name() == expected_name
        health = svc.health_check()
        assert health["status"] == "scaffolded"


def test_extension_stubs_raise_not_implemented() -> None:
    """Verify that unimplemented extension stub methods raise NotImplementedError."""
    ing = BaseIngestionService()
    with pytest.raises(NotImplementedError):
        ing.stage_raw_payload("s1", "e1", {})
    with pytest.raises(NotImplementedError):
        ing.quarantine_payload("s1", "e1", "reason")

    dq = BaseDataQualityService()
    with pytest.raises(NotImplementedError):
        dq.validate_invariants("players", [])
    with pytest.raises(NotImplementedError):
        dq.reconcile_innings_deliveries("inn-1")

    prov = BaseProvenanceService()
    with pytest.raises(NotImplementedError):
        prov.record_verification("player", "p1", 1, "ODC-By")
    with pytest.raises(NotImplementedError):
        prov.resolve_conflict("ver-1", "notes")
