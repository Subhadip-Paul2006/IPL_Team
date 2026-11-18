"""Player Verification & Research Engine (PVRE) inter-engine runtime contracts.

Authoritative contracts reflecting TRD §9.5, §9.6, PRD FR-PV1..FR-PV8, and
ORIGINAL_REQUEST R1..R4 specifications for Rajasthan Royals squad intelligence platform.
"""

from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from src.contracts.base import BaseContract

# ==============================================================================
# Domain Taxonomy & Lifecycle Enumerations
# ==============================================================================


class ResearchMode(StrEnum):
    """Operational modes for PVRE execution (TRD §9.1, §9.2)."""

    MODE_A = "MODE_A"
    MODE_B = "MODE_B"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class RouteStatus(StrEnum):
    """Deterministic routing destination status (TRD §9.2, AC-24)."""

    ROUTED_RR_INCUMBENT = "ROUTED_RR_INCUMBENT"
    ROUTED_UNCAPPED_CANDIDATE = "ROUTED_UNCAPPED_CANDIDATE"
    ROUTED_SAFETY_REVIEW = "ROUTED_SAFETY_REVIEW"
    ROUTED_OUT_OF_SCOPE = "ROUTED_OUT_OF_SCOPE"


class ReplaceabilitySignal(StrEnum):
    """Analytical replaceability synthesis signals for incumbent players (TRD §9.3.3, AC-27)."""

    RETAIN_SIGNAL = "RETAIN_SIGNAL"
    MONITOR_SIGNAL = "MONITOR_SIGNAL"
    POTENTIALLY_REPLACEABLE = "POTENTIALLY_REPLACEABLE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class CareerCoverageState(StrEnum):
    """Mutually exclusive career data coverage states (TRD §5.3, §9.4, DATA_DICTIONARY §9.2)."""

    COMPLETE_WITHIN_VERIFIED_SOURCES = "COMPLETE_WITHIN_VERIFIED_SOURCES"
    PARTIAL_COVERAGE = "PARTIAL_COVERAGE"
    UNKNOWN = "UNKNOWN"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class PlayerCappedStatus(StrEnum):
    """Player international cap status taxonomy (TRD §9.4, AI_INSTRUCTIONS R13)."""

    CAPPED = "CAPPED"
    UNCAPPED = "UNCAPPED"
    UNVERIFIED = "UNVERIFIED"


class PVREVerificationStatus(StrEnum):
    """Discrete verification states for individual assertions and datasets (ORIGINAL_REQUEST R1)."""

    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    UNKNOWN = "UNKNOWN"
    CONFLICT = "CONFLICT"
    NOT_COMPUTABLE = "NOT_COMPUTABLE"
    DATASET_UNAVAILABLE = "DATASET_UNAVAILABLE"


# Backward-compatible alias for verification status
VerificationStatus = PVREVerificationStatus


class PVREReviewStatus(StrEnum):
    """Review gate status for PVRE executions and dossiers (TRD §9.5, PRD FR-PV7)."""

    CLEAR = "CLEAR"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REJECTED = "REJECTED"


class SourceReliability(StrEnum):
    """Evidence source reliability taxonomy for multi-source reconciliation (DATA_SOURCE_REGISTER §1)."""

    TIER_1_OFFICIAL = "TIER_1_OFFICIAL"
    TIER_2_COMMERCIAL_ARCHIVE = "TIER_2_COMMERCIAL_ARCHIVE"
    TIER_3_COMMUNITY_SCRAPE = "TIER_3_COMMUNITY_SCRAPE"
    TIER_4_MANUAL_ESTIMATE = "TIER_4_MANUAL_ESTIMATE"


class EvidenceTier(StrEnum):
    """Evidence tier classification for provenance and confidence weighting (DATA_SOURCE_REGISTER §1)."""

    TIER_1_OFFICIAL = "TIER_1_OFFICIAL"
    TIER_2_COMMERCIAL = "TIER_2_COMMERCIAL"
    TIER_3_MEDIA = "TIER_3_MEDIA"
    TIER_4_CROWDSOURCED = "TIER_4_CROWDSOURCED"


# ==============================================================================
# Core Runtime Contracts
# ==============================================================================


class PVRERequestContract(BaseContract):
    """Input request contract for Player Verification & Research Engine (TRD §9.6.1)."""

    contract_version: str = "PVRE-2.2.0"
    research_run_id: UUID
    player_query: str
    player_id: UUID | None = None
    canonical_name: str
    identity_status: str
    rr_relationship_state: str
    rr_current_state: str
    player_capped_status: str
    ipl_uncapped_eligibility: str
    target_season_id: UUID
    evaluation_date: date
    research_window_years: int = Field(default=3, ge=2, le=3)
    force_refresh: bool = False


