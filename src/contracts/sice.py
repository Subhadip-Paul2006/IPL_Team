"""Squad Intelligence & Composition Engine (SICE) Contracts.

Defines Pydantic v2 data contracts for SICE operations in accordance with
docs/TRD.md §8, docs/RANKING_SPEC.md, docs/DATA_DICTIONARY.md §10.3 & §11,
and ratified human decisions HD-01 through HD-13.
"""

from __future__ import annotations

import math
import re
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

from src.contracts.base import BaseContract

# ==============================================================================
# Enumerations
# ==============================================================================


class SICEContractVersion(StrEnum):
    """Authoritative semantic contract version constants for SICE."""

    RANKING_VERSION = "RK-1.0.0"
    REPLACEMENT_VERSION = "RE-1.0.0"
    SQUAD_EVAL_VERSION = "SICE-2.0.0"


class RecommendationState(StrEnum):
    """Authoritative 5-state analytical recommendation taxonomy (DATA_DICTIONARY §10.3, TRD §8.4)."""

    ANALYTICAL_RETAIN = "ANALYTICAL_RETAIN"
    ANALYTICAL_MONITOR = "ANALYTICAL_MONITOR"
    ANALYTICAL_REPLACEMENT_CANDIDATE = "ANALYTICAL_REPLACEMENT_CANDIDATE"
    NO_SUITABLE_VERIFIED_REPLACEMENT = "NO_SUITABLE_VERIFIED_REPLACEMENT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


# Backward compatibility alias
RecommendationLabel = RecommendationState


class RunType(StrEnum):
    """Operational run classification isolating Top-10 ranking from replacement & squad evaluation."""

    HACKATHON_TOP10 = "HACKATHON_TOP10"
    REPLACEMENT_EVALUATION = "REPLACEMENT_EVALUATION"
    SQUAD_EVALUATION = "SQUAD_EVALUATION"
    DRAFT_EXPLORATION = "DRAFT_EXPLORATION"


class RosterStatus(StrEnum):
    """Squad capacity, draft tolerance, and IPL roster constraint status (HD-05, HD-08, HD-09)."""

    ROSTER_VALID = "ROSTER_VALID"
    ROSTER_INCOMPLETE = "ROSTER_INCOMPLETE"
    ROSTER_UNDERSIZED = "ROSTER_UNDERSIZED"
    ROSTER_OVERSIZED = "ROSTER_OVERSIZED"
    OVERSEAS_BREACH = "OVERSEAS_BREACH"
    CRITICAL_WK_SHORTAGE = "CRITICAL_WK_SHORTAGE"
    SLOT_WASTE = "SLOT_WASTE"


class DimensionStatus(StrEnum):
    """Computability and evidence availability status for individual dimensions (DATA_DICTIONARY §11)."""

    COMPUTED = "COMPUTED"
    NOT_COMPUTABLE = "NOT_COMPUTABLE"
    INSUFFICIENT_SAMPLE = "INSUFFICIENT_SAMPLE"
    SCORECARD_ONLY = "SCORECARD_ONLY"
    STYLE_UNAVAILABLE = "STYLE_UNAVAILABLE"
    DEFERRED = "DEFERRED"
    UNDEFEATED_IN_WINDOW = "UNDEFEATED_IN_WINDOW"
    ZERO_WICKETS = "ZERO_WICKETS"


class CandidateRankingStatus(StrEnum):
    """Candidate qualification tier in ranking board output (RANKING_SPEC §6)."""

    TOP_10 = "TOP_10"
    RESERVE = "RESERVE"
    UNQUALIFIED = "UNQUALIFIED"


class UncertaintyFlag(StrEnum):
    """Provenance and evidence completeness certification flag (RANKING_SPEC §2)."""

    VERIFIED = "VERIFIED"
    PROVISIONAL = "PROVISIONAL"
    SAMPLE_CONSTRAINED = "SAMPLE_CONSTRAINED"


class DimensionAdvantage(StrEnum):
    """Statistical delta direction across comparison dimensions (Readiness §7.5)."""

    SIGNIFICANT_CANDIDATE_ADVANTAGE = "SIGNIFICANT_CANDIDATE_ADVANTAGE"
    SIGNIFICANT_INCUMBENT_ADVANTAGE = "SIGNIFICANT_INCUMBENT_ADVANTAGE"
    PARITY_WITHIN_UNCERTAINTY = "PARITY_WITHIN_UNCERTAINTY"
    NEUTRAL = "NEUTRAL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class LineupType(StrEnum):
    """Tactical lineup package identifier (HD-06)."""

    TRADITIONAL_XI = "TRADITIONAL_XI"
    BAT_FIRST_IMPACT = "BAT_FIRST_IMPACT"
    BOWL_FIRST_IMPACT = "BOWL_FIRST_IMPACT"


