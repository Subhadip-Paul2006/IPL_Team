"""Unit tests for PVRE Mode B: Replacement Candidate Research Engine.

Validates:
- Domestic career discovery across formats (Ranji, SMAT, Vijay Hazare, Duleep, U16/U19/U23).
- Scorecard fallback protocol: BBB metrics return NOT_COMPUTABLE, missing junior balls stay None.
- Affirmative uncapped verification: 0 senior international caps, U-19 international caps
  do not disqualify, absence from DB does not assume uncapped.
- Candidate filtering and ReplacementCandidateEvidence compilation for SICE.
- Role-aware 16-dimension comparison matrix (D01–D16) for SICE without modifying ranking engine.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from src.contracts.pvre import (
    CareerCoverageState,
    PlayerCappedStatus,
    ReplacementCandidateEvidence,
    ReplacementResearchRequest,
)
from src.contracts.tmve import EligibilityStatus
from src.pvre.mode_b_candidate import (
    BALL_BY_BALL_GRANULARITY,
    DOMESTIC_COMPETITIONS,
    NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES,
    SCORECARD_ONLY_GRANULARITY,
    SICE_DIMENSIONS_SPEC,
    AffirmativeEligibilityVerifier,
    DomesticScorecardFallbackProtocol,
    ModeBCandidateEngine,
)

from tests.fixtures.pvre_contract_fixtures import (
    DEFAULT_EVALUATION_DATE,
    SYNTHETIC_POLICY_ID,
    SYNTHETIC_TARGET_SEASON_ID,
)

# Deterministic Test Fixtures
TEST_POLICY_ID = SYNTHETIC_POLICY_ID
TEST_SEASON_ID = SYNTHETIC_TARGET_SEASON_ID
TEST_EVAL_DATE = DEFAULT_EVALUATION_DATE


# =============================================================================
# 1. Domestic Competitions Registry & Taxonomy Tests
# =============================================================================


def test_domestic_competitions_taxonomy() -> None:
    """Verify domestic competition taxonomy covers required multi-format competitions."""
    required = [
        "Ranji Trophy",
        "Syed Mushtaq Ali Trophy",
        "Vijay Hazare Trophy",
        "Duleep Trophy",
        "BCCI Cooch Behar Trophy U-19",
        "BCCI Vinoo Mankad Trophy U-19",
        "BCCI Col CK Nayudu Trophy U-23",
        "BCCI Vijay Merchant Trophy U-16",
    ]
    for comp in required:
        assert comp in DOMESTIC_COMPETITIONS
        spec = DOMESTIC_COMPETITIONS[comp]
        assert "format" in spec
        assert "default_granularity" in spec
        assert "balls_per_over" in spec
        assert spec["balls_per_over"] == 6

    # Verify SMAT is BALL_BY_BALL while Ranji and junior are SCORECARD_ONLY
    assert DOMESTIC_COMPETITIONS["Syed Mushtaq Ali Trophy"]["default_granularity"] == BALL_BY_BALL_GRANULARITY
    assert DOMESTIC_COMPETITIONS["Ranji Trophy"]["default_granularity"] == SCORECARD_ONLY_GRANULARITY
    assert DOMESTIC_COMPETITIONS["Vijay Hazare Trophy"]["default_granularity"] == SCORECARD_ONLY_GRANULARITY
    assert DOMESTIC_COMPETITIONS["BCCI Vijay Merchant Trophy U-16"]["default_granularity"] == SCORECARD_ONLY_GRANULARITY


# =============================================================================
# 2. Scorecard Fallback Protocol Tests
# =============================================================================


def test_scorecard_fallback_batting_metrics() -> None:
    """Test scorecard fallback computes batting metrics and returns NOT_COMPUTABLE for BBB."""
    proto = DomesticScorecardFallbackProtocol()
    metrics = proto.process_innings_scorecard(
        runs=72,
        balls_faced=45,
        fours=8,
        sixes=2,
        dismissed=True,
        is_junior=False,
    )

    assert metrics["granularity"] == SCORECARD_ONLY_GRANULARITY
    assert metrics["runs"] == 72
    assert metrics["balls_faced"] == 45
    assert metrics["strike_rate"] == 160.0  # (72 / 45) * 100
    assert metrics["batting_average"] == 72.0
    assert metrics["fours"] == 8
    assert metrics["sixes"] == 2
    # Boundary runs = (8 * 4) + (2 * 6) = 32 + 12 = 44 -> 44/72 = 61.11%
    assert metrics["boundary_pct"] == 61.11

    # Delivery-level metrics MUST return NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES
    assert metrics["dot_ball_pct"] == NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES
    assert metrics["powerplay_strike_rate"] == NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES
    assert metrics["middle_overs_strike_rate"] == NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES
    assert metrics["death_overs_strike_rate"] == NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES
    assert metrics["pace_vs_spin_splits"] == NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES


def test_scorecard_fallback_missing_junior_balls_faced() -> None:
    """Test invariant: missing balls faced in junior scorecards return balls_faced=None and strike_rate=None.

    Guarantees no imputation of balls faced from runs or assumption of run-a-ball.
    """
    proto = DomesticScorecardFallbackProtocol()
    metrics = proto.process_innings_scorecard(
        runs=34,
        balls_faced=None,
        fours=4,
        sixes=0,
        dismissed=False,
        is_junior=True,
    )

    assert metrics["granularity"] == SCORECARD_ONLY_GRANULARITY
    assert metrics["runs"] == 34
    assert metrics["balls_faced"] is None
    assert metrics["strike_rate"] is None  # Strike rate cannot be computed without balls
    assert metrics["batting_average"] == 34.0
    assert metrics["dot_ball_pct"] == NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES


def test_scorecard_fallback_bowling_metrics() -> None:
    """Test scorecard fallback computes bowling metrics and returns NOT_COMPUTABLE for BBB."""
    proto = DomesticScorecardFallbackProtocol()
    # 4 overs, 28 runs conceded, 3 wickets
    metrics = proto.process_bowling_scorecard(
        overs=4.0,
        runs_conceded=28,
        wickets=3,
        legal_balls=24,
    )

    assert metrics["granularity"] == SCORECARD_ONLY_GRANULARITY
    assert metrics["overs"] == 4.0
    assert metrics["legal_balls"] == 24
    assert metrics["runs_conceded"] == 28
    assert metrics["wickets"] == 3
    assert metrics["economy_rate"] == 7.0  # 28 / 4.0
    assert metrics["bowling_strike_rate"] == 8.0  # 24 / 3
    assert metrics["bowling_average"] == 9.33  # 28 / 3

    # BBB delivery metrics MUST return NOT_COMPUTABLE
    assert metrics["bowling_dot_ball_pct"] == NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES
    assert metrics["phase_economy"] == NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES
    assert metrics["speed_summary"] == NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES
    assert metrics["line_length_summary"] == NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES


# =============================================================================
# 3. Affirmative Eligibility Policy Verification Tests
# =============================================================================


def test_affirmative_eligibility_uncapped_player() -> None:
    """Verify uncapped player with 0 senior international caps passes verification."""
    verifier = AffirmativeEligibilityVerifier()
    candidate = {
        "player_id": uuid4(),
        "canonical_name": "Ashutosh Sharma",
        "in_database": True,
        "senior_international_caps": 0,
        "youth_international_caps": 0,
        "total_domestic_matches": 28,
    }

    capped_status, elig_status, reasons = verifier.verify_candidate_eligibility(
        candidate, TEST_POLICY_ID, policy_verified=True
    )

    assert capped_status == PlayerCappedStatus.UNCAPPED
    assert elig_status == EligibilityStatus.VERIFIED_ELIGIBLE
    assert len(reasons) == 0


def test_affirmative_eligibility_senior_caps_disqualify() -> None:
    """Verify senior international appearances immediately disqualify from uncapped status."""
    verifier = AffirmativeEligibilityVerifier()
    candidate = {
        "player_id": uuid4(),
        "canonical_name": "Rinku Singh",
        "in_database": True,
        "senior_international_caps": 15,  # Has senior caps
        "youth_international_caps": 0,
        "total_domestic_matches": 60,
    }

    capped_status, elig_status, reasons = verifier.verify_candidate_eligibility(
        candidate, TEST_POLICY_ID, policy_verified=True
    )

    assert capped_status == PlayerCappedStatus.CAPPED
    assert elig_status == EligibilityStatus.VERIFIED_NOT_ELIGIBLE
    assert "SENIOR_INTERNATIONAL_CAPS_DISQUALIFIED" in reasons


def test_affirmative_eligibility_youth_caps_do_not_disqualify() -> None:
    """Verify youth international appearances (e.g. U-19 World Cup) do NOT disqualify uncapped candidate."""
    verifier = AffirmativeEligibilityVerifier()
    candidate = {
        "player_id": uuid4(),
        "canonical_name": "Vaibhav Suryavanshi",
        "in_database": True,
        "senior_international_caps": 0,  # 0 Senior international caps
        "youth_international_caps": 12,  # Played in U-19 World Cup / Asia Cup
        "total_domestic_matches": 15,
    }

    capped_status, elig_status, reasons = verifier.verify_candidate_eligibility(
        candidate, TEST_POLICY_ID, policy_verified=True
    )

    assert capped_status == PlayerCappedStatus.UNCAPPED
    assert elig_status == EligibilityStatus.VERIFIED_ELIGIBLE
    assert len(reasons) == 0


def test_negative_proof_invariant_absence_from_database() -> None:
    """Verify negative proof invariant: absence from database is never proof of uncapped status."""
    verifier = AffirmativeEligibilityVerifier()
    candidate = {
        "player_id": None,  # Not resolved in database
        "canonical_name": "Unknown Domestic Prospect",
        "in_database": False,
        "senior_international_caps": 0,
    }

    capped_status, elig_status, reasons = verifier.verify_candidate_eligibility(
        candidate, TEST_POLICY_ID, policy_verified=True
    )

    assert capped_status == PlayerCappedStatus.UNVERIFIED
    assert elig_status == EligibilityStatus.NOT_ASSESSED
    assert "UNKNOWN_PLAYER_NOT_IN_DATABASE" in reasons


def test_unverified_eligibility_policy_blocks_candidate() -> None:
    """Verify missing or unverified eligibility policy ID blocks candidate entry."""
    verifier = AffirmativeEligibilityVerifier()
    candidate = {
        "player_id": uuid4(),
        "canonical_name": "Domestic Player",
        "in_database": True,
        "senior_international_caps": 0,
    }

    # Policy ID is None
    capped_status, elig_status, reasons = verifier.verify_candidate_eligibility(
        candidate, None, policy_verified=False
    )

    assert capped_status == PlayerCappedStatus.UNVERIFIED
    assert elig_status == EligibilityStatus.NOT_ASSESSED
    assert "UNVERIFIED_ELIGIBILITY_POLICY" in reasons


# =============================================================================
# 4. Mode B Candidate Engine Filtering & Ingestion Tests
# =============================================================================


@pytest.fixture
def sample_candidate_pool() -> list[dict]:
    """Fixture providing a diverse candidate pool of domestic players."""
    pid1, pid2, pid3, pid4 = uuid4(), uuid4(), uuid4(), uuid4()
    return [
        {
            "player_id": pid1,
            "canonical_name": "Candidate Batter A",
            "primary_role": "MIDDLE_ORDER_BATTER",
            "secondary_role": "FINISHER_BATTER",
            "batting_hand": "RIGHT",
            "bowling_style": "RIGHT_ARM_OFF_BREAK",
            "age_at_evaluation": 23.5,
            "senior_international_caps": 0,
            "youth_international_caps": 5,
            "in_database": True,
            "total_matches": 22,
            "domestic_t20_metrics": {
                "strike_rate": 154.2,
                "average": 34.5,
                "boundary_pct": 21.0,
                "dot_ball_pct": 30.5,
            },
            "first_class_metrics": {"matches": 10, "runs": 620, "average": 38.75},
            "sample_indicators": {"matches": 22, "innings": 20, "balls_faced": 380, "wickets": 0},
            "evidence_tier": 1,
            "career_coverage_state": CareerCoverageState.COMPLETE_WITHIN_VERIFIED_SOURCES.value,
        },
        {
            "player_id": pid2,
            "canonical_name": "Candidate Finisher B",
            "primary_role": "FINISHER_BATTER",
            "secondary_role": "WICKETKEEPER",
            "batting_hand": "LEFT",
            "bowling_style": None,
            "age_at_evaluation": 21.0,
            "senior_international_caps": 0,
            "youth_international_caps": 0,
            "in_database": True,
            "total_matches": 18,
            "domestic_t20_metrics": {
                "strike_rate": 178.6,
                "average": 29.0,
                "boundary_pct": 25.5,
                "dot_ball_pct": 28.0,
            },
            "sample_indicators": {"matches": 18, "innings": 16, "balls_faced": 210, "wickets": 0},
            "evidence_tier": 1,
            "career_coverage_state": CareerCoverageState.COMPLETE_WITHIN_VERIFIED_SOURCES.value,
        },
        {
            "player_id": pid3,
            "canonical_name": "Candidate Bowler C",
            "primary_role": "PACE_BOWLER",
            "secondary_role": None,
            "batting_hand": "RIGHT",
            "bowling_style": "RIGHT_ARM_FAST",
            "age_at_evaluation": 22.0,
            "senior_international_caps": 0,
            "youth_international_caps": 8,
            "in_database": True,
            "total_matches": 25,
            "domestic_t20_metrics": {
                "economy_rate": 7.45,
                "bowling_strike_rate": 15.2,
                "bowling_dot_ball_pct": 48.0,
            },
            "sample_indicators": {"matches": 25, "innings": 25, "balls_faced": 20, "wickets": 32},
            "evidence_tier": 2,
            "career_coverage_state": CareerCoverageState.COMPLETE_WITHIN_VERIFIED_SOURCES.value,
        },
        {
            "player_id": pid4,
            "canonical_name": "Senior Capped Player D",
            "primary_role": "MIDDLE_ORDER_BATTER",
            "batting_hand": "RIGHT",
            "age_at_evaluation": 29.0,
            "senior_international_caps": 20,  # CAPPED
            "in_database": True,
            "total_matches": 80,
            "domestic_t20_metrics": {"strike_rate": 140.0, "average": 32.0},
        },
    ]


def test_research_replacement_candidates_role_and_uncapped(sample_candidate_pool: list[dict]) -> None:
    """Test candidate research filters by role and enforces uncapped eligibility."""
    engine = ModeBCandidateEngine()
    request = ReplacementResearchRequest(
        research_run_id=uuid4(),
        target_season_id=TEST_SEASON_ID,
        evaluation_date=TEST_EVAL_DATE,
        target_role="MIDDLE_ORDER_BATTER",
        must_be_uncapped=True,
        max_age=25.0,
        min_domestic_matches=10,
        candidate_pool_limit=10,
    )

    results = engine.research_replacement_candidates(request, sample_candidate_pool)

    # Capped player D must be excluded; Bowler C must be excluded (wrong role);
    # Candidate Batter A must be included.
    names = [r.canonical_name for r in results]
    assert "Candidate Batter A" in names
    assert "Senior Capped Player D" not in names
    assert "Candidate Bowler C" not in names
    assert all(isinstance(r, ReplacementCandidateEvidence) for r in results)
    assert all(r.ipl_uncapped_eligibility == "VERIFIED_ELIGIBLE" for r in results)


def test_research_replacement_candidates_batting_hand_filter(sample_candidate_pool: list[dict]) -> None:
    """Test candidate research filters by batting hand constraint."""
    engine = ModeBCandidateEngine()
    request = ReplacementResearchRequest(
        research_run_id=uuid4(),
        target_season_id=TEST_SEASON_ID,
        evaluation_date=TEST_EVAL_DATE,
        target_role="FINISHER_BATTER",
        batting_hand="LEFT",
        must_be_uncapped=True,
        candidate_pool_limit=10,
    )

    results = engine.research_replacement_candidates(request, sample_candidate_pool)
    names = [r.canonical_name for r in results]
    assert "Candidate Finisher B" in names
    assert "Candidate Batter A" not in names


def test_research_replacement_candidates_max_age_filter(sample_candidate_pool: list[dict]) -> None:
    """Test candidate research filters by max age."""
    engine = ModeBCandidateEngine()
    request = ReplacementResearchRequest(
        research_run_id=uuid4(),
        target_season_id=TEST_SEASON_ID,
        evaluation_date=TEST_EVAL_DATE,
        target_role="BATTER",
        max_age=22.0,  # Excludes Candidate Batter A (age 23.5)
        must_be_uncapped=True,
        candidate_pool_limit=10,
    )

    results = engine.research_replacement_candidates(request, sample_candidate_pool)
    for r in results:
        assert r.age_at_evaluation <= 22.0


def test_research_replacement_candidates_min_matches_filter(sample_candidate_pool: list[dict]) -> None:
    """Test candidate research filters by minimum domestic matches."""
    engine = ModeBCandidateEngine()
    request = ReplacementResearchRequest(
        research_run_id=uuid4(),
        target_season_id=TEST_SEASON_ID,
        evaluation_date=TEST_EVAL_DATE,
        target_role="BATTER",
        min_domestic_matches=20,  # Excludes Finisher B (18 matches)
        must_be_uncapped=True,
        candidate_pool_limit=10,
    )

    results = engine.research_replacement_candidates(request, sample_candidate_pool)
    for r in results:
        assert r.sample_indicators["matches"] >= 20


# =============================================================================
# 5. SICE 16-Dimension Role-Aware Comparison Matrix Tests
# =============================================================================


def test_sice_16_dimensions_spec_completeness() -> None:
    """Verify SICE 16-dimension specification contains exact D01 through D16 definitions."""
    assert len(SICE_DIMENSIONS_SPEC) == 16
    for i in range(1, 17):
        key = f"D{i:02d}"
        assert key in SICE_DIMENSIONS_SPEC
        assert "name" in SICE_DIMENSIONS_SPEC[key]
        assert "metric_basis" in SICE_DIMENSIONS_SPEC[key]


def test_sice_comparison_matrix_generation() -> None:
    """Test compiling role-aware 16-dimension comparison matrix between incumbent and candidate."""
    engine = ModeBCandidateEngine()
    candidate_id = uuid4()
    candidate = ReplacementCandidateEvidence(
        candidate_player_id=candidate_id,
        canonical_name="Ashutosh Sharma",
        age_at_evaluation=24.5,
        primary_role="FINISHER_BATTER",
        batting_hand="RIGHT",
        ipl_uncapped_eligibility="VERIFIED_ELIGIBLE",
        verified_policy_id=TEST_POLICY_ID,
        domestic_t20_metrics={
            "strike_rate": 182.4,
            "average": 31.5,
            "boundary_pct": 24.8,
            "dot_ball_pct": 28.2,
            "powerplay_strike_rate": 140.0,
            "middle_overs_strike_rate": 165.0,
            "death_overs_strike_rate": 215.0,
            "economy_rate": None,
        },
        sample_indicators={"matches": 28, "innings": 25, "balls_faced": 340, "wickets": 0},
        evidence_tier=1,
        career_coverage_state=CareerCoverageState.COMPLETE_WITHIN_VERIFIED_SOURCES.value,
    )

    incumbent_metrics = {
        "strike_rate": 145.2,
        "average": 35.0,
        "boundary_pct": 21.4,
        "dot_ball_pct": 32.1,
        "powerplay_strike_rate": 138.0,
        "middle_overs_strike_rate": 142.0,
        "death_overs_strike_rate": 190.0,
        "age_at_evaluation": 30.5,
    }

    matrix = engine.compile_sice_comparison_matrix(candidate, incumbent_metrics)

    # Must contain all 16 dimensions D01 to D16
    assert len(matrix) == 16
    assert "D01" in matrix
    assert "D15" in matrix
    assert "D16" in matrix

    # Verify Base Scoring Rate (D01) delta calculation
    d01 = matrix["D01"]
    assert d01["dimension_name"] == "Base Scoring Rate"
    assert d01["candidate_metric"] == 182.4
    assert d01["incumbent_metric"] == 145.2
    assert d01["relative_delta"] == round(182.4 - 145.2, 2)  # +37.2
    assert d01["computable"] is True

    # Verify Dismissal Resistance (D02) delta calculation
    d02 = matrix["D02"]
    assert d02["candidate_metric"] == 31.5
    assert d02["incumbent_metric"] == 35.0
    assert d02["relative_delta"] == round(31.5 - 35.0, 2)  # -3.5

    # Verify Age Trajectory Delta (D15)
    d15 = matrix["D15"]
    assert d15["candidate_metric"] == 24.5
    assert d15["incumbent_metric"] == 30.5
    assert d15["relative_delta"] == round(24.5 - 30.5, 2)  # -6.0 younger


def test_sice_comparison_matrix_scorecard_only_not_computable() -> None:
    """Test scorecard-only candidate metrics return computable=False for BBB dimensions."""
    engine = ModeBCandidateEngine()
    candidate = ReplacementCandidateEvidence(
        candidate_player_id=uuid4(),
        canonical_name="Ranji Red Ball Prospect",
        age_at_evaluation=21.0,
        primary_role="MIDDLE_ORDER_BATTER",
        ipl_uncapped_eligibility="VERIFIED_ELIGIBLE",
        verified_policy_id=TEST_POLICY_ID,
        domestic_t20_metrics={
            "strike_rate": 130.0,
            "average": 42.0,
            "dot_ball_pct": NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES,  # Scorecard only
            "powerplay_strike_rate": NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES,
        },
        sample_indicators={"matches": 15, "innings": 14, "balls_faced": 200},
        evidence_tier=1,
    )

    incumbent_metrics = {"dot_ball_pct": 32.0}
    matrix = engine.compile_sice_comparison_matrix(candidate, incumbent_metrics)

    # Dot ball suppression (D04) must flag computable=False
    d04 = matrix["D04"]
    assert d04["candidate_metric"] == NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES
    assert d04["computable"] is False
    assert d04["relative_delta"] is None
