"""Extension interface stub for data ingestion services."""

from typing import Any

from src.services.base import ServiceBoundary


class BaseIngestionService(ServiceBoundary):
    """Base interface for raw data ingestion and staging."""

    def get_service_name(self) -> str:
        return "data_ingestion_service"

    def health_check(self) -> dict[str, Any]:
        return {"service": self.get_service_name(), "status": "scaffolded"}

    def stage_raw_payload(self, source_id: str, external_id: str, payload: dict[str, Any]) -> str:
        """Stage raw JSON/CSV payload to immutable landing store."""
        raise NotImplementedError

    def quarantine_payload(self, source_id: str, external_id: str, reason: str) -> None:
        """Quarantine malformed or schema-invalid payload."""
        raise NotImplementedError
