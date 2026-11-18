"""Mother Intelligence Engine (MIE) Typed Inter-Engine Runtime Contracts.

Authoritative typed Pydantic v2 data contracts reflecting TRD §2.2, §2.3, PRD §4, §5,
and AC-03, AC-04, AC-09, AC-14, AC-15, AC-20 specifications.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

from src.contracts.base import BaseContract
from src.contracts.cdcre import (
    CandidateDiscoveryResult,
    CareerDataCoverage,
    CDCREOutputContract,
)
from src.contracts.cmie import CMIEOutputContract, CMIEVerificationStatus, SourceTrace
from src.contracts.cppae import CPPAEOutput
from src.contracts.pvre import (
    CareerCoverageState,
    PlayerCappedStatus,
    PVREOutputContract,
    PVREReviewDossierContract,
    VerificationStatus,
)
from src.contracts.sice import (
    LineupEvaluationResult,
    ReplacementComparisonOutputContract,
    SICEOutputContract,
)
from src.contracts.tmve import (
    EligibilityOutputContract,
    EligibilityStatus,
    ReviewDossierContract,
    RRCurrentState,
    RRRelationshipState,
    TMVEOutputContract,
)

# ==============================================================================
# Enumerations
# ==============================================================================


class EngineName(StrEnum):
    """Canonical engine identifiers in strict orchestration sequence."""

    PIRE = "PIRE"  # Engine 01: Player Identity Resolution
    TMVE = "TMVE"  # Engine 02: Team Membership Verification
    CDCRE = "CDCRE"  # Engine 03: Career Discovery & Competition Research
    CPPAE = "CPPAE"  # Engine 04: Complete Player Performance Analytics
    CMIE = "CMIE"  # Engine 05: Contextual Match Intelligence
    SICE = "SICE"  # Engine 06: Squad Intelligence & Composition
    PVRE = "PVRE"  # Engine 07: Player Verification & Research Engine


class ExecutionState(StrEnum):
    """Execution status for individual engine adapters within orchestration."""

    SUCCESS = "SUCCESS"
    SKIPPED = "SKIPPED"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    MOCK_FIXTURE = "MOCK_FIXTURE"


class OverallVerificationStatus(StrEnum):
    """Aggregated platform verification status across all seven engines."""

    VERIFIED = "VERIFIED"
    PROVISIONAL = "PROVISIONAL"
    UNVERIFIED = "UNVERIFIED"
    CONFLICT = "CONFLICT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NOT_ASSESSED = "NOT_ASSESSED"


# ==============================================================================
# Engine Execution & Diagnostic Records
# ==============================================================================


class EngineExecutionRecord(BaseContract):
    """Diagnostic tracking record for an individual engine's execution lifecycle."""

    engine: EngineName
    state: ExecutionState
    execution_time_ms: float = Field(ge=0.0)
    adapter_version: str = "v2.2.0"
    records_processed_count: int = Field(default=0, ge=0)
    error_message: str | None = None
    warnings: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ==============================================================================
# Aggregated Verification & Confidence Contracts
# ==============================================================================


class AggregatedVerificationStatus(BaseContract):
    """Holistic multi-dimensional verification state across all platform facets."""

    overall_status: OverallVerificationStatus
    identity_status: str  # RESOLVED, PROVISIONAL, UNRESOLVED
    resolution_tier: int | None = Field(default=None, ge=1, le=4)
    rr_relationship_state: RRRelationshipState
    rr_current_state: RRCurrentState
    ipl_uncapped_eligibility: EligibilityStatus
    player_capped_status: PlayerCappedStatus
    career_coverage_state: CareerCoverageState
    calibrated_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    is_calibrated: bool = False  # AC-15: numeric confidence exposed ONLY if calibrated=True
    requires_human_review: bool = False
    review_reason_codes: list[str] = Field(default_factory=list)
    contradictory_evidence_count: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def enforce_confidence_calibration(self) -> AggregatedVerificationStatus:
        """Enforce Rule AC-15: numeric confidence exposed ONLY when is_calibrated is True."""
        if not self.is_calibrated and self.calibrated_confidence is not None:
            raise ValueError(
                "Rule AC-15 violation: calibrated_confidence must be None when is_calibrated is False"
            )
        return self


class UnifiedProvenanceGraph(BaseContract):
    """Consolidated provenance graph tracking all evidence sources, URLs, and licenses."""

    total_sources_consulted: int = Field(default=0, ge=0)
    source_record_ids: list[str | int] = Field(default_factory=list)
    verification_record_ids: list[str | int] = Field(default_factory=list)
    primary_sources: list[str] = Field(default_factory=list)
    attribution_notices: list[str] = Field(default_factory=list)
    licenses_observed: list[str] = Field(default_factory=list)
    provenance_tiers_summary: dict[str, int] = Field(default_factory=dict)
    cmie_source_traces: list[SourceTrace] = Field(default_factory=list)


class PlayerDataCoverage(BaseContract):
    """Observed local evidence and explicit limits for one MIE player report."""

    records_observed: int = Field(default=0, ge=0)
    competitions_covered: list[str] = Field(default_factory=list)
    seasons_covered: list[str] = Field(default_factory=list)
    missing_periods: list[str] | None = None
    source_completeness: str = "PARTIAL_SNAPSHOT"
    identity_certainty: str = "UNKNOWN"
    unavailable_datasets: list[str] = Field(default_factory=list)
    last_ingestion_timestamp: datetime | None = None
    derived_performance_source_record_ids: list[UUID] = Field(default_factory=list)


# ==============================================================================
# Inbound Request Contract
# ==============================================================================


