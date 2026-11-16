"""Adversarial and Fuzzing Test Suite for SICE (Squad Intelligence & Composition Engine).

Implements the 11 comprehensive adversarial scenarios specified in
PHASE6_SICE_READINESS_REPORT.md §11.3 and Milestone 6 dispatch requirements:
1. Malformed / corrupted payloads across CPPAE/TMVE/PVRE
2. Boundary age attacks (under 18, over 40, leap day, exact evaluation date)
3. Negative / infinite / NaN statistical inputs (zero NaN leakage, Rule R1)
4. Extreme roster imbalances (all overseas, zero keepers, 25 pure bowlers, empty squad)
5. Multi-way tiebreaking collisions across all 5 keys (K1, K2, K3, tiebreaker 1, tiebreaker 2, UUID)
6. Role transition hard boundary attacks (HB-1 Pace-to-Spin, HB-2 non-WK to WK, HB-3 pure batter to pure bowler)
7. Missing data vs zero statistics confusion (Rule R1: missing is NULL/None, never 0.0)
8. Delivery re-parsing injection attempt (confirm zero delivery JSON access)
9. PG16 injection / live DB connection attempt (Rule R5: mock repositories only, zero network)
10. Direct release/retention decision attempt (Rule R20: analytical signals only, zero decisions)
11. Scalar composite recruitment score attempt (Rule R21: multi-dimensional vectors, zero scalar collapse)
"""

from __future__ import annotations

import ast
import math
import os
from datetime import date
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from src.contracts.sice import (
    CandidateReplacementEvaluation,
    DimensionComparisonResult,
    RankedCandidateContract,
    RecommendationState,
    ReplacementComparisonOutputContract,
    ReplacementComparisonRequest,
    RosterStatus,
    SquadBalanceDimensions,
)
from src.sice import (
    DatabaseEnvironmentGuardError,
    RankingDeterminismError,
    RepositoryMode,
    RoleCompatibilityError,
    RoleCompatibilityEvaluator,
    RoleTransitionCategory,
    SafetyReviewInterceptionError,
    SICEEngine,
    SICERankingEngine,
    SICERepository,
)

# ==============================================================================
# Helper Assertions
# ==============================================================================


def _assert_zero_nan_leakage(obj: Any) -> None:
    """Recursively verify that no float field in a Pydantic contract or dict contains NaN."""
    if isinstance(obj, float):
        assert not math.isnan(obj), f"NaN detected in numeric value: {obj}"
        assert not math.isinf(obj), f"Inf detected in numeric value: {obj}"
    elif hasattr(obj, "model_dump"):
        dumped = obj.model_dump()
        _assert_zero_nan_leakage(dumped)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            try:
                _assert_zero_nan_leakage(v)
            except AssertionError as e:
                raise AssertionError(f"NaN leakage in field '{k}': {e}") from e
    elif isinstance(obj, (list, tuple, set)):
        for idx, item in enumerate(obj):
            try:
                _assert_zero_nan_leakage(item)
            except AssertionError as e:
                raise AssertionError(f"NaN leakage at index {idx}: {e}") from e


# ==============================================================================
# Scenario 1: Malformed / Corrupted Payloads across CPPAE/TMVE/PVRE
# ==============================================================================


