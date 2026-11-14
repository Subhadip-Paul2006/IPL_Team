"""Authoritative Pydantic contract suite reflecting the 33 TRD entities."""

from src.contracts.base import BaseContract
from src.contracts.career import (
    PlayerAvailability,
    PlayerAward,
    PlayerCompetitionHistory,
    PlayerInjury,
    PlayerMembershipState,
)
from src.contracts.competition import (
    Competition,
    PlayerTeamHistory,
    Season,
    SquadMembership,
    Team,
    TeamSeasonParticipation,
    Venue,
)
from src.contracts.conditions import PitchCondition, WeatherCondition
from src.contracts.eligibility import EligibilityPolicy, PlayerEligibility
from src.contracts.features import DerivedFeature
from src.contracts.match import Delivery, Innings, Match
from src.contracts.player import Player, PlayerAlias
from src.contracts.provenance import DataSource, SourceRecord, VerificationRecord
from src.contracts.ranking import RankingConfiguration, RankingRun
from src.contracts.scorecard import (
    BattingInnings,
    BowlingSpell,
    FieldingEvent,
    WicketkeepingEvent,
)
from src.contracts.team_builder import UserTeam, UserTeamPlayer

__all__ = [
    "BaseContract",
    # Domain 1: Ingestion & Provenance (1-3)
    "DataSource",
    "SourceRecord",
    "VerificationRecord",
    # Domain 2: Core Identity (4-5)
    "Player",
    "PlayerAlias",
    # Domain 3: Teams & Competitions (6-12)
    "Venue",
    "Team",
    "Competition",
    "Season",
    "TeamSeasonParticipation",
    "SquadMembership",
    "PlayerTeamHistory",
    # Domain 4: Matches & Conditions (13-15)
    "Match",
    "Innings",
    "Delivery",
    # Domain 5: Scorecards & Fielding (16-19)
    "BattingInnings",
    "BowlingSpell",
    "FieldingEvent",
    "WicketkeepingEvent",
    # Domain 4b: Conditions (20-21)
    "PitchCondition",
    "WeatherCondition",
    # Domain 6: Career & Eligibility (22-28)
    "PlayerAvailability",
    "PlayerInjury",
    "PlayerAward",
    "PlayerCompetitionHistory",
    "PlayerMembershipState",
    "EligibilityPolicy",
    "PlayerEligibility",
    # Domain 7: User Team Composition (29-30)
    "UserTeam",
    "UserTeamPlayer",
    # Domain 8: Feature Store (31)
    "DerivedFeature",
    # Domain 9: Ranking Configurations & Runs (32-33)
    "RankingConfiguration",
    "RankingRun",
]