# ==============================================================================
# Validation Helpers
# ==============================================================================

_SHA256_HEX_REGEX = re.compile(r"^[0-9a-fA-F]{64}$")


_NAN_INF_STRINGS = frozenset(
    {
        "nan",
        "+nan",
        "-nan",
        "inf",
        "+inf",
        "-inf",
        "infinity",
        "+infinity",
        "-infinity",
    }
)


def _check_no_nan_inf(v: Any) -> Any:
    """Validate that numeric values do not contain NaN or Infinity (Rule R1)."""
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        raise ValueError("NaN or Infinity forbidden")
    if isinstance(v, str) and v.strip().lower() in _NAN_INF_STRINGS:
        raise ValueError("NaN or Infinity forbidden")
    if isinstance(v, dict):
        for k, val in v.items():
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                raise ValueError(f"NaN or Infinity forbidden in {k}")
            if isinstance(val, str) and val.strip().lower() in _NAN_INF_STRINGS:
                raise ValueError(f"NaN or Infinity forbidden in {k}")
    if isinstance(v, list):
        for item in v:
            if isinstance(item, float) and (math.isnan(item) or math.isinf(item)):
                raise ValueError("NaN or Infinity forbidden in list element")
            if isinstance(item, str) and item.strip().lower() in _NAN_INF_STRINGS:
                raise ValueError("NaN or Infinity forbidden in list element")
    return v


# ==============================================================================
# Domain Models
# ==============================================================================


class RankedCandidateContract(BaseContract):
    """Individual ranked uncapped candidate with verified metrics and bootstrap CIs."""

    rank: int = Field(..., ge=1)
    player_id: UUID
    canonical_name: str = Field(..., max_length=100)
    role: str = Field(..., max_length=30)
    age_at_evaluation: float = Field(..., ge=14.0, le=55.0)
    score: float = Field(..., ge=0.0, le=100.0)
    score_ci_lower: float | None = None
    score_ci_upper: float | None = None
    top10_stability_pct: float | None = Field(default=None, ge=0.0, le=100.0)
    match_appearances: int = Field(default=0, ge=0)
    volume_total: int = Field(default=0, ge=0)
    volume_pressure: int = Field(default=0, ge=0)
    key_metric_raw: float | None = None
    key_metric_shrunk: float | None = None
    delta_metric: float | None = None
    consistency_score: float | None = None
    career_batting_average: float | None = None
    career_batting_strike_rate: float | None = None
    career_balls_faced: int | None = Field(default=None, ge=0)
    status: CandidateRankingStatus = CandidateRankingStatus.TOP_10
    uncertainty_flag: UncertaintyFlag = UncertaintyFlag.VERIFIED
    verification_record_ids: list[UUID] = Field(default_factory=list)
    profile_tag: str | None = None
    source_provenance_id: UUID | None = None
    format_tags: list[str] = Field(default_factory=list)

    @field_validator("*", mode="before")
    @classmethod
    def validate_no_nan_inf(cls, v: Any) -> Any:
        return _check_no_nan_inf(v)

    @model_validator(mode="after")
    def validate_confidence_interval(self) -> RankedCandidateContract:
        if (
            self.score_ci_lower is not None
            and self.score_ci_upper is not None
            and self.score_ci_lower > self.score_ci_upper
        ):
            raise ValueError("score_ci_lower cannot be greater than score_ci_upper")
        return self


class RankingBoardOutputContract(BaseContract):
    """Complete frozen execution board for Top-10 uncapped candidates (Entity 33 compatible)."""

    contract_version: str = SICEContractVersion.RANKING_VERSION.value
    run_id: UUID = Field(default_factory=uuid4)
    config_id: UUID
    target_season_id: UUID
    evaluation_date: date
    data_snapshot_sha256: str = Field(...)
    qualified_candidates_count: int = Field(..., ge=0)
    top10: list[RankedCandidateContract] = Field(default_factory=list)
    reserve_list: list[RankedCandidateContract] = Field(default_factory=list)
    bootstrap_iterations: int = Field(default=1000, ge=100)
    seed: int = 0
    computed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    determinism_note: str | None = None
    run_type: RunType = RunType.HACKATHON_TOP10

    @field_validator("*", mode="before")
    @classmethod
    def validate_no_nan_inf(cls, v: Any) -> Any:
        return _check_no_nan_inf(v)

    @field_validator("data_snapshot_sha256")
    @classmethod
    def validate_sha256(cls, v: str) -> str:
        if not _SHA256_HEX_REGEX.match(v):
            raise ValueError(
                "data_snapshot_sha256 must be a valid 64-character hexadecimal SHA256 string"
            )
        return v.lower()

    @field_validator("top10")
    @classmethod
    def validate_top10_size(cls, v: list[RankedCandidateContract]) -> list[RankedCandidateContract]:
        if len(v) > 10:
            raise ValueError("top10 list cannot contain more than 10 candidates")
        return v