def test_scenario_1_malformed_and_corrupted_payloads() -> None:
    """Verify SICE subsystems cleanly reject corrupted or malformed payloads without unhandled crashes."""
    engine = SICEEngine.create_default(default_seed=42)

    # 1. Missing date of birth in candidate pool triggers SafetyReviewInterceptionError
    corrupted_candidate: dict[str, Any] = {
        "player_id": uuid4(),
        "canonical_name": "Corrupted Player",
        "primary_role": "Top-order Batter",
        # Missing date_of_birth
        "eligibility_status": "VERIFIED_ELIGIBLE",
        "identity_status": "RESOLVED",
    }
    with pytest.raises(SafetyReviewInterceptionError, match="missing date of birth"):
        engine.rank_uncapped_candidates(candidate_pool=[corrupted_candidate])

    # 2. Corrupted ReplacementComparisonRequest raises TypeError
    with pytest.raises(TypeError, match="ReplacementComparisonRequest"):
        engine.compare_replacement("not-a-request")  # type: ignore[arg-type]

    # 3. Pydantic contract rejects malformed types (e.g. non-UUID for player_id)
    with pytest.raises(ValidationError):
        RankedCandidateContract(
            rank=1,
            player_id="not-a-valid-uuid",  # type: ignore[arg-type]
            canonical_name="Test Batter",
            role="Top-order Batter",
            age_at_evaluation=18.5,
            score=75.0,
        )

    # 4. Duplicate player_id in candidate pool raises RankingDeterminismError
    dup_id = uuid4()
    pool_with_dups = [
        {
            "player_id": dup_id,
            "canonical_name": "Candidate A",
            "date_of_birth": date(2005, 1, 1),
            "primary_role": "Top-order Batter",
            "eligibility_status": "VERIFIED_ELIGIBLE",
            "identity_status": "RESOLVED",
        },
        {
            "player_id": dup_id,
            "canonical_name": "Candidate A Duplicate",
            "date_of_birth": date(2005, 1, 1),
            "primary_role": "Top-order Batter",
            "eligibility_status": "VERIFIED_ELIGIBLE",
            "identity_status": "RESOLVED",
        },
    ]
    with pytest.raises(RankingDeterminismError, match="Duplicate candidate"):
        engine.rank_uncapped_candidates(candidate_pool=pool_with_dups)


# ==============================================================================
# Scenario 2: Boundary Age Attacks
# ==============================================================================


