"""Career Discovery & Competition Research Engine (CDCRE) inter-engine runtime contracts.

Authoritative contracts reflecting TRD §5.1, §5.2, §5.3, §5.4, §5.5, and PRD FR-C1-FR-C5
specifications for Rajasthan Royals squad intelligence platform.
"""

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field

from src.contracts.base import BaseContract


class AmbiguityStatus(StrEnum):
    """Authoritative ambiguity status for candidate player identity discovery (TRD §5.1)."""

    NONE = "NONE"
    SINGLE_CORROBORATED = "SINGLE_CORROBORATED"
    MULTIPLE = "MULTIPLE"


class CoverageStatus(StrEnum):
    """Authoritative four-state coverage model for player tournament participation (TRD §5.3).

    Strictly aligns with PostgreSQL 16 DDL constraint chk_coverage_status.
    """

    VERIFIED_PARTICIPATION = "VERIFIED_PARTICIPATION"
    DATASET_UNAVAILABLE = "DATASET_UNAVAILABLE"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"
    CONFIRMED_NON_PARTICIPATION = "CONFIRMED_NON_PARTICIPATION"


class GapType(StrEnum):
    """Classification of career gaps across domestic and international competitions (TRD §5.4)."""

    FRANCHISE_SUSPENSION = "FRANCHISE_SUSPENSION"
    INJURY = "INJURY"
    NOC_DENIED = "NOC_DENIED"
    UNAVAILABLE = "UNAVAILABLE"
    UNEXPLAINED_GAP = "UNEXPLAINED_GAP"


class CandidatePlayerRecord(BaseContract):
    """Candidate player identity record discovered from canonical rosters and aliases (TRD §5.1)."""

    player_id: UUID | None = None
    canonical_name: str
    source_id: str | None = None
    teams: list[str] = Field(default_factory=list)
    competitions: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class CandidateDiscoveryResult(BaseContract):
    """Result of pre-identity candidate discovery for a raw name query (TRD §5.1, AC-10)."""

    raw_name_query: str
    ambiguity_status: AmbiguityStatus
    candidates: list[CandidatePlayerRecord] = Field(default_factory=list)
    collision_detected: bool = False


class CompetitionHistoryRecord(BaseContract):
    """Historical participation record for a player in a competition season (TRD §5.2, §5.3)."""

    competition_id: UUID
    competition_name: str
    season_year: str
    format_tag: str
    appearances: int | None = Field(default=None, ge=0)
    coverage_status: CoverageStatus
    balls_per_over: int = Field(default=6, gt=0)
    provenance_record_id: UUID | None = None


class CareerGapRecord(BaseContract):
    """Multi-season career gap detected and classified across tournament history (TRD §5.4)."""

    player_id: UUID
    start_season: str
    end_season: str
    gap_seasons: list[str] = Field(default_factory=list)
    gap_type: GapType
    competition_name: str
    evidence_notes: str | None = None
    provenance_record_id: UUID | None = None


class CareerDataCoverage(BaseContract):
    """Comprehensive post-identity career coverage evaluation container (TRD §5.3, §5.4)."""

    canonical_player_id: UUID
    competitions_evaluated_count: int = Field(default=0, ge=0)
    competitions_covered: list[CompetitionHistoryRecord] = Field(default_factory=list)
    coverage_summary: dict[CoverageStatus, int] = Field(default_factory=dict)
    career_gaps: list[CareerGapRecord] = Field(default_factory=list)
    the_hundred_appearances_deferred: bool = False


class CDCREOutputContract(BaseContract):
    """Inter-engine output contract for CDCRE discovery and research integration (TRD §5.5)."""

    candidate_discovery: CandidateDiscoveryResult | None = None
    career_coverage: CareerDataCoverage | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "AmbiguityStatus",
    "CoverageStatus",
    "GapType",
    "CandidatePlayerRecord",
    "CandidateDiscoveryResult",
    "CompetitionHistoryRecord",
    "CareerGapRecord",
    "CareerDataCoverage",
    "CDCREOutputContract",
]
