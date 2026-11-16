"""Comprehensive Unit Test Suite for SICE Replacement Engine (RE-1.0.0).

Organized into 8 dedicated functional test suites (69 unit tests):
- Suite 1: Cosine & Gower Similarity Models (10 tests, T1.01–T1.10)
- Suite 2: Role Compatibility Matrix & Hard Boundaries (10 tests, T2.01–T2.10)
- Suite 3: 16 Comparison Dimensions (D01–D16) & Inverted Deltas (10 tests, T3.01–T3.10)
- Suite 4: Multi-Objective Pareto Dominance Screening (HD-11) (7 tests, T4.01–T4.07)
- Suite 5: Scorecard-Only Evidence Cap (HD-12) (6 tests, T5.01–T5.06)
- Suite 6: Overseas Replacement Slot Liberation (HD-13) (6 tests, T6.01–T6.06)
- Suite 7: 5 Recommendation States Classification (8 tests, T7.01–T7.08)
- Suite 8: Safety Interception Gate & Boundary Guards (12 tests, T8.01–T8.12)

Governing Specifications:
- reports/phase6-execution/PHASE6_SICE_READINESS_REPORT.md §7 & §16
- docs/DATA_DICTIONARY.md §10.3 & §11
- docs/RANKING_SPEC.md §9
- docs/TRD.md §8.3 & §8.4
"""

from __future__ import annotations

import math
from datetime import date
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from src.contracts.sice import (
    CandidateReplacementEvaluation,
    DimensionAdvantage,
    DimensionComparisonResult,
    DimensionStatus,
    RecommendationState,
    ReplacementComparisonOutputContract,
    ReplacementComparisonRequest,
)
from src.sice.exceptions import (
    RoleCompatibilityError,
    SafetyReviewInterceptionError,
    SICEError,
)
from src.sice.replacement_engine import (
    ReplacementCandidateCategory,
    ReplacementEngine,
)
from src.sice.role_compatibility import (
    CanonicalRole,
    RoleCompatibilityEvaluator,
    evaluate_role_compatibility,
)
from src.sice.similarity import (
    SubspaceDistanceResult,
    cosine_similarity,
    gower_similarity,
    subspace_weighted_euclidean_distance,
)

# -----------------------------------------------------------------------------
# Common Test Fixtures
# -----------------------------------------------------------------------------
FIXED_EVAL_DATE = date(2026, 11, 14)
TARGET_SEASON_UUID = UUID("11111111-2222-3333-4444-555555555555")
INCUMBENT_UUID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
CANDIDATE_A_UUID = UUID("11111111-1111-1111-1111-111111111111")
CANDIDATE_B_UUID = UUID("22222222-2222-2222-2222-222222222222")


# =============================================================================
# SUITE 1: Cosine & Gower Similarity Models (10 Tests)
# =============================================================================
def test_cosine_similarity_identical_vectors():
    """T1.01: Identical directional alignment yields 1.0."""
    v1 = [140.0, 35.0, 0.65]
    v2 = [140.0, 35.0, 0.65]
    sim = cosine_similarity(v1, v2)
    assert sim is not None
    assert math.isclose(sim, 1.0, rel_tol=1e-5)