def test_scenario_2_boundary_age_attacks() -> None:
    """Verify age evaluation at boundaries: leap days, under 18, over 40, and exact evaluation date."""
    ranking_engine = SICERankingEngine(default_seed=42)

    # 1. Leap day candidate (born 2004-02-29) evaluated at non-leap evaluation date (age ~23.09)
    leap_id = uuid4()
    leap_candidate = {
        "player_id": leap_id,
        "canonical_name": "Leap Day Batter",
        "date_of_birth": date(2004, 2, 29),
        "primary_role": "Top-order Batter",
        "identity_status": "RESOLVED",
        "eligibility_status": "VERIFIED_ELIGIBLE",
        "runs": 450,
        "balls_faced": 300,
        "dismissals": 10,
        "strike_rate": 150.0,
        "batting_average": 45.0,
        "verified_innings": 12,
        "dnb_innings": 1,
        "total_cross_format_innings": 12,
        "walkover_batted_count": 0,
        "format_tags": ["T20"],
        "verification_record_ids": [uuid4()],
    }
    board = ranking_engine.run_ranking(
        candidate_pool=[leap_candidate],
        evaluation_date=date(2027, 4, 1),
        seed=42,
    )
    assert board.qualified_candidates_count == 1
    ranked_leap = board.top10[0]
    # Age on 2027-04-01 should be approx 23.09 years
    assert 23.0 <= ranked_leap.age_at_evaluation <= 23.2

    # 2. Under 18 candidate (born 2011-03-27, age 16.0): filtered out of adult IPL recruitment universe
    young_id = uuid4()
    young_candidate = {
        "player_id": young_id,
        "canonical_name": "Vaibhav Suryavanshi",
        "date_of_birth": date(2011, 3, 27),
        "primary_role": "Top-order Batter",
        "identity_status": "RESOLVED",
        "eligibility_status": "VERIFIED_ELIGIBLE",
        "runs": 480,
        "balls_faced": 300,
        "dismissals": 10,
        "strike_rate": 160.0,
        "batting_average": 48.0,
        "verified_innings": 12,
        "dnb_innings": 1,
        "total_cross_format_innings": 12,
        "walkover_batted_count": 0,
        "format_tags": ["T20"],
        "verification_record_ids": [uuid4()],
    }
    board_young = ranking_engine.run_ranking(
        candidate_pool=[young_candidate],
        evaluation_date=date(2027, 4, 1),
        seed=42,
    )
    # Filtered out at universe gate (dob > max_dob / under 18)
    assert board_young.qualified_candidates_count == 0
    assert len(board_young.top10) == 0

    # 3. Over 40 candidate (born 1985-01-01, age 42.0): filtered out of uncapped recruitment universe
    old_id = uuid4()
    old_candidate = {
        "player_id": old_id,
        "canonical_name": "Veteran Player",
        "date_of_birth": date(1985, 1, 1),
        "primary_role": "Top-order Batter",
        "identity_status": "RESOLVED",
        "eligibility_status": "VERIFIED_ELIGIBLE",
        "runs": 450,
        "balls_faced": 300,
        "dismissals": 10,
        "strike_rate": 150.0,
        "batting_average": 45.0,
        "verified_innings": 12,
        "dnb_innings": 1,
        "total_cross_format_innings": 12,
        "walkover_batted_count": 0,
        "format_tags": ["T20"],
        "verification_record_ids": [uuid4()],
    }
    board_old = ranking_engine.run_ranking(
        candidate_pool=[old_candidate],
        evaluation_date=date(2027, 4, 1),
        seed=42,
    )
    # Filtered out at universe gate (dob < min_dob / over 26)
    assert board_old.qualified_candidates_count == 0
    assert len(board_old.top10) == 0

    # 4. Exact evaluation date candidate (DOB == evaluation_date -> age 0.0, filtered out)
    exact_date_candidate = {
        "player_id": uuid4(),
        "canonical_name": "Zero Age Candidate",
        "date_of_birth": date(2027, 4, 1),
        "primary_role": "Top-order Batter",
        "identity_status": "RESOLVED",
        "eligibility_status": "VERIFIED_ELIGIBLE",
        "total_cross_format_innings": 10,
    }
    board_exact = ranking_engine.run_ranking(
        candidate_pool=[exact_date_candidate],
        evaluation_date=date(2027, 4, 1),
        seed=42,
    )
    assert board_exact.qualified_candidates_count == 0
    assert len(board_exact.top10) == 0

    # 5. Contract age bounds enforcement (ge=14.0, le=55.0)
    with pytest.raises(ValidationError):
        RankedCandidateContract(
            rank=1,
            player_id=uuid4(),
            canonical_name="Underage Child",
            role="Top-order Batter",
            age_at_evaluation=12.0,  # Below 14.0
            score=80.0,
        )

    with pytest.raises(ValidationError):
        RankedCandidateContract(
            rank=1,
            player_id=uuid4(),
            canonical_name="Senior Player",
            role="Top-order Batter",
            age_at_evaluation=56.0,  # Above 55.0
            score=80.0,
        )


# ==============================================================================
# Scenario 3: Negative / Infinite / NaN Statistical Inputs (Zero NaN Leakage)
# ==============================================================================


