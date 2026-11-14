"""Extension interface stub for data quality and coverage services."""

from typing import Any

from src.services.base import ServiceBoundary


class BaseDataQualityService(ServiceBoundary):
    """Base interface for data quality validation and delivery reconciliation."""

    def get_service_name(self) -> str:
        return "data_quality_service"

    def health_check(self) -> dict[str, Any]:
        return {"service": self.get_service_name(), "status": "scaffolded"}

    def validate_invariants(self, table_name: str, records: list[dict[str, Any]]) -> bool:
        """Validate relational invariants and null-safety rules."""
        raise NotImplementedError

    def reconcile_innings_deliveries(self, innings_id: str) -> dict[str, Any]:
        """Reconcile scorecard totals against aggregated delivery events."""
        raise NotImplementedError