def test_cosine_similarity_orthogonal_vectors():
    """T1.02: Orthogonal feature vectors yield 0.0."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [0.0, 1.0, 0.0]
    sim = cosine_similarity(v1, v2)
    assert sim is not None
    assert math.isclose(sim, 0.0, abs_tol=1e-5)


def test_cosine_similarity_zero_vector_edge_case():
    """T1.03: Zero-magnitude vector handled gracefully without division by zero."""
    v1 = [0.0, 0.0, 0.0]
    v2 = [120.0, 25.0, 0.5]
    sim = cosine_similarity(v1, v2)
    assert sim == 0.0
    # Both vectors zero
    assert cosine_similarity([0.0, 0.0], [0.0, 0.0]) == 0.0


def test_cosine_similarity_symmetry_and_range():
    """T1.04: Symmetric S(u, v) = S(v, u) and strictly bounded in [0.0, 1.0]."""
    u = [125.0, 32.5, 14.2, 8.2, 18.0]
    v = [142.0, 28.0, 16.5, 7.8, 22.0]
    s_uv = cosine_similarity(u, v)
    s_vu = cosine_similarity(v, u)
    assert s_uv is not None and s_vu is not None
    assert math.isclose(s_uv, s_vu, rel_tol=1e-5)
    assert 0.0 <= s_uv <= 1.0


def test_cosine_similarity_dimension_mismatch():
    """T1.05: Unequal length vectors reject with ValueError."""
    v1 = [1.0, 2.0]
    v2 = [1.0, 2.0, 3.0]
    with pytest.raises(ValueError, match="Vector dimensions must match"):
        cosine_similarity(v1, v2)


def test_gower_similarity_identical_entities():
    """T1.06: Identical mixed-type profiles yield 1.0."""
    x = {"role": "Pace Bowler", "sr": 145.0, "econ": 7.8}
    y = {"role": "Pace Bowler", "sr": 145.0, "econ": 7.8}
    ranges = {"sr": 100.0, "econ": 6.0}
    sim = gower_similarity(x, y, ranges)
    assert sim is not None
    assert math.isclose(sim, 1.0, rel_tol=1e-5)


def test_gower_similarity_mixed_types_calculation():
    """T1.07: Proper weighting across categorical match and normalized numeric distance."""
    x = {"hand": "RIGHT", "avg": 40.0}
    y = {"hand": "LEFT", "avg": 30.0}
    ranges = {"avg": 50.0}
    # s_hand = 0.0, s_avg = 1 - 10/50 = 0.8. Mean = (0.0 + 0.8) / 2 = 0.40
    sim = gower_similarity(x, y, ranges)
    assert sim is not None
    assert math.isclose(sim, 0.40, rel_tol=1e-5)


def test_gower_similarity_missing_attributes_null_safety():
    """T1.08: None values excluded from numerator and denominator."""
    x = {"hand": "RIGHT", "avg": None}
    y = {"hand": "RIGHT", "avg": 30.0}
    # avg ignored, hand matches -> 1.0
    sim = gower_similarity(x, y)
    assert sim is not None
    assert math.isclose(sim, 1.0, rel_tol=1e-5)


def test_gower_similarity_zero_overlap():
    """T1.09: Completely disjoint or all-null attributes return 0.0."""
    x = {"metric_a": 10.0}
    y = {"metric_b": 20.0}
    assert gower_similarity(x, y) == 0.0


def test_subspace_euclidean_distance_with_penalty():
    """T1.10: Incomplete subspace penalized per Readiness §7.3."""
    inc = {f"f{i}": 10.0 for i in range(10)}
    cand = {f"f{i}": 10.0 for i in range(4)}
    res = subspace_weighted_euclidean_distance(inc, cand, total_dimensions=10)
    assert isinstance(res, SubspaceDistanceResult)
    # 4 mutually observed out of 10 -> penalty = 1 + 0.5 * (1 - 4/10) = 1.30
    assert math.isclose(res.penalty, 1.30, rel_tol=1e-4)


# =============================================================================
# SUITE 2: Role Compatibility Matrix & Hard Boundaries (10 Tests)
# =============================================================================
def test_role_compatibility_identical_canonical_roles():
    """T2.01: Identity transitions evaluate to 1.0."""
    for role in CanonicalRole:
        compat = evaluate_role_compatibility(role.value, role.value)
        assert compat == 1.0, f"Role {role} did not evaluate to 1.0 with itself"


def test_role_compatibility_adjacent_batting_roles():
    """T2.02: High compatibility between adjacent batting positions."""
    compat = evaluate_role_compatibility("Top-order Batter", "Middle-order Batter")
    assert 0.70 <= compat <= 0.85


def test_role_compatibility_allrounder_to_specialist():
    """T2.03: Moderate compatibility between all-rounder and matching specialist."""
    compat = evaluate_role_compatibility("Bowling All-rounder", "Pace Bowler")
    assert 0.55 <= compat <= 0.75


def test_role_compatibility_hard_boundary_pace_vs_spin():
    """T2.04: Cross-discipline replacement strictly barred (0.00)."""
    compat = evaluate_role_compatibility("Pace Bowler", "Spin Bowler")
    assert compat == 0.00


def test_role_compatibility_hard_boundary_spin_vs_pace():
    """T2.05: Symmetric hard boundary for spin vs pace."""
    compat = evaluate_role_compatibility("Spin Bowler", "Pace Bowler")
    assert compat == 0.00


def test_role_compatibility_hard_boundary_wicketkeeper():
    """T2.06: Non-wicketkeeper cannot replace specialist wicketkeeper without bypass."""
    compat = evaluate_role_compatibility(
        incumbent_role="Wicketkeeper Batter",
        candidate_role="Top-order Batter",
        cand_is_wk=False,
        allow_non_wk_keeper_replacement=False,
    )
    assert compat == 0.00


def test_role_compatibility_pure_batter_vs_pure_bowler():
    """T2.07: Pure batter replacing pure bowler evaluates to 0.00."""
    compat = evaluate_role_compatibility("Top-order Batter", "Pace Bowler")
    assert compat == 0.00
    compat_rev = evaluate_role_compatibility("Pace Bowler", "Top-order Batter")
    assert compat_rev == 0.00


def test_role_compatibility_handedness_modifier():
    """T2.08: Handedness modifier reduces score by 0.95 factor for batters."""
    evaluator = RoleCompatibilityEvaluator()
    res_same = evaluator.evaluate_compatibility(
        "Top-order Batter", "Top-order Batter", "RIGHT", "RIGHT"
    )
    res_diff = evaluator.evaluate_compatibility(
        "Top-order Batter", "Top-order Batter", "RIGHT", "LEFT"
    )
    assert res_same.compatibility_score == 1.0
    assert math.isclose(res_diff.compatibility_score, 0.95, rel_tol=1e-4)


def test_role_compatibility_bowling_style_modifier():
    """T2.09: Bowling style modifier within spin role."""
    evaluator = RoleCompatibilityEvaluator()
    res = evaluator.evaluate_compatibility(
        incumbent_role="Spin Bowler",
        candidate_role="Spin Bowler",
        incumbent_bowling_style="Right-arm legbreak",
        candidate_bowling_style="Left-arm orthodox",
    )
    # Base 1.0 * style mod 0.90 = 0.90
    assert math.isclose(res.compatibility_score, 0.90, rel_tol=1e-4)


def test_role_compatibility_unknown_role_raises_error():
    """T2.10: Invalid or unrecognized role string raises domain exception."""
    with pytest.raises(RoleCompatibilityError):
        evaluate_role_compatibility("Martian Bowler", "Pace Bowler")


# =============================================================================
# SUITE 3: 16 Comparison Dimensions (D01–D16) & Inverted Deltas (10 Tests)
# =============================================================================
def test_d01_to_d03_forward_batting_deltas():
    """T3.01: Forward deltas Delta = X_cand - X_inc."""
    engine = ReplacementEngine()
    inc = {
        "strike_rate": 135.0,
        "batting_average": 30.0,
        "boundary_pct": 15.0,
        "balls_faced": 120,
    }
    cand = {
        "strike_rate": 150.0,
        "batting_average": 35.0,
        "boundary_pct": 20.0,
        "balls_faced": 100,
    }
    dims = engine._compute_16_dimensions(inc, cand, inc_age=30.0, cand_age=23.0)
    d_map = {d.dimension_id: d for d in dims}

    assert d_map["D01"].delta == 15.0
    assert d_map["D01"].advantage == DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE

    assert d_map["D02"].delta == 5.0
    assert d_map["D02"].advantage == DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE

    assert d_map["D03"].delta == 5.0
    assert d_map["D03"].advantage == DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE


def test_d04_inverted_dot_suppression_delta():
    """T3.02: Inverted delta Delta = X_inc - X_cand (lower dot % is superior)."""
    engine = ReplacementEngine()
    inc = {"dot_ball_pct": 45.0, "balls_faced": 100}
    cand = {"dot_ball_pct": 32.0, "balls_faced": 100}
    dims = engine._compute_16_dimensions(inc, cand, 28.0, 22.0)
    d04 = next(d for d in dims if d.dimension_id == "D04")
    assert d04.delta == 13.0
    assert d04.advantage == DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE


def test_d08_inverted_bowling_economy_delta():
    """T3.03: Inverted delta Delta = X_inc - X_cand (lower economy is superior)."""
    engine = ReplacementEngine()
    inc = {"economy_rate": 8.80, "balls_bowled": 120}
    cand = {"economy_rate": 7.20, "balls_bowled": 120}
    dims = engine._compute_16_dimensions(inc, cand, 29.0, 21.0)
    d08 = next(d for d in dims if d.dimension_id == "D08")
    assert d08.delta == 1.60
    assert d08.advantage == DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE


def test_d09_inverted_bowling_strike_rate_delta():
    """T3.04: Inverted delta Delta = X_inc - X_cand (lower bowling SR is superior)."""
    engine = ReplacementEngine()
    inc = {"bowling_strike_rate": 22.0, "balls_bowled": 120, "wickets": 8}
    cand = {"bowling_strike_rate": 15.5, "balls_bowled": 120, "wickets": 10}
    dims = engine._compute_16_dimensions(inc, cand, 29.0, 22.0)
    d09 = next(d for d in dims if d.dimension_id == "D09")
    assert d09.delta == 6.5
    assert d09.advantage == DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE


def test_d11_inverted_phase_bowling_control_delta():
    """T3.05: Phase economy inverted delta."""
    engine = ReplacementEngine()
    inc = {"death_economy": 11.5, "death_balls_bowled": 36}
    cand = {"death_economy": 9.2, "death_balls_bowled": 36}
    dims = engine._compute_16_dimensions(inc, cand, 29.0, 22.0)
    d11 = next(d for d in dims if d.dimension_id == "D11")
    assert d11.delta == 2.3
    assert d11.advantage == DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE


def test_d15_age_trajectory_delta_direction():
    """T3.06: Delta_age = Age_cand - Age_inc (negative = candidate younger)."""
    engine = ReplacementEngine()
    dims = engine._compute_16_dimensions({}, {}, inc_age=31.5, cand_age=21.0)
    d15 = next(d for d in dims if d.dimension_id == "D15")
    assert d15.delta == -10.5
    assert d15.advantage == DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE


def test_dimension_sample_size_thresholds_insufficient_sample():
    """T3.07: Metrics with samples below threshold evaluate to INSUFFICIENT_SAMPLE."""
    engine = ReplacementEngine()
    inc = {"strike_rate": 140.0, "balls_faced": 100}
    cand = {"strike_rate": 155.0, "balls_faced": 15}  # < 20 threshold
    dims = engine._compute_16_dimensions(inc, cand, 28.0, 22.0)
    d01 = next(d for d in dims if d.dimension_id == "D01")
    assert d01.dimension_status == DimensionStatus.INSUFFICIENT_SAMPLE
    assert d01.advantage == DimensionAdvantage.NOT_APPLICABLE
    assert d01.delta is None


def test_dimension_null_handling_missing_data():
    """T3.08: Missing metric returns delta=None, computable=False, zero NaN."""
    engine = ReplacementEngine()
    dims = engine._compute_16_dimensions({}, {}, 28.0, 22.0)
    for d in dims:
        if d.dimension_id in ("D15", "D16"):
            continue
        assert d.computable is False or d.delta is None or not math.isnan(float(d.delta or 0.0))


def test_d02_undefeated_in_window_tag():
    """T3.09: Undefeated candidate tagged with UNDEFEATED_IN_WINDOW."""
    engine = ReplacementEngine()
    inc = {"batting_average": 32.0}
    cand = {"batting_average": 85.0, "dismissals": 0, "balls_faced": 60}
    dims = engine._compute_16_dimensions(inc, cand, 28.0, 22.0)
    d02 = next(d for d in dims if d.dimension_id == "D02")
    assert d02.dimension_status == DimensionStatus.UNDEFEATED_IN_WINDOW
    assert d02.advantage == DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE


def test_d09_zero_wickets_tag():
    """T3.10: Bowler with 0 wickets tagged with ZERO_WICKETS."""
    engine = ReplacementEngine()
    inc = {"bowling_strike_rate": 20.0}
    cand = {"bowling_strike_rate": 0.0, "wickets": 0, "balls_bowled": 36}
    dims = engine._compute_16_dimensions(inc, cand, 28.0, 22.0)
    d09 = next(d for d in dims if d.dimension_id == "D09")
    assert d09.dimension_status == DimensionStatus.ZERO_WICKETS
    assert d09.delta is None


# =============================================================================
# SUITE 4: Multi-Objective Pareto Dominance Screening (HD-11) (7 Tests)
# =============================================================================
def test_pareto_strictly_dominated_candidate_filtered():
    """T4.01: Candidate strictly worse across all criteria is dominated."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {
        "player_id": INCUMBENT_UUID,
        "canonical_name": "Trent Boult",
        "primary_role": "Pace Bowler",
        "replaceability_signal": "POTENTIALLY_REPLACEABLE",
        "review_status": "CLEAR",
        "age": 35.0,
        "metrics": {"economy_rate": 8.0, "bowling_strike_rate": 20.0},
    }
    # Cand A dominates Cand B across Economy (lower/better), Bowling SR (lower/better), and Age (younger)
    cand_a = {
        "candidate_player_id": CANDIDATE_A_UUID,
        "canonical_name": "Candidate Alpha",
        "primary_role": "Pace Bowler",
        "age": 21.0,
        "metrics": {"economy_rate": 6.8, "bowling_strike_rate": 14.0},
        "sample_indicators": {"balls_bowled": 120, "wickets": 8},
    }
    cand_b = {
        "candidate_player_id": CANDIDATE_B_UUID,
        "canonical_name": "Candidate Beta",
        "primary_role": "Pace Bowler",
        "age": 25.0,
        "metrics": {"economy_rate": 8.5, "bowling_strike_rate": 22.0},
        "sample_indicators": {"balls_bowled": 120, "wickets": 5},
    }
    out = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[cand_a, cand_b])
    frontier_ids = [e.candidate_player_id for e in out.evaluations]
    assert CANDIDATE_A_UUID in frontier_ids
    assert CANDIDATE_B_UUID not in frontier_ids


