"""User custom team composition contracts (TRD §11 Domain 7)."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import Field

from src.contracts.base import BaseContract


class UserTeam(BaseContract):
    """TRD Entity 29: user_teams."""

    team_id: UUID = Field(default_factory=uuid4)
    team_name: str = Field(..., max_length=100)
    created_by: str | None = Field(default=None, max_length=50)
    target_season: str | None = Field(default=None, max_length=20)
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserTeamPlayer(BaseContract):
    """TRD Entity 30: user_team_players."""

    id: UUID = Field(default_factory=uuid4)
    user_team_id: UUID
    player_id: UUID
    assigned_role: str | None = Field(default=None, max_length=30)
    batting_order: int | None = Field(default=None, ge=1, le=11)
    is_designated_wk: bool = False
    is_captain: bool = False
    added_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
