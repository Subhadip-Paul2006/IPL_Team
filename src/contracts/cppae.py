"""CPPAE (Complete Player Performance Analytics Engine) Contracts (TRD §6, §11 Domain 8)."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from src.contracts.base import BaseContract


class PerStatMetric(BaseContract):
    """Atomic metric definition and value descriptor per TRD §6.3."""

    metric_id: str = Field(..., max_length=20)  # e.g. "B01", "W06", "M02", "BPPS"
    name: str = Field(..., max_length=100)
    value: float | int | str | None = None
    definition_ref: str = Field(..., max_length=100)  # e.g. "DATA_DICTIONARY §1 B01"
    formula: str = Field(..., max_length=255)
    source_fields: list[str] = Field(default_factory=list)
    format_tag: str = Field(default="T20", max_length=20)
    sample_size: int | None = None
    null_reason: str | None = None
    status: str = Field(default="DERIVED", max_length=30)
    insufficient_sample_flag: bool = False

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"OBSERVED", "DERIVED", "MODEL_INFERRED", "NOT_COMPUTABLE", "DEFERRED"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class BattingPhaseSplit(BaseContract):
    """Phase-specific batting performance (B12)."""

    phase: str  # "Powerplay", "Middle", "Death"
    balls_faced: int = 0
    runs_scored: int = 0
    dismissals: int = 0
    fours: int = 0
    sixes: int = 0
    dot_balls: int = 0
    strike_rate: float | None = None
    batting_average: float | None = None
    dot_pct: float | None = None
    boundary_pct: float | None = None


class BattingPositionSplit(BaseContract):
    """Position-specific batting performance (B10, B11)."""

    position: int | str  # 1..11 or "Opening", "Top-Order", "Middle-Order", "Finishing"
    innings_count: int = 0
    balls_faced: int = 0
    runs_scored: int = 0
    dismissals: int = 0
    fours: int = 0
    sixes: int = 0
    dot_balls: int = 0
    strike_rate: float | None = None
    batting_average: float | None = None
    dot_pct: float | None = None
    boundary_pct: float | None = None
    insufficient_sample: bool = False


class HeadToHeadMatchup(BaseContract):
    """Batter vs Bowler matchup (B13 / W10)."""

    opponent_id: str
    opponent_name: str
    balls: int = 0
    runs: int = 0
    dismissals: int = 0  # wickets for bowler, outs for batter
    dots: int = 0
    fours: int = 0
    sixes: int = 0
    strike_rate: float | None = None
    economy_rate: float | None = None
    average: float | None = None
    dot_pct: float | None = None
    warning_flag: str | None = None  # e.g. "INSUFFICIENT_SAMPLE", "SMALL_SAMPLE_WARNING"


class PartnershipRecord(BaseContract):
    """Contiguous crease-sharing partnership window (B16)."""

    partner_id: str
    partner_name: str
    innings_id: str | None = None
    match_id: str | None = None
    player_runs: int = 0
    partner_runs: int = 0
    extras_runs: int = 0
    total_partnership_runs: int = 0
    balls_faced: int = 0
    unbroken: bool = False


class BattingProfile(BaseContract):
    """Complete Batting Profile covering B01-B17 and BPPS."""

    matches: int = 0
    innings: int = 0
    dnb_count: int = 0
    zero_ball_batted_count: int = 0
    runs: int = 0
    balls_faced: int = 0
    dismissals: int = 0
    not_outs: int = 0
    batting_average: float | None = None
    strike_rate: float | None = None
    fours: int = 0
    sixes: int = 0
    boundaries: int = 0
    boundary_pct: float | None = None
    dot_balls: int = 0
    dot_pct: float | None = None
    bpps: float = 0.0
    profile_tag: str | None = None  # e.g. "UNDEFEATED_IN_WINDOW"
    phase_splits: dict[str, BattingPhaseSplit] = Field(default_factory=dict)
    position_splits: dict[str, BattingPositionSplit] = Field(default_factory=dict)
    bowler_matchups: dict[str, HeadToHeadMatchup] = Field(default_factory=dict)
    pace_vs_spin: dict[str, HeadToHeadMatchup] = Field(default_factory=dict)
    bowling_style_matchups: dict[str, HeadToHeadMatchup] = Field(default_factory=dict)
    partnerships: list[PartnershipRecord] = Field(default_factory=list)
    outcome_splits: dict[str, dict[str, Any]] = Field(default_factory=dict)


class BowlingPhaseSplit(BaseContract):
    """Phase-specific bowling performance (W09)."""

    phase: str
    legal_balls: int = 0
    overs_display: str = "0.0"
    runs_conceded: int = 0
    wickets: int = 0
    dot_balls: int = 0
    economy_rate: float | None = None
    bowling_average: float | None = None
    bowling_strike_rate: float | None = None
    dot_pct: float | None = None


class DeliverySpeedSummary(BaseContract):
    """Recorded delivery speed metrics (W11)."""

    recorded_balls: int = 0
    total_balls: int = 0
    coverage_pct: float = 0.0
    mean_speed_kph: float | None = None
    min_speed_kph: float | None = None
    max_speed_kph: float | None = None
    status: str = "OBSERVED"  # "OBSERVED" or "NOT_COMPUTABLE"


class LineLengthSummary(BaseContract):
    """Pitch coordinate tracking buckets (W12)."""

    tracked_balls: int = 0
    total_balls: int = 0
    coverage_pct: float = 0.0
    length_buckets: dict[str, int] = Field(default_factory=dict)  # Yorker, Full, Good, Short, Bouncer
    line_buckets: dict[str, int] = Field(default_factory=dict)  # Outside Off, Stumps, Down Leg
    status: str = "OBSERVED"


class BowlingProfile(BaseContract):
    """Complete Bowling Profile covering W01-W12, BWPS, HLES."""

    matches: int = 0
    innings: int = 0
    legal_balls_bowled: int = 0
    overs_display: str = "0.0"
    balls_per_over: int = 6
    runs_conceded: int = 0
    wickets_taken: int = 0
    bowler_credited_wickets: int = 0
    dot_balls_bowled: int = 0
    bowling_average: float | None = None
    economy_rate: float | None = None
    bowling_strike_rate: float | None = None
    dot_pct: float | None = None
    bwps: float = 0.0
    hles: float | None = None  # None/DEFERRED for non-T20
    phase_splits: dict[str, BowlingPhaseSplit] = Field(default_factory=dict)
    batter_matchups: dict[str, HeadToHeadMatchup] = Field(default_factory=dict)
    speed_summary: DeliverySpeedSummary | None = None
    line_length_summary: LineLengthSummary | None = None
    outcome_splits: dict[str, dict[str, Any]] = Field(default_factory=dict)


class FieldingProfile(BaseContract):
    """Fielding Profile covering F01-F07."""

    appearances: int | None = None
    catches: int = 0
    run_outs_direct: int = 0
    run_outs_assisted: int = 0
    run_outs_total: int = 0
    stumpings: int = 0
    recorded_dropped_catches: int | None = None
    boundary_saves: int | None = None
    missed_opportunities: int | None = None
    coverage_class: str = "COVERAGE_LIMITED"  # "FULLY_RECORDED", "PARTIALLY_RECORDED", "COVERAGE_LIMITED"


class WicketkeepingProfile(BaseContract):
    """Wicketkeeping Profile covering F08-F09, WK-01 through WK-03."""

    appearances: int = 0
    dismissals_total: int = 0
    stumpings: int = 0
    catches: int = 0
    dismissals_per_appearance: float | None = None
    recorded_missed_stumpings: int | None = None
    recorded_missed_catches: int | None = None
    coverage_class: str = "COVERAGE_LIMITED"


class MatchContributionProfile(BaseContract):
    """Match Contribution Profile covering M01-M07."""

    player_of_match_awards: int = 0
    batting_contribution_pct: float | None = None  # M02 team run share
    bowling_wicket_share_pct: float | None = None  # M03 team wicket share
    bowling_run_suppression_pct: float | None = None  # M03 run suppression
    situation_context: dict[str, Any] = Field(default_factory=dict)  # M04 chase/defend
    win_loss_performance: dict[str, Any] = Field(default_factory=dict)  # M05
    high_leverage_contribution: dict[str, Any] = Field(default_factory=dict)  # M06
    additive_composite: float | None = None  # M07 = M02 + M03
    per_match_composite: dict[str, dict[str, Any]] = Field(default_factory=dict)


class SampleSizes(BaseContract):
    """Visible sample sizes per TRD §6.2."""

    matches: int = 0
    innings: int = 0
    balls_faced: int = 0
    legal_balls_bowled: int = 0
    delivery_events_faced: int = 0
    delivery_events_bowled: int = 0
    fielding_innings: int = 0
    wicketkeeping_innings: int = 0


class CPPAEOutput(BaseContract):
    """Authoritative CPPAE Output Contract (TRD §6.3)."""

    player_id: UUID
    canonical_name: str
    format_tag: str = Field(default="T20", max_length=20)
    window: str = Field(default="career", max_length=50)
    batting: BattingProfile | None = None
    bowling: BowlingProfile | None = None
    fielding: FieldingProfile | None = None
    wicketkeeping: WicketkeepingProfile | None = None
    match_contribution: MatchContributionProfile | None = None
    samples: SampleSizes = Field(default_factory=SampleSizes)
    per_stat: dict[str, PerStatMetric] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
