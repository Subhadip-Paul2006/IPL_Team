"""Synthetic test fixtures for CDCRE (Career Discovery & Competition Research Engine) contracts.

Author: Worker 1 (Contracts & Domain Models Specialist)
Milestone: M1

==============================================================================
CRITICAL DOMAIN GUARDRAIL COMPLIANCE:
- R2: NEVER fabricate or hallucinate statistics, players, or memberships.
- P1: Generating synthetic / mock / hallucinated player or match records is
      STRICTLY PROHIBITED in application data or production stores.
- NOTICE: The synthetic fixtures in this module are EXCLUSIVELY FOR OFFLINE
  UNIT & INTEGRATION TESTS. All synthetic names, entities, and values are
  strictly scoped test fixtures. NO REAL CRICKETER STATS OR IDENTITIES ARE
  FABRICATED OR REPRESENTED IN PRODUCTION DATA.
==============================================================================
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest
from src.contracts.cdcre import (
    AmbiguityStatus,
    CandidateDiscoveryResult,
    CandidatePlayerRecord,
    CareerDataCoverage,
    CareerGapRecord,
    CDCREOutputContract,
    CompetitionHistoryRecord,
    CoverageStatus,
    GapType,
)

# =============================================================================
# Canonical Deterministic UUID Constants for Test Scenarios
# =============================================================================

SYNTHETIC_PLAYER_UUID_PRIMARY = UUID("10000000-0000-0000-0000-000000000001")
SYNTHETIC_PLAYER_UUID_SECONDARY = UUID("10000000-0000-0000-0000-000000000002")
SYNTHETIC_PLAYER_UUID_COLLISION_A = UUID("10000000-0000-0000-0000-000000000003")
SYNTHETIC_PLAYER_UUID_COLLISION_B = UUID("10000000-0000-0000-0000-000000000004")

IPL_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000001")
SMAT_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000002")
HUNDRED_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000003")
BBL_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000004")
BPL_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000005")

PROVENANCE_SOURCE_UUID_1 = UUID("30000000-0000-0000-0000-000000000001")
PROVENANCE_SOURCE_UUID_2 = UUID("30000000-0000-0000-0000-000000000002")


# =============================================================================
# Builder Functions
# =============================================================================


def build_synthetic_candidate_record(
    player_id: UUID | None = SYNTHETIC_PLAYER_UUID_PRIMARY,
    canonical_name: str = "Synthetic Test Player",
    source_id: str | None = "cricsheet_syn01",
    teams: list[str] | None = None,
    competitions: list[str] | None = None,
    confidence: float = 1.0,
) -> CandidatePlayerRecord:
    """Build a synthetic CandidatePlayerRecord instance."""
    return CandidatePlayerRecord(
        player_id=player_id,
        canonical_name=canonical_name,
        source_id=source_id,
        teams=["Rajasthan Royals"] if teams is None else teams,
        competitions=["Indian Premier League"] if competitions is None else competitions,
        confidence=confidence,
    )


def build_synthetic_candidate_discovery(
    raw_name_query: str = "Synthetic Player",
    ambiguity_status: AmbiguityStatus = AmbiguityStatus.SINGLE_CORROBORATED,
    candidates: list[CandidatePlayerRecord] | None = None,
    collision_detected: bool = False,
) -> CandidateDiscoveryResult:
    """Build a synthetic CandidateDiscoveryResult instance."""
    if candidates is None:
        candidates = [build_synthetic_candidate_record()]
    return CandidateDiscoveryResult(
        raw_name_query=raw_name_query,
        ambiguity_status=ambiguity_status,
        candidates=candidates,
        collision_detected=collision_detected,
    )


def build_synthetic_collision_discovery(
    raw_name_query: str = "Rashid Khan",
) -> CandidateDiscoveryResult:
    """Build a synthetic collision CandidateDiscoveryResult with MULTIPLE status."""
    cand_a = CandidatePlayerRecord(
        player_id=SYNTHETIC_PLAYER_UUID_COLLISION_A,
        canonical_name="Rashid Khan (Afghanistan)",
        source_id="cricsheet_rk01",
        teams=["Gujarat Titans", "Sunrisers Hyderabad", "Adelaide Strikers"],
        competitions=["Indian Premier League", "Big Bash League"],
        confidence=0.95,
    )
    cand_b = CandidatePlayerRecord(
        player_id=SYNTHETIC_PLAYER_UUID_COLLISION_B,
        canonical_name="Rashid Khan (Organizer Mapping)",
        source_id="org_rk02",
        teams=["Associate League Team"],
        competitions=["T20I Bilateral"],
        confidence=0.85,
    )
    return CandidateDiscoveryResult(
        raw_name_query=raw_name_query,
        ambiguity_status=AmbiguityStatus.MULTIPLE,
        candidates=[cand_a, cand_b],
        collision_detected=True,
    )


def build_synthetic_competition_history(
    competition_id: UUID = IPL_COMPETITION_UUID,
    competition_name: str = "Indian Premier League",
    season_year: str = "2024",
    format_tag: str = "T20",
    appearances: int | None = 14,
    coverage_status: CoverageStatus = CoverageStatus.VERIFIED_PARTICIPATION,
    balls_per_over: int = 6,
    provenance_record_id: UUID | None = PROVENANCE_SOURCE_UUID_1,
) -> CompetitionHistoryRecord:
    """Build a standard synthetic CompetitionHistoryRecord instance."""
    return CompetitionHistoryRecord(
        competition_id=competition_id,
        competition_name=competition_name,
        season_year=season_year,
        format_tag=format_tag,
        appearances=appearances,
        coverage_status=coverage_status,
        balls_per_over=balls_per_over,
        provenance_record_id=provenance_record_id,
    )


def build_synthetic_hundred_history(
    competition_id: UUID = HUNDRED_COMPETITION_UUID,
    season_year: str = "2023",
    appearances: int | None = 8,
    coverage_status: CoverageStatus = CoverageStatus.VERIFIED_PARTICIPATION,
) -> CompetitionHistoryRecord:
    """Build The Hundred competition history preserving balls_per_over = 5."""
    return CompetitionHistoryRecord(
        competition_id=competition_id,
        competition_name="The Hundred Men's Competition",
        season_year=season_year,
        format_tag="THE_HUNDRED",
        appearances=appearances,
        coverage_status=coverage_status,
        balls_per_over=5,
        provenance_record_id=PROVENANCE_SOURCE_UUID_2,
    )


def build_synthetic_unavailable_dataset_history(
    competition_id: UUID = BPL_COMPETITION_UUID,
    competition_name: str = "Bangladesh Premier League",
    season_year: str = "2018",
) -> CompetitionHistoryRecord:
    """Build a CompetitionHistoryRecord for a missing/unsupported dataset (AC-11)."""
    return CompetitionHistoryRecord(
        competition_id=competition_id,
        competition_name=competition_name,
        season_year=season_year,
        format_tag="T20",
        appearances=None,
        coverage_status=CoverageStatus.DATASET_UNAVAILABLE,
        balls_per_over=6,
        provenance_record_id=None,
    )


def build_synthetic_career_gap(
    player_id: UUID = SYNTHETIC_PLAYER_UUID_PRIMARY,
    start_season: str = "2021",
    end_season: str = "2021",
    gap_seasons: list[str] | None = None,
    gap_type: GapType = GapType.INJURY,
    competition_name: str = "Indian Premier League",
    evidence_notes: str | None = "Ruled out due to hamstring strain",
    provenance_record_id: UUID | None = PROVENANCE_SOURCE_UUID_1,
) -> CareerGapRecord:
    """Build a synthetic CareerGapRecord instance."""
    return CareerGapRecord(
        player_id=player_id,
        start_season=start_season,
        end_season=end_season,
        gap_seasons=["2021"] if gap_seasons is None else gap_seasons,
        gap_type=gap_type,
        competition_name=competition_name,
        evidence_notes=evidence_notes,
        provenance_record_id=provenance_record_id,
    )


def build_synthetic_rr_suspension_gap(
    player_id: UUID = SYNTHETIC_PLAYER_UUID_PRIMARY,
) -> CareerGapRecord:
    """Build a synthetic career gap representing Rajasthan Royals 2016-2017 franchise suspension."""
    return CareerGapRecord(
        player_id=player_id,
        start_season="2016",
        end_season="2017",
        gap_seasons=["2016", "2017"],
        gap_type=GapType.FRANCHISE_SUSPENSION,
        competition_name="Indian Premier League",
        evidence_notes="Rajasthan Royals franchise suspension per Supreme Court committee order (2016-2017)",
        provenance_record_id=PROVENANCE_SOURCE_UUID_1,
    )


def build_synthetic_career_data_coverage(
    canonical_player_id: UUID = SYNTHETIC_PLAYER_UUID_PRIMARY,
    the_hundred_deferred: bool = True,
) -> CareerDataCoverage:
    """Build a comprehensive synthetic CareerDataCoverage instance."""
    ipl_rec = build_synthetic_competition_history(
        competition_id=IPL_COMPETITION_UUID,
        season_year="2024",
        appearances=14,
        coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
    )
    smat_rec = build_synthetic_competition_history(
        competition_id=SMAT_COMPETITION_UUID,
        competition_name="Syed Mushtaq Ali Trophy",
        season_year="2023/24",
        appearances=7,
        coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
    )
    hundred_rec = build_synthetic_hundred_history(
        competition_id=HUNDRED_COMPETITION_UUID,
        season_year="2023",
        appearances=8,
        coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
    )
    unavail_rec = build_synthetic_unavailable_dataset_history(
        competition_id=BPL_COMPETITION_UUID,
        season_year="2018",
    )

    gaps = [build_synthetic_rr_suspension_gap(canonical_player_id)]

    coverage_summary: dict[CoverageStatus, int] = {
        CoverageStatus.VERIFIED_PARTICIPATION: 3,
        CoverageStatus.DATASET_UNAVAILABLE: 1,
        CoverageStatus.NOT_ESTABLISHED: 0,
        CoverageStatus.CONFIRMED_NON_PARTICIPATION: 0,
    }

    return CareerDataCoverage(
        canonical_player_id=canonical_player_id,
        competitions_evaluated_count=4,
        competitions_covered=[ipl_rec, smat_rec, hundred_rec, unavail_rec],
        coverage_summary=coverage_summary,
        career_gaps=gaps,
        the_hundred_appearances_deferred=the_hundred_deferred,
    )


def build_synthetic_cdcre_output(
    candidate_discovery: CandidateDiscoveryResult | None = None,
    career_coverage: CareerDataCoverage | None = None,
    metadata: dict[str, Any] | None = None,
) -> CDCREOutputContract:
    """Build a synthetic CDCREOutputContract instance."""
    if candidate_discovery is None:
        candidate_discovery = build_synthetic_candidate_discovery()
    if career_coverage is None:
        career_coverage = build_synthetic_career_data_coverage()
    if metadata is None:
        metadata = {
            "engine": "CDCRE",
            "version": "1.0.0",
            "evaluated_by": "Worker 1 Test Suite",
        }
    return CDCREOutputContract(
        candidate_discovery=candidate_discovery,
        career_coverage=career_coverage,
        metadata=metadata,
    )


# =============================================================================
# Pytest Fixtures
# =============================================================================


@pytest.fixture
def sample_candidate_record() -> CandidatePlayerRecord:
    """Fixture providing a valid synthetic CandidatePlayerRecord."""
    return build_synthetic_candidate_record()


@pytest.fixture
def sample_candidate_discovery_result() -> CandidateDiscoveryResult:
    """Fixture providing a single corroborated CandidateDiscoveryResult."""
    return build_synthetic_candidate_discovery()


@pytest.fixture
def sample_collision_discovery_result() -> CandidateDiscoveryResult:
    """Fixture providing a collision CandidateDiscoveryResult (MULTIPLE)."""
    return build_synthetic_collision_discovery()


@pytest.fixture
def sample_competition_history_record() -> CompetitionHistoryRecord:
    """Fixture providing a standard 6-ball CompetitionHistoryRecord."""
    return build_synthetic_competition_history()


@pytest.fixture
def sample_hundred_history_record() -> CompetitionHistoryRecord:
    """Fixture providing The Hundred 5-ball CompetitionHistoryRecord."""
    return build_synthetic_hundred_history()


@pytest.fixture
def sample_unavailable_dataset_record() -> CompetitionHistoryRecord:
    """Fixture providing a DATASET_UNAVAILABLE CompetitionHistoryRecord (AC-11)."""
    return build_synthetic_unavailable_dataset_history()


@pytest.fixture
def sample_career_gap_record() -> CareerGapRecord:
    """Fixture providing an injury CareerGapRecord."""
    return build_synthetic_career_gap()


@pytest.fixture
def sample_rr_suspension_gap_record() -> CareerGapRecord:
    """Fixture providing a Rajasthan Royals 2016-2017 franchise suspension CareerGapRecord."""
    return build_synthetic_rr_suspension_gap()


@pytest.fixture
def sample_career_data_coverage() -> CareerDataCoverage:
    """Fixture providing a comprehensive CareerDataCoverage."""
    return build_synthetic_career_data_coverage()


@pytest.fixture
def sample_cdcre_output_contract() -> CDCREOutputContract:
    """Fixture providing a full CDCREOutputContract."""
    return build_synthetic_cdcre_output()