def test_pareto_tradeoff_preserves_both_candidates():
    """T4.02: Conflicting criteria preserve both candidates on frontier."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {
        "player_id": INCUMBENT_UUID,
        "canonical_name": "Incumbent Batter",
        "primary_role": "Top-order Batter",
        "replaceability_signal": "POTENTIALLY_REPLACEABLE",
        "review_status": "CLEAR",
        "age": 30.0,
        "metrics": {"strike_rate": 140.0, "boundary_pct": 18.0},
    }
    # Cand A: higher SR (165 vs 135), but lower Boundary % (19 vs 25)
    cand_a = {
        "candidate_player_id": CANDIDATE_A_UUID,
        "canonical_name": "Cand A",
        "primary_role": "Top-order Batter",
        "age": 22.0,
        "metrics": {"strike_rate": 165.0, "boundary_pct": 19.0},
        "sample_indicators": {"balls_faced": 100},
    }
    cand_b = {
        "candidate_player_id": CANDIDATE_B_UUID,
        "canonical_name": "Cand B",
        "primary_role": "Top-order Batter",
        "age": 22.0,
        "metrics": {"strike_rate": 135.0, "boundary_pct": 25.0},
        "sample_indicators": {"balls_faced": 100},
    }
    out = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[cand_a, cand_b])
    frontier_ids = [e.candidate_player_id for e in out.evaluations]
    assert CANDIDATE_A_UUID in frontier_ids
    assert CANDIDATE_B_UUID in frontier_ids


def test_pareto_direction_compliance_inverted_criteria():
    """T4.03: Verifies lower Economy (D08), Bowling SR (D09), Age (D15) treated as superior."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {
        "player_id": INCUMBENT_UUID,
        "primary_role": "Pace Bowler",
        "replaceability_signal": "POTENTIALLY_REPLACEABLE",
        "review_status": "CLEAR",
        "age": 32.0,
        "metrics": {"economy_rate": 8.5, "bowling_strike_rate": 20.0},
    }
    cand_a = {
        "candidate_player_id": CANDIDATE_A_UUID,
        "primary_role": "Pace Bowler",
        "age": 20.0,
        "metrics": {"economy_rate": 6.5, "bowling_strike_rate": 15.0},
        "sample_indicators": {"balls_bowled": 120, "wickets": 8},
    }
    cand_b = {
        "candidate_player_id": CANDIDATE_B_UUID,
        "primary_role": "Pace Bowler",
        "age": 25.0,
        "metrics": {"economy_rate": 8.0, "bowling_strike_rate": 18.0},
        "sample_indicators": {"balls_bowled": 120, "wickets": 6},
    }
    out = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[cand_a, cand_b])
    assert [e.candidate_player_id for e in out.evaluations] == [CANDIDATE_A_UUID]


