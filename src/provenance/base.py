"""Extension interface stub for provenance and evidence verification services."""

from typing import Any

from src.services.base import ServiceBoundary


class BaseProvenanceService(ServiceBoundary):
    """Base interface for evidence recording and conflict resolution."""

    def get_service_name(self) -> str:
        return "provenance_service"

    def health_check(self) -> dict[str, Any]:
        return {"service": self.get_service_name(), "status": "scaffolded"}

    def record_verification(
        self,
        subject_type: str,
        subject_id: str,
        evidence_tier: int,
        license_str: str,
    ) -> str:
        """Record verified evidence tier and license attribution."""
        raise NotImplementedError

    def resolve_conflict(self, verification_id: str, resolution_notes: str) -> bool:
        """Resolve evidence conflict or route to human review dossier."""
        raise NotImplementedError
