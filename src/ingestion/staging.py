"""Immutable raw staging and quarantine service.

Part of Phase 1 Historical Data Pipeline Closure (Track A).
Implements BaseIngestionService with bitwise SHA-256 verification, immutable landing storage,
and structured quarantine tracking for malformed or rule-violating payloads.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from src.contracts.provenance import SourceRecord
from src.ingestion.base import BaseIngestionService


def compute_payload_sha256(payload: dict[str, Any] | str | bytes) -> str:
    """Compute deterministic SHA-256 for a JSON payload or string."""
    if isinstance(payload, bytes):
        raw_bytes = payload
    elif isinstance(payload, str):
        raw_bytes = payload.encode("utf-8")
    else:
        # Deterministic canonical JSON representation
        raw_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw_bytes).hexdigest()


class ImmutableStagingService(BaseIngestionService):
    """Immutable staging lake with cryptographic validation and quarantine pipeline."""

    def __init__(self, staging_root: Path | str | None = None) -> None:
        self.staging_root = Path(staging_root) if staging_root else None
        self._staged_records: dict[str, SourceRecord] = {}
        self._quarantined_records: list[dict[str, Any]] = []

    def get_service_name(self) -> str:
        return "immutable_staging_service"

    def health_check(self) -> dict[str, Any]:
        return {
            "service": self.get_service_name(),
            "status": "operational",
            "staged_count": len(self._staged_records),
            "quarantined_count": len(self._quarantined_records),
        }

    def stage_raw_payload(
        self,
        source_id: str,
        external_id: str,
        payload: dict[str, Any],
        expected_sha256: str | None = None,
        entity_type: str = "match_json",
    ) -> str:
        """Stage raw JSON payload to immutable landing store with SHA-256 validation."""
        computed_hash = compute_payload_sha256(payload)

        # Integrity Check
        if expected_sha256 and computed_hash.lower() != expected_sha256.lower():
            reason = f"Checksum mismatch: expected {expected_sha256}, computed {computed_hash}"
            self.quarantine_payload(source_id, external_id, reason, payload=payload)
            raise ValueError(reason)

        try:
            source_uuid = UUID(source_id)
        except ValueError:
            source_uuid = uuid4()

        record_id = uuid4()
        record = SourceRecord(
            record_id=record_id,
            source_id=source_uuid,
            external_entity_id=external_id,
            raw_payload=payload,
            payload_sha256=computed_hash,
            processing_status="Pending",
            parsed_entity_type=entity_type,
        )

        self._staged_records[str(record_id)] = record

        # Optional filesystem landing
        if self.staging_root:
            landing_dir = self.staging_root / "raw" / str(source_uuid)
            landing_dir.mkdir(parents=True, exist_ok=True)
            landing_file = landing_dir / f"{external_id}_{computed_hash[:12]}.json"
            if not landing_file.exists():
                with landing_file.open("w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2)

        return str(record_id)

    def quarantine_payload(
        self,
        source_id: str,
        external_id: str,
        reason: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Quarantine malformed or schema-invalid payload with audit record."""
        quarantine_entry = {
            "quarantine_id": str(uuid4()),
            "source_id": str(source_id),
            "external_id": str(external_id),
            "reason": reason,
            "payload_sha256": compute_payload_sha256(payload) if payload else None,
            "raw_payload": payload,
        }
        self._quarantined_records.append(quarantine_entry)

        # Optional filesystem quarantine landing
        if self.staging_root and payload:
            quarantine_dir = self.staging_root / "quarantine"
            quarantine_dir.mkdir(parents=True, exist_ok=True)
            quarantine_file = quarantine_dir / f"{external_id}_quarantined.json"
            with quarantine_file.open("w", encoding="utf-8") as f:
                json.dump({"quarantine_entry": quarantine_entry, "payload": payload}, f, indent=2)

    def get_staged_record(self, record_id: str) -> SourceRecord | None:
        """Retrieve staged source record by UUID."""
        return self._staged_records.get(str(record_id))

    def get_all_staged(self) -> list[SourceRecord]:
        """Retrieve all currently staged source records."""
        return list(self._staged_records.values())

    def get_all_quarantined(self) -> list[dict[str, Any]]:
        """Retrieve all quarantine audit records."""
        return list(self._quarantined_records)
