"""Adversarial and boundary condition test suite for Mother Intelligence Engine (MIE).

Verifies:
1. Multi-candidate collision detection and user clarification routing (AC-03).
2. Contradictory DOB evidence immediately triggering REVIEW_REQUIRED (AC-29).
3. Contradictory external career statistics triggering REVIEW_REQUIRED (AC-29).
4. Zero-sample and walkover edge cases with NULL safety (Rule R1).
5. High-throughput sequential calls deterministic reproducibility.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from src.mie.contracts import OverallVerificationStatus
from src.mie.orchestrator import MotherIntelligenceEngine


def test_adversarial_name_collision_triggers_review_required() -> None:
    """AC-03: Multi-candidate name collision routes to user clarification / review queue."""
    mie = MotherIntelligenceEngine()

    # Register two distinct players with identical name "Amit Sharma"
    id_1 = str(uuid4())
    id_2 = str(uuid4())
    mie.pire.resolver.register_player(
        canonical_player_id=id_1,
        canonical_name="Amit Sharma",
        teams={"Delhi"},
        birth_year=1998,
    )
    mie.pire.resolver.register_player(
        canonical_player_id=id_2,
        canonical_name="Amit Sharma",
        teams={"Punjab"},
        birth_year=2003,
    )

    # Force collision flag
    mie.pire.resolver.players[id_1].is_name_collision = True
    mie.pire.resolver.players[id_2].is_name_collision = True

    # Resolve without context disambiguation
    report = mie.request_player_intelligence("Amit Sharma")

    assert report.is_review_required is True
    assert report.verification.overall_status in (
        OverallVerificationStatus.REVIEW_REQUIRED,
        OverallVerificationStatus.CONFLICT,
    )
    assert report.safety_dossier is not None


def test_adversarial_conflicting_dob_evidence_triggers_review_required() -> None:
    """AC-29: Conflicting dates of birth across sources immediately routes to REVIEW_REQUIRED."""
    mie = MotherIntelligenceEngine()
    player_id = UUID("66666666-6666-6666-6666-666666666666")

    mie.pire.resolver.register_player(
        canonical_player_id=str(player_id),
        canonical_name="Target Prospect",
    )

    # Inject conflicting DOB assertions across sources
    dob_evidence = [
        {"source_id": "bcci_roster", "dob": "2004-05-10"},
        {"source_id": "state_association", "dob": "2003-11-22"},
    ]

    report = mie.request_player_intelligence(
        query="Target Prospect",
        mock_data={"dob_evidence": dob_evidence},
    )

    assert report.is_review_required is True
    assert report.verification.overall_status in (
        OverallVerificationStatus.REVIEW_REQUIRED,
        OverallVerificationStatus.CONFLICT,
    )


def test_adversarial_conflicting_career_statistics_triggers_review_required() -> None:
    """AC-29: Materially conflicting match counts across authoritative providers triggers review."""
    mie = MotherIntelligenceEngine()
    player_id = UUID("77777777-7777-7777-7777-777777777777")

    mie.pire.resolver.register_player(
        canonical_player_id=str(player_id),
        canonical_name="Statistical Conflict Player",
    )

    statistical_sources = [
        {"provider": "bcci.tv", "matches_count": 32, "runs": 950},
        {"provider": "espncricinfo.com", "matches_count": 38, "runs": 1150},
    ]

    report = mie.request_player_intelligence(
        query="Statistical Conflict Player",
        mock_data={"statistical_sources": statistical_sources},
    )

    assert report.is_review_required is True


def test_adversarial_zero_sample_null_safety() -> None:
    """Rule R1: Missing or unobserved performance metrics must remain NULL, never 0.0."""
    mie = MotherIntelligenceEngine()
    player_id = UUID("88888888-8888-8888-8888-888888888888")

    mie.pire.resolver.register_player(
        canonical_player_id=str(player_id),
        canonical_name="Zero Sample Player",
    )

    report = mie.request_player_intelligence(
        query="Zero Sample Player",
        mock_data={"deliveries": []},
    )

    perf = report.performance
    assert perf.samples.balls_faced == 0
    # Average and strike rate must be None, NOT 0.0!
    if perf.batting:
        assert perf.batting.batting_average is None
        assert perf.batting.strike_rate is None
    if perf.bowling:
        assert perf.bowling.economy_rate is None
        assert perf.bowling.bowling_average is None


def test_sequential_determinism_invariant() -> None:
    """NFR-01: Repeated identical queries produce deterministic identical output reports."""
    mie = MotherIntelligenceEngine()
    player_id = UUID("99999999-9999-9999-9999-999999999999")

    mie.pire.resolver.register_player(
        canonical_player_id=str(player_id),
        canonical_name="Deterministic Test Player",
    )

    report1 = mie.request_player_intelligence("Deterministic Test Player")
    report2 = mie.request_player_intelligence("Deterministic Test Player")

    assert report1.canonical_name == report2.canonical_name
    assert report1.verification.overall_status == report2.verification.overall_status
    assert report1.verification.rr_relationship_state == report2.verification.rr_relationship_state
    assert (
        report1.verification.ipl_uncapped_eligibility
        == report2.verification.ipl_uncapped_eligibility
    )
