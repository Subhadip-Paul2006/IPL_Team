"""Repository adapters for the existing provenance tables.

The Supabase adapter persists rows in the existing ``data_sources``,
``source_records``, and ``verification_records`` schema. The in-memory adapter is
for deterministic tests and offline development only; it is never advertised as
durable persistence.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol
from uuid import UUID

from src.contracts.provenance import DataSource, SourceRecord, VerificationRecord


class EvidenceRepository(Protocol):
    """Persistence and lookup interface over the established provenance entities."""

    durable: bool

    def register_data_source(self, source: DataSource) -> DataSource: ...

    def create_source_record(self, record: SourceRecord) -> SourceRecord: ...

    def get_data_source(self, source_id: UUID) -> DataSource | None: ...

    def get_source_record(self, record_id: UUID) -> SourceRecord | None: ...

    def get_source_records_by_key(
        self, source_id: UUID, external_entity_id: str
    ) -> list[SourceRecord]: ...

    def get_verification_record(self, verification_id: UUID) -> VerificationRecord | None: ...

    def list_verification_records(
        self, subject_type: str, subject_id: UUID
    ) -> list[VerificationRecord]: ...


class InMemoryEvidenceRepository:
    """Non-durable repository for isolated tests and explicitly offline runs."""

    durable = False

    def __init__(self) -> None:
        self._sources: dict[UUID, DataSource] = {}
        self._sources_by_name: dict[str, UUID] = {}
        self._records: dict[UUID, SourceRecord] = {}
        self._record_keys: dict[tuple[UUID, str, str], UUID] = {}
        self._verifications: dict[UUID, VerificationRecord] = {}

    def register_data_source(self, source: DataSource) -> DataSource:
        existing_id = self._sources_by_name.get(source.source_name)
        if existing_id is not None:
            return self._sources[existing_id]
        self._sources[source.source_id] = source
        self._sources_by_name[source.source_name] = source.source_id
        return source

    def create_source_record(self, record: SourceRecord) -> SourceRecord:
        if record.source_id not in self._sources:
            raise ValueError("source record references an unregistered data source")
        key = (record.source_id, record.external_entity_id, record.payload_sha256.lower())
        existing_id = self._record_keys.get(key)
        if existing_id is not None:
            return self._records[existing_id]
        self._records[record.record_id] = record
        self._record_keys[key] = record.record_id
        return record

    def get_data_source(self, source_id: UUID) -> DataSource | None:
        return self._sources.get(source_id)

    def get_source_record(self, record_id: UUID) -> SourceRecord | None:
        return self._records.get(record_id)

    def get_source_records_by_key(
        self, source_id: UUID, external_entity_id: str
    ) -> list[SourceRecord]:
        return [
            record
            for record in self._records.values()
            if record.source_id == source_id and record.external_entity_id == external_entity_id
        ]

    def get_verification_record(self, verification_id: UUID) -> VerificationRecord | None:
        return self._verifications.get(verification_id)

    def list_verification_records(
        self, subject_type: str, subject_id: UUID
    ) -> list[VerificationRecord]:
        return [
            record
            for record in self._verifications.values()
            if record.subject_type == subject_type and record.subject_id == subject_id
        ]

    def add_verification_record(self, record: VerificationRecord) -> None:
        """Insert a fixture verification row for tests; production writes use ingestion."""
        self._verifications[record.verification_id] = record


class SupabaseEvidenceRepository:
    """Persistence adapter for the existing Supabase tables and unique constraints."""

    durable = True

    def __init__(self, client: Any) -> None:
        if client is None or not callable(getattr(client, "table", None)):
            raise TypeError("SupabaseEvidenceRepository requires a table-capable client")
        self._client = client

    def register_data_source(self, source: DataSource) -> DataSource:
        existing = self._select_one("data_sources", "source_name", source.source_name)
        if existing is not None:
            return DataSource.model_validate(existing)
        try:
            response = (
                self._client.table("data_sources").insert(source.model_dump(mode="json")).execute()
            )
        except Exception:
            # Handle a concurrent registration using the schema's uq_data_sources_name.
            existing = self._select_one("data_sources", "source_name", source.source_name)
            if existing is None:
                raise
            return DataSource.model_validate(existing)
        rows = self._rows(response)
        if not rows:
            existing = self._select_one("data_sources", "source_name", source.source_name)
            if existing is None:
                raise RuntimeError("data source insert returned no persisted row")
            rows = [existing]
        return DataSource.model_validate(rows[0])

    def create_source_record(self, record: SourceRecord) -> SourceRecord:
        if self.get_data_source(record.source_id) is None:
            raise ValueError("source record references an unregistered data source")
        query = (
            self._client.table("source_records")
            .select("*")
            .eq("source_id", str(record.source_id))
            .eq("external_entity_id", record.external_entity_id)
            .eq("payload_sha256", record.payload_sha256.lower())
            .limit(1)
        )
        rows = self._rows(query.execute())
        if rows:
            return SourceRecord.model_validate(rows[0])

        try:
            response = (
                self._client.table("source_records")
                .insert(record.model_dump(mode="json"))
                .execute()
            )
        except Exception:
            # The schema's uq_source_payload_hash is the idempotency boundary.
            rows = self._rows(query.execute())
            if not rows:
                raise
            return SourceRecord.model_validate(rows[0])
        rows = self._rows(response)
        if not rows:
            rows = self._rows(query.execute())
        if not rows:
            raise RuntimeError("source record insert returned no persisted row")
        return SourceRecord.model_validate(rows[0])

    def get_data_source(self, source_id: UUID) -> DataSource | None:
        row = self._select_one("data_sources", "source_id", str(source_id))
        return DataSource.model_validate(row) if row is not None else None

    def get_source_record(self, record_id: UUID) -> SourceRecord | None:
        row = self._select_one("source_records", "record_id", str(record_id))
        return SourceRecord.model_validate(row) if row is not None else None

    def get_source_records_by_key(
        self, source_id: UUID, external_entity_id: str
    ) -> list[SourceRecord]:
        response = (
            self._client.table("source_records")
            .select("*")
            .eq("source_id", str(source_id))
            .eq("external_entity_id", external_entity_id)
            .execute()
        )
        return [SourceRecord.model_validate(row) for row in self._rows(response)]

    def get_verification_record(self, verification_id: UUID) -> VerificationRecord | None:
        row = self._select_one("verification_records", "verification_id", str(verification_id))
        return VerificationRecord.model_validate(row) if row is not None else None

    def list_verification_records(
        self, subject_type: str, subject_id: UUID
    ) -> list[VerificationRecord]:
        response = (
            self._client.table("verification_records")
            .select("*")
            .eq("subject_type", subject_type)
            .eq("subject_id", str(subject_id))
            .execute()
        )
        return [VerificationRecord.model_validate(row) for row in self._rows(response)]

    def _select_one(self, table_name: str, field: str, value: str) -> dict[str, Any] | None:
        response = self._client.table(table_name).select("*").eq(field, value).limit(1).execute()
        rows = self._rows(response)
        return rows[0] if rows else None

    @staticmethod
    def _rows(response: Any) -> list[dict[str, Any]]:
        data = getattr(response, "data", None)
        if isinstance(data, Mapping):
            return [dict(data)]
        if isinstance(data, list):
            return [dict(row) for row in data if isinstance(row, Mapping)]
        return []


__all__ = ["EvidenceRepository", "InMemoryEvidenceRepository", "SupabaseEvidenceRepository"]