class DimensionComparisonResult(BaseContract):
    """Point-by-point comparison across 16 micro dimensions (D01–D16)."""

    dimension_id: str = Field(..., max_length=10)
    dimension_name: str = Field(..., max_length=100)
    incumbent_value: float | str | None = None
    candidate_value: float | str | None = None
    delta: float | None = None
    incumbent_sample: int | None = Field(default=None, ge=0)
    candidate_sample: int | None = Field(default=None, ge=0)
    advantage: DimensionAdvantage = DimensionAdvantage.NEUTRAL
    confidence_interval_lower: float | None = None
    confidence_interval_upper: float | None = None
    computable: bool = True
    dimension_status: DimensionStatus = DimensionStatus.COMPUTED
    notes: str | None = None

    @field_validator("*", mode="before")
    @classmethod
    def validate_no_nan_inf(cls, v: Any) -> Any:
        return _check_no_nan_inf(v)

    @model_validator(mode="after")
    def validate_confidence_interval(self) -> DimensionComparisonResult:
        if (
            self.confidence_interval_lower is not None
            and self.confidence_interval_upper is not None
            and self.confidence_interval_lower > self.confidence_interval_upper
        ):
            raise ValueError(
                "confidence_interval_lower cannot be greater than confidence_interval_upper"
            )
        return self


class CandidateReplacementEvaluation(BaseContract):
    """Full comparative dossier of one candidate against an RR incumbent."""

    candidate_player_id: UUID
    canonical_name: str = Field(..., max_length=100)
    age_at_evaluation: float = Field(..., ge=14.0, le=55.0)
    role_compatibility: str = Field(..., max_length=50)
    recommendation_label: RecommendationState
    dimension_comparisons: list[DimensionComparisonResult] = Field(default_factory=list)
    evidence_verification_ids: list[UUID] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    overseas_slot_liberated: bool = False
    similarity_scores: dict[str, float] = Field(default_factory=dict)

    @field_validator("*", mode="before")
    @classmethod
    def validate_no_nan_inf(cls, v: Any) -> Any:
        return _check_no_nan_inf(v)


class ReplacementComparisonRequest(BaseContract):
    """Input request contract for incumbent replacement evaluation."""

    incumbent_player_id: UUID
    target_season_id: UUID
    evaluation_date: date
    candidate_pool_ids: list[UUID] | None = None
    config_version: str = "RE-1.0.0"
    force_refresh: bool = False


class ReplacementComparisonOutputContract(BaseContract):
    """Frozen execution result of incumbent-vs-candidate replacement evaluation."""

    contract_version: str = SICEContractVersion.REPLACEMENT_VERSION.value
    comparison_id: UUID = Field(default_factory=uuid4)
    incumbent_player_id: UUID
    incumbent_canonical_name: str = Field(..., max_length=100)
    incumbent_role: str = Field(..., max_length=50)
    replaceability_signal: str = Field(..., max_length=50)
    evaluation_date: date
    target_season_id: UUID
    evaluations: list[CandidateReplacementEvaluation] = Field(default_factory=list)
    recommended_action: RecommendationState
    review_status: str = "CLEAR"
    review_dossier_id: UUID | None = None
    data_snapshot_sha256: str = Field(...)
    computed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    run_type: RunType = RunType.REPLACEMENT_EVALUATION
    overseas_slot_liberated: bool = False

    @field_validator("*", mode="before")
    @classmethod
    def validate_no_nan_inf(cls, v: Any) -> Any:
        return _check_no_nan_inf(v)

    @field_validator("data_snapshot_sha256")
    @classmethod
    def validate_sha256(cls, v: str) -> str:
        if not _SHA256_HEX_REGEX.match(v):
            raise ValueError(
                "data_snapshot_sha256 must be a valid 64-character hexadecimal SHA256 string"
            )
        return v.lower()