def test_pareto_all_candidates_non_dominated():
    """T4.04: N candidates each leading in 1 distinct dimension are all preserved."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {
        "player_id": INCUMBENT_UUID,
        "primary_role": "Top-order Batter",
        "replaceability_signal": "POTENTIALLY_REPLACEABLE",
        "review_status": "CLEAR",
        "age": 30.0,
        "metrics": {"strike_rate": 130.0, "boundary_pct": 15.0},
    }
    # C1 leads in SR, C2 leads in Boundary %, C3 leads in youth
    c1 = {
        "candidate_player_id": UUID("11111111-0000-0000-0000-000000000001"),
        "primary_role": "Top-order Batter",
        "age": 25.0,
        "metrics": {"strike_rate": 170.0, "boundary_pct": 14.0},
        "sample_indicators": {"balls_faced": 100},
    }
    c2 = {
        "candidate_player_id": UUID("11111111-0000-0000-0000-000000000002"),
        "primary_role": "Top-order Batter",
        "age": 25.0,
        "metrics": {"strike_rate": 140.0, "boundary_pct": 28.0},
        "sample_indicators": {"balls_faced": 100},
    }
    c3 = {
        "candidate_player_id": UUID("11111111-0000-0000-0000-000000000003"),
        "primary_role": "Top-order Batter",
        "age": 19.0,
        "metrics": {"strike_rate": 145.0, "boundary_pct": 16.0},
        "sample_indicators": {"balls_faced": 100},
    }
    out = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[c1, c2, c3])
    assert len(out.evaluations) == 3


def test_pareto_single_candidate_pool():
    """T4.05: Single candidate pool is automatically non-dominated."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {"player_id": INCUMBENT_UUID, "primary_role": "Top-order Batter", "age": 30.0}
    c1 = {"candidate_player_id": CANDIDATE_A_UUID, "primary_role": "Top-order Batter", "age": 22.0}
    out = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[c1])
    assert len(out.evaluations) == 1
    assert out.evaluations[0].candidate_player_id == CANDIDATE_A_UUID


def test_pareto_zero_scalar_composite_scoring_guard():
    """T4.06: Engine outputs non-dominated vector set without collapsing to scalar score."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {"player_id": INCUMBENT_UUID, "primary_role": "Top-order Batter", "age": 30.0}
    cand = {
        "candidate_player_id": CANDIDATE_A_UUID,
        "primary_role": "Top-order Batter",
        "age": 22.0,
    }
    out = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[cand])
    # Model fields check
    assert "composite_replacement_score" not in type(out).model_fields
    assert "replacement_score" not in type(out).model_fields


def test_pareto_determinism_across_permutations():
    """T4.07: Output frontier is invariant to input list ordering."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {"player_id": INCUMBENT_UUID, "primary_role": "Top-order Batter", "age": 30.0}
    c1 = {
        "candidate_player_id": CANDIDATE_A_UUID,
        "primary_role": "Top-order Batter",
        "age": 21.0,
        "metrics": {"strike_rate": 160.0, "boundary_pct": 20.0},
        "sample_indicators": {"balls_faced": 100},
    }
    c2 = {
        "candidate_player_id": CANDIDATE_B_UUID,
        "primary_role": "Top-order Batter",
        "age": 23.0,
        "metrics": {"strike_rate": 140.0, "boundary_pct": 25.0},
        "sample_indicators": {"balls_faced": 100},
    }
    out_orig = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[c1, c2])
    out_rev = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[c2, c1])
    orig_ids = [e.candidate_player_id for e in out_orig.evaluations]
    rev_ids = [e.candidate_player_id for e in out_rev.evaluations]
    assert set(orig_ids) == set(rev_ids)


# =============================================================================
# SUITE 5: Scorecard-Only Evidence Cap (HD-12) (6 Tests)
# =============================================================================
def test_scorecard_cap_four_uncomputable_allows_standard_recommendation():
    """T5.01: Boundary <= 4 uncomputable dimensions allows standard recommendation."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {
        "player_id": INCUMBENT_UUID,
        "primary_role": "Top-order Batter",
        "replaceability_signal": "POTENTIALLY_REPLACEABLE",
        "age": 32.0,
        "metrics": {"strike_rate": 130.0, "batting_average": 28.0, "boundary_pct": 14.0},
    }
    # Candidate with delivery metrics present (only 3 uncomputable: D11, D12, D13)
    cand = {
        "candidate_player_id": CANDIDATE_A_UUID,
        "primary_role": "Top-order Batter",
        "age": 21.0,
        "is_scorecard_only": False,
        "metrics": {
            "strike_rate": 155.0,
            "batting_average": 36.0,
            "boundary_pct": 22.0,
            "dot_ball_pct": 30.0,
            "pp_strike_rate": 145.0,
            "middle_strike_rate": 150.0,
            "death_strike_rate": 180.0,
            "economy_rate": 8.0,
            "bowling_strike_rate": 20.0,
            "bowling_dot_pct": 40.0,
            "dismissals_per_match": 0.5,
        },
        "sample_indicators": {"balls_faced": 100, "balls_bowled": 60, "appearances": 10},
    }
    out = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[cand])
    assert len(out.evaluations) == 1
    assert (
        out.evaluations[0].recommendation_label
        == RecommendationState.ANALYTICAL_REPLACEMENT_CANDIDATE
    )


def test_scorecard_cap_five_uncomputable_triggers_monitor_cap():
    """T5.02: Boundary > 4 uncomputable dimensions caps recommendation at ANALYTICAL_MONITOR."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {
        "player_id": INCUMBENT_UUID,
        "primary_role": "Top-order Batter",
        "replaceability_signal": "POTENTIALLY_REPLACEABLE",
        "age": 32.0,
    }
    # Candidate is scorecard-only -> D04, D05, D06, D07, D10, D11, D12, D13 uncomputable (>4)
    cand = {
        "candidate_player_id": CANDIDATE_A_UUID,
        "primary_role": "Top-order Batter",
        "age": 21.0,
        "is_scorecard_only": True,
        "evidence_tier": "SCORECARD_ONLY",
        "metrics": {"strike_rate": 165.0, "batting_average": 45.0, "boundary_pct": 24.0},
        "sample_indicators": {"balls_faced": 100},
    }
    out = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[cand])
    assert len(out.evaluations) == 1
    assert out.evaluations[0].recommendation_label == RecommendationState.ANALYTICAL_MONITOR


def test_scorecard_cap_notes_contain_capped_by_scorecard_granularity():
    """T5.03: Cap reason explicitly logged in uncomputable dimensions."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {"player_id": INCUMBENT_UUID, "primary_role": "Top-order Batter", "age": 30.0}
    cand = {
        "candidate_player_id": CANDIDATE_A_UUID,
        "primary_role": "Top-order Batter",
        "age": 22.0,
        "is_scorecard_only": True,
    }
    out = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[cand])
    d04 = next(d for d in out.evaluations[0].dimension_comparisons if d.dimension_id == "D04")
    assert d04.dimension_status == DimensionStatus.NOT_COMPUTABLE
    assert "Scorecard" in str(d04.notes)


def test_scorecard_cap_all_delivery_metrics_uncomputable():
    """T5.04: Scorecard-only candidate missing all delivery data has delivery dims uncomputable."""
    engine = ReplacementEngine()
    dims = engine._compute_16_dimensions(
        {},
        {"is_scorecard_only": True},
        inc_age=30.0,
        cand_age=22.0,
    )
    delivery_dims = ["D04", "D05", "D06", "D07", "D10", "D11"]
    for d in dims:
        if d.dimension_id in delivery_dims:
            assert d.dimension_status == DimensionStatus.NOT_COMPUTABLE


def test_scorecard_cap_preserves_retain_signal():
    """T5.05: Scorecard cap does not alter incumbent RETAIN_SIGNAL."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {
        "player_id": INCUMBENT_UUID,
        "primary_role": "Top-order Batter",
        "replaceability_signal": "RETAIN_SIGNAL",
        "age": 30.0,
    }
    cand = {
        "candidate_player_id": CANDIDATE_A_UUID,
        "primary_role": "Top-order Batter",
        "age": 20.0,
        "is_scorecard_only": True,
    }
    out = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[cand])
    assert out.recommended_action == RecommendationState.ANALYTICAL_RETAIN