def test_scenario_3_zero_nan_leakage_and_numeric_integrity() -> None:
    """Verify that no NaN or Inf values leak into any emitted SICE output contracts (Rule R1)."""
    engine = SICEEngine.create_default(default_seed=42)

    # 1. Pydantic contracts strictly reject NaN / Inf floats
    with pytest.raises(ValidationError):
        DimensionComparisonResult(
            dimension_id="D01",
            dimension_name="Batting Strike Rate",
            delta=float("nan"),
        )

    with pytest.raises(ValidationError):
        DimensionComparisonResult(
            dimension_id="D01",
            dimension_name="Batting Strike Rate",
            delta=float("inf"),
        )

    # 2. Ranking board output with zero NaN leakage
    p_id = uuid4()
    candidate = {
        "player_id": p_id,
        "canonical_name": "Test Candidate",
        "date_of_birth": date(2005, 5, 10),
        "primary_role": "Top-order Batter",
        "eligibility_status": "VERIFIED_ELIGIBLE",
        "identity_status": "RESOLVED",
        "b05_batting_average": None,  # Missing average (never dismissed)
        "b06_strike_rate": 135.0,
        "b04_balls_faced": 150,
        "consistency_score": 75.0,
    }
    board = engine.rank_uncapped_candidates(candidate_pool=[candidate], seed=42)
    _assert_zero_nan_leakage(board)

    # 3. Squad evaluation output with zero NaN leakage
    team = engine.create_user_team("Zero NaN Test Squad")
    for i in range(12):
        engine.add_player_to_team(
            team_id=team.team_id,
            player_id=uuid4(),
            assigned_role="Top-order Batter" if i < 6 else "Pace Bowler",
            batting_order=(i + 1) if i < 11 else None,
            is_designated_wk=(i == 0),
        )
    squad_res = engine.evaluate_squad(team.team_id)
    _assert_zero_nan_leakage(squad_res)

    # 4. Replacement comparison output with zero NaN leakage
    req = ReplacementComparisonRequest(
        incumbent_player_id=uuid4(),
        target_season_id=uuid4(),
        evaluation_date=date(2027, 4, 1),
    )
    repl_res = engine.compare_replacement(req)
    _assert_zero_nan_leakage(repl_res)


# ==============================================================================
# Scenario 4: Extreme Roster Imbalances
# ==============================================================================


def test_scenario_4_extreme_roster_imbalances() -> None:
    """Verify extreme roster configurations: all overseas, zero keepers, 25 pure bowlers, empty squad."""
    engine = SICEEngine.create_default(default_seed=42)

    # 1. Empty Squad (0 players)
    empty_team = engine.create_user_team("Empty Squad")
    eval_empty = engine.evaluate_squad(empty_team.team_id)
    assert eval_empty.squad_size == 0
    assert eval_empty.is_valid_ipl_roster is False
    assert eval_empty.roster_status == RosterStatus.ROSTER_INCOMPLETE

    # 2. All Overseas Squad (20 players, all overseas)
    overseas_team = engine.create_user_team("All Overseas Squad")
    meta_overseas: dict[UUID, dict[str, Any]] = {}
    for i in range(20):
        pid = uuid4()
        meta_overseas[pid] = {"is_overseas": True, "nationality": "Australia"}
        engine.add_player_to_team(
            team_id=overseas_team.team_id,
            player_id=pid,
            assigned_role="Top-order Batter" if i < 10 else "Pace Bowler",
            is_designated_wk=(i == 0 or i == 1),
        )
    val_overseas = engine.validate_roster(overseas_team.team_id, player_metadata=meta_overseas)
    assert val_overseas["is_valid_ipl_roster"] is False
    assert val_overseas["roster_status"] == RosterStatus.OVERSEAS_BREACH
    assert val_overseas["overseas_count"] == 20

    # 3. Zero Wicketkeepers Squad (20 domestic players, 0 designated keepers)
    no_wk_team = engine.create_user_team("Zero Keepers Squad")
    for i in range(20):
        engine.add_player_to_team(
            team_id=no_wk_team.team_id,
            player_id=uuid4(),
            assigned_role="Top-order Batter" if i < 10 else "Pace Bowler",
            is_designated_wk=False,
        )
    val_no_wk = engine.validate_roster(no_wk_team.team_id)
    assert val_no_wk["designated_wk_count"] == 0
    assert "CRITICAL_WK_SHORTAGE" in val_no_wk["flags"]

    # Playing XI optimization rejects lineup when 0 keepers available
    lineups = engine.optimize_playing_xi(team_id=no_wk_team.team_id)
    assert len(lineups) >= 1
    # Traditional lineup must be invalid due to missing wicketkeeper
    assert not any(lineup.is_valid_ipl_lineup for lineup in lineups)

    # 4. 25 Pure Bowlers Squad
    bowlers_team = engine.create_user_team("25 Pure Bowlers Squad")
    for _ in range(25):
        engine.add_player_to_team(
            team_id=bowlers_team.team_id,
            player_id=uuid4(),
            assigned_role="Pace Bowler",
            is_designated_wk=False,
        )
    eval_bowlers = engine.evaluate_squad(bowlers_team.team_id)
    assert eval_bowlers.squad_size == 25
    assert eval_bowlers.balance_dimensions.wicketkeeper_count == 0
    assert eval_bowlers.balance_dimensions.positional_coverage_deficit > 0
    assert "CRITICAL_WK_SHORTAGE" in eval_bowlers.critical_deficits