class PVREOutputContract(BaseContract):
    """Authoritative 26-field PVRE Output Contract (TRD §9.6.2, PRD FR-PV8)."""

    # 1. Governance & Run Identification
    contract_version: str = "PVRE-2.2.0"
    research_run_id: UUID
    player_id: UUID | None = None
    canonical_name: str
    identity_status: str

    # 2. Routing & Mode Selection
    research_mode: str
    route_status: str
    evaluation_date: date
    target_season_id: UUID

    # 3. Membership & Eligibility States
    rr_relationship_state: str
    rr_current_state: str
    player_capped_status: str
    ipl_uncapped_eligibility: str

    # 4. Research Windows
    research_window_start: date
    research_window_end: date

    # 5. Career Coverage State
    career_coverage_state: str

    # 6. Domain Profiles & Assessments
    rr_historical_profile: dict[str, Any] | None = None
    recent_global_performance: dict[str, Any] | None = None
    complete_career_profile: dict[str, Any] | None = None
    replaceability_assessment: dict[str, Any] | None = None

    # 7. Coverage, Provenance & Quality
    competition_coverage: dict[str, str] = Field(default_factory=dict)
    source_record_ids: list[UUID | int] = Field(default_factory=list)
    verification_record_ids: list[UUID | int] = Field(default_factory=list)
    review_status: str = "CLEAR"
    review_reason_codes: list[str] = Field(default_factory=list)
    data_quality_summary: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_research_window(self) -> "PVREOutputContract":
        """Validate research window start is not after research window end."""
        if self.research_window_start > self.research_window_end:
            raise ValueError(
                f"research_window_start ({self.research_window_start}) must not be after "
                f"research_window_end ({self.research_window_end})"
            )
        return self


class ReviewDossierContract(BaseContract):
    """Structured safety review dossier generated when claims require human review (TRD §9.5)."""

    contract_version: str = "DOSSIER-1.0.0"
    dossier_id: UUID
    subject_type: str = "player_research"
    subject_id: UUID | None = None
    review_status: str = "REVIEW_REQUIRED"
    review_reason_codes: list[str] = Field(default_factory=list)
    unresolved_claims: list[dict[str, Any]] = Field(default_factory=list)
    conflicting_source_ids: list[UUID | int] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    recommended_manual_checks: list[str] = Field(default_factory=list)


# Domain-specific alias for safety review dossiers
PVREReviewDossierContract = ReviewDossierContract


class ReplacementCandidateEvidence(BaseContract):
    """Normalized candidate research record for SICE replacement comparison (ORIGINAL_REQUEST R4)."""

    candidate_player_id: UUID
    canonical_name: str
    age_at_evaluation: float = Field(ge=14.0, le=55.0)
    primary_role: str
    secondary_role: str | None = None
    batting_hand: str | None = None
    bowling_style: str | None = None
    ipl_uncapped_eligibility: str
    verified_policy_id: UUID
    domestic_t20_metrics: dict[str, Any] = Field(default_factory=dict)
    first_class_metrics: dict[str, Any] | None = None
    list_a_metrics: dict[str, Any] | None = None
    sample_indicators: dict[str, int] = Field(default_factory=dict)
    evidence_tier: int = Field(default=1, ge=1, le=4)
    career_coverage_state: str = "COMPLETE_WITHIN_VERIFIED_SOURCES"
    missing_competitions: list[str] = Field(default_factory=list)
    provenance_verification_ids: list[UUID] = Field(default_factory=list)


# ==============================================================================
# Additional Typed Domain Contracts (ORIGINAL_REQUEST R1)
# ==============================================================================


class PlayerResearchRequest(BaseContract):
    """Typed request contract for player research and verification workflow (ORIGINAL_REQUEST R1)."""

    contract_version: str = "PVRE-2.2.0"
    research_run_id: UUID
    player_query: str
    player_id: UUID | None = None
    canonical_name: str
    identity_status: str = "RESOLVED"
    rr_relationship_state: str = "RR_RELATIONSHIP_UNKNOWN"
    rr_current_state: str = "UNKNOWN"
    player_capped_status: str = "UNVERIFIED"
    ipl_uncapped_eligibility: str = "NOT_ASSESSED"
    target_season_id: UUID
    evaluation_date: date
    research_window_years: int = Field(default=3, ge=2, le=3)
    force_refresh: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class PlayerResearchOutput(PVREOutputContract):
    """Typed output contract for player research and verification workflow (ORIGINAL_REQUEST R1)."""