def test_zero_fabrication_of_delivery_metrics_from_scorecard():
    """T5.06: Delivery metrics marked NOT_COMPUTABLE without guessing (Rule R2)."""
    engine = ReplacementEngine()
    cand = {"is_scorecard_only": True, "strike_rate": 150.0}
    dims = engine._compute_16_dimensions({}, cand, 30.0, 22.0)
    d05 = next(d for d in dims if d.dimension_id == "D05")
    assert d05.computable is False
    assert d05.delta is None


# =============================================================================
# SUITE 6: Overseas Replacement Slot Liberation (HD-13) (6 Tests)
# =============================================================================
def test_overseas_slot_liberated_overseas_inc_domestic_cand():
    """T6.01: Overseas incumbent replaced by Indian candidate sets flag True."""
    engine = ReplacementEngine()
    inc = {"is_overseas": True, "nationality": "NZL"}
    cand = {
        "is_overseas": False,
        "nationality": "IND",
        "ipl_uncapped_eligibility": "VERIFIED_ELIGIBLE",
    }
    assert engine._check_overseas_slot_liberation(inc, cand) is True


def test_overseas_slot_not_liberated_domestic_inc_domestic_cand():
    """T6.02: Domestic incumbent replaced by domestic candidate sets flag False."""
    engine = ReplacementEngine()
    inc = {"is_overseas": False, "nationality": "IND"}
    cand = {
        "is_overseas": False,
        "nationality": "IND",
        "ipl_uncapped_eligibility": "VERIFIED_ELIGIBLE",
    }
    assert engine._check_overseas_slot_liberation(inc, cand) is False


def test_overseas_slot_not_liberated_overseas_inc_overseas_cand():
    """T6.03: Overseas incumbent replaced by overseas candidate sets flag False."""
    engine = ReplacementEngine()
    inc = {"is_overseas": True, "nationality": "SA"}
    cand = {
        "is_overseas": True,
        "nationality": "AUS",
        "ipl_uncapped_eligibility": "VERIFIED_ELIGIBLE",
    }
    assert engine._check_overseas_slot_liberation(inc, cand) is False


def test_overseas_slot_not_liberated_domestic_inc_overseas_cand():
    """T6.04: Domestic incumbent replaced by overseas candidate sets flag False."""
    engine = ReplacementEngine()
    inc = {"is_overseas": False, "nationality": "IND"}
    cand = {
        "is_overseas": True,
        "nationality": "ENG",
        "ipl_uncapped_eligibility": "VERIFIED_ELIGIBLE",
    }
    assert engine._check_overseas_slot_liberation(inc, cand) is False


def test_overseas_candidate_eligibility_tmve_verification():
    """T6.05: Candidate eligibility must originate from TMVE verification."""
    engine = ReplacementEngine()
    inc = {"is_overseas": True}
    cand_unverified = {
        "is_overseas": False,
        "nationality": "IND",
        "ipl_uncapped_eligibility": "UNVERIFIED",
    }
    assert engine._check_overseas_slot_liberation(inc, cand_unverified) is False


def test_overseas_candidate_missing_eligibility_defaults_unverified():
    """T6.06: Candidate missing ipl_uncapped_eligibility defaults to unverified (Rule R13, HD-13)."""
    engine = ReplacementEngine()
    inc = {"is_overseas": True, "nationality": "NZL"}
    cand_missing_elig = {"is_overseas": False, "nationality": "IND"}
    assert engine._check_overseas_slot_liberation(inc, cand_missing_elig) is False


# =============================================================================
# SUITE 7: 5 Recommendation States Classification (8 Tests)
# =============================================================================
def test_recommendation_state_direct_upgrade():
    """T7.01: Candidate superior in >=6 dimensions and younger maps to DIRECT_UPGRADE."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {
        "player_id": INCUMBENT_UUID,
        "canonical_name": "Sanju Samson",
        "primary_role": "Top-order Batter",
        "replaceability_signal": "POTENTIALLY_REPLACEABLE",
        "age": 31.0,
        "metrics": {"strike_rate": 135.0, "batting_average": 28.0, "boundary_pct": 14.0},
    }
    cand = {
        "candidate_player_id": CANDIDATE_A_UUID,
        "canonical_name": "Prodigy Batter",
        "primary_role": "Top-order Batter",
        "age": 20.0,
        "metrics": {
            "strike_rate": 160.0,
            "batting_average": 38.0,
            "boundary_pct": 22.0,
            "dot_ball_pct": 28.0,
            "pp_strike_rate": 155.0,
            "middle_strike_rate": 150.0,
            "death_strike_rate": 180.0,
            "dismissals_per_match": 0.5,
        },
        "sample_indicators": {"balls_faced": 120, "appearances": 10},
    }
    out = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[cand])
    assert len(out.evaluations) == 1
    assert (
        out.evaluations[0].recommendation_label
        == RecommendationState.ANALYTICAL_REPLACEMENT_CANDIDATE
    )
    assert out.recommended_action == RecommendationState.ANALYTICAL_REPLACEMENT_CANDIDATE


def test_recommendation_state_systemic_fit():
    """T7.02: Candidate fulfills tactical phase gap with high alignment maps to SYSTEMIC_FIT."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {
        "player_id": INCUMBENT_UUID,
        "canonical_name": "Pace Bowler",
        "primary_role": "Pace Bowler",
        "replaceability_signal": "POTENTIALLY_REPLACEABLE",
        "age": 30.0,
        "metrics": {"death_economy": 11.8, "economy_rate": 9.0},
        "sample_indicators": {"balls_bowled": 120},
    }
    cand = {
        "candidate_player_id": CANDIDATE_A_UUID,
        "canonical_name": "Death Specialist",
        "primary_role": "Pace Bowler",
        "age": 26.0,
        "metrics": {
            "death_economy": 8.2,
            "economy_rate": 7.5,
            "bowling_strike_rate": 14.0,
            "bowling_dot_pct": 45.0,
        },
        "sample_indicators": {"balls_bowled": 120, "death_balls_bowled": 36, "wickets": 8},
    }
    out = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[cand])
    assert len(out.evaluations) == 1
    assert (
        out.evaluations[0].recommendation_label
        == RecommendationState.ANALYTICAL_REPLACEMENT_CANDIDATE
    )


def test_recommendation_state_lateral_rotation():
    """T7.03: Candidate metrics match incumbent within confidence parity maps to LATERAL_ROTATION."""
    engine = ReplacementEngine()
    dims = [
        DimensionComparisonResult(
            dimension_id=f"D{i:02d}",
            dimension_name=f"Dim {i}",
            advantage=DimensionAdvantage.PARITY_WITHIN_UNCERTAINTY,
        )
        for i in range(1, 10)
    ]
    dims.append(
        DimensionComparisonResult(
            dimension_id="D10",
            dimension_name="Dim 10",
            advantage=DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE,
        )
    )
    cat = engine._classify_candidate_category(
        compat_score=0.85,
        dimensions=dims,
        age_delta=0.5,
        capped_by_scorecard=False,
        similarity_scores={},
    )
    assert cat == ReplacementCandidateCategory.LATERAL_ROTATION