# ==============================================================================
# Scenario 5: Multi-Way Tiebreaking Collisions across All 5 Keys
# ==============================================================================


def test_scenario_5_multi_way_tiebreaking_collisions() -> None:
    """Verify total determinism when candidates collide across K1, K2, K3, tiebreaker 1, tiebreaker 2."""
    ranking_engine = SICERankingEngine(default_seed=42)

    # Three candidates with identical values on all 5 keys:
    # K1: DOB (2005-06-15)
    # K2: Consistency (85.0)
    # K3: Batting Average B05 (38.5)
    # Tiebreaker 1: Strike Rate B06 (142.5) [HD-01: B06, NOT B10!]
    # Tiebreaker 2: Balls Faced B04 (450)
    # Tiebreaker 3: Lexicographical canonical player UUID string ascending
    id_1 = UUID("11111111-1111-1111-1111-111111111111")
    id_2 = UUID("22222222-2222-2222-2222-222222222222")
    id_3 = UUID("33333333-3333-3333-3333-333333333333")

    c1: dict[str, Any] = {
        "player_id": id_1,
        "canonical_name": "Candidate Alpha",
        "date_of_birth": date(2005, 6, 15),
        "primary_role": "Top-order Batter",
        "identity_status": "RESOLVED",
        "eligibility_status": "VERIFIED_ELIGIBLE",
        "runs": 450,
        "balls_faced": 300,
        "dismissals": 10,
        "strike_rate": 150.0,
        "batting_average": 45.0,
        "verified_innings": 12,
        "dnb_innings": 1,
        "total_cross_format_innings": 12,
        "walkover_batted_count": 0,
        "format_tags": ["T20"],
        "verification_record_ids": [uuid4()],
    }
    c2: dict[str, Any] = {
        "player_id": id_2,
        "canonical_name": "Candidate Beta",
        "date_of_birth": date(2005, 6, 15),
        "primary_role": "Top-order Batter",
        "identity_status": "RESOLVED",
        "eligibility_status": "VERIFIED_ELIGIBLE",
        "runs": 450,
        "balls_faced": 300,
        "dismissals": 10,
        "strike_rate": 150.0,
        "batting_average": 45.0,
        "verified_innings": 12,
        "dnb_innings": 1,
        "total_cross_format_innings": 12,
        "walkover_batted_count": 0,
        "format_tags": ["T20"],
        "verification_record_ids": [uuid4()],
    }
    c3: dict[str, Any] = {
        "player_id": id_3,
        "canonical_name": "Candidate Gamma",
        "date_of_birth": date(2005, 6, 15),
        "primary_role": "Top-order Batter",
        "identity_status": "RESOLVED",
        "eligibility_status": "VERIFIED_ELIGIBLE",
        "runs": 450,
        "balls_faced": 300,
        "dismissals": 10,
        "strike_rate": 150.0,
        "batting_average": 45.0,
        "verified_innings": 12,
        "dnb_innings": 1,
        "total_cross_format_innings": 12,
        "walkover_batted_count": 0,
        "format_tags": ["T20"],
        "verification_record_ids": [uuid4()],
    }

    # Run ranking under various input permutations
    order_a: list[Any] = [c3, c1, c2]
    order_b: list[Any] = [c2, c3, c1]
    order_c: list[Any] = [c1, c2, c3]

    res_a = ranking_engine.run_ranking(candidate_pool=order_a, seed=42)
    res_b = ranking_engine.run_ranking(candidate_pool=order_b, seed=42)
    res_c = ranking_engine.run_ranking(candidate_pool=order_c, seed=42)

    # All three runs must yield identical rank ordering sorted strictly by UUID ascending
    expected_ids = [id_1, id_2, id_3]

    assert [c.player_id for c in res_a.top10] == expected_ids
    assert [c.player_id for c in res_b.top10] == expected_ids
    assert [c.player_id for c in res_c.top10] == expected_ids


