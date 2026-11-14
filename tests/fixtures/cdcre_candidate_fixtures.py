"""Test fixtures for CDCRE Pre-Identity Candidate Discovery (Milestone 2).

Provides test data, collision expectations, and helper factories
for testing candidate discovery without hardcoding or fabrication.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest
from src.contracts.cdcre import (
    AmbiguityStatus,
    CandidateDiscoveryResult,
    CandidatePlayerRecord,
)

# =============================================================================
# The Seven Known Name Collision Fixtures from Phase 1B & Organizer Dataset
# =============================================================================

KNOWN_COLLISION_FIXTURES: list[dict[str, Any]] = [
    {
        "name": "Abdul Samad",
        "cand1_id": "organizer_7446",
        "cand1_pid": "7446",
        "cand1_teams": ["Lucknow Super Giants", "Sunrisers Hyderabad"],
        "cand2_id": "organizer_6922",
        "cand2_pid": "6922",
        "cand2_teams": ["Pakistan", "Pakistan A"],
    },
    {
        "name": "Bashir Ahmad",
        "cand1_id": "organizer_29833",
        "cand1_pid": "29833",
        "cand1_teams": ["Afghanistan"],
        "cand2_id": "organizer_39479",
        "cand2_pid": "39479",
        "cand2_teams": ["Afghanistan A"],
    },
    {
        "name": "Basil Hameed",
        "cand1_id": "organizer_8638",
        "cand1_pid": "8638",
        "cand1_teams": ["United Arab Emirates"],
        "cand2_id": "organizer_39444",
        "cand2_pid": "39444",
        "cand2_teams": ["United Arab Emirates"],
    },
    {
        "name": "Haider Ali",
        "cand1_id": "organizer_7338",
        "cand1_pid": "7338",
        "cand1_teams": ["Pakistan", "Pakistan A"],
        "cand2_id": "organizer_28756",
        "cand2_pid": "28756",
        "cand2_teams": ["United Arab Emirates"],
    },
    {
        "name": "Mohammad Ali",
        "cand1_id": "organizer_3083",
        "cand1_pid": "3083",
        "cand1_teams": ["Pakistan"],
        "cand2_id": "organizer_20229",
        "cand2_pid": "20229",
        "cand2_teams": ["Pakistan"],
    },
    {
        "name": "Muhammad Farooq",
        "cand1_id": "organizer_27373",
        "cand1_pid": "27373",
        "cand1_teams": ["United Arab Emirates"],
        "cand2_id": "organizer_28978",
        "cand2_pid": "28978",
        "cand2_teams": ["United Arab Emirates"],
    },
    {
        "name": "Rashid Khan",
        "cand1_id": "organizer_4722",
        "cand1_pid": "4722",
        "cand1_teams": ["Afghanistan", "Gujarat Titans"],
        "cand2_id": "organizer_20172",
        "cand2_pid": "20172",
        "cand2_teams": ["Nepal"],
    },
]

# Single-match player fixtures
SINGLE_MATCH_FIXTURES: list[dict[str, Any]] = [
    {
        "query": "Sanju Samson",
        "expected_canonical_name": "Sanju Samson",
        "expected_source_id": "organizer_2258",
        "expected_team": "Rajasthan Royals",
    },
    {
        "query": "SV Samson",
        "expected_canonical_name": "Sanju Samson",
        "expected_source_id": "organizer_2258",
        "expected_team": "Rajasthan Royals",
    },
    {
        "query": "AAA Amsterdam",
        "expected_canonical_name": "AAA Amsterdam",
        "expected_source_id": "cricsheet_b4a23876",
        "expected_team": None,
    },
]

# Non-existent query fixtures
NON_EXISTENT_QUERIES: list[str] = [
    "Nonexistent Player XYZ 12345",
    "Fictional Character Holmes",
    "Completely Unknown Batter 99",
]

# Whitespace and punctuation test fixtures
PUNCTUATION_CASING_FIXTURES: list[dict[str, Any]] = [
    {
        "canonical": "Rashid Khan",
        "variants": [
            "rashid khan",
            "RASHID KHAN",
            "  Rashid   Khan  ",
            "Rashid-Khan",
            "Rashid   Khan",
        ],
        "expected_status": AmbiguityStatus.MULTIPLE,
    },
    {
        "canonical": "Abdul Samad",
        "variants": [
            "abdul samad",
            "ABDUL SAMAD",
            "  Abdul   Samad  ",
            "Abdul-Samad",
        ],
        "expected_status": AmbiguityStatus.MULTIPLE,
    },
    {
        "canonical": "Sanju Samson",
        "variants": [
            "sanju samson",
            "SANJU SAMSON",
            "  Sanju   Samson  ",
            "Sanju-Samson",
        ],
        "expected_status": AmbiguityStatus.SINGLE_CORROBORATED,
    },
]


def build_candidate_player_record(
    player_id: UUID | None = None,
    canonical_name: str = "Test Player",
    source_id: str | None = "organizer_1001",
    teams: list[str] | None = None,
    competitions: list[str] | None = None,
    confidence: float = 1.0,
) -> CandidatePlayerRecord:
    """Helper to construct a validated CandidatePlayerRecord."""
    return CandidatePlayerRecord(
        player_id=player_id,
        canonical_name=canonical_name,
        source_id=source_id,
        teams=teams if teams is not None else ["Rajasthan Royals"],
        competitions=competitions if competitions is not None else ["IPL 2024"],
        confidence=confidence,
    )


def build_candidate_discovery_result(
    raw_name_query: str = "Test Player",
    ambiguity_status: AmbiguityStatus = AmbiguityStatus.SINGLE_CORROBORATED,
    candidates: list[CandidatePlayerRecord] | None = None,
    collision_detected: bool = False,
) -> CandidateDiscoveryResult:
    """Helper to construct a validated CandidateDiscoveryResult."""
    if candidates is None:
        candidates = [build_candidate_player_record()]
    return CandidateDiscoveryResult(
        raw_name_query=raw_name_query,
        ambiguity_status=ambiguity_status,
        candidates=candidates,
        collision_detected=collision_detected,
    )


@pytest.fixture
def known_collisions_list() -> list[dict[str, Any]]:
    """Fixture providing all 7 collision test dictionaries."""
    return KNOWN_COLLISION_FIXTURES


@pytest.fixture
def single_match_fixtures() -> list[dict[str, Any]]:
    """Fixture providing single corroborated match test dictionaries."""
    return SINGLE_MATCH_FIXTURES


@pytest.fixture
def non_existent_queries() -> list[str]:
    """Fixture providing non-existent query strings."""
    return NON_EXISTENT_QUERIES