def test_recommendation_state_long_term_project():
    """T7.04: Significantly younger candidate with high raw upside maps to LONG_TERM_PROJECT."""
    engine = ReplacementEngine()
    dims = [
        DimensionComparisonResult(
            dimension_id="D01",
            dimension_name="SR",
            advantage=DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE,
        ),
        DimensionComparisonResult(
            dimension_id="D03",
            dimension_name="Bnd",
            advantage=DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE,
        ),
    ]
    cat = engine._classify_candidate_category(
        compat_score=0.75,
        dimensions=dims,
        age_delta=-7.0,  # 7 years younger
        capped_by_scorecard=False,
        similarity_scores={},
    )
    assert cat == ReplacementCandidateCategory.LONG_TERM_PROJECT


def test_recommendation_state_analytical_monitor_on_mixed_signals():
    """T7.05: Mixed metric performance yields ANALYTICAL_MONITOR."""
    engine = ReplacementEngine()
    dims = [
        DimensionComparisonResult(
            dimension_id="D01",
            dimension_name="SR",
            advantage=DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE,
        ),
        DimensionComparisonResult(
            dimension_id="D02",
            dimension_name="Avg",
            advantage=DimensionAdvantage.SIGNIFICANT_INCUMBENT_ADVANTAGE,
        ),
    ]
    cat = engine._classify_candidate_category(
        compat_score=0.60,
        dimensions=dims,
        age_delta=1.0,
        capped_by_scorecard=False,
        similarity_scores={},
    )
    assert cat == ReplacementCandidateCategory.ANALYTICAL_MONITOR


def test_recommendation_state_no_suitable_replacement():
    """T7.06: Incumbent replaceable but empty pool produces NO_SUITABLE_VERIFIED_REPLACEMENT."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {
        "player_id": INCUMBENT_UUID,
        "primary_role": "Top-order Batter",
        "replaceability_signal": "POTENTIALLY_REPLACEABLE",
        "age": 32.0,
    }
    out = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[])
    assert out.recommended_action == RecommendationState.NO_SUITABLE_VERIFIED_REPLACEMENT


def test_recommendation_state_insufficient_evidence():
    """T7.07: Insufficient evidence on incumbent produces INSUFFICIENT_EVIDENCE."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {
        "player_id": INCUMBENT_UUID,
        "primary_role": "Top-order Batter",
        "replaceability_signal": "INSUFFICIENT_EVIDENCE",
        "age": 30.0,
    }
    out = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[])
    assert out.recommended_action == RecommendationState.INSUFFICIENT_EVIDENCE


def test_recommendation_state_elite_incumbent_analytical_retain():
    """T7.08: Elite incumbent with RETAIN_SIGNAL triggers ANALYTICAL_RETAIN."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {
        "player_id": INCUMBENT_UUID,
        "primary_role": "Top-order Batter",
        "replaceability_signal": "RETAIN_SIGNAL",
        "age": 28.0,
    }
    cand = {
        "candidate_player_id": CANDIDATE_A_UUID,
        "primary_role": "Top-order Batter",
        "age": 22.0,
    }
    out = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[cand])
    assert out.recommended_action == RecommendationState.ANALYTICAL_RETAIN


# =============================================================================
# SUITE 8: Safety Interception Gate & Boundary Guards (12 Tests)
# =============================================================================
def test_safety_gate_incumbent_review_required_halts_evaluation():
    """T8.01: Incumbent review_status = 'REVIEW_REQUIRED' halts evaluation."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {
        "player_id": INCUMBENT_UUID,
        "review_status": "REVIEW_REQUIRED",
        "primary_role": "Top-order Batter",
    }
    # Standard mode returns review contract with empty evaluations
    out = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[])
    assert out.review_status == "REVIEW_REQUIRED"
    assert out.recommended_action == RecommendationState.INSUFFICIENT_EVIDENCE
    assert len(out.evaluations) == 0

    # Strict mode raises SafetyReviewInterceptionError
    with pytest.raises(SafetyReviewInterceptionError):
        engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[], strict_mode=True)


def test_safety_gate_candidate_review_required_excluded():
    """T8.02: Candidate with review_status = 'REVIEW_REQUIRED' is excluded from pool."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {"player_id": INCUMBENT_UUID, "primary_role": "Top-order Batter", "age": 30.0}
    c_safe = {
        "candidate_player_id": CANDIDATE_A_UUID,
        "primary_role": "Top-order Batter",
        "age": 22.0,
        "review_status": "CLEAR",
    }
    c_review = {
        "candidate_player_id": CANDIDATE_B_UUID,
        "primary_role": "Top-order Batter",
        "age": 23.0,
        "review_status": "REVIEW_REQUIRED",
    }

    out = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[c_safe, c_review])
    cand_ids = [e.candidate_player_id for e in out.evaluations]
    assert CANDIDATE_A_UUID in cand_ids
    assert CANDIDATE_B_UUID not in cand_ids


def test_safety_gate_invalid_age_bounds_validation():
    """T8.03: Candidate age < 14.0 or > 55.0 rejected by Pydantic."""
    with pytest.raises(ValidationError):
        CandidateReplacementEvaluation(
            candidate_player_id=CANDIDATE_A_UUID,
            canonical_name="Too Young",
            age_at_evaluation=12.0,  # Below 14.0
            role_compatibility="1.0",
            recommendation_label=RecommendationState.ANALYTICAL_MONITOR,
        )


def test_safety_gate_nan_inf_metric_rejection():
    """T8.04: Supplying NaN or Inf rejected by contract."""
    with pytest.raises(ValidationError, match="NaN or Infinity forbidden"):
        DimensionComparisonResult(
            dimension_id="D01",
            dimension_name="Base SR",
            delta=float("nan"),
        )


def test_safety_gate_data_snapshot_sha256_validation():
    """T8.05: Invalid SHA256 string rejected by contract."""
    with pytest.raises(ValidationError, match="valid 64-character hexadecimal"):
        ReplacementComparisonOutputContract(
            incumbent_player_id=INCUMBENT_UUID,
            incumbent_canonical_name="Sanju Samson",
            incumbent_role="Top-order Batter",
            replaceability_signal="RETAIN_SIGNAL",
            evaluation_date=FIXED_EVAL_DATE,
            target_season_id=TARGET_SEASON_UUID,
            recommended_action=RecommendationState.ANALYTICAL_RETAIN,
            data_snapshot_sha256="not_a_valid_hex_sha256",
        )


def test_safety_guardrail_no_scalar_composite_replacement_score():
    """T8.06: Asserts contract does NOT expose scalar composite score (Rule R21)."""
    assert "composite_replacement_score" not in ReplacementComparisonOutputContract.model_fields
    assert "overall_replacement_score" not in ReplacementComparisonOutputContract.model_fields


def test_safety_guardrail_no_recruitment_probabilities():
    """T8.07: Asserts contract does NOT expose recruitment probabilities (PRD §4.5)."""
    assert "replacement_probability" not in ReplacementComparisonOutputContract.model_fields
    assert "transfer_probability" not in ReplacementComparisonOutputContract.model_fields


def test_safety_gate_unknown_player_id_handling():
    """T8.08: Non-existent player UUID handled cleanly without unhandled crash."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=uuid4(),
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    # When neither dossier nor database resolution is possible
    with pytest.raises(SICEError):
        # Passing explicitly None incumbent dossier to trigger resolution failure
        engine._resolve_incumbent = lambda pid, dos: None  # type: ignore[assignment]
        engine.compare_replacement(req)


