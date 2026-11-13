"""Player identity and alias contracts (TRD §11 Domain 2)."""

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from src.contracts.base import BaseContract


class Player(BaseContract):
    """TRD Entity 4: players."""

    player_id: UUID = Field(default_factory=uuid4)
    canonical_name: str = Field(..., max_length=100)
    full_name: str | None = Field(default=None, max_length=150)
    date_of_birth: date | None = None
    nationality: str = Field(..., max_length=50)
    primary_role: str = Field(..., max_length=30)
    batting_hand: str | None = Field(default=None, max_length=10)
    bowling_arm: str | None = Field(default=None, max_length=10)
    bowling_style: str | None = Field(default=None, max_length=50)
    cricsheet_id: str | None = Field(default=None, max_length=50)
    bcci_id: str | None = Field(default=None, max_length=50)
    espn_id: str | None = Field(default=None, max_length=50)
    identity_status: str = Field(default="UNRESOLVED", max_length=20)
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("primary_role")
    @classmethod
    def validate_primary_role(cls, v: str) -> str:
        allowed = {
            "Top-order Batter",
            "Middle-order Batter",
            "Wicketkeeper Batter",
            "Batting All-rounder",
            "Bowling All-rounder",
            "Pace Bowler",
            "Spin Bowler",
            "Wicketkeeper",
        }
        if v not in allowed:
            raise ValueError(f"primary_role must be one of {allowed}")
        return v

    @field_validator("batting_hand")
    @classmethod
    def validate_batting_hand(cls, v: str | None) -> str | None:
        if v is not None and v not in {"Right", "Left"}:
            raise ValueError("batting_hand must be 'Right' or 'Left'")
        return v

    @field_validator("bowling_arm")
    @classmethod
    def validate_bowling_arm(cls, v: str | None) -> str | None:
        if v is not None and v not in {"Right", "Left"}:
            raise ValueError("bowling_arm must be 'Right' or 'Left'")
        return v

    @field_validator("identity_status")
    @classmethod
    def validate_identity_status(cls, v: str) -> str:
        allowed = {"UNRESOLVED", "PROVISIONAL", "RESOLVED"}
        if v not in allowed:
            raise ValueError(f"identity_status must be one of {allowed}")
        return v


class PlayerAlias(BaseContract):
    """TRD Entity 5: player_aliases."""

    alias_id: UUID = Field(default_factory=uuid4)
    player_id: UUID
    alias_name: str = Field(..., max_length=100)
    source_id: UUID
    match_threshold_met: bool = False
    is_verified: bool = False
    needs_review: bool = False
    verified_by: str | None = Field(default=None, max_length=50)
    verified_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