class SquadBalanceDimensions(BaseContract):
    """Evaluated metrics across all 16 Macro Squad Balance Dimensions (DIM-01 to DIM-16)."""

    roster_capacity_status: RosterStatus = RosterStatus.ROSTER_VALID
    squad_size: int = Field(default=0, ge=0)
    overseas_count: int = Field(default=0, ge=0)
    overseas_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    domestic_count: int = Field(default=0, ge=0)
    role_entropy: float = Field(default=0.0, ge=0.0)
    batting_depth_index: float | None = None
    lower_order_resilience: float | None = None
    bowling_overs_capacity: float = Field(default=0.0, ge=0.0)
    frontline_bowlers_count: int = Field(default=0, ge=0)
    secondary_bowlers_count: int = Field(default=0, ge=0)
    pace_bowler_count: int = Field(default=0, ge=0)
    spin_bowler_count: int = Field(default=0, ge=0)
    pace_to_spin_ratio: float | None = None
    phase_coverage_status: dict[str, float] = Field(default_factory=dict)
    wicketkeeper_count: int = Field(default=0, ge=0)
    all_rounder_count: int = Field(default=0, ge=0)
    left_hand_batting_ratio_top7: float = Field(default=0.0, ge=0.0, le=1.0)
    bowling_style_diversity_count: int = Field(default=0, ge=0)
    mean_squad_age: float | None = None
    verified_uncapped_count: int = Field(default=0, ge=0)
    role_cannibalization_flags: list[str] = Field(default_factory=list)
    positional_coverage_deficit: int = Field(default=0, ge=0)
    tactical_versatility_score: float = Field(default=0.0, ge=0.0, le=1.0)
    evidentiary_health_score: float = Field(default=0.0, ge=0.0, le=1.0)
    dimension_scores: dict[str, float | None] = Field(default_factory=dict)

    @field_validator("*", mode="before")
    @classmethod
    def validate_no_nan_inf(cls, v: Any) -> Any:
        return _check_no_nan_inf(v)


class LineupEvaluationResult(BaseContract):
    """Evaluated Playing XI combination with Impact Player tactical package."""

    lineup_type: LineupType = LineupType.TRADITIONAL_XI
    starting_xi_player_ids: list[UUID] = Field(default_factory=list)
    batting_order: list[UUID] = Field(default_factory=list)
    captain_player_id: UUID | None = None
    designated_wicketkeeper_player_id: UUID | None = None
    overseas_player_ids: list[UUID] = Field(default_factory=list)
    overseas_count: int = Field(default=0, ge=0)
    nominated_substitute_ids: list[UUID] = Field(default_factory=list)
    impact_player_id: UUID | None = None
    impact_sub_out_id: UUID | None = None
    batting_depth_index: float | None = None
    lower_order_resilience: float | None = None
    bowling_overs_capacity: float = Field(default=0.0, ge=0.0)
    frontline_bowlers_count: int = Field(default=0, ge=0)
    phase_deficits: dict[str, float] = Field(default_factory=dict)
    is_valid_ipl_lineup: bool = True
    violations: list[str] = Field(default_factory=list)

    @field_validator("*", mode="before")
    @classmethod
    def validate_no_nan_inf(cls, v: Any) -> Any:
        return _check_no_nan_inf(v)

    @field_validator("starting_xi_player_ids")
    @classmethod
    def validate_starting_xi_size(cls, v: list[UUID]) -> list[UUID]:
        if len(v) > 11:
            raise ValueError(f"Starting XI cannot contain more than 11 players (received {len(v)})")
        return v


class AnalyticalRecommendation(BaseContract):
    """Structured recommendation statement backed by metrics and confidence."""

    statement: str
    evidence_metrics: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    label: str = "ANALYTICAL_RECOMMENDATION"

    @field_validator("*", mode="before")
    @classmethod
    def validate_no_nan_inf(cls, v: Any) -> Any:
        return _check_no_nan_inf(v)


class SICEOutputContract(BaseContract):
    """Authoritative master squad intelligence evaluation contract."""

    contract_version: str = SICEContractVersion.SQUAD_EVAL_VERSION.value
    team_id: UUID
    target_season: str
    squad_size: int = Field(..., ge=0)
    is_valid_ipl_roster: bool
    roster_status: RosterStatus = RosterStatus.ROSTER_VALID
    squad_health_index: float | None = None
    uncertainty_badge: str
    balance_dimensions: SquadBalanceDimensions
    role_distribution: dict[str, int] = Field(default_factory=dict)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    critical_deficits: list[str] = Field(default_factory=list)
    recommended_lineups: list[LineupEvaluationResult] = Field(default_factory=list)
    recommendations: list[AnalyticalRecommendation] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("*", mode="before")
    @classmethod
    def validate_no_nan_inf(cls, v: Any) -> Any:
        return _check_no_nan_inf(v)

    @model_validator(mode="after")
    def validate_draft_tolerance(self) -> SICEOutputContract:
        """Enforce HD-09 draft tolerance and IPL roster capacity invariants."""
        if self.squad_size < 18:
            if self.is_valid_ipl_roster:
                raise ValueError(
                    f"squad_size={self.squad_size} cannot be certified as valid IPL roster (min 18 players required per HD-05/HD-09)"
                )
            if self.squad_health_index is not None:
                raise ValueError(
                    "squad_health_index must be None for incomplete draft squads (squad_size < 18 per HD-09)"
                )
        elif self.squad_size > 25:
            if self.is_valid_ipl_roster:
                raise ValueError(
                    f"squad_size={self.squad_size} exceeds maximum IPL roster capacity of 25 players (HD-05/HD-09)"
                )
        return self