class CappedStatusEvidence(BaseContract):
    """Source-backed international cap classification supplied to MIE."""

    status: PlayerCappedStatus
    verification_status: VerificationStatus
    source_record_ids: list[str] = Field(default_factory=list)
    verification_record_ids: list[str] = Field(default_factory=list)
    conflicting_source_ids: list[str] = Field(default_factory=list)
    provider_authority_id: str | None = None

    @model_validator(mode="after")
    def validate_cap_evidence(self) -> CappedStatusEvidence:
        if self.verification_status == VerificationStatus.VERIFIED:
            if self.status == PlayerCappedStatus.UNVERIFIED or not self.source_record_ids:
                raise ValueError(
                    "verified cap status requires CAPPED/UNCAPPED and source record IDs"
                )
            if self.conflicting_source_ids:
                raise ValueError("verified cap status cannot contain conflicting source IDs")
        if (
            self.verification_status == VerificationStatus.CONFLICT
            and not self.conflicting_source_ids
        ):
            raise ValueError("conflicting cap evidence requires conflicting source IDs")
        return self


class PlayerIntelligenceRequest(BaseContract):
    """Inbound request contract for end-to-end player intelligence orchestration."""

    request_id: UUID = Field(default_factory=uuid4)
    player_query: str = Field(..., min_length=1, max_length=150)
    user_team_id: UUID | None = None
    target_season_id: UUID = Field(default=UUID("11111111-2222-3333-4444-555555555555"))
    evaluation_date: date = Field(default_factory=date.today)
    research_window_years: int = Field(default=3, ge=1, le=5)
    force_refresh: bool = False
    include_weather_enrichment: bool = False
    context_teams: list[str] = Field(default_factory=list)
    context_competition: str | None = None
    capped_status_evidence: CappedStatusEvidence | None = None

    @field_validator("player_query")
    @classmethod
    def normalize_player_query(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("player_query must contain a non-whitespace character")
        return normalized

    @field_validator("capped_status_evidence", mode="before")
    @classmethod
    def reject_caller_supplied_cap_evidence(cls, value: Any) -> Any:
        """Only the trusted internal source provider may establish capped status."""
        if value is not None:
            raise ValueError("capped status evidence must come from the trusted internal provider")
        return value


# ==============================================================================
# Outbound Consolidated Player Intelligence Report
# ==============================================================================


class PlayerIntelligenceReport(BaseContract):
    """Unified, end-to-end multi-engine intelligence report produced by MIE.

    Strictly complies with TRD §2.2, TRD §2.3, and PRD §4.
    """

    report_version: str = "MIE-2.2.0"
    report_id: UUID = Field(default_factory=uuid4)
    request: PlayerIntelligenceRequest
    player_id: UUID | None = None
    canonical_name: str | None = None

    # Specialized Engine 01–07 Outputs
    identity: dict[str, Any]  # PIRE resolution result
    membership: TMVEOutputContract | dict[str, Any]  # TMVE Dimensions 1 & 2
    eligibility: EligibilityOutputContract | dict[str, Any]  # Dimension 3
    candidate_discovery: CandidateDiscoveryResult | dict[str, Any] | None = None  # CDCRE M2
    career: CareerDataCoverage | CDCREOutputContract | dict[str, Any]  # CDCRE M3
    performance: CPPAEOutput | dict[str, Any]  # CPPAE Performance Profile
    context: CMIEOutputContract | dict[str, Any]  # CMIE Contextual Annotations
    squad_evaluation: SICEOutputContract | LineupEvaluationResult | dict[str, Any] | None = None
    replacement_comparison: ReplacementComparisonOutputContract | dict[str, Any] | None = None
    pvre: PVREOutputContract | dict[str, Any]  # PVRE Engine 07 dossier

    # Unified Meta & Safety Facets
    verification: AggregatedVerificationStatus
    provenance: UnifiedProvenanceGraph
    data_availability: dict[str, str] = Field(default_factory=dict)
    local_source_evidence: list[dict[str, str | None]] = Field(default_factory=list)
    data_coverage: PlayerDataCoverage = Field(default_factory=PlayerDataCoverage)
    safety_dossier: PVREReviewDossierContract | ReviewDossierContract | dict[str, Any] | None = None
    engine_executions: dict[str, EngineExecutionRecord] = Field(default_factory=dict)
    total_execution_time_ms: float = Field(default=0.0, ge=0.0)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_review_required(self) -> bool:
        """Check if report is gated by mandatory review requirements."""
        return (
            self.verification.overall_status
            in (
                OverallVerificationStatus.REVIEW_REQUIRED,
                OverallVerificationStatus.CONFLICT,
            )
            or self.verification.requires_human_review
            or self.safety_dossier is not None
        )

    @property
    def is_rr_incumbent(self) -> bool:
        """Check if player has a verified current or historical RR relationship."""
        rel = self.verification.rr_relationship_state
        return rel in (
            RRRelationshipState.HISTORICAL_RR_APPEARANCE,
            RRRelationshipState.HISTORICAL_RR_SQUAD_ONLY,
            RRRelationshipState.PREVIOUSLY_ASSOCIATED,
        )

    @property
    def is_uncapped_eligible(self) -> bool:
        """Check if player is verified uncapped-eligible under target season rules."""
        return (
            self.verification.ipl_uncapped_eligibility == EligibilityStatus.VERIFIED_ELIGIBLE
            and self.verification.player_capped_status == PlayerCappedStatus.UNCAPPED
        )


PlayerIntelligenceReport.model_rebuild()


__all__ = [
    "EngineName",
    "ExecutionState",
    "OverallVerificationStatus",
    "EngineExecutionRecord",
    "AggregatedVerificationStatus",
    "CMIEVerificationStatus",
    "SourceTrace",
    "UnifiedProvenanceGraph",
    "PlayerDataCoverage",
    "PlayerIntelligenceRequest",
    "PlayerIntelligenceReport",
]
