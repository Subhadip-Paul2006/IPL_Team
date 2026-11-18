"""End-to-End Pipeline Integration Tests for PVRE (10 Mandatory Phase 4B Scenarios).

Implements and validates all 10 mandatory Phase 4B test scenarios from PHASES.md:
1. Sanju Samson: Verified RR Incumbent -> Mode A -> RETAIN_SIGNAL.
2. Historical RR Player / Squad-Only: 0 match stats for squad-only seasons.
3. Verified Uncapped Candidate: SMAT breakout -> Mode B -> Candidate Pool.
4. Verified Capped Non-RR: Virat Kohli -> ROUTED_OUT_OF_SCOPE.
5. Unknown Player Absent from DB: Domestic prospect -> REVIEW_REQUIRED.
6. Duplicate Identities / Collision: "Amit Sharma" -> REVIEW_REQUIRED.
7. Conflicting DOB Records: Passport vs BCCI roster -> REVIEW_REQUIRED.
8. Missing Domestic Datasets: Unindexed season -> PARTIAL_COVERAGE.
9. Conflicting External Sources: Discrepant stats -> REVIEW_REQUIRED.
10. Incomplete Career Coverage: Truncated career -> PARTIAL_COVERAGE.

Also validates:
- PVREngine facade ServiceBoundary integration, health_check(), and repository persistence.
- Mode B replacement candidate research and SICE 16-dimension role-aware comparison matrix.
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from src.contracts.pvre import (
    CareerCoverageState,
    PlayerCappedStatus,
    PVREReviewStatus,
    ReplaceabilitySignal,
    ReplacementResearchRequest,
    ResearchMode,
    RouteStatus,
)
from src.pvre.engine import PVREngine
from src.pvre.mode_b_candidate import SICE_DIMENSIONS_SPEC
from src.pvre.repository import PVRERepository, RepositoryMode
from src.pvre.safety_review import SafetyReviewReasonCode

from tests.fixtures.pvre_contract_fixtures import (
    SYNTHETIC_POLICY_ID,
    SYNTHETIC_TARGET_SEASON_ID,
    build_mode_a_incumbent_request,
    build_out_of_scope_request,
    build_pvre_request,
)


@pytest.fixture
def pvre_engine() -> PVREngine:
    """Fixture providing an initialized PVREngine facade with in-memory persistence."""
    repo = PVRERepository(mode=RepositoryMode.IN_MEMORY)
    return PVREngine(repository=repo)


# =============================================================================
# Scenario 1: Sanju Samson (Verified RR Incumbent -> Mode A -> RETAIN_SIGNAL)
# =============================================================================


def test_scenario_1_sanju_samson_verified_rr_incumbent(pvre_engine: PVREngine) -> None:
    """Scenario 1: Sanju Samson (t_eval = 2026-11-01).

    PIRE resolves player ID; TMVE confirms CURRENT_RR; Module A1 analyzes RR seasons;
    Module A2 assesses recent window; Module A3 emits RETAIN_SIGNAL.
    """
    eval_date = date(2026, 11, 1)

    req = build_mode_a_incumbent_request(
        evaluation_date=eval_date,
        research_window_years=3,
    )

    # Realistic sample records for Sanju Samson
    rr_matches = [
        {
            "match_id": uuid4(),
            "match_date": date(2024, 4, 15),
            "season_year": "2024",
            "competition_name": "Indian Premier League",
            "team_name": "Rajasthan Royals",
            "opponent_name": "Gujarat Titans",
            "innings": 1,
            "batted": True,
            "runs": 68,
            "balls_faced": 38,
            "batting_runs": 68,
            "batting_balls": 38,
            "fours": 7,
            "sixes": 2,
            "dismissal": "not out",
            "balls_bowled": 0,
            "runs_conceded": 0,
            "wickets": 0,
            "catches": 1,
            "stumpings": 0,
        },
        {
            "match_id": uuid4(),
            "match_date": date(2025, 5, 2),
            "season_year": "2025",
            "competition_name": "Indian Premier League",
            "team_name": "Rajasthan Royals",
            "opponent_name": "Chennai Super Kings",
            "innings": 2,
            "batted": True,
            "runs": 82,
            "balls_faced": 45,
            "batting_runs": 82,
            "batting_balls": 45,
            "fours": 8,
            "sixes": 4,
            "dismissal": "caught",
            "balls_bowled": 0,
            "runs_conceded": 0,
            "wickets": 0,
            "catches": 2,
            "stumpings": 1,
        },
    ]

    squad_records = [
        {"season": 2013, "squad_name": "Rajasthan Royals", "contract_type": "Auction"},
        {"season": 2014, "squad_name": "Rajasthan Royals", "contract_type": "Retained"},
        {"season": 2015, "squad_name": "Rajasthan Royals", "contract_type": "Retained"},
        {"season": 2018, "squad_name": "Rajasthan Royals", "contract_type": "Auction"},
        {"season": 2019, "squad_name": "Rajasthan Royals", "contract_type": "Retained"},
        {"season": 2020, "squad_name": "Rajasthan Royals", "contract_type": "Retained"},
        {"season": 2021, "squad_name": "Rajasthan Royals", "contract_type": "Retained"},
        {"season": 2022, "squad_name": "Rajasthan Royals", "contract_type": "Retained"},
        {"season": 2023, "squad_name": "Rajasthan Royals", "contract_type": "Retained"},
        {"season": 2024, "squad_name": "Rajasthan Royals", "contract_type": "Retained"},
        {"season": 2025, "squad_name": "Rajasthan Royals", "contract_type": "Retained"},
        {"season": 2026, "squad_name": "Rajasthan Royals", "contract_type": "Retained"},
    ]

    context = {
        "squad_records": squad_records,
        "rr_match_records": rr_matches,
        "primary_role": "TOP_ORDER_BATTER",
        "date_of_birth": date(1994, 11, 11),
        "in_database": True,
    }

    output = pvre_engine.execute_player_research(req, context=context)

    # Verifications
    assert output.route_status == RouteStatus.ROUTED_RR_INCUMBENT.value
    assert output.research_mode == ResearchMode.MODE_A.value
    assert output.review_status == PVREReviewStatus.CLEAR.value

    # Module A1: RR Historical Profile
    assert output.rr_historical_profile is not None
    assert output.rr_historical_profile["total_seasons"] >= 10
    assert "2016" not in output.rr_historical_profile["seasons_active"]
    assert "2017" not in output.rr_historical_profile["seasons_active"]

    # Module A2: Recent Global Performance
    assert output.recent_global_performance is not None
    assert output.recent_global_performance["weighted_strike_rate"] > 140.0

    # Module A3: Replaceability Signal
    assert output.replaceability_assessment is not None
    assert (
        output.replaceability_assessment["signal"]
        == ReplaceabilitySignal.RETAIN_SIGNAL.value
    )

    # Persisted in repository
    retrieved = pvre_engine.repository.get_research_output(output.research_run_id)
    assert retrieved is not None
    assert retrieved.canonical_name == "Sanju Samson"


# =============================================================================
# Scenario 2: Historical RR Player / Squad-Only Alumnus (0 Match Stats)
# =============================================================================


def test_scenario_2_historical_rr_squad_only_alumnus(pvre_engine: PVREngine) -> None:
    """Scenario 2: Historical RR Player / Squad-Only Alumnus.

    TMVE confirms HISTORICAL_RR_SQUAD_ONLY; Module A1 strictly separates squad
    inclusion from appearances; zero batting/bowling stats credited for squad-only seasons.
    """
    req = build_pvre_request(
        canonical_name="Reserve Batter Alumnus",
        rr_relationship_state="HISTORICAL_RR_SQUAD_ONLY",
        rr_current_state="NOT_CURRENT",
    )

    squad_records = [
        {"season": 2019, "squad_name": "Rajasthan Royals", "contract_type": "Auction", "appearances": 0},
        {"season": 2020, "squad_name": "Rajasthan Royals", "contract_type": "Retained", "appearances": 0},
    ]
    # 0 match appearances in Playing XI
    rr_matches: list[dict] = []

    context = {
        "squad_records": squad_records,
        "rr_match_records": rr_matches,
        "primary_role": "MIDDLE_ORDER_BATTER",
        "in_database": True,
    }

    output = pvre_engine.execute_player_research(req, context=context)

    assert output.route_status == RouteStatus.ROUTED_RR_INCUMBENT.value
    assert output.rr_relationship_state == "HISTORICAL_RR_SQUAD_ONLY"

    # Module A1 verifies zero stats for squad-only seasons
    rr_profile = output.rr_historical_profile
    assert rr_profile is not None
    assert rr_profile["total_matches"] == 0
    assert len(rr_profile["squad_only_seasons"]) == 2
    assert "2019" in rr_profile["squad_only_seasons"]
    assert "2020" in rr_profile["squad_only_seasons"]

    # All batting/bowling aggregates must be zero (not credited with false stats)
    assert rr_profile["total_runs"] == 0
    assert rr_profile["total_balls_faced"] == 0
    assert rr_profile["total_wickets"] == 0


# =============================================================================
# Scenario 3: Verified Uncapped Candidate (SMAT Breakout Performer)
# =============================================================================


def test_scenario_3_verified_uncapped_candidate_mode_b(pvre_engine: PVREngine) -> None:
    """Scenario 3: Domestic T20 breakout performer (young SMAT star).

    PIRE resolves identity; TMVE confirms NO_VERIFIED_RR_RELATIONSHIP;
    0 international caps; target policy compliance verified; Mode B domestic discovery.
    """
    req = build_pvre_request(
        canonical_name="Young SMAT Star",
        player_capped_status=PlayerCappedStatus.UNCAPPED.value,
        ipl_uncapped_eligibility="VERIFIED_ELIGIBLE",
        rr_relationship_state="NO_VERIFIED_RR_RELATIONSHIP",
        rr_current_state="NOT_CURRENT",
    )

    context = {
        "in_database": True,
        "policy_verified": True,
        "primary_role": "OPENING_BATTER",
        "age_at_evaluation": 20.4,
        "domestic_t20_metrics": {
            "matches": 14,
            "innings": 14,
            "runs": 485,
            "balls_faced": 320,
            "strike_rate": 151.56,
            "average": 40.41,
            "boundary_pct": 21.25,
            "dot_ball_pct": 34.06,
        },
    }

    output = pvre_engine.execute_player_research(req, context=context)

    assert output.route_status == RouteStatus.ROUTED_UNCAPPED_CANDIDATE.value
    assert output.research_mode == ResearchMode.MODE_B.value
    assert output.ipl_uncapped_eligibility == "VERIFIED_ELIGIBLE"
    assert output.review_status == PVREReviewStatus.CLEAR.value

    # Mode B outputs populated; Mode A outputs None
    assert output.complete_career_profile is not None
    assert output.rr_historical_profile is None
    assert output.replaceability_assessment is None


# =============================================================================
# Scenario 4: Verified Capped Non-RR Player (Virat Kohli -> OUT_OF_SCOPE)
# =============================================================================


def test_scenario_4_verified_capped_non_rr_out_of_scope(pvre_engine: PVREngine) -> None:
    """Scenario 4: Virat Kohli / Jasprit Bumrah.

    Senior international caps verified; player is CAPPED; NO_VERIFIED_RR_RELATIONSHIP.
    Deterministically routes to OUT_OF_SCOPE; candidate pool entry blocked.
    """
    req = build_out_of_scope_request()

    output = pvre_engine.execute_player_research(req)

    assert output.route_status == RouteStatus.ROUTED_OUT_OF_SCOPE.value
    assert output.research_mode == ResearchMode.OUT_OF_SCOPE.value
    assert output.player_capped_status == PlayerCappedStatus.CAPPED.value
    assert output.review_status == PVREReviewStatus.CLEAR.value

    # Candidate pool entry blocked: profiles remain empty
    assert output.complete_career_profile is None
    assert output.rr_historical_profile is None
    assert output.replaceability_assessment is None
    assert "out_of_scope_reason" in output.data_quality_summary


# =============================================================================
# Scenario 5: Unknown Player Absent from Database (REVIEW_REQUIRED)
# =============================================================================


def test_scenario_5_unknown_player_database_absence(pvre_engine: PVREngine) -> None:
    """Scenario 5: Newly registered domestic U-19 prospect absent from internal DB.

    Mother Controller defaults player_capped_status = 'UNVERIFIED',
    ipl_uncapped_eligibility = 'NOT_ASSESSED'; routes to REVIEW_REQUIRED.
    Negative proof invariant: Never assumes unknown player is uncapped.
    """
    req = build_pvre_request(
        player_id=None,
        canonical_name="Newly Registered U-19 Bowler",
        player_capped_status=PlayerCappedStatus.UNVERIFIED.value,
        ipl_uncapped_eligibility="NOT_ASSESSED",
        rr_relationship_state="NO_VERIFIED_RR_RELATIONSHIP",
        rr_current_state="NOT_CURRENT",
    )

    context = {"in_database": False}
    output = pvre_engine.execute_player_research(req, context=context)

    assert output.route_status == RouteStatus.ROUTED_SAFETY_REVIEW.value
    assert output.research_mode == ResearchMode.REVIEW_REQUIRED.value
    assert output.review_status == PVREReviewStatus.REVIEW_REQUIRED.value
    assert (
        SafetyReviewReasonCode.UNKNOWN_PLAYER_NOT_IN_DATABASE.value
        in output.review_reason_codes
    )

    # Dossier was compiled and persisted
    dossier = pvre_engine.controller.last_dossier
    assert dossier is not None
    assert SafetyReviewReasonCode.UNKNOWN_PLAYER_NOT_IN_DATABASE.value in dossier.review_reason_codes


# =============================================================================
# Scenario 6: Duplicate Identities / Collision ("Amit Sharma" -> REVIEW_REQUIRED)
# =============================================================================


def test_scenario_6_duplicate_identities_collision(pvre_engine: PVREngine) -> None:
    """Scenario 6: Two distinct domestic players with identical names ("Amit Sharma").

    PIRE detects multiple candidate entities; Mother Controller halts automated processing,
    flags COLLISION_MULTIPLE_IDENTITIES, and blocks automatic merging.
    """
    req = build_pvre_request(
        player_id=None,
        canonical_name="Amit Sharma",
        identity_status="PROVISIONAL",
        rr_relationship_state="NO_VERIFIED_RR_RELATIONSHIP",
        rr_current_state="NOT_CURRENT",
    )

    context = {"candidate_count": 2}
    output = pvre_engine.execute_player_research(req, context=context)

    assert output.route_status == RouteStatus.ROUTED_SAFETY_REVIEW.value
    assert output.research_mode == ResearchMode.REVIEW_REQUIRED.value
    assert output.review_status == PVREReviewStatus.REVIEW_REQUIRED.value
    assert (
        SafetyReviewReasonCode.COLLISION_MULTIPLE_IDENTITIES.value
        in output.review_reason_codes
    )


# =============================================================================
# Scenario 7: Conflicting DOB Records (Passport vs BCCI -> REVIEW_REQUIRED)
# =============================================================================


def test_scenario_7_conflicting_dob_records(pvre_engine: PVREngine) -> None:
    """Scenario 7: Passport DOB 2004-05-10 vs BCCI registration DOB 2003-11-22.

    Provenance tracker detects conflict; flags CONFLICT; preserves both claims;
    routes immediately to REVIEW_REQUIRED. Zero silent overwriting or averaging.
    """
    req = build_pvre_request(
        player_id=uuid4(),
        canonical_name="Domestic Prospect DOB Conflict",
        player_capped_status=PlayerCappedStatus.UNCAPPED.value,
        ipl_uncapped_eligibility="VERIFIED_ELIGIBLE",
        rr_relationship_state="NO_VERIFIED_RR_RELATIONSHIP",
        rr_current_state="NOT_CURRENT",
    )

    context = {
        "in_database": True,
        "primary_dob": "2004-05-10",
        "conflicting_dob": "2003-11-22",
        "primary_dob_source": "S18A",
        "conflicting_dob_source": "S20A",
    }

    output = pvre_engine.execute_player_research(req, context=context)

    assert output.route_status == RouteStatus.ROUTED_SAFETY_REVIEW.value
    assert output.research_mode == ResearchMode.REVIEW_REQUIRED.value
    assert output.review_status == PVREReviewStatus.REVIEW_REQUIRED.value
    assert SafetyReviewReasonCode.CONFLICT_DOB_RECORD.value in output.review_reason_codes

    # Verify both conflicting sources were preserved in dossier
    dossier = pvre_engine.controller.last_dossier
    assert dossier is not None
    assert len(dossier.conflicting_source_ids) >= 2


# =============================================================================
# Scenario 8: Missing Domestic Datasets (Unindexed Season -> PARTIAL_COVERAGE)
# =============================================================================


def test_scenario_8_missing_domestic_datasets_partial_coverage(
    pvre_engine: PVREngine,
) -> None:
    """Scenario 8: Player participated in SMAT 2020 or Vinoo Mankad 2022 (unindexed).

    Domestic discovery detects unindexed seasons; flags career_coverage_state = 'PARTIAL_COVERAGE';
    lists missing competitions; evaluates metrics over available sample only.
    Negative proof: missing dataset is never inferred as non-participation.
    """
    req = build_pvre_request(
        canonical_name="Candidate With Missing Season Dataset",
        player_capped_status=PlayerCappedStatus.UNCAPPED.value,
        ipl_uncapped_eligibility="VERIFIED_ELIGIBLE",
        rr_relationship_state="NO_VERIFIED_RR_RELATIONSHIP",
        rr_current_state="NOT_CURRENT",
    )

    missing = ["Syed Mushtaq Ali Trophy 2020", "Vinoo Mankad Trophy 2022"]
    context = {
        "in_database": True,
        "policy_verified": True,
        "missing_competitions": missing,
        "career_coverage_state": CareerCoverageState.PARTIAL_COVERAGE.value,
    }

    output = pvre_engine.execute_player_research(req, context=context)

    assert output.route_status == RouteStatus.ROUTED_UNCAPPED_CANDIDATE.value
    assert output.career_coverage_state == CareerCoverageState.PARTIAL_COVERAGE.value

    # Missing competitions explicitly tracked in competition_coverage
    comp_cov = output.competition_coverage
    assert "Syed Mushtaq Ali Trophy 2020" in comp_cov
    assert comp_cov["Syed Mushtaq Ali Trophy 2020"] == "DATASET_UNAVAILABLE"


# =============================================================================
# Scenario 9: Conflicting External Sources (Discrepant Stats -> REVIEW_REQUIRED)
# =============================================================================


def test_scenario_9_conflicting_external_statistics(pvre_engine: PVREngine) -> None:
    """Scenario 9: ESPNcricinfo reports 35 matches, BCCI scorecards verify 32.

    Statistical discrepancy across providers; routes to REVIEW_REQUIRED;
    compiles review dossier with conflicting source IDs.
    """
    req = build_pvre_request(
        canonical_name="Candidate Discrepant Match Count",
        player_capped_status=PlayerCappedStatus.UNCAPPED.value,
        ipl_uncapped_eligibility="VERIFIED_ELIGIBLE",
        rr_relationship_state="NO_VERIFIED_RR_RELATIONSHIP",
        rr_current_state="NOT_CURRENT",
    )

    context = {
        "in_database": True,
        "stat_discrepancy_metric": "MATCHES",
        "stat_val_a": 35,
        "stat_val_b": 32,
        "stat_src_a": "S20A",
        "stat_src_b": "S18B",
    }

    output = pvre_engine.execute_player_research(req, context=context)

    assert output.route_status == RouteStatus.ROUTED_SAFETY_REVIEW.value
    assert output.review_status == PVREReviewStatus.REVIEW_REQUIRED.value
    assert (
        SafetyReviewReasonCode.CONFLICTING_CAREER_STATISTICS.value
        in output.review_reason_codes
    )


# =============================================================================
# Scenario 10: Incomplete Career Coverage (Truncated Career -> PARTIAL_COVERAGE)
# =============================================================================


def test_scenario_10_incomplete_career_coverage_truncated(
    pvre_engine: PVREngine,
) -> None:
    """Scenario 10: Player debuted in 2018, but verified scorecards available only from 2022.

    System identifies truncated temporal coverage; sets career_coverage_state = 'PARTIAL_COVERAGE';
    computes sample indicators over available sample; zero statistical interpolation.
    """
    req = build_pvre_request(
        canonical_name="Truncated Career Batter",
        player_capped_status=PlayerCappedStatus.UNCAPPED.value,
        ipl_uncapped_eligibility="VERIFIED_ELIGIBLE",
        rr_relationship_state="NO_VERIFIED_RR_RELATIONSHIP",
        rr_current_state="NOT_CURRENT",
    )

    context = {
        "in_database": True,
        "policy_verified": True,
        "career_coverage_state": CareerCoverageState.PARTIAL_COVERAGE.value,
        "sample_indicators": {"matches": 18, "innings": 17, "balls_faced": 340, "wickets": 0},
    }

    output = pvre_engine.execute_player_research(req, context=context)

    assert output.route_status == RouteStatus.ROUTED_UNCAPPED_CANDIDATE.value
    assert output.career_coverage_state == CareerCoverageState.PARTIAL_COVERAGE.value

    # Verify complete career profile displays sample indicators without interpolation
    profile = output.complete_career_profile
    assert profile is not None
    assert "candidate_evidence" in profile
    cand_evidence = profile["candidate_evidence"]
    assert cand_evidence["sample_indicators"]["matches"] == 18
    assert cand_evidence["sample_indicators"]["balls_faced"] == 340


# =============================================================================
# 11. PVREngine ServiceBoundary & SICE 16-Dimension Matrix Integration
# =============================================================================


def test_pvre_engine_service_boundary_and_health_check(pvre_engine: PVREngine) -> None:
    """Verify PVREngine satisfies ServiceBoundary contracts and comprehensive health check."""
    assert pvre_engine.get_service_name() == "player_verification_research_engine"

    health = pvre_engine.health_check()
    assert health["status"] == "healthy"
    assert health["service"] == "player_verification_research_engine"
    assert health["controller"]["status"] == "ready"
    assert health["mode_a"]["status"] == "ready"
    assert health["mode_b"]["status"] == "ready"
    assert health["safety_review"]["status"] == "ready"
    assert health["source_registry"]["sources_registered"] >= 10
    assert health["repository"]["status"] == "ready"


def test_pvre_engine_execute_replacement_research_and_sice_matrix(
    pvre_engine: PVREngine,
) -> None:
    """Verify Mode B replacement research and SICE 16-dimension comparison matrix generation."""
    research_req = ReplacementResearchRequest(
        research_run_id=uuid4(),
        target_season_id=SYNTHETIC_TARGET_SEASON_ID,
        evaluation_date=date(2025, 3, 1),
        target_role="MIDDLE_ORDER_BATTER",
        secondary_role=None,
        batting_hand="RIGHT",
        bowling_style=None,
        max_age=25.0,
        min_domestic_matches=5,
        must_be_uncapped=True,
        candidate_pool_limit=10,
    )

    candidate_pool = [
        {
            "player_id": uuid4(),
            "canonical_name": "Qualified Middle Order Prospect",
            "primary_role": "MIDDLE_ORDER_BATTER",
            "batting_hand": "RIGHT",
            "age_at_evaluation": 22.5,
            "ipl_uncapped_eligibility": "VERIFIED_ELIGIBLE",
            "verified_policy_id": SYNTHETIC_POLICY_ID,
            "total_matches": 18,
            "domestic_t20_metrics": {
                "strike_rate": 146.5,
                "average": 36.2,
                "boundary_pct": 19.8,
                "dot_ball_pct": 35.1,
                "powerplay_strike_rate": 138.0,
                "middle_overs_strike_rate": 142.5,
                "death_overs_strike_rate": 172.0,
            },
        },
        {
            # Over-age candidate (should be filtered out)
            "player_id": uuid4(),
            "canonical_name": "Over-age Candidate",
            "primary_role": "MIDDLE_ORDER_BATTER",
            "batting_hand": "RIGHT",
            "age_at_evaluation": 29.0,
            "ipl_uncapped_eligibility": "VERIFIED_ELIGIBLE",
            "verified_policy_id": SYNTHETIC_POLICY_ID,
            "total_matches": 25,
        },
    ]

    candidates = pvre_engine.execute_replacement_research(
        research_req, candidate_pool=candidate_pool
    )

    # Exactly 1 candidate passes all filters (under 25, right-hand, middle-order)
    assert len(candidates) == 1
    cand = candidates[0]
    assert cand.canonical_name == "Qualified Middle Order Prospect"

    # Persisted in repository
    persisted = pvre_engine.repository.get_candidate_evidence(cand.candidate_player_id)
    assert persisted is not None

    # Test SICE 16-Dimension Comparison Matrix
    incumbent_metrics = {
        "strike_rate": 135.0,
        "average": 30.0,
        "boundary_pct": 16.5,
        "dot_ball_pct": 40.0,
        "powerplay_strike_rate": 130.0,
        "middle_overs_strike_rate": 132.0,
        "death_overs_strike_rate": 160.0,
        "age_at_evaluation": 31.0,
    }

    matrix = pvre_engine.mode_b_engine.compile_sice_comparison_matrix(
        candidate=cand,
        incumbent_metrics=incumbent_metrics,
    )

    # All 16 dimensions must be evaluated
    assert len(matrix) == 16
    for dim_id in SICE_DIMENSIONS_SPEC:
        assert dim_id in matrix
        dim_result = matrix[dim_id]
        assert "dimension_id" in dim_result
        assert "relative_delta" in dim_result

    # D01 Strike Rate Delta: candidate (146.5) - incumbent (135.0) = +11.5
    assert matrix["D01"]["relative_delta"] == 11.5
    # D02 Batting Average Delta: candidate (36.2) - incumbent (30.0) = +6.2
    assert matrix["D02"]["relative_delta"] == 6.2
    # D15 Age Delta: candidate (22.5) - incumbent (31.0) = -8.5
    assert matrix["D15"]["relative_delta"] == -8.5
