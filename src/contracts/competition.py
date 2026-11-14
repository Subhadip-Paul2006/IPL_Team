"""Teams, venues, competitions, and squad contracts (TRD §11 Domain 3)."""

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

from src.contracts.base import BaseContract


class Venue(BaseContract):
    """TRD Entity 6: venues."""

    venue_id: UUID = Field(default_factory=uuid4)
    stadium_name: str = Field(..., max_length=150)
    city: str = Field(..., max_length=100)
    country: str = Field(..., max_length=50)
    cricsheet_venue_id: str | None = Field(default=None, max_length=50)
    latitude: float | None = None
    longitude: float | None = None
    elevation_meters: float | None = None
    boundary_size_offside: float | None = None
    boundary_size_legside: float | None = None
    boundary_size_straight: float | None = None
    pitch_type_default: str | None = Field(default=None, max_length=50)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Team(BaseContract):
    """TRD Entity 7: teams."""

    team_id: UUID = Field(default_factory=uuid4)
    team_name: str = Field(..., max_length=100)
    short_code: str = Field(..., max_length=10)
    home_venue_id: UUID | None = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Competition(BaseContract):
    """TRD Entity 8: competitions."""

    competition_id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., max_length=100)
    competition_type: str = Field(..., max_length=30)
    governing_body: str = Field(..., max_length=50)
    country: str = Field(..., max_length=50)
    match_overs: int = Field(default=20, gt=0)
    balls_per_over: int = Field(default=6, ge=2, le=8)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("competition_type")
    @classmethod
    def validate_competition_type(cls, v: str) -> str:
        allowed = {
            "Domestic Franchise T20",
            "Domestic T20",
            "International T20",
            "Domestic List A",
            "ODI",
            "First Class",
            "Other",
        }
        if v not in allowed:
            raise ValueError(f"competition_type must be one of {allowed}")
        return v


class Season(BaseContract):
    """TRD Entity 9: seasons."""

    season_id: UUID = Field(default_factory=uuid4)
    competition_id: UUID
    season_year: str = Field(..., max_length=20)
    start_date: date
    end_date: date
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_season_dates(self) -> "Season":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be greater than or equal to start_date")
        return self


class TeamSeasonParticipation(BaseContract):
    """TRD Entity 10: team_season_participation."""

    participation_id: UUID = Field(default_factory=uuid4)
    team_id: UUID
    season_id: UUID
    participation_status: str = Field(..., max_length=20)
    effective_start_date: date | None = None
    effective_end_date: date | None = None
    evidence_source_id: UUID | None = None
    verification_id: UUID | None = None
    verification_status: str = Field(default="UNVERIFIED", max_length=20)
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("participation_status")
    @classmethod
    def validate_participation_status(cls, v: str) -> str:
        allowed = {"PARTICIPATING", "SUSPENDED", "NOT_ENTERED", "UNKNOWN"}
        if v not in allowed:
            raise ValueError(f"participation_status must be one of {allowed}")
        return v

    @field_validator("verification_status")
    @classmethod
    def validate_verification_status(cls, v: str) -> str:
        allowed = {"PENDING", "VERIFIED", "UNVERIFIED", "CONFLICT"}
        if v not in allowed:
            raise ValueError(f"verification_status must be one of {allowed}")
        return v


class SquadMembership(BaseContract):
    """TRD Entity 11: squad_memberships."""

    membership_id: UUID = Field(default_factory=uuid4)
    player_id: UUID
    team_id: UUID
    season_id: UUID
    contract_type: str = Field(..., max_length=30)
    salary_inr: float | None = Field(default=None, ge=0)
    jersey_number: int | None = Field(default=None, ge=0, le=999)
    is_captain: bool = False
    is_overseas: bool | None = None
    is_active_squad: bool | None = None  # Nullable with NO default per TRD
    evidence_source_id: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("contract_type")
    @classmethod
    def validate_contract_type(cls, v: str) -> str:
        allowed = {
            "Retained",
            "Auction Buy",
            "Replacement",
            "Trade",
            "Draft",
            "Squad Inclusion",
            "Released",
        }
        if v not in allowed:
            raise ValueError(f"contract_type must be one of {allowed}")
        return v


class PlayerTeamHistory(BaseContract):
    """TRD Entity 12: player_team_history."""

    history_id: UUID = Field(default_factory=uuid4)
    player_id: UUID
    team_id: UUID
    season_year: str = Field(..., max_length=20)
    season_id: UUID | None = None
    association_type: str = Field(..., max_length=30)
    appearances: int = Field(default=0, ge=0)
    evidence_source: UUID | None = None
    provenance_id: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("association_type")
    @classmethod
    def validate_association_type(cls, v: str) -> str:
        allowed = {"Squad", "Played", "Released", "Retained", "Acquired", "Loan"}
        if v not in allowed:
            raise ValueError(f"association_type must be one of {allowed}")
        return v
