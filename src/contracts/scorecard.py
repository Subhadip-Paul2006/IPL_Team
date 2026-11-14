"""Scorecard and fielding contracts (TRD §11 Domain 5)."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

from src.contracts.base import BaseContract


class BattingInnings(BaseContract):
    """TRD Entity 16: batting_innings."""

    batting_innings_id: UUID = Field(default_factory=uuid4)
    innings_id: UUID
    player_id: UUID
    team_id: UUID
    did_not_bat: bool = False
    batting_position: int | None = Field(default=None, ge=1, le=11)
    runs_scored: int = Field(default=0, ge=0)
    balls_faced: int = Field(default=0, ge=0)
    minutes_at_crease: int | None = Field(default=None, ge=0)
    fours: int = Field(default=0, ge=0)
    sixes: int = Field(default=0, ge=0)
    dot_balls_faced: int = Field(default=0, ge=0)
    strike_rate: float | None = None
    dismissal_kind: str | None = Field(default=None, max_length=30)
    dismissal_bowler_id: UUID | None = None
    dismissal_fielder_id: UUID | None = None
    is_not_out: bool  # Mandatory with no default per TRD
    runs_powerplay: int = Field(default=0, ge=0)
    balls_powerplay: int = Field(default=0, ge=0)
    runs_middle: int = Field(default=0, ge=0)
    balls_middle: int = Field(default=0, ge=0)
    runs_death: int = Field(default=0, ge=0)
    balls_death: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_batting_invariants(self) -> "BattingInnings":
        if self.dot_balls_faced > self.balls_faced:
            raise ValueError("dot_balls_faced cannot exceed balls_faced")
        if self.strike_rate is not None and self.balls_faced == 0:
            raise ValueError("strike_rate must be None when balls_faced is 0")
        if self.did_not_bat and self.balls_faced > 0:
            raise ValueError("balls_faced must be 0 if did_not_bat is True")
        return self


class BowlingSpell(BaseContract):
    """TRD Entity 17: bowling_spells."""

    spell_id: UUID = Field(default_factory=uuid4)
    innings_id: UUID
    player_id: UUID
    team_id: UUID
    spell_order: int = Field(default=1, ge=1)
    legal_balls_bowled: int = Field(default=0, ge=0)
    illegal_events_wides: int = Field(default=0, ge=0)
    illegal_events_noballs: int = Field(default=0, ge=0)
    maidens: int = Field(default=0, ge=0)
    runs_conceded: int = Field(default=0, ge=0)
    wickets_taken: int = Field(default=0, ge=0, le=10)
    dot_balls_bowled: int = Field(default=0, ge=0)
    economy_rate: float | None = None
    bowling_average: float | None = None
    bowling_strike_rate: float | None = None
    runs_conceded_powerplay: int = Field(default=0, ge=0)
    balls_bowled_powerplay: int = Field(default=0, ge=0)
    wickets_powerplay: int = Field(default=0, ge=0)
    runs_conceded_middle: int = Field(default=0, ge=0)
    balls_bowled_middle: int = Field(default=0, ge=0)
    wickets_middle: int = Field(default=0, ge=0)
    runs_conceded_death: int = Field(default=0, ge=0)
    balls_bowled_death: int = Field(default=0, ge=0)
    wickets_death: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_bowling_invariants(self) -> "BowlingSpell":
        if self.dot_balls_bowled > self.legal_balls_bowled:
            raise ValueError("dot_balls_bowled cannot exceed legal_balls_bowled")
        if self.economy_rate is not None and self.legal_balls_bowled == 0:
            raise ValueError("economy_rate must be None when legal_balls_bowled is 0")
        if self.bowling_average is not None and self.wickets_taken == 0:
            raise ValueError("bowling_average must be None when wickets_taken is 0")
        return self


class FieldingEvent(BaseContract):
    """TRD Entity 18: fielding_events."""

    fielding_event_id: UUID = Field(default_factory=uuid4)
    delivery_id: UUID | None = None
    season_year: str | None = Field(default=None, max_length=20)
    player_id: UUID
    is_substitute: bool = False
    event_type: str = Field(..., max_length=30)
    is_recorded_opportunity: bool = True
    assisted_by_player_id: UUID | None = None
    fielding_position: str | None = Field(default=None, max_length=40)
    runs_saved: int | None = Field(default=None, ge=0)
    provenance_tier: str = Field(..., max_length=30)  # Mandatory with no default
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        allowed = {
            "Catch",
            "Run Out Thrower",
            "Run Out Catcher",
            "Stumping",
            "Dropped Catch",
            "Missed Run Out",
            "Boundary Save",
        }
        if v not in allowed:
            raise ValueError(f"event_type must be one of {allowed}")
        return v

    @field_validator("provenance_tier")
    @classmethod
    def validate_provenance_tier(cls, v: str) -> str:
        allowed = {
            "DIRECTLY_MEASURED",
            "OFFICIALLY_REPORTED",
            "THIRD_PARTY_ESTIMATE",
            "MODEL_INFERRED",
            "UNKNOWN",
        }
        if v not in allowed:
            raise ValueError(f"provenance_tier must be one of {allowed}")
        return v

    @model_validator(mode="after")
    def validate_delivery_pairing(self) -> "FieldingEvent":
        if (self.delivery_id is None) != (self.season_year is None):
            raise ValueError("delivery_id and season_year must either both be set or both be None")
        return self


class WicketkeepingEvent(BaseContract):
    """TRD Entity 19: wicketkeeping_events."""

    wk_event_id: UUID = Field(default_factory=uuid4)
    innings_id: UUID
    player_id: UUID
    match_id: UUID
    stumpings: int = Field(default=0, ge=0)
    catches: int = Field(default=0, ge=0)
    missed_stumpings: int | None = Field(default=None, ge=0)
    missed_catches: int | None = Field(default=None, ge=0)
    appearances: int = Field(..., gt=0)  # Mandatory with no default
    provenance_tier: str = Field(..., max_length=30)  # Mandatory with no default
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("provenance_tier")
    @classmethod
    def validate_provenance_tier(cls, v: str) -> str:
        allowed = {
            "DIRECTLY_MEASURED",
            "OFFICIALLY_REPORTED",
            "THIRD_PARTY_ESTIMATE",
            "MODEL_INFERRED",
            "UNKNOWN",
        }
        if v not in allowed:
            raise ValueError(f"provenance_tier must be one of {allowed}")
        return v
