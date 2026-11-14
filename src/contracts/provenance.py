"""Provenance and data ingestion contracts (TRD §11 Domain 1)."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from src.contracts.base import BaseContract


class DataSource(BaseContract):
    """TRD Entity 1: data_sources."""

    source_id: UUID = Field(default_factory=uuid4)
    source_name: str = Field(..., max_length=100)
    source_type: str = Field(..., max_length=50)
    base_url: str | None = Field(default=None, max_length=255)
    license_type: str = Field(..., max_length=50)
    license_status: str = Field(default="UNVERIFIED", max_length=20)
    license_evidence: str | None = None
    update_cadence: str = Field(..., max_length=30)
    data_steward: str = Field(..., max_length=100)
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        allowed = {
            "JSON Feed",
            "CSV Archive",
            "REST API",
            "Web Scraping / Official Feed",
            "Manual Ingestion",
            "External Research",
        }
        if v not in allowed:
            raise ValueError(f"source_type must be one of {allowed}")
        return v

    @field_validator("license_status")
    @classmethod
    def validate_license_status(cls, v: str) -> str:
        allowed = {"VERIFIED", "PARTIALLY_VERIFIED", "UNVERIFIED", "UNAVAILABLE", "RESTRICTED"}
        if v not in allowed:
            raise ValueError(f"license_status must be one of {allowed}")
        return v


class SourceRecord(BaseContract):
    """TRD Entity 2: source_records."""

    record_id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    external_entity_id: str = Field(..., max_length=100)
    raw_payload: dict[str, Any]
    payload_sha256: str = Field(..., min_length=64, max_length=64)
    ingestion_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    processing_status: str = Field(default="Pending", max_length=30)
    error_message: str | None = None
    parsed_entity_type: str | None = Field(default=None, max_length=50)
    core_record_id: UUID | None = None

    @field_validator("processing_status")
    @classmethod
    def validate_processing_status(cls, v: str) -> str:
        allowed = {"Pending", "Parsed", "Normalized", "Failed", "Quarantined"}
        if v not in allowed:
            raise ValueError(f"processing_status must be one of {allowed}")
        return v


class VerificationRecord(BaseContract):
    """TRD Entity 3: verification_records."""

    verification_id: UUID = Field(default_factory=uuid4)
    subject_type: str = Field(..., max_length=30)
    subject_id: UUID
    source_record_id: UUID | None = None
    data_source_id: UUID | None = None
    source_url: str | None = Field(default=None, max_length=500)
    source_provider: str | None = Field(default=None, max_length=100)
    evidence_tier: int | None = None
    retrieval_ts: datetime = Field(default_factory=lambda: datetime.now(UTC))
    license: str | None = Field(default=None, max_length=80)
    verification_status: str = Field(default="PENDING", max_length=30)
    confidence: float | None = None
    original_source_record_id: str | None = Field(default=None, max_length=100)
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("subject_type")
    @classmethod
    def validate_subject_type(cls, v: str) -> str:
        allowed = {
            "player_identity",
            "player_membership",
            "player_eligibility",
            "career_participation",
            "source_record",
            "team_participation",
        }
        if v not in allowed:
            raise ValueError(f"subject_type must be one of {allowed}")
        return v

    @field_validator("evidence_tier")
    @classmethod
    def validate_evidence_tier(cls, v: int | None) -> int | None:
        if v is not None and not (1 <= v <= 5):
            raise ValueError("evidence_tier must be between 1 and 5")
        return v

    @field_validator("verification_status")
    @classmethod
    def validate_verification_status(cls, v: str) -> str:
        allowed = {"PENDING", "VERIFIED", "UNVERIFIED", "CONFLICT"}
        if v not in allowed:
            raise ValueError(f"verification_status must be one of {allowed}")
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float | None) -> float | None:
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v