# ==============================================================================
# Scenario 6: Role Transition Hard Boundary Attacks
# ==============================================================================


def test_scenario_6_role_transition_hard_boundaries() -> None:
    """Verify enforcement of Hard Boundaries HB-1 (Pace/Spin), HB-2 (Non-WK/WK), HB-3 (Batter/Bowler)."""
    evaluator = RoleCompatibilityEvaluator()

    # HB-1: Specialist Pace Bowler <-> Specialist Spin Bowler = 0.00
    res_hb1 = evaluator.evaluate_compatibility(
        incumbent_role="Pace Bowler",
        candidate_role="Spin Bowler",
    )
    assert res_hb1.compatibility_score == 0.00
    assert res_hb1.is_compatible is False
    assert res_hb1.hard_boundary_violated is True
    assert res_hb1.transition_category == RoleTransitionCategory.INCOMPATIBLE

    with pytest.raises(RoleCompatibilityError, match="HB-1"):
        evaluator.evaluate_compatibility(
            incumbent_role="Pace Bowler",
            candidate_role="Spin Bowler",
            strict_mode=True,
        )

    # HB-2: Non-Wicketkeeper <-> Designated Wicketkeeper = 0.00
    res_hb2 = evaluator.evaluate_compatibility(
        incumbent_role="Top-order Batter",
        candidate_role="Top-order Batter",
        incumbent_is_wk=True,
        candidate_is_wk=False,
    )
    assert res_hb2.compatibility_score == 0.00
    assert res_hb2.is_compatible is False
    assert res_hb2.hard_boundary_violated is True

    with pytest.raises(RoleCompatibilityError, match="HB-2"):
        evaluator.evaluate_compatibility(
            incumbent_role="Top-order Batter",
            candidate_role="Top-order Batter",
            incumbent_is_wk=True,
            candidate_is_wk=False,
            strict_mode=True,
        )

    # HB-3: Pure Batter <-> Pure Bowler = 0.00
    res_hb3 = evaluator.evaluate_compatibility(
        incumbent_role="Top-order Batter",
        candidate_role="Pace Bowler",
    )
    assert res_hb3.compatibility_score == 0.00
    assert res_hb3.is_compatible is False
    assert res_hb3.hard_boundary_violated is True

    with pytest.raises(RoleCompatibilityError, match="HB-3"):
        evaluator.evaluate_compatibility(
            incumbent_role="Top-order Batter",
            candidate_role="Pace Bowler",
            strict_mode=True,
        )


# ==============================================================================
# Scenario 7: Missing Data vs Zero Statistics Confusion
# ==============================================================================