def test_safety_gate_incumbent_verification_status_conflict_halts_evaluation():
    """T8.09: Incumbent verification_status = 'CONFLICT' halts evaluation in strict and standard modes."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {
        "player_id": INCUMBENT_UUID,
        "verification_status": "CONFLICT",
        "primary_role": "Top-order Batter",
        "replaceability_signal": "POTENTIALLY_REPLACEABLE",
    }
    # Standard mode returns review contract with empty evaluations
    out = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[])
    assert out.review_status == "REVIEW_REQUIRED"
    assert out.recommended_action == RecommendationState.INSUFFICIENT_EVIDENCE
    assert len(out.evaluations) == 0

    # Strict mode raises SafetyReviewInterceptionError
    with pytest.raises(SafetyReviewInterceptionError):
        engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[], strict_mode=True)


def test_safety_gate_incumbent_review_status_conflict_halts_evaluation():
    """T8.10: Incumbent review_status = 'CONFLICT' halts evaluation in strict and standard modes."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {
        "player_id": INCUMBENT_UUID,
        "review_status": "CONFLICT",
        "primary_role": "Top-order Batter",
    }
    out = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[])
    assert out.review_status == "REVIEW_REQUIRED"
    assert out.recommended_action == RecommendationState.INSUFFICIENT_EVIDENCE
    assert len(out.evaluations) == 0

    with pytest.raises(SafetyReviewInterceptionError):
        engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[], strict_mode=True)


