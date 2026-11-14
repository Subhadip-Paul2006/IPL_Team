"""Player career, availability, injuries, awards, and membership state contracts (TRD §11 Domain 6)."""

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

from src.contracts.base import BaseContract


class PlayerAvailability(BaseContract):
    """TRD Entity 22: player_availability."""

    availability_id: UUID = Field(default_factory=uuid4)
    player_id: UUID
    season_id: UUID
    start_date: date
    end_date: date
    availability_status: str | None = Field(default=None, max_length=30)
    national_board_noc_status: str | None = Field(default=None, max_length=20)
    matches_expected_available: int | None = Field(default=None, ge=0)
    reason_for_unavailability: str | None = None
    source_record_id: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("national_board_noc_status")
    @classmethod
    def validate_noc_status(cls, v: str | None) -> str | None:
        if v is not None and v not in {"GRANTED", "DENIED", "UNKNOWN", "NOT_APPLICABLE"}:
            raise ValueError(
                "national_board_noc_status must be GRANTED, DENIED, UNKNOWN, or NOT_APPLICABLE"
            )
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> "PlayerAvailability":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be greater than or equal to start_date")
        return self


class PlayerInjury(BaseContract):
    """TRD Entity 23: player_injuries."""

    injury_id: UUID = Field(default_factory=uuid4)
    player_id: UUID
    injury_date: date | None = None
    injury_type: str | None = Field(default=None, max_length=50)
    body_part: str | None = Field(default=None, max_length=50)
    severity: str | None = Field(default=None, max_length=20)
    surgery_required: bool | None = None
    recovery_time_days: int | None = None
    return_to_play_date: date | None = None
    recurrence_risk_score: float | None = Field(default=None, ge=0.0, le=1.0)
    medical_notes: str | None = None
    source_record_id: UUID | None = None
    verified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str | None) -> str | None:
        if v is not None and v not in {"Minor", "Moderate", "Severe", "Catastrophic"}:
            raise ValueError("severity must be Minor, Moderate, Severe, or Catastrophic")
        return v


class PlayerAward(BaseContract):
    """TRD Entity 24: player_awards."""

    award_id: UUID = Field(default_factory=uuid4)
    player_id: UUID
    match_id: UUID | None = None
    award_type: str = Field(..., max_length=40)
    award_value: str | None = Field(default=None, max_length=100)
    award_date: date | None = None
    source_record_id: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("award_type")
    @classmethod
    def validate_award_type(cls, v: str) -> str:
        allowed = {"Player of the Match", "Player of the Tournament", "MVP", "Milestone", "Other"}
        if v not in allowed:
            raise ValueError(f"award_type must be one of {allowed}")
        return v


class PlayerCompetitionHistory(BaseContract):
    """TRD Entity 25: player_competition_history."""

    comp_history_id: UUID = Field(default_factory=uuid4)
    player_id: UUID
    competition_id: UUID
    season_year: str = Field(..., max_length=20)
    season_id: UUID | None = None
    appearances: int | None = Field(default=None, ge=0)
    coverage_status: str = Field(..., max_length=30)
    provenance_id: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("coverage_status")
    @classmethod
    def validate_coverage_status(cls, v: str) -> str:
        allowed = {
            "VERIFIED_PARTICIPATION",
            "DATASET_UNAVAILABLE",
            "NOT_ESTABLISHED",
            "CONFIRMED_NON_PARTICIPATION",
        }
        if v not in allowed:
            raise ValueError(f"coverage_status must be one of {allowed}")
        return v


class PlayerMembershipState(BaseContract):
    """TRD Entity 26: player_membership_state."""

    state_id: UUID = Field(default_factory=uuid4)
    player_id: UUID
    as_of_date: date
    rr_relationship_state: str = Field(..., max_length=30)
    rr_current_state: str = Field(..., max_length=15)
    negative_verification_met: bool | None = None
    evidence_verification_id: UUID | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("rr_relationship_state")
    @classmethod
    def validate_rr_relationship_state(cls, v: str) -> str:
        allowed = {
            "HISTORICAL_RR_APPEARANCE",
            "HISTORICAL_RR_SQUAD_ONLY",
            "PREVIOUSLY_ASSOCIATED",
            "NO_VERIFIED_RR_RELATIONSHIP",
            "RR_RELATIONSHIP_UNKNOWN",
        }
        if v not in allowed:
            raise ValueError(f"rr_relationship_state must be one of {allowed}")
        return v

    @field_validator("rr_current_state")
    @classmethod
    def validate_rr_current_state(cls, v: str) -> str:
        allowed = {"CURRENT", "NOT_CURRENT", "UNKNOWN"}
        if v not in allowed:
            raise ValueError(f"rr_current_state must be one of {allowed}")
        return v
