"""Support Service C Provenance Implementation for CDCRE.

Part of Phase 04A — Career Discovery & Competition Research Engine (Milestone 5).
Implements CDCREProvenanceService extending BaseProvenanceService, enforcing
strict PostgreSQL 16 DDL constraint compliance (chk_subject_type), maintaining
deterministic and tracked provenance records linked to source_records(record_id),
and supporting evidence conflict resolution.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import NAMESPACE_DNS, UUID, uuid4, uuid5

from src.contracts.provenance import VerificationRecord
from src.provenance.base import BaseProvenanceService

logger = logging.getLogger(__name__)

# Canonical namespace for reproducible provenance record UUIDv5 generation
PROVENANCE_NAMESPACE = uuid5(NAMESPACE_DNS, "cdcre.rajasthanroyals.com/provenance")

# Strict PostgreSQL 16 DDL constraint: chk_subject_type
# Valid subject types are strictly:
# 'player_identity', 'player_membership', 'player_eligibility',
# 'match_performance', 'auction_record', 'medical_clearance'
VALID_SUBJECT_TYPES: frozenset[str] = frozenset({
    "player_identity",
    "player_membership",
    "player_eligibility",
    "match_performance",
    "auction_record",
    "medical_clearance",
})


class CDCREProvenanceService(BaseProvenanceService):
    """Authoritative provenance tracking service for CDCRE career and competition evidence.

    Adheres strictly to:
    - PostgreSQL 16 DDL `chk_subject_type` constraint.
    - Foreign key relationship `player_competition_history.provenance_id -> source_records(record_id)`.
    - Zero mislabeling or bypass of verification tiers.
    """

    def __init__(self, db_client: Any = None) -> None:
        """Initialize the CDCRE provenance service with optional DB client."""
        self._db_client = db_client
        self._source_records: dict[UUID, dict[str, Any]] = {}
        self._verification_records: dict[UUID, VerificationRecord] = {}
        self._conflicts: dict[UUID, dict[str, Any]] = {}

    def get_service_name(self) -> str:
        """Return canonical service identifier."""
        return "cdcre_provenance_service"

    def health_check(self) -> dict[str, Any]:
        """Perform service health inspection and return diagnostic status dictionary."""
        return {
            "service": self.get_service_name(),
            "status": "healthy",
            "source_records_count": len(self._source_records),
            "verifications_count": len(self._verification_records),
            "conflicts_count": len(self._conflicts),
            "db_connected": self._db_client is not None,
        }

    def record_verification(
        self,
        subject_type: str,
        subject_id: str,
        evidence_tier: int,
        license_str: str,
        confidence: float = 1.0,
        source_provider: str = "CricSheet / Organizer Canonical Datasets",
        notes: str | None = None,
    ) -> str:
        """Record verified evidence tier and license attribution.

        Strictly enforces PostgreSQL 16 DDL constraint chk_subject_type.
        Valid subject types are strictly:
        'player_identity', 'player_membership', 'player_eligibility',
        'match_performance', 'auction_record', 'medical_clearance'.

        Args:
            subject_type: DDL-validated entity domain. Career records record under
                          'match_performance' or 'player_identity'.
            subject_id: UUID or string identifier of the subject.
            evidence_tier: Evidence reliability tier (1=official/canonical, 2=corroborated, etc.).
            license_str: License attribution string.
            confidence: Confidence score between 0.0 and 1.0.
            source_provider: Origin data provider identifier.
            notes: Optional explanatory notes.

        Returns:
            String representation of the created verification_id UUID.

        Raises:
            ValueError: If subject_type violates chk_subject_type, or if parameters are invalid.
        """
        if not subject_type or not isinstance(subject_type, str):
            raise ValueError(
                f"Invalid subject_type '{subject_type}' violates DDL constraint chk_subject_type. "
                f"Must be a non-empty string in {sorted(VALID_SUBJECT_TYPES)}."
            )

        clean_subject_type = subject_type.strip().lower()

        # STRICT DDL COMPLIANCE: Respect chk_subject_type constraint
        if clean_subject_type not in VALID_SUBJECT_TYPES:
            raise ValueError(
                f"Invalid subject_type '{subject_type}' violates DDL constraint chk_subject_type. "
                f"Valid subject types are strictly: {sorted(VALID_SUBJECT_TYPES)}. "
                f"Career records must be recorded under 'match_performance' or 'player_identity'."
            )

        # Parse subject_id as UUID
        try:
            subject_uuid = UUID(str(subject_id))
        except (ValueError, AttributeError) as exc:
            raise ValueError(f"Invalid subject_id '{subject_id}': must be a valid UUID") from exc

        if evidence_tier < 1:
            raise ValueError(f"evidence_tier must be >= 1, got {evidence_tier}")

        verification_uuid = uuid4()
        now = datetime.now(UTC)

        # Build VerificationRecord contract
        v_record = VerificationRecord(
            verification_id=verification_uuid,
            subject_type=clean_subject_type,
            subject_id=subject_uuid,
            evidence_tier=evidence_tier,
            license=license_str,
            verification_status="VERIFIED",
            confidence=max(0.0, min(1.0, float(confidence))),
            source_provider=source_provider,
            notes=notes,
            created_at=now,
        )

        self._verification_records[verification_uuid] = v_record

        # Synchronize with DB client if provided
        if self._db_client is not None:
            if hasattr(self._db_client, "table"):
                self._db_client.table("verification_records").insert(v_record.model_dump()).execute()
            elif hasattr(self._db_client, "insert"):
                self._db_client.insert("verification_records", v_record.model_dump())

        return str(verification_uuid)

    def record_career_provenance(
        self,
        player_id: UUID,
        competition_id: UUID,
        source_id: str | None = None,
        notes: str | None = None,
    ) -> UUID:
        """Create a deterministic and tracked provenance record linked to source_records(record_id).

        This satisfies the foreign key:
        `player_competition_history.provenance_id REFERENCES source_records(record_id)`.

        Args:
            player_id: Canonical player UUID.
            competition_id: Canonical competition UUID.
            source_id: Optional source identifier tag or external ID.
            notes: Optional contextual notes.

        Returns:
            UUID of the created or retrieved source record.
        """
        if not isinstance(player_id, UUID):
            try:
                player_id = UUID(str(player_id))
            except (ValueError, AttributeError) as exc:
                raise ValueError(f"player_id must be a valid UUID, got {player_id!r}") from exc

        if not isinstance(competition_id, UUID):
            try:
                competition_id = UUID(str(competition_id))
            except (ValueError, AttributeError) as exc:
                raise ValueError(f"competition_id must be a valid UUID, got {competition_id!r}") from exc

        src_tag = str(source_id).strip() if source_id else "canonical_pack"
        provenance_key = f"career:{player_id}:{competition_id}:{src_tag}"
        record_id = uuid5(PROVENANCE_NAMESPACE, provenance_key)

        now = datetime.now(UTC)
        source_record = {
            "record_id": record_id,
            "source_id": uuid5(PROVENANCE_NAMESPACE, "data_source:cdcre_canonical"),
            "external_entity_id": f"{player_id}:{competition_id}",
            "raw_payload": {
                "player_id": str(player_id),
                "competition_id": str(competition_id),
                "source_id": src_tag,
                "notes": notes,
            },
            "payload_sha256": "0" * 64,  # Deterministic placeholder
            "ingestion_timestamp": now,
            "processing_status": "Normalized",
            "parsed_entity_type": "player_competition_history",
            "core_record_id": player_id,
        }

        self._source_records[record_id] = source_record

        if self._db_client is not None:
            if hasattr(self._db_client, "table"):
                self._db_client.table("source_records").insert(source_record).execute()
            elif hasattr(self._db_client, "insert"):
                self._db_client.insert("source_records", source_record)

        return record_id

    def resolve_conflict(self, verification_id: str, resolution_notes: str) -> bool:
        """Resolve evidence conflict or record human review notes.

        Args:
            verification_id: String UUID of verification record in conflict.
            resolution_notes: Resolution justification and decision.

        Returns:
            True if verification record found and updated, False otherwise.
        """
        try:
            v_uuid = UUID(str(verification_id))
        except (ValueError, AttributeError):
            return False

        if v_uuid in self._verification_records:
            rec = self._verification_records[v_uuid]
            self._verification_records[v_uuid] = rec.model_copy(
                update={
                    "verification_status": "VERIFIED",
                    "notes": f"{rec.notes or ''}\nConflict Resolution: {resolution_notes}".strip(),
                }
            )
            self._conflicts[v_uuid] = {
                "verification_id": v_uuid,
                "resolution_notes": resolution_notes,
                "resolved_at": datetime.now(UTC),
            }
            return True

        return False

    def get_verification(self, verification_id: UUID | str) -> VerificationRecord | None:
        """Retrieve a VerificationRecord by its UUID."""
        try:
            v_uuid = UUID(str(verification_id)) if not isinstance(verification_id, UUID) else verification_id
        except (ValueError, AttributeError):
            return None
        return self._verification_records.get(v_uuid)

    def get_source_record(self, record_id: UUID | str) -> dict[str, Any] | None:
        """Retrieve a source record dictionary by its UUID."""
        try:
            r_uuid = UUID(str(record_id)) if not isinstance(record_id, UUID) else record_id
        except (ValueError, AttributeError):
            return None
        return self._source_records.get(r_uuid)


__all__ = [
    "CDCREProvenanceService",
    "PROVENANCE_NAMESPACE",
    "VALID_SUBJECT_TYPES",
]