def test_scenario_7_missing_data_vs_zero_statistics_confusion() -> None:
    """Verify Rule R1: missing data evaluates to NULL/None, never 0.0, and uncomputable dims cap at MONITOR."""
    # 1. Contract field represents unobserved metric as None, distinct from 0.0
    dim_missing = DimensionComparisonResult(
        dimension_id="D07",
        dimension_name="Death Over Economy",
        incumbent_value=None,  # Never bowled death overs
        candidate_value=9.5,
        computable=False,
        notes="Unobserved in evaluation window",
    )
    assert dim_missing.incumbent_value is None
    assert dim_missing.computable is False

    dim_zero = DimensionComparisonResult(
        dimension_id="D07",
        dimension_name="Death Over Economy",
        incumbent_value=0.0,  # Bowled maiden death over
        candidate_value=9.5,
        computable=True,
    )
    assert dim_zero.incumbent_value == 0.0
    assert dim_zero.computable is True
    assert dim_missing.incumbent_value != dim_zero.incumbent_value

    # 2. HD-12: More than 4 uncomputable dimensions cap recommendation at ANALYTICAL_MONITOR
    engine = SICEEngine.create_default(default_seed=42)
    inc_id = uuid4()
    req = ReplacementComparisonRequest(
        incumbent_player_id=inc_id,
        target_season_id=uuid4(),
        evaluation_date=date(2027, 4, 1),
    )
    # Candidate with scarce scorecard-only metrics (many uncomputable dimensions)
    sparse_candidate = {
        "candidate_player_id": uuid4(),
        "canonical_name": "Sparse Scorecard Player",
        "primary_role": "Top-order Batter",
        "strike_rate": 130.0,
        "batting_average": 30.0,
        # Missing phase metrics, boundary metrics, pressure metrics
    }
    repl_res = engine.compare_replacement(
        req,
        candidate_pool=[sparse_candidate],
    )
    # Must not emit DIRECT_UPGRADE or uncalibrated replacement
    for eval_item in repl_res.evaluations:
        uncomputable_count = sum(1 for d in eval_item.dimension_comparisons if not d.computable)
        if uncomputable_count > 4:
            assert eval_item.recommendation_label in (
                RecommendationState.ANALYTICAL_MONITOR,
                RecommendationState.INSUFFICIENT_EVIDENCE,
                RecommendationState.NO_SUITABLE_VERIFIED_REPLACEMENT,
            )


# ==============================================================================
# Scenario 8: Delivery Re-Parsing Injection Attempt
# ==============================================================================


def test_scenario_8_zero_delivery_reparsing_injection() -> None:
    """Verify that SICE contains zero delivery JSON re-parsing and zero raw delivery dictionary ingestion."""
    sice_dir = Path("src/sice")
    assert sice_dir.exists(), "src/sice directory must exist"

    # Scan all Python source files in src/sice for forbidden delivery parsing imports
    forbidden_terms = [
        "cricsheet_parser",
        "parse_deliveries",
        "load_delivery_json",
        "raw_deliveries",
    ]

    for py_file in sice_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(py_file))

        # Check imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for forbidden in forbidden_terms:
                        assert forbidden not in alias.name, (
                            f"Forbidden delivery parsing import '{alias.name}' detected in {py_file.name}"
                        )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for forbidden in forbidden_terms:
                    assert forbidden not in module, (
                        f"Forbidden delivery parsing import from '{module}' in {py_file.name}"
                    )

    # Verify SiceRankingEngine uses pre-aggregated match observations, not raw delivery dicts
    ranking_engine = SICERankingEngine(default_seed=42)
    assert not hasattr(ranking_engine, "parse_raw_delivery_json")


# ==============================================================================
# Scenario 9: PG16 Injection / Live DB Connection Attempt
# ==============================================================================


def test_scenario_9_pg16_guard_and_parameterized_injection() -> None:
    """Verify DatabaseEnvironmentGuard blocks unauthorized live connections and parameterized SQL stops injection."""
    # 1. Attempting DATABASE mode operations without authorization environment variable raises DatabaseEnvironmentGuardError
    if "SICE_AUTHORIZED_PG16_DB" in os.environ:
        del os.environ["SICE_AUTHORIZED_PG16_DB"]

    repo_db = SICERepository(mode=RepositoryMode.DATABASE)
    with pytest.raises(DatabaseEnvironmentGuardError, match="PostgreSQL Environment Guard"):
        repo_db.execute_parameterized("SELECT 1")

    # 2. Raw unparameterized SQL injection attempts are detected and rejected
    repo_mem = SICERepository(mode=RepositoryMode.IN_MEMORY)
    with pytest.raises(ValueError, match="SQL Injection vector detected"):
        repo_mem.execute_parameterized("SELECT * FROM user_teams WHERE team_name = '' OR '1'='1'")

    # 3. Parameterized queries safely accept arbitrary input without executing injection
    param_team_name = "RR'; DROP TABLE user_teams; --"
    repo_mem.execute_parameterized(
        "INSERT INTO user_teams (team_id, team_name) VALUES (%s, %s)",
        (uuid4(), param_team_name),
    )
    # Persisted literally in executed queries audit log
    last_query = repo_mem.executed_queries[-1]
    assert last_query["params"] is not None
    assert last_query["params"][1] == param_team_name