class ReplacementResearchRequest(BaseContract):
    """Request contract for Mode B replacement candidate research (ORIGINAL_REQUEST R1, R4)."""

    contract_version: str = "PVRE-2.2.0"
    research_run_id: UUID
    target_season_id: UUID
    evaluation_date: date
    target_role: str
    secondary_role: str | None = None
    batting_hand: str | None = None
    bowling_style: str | None = None
    max_age: float | None = None
    min_domestic_matches: int = Field(default=5, ge=0)
    must_be_uncapped: bool = True
    candidate_pool_limit: int = Field(default=50, ge=1, le=500)
    force_refresh: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class VerificationClaim(BaseContract):
    """Individual fact claim subject to verification (ORIGINAL_REQUEST R1)."""

    claim_id: UUID
    subject_id: UUID | None = None
    canonical_name: str
    claim_type: str
    claimed_value: Any
    source_id: UUID | int | str
    source_tier: EvidenceTier | str
    retrieval_timestamp: datetime
    verification_status: PVREVerificationStatus | str = PVREVerificationStatus.UNVERIFIED
    conflict_ids: list[UUID] = Field(default_factory=list)


class EvidenceSource(BaseContract):
    """External or internal evidence source metadata (ORIGINAL_REQUEST R1, R2)."""

    source_id: str
    source_name: str
    tier: EvidenceTier | str
    reliability: SourceReliability | str
    coverage_competitions: list[str] = Field(default_factory=list)
    granularity: str = "BALL_BY_BALL"
    balls_per_over_default: int = 6
    licence: str = "ODC-By v1.0"
    is_active: bool = True
    is_mockable: bool = True


class ResearchConflict(BaseContract):
    """Preserved conflicting claims between evidence sources (ORIGINAL_REQUEST R1, TRD §9.5)."""

    conflict_id: UUID
    claim_type: str
    subject_name: str
    subject_id: UUID | None = None
    primary_source_id: UUID | int | str
    primary_value: Any
    primary_tier: EvidenceTier | str
    conflicting_source_id: UUID | int | str
    conflicting_value: Any
    conflicting_tier: EvidenceTier | str
    detected_at: datetime
    resolution_status: str = "UNRESOLVED"
    review_dossier_id: UUID | None = None


class CareerVerification(BaseContract):
    """Verification summary of a player's career across formats (ORIGINAL_REQUEST R1)."""

    verification_id: UUID
    player_id: UUID | None = None
    canonical_name: str
    capped_status: PlayerCappedStatus | str
    senior_international_caps: int = Field(default=0, ge=0)
    youth_international_caps: int = Field(default=0, ge=0)
    ipl_appearances: int = Field(default=0, ge=0)
    rr_appearances: int = Field(default=0, ge=0)
    rr_squad_seasons: int = Field(default=0, ge=0)
    domestic_t20_appearances: int = Field(default=0, ge=0)
    first_class_appearances: int = Field(default=0, ge=0)
    list_a_appearances: int = Field(default=0, ge=0)
    coverage_state: CareerCoverageState | str
    verification_status: PVREVerificationStatus | str
    verified_at: datetime


class ResearchCoverage(BaseContract):
    """Research coverage details across competitions and datasets (ORIGINAL_REQUEST R1)."""

    evaluation_date: date
    coverage_state: CareerCoverageState | str
    competitions_searched: list[str] = Field(default_factory=list)
    competitions_verified: list[str] = Field(default_factory=list)
    competitions_unavailable: list[str] = Field(default_factory=list)
    missing_competitions: list[str] = Field(default_factory=list)
    total_matches_indexed: int = Field(default=0, ge=0)
    date_range_start: date | None = None
    date_range_end: date | None = None


__all__ = [
    # Enums
    "ResearchMode",
    "RouteStatus",
    "ReplaceabilitySignal",
    "CareerCoverageState",
    "PlayerCappedStatus",
    "PVREVerificationStatus",
    "VerificationStatus",
    "PVREReviewStatus",
    "SourceReliability",
    "EvidenceTier",
    # Core Contracts
    "PVRERequestContract",
    "PVREOutputContract",
    "ReviewDossierContract",
    "PVREReviewDossierContract",
    "ReplacementCandidateEvidence",
    # Additional Typed Contracts
    "PlayerResearchRequest",
    "PlayerResearchOutput",
    "ReplacementResearchRequest",
    "VerificationClaim",
    "EvidenceSource",
    "ResearchConflict",
    "CareerVerification",
    "ResearchCoverage",
]
