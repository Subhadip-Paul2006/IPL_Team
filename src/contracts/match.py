"""Matches, innings, and delivery contracts (TRD §11 Domain 4)."""

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

from src.contracts.base import BaseContract


class Match(BaseContract):
    """TRD Entity 13: matches."""

    match_id: UUID = Field(default_factory=uuid4)
    external_cricsheet_id: str | None = Field(default=None, max_length=50)
    season_id: UUID
    venue_id: UUID
    match_number: int | None = None
    match_type: str = Field(default="T20", max_length=30)
    match_date: date
    home_team_id: UUID
    away_team_id: UUID
    toss_winner_id: UUID | None = None
    toss_decision: str | None = Field(default=None, max_length=10)
    winner_id: UUID | None = None
    outcome_type: str = Field(..., max_length=30)
    win_margin_runs: int | None = Field(default=None, ge=0)
    win_margin_wickets: int | None = Field(default=None, ge=0)
    is_dls_applied: bool = False
    dls_method_version: str | None = Field(default=None, max_length=20)
    player_of_match_id: UUID | None = None
    innings_balls_scheduled: int = Field(default=120, gt=0)
    source_record_id: UUID | None = None
    status: str = Field(..., max_length=20)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("toss_decision")
    @classmethod
    def validate_toss_decision(cls, v: str | None) -> str | None:
        if v is not None and v not in {"bat", "field"}:
            raise ValueError("toss_decision must be 'bat' or 'field'")
        return v

    @field_validator("outcome_type")
    @classmethod
    def validate_outcome_type(cls, v: str) -> str:
        allowed = {"runs", "wickets", "tie", "super_over", "no_result", "abandoned"}
        if v not in allowed:
            raise ValueError(f"outcome_type must be one of {allowed}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"Scheduled", "Completed", "Abandoned", "No Result"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v

    @model_validator(mode="after")
    def validate_teams_distinct(self) -> "Match":
        if self.home_team_id == self.away_team_id:
            raise ValueError("home_team_id and away_team_id must be distinct")
        return self


class Innings(BaseContract):
    """TRD Entity 14: innings."""

    innings_id: UUID = Field(default_factory=uuid4)
    match_id: UUID
    innings_number: int = Field(..., ge=1, le=4)
    batting_team_id: UUID
    bowling_team_id: UUID
    is_super_over: bool = False
    overs_allocated_balls: int = Field(default=120, gt=0)
    target_runs: int | None = Field(default=None, ge=0)
    target_overs_balls: int | None = Field(default=None, gt=0)
    total_runs: int = Field(default=0, ge=0)
    total_wickets: int = Field(default=0, ge=0, le=10)
    total_legal_deliveries: int = Field(default=0, ge=0)
    total_extras: int = Field(default=0, ge=0)
    is_declared: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_innings_teams(self) -> "Innings":
        if self.batting_team_id == self.bowling_team_id:
            raise ValueError("batting_team_id and bowling_team_id must be distinct")
        return self


class Delivery(BaseContract):
    """TRD Entity 15: deliveries (partitioned by season_year)."""

    delivery_id: UUID = Field(default_factory=uuid4)
    innings_id: UUID
    season_year: str = Field(..., max_length=20)
    over_number: int = Field(..., ge=0, lt=60)
    ball_in_over: int = Field(..., ge=1)
    delivery_sequence: int = Field(..., ge=1)
    batter_id: UUID
    bowler_id: UUID
    non_striker_id: UUID
    runs_batter: int = Field(..., ge=0)
    runs_extras: int = Field(default=0, ge=0)
    runs_total: int = Field(..., ge=0)
    is_wide: bool = False
    is_noball: bool = False
    is_bye: bool = False
    is_legbye: bool = False
    is_penalty: bool = False
    runs_wides: int = Field(default=0, ge=0)
    runs_noballs: int = Field(default=0, ge=0)
    runs_byes: int = Field(default=0, ge=0)
    runs_legbyes: int = Field(default=0, ge=0)
    runs_penalties: int = Field(default=0, ge=0)
    is_wicket: bool = False
    wicket_kind: str | None = Field(default=None, max_length=30)
    player_out_id: UUID | None = None
    is_bowler_credited_wicket: bool = False
    match_phase: str | None = Field(default=None, max_length=20)
    variation_type: str | None = Field(default=None, max_length=50)
    ball_speed_kph: float | None = None
    pitch_coordinate_x: float | None = None
    pitch_coordinate_y: float | None = None
    post_shot_landing_x: float | None = None
    post_shot_landing_y: float | None = None
    source_record_id: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("match_phase")
    @classmethod
    def validate_match_phase(cls, v: str | None) -> str | None:
        if v is not None and v not in {"Powerplay", "Middle", "Death"}:
            raise ValueError("match_phase must be 'Powerplay', 'Middle', or 'Death'")
        return v

    @model_validator(mode="after")
    def validate_runs_and_wickets(self) -> "Delivery":
        if self.runs_total != self.runs_batter + self.runs_extras:
            raise ValueError("runs_total must equal runs_batter + runs_extras")
        if not self.is_wicket and self.player_out_id is not None:
            raise ValueError("player_out_id cannot be set when is_wicket is False")
        return self