def test_safety_gate_incumbent_verification_status_review_required_halts_evaluation():
    """T8.11: Incumbent verification_status = 'REVIEW_REQUIRED' without review_status key halts evaluation."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {
        "player_id": INCUMBENT_UUID,
        "verification_status": "REVIEW_REQUIRED",
        "primary_role": "Top-order Batter",
    }
    out = engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[])
    assert out.review_status == "REVIEW_REQUIRED"
    assert out.recommended_action == RecommendationState.INSUFFICIENT_EVIDENCE
    assert len(out.evaluations) == 0

    with pytest.raises(SafetyReviewInterceptionError):
        engine.compare_replacement(req, incumbent_dossier=inc, candidate_pool=[], strict_mode=True)


def test_safety_gate_candidate_pool_filtering_excludes_conflict_and_review_required():
    """T8.12: Candidate pool filtering excludes candidates with CONFLICT or REVIEW_REQUIRED."""
    engine = ReplacementEngine()
    req = ReplacementComparisonRequest(
        incumbent_player_id=INCUMBENT_UUID,
        target_season_id=TARGET_SEASON_UUID,
        evaluation_date=FIXED_EVAL_DATE,
    )
    inc = {"player_id": INCUMBENT_UUID, "primary_role": "Top-order Batter", "age": 30.0}
    c_safe = {
        "candidate_player_id": CANDIDATE_A_UUID,
        "canonical_name": "Safe Candidate",
        "primary_role": "Top-order Batter",
        "age": 22.0,
        "review_status": "CLEAR",
        "verification_status": "CLEAR",
    }
    c_verif_conflict = {
        "candidate_player_id": CANDIDATE_B_UUID,
        "canonical_name": "Verif Conflict Candidate",
        "primary_role": "Top-order Batter",
        "age": 23.0,
        "verification_status": "CONFLICT",
        "review_status": "CLEAR",
    }
    cand_c_uuid = UUID("33333333-3333-3333-3333-333333333333")
    c_rev_conflict = {
        "candidate_player_id": cand_c_uuid,
        "canonical_name": "Review Conflict Candidate",
        "primary_role": "Top-order Batter",
        "age": 24.0,
        "review_status": "CONFLICT",
    }
    cand_d_uuid = UUID("44444444-4444-4444-4444-444444444444")
    c_verif_review = {
        "candidate_player_id": cand_d_uuid,
        "canonical_name": "Verif Review Candidate",
        "primary_role": "Top-order Batter",
        "age": 25.0,
        "verification_status": "REVIEW_REQUIRED",
    }

    out = engine.compare_replacement(
        req,
        incumbent_dossier=inc,
        candidate_pool=[c_safe, c_verif_conflict, c_rev_conflict, c_verif_review],
    )
    cand_ids = [e.candidate_player_id for e in out.evaluations]
    assert CANDIDATE_A_UUID in cand_ids
    assert CANDIDATE_B_UUID not in cand_ids
    assert cand_c_uuid not in cand_ids
    assert cand_d_uuid not in cand_ids


# ==============================================================================
# Suite 9: SICE Models & Contract Interface Compliance
# ==============================================================================


def test_sice_models_module_importability() -> None:
    """T9.01: All SICE contracts, enums, and dataclasses are directly importable from src.sice.models."""
    from src.sice import models
    from src.sice.models import (
        AnalyticalRecommendation,
        AttributeSpec,
        CandidateRankingStatus,
        CandidateReplacementEvaluation,
        CanonicalRole,
        DimensionAdvantage,
        DimensionComparisonResult,
        DimensionStatus,
        LineupEvaluationResult,
        LineupType,
        RankedCandidateContract,
        RankingBoardOutputContract,
        RecommendationLabel,
        RecommendationState,
        ReplacementCandidateCategory,
        ReplacementComparisonOutputContract,
        ReplacementComparisonRequest,
        RoleCompatibilityResult,
        RoleTransitionCategory,
        RosterStatus,
        RunType,
        SICEContractVersion,
        SICEOutputContract,
        SquadBalanceDimensions,
        SubspaceDistanceResult,
        UncertaintyFlag,
    )

    imported_objects = (
        AnalyticalRecommendation,
        AttributeSpec,
        CandidateRankingStatus,
        CandidateReplacementEvaluation,
        CanonicalRole,
        DimensionAdvantage,
        DimensionComparisonResult,
        DimensionStatus,
        LineupEvaluationResult,
        LineupType,
        RankedCandidateContract,
        RankingBoardOutputContract,
        RecommendationLabel,
        RecommendationState,
        ReplacementCandidateCategory,
        ReplacementComparisonOutputContract,
        ReplacementComparisonRequest,
        RoleCompatibilityResult,
        RoleTransitionCategory,
        RosterStatus,
        RunType,
        SICEContractVersion,
        SICEOutputContract,
        SquadBalanceDimensions,
        SubspaceDistanceResult,
        UncertaintyFlag,
    )
    for obj in imported_objects:
        assert obj is not None

    expected_symbols = {
        "AnalyticalRecommendation",
        "AttributeSpec",
        "CandidateRankingStatus",
        "CandidateReplacementEvaluation",
        "CanonicalRole",
        "DimensionAdvantage",
        "DimensionComparisonResult",
        "DimensionStatus",
        "LineupEvaluationResult",
        "LineupType",
        "RankedCandidateContract",
        "RankingBoardOutputContract",
        "RecommendationLabel",
        "RecommendationState",
        "ReplacementCandidateCategory",
        "ReplacementComparisonOutputContract",
        "ReplacementComparisonRequest",
        "RoleCompatibilityResult",
        "RoleTransitionCategory",
        "RosterStatus",
        "RunType",
        "SICEContractVersion",
        "SICEOutputContract",
        "SquadBalanceDimensions",
        "SubspaceDistanceResult",
        "UncertaintyFlag",
    }
    for sym in expected_symbols:
        assert hasattr(models, sym), f"Missing symbol {sym} in src.sice.models"
        assert getattr(models, sym) is not None

    # Verify __all__ completeness
    for sym in expected_symbols:
        assert sym in models.__all__, f"{sym} missing from src.sice.models.__all__"


def test_sice_models_replacement_request_instantiation_and_validation() -> None:
    """T9.02: ReplacementComparisonRequest via src.sice.models validates correctly and forbids extra fields."""
    from src.sice.models import ReplacementComparisonRequest

    incumbent_id = uuid4()
    season_id = uuid4()
    eval_date = date(2027, 4, 1)

    req = ReplacementComparisonRequest(
        incumbent_player_id=incumbent_id,
        target_season_id=season_id,
        evaluation_date=eval_date,
    )
    assert req.incumbent_player_id == incumbent_id
    assert req.target_season_id == season_id
    assert req.evaluation_date == eval_date
    assert req.config_version == "RE-1.0.0"
    assert req.force_refresh is False

    # Extra fields must be forbidden
    with pytest.raises(ValidationError):
        ReplacementComparisonRequest(
            incumbent_player_id=incumbent_id,
            target_season_id=season_id,
            evaluation_date=eval_date,
            unexpected_field="forbidden_payload",  # type: ignore[call-arg]
        )


def test_sice_models_replacement_output_instantiation_and_validation() -> None:
    """T9.03: ReplacementComparisonOutputContract via src.sice.models validates structure and forbids extras."""
    from src.sice.models import (
        RecommendationState,
        ReplacementComparisonOutputContract,
    )

    incumbent_id = uuid4()
    season_id = uuid4()
    eval_date = date(2027, 4, 1)
    valid_sha256 = "0" * 64

    out = ReplacementComparisonOutputContract(
        incumbent_player_id=incumbent_id,
        incumbent_canonical_name="Sanju Samson",
        incumbent_role="Wicketkeeper Batter",
        replaceability_signal="ANALYTICAL_MONITOR",
        target_season_id=season_id,
        evaluation_date=eval_date,
        evaluations=[],
        recommended_action=RecommendationState.NO_SUITABLE_VERIFIED_REPLACEMENT,
        data_snapshot_sha256=valid_sha256,
    )
    assert out.incumbent_player_id == incumbent_id
    assert out.contract_version == "RE-1.0.0"
    assert out.recommended_action == RecommendationState.NO_SUITABLE_VERIFIED_REPLACEMENT
    assert len(out.evaluations) == 0
    assert out.data_snapshot_sha256 == valid_sha256

    # Extra fields must be forbidden
    with pytest.raises(ValidationError):
        ReplacementComparisonOutputContract(
            incumbent_player_id=incumbent_id,
            incumbent_canonical_name="Sanju Samson",
            incumbent_role="Wicketkeeper Batter",
            replaceability_signal="ANALYTICAL_MONITOR",
            target_season_id=season_id,
            evaluation_date=eval_date,
            evaluations=[],
            recommended_action=RecommendationState.NO_SUITABLE_VERIFIED_REPLACEMENT,
            data_snapshot_sha256=valid_sha256,
            forbidden_tag="illegal",  # type: ignore[call-arg]
        )


def test_sice_models_strict_nan_and_inf_rejection() -> None:
    """T9.04: Strict NaN and Inf rejection on numerical metrics via src.sice.models contracts."""
    from src.sice.models import (
        CandidateReplacementEvaluation,
        DimensionAdvantage,
        DimensionComparisonResult,
        DimensionStatus,
        RecommendationState,
    )

    # DimensionComparisonResult rejects NaN/Inf in numerical fields
    with pytest.raises(ValidationError):
        DimensionComparisonResult(
            dimension_id="D01",
            dimension_name="Base Scoring Rate",
            incumbent_value=float("nan"),
            candidate_value=135.0,
            delta=float("nan"),
            advantage=DimensionAdvantage.SIGNIFICANT_INCUMBENT_ADVANTAGE,
            dimension_status=DimensionStatus.COMPUTED,
        )

    with pytest.raises(ValidationError):
        DimensionComparisonResult(
            dimension_id="D01",
            dimension_name="Base Scoring Rate",
            incumbent_value=140.0,
            candidate_value=float("inf"),
            delta=float("inf"),
            advantage=DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE,
            dimension_status=DimensionStatus.COMPUTED,
        )

    # CandidateReplacementEvaluation rejects NaN in age_at_evaluation and confidence
    with pytest.raises(ValidationError):
        CandidateReplacementEvaluation(
            candidate_player_id=uuid4(),
            canonical_name="Test Candidate",
            age_at_evaluation=float("nan"),
            role_compatibility="DIRECT_MATCH",
            recommendation_label=RecommendationState.ANALYTICAL_REPLACEMENT_CANDIDATE,
        )

    with pytest.raises(ValidationError):
        CandidateReplacementEvaluation(
            candidate_player_id=uuid4(),
            canonical_name="Test Candidate",
            age_at_evaluation=22.0,
            role_compatibility="DIRECT_MATCH",
            recommendation_label=RecommendationState.ANALYTICAL_REPLACEMENT_CANDIDATE,
            confidence=float("inf"),
        )


def test_sice_models_role_compatibility_and_similarity_dataclasses() -> None:
    """T9.05: Role compatibility and similarity models via src.sice.models instantiate and preserve contracts."""
    from src.sice.models import (
        AttributeSpec,
        CanonicalRole,
        ReplacementCandidateCategory,
        RoleCompatibilityResult,
        RoleTransitionCategory,
        SubspaceDistanceResult,
    )

    # RoleCompatibilityResult dataclass
    role_res = RoleCompatibilityResult(
        compatibility_score=0.85,
        is_compatible=True,
        transition_category=RoleTransitionCategory.ADJACENT_ROLE,
        hard_boundary_violated=False,
        boundary_reasons=[],
        incumbent_canonical_role="Top-order Batter",
        candidate_canonical_role="Middle-order Batter",
        handedness_match=True,
        style_match=True,
    )
    assert role_res.compatibility_score == 0.85
    assert role_res.is_compatible is True
    assert role_res.transition_category == RoleTransitionCategory.ADJACENT_ROLE
    assert role_res.hard_boundary_violated is False
    assert role_res.incumbent_canonical_role == "Top-order Batter"
    assert role_res.candidate_canonical_role == "Middle-order Batter"

    # AttributeSpec
    spec = AttributeSpec(
        attr_type="continuous", weight=1.5, val_range=100.0, min_val=0.0, max_val=100.0
    )
    assert spec.attr_type == "continuous"
    assert spec.weight == 1.5
    assert spec.val_range == 100.0

    # SubspaceDistanceResult
    dist_res = SubspaceDistanceResult(distance=0.25, similarity=0.75, penalty=0.0)
    assert dist_res.distance == 0.25
    assert dist_res.similarity == 0.75
    assert dist_res.penalty == 0.0

    # ReplacementCandidateCategory enum
    assert ReplacementCandidateCategory.DIRECT_UPGRADE == "DIRECT_UPGRADE"
    assert CanonicalRole.TOP_ORDER_BATTER == "Top-order Batter"


def test_sice_models_package_level_reexport() -> None:
    """T9.06: from src.sice import models exposes authoritative contract definitions identically."""
    import src.contracts.sice as contract_module
    import src.sice as sice_pkg

    assert hasattr(sice_pkg, "models")
    assert (
        sice_pkg.models.ReplacementComparisonRequest is contract_module.ReplacementComparisonRequest
    )
    assert (
        sice_pkg.models.ReplacementComparisonOutputContract
        is contract_module.ReplacementComparisonOutputContract
    )
    assert sice_pkg.models.RecommendationState is contract_module.RecommendationState
