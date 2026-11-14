"""Test fixtures for CDCRE Post-Identity Career Retrieval (Milestone 3).

Provides deterministic canonical player UUIDs, synthetic competition history records,
The Hundred 5-ball format test scenarios, and helper builder functions for testing
career retrieval without hardcoding or fabrication.
"""

from __future__ import annotations

from uuid import UUID

import pytest
from src.cdcre.candidate_discovery import derive_player_uuid
from src.cdcre.career_retrieval import CareerRetrievalEngine
from src.cdcre.competition_registry import (
    BBL_COMPETITION_UUID,
    HUNDRED_COMPETITION_UUID,
    IPL_COMPETITION_UUID,
    SMAT_COMPETITION_UUID,
    CompetitionRegistry,
    derive_provenance_uuid,
)
from src.contracts.cdcre import (
    CompetitionHistoryRecord,
    CoverageStatus,
)

# =============================================================================
# Deterministic Canonical Player UUID Constants for Synthetic Scenarios
# =============================================================================

SYNTHETIC_HUNDRED_PLAYER_UUID = UUID("40000000-0000-0000-0000-000000000001")
SYNTHETIC_STANDARD_PLAYER_UUID = UUID("40000000-0000-0000-0000-000000000002")
SYNTHETIC_MULTI_COMP_PLAYER_UUID = UUID("40000000-0000-0000-0000-000000000003")
SYNTHETIC_ZERO_APPEARANCE_PLAYER_UUID = UUID("40000000-0000-0000-0000-000000000004")
SYNTHETIC_NONEXISTENT_PLAYER_UUID = UUID("40000000-0000-0000-0000-000000000099")

# =============================================================================
# Real Canonical Player UUIDs from Datasets
# =============================================================================

# Sanju Samson (Rajasthan Royals / Kerala / India)
SANJU_SAMSON_ORGANIZER_UUID = derive_player_uuid("organizer_2258")
SANJU_SAMSON_CRICSHEET_UUID = derive_player_uuid("a4cc73aa")

# Jos Buttler (Rajasthan Royals / Manchester Originals / England)
JOS_BUTTLER_ORGANIZER_UUID = derive_player_uuid("organizer_813")
JOS_BUTTLER_CRICSHEET_UUID = derive_player_uuid("99b75528")

# Rashid Khan (Gujarat Titans)
RASHID_KHAN_GT_UUID = derive_player_uuid("organizer_4722")

# Abdul Samad collision pair (Sunrisers Hyderabad vs Pakistan)
ABDUL_SAMAD_SRH_UUID = derive_player_uuid("organizer_7446")
ABDUL_SAMAD_PAK_UUID = derive_player_uuid("organizer_6922")

# CricSheet-only players
DP_HUGHES_CRICSHEET_UUID = derive_player_uuid("f3982af9")  # Active in BBL and The Hundred
AAA_AMSTERDAM_UUID = derive_player_uuid("b4a23876")  # In people.csv but 0 match appearances


# =============================================================================
# Builder Functions for Synthetic Test Scenarios
# =============================================================================


def build_synthetic_hundred_records(
    competition_id: UUID = HUNDRED_COMPETITION_UUID,
) -> list[CompetitionHistoryRecord]:
    """Build synthetic history records containing The Hundred with balls_per_over = 5."""
    return [
        CompetitionHistoryRecord(
            competition_id=competition_id,
            competition_name="The Hundred Men's Competition",
            season_year="2022",
            format_tag="100-ball",
            appearances=8,
            coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
            balls_per_over=5,
            provenance_record_id=derive_provenance_uuid("the_hundred:2022"),
        ),
        CompetitionHistoryRecord(
            competition_id=competition_id,
            competition_name="The Hundred Men's Competition",
            season_year="2023",
            format_tag="100-ball",
            appearances=9,
            coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
            balls_per_over=5,
            provenance_record_id=derive_provenance_uuid("the_hundred:2023"),
        ),
    ]


def build_synthetic_standard_records(
    ipl_comp_id: UUID = IPL_COMPETITION_UUID,
    smat_comp_id: UUID = SMAT_COMPETITION_UUID,
) -> list[CompetitionHistoryRecord]:
    """Build synthetic history records for standard formats with balls_per_over = 6."""
    return [
        CompetitionHistoryRecord(
            competition_id=ipl_comp_id,
            competition_name="Indian Premier League",
            season_year="2023",
            format_tag="T20",
            appearances=14,
            coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
            balls_per_over=6,
            provenance_record_id=derive_provenance_uuid("ipl:2023"),
        ),
        CompetitionHistoryRecord(
            competition_id=ipl_comp_id,
            competition_name="Indian Premier League",
            season_year="2024",
            format_tag="T20",
            appearances=15,
            coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
            balls_per_over=6,
            provenance_record_id=derive_provenance_uuid("ipl:2024"),
        ),
        CompetitionHistoryRecord(
            competition_id=smat_comp_id,
            competition_name="Syed Mushtaq Ali Trophy",
            season_year="2023/24",
            format_tag="T20",
            appearances=7,
            coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
            balls_per_over=6,
            provenance_record_id=derive_provenance_uuid("smat:2023/24"),
        ),
    ]


def build_synthetic_multi_comp_records() -> list[CompetitionHistoryRecord]:
    """Build multi-competition history including IPL, BBL, and The Hundred."""
    records = build_synthetic_standard_records()
    records.extend(build_synthetic_hundred_records())
    records.append(
        CompetitionHistoryRecord(
            competition_id=BBL_COMPETITION_UUID,
            competition_name="Big Bash League",
            season_year="2022/23",
            format_tag="T20",
            appearances=10,
            coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
            balls_per_over=6,
            provenance_record_id=derive_provenance_uuid("bbl:2022/23"),
        )
    )
    records.sort(key=lambda r: (r.competition_name, r.season_year))
    return records


# =============================================================================
# Pytest Fixtures
# =============================================================================


@pytest.fixture
def mock_registry_with_fixtures() -> CompetitionRegistry:
    """Create a lightweight CompetitionRegistry with pre-registered synthetic players."""
    registry = CompetitionRegistry(enable_cache=False)
    # Register synthetic scenarios
    registry.register_competition_history(
        SYNTHETIC_HUNDRED_PLAYER_UUID,
        build_synthetic_hundred_records(),
    )
    registry.register_competition_history(
        SYNTHETIC_STANDARD_PLAYER_UUID,
        build_synthetic_standard_records(),
    )
    registry.register_competition_history(
        SYNTHETIC_MULTI_COMP_PLAYER_UUID,
        build_synthetic_multi_comp_records(),
    )
    return registry


@pytest.fixture
def mock_career_engine(mock_registry_with_fixtures: CompetitionRegistry) -> CareerRetrievalEngine:
    """Create a CareerRetrievalEngine backed by the fixture registry."""
    return CareerRetrievalEngine(registry=mock_registry_with_fixtures)