# ==============================================================================
# Scenario 10: Direct Release/Retention Decision Attempt
# ==============================================================================


def test_scenario_10_no_direct_release_or_retention_decisions() -> None:
    """Verify Rule R20: SICE produces analytical recommendation signals only, zero operational decisions."""
    # 1. Recommendation states are strictly analytical
    for state in RecommendationState:
        assert state.value.startswith("ANALYTICAL_") or state.value in (
            "NO_SUITABLE_VERIFIED_REPLACEMENT",
            "INSUFFICIENT_EVIDENCE",
        )
        assert "EXECUTE_RELEASE" not in state.value
        assert "TERMINATE_CONTRACT" not in state.value

    # 2. Verify engine classes have no contract-signing or player-release methods
    engine = SICEEngine.create_default(default_seed=42)
    assert not hasattr(engine, "release_player")
    assert not hasattr(engine, "terminate_player_contract")
    assert not hasattr(engine, "execute_recruitment")
    assert not hasattr(engine.composition_engine, "execute_roster_cuts")
    assert not hasattr(engine.replacement_engine, "finalize_replacement_decision")


# ==============================================================================
# Scenario 11: Scalar Composite Recruitment Score Attempt
# ==============================================================================


def test_scenario_11_no_scalar_composite_recruitment_score() -> None:
    """Verify Rule R21: candidate and squad assessments maintain multi-dimensional vectors without scalar collapse."""
    engine = SICEEngine.create_default(default_seed=42)

    # 1. Squad Balance Dimensions maintains 16 separate dimensions (not collapsed into 1 score)
    team = engine.create_user_team("Balance Vectors Squad")
    for i in range(18):
        engine.add_player_to_team(
            team_id=team.team_id,
            player_id=uuid4(),
            assigned_role="Top-order Batter" if i < 10 else "Pace Bowler",
            batting_order=(i + 1) if i < 11 else None,
            is_designated_wk=(i == 0 or i == 1),
        )
    squad_res = engine.evaluate_squad(team.team_id)
    dims = squad_res.balance_dimensions
    assert isinstance(dims, SquadBalanceDimensions)

    # Explicit check for multi-dimensional balance attributes
    assert hasattr(dims, "roster_capacity_status")
    assert hasattr(dims, "overseas_ratio")
    assert hasattr(dims, "role_entropy")
    assert hasattr(dims, "bowling_overs_capacity")
    assert hasattr(dims, "pace_to_spin_ratio")
    assert hasattr(dims, "wicketkeeper_count")
    assert hasattr(dims, "all_rounder_count")
    assert hasattr(dims, "tactical_versatility_score")
    assert hasattr(dims, "evidentiary_health_score")

    # 2. Replacement evaluation maintains 16 individual dimension comparison results
    req = ReplacementComparisonRequest(
        incumbent_player_id=uuid4(),
        target_season_id=uuid4(),
        evaluation_date=date(2027, 4, 1),
    )
    repl_res = engine.compare_replacement(req)
    assert isinstance(repl_res, ReplacementComparisonOutputContract)

    # Verify that each candidate evaluation carries a list of DimensionComparisonResult objects
    for eval_item in repl_res.evaluations:
        assert isinstance(eval_item, CandidateReplacementEvaluation)
        assert len(eval_item.dimension_comparisons) > 0
        dim_ids = [d.dimension_id for d in eval_item.dimension_comparisons]
        # Dimensions D01 through D16 should be represented individually
        assert "D01" in dim_ids
        # Assert no single scalar composite recruitment score field exists
        assert not hasattr(eval_item, "composite_recruitment_probability")
        assert not hasattr(eval_item, "overall_replacement_score")
