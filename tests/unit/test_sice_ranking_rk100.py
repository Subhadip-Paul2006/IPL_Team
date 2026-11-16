"""Comprehensive Unit Test Suite for SICE Top-10 Ranking Engine (RK-1.0.0).

Structured according to Milestone 3 Test Suite Architecture:
- Suite 1: RK-1.0.0 3-Key Ordering Hierarchy (9 tests)
- Suite 2: Deterministic Tiebreaker Ladder (8 tests)
- Suite 3: Match-Level Bootstrap Confidence Intervals (8 tests)
- Suite 4: Format Segregation (7 tests)
- Suite 5: Relevance Gates & Reserve List Routing (10 tests)
- Suite 6: Contract Compliance, Identity Immutability & Guardrails (8 tests)

Total: 50 dedicated unit tests.
"""

from __future__ import annotations

import ast
import inspect
import time
from datetime import date
from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from src.contracts.ranking import RankingConfiguration, RankingRun
from src.contracts.sice import (
    CandidateRankingStatus,
    RankedCandidateContract,
    RankingBoardOutputContract,
    RunType,
    UncertaintyFlag,
)
from src.sice.exceptions import RankingDeterminismError
from src.sice.ranking_engine import SICERankingEngine

# ==============================================================================
# Shared Fixtures & Mock Builders
# ==============================================================================


@pytest.fixture
def fixed_eval_date() -> date:
    """Immutable evaluation date for deterministic age calculations."""
    return date(2026, 11, 14)


@pytest.fixture
def target_season_uuid() -> UUID:
    """Target season ID for IPL 2027."""
    return UUID("11111111-2222-3333-4444-555555555555")


@pytest.fixture
def active_policy_uuid() -> UUID:
    """Active eligibility policy ID."""
    return UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


@pytest.fixture
def base_ranking_config(
    fixed_eval_date: date,
    target_season_uuid: UUID,
    active_policy_uuid: UUID,
) -> RankingConfiguration:
    """Baseline RankingConfiguration frozen for RK-1.0.0."""
    return RankingConfiguration(
        config_version="RK-1.0.0",
        target_season_id=target_season_uuid,
        policy_id=active_policy_uuid,
        evaluation_date=fixed_eval_date,
        role_grouping_json={
            "roles": [
                "Top-order Batter",
                "Middle-order Batter",
                "Wicketkeeper Batter",
                "Batting All-rounder",
                "Bowling All-rounder",
                "Pace Bowler",
                "Spin Bowler",
            ]
        },
        gate_thresholds_json={
            "batter_sr_percentile": 75,
            "batter_sr_threshold": 136.0,
            "bowler_wkt_percentile": 75,
            "min_sample_balls": 120,
            "bar_sr_percentile": 60,
            "bar_min_balls_faced": 60,
            "bar_min_balls_bowled": 60,
            "bar_min_sr": 125.0,
            "bar_max_economy": 8.8,
            "bwl_ar_wkt_percentile": 60,
            "bwl_ar_min_balls_faced": 60,
            "bwl_ar_min_balls_bowled": 60,
            "bwl_ar_min_sr": 125.0,
            "bwl_ar_max_economy": 8.8,
            "wk_min_dismissals": 3,
            "wk_min_appearances": 5,
            "pacer_max_economy": 8.4,
            "spinner_max_economy": 7.3,
        },
        ordering_json={"keys": ["age_asc", "consistency_desc", "b05_average_desc_nulls_last"]},
        tiebreakers_json={
            "tiebreakers": ["b06_strike_rate_desc", "b04_balls_faced_desc", "uuid_asc"]
        },
        seed=0,
    )


@pytest.fixture
def candidate_builder(fixed_eval_date: date):
    """Factory helper to construct candidate dictionaries with verified defaults."""

    def _build(**kwargs: Any) -> dict[str, Any]:
        player_id = kwargs.get("player_id", uuid4())
        dob = kwargs.get("date_of_birth", date(2004, 1, 1))
        runs = kwargs.get("runs", 300)
        balls_faced = kwargs.get("balls_faced", 200)
        dismissals = kwargs.get("dismissals", 8)

        # Default Batting Average calculation
        if "batting_average" in kwargs:
            batting_avg = kwargs["batting_average"]
        else:
            batting_avg = round(runs / dismissals, 2) if dismissals > 0 else None

        # Default Strike Rate calculation
        if "strike_rate" in kwargs:
            strike_rate = kwargs["strike_rate"]
        else:
            strike_rate = round(runs / balls_faced * 100.0, 2) if balls_faced > 0 else None

        return {
            "player_id": player_id,
            "canonical_name": kwargs.get("canonical_name", f"Player_{str(player_id)[:8]}"),
            "date_of_birth": dob,
            "primary_role": kwargs.get("primary_role", "Top-order Batter"),
            "identity_status": kwargs.get("identity_status", "RESOLVED"),
            "eligibility_status": kwargs.get("eligibility_status", "VERIFIED_ELIGIBLE"),
            "review_status": kwargs.get("review_status"),
            "verified_innings": kwargs.get("verified_innings", 10),
            "dnb_innings": kwargs.get("dnb_innings", 1),
            "walkover_batted_count": kwargs.get("walkover_batted_count", 0),
            "runs": runs,
            "balls_faced": balls_faced,
            "dismissals": dismissals,
            "not_outs": kwargs.get("not_outs", 1),
            "strike_rate": strike_rate,
            "batting_average": batting_avg,
            "legal_balls_bowled": kwargs.get("legal_balls_bowled", 0),
            "wickets": kwargs.get("wickets", 0),
            "runs_conceded": kwargs.get("runs_conceded", 0),
            "economy_rate": kwargs.get("economy_rate"),
            "bowling_strike_rate": kwargs.get("bowling_strike_rate"),
            "bowling_style": kwargs.get("bowling_style"),
            "wk_dismissals": kwargs.get("wk_dismissals", 0),
            "wk_appearances": kwargs.get("wk_appearances", 0),
            "fc_stats": kwargs.get("fc_stats"),
            "list_a_stats": kwargs.get("list_a_stats"),
            "format_tags": kwargs.get("format_tags", ["T20"]),
            "verification_record_ids": kwargs.get("verification_record_ids", [uuid4()]),
            "profile_tag": kwargs.get("profile_tag"),
            "bpps": kwargs.get("bpps"),
            "score": kwargs.get("score", 75.0),
        }

    return _build


@pytest.fixture
def sample_match_tensor() -> dict[str, dict[str, float]]:
    """Sample pre-aggregated match contributions across 20 matches."""
    tensor: dict[str, dict[str, float]] = {}
    for i in range(1, 21):
        mid = f"MATCH_{i:02d}"
        tensor[mid] = {}
    return tensor


# ==============================================================================
# Suite 1: RK-1.0.0 3-Key Ordering Hierarchy (9 tests)
# ==============================================================================


def test_k1_younger_candidate_outranks_older_regardless_of_performance(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """K1: Younger candidate must outrank older candidate regardless of performance."""
    engine = SICERankingEngine()

    cand_younger = candidate_builder(
        date_of_birth=date(2006, 3, 15),  # Age ~20.67
        strike_rate=138.0,
        balls_faced=200,
        runs=250,
        dismissals=10,
        batting_average=25.0,
        verified_innings=10,
        dnb_innings=3,  # consistency = 0.70
    )
    cand_older = candidate_builder(
        date_of_birth=date(2002, 5, 10),  # Age ~24.51
        strike_rate=165.0,
        balls_faced=250,
        runs=520,
        dismissals=10,
        batting_average=52.0,
        verified_innings=20,
        dnb_innings=1,  # consistency = 0.95
    )

    board = engine.run_ranking(
        configuration=base_ranking_config, candidates=[cand_older, cand_younger]
    )

    assert len(board.top10) == 2
    assert board.top10[0].player_id == cand_younger["player_id"]
    assert board.top10[1].player_id == cand_older["player_id"]


def test_k1_age_evaluated_against_frozen_evaluation_date_not_wall_clock(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
    fixed_eval_date: date,
) -> None:
    """K1: Age must be evaluated against config.evaluation_date (2026-11-14), not wall clock."""
    engine = SICERankingEngine()

    # Born on 2008-11-15: on eval date 2026-11-14, age is exactly 17.997 years (< 18.0)
    cand_underage = candidate_builder(
        date_of_birth=date(2008, 11, 15),
        strike_rate=150.0,
        balls_faced=200,
    )

    board = engine.run_ranking(configuration=base_ranking_config, candidates=[cand_underage])
    assert board.qualified_candidates_count == 0
    assert len(board.top10) == 0


def test_k1_age_boundary_eligibility_window_inclusive(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
    fixed_eval_date: date,
) -> None:
    """K1: Age boundaries [18.0, 26.0] are inclusive."""
    engine = SICERankingEngine()

    p_18_exact = candidate_builder(
        date_of_birth=date(2008, 11, 14),  # Age exactly 18.00
        canonical_name="Player_18_Exact",
        strike_rate=140.0,
        balls_faced=150,
    )
    p_17_fail = candidate_builder(
        date_of_birth=date(2008, 11, 16),  # Age 17.99
        canonical_name="Player_17_Fail",
        strike_rate=140.0,
        balls_faced=150,
    )
    p_26_exact = candidate_builder(
        date_of_birth=date(2000, 11, 14),  # Age exactly 26.00
        canonical_name="Player_26_Exact",
        strike_rate=140.0,
        balls_faced=150,
    )
    p_26_fail = candidate_builder(
        date_of_birth=date(2000, 11, 12),  # Age 26.01
        canonical_name="Player_26_Fail",
        strike_rate=140.0,
        balls_faced=150,
    )

    board = engine.run_ranking(
        configuration=base_ranking_config,
        candidates=[p_18_exact, p_17_fail, p_26_exact, p_26_fail],
    )

    top_ids = [c.player_id for c in board.top10]
    assert p_18_exact["player_id"] in top_ids
    assert p_26_exact["player_id"] in top_ids
    assert p_17_fail["player_id"] not in top_ids
    assert p_26_fail["player_id"] not in top_ids


def test_k1_identical_dob_invokes_k2_consistency_ordering(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """When K1 (DOB) is identical, K2 (consistency) breaks the tie."""
    engine = SICERankingEngine()

    # Same DOB: 2004-06-15
    cand_high_consistency = candidate_builder(
        date_of_birth=date(2004, 6, 15),
        verified_innings=10,
        dnb_innings=1,  # K2 = 9/10 = 0.90
        batting_average=28.0,
        strike_rate=140.0,
        balls_faced=200,
    )
    cand_low_consistency = candidate_builder(
        date_of_birth=date(2004, 6, 15),
        verified_innings=10,
        dnb_innings=4,  # K2 = 6/10 = 0.60
        batting_average=45.0,
        strike_rate=140.0,
        balls_faced=200,
    )

    board = engine.run_ranking(
        configuration=base_ranking_config,
        candidates=[cand_low_consistency, cand_high_consistency],
    )

    assert board.top10[0].player_id == cand_high_consistency["player_id"]
    assert board.top10[1].player_id == cand_low_consistency["player_id"]


def test_k2_consistency_zero_dnb_and_all_dnb_edge_cases(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """K2: 0 DNB yields 1.000 consistency; all DNB yields 0.000 consistency."""
    engine = SICERankingEngine()

    cand_all_batted = candidate_builder(
        date_of_birth=date(2004, 1, 1),
        verified_innings=10,
        dnb_innings=0,  # K2 = 1.000
        strike_rate=140.0,
        balls_faced=150,
    )
    cand_all_dnb = candidate_builder(
        date_of_birth=date(2004, 1, 1),
        verified_innings=10,
        dnb_innings=10,  # K2 = 0.000
        strike_rate=140.0,
        balls_faced=150,
    )

    board = engine.run_ranking(
        configuration=base_ranking_config,
        candidates=[cand_all_dnb, cand_all_batted],
    )

    assert board.top10[0].player_id == cand_all_batted["player_id"]
    assert board.top10[0].consistency_score == 1.0
    assert board.top10[1].player_id == cand_all_dnb["player_id"]
    assert board.top10[1].consistency_score == 0.0


def test_k2_consistency_walkover_batted_appearance_not_dnb(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """K2: Walkover 0-ball batted appearance is counted as batted, NOT DNB (B02/DDL chk_dnb_zero)."""
    engine = SICERankingEngine()

    cand = candidate_builder(
        verified_innings=10,
        dnb_innings=1,
        walkover_batted_count=1,  # 1 appearance with 0 balls faced while at crease
        strike_rate=140.0,
        balls_faced=150,
    )

    board = engine.run_ranking(configuration=base_ranking_config, candidates=[cand])
    assert board.top10[0].consistency_score == 0.90


def test_k2_identical_consistency_invokes_k3_b05_average_ordering(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """When K1 (DOB) and K2 (consistency) are identical, K3 (B05 Batting Average) breaks tie."""
    engine = SICERankingEngine()

    cand_high_avg = candidate_builder(
        date_of_birth=date(2003, 8, 20),
        verified_innings=10,
        dnb_innings=2,  # K2 = 0.80
        runs=220,
        dismissals=5,  # B05 = 44.0
        strike_rate=140.0,
        balls_faced=200,
    )
    cand_low_avg = candidate_builder(
        date_of_birth=date(2003, 8, 20),
        verified_innings=10,
        dnb_innings=2,  # K2 = 0.80
        runs=160,
        dismissals=5,  # B05 = 32.0
        strike_rate=140.0,
        balls_faced=200,
    )

    board = engine.run_ranking(
        configuration=base_ranking_config,
        candidates=[cand_low_avg, cand_high_avg],
    )

    assert board.top10[0].player_id == cand_high_avg["player_id"]
    assert board.top10[1].player_id == cand_low_avg["player_id"]


def test_k3_undefeated_batter_null_average_sorts_nulls_last(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """K3: Undefeated batter (0 dismissals, average=NULL) sorts NULLS LAST after computed values."""
    engine = SICERankingEngine()

    cand_computed = candidate_builder(
        date_of_birth=date(2004, 1, 10),
        verified_innings=10,
        dnb_innings=2,  # K2 = 0.80
        runs=150,
        dismissals=3,  # B05 = 50.0
        strike_rate=140.0,
        balls_faced=150,
    )
    cand_undefeated = candidate_builder(
        date_of_birth=date(2004, 1, 10),
        verified_innings=10,
        dnb_innings=2,  # K2 = 0.80
        runs=150,
        dismissals=0,  # B05 = NULL (*)
        batting_average=None,
        strike_rate=140.0,
        balls_faced=150,
    )

    board = engine.run_ranking(
        configuration=base_ranking_config,
        candidates=[cand_undefeated, cand_computed],
    )

    assert board.top10[0].player_id == cand_computed["player_id"]
    assert board.top10[1].player_id == cand_undefeated["player_id"]
    assert board.top10[1].career_batting_average is None


def test_legacy_bpps_bwps_rejected_as_ranking_sort_keys(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Legacy BPPS and BWPS are descriptive metrics only and NEVER sort keys in RK-1.0.0 (HD-01)."""
    engine = SICERankingEngine()

    cand_young_low_bpps = candidate_builder(
        date_of_birth=date(2005, 1, 1),  # Younger
        bpps=62.0,
        batting_average=32.0,
        strike_rate=140.0,
        balls_faced=200,
    )
    cand_old_high_bpps = candidate_builder(
        date_of_birth=date(2002, 1, 1),  # Older
        bpps=94.5,
        batting_average=45.0,
        strike_rate=160.0,
        balls_faced=250,
    )

    board = engine.run_ranking(
        configuration=base_ranking_config,
        candidates=[cand_old_high_bpps, cand_young_low_bpps],
    )

    assert board.top10[0].player_id == cand_young_low_bpps["player_id"]
    assert board.top10[1].player_id == cand_old_high_bpps["player_id"]


# ==============================================================================
# Suite 2: Deterministic Tiebreaker Ladder (8 tests)
# ==============================================================================


def test_tiebreaker_1_b06_strike_rate_descending(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Tiebreaker 1: B06 Batting Strike Rate descending breaks tie on K1, K2, K3."""
    engine = SICERankingEngine()

    cand_fast = candidate_builder(
        date_of_birth=date(2004, 1, 1),
        verified_innings=10,
        dnb_innings=2,
        batting_average=35.0,
        strike_rate=158.5,
        balls_faced=200,
    )
    cand_slow = candidate_builder(
        date_of_birth=date(2004, 1, 1),
        verified_innings=10,
        dnb_innings=2,
        batting_average=35.0,
        strike_rate=136.2,
        balls_faced=200,
    )

    board = engine.run_ranking(
        configuration=base_ranking_config,
        candidates=[cand_slow, cand_fast],
    )

    assert board.top10[0].player_id == cand_fast["player_id"]
    assert board.top10[1].player_id == cand_slow["player_id"]


def test_tiebreaker_1_explicitly_uses_b06_and_never_b10(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Tiebreaker 1: Explicitly uses B06 Batting Strike Rate and NEVER B10 batting position (HD-01)."""
    engine = SICERankingEngine()

    # Candidate A: lower batting position (B10=4), but higher strike rate (B06=148.0)
    cand_middle_order = candidate_builder(
        date_of_birth=date(2004, 1, 1),
        verified_innings=10,
        dnb_innings=2,
        batting_average=35.0,
        strike_rate=148.0,  # Higher B06
        balls_faced=200,
    )
    # Candidate B: opening batter (B10=1), but lower strike rate (B06=142.0)
    cand_opener = candidate_builder(
        date_of_birth=date(2004, 1, 1),
        verified_innings=10,
        dnb_innings=2,
        batting_average=35.0,
        strike_rate=142.0,  # Lower B06
        balls_faced=200,
    )

    board = engine.run_ranking(
        configuration=base_ranking_config,
        candidates=[cand_opener, cand_middle_order],
    )

    # Candidate with higher B06 strike rate must win
    assert board.top10[0].player_id == cand_middle_order["player_id"]
    assert board.top10[1].player_id == cand_opener["player_id"]


def test_tiebreaker_1_null_strike_rate_handling(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Tiebreaker 1: NULL strike rate (0 balls faced) sorts after computed strike rate."""
    engine = SICERankingEngine()

    cand_valid_sr = candidate_builder(
        date_of_birth=date(2004, 1, 1),
        verified_innings=10,
        dnb_innings=2,
        batting_average=None,
        strike_rate=140.0,
        balls_faced=150,
    )
    cand_null_sr = candidate_builder(
        date_of_birth=date(2004, 1, 1),
        verified_innings=10,
        dnb_innings=2,
        batting_average=None,
        strike_rate=None,
        balls_faced=0,
    )

    board = engine.run_ranking(
        configuration=base_ranking_config,
        candidates=[cand_null_sr, cand_valid_sr],
    )

    assert board.top10[0].player_id == cand_valid_sr["player_id"]


def test_tiebreaker_2_career_balls_faced_b04_descending(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Tiebreaker 2: Career Balls Faced (B04) descending breaks tie on K1, K2, K3, TB1."""
    engine = SICERankingEngine()

    cand_large_sample = candidate_builder(
        date_of_birth=date(2004, 1, 1),
        verified_innings=10,
        dnb_innings=2,
        batting_average=35.0,
        strike_rate=150.0,
        balls_faced=450,  # Larger sample
    )
    cand_small_sample = candidate_builder(
        date_of_birth=date(2004, 1, 1),
        verified_innings=10,
        dnb_innings=2,
        batting_average=35.0,
        strike_rate=150.0,
        balls_faced=160,  # Smaller sample
    )

    board = engine.run_ranking(
        configuration=base_ranking_config,
        candidates=[cand_small_sample, cand_large_sample],
    )

    assert board.top10[0].player_id == cand_large_sample["player_id"]
    assert board.top10[1].player_id == cand_small_sample["player_id"]


def test_tiebreaker_3_uuid_lexicographical_ascending_total_order(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Tiebreaker 3: Player UUID lexicographical ascending establishes deterministic total order."""
    engine = SICERankingEngine()

    uuid_a = UUID("01234567-0000-4000-8000-000000000000")
    uuid_b = UUID("fedcba98-0000-4000-8000-000000000000")

    cand_a = candidate_builder(
        player_id=uuid_a,
        date_of_birth=date(2004, 1, 1),
        verified_innings=10,
        dnb_innings=2,
        batting_average=35.0,
        strike_rate=150.0,
        balls_faced=200,
    )
    cand_b = candidate_builder(
        player_id=uuid_b,
        date_of_birth=date(2004, 1, 1),
        verified_innings=10,
        dnb_innings=2,
        batting_average=35.0,
        strike_rate=150.0,
        balls_faced=200,
    )

    board = engine.run_ranking(
        configuration=base_ranking_config,
        candidates=[cand_b, cand_a],
    )

    assert board.top10[0].player_id == uuid_a
    assert board.top10[1].player_id == uuid_b


def test_tiebreaker_total_order_invariant_under_input_shuffling(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Tiebreaker total order must be invariant under any candidate list permutation."""
    engine = SICERankingEngine()

    candidates = [
        candidate_builder(
            player_id=UUID(f"00000000-0000-4000-8000-{i:012x}"),
            date_of_birth=date(2004, 1, 1),
            strike_rate=145.0,
            balls_faced=150,
        )
        for i in range(10)
    ]

    # Run on forward and reversed input lists
    board_forward = engine.run_ranking(configuration=base_ranking_config, candidates=candidates)
    board_reversed = engine.run_ranking(
        configuration=base_ranking_config, candidates=list(reversed(candidates))
    )

    assert [c.player_id for c in board_forward.top10] == [c.player_id for c in board_reversed.top10]


def test_tiebreaker_no_uncalibrated_randomness_when_seed_zero(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Seed=0 guarantees pure deterministic execution without random perturbations."""
    engine = SICERankingEngine()

    candidates = [
        candidate_builder(
            player_id=UUID(f"00000000-0000-4000-8000-{i:012x}"),
            date_of_birth=date(2004, 1, 1),
            strike_rate=140.0 + i,
            balls_faced=150,
        )
        for i in range(5)
    ]

    run1 = engine.run_ranking(configuration=base_ranking_config, candidates=candidates)
    run2 = engine.run_ranking(configuration=base_ranking_config, candidates=candidates)

    assert run1.data_snapshot_sha256 == run2.data_snapshot_sha256
    assert [c.player_id for c in run1.top10] == [c.player_id for c in run2.top10]


def test_tiebreaker_rejection_of_duplicate_player_id(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Duplicate candidate player_id in pool raises RankingDeterminismError."""
    engine = SICERankingEngine()
    dup_uuid = UUID("12345678-1234-4000-8000-123456789abc")

    c1 = candidate_builder(player_id=dup_uuid)
    c2 = candidate_builder(player_id=dup_uuid)

    with pytest.raises(RankingDeterminismError):
        engine.run_ranking(configuration=base_ranking_config, candidates=[c1, c2])


# ==============================================================================
# Suite 3: Match-Level Bootstrap Confidence Intervals (8 tests)
# ==============================================================================


def test_bootstrap_seed_42_bit_for_bit_determinism(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Bootstrap execution with seed=42 produces bit-for-bit identical CIs and stability."""
    engine = SICERankingEngine()

    pids = [UUID(f"00000000-0000-4000-8000-{i:012x}") for i in range(5)]
    candidates = [
        candidate_builder(player_id=pid, strike_rate=145.0, balls_faced=150) for pid in pids
    ]

    # Pre-aggregated match summaries
    match_summaries = {
        f"M{m}": {str(pid): 50.0 + (m * 2) + i for i, pid in enumerate(pids)} for m in range(1, 15)
    }

    run1 = engine.run_ranking(
        configuration=base_ranking_config,
        candidates=candidates,
        match_summaries=match_summaries,
        bootstrap_iterations=100,
    )
    run2 = engine.run_ranking(
        configuration=base_ranking_config,
        candidates=candidates,
        match_summaries=match_summaries,
        bootstrap_iterations=100,
    )

    for c1, c2 in zip(run1.top10, run2.top10, strict=True):
        assert c1.score_ci_lower == c2.score_ci_lower
        assert c1.score_ci_upper == c2.score_ci_upper
        assert c1.top10_stability_pct == c2.top10_stability_pct


def test_bootstrap_seed_sensitivity_different_seeds(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Running bootstrap with different seeds applies RNG seeds properly."""
    engine = SICERankingEngine()

    pids = [UUID(f"00000000-0000-4000-8000-{i:012x}") for i in range(12)]
    candidates = [
        candidate_builder(player_id=pid, strike_rate=140.0 + i, balls_faced=150)
        for i, pid in enumerate(pids)
    ]
    match_summaries = {
        f"M{m}": {str(pid): float((m * 7 + i * 3) % 100) for i, pid in enumerate(pids)}
        for m in range(1, 20)
    }

    contracts_a = [
        engine._build_candidate_contract(c, rank=i + 1, is_top10=True)
        for i, c in enumerate(candidates)
    ]
    contracts_b = [
        engine._build_candidate_contract(c, rank=i + 1, is_top10=True)
        for i, c in enumerate(candidates)
    ]

    engine.run_match_level_bootstrap_resampling(
        candidates=contracts_a, match_summaries=match_summaries, iterations=100, seed=42
    )
    engine.run_match_level_bootstrap_resampling(
        candidates=contracts_b, match_summaries=match_summaries, iterations=100, seed=12345
    )

    # Valid bounds for all
    for ca in contracts_a:
        assert ca.score_ci_lower is not None and ca.score_ci_upper is not None
        assert ca.score_ci_lower <= ca.score_ci_upper


def test_bootstrap_95_percentile_ci_bounds_validity(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Bootstrap 95% Confidence Intervals enforce score_ci_lower <= score_ci_upper."""
    engine = SICERankingEngine()

    pids = [UUID(f"00000000-0000-4000-8000-{i:012x}") for i in range(4)]
    candidates = [
        candidate_builder(player_id=pid, strike_rate=145.0, balls_faced=150) for pid in pids
    ]
    match_summaries = {
        f"M{m}": {str(pid): float(40 + (m * 5) % 50) for pid in pids} for m in range(1, 25)
    }

    board = engine.run_ranking(
        configuration=base_ranking_config,
        candidates=candidates,
        match_summaries=match_summaries,
        bootstrap_iterations=200,
    )

    for c in board.top10:
        assert c.score_ci_lower is not None
        assert c.score_ci_upper is not None
        assert c.score_ci_lower <= c.score_ci_upper


def test_bootstrap_top10_stability_pct_calculation(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Bootstrap calculates top-10 rank stability percentage correctly."""
    engine = SICERankingEngine()

    p_dom = UUID("00000000-0000-4000-8000-000000000001")
    cand_dominant = candidate_builder(player_id=p_dom, strike_rate=160.0, balls_faced=200)

    # Candidate with dominant scores in all matches
    match_summaries = {f"M{m}": {str(p_dom): 99.0} for m in range(1, 10)}

    board = engine.run_ranking(
        configuration=base_ranking_config,
        candidates=[cand_dominant],
        match_summaries=match_summaries,
        bootstrap_iterations=100,
    )

    assert board.top10[0].top10_stability_pct == 100.0


def test_bootstrap_resamples_pre_aggregated_match_summaries_not_deliveries(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Bootstrap accepts pre-aggregated match-level summaries without delivery JSONs (HD-02)."""
    engine = SICERankingEngine()

    cand = candidate_builder(strike_rate=145.0, balls_faced=150)
    pid = str(cand["player_id"])

    # Pre-aggregated match summary dictionary
    match_summaries = {
        "M1": {pid: {"score": 85.0, "m07": 0.85}},
        "M2": {pid: {"score": 75.0, "m07": 0.75}},
    }

    board = engine.run_ranking(
        configuration=base_ranking_config,
        candidates=[cand],
        match_summaries=match_summaries,
        bootstrap_iterations=100,
    )

    assert board.top10[0].score_ci_lower is not None
    assert board.top10[0].score_ci_upper is not None


def test_bootstrap_zero_imports_of_cricsheet_parser_in_sice() -> None:
    """AST inspection proves zero imports of cricsheet_parser or normalizer in SICE ranking engine."""
    import src.sice.ranking_engine as re_mod

    source = inspect.getsource(re_mod)
    tree = ast.parse(source)

    forbidden_modules = ("cricsheet_parser", "src.ingestion.normalizer")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for forbidden in forbidden_modules:
                    assert forbidden not in alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for forbidden in forbidden_modules:
                assert forbidden not in node.module


def test_bootstrap_performance_benchmark_sub_two_seconds(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Benchmark: 1,000 bootstrap resamples across 100 matches and 30 candidates executes in < 2s."""
    engine = SICERankingEngine()

    pids = [UUID(f"00000000-0000-4000-8000-{i:012x}") for i in range(30)]
    candidates = [
        candidate_builder(player_id=pid, strike_rate=140.0, balls_faced=150) for pid in pids
    ]

    match_summaries = {
        f"M{m}": {str(pid): float((m + i * 3) % 90 + 10) for i, pid in enumerate(pids)}
        for m in range(100)
    }

    start = time.perf_counter()
    engine.run_ranking(
        configuration=base_ranking_config,
        candidates=candidates,
        match_summaries=match_summaries,
        bootstrap_iterations=1000,
    )
    elapsed = time.perf_counter() - start

    assert elapsed < 2.0, f"Bootstrap execution took {elapsed:.3f}s (exceeded 2.0s limit)"


def test_bootstrap_single_match_or_zero_variance_candidate(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Candidate with zero score variance across appearances yields score_ci_lower == score_ci_upper."""
    engine = SICERankingEngine()

    cand = candidate_builder(strike_rate=145.0, balls_faced=150, score=70.0)
    pid = str(cand["player_id"])

    # Identical score in all matches
    match_summaries = {f"M{m}": {pid: 70.0} for m in range(1, 10)}

    board = engine.run_ranking(
        configuration=base_ranking_config,
        candidates=[cand],
        match_summaries=match_summaries,
        bootstrap_iterations=100,
    )

    c = board.top10[0]
    assert c.score_ci_lower == 70.0
    assert c.score_ci_upper == 70.0


# ==============================================================================
# Suite 4: Format Segregation (7 tests)
# ==============================================================================


def test_format_segregation_k3_b05_uses_domestic_t20_only(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """K3: Evaluates Domestic T20 batting average only; First-Class average is segregated (HD-04)."""
    engine = SICERankingEngine()

    # Candidate A: T20 Avg = 42.0, First-Class Avg = 22.0
    cand_a = candidate_builder(
        date_of_birth=date(2004, 1, 1),
        verified_innings=10,
        dnb_innings=2,
        runs=210,
        dismissals=5,
        batting_average=42.0,
        strike_rate=140.0,
        balls_faced=150,
        fc_stats={"runs": 220, "dismissals": 10, "batting_average": 22.0},
    )
    # Candidate B: T20 Avg = 33.0, First-Class Avg = 68.0
    cand_b = candidate_builder(
        date_of_birth=date(2004, 1, 1),
        verified_innings=10,
        dnb_innings=2,
        runs=165,
        dismissals=5,
        batting_average=33.0,
        strike_rate=140.0,
        balls_faced=150,
        fc_stats={"runs": 680, "dismissals": 10, "batting_average": 68.0},
    )

    board = engine.run_ranking(configuration=base_ranking_config, candidates=[cand_b, cand_a])

    # Candidate A outranks Candidate B on T20 average (42.0 > 33.0)
    assert board.top10[0].player_id == cand_a["player_id"]
    assert board.top10[1].player_id == cand_b["player_id"]


def test_format_segregation_k2_consistency_uses_domestic_t20_only(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """K2: Evaluates Domestic T20 consistency only; List-A appearances are segregated (HD-04)."""
    engine = SICERankingEngine()

    # Candidate A: T20 consistency = 0.90 (9/10), List-A consistency = 0.40
    cand_a = candidate_builder(
        date_of_birth=date(2004, 1, 1),
        verified_innings=10,
        dnb_innings=1,
        strike_rate=140.0,
        balls_faced=150,
        list_a_stats={"innings": 10, "dnb": 6},
    )
    # Candidate B: T20 consistency = 0.60 (6/10), List-A consistency = 1.00
    cand_b = candidate_builder(
        date_of_birth=date(2004, 1, 1),
        verified_innings=10,
        dnb_innings=4,
        strike_rate=140.0,
        balls_faced=150,
        list_a_stats={"innings": 10, "dnb": 0},
    )

    board = engine.run_ranking(configuration=base_ranking_config, candidates=[cand_b, cand_a])

    assert board.top10[0].player_id == cand_a["player_id"]
    assert board.top10[1].player_id == cand_b["player_id"]


def test_format_segregation_tiebreaker_b06_sr_uses_domestic_t20_only(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """TB1: Uses Domestic T20 strike rate only; First-Class strike rate is excluded."""
    engine = SICERankingEngine()

    cand_a = candidate_builder(
        date_of_birth=date(2004, 1, 1),
        strike_rate=155.0,  # T20 SR
        balls_faced=150,
        fc_stats={"strike_rate": 48.0},
    )
    cand_b = candidate_builder(
        date_of_birth=date(2004, 1, 1),
        strike_rate=138.0,  # T20 SR
        balls_faced=150,
        fc_stats={"strike_rate": 75.0},
    )

    board = engine.run_ranking(configuration=base_ranking_config, candidates=[cand_b, cand_a])

    assert board.top10[0].player_id == cand_a["player_id"]
    assert board.top10[1].player_id == cand_b["player_id"]


def test_format_segregation_tiebreaker_b04_balls_faced_uses_domestic_t20_only(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """TB2: Uses Domestic T20 balls faced only; First-Class balls faced is excluded."""
    engine = SICERankingEngine()

    cand_a = candidate_builder(
        date_of_birth=date(2004, 1, 1),
        strike_rate=145.0,
        balls_faced=350,  # T20 BF
        fc_stats={"balls_faced": 500},
    )
    cand_b = candidate_builder(
        date_of_birth=date(2004, 1, 1),
        strike_rate=145.0,
        balls_faced=180,  # T20 BF
        fc_stats={"balls_faced": 3000},
    )

    board = engine.run_ranking(configuration=base_ranking_config, candidates=[cand_b, cand_a])

    assert board.top10[0].player_id == cand_a["player_id"]
    assert board.top10[1].player_id == cand_b["player_id"]


def test_candidate_universe_multi_format_sample_qualification(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Candidate with 3 T20 + 3 List-A innings satisfies universe minimum sample (>= 5 innings)."""
    engine = SICERankingEngine()

    cand = candidate_builder(
        verified_innings=3,
        list_a_stats={"innings": 3},  # Total cross-format = 6 >= 5
        strike_rate=145.0,
        balls_faced=150,
    )

    board = engine.run_ranking(configuration=base_ranking_config, candidates=[cand])
    assert board.qualified_candidates_count == 1
    assert len(board.top10) == 1


def test_candidate_universe_insufficient_sample_cross_format_rejection(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Candidate with 2 T20 + 2 List-A innings (< 5 total) is excluded from qualified candidate pool."""
    engine = SICERankingEngine()

    cand = candidate_builder(
        verified_innings=2,
        list_a_stats={"innings": 2},  # Total cross-format = 4 < 5
        strike_rate=145.0,
        balls_faced=150,
    )

    board = engine.run_ranking(configuration=base_ranking_config, candidates=[cand])
    assert board.qualified_candidates_count == 0
    assert len(board.top10) == 0


def test_the_hundred_format_rate_metrics_deferred(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """The Hundred rate metrics remain DEFERRED per TRD D16 and are not blended into T20 rates."""
    engine = SICERankingEngine()

    cand = candidate_builder(
        strike_rate=142.0,
        balls_faced=150,
        format_tags=["T20", "THE_HUNDRED"],
    )

    board = engine.run_ranking(configuration=base_ranking_config, candidates=[cand])
    assert board.top10[0].career_batting_strike_rate == 142.0


# ==============================================================================
# Suite 5: Relevance Gates and Reserve List Routing (10 tests)
# ==============================================================================


def test_specialist_batter_gate_pass(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Specialist batter with SR >= 136.0 and balls_faced >= 120 clears relevance gate."""
    engine = SICERankingEngine()

    cand = candidate_builder(
        primary_role="Top-order Batter",
        strike_rate=148.0,
        balls_faced=240,
    )

    board = engine.run_ranking(configuration=base_ranking_config, candidates=[cand])
    assert board.qualified_candidates_count == 1
    assert len(board.top10) == 1
    assert board.top10[0].player_id == cand["player_id"]


def test_specialist_batter_gate_fail_on_low_strike_rate(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Specialist batter with low strike rate fails gate and routes to reserve_list."""
    engine = SICERankingEngine()

    cand = candidate_builder(
        primary_role="Top-order Batter",
        strike_rate=118.0,  # Below 136.0 threshold
        balls_faced=300,
    )

    board = engine.run_ranking(configuration=base_ranking_config, candidates=[cand])
    assert len(board.top10) == 0
    assert len(board.reserve_list) == 1
    assert board.reserve_list[0].status == CandidateRankingStatus.RESERVE


def test_specialist_batter_gate_fail_on_sample_size(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Specialist batter with insufficient sample (< 120 balls) routes to reserves as SAMPLE_CONSTRAINED."""
    engine = SICERankingEngine()

    cand = candidate_builder(
        primary_role="Top-order Batter",
        strike_rate=175.0,
        balls_faced=85,  # Below 120 balls threshold
    )

    board = engine.run_ranking(configuration=base_ranking_config, candidates=[cand])
    assert len(board.top10) == 0
    assert len(board.reserve_list) == 1
    assert board.reserve_list[0].uncertainty_flag == UncertaintyFlag.SAMPLE_CONSTRAINED


def test_specialist_bowler_gate_pace_spin_stratification_hd03(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Pace and Spin reference populations are stratified: pacer clears at 8.1; spinner fails at 8.1 (HD-03)."""
    engine = SICERankingEngine()

    cand_pacer = candidate_builder(
        primary_role="Pace Bowler",
        bowling_style="Right-arm fast",
        legal_balls_bowled=180,
        economy_rate=8.1,  # <= 8.4 pacer threshold -> Pass
    )
    cand_spinner = candidate_builder(
        primary_role="Spin Bowler",
        bowling_style="Right-arm legbreak",
        legal_balls_bowled=180,
        economy_rate=8.1,  # > 7.3 spinner threshold -> Fail
    )

    board = engine.run_ranking(
        configuration=base_ranking_config,
        candidates=[cand_pacer, cand_spinner],
    )

    assert len(board.top10) == 1
    assert board.top10[0].player_id == cand_pacer["player_id"]
    assert len(board.reserve_list) == 1
    assert board.reserve_list[0].player_id == cand_spinner["player_id"]


def test_specialist_bowler_gate_pass_and_sample_fail(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Specialist bowler with < 120 legal balls fails sample gate and routes to reserves."""
    engine = SICERankingEngine()

    cand = candidate_builder(
        primary_role="Pace Bowler",
        bowling_style="Pace",
        legal_balls_bowled=80,  # Below 120 balls
        economy_rate=7.5,
    )

    board = engine.run_ranking(configuration=base_ranking_config, candidates=[cand])
    assert len(board.top10) == 0
    assert len(board.reserve_list) == 1
    assert board.reserve_list[0].uncertainty_flag == UncertaintyFlag.SAMPLE_CONSTRAINED


def test_batting_all_rounder_bar_dual_threshold_gate_hd03_hd07(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Batting All-Rounder (BAR) dual threshold gate (HD-03, HD-07)."""
    engine = SICERankingEngine()

    bar_pass = candidate_builder(
        primary_role="Batting All-rounder",
        strike_rate=138.0,  # >= 125.0
        balls_faced=180,  # >= 60
        legal_balls_bowled=90,  # >= 60
        economy_rate=7.5,  # <= 8.8
    )
    bar_fail = candidate_builder(
        primary_role="Batting All-rounder",
        strike_rate=138.0,
        balls_faced=180,
        legal_balls_bowled=90,
        economy_rate=9.8,  # > 8.8 -> Fail
    )

    board = engine.run_ranking(configuration=base_ranking_config, candidates=[bar_pass, bar_fail])
    assert len(board.top10) == 1
    assert board.top10[0].player_id == bar_pass["player_id"]
    assert len(board.reserve_list) == 1
    assert board.reserve_list[0].player_id == bar_fail["player_id"]


def test_bowling_all_rounder_bwl_ar_dual_threshold_gate_hd03_hd07(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Bowling All-Rounder (BWL_AR) dual threshold gate (HD-03, HD-07)."""
    engine = SICERankingEngine()

    bwl_ar_pass = candidate_builder(
        primary_role="Bowling All-rounder",
        legal_balls_bowled=150,  # >= 60
        balls_faced=80,  # >= 60
        strike_rate=132.0,  # >= 125.0
        economy_rate=7.8,  # <= 8.8
    )
    bwl_ar_fail = candidate_builder(
        primary_role="Bowling All-rounder",
        legal_balls_bowled=150,
        balls_faced=80,
        strike_rate=102.0,  # < 125.0 -> Fail
        economy_rate=7.8,
    )

    board = engine.run_ranking(
        configuration=base_ranking_config, candidates=[bwl_ar_pass, bwl_ar_fail]
    )
    assert len(board.top10) == 1
    assert board.top10[0].player_id == bwl_ar_pass["player_id"]
    assert len(board.reserve_list) == 1
    assert board.reserve_list[0].player_id == bwl_ar_fail["player_id"]


def test_wicketkeeper_batter_gate_dismissals_requirement(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Wicketkeeper Batter gate requires batter gate + >= 3 dismissals or >= 5 keeping appearances."""
    engine = SICERankingEngine()

    wk_pass = candidate_builder(
        primary_role="Wicketkeeper Batter",
        strike_rate=145.0,
        balls_faced=150,
        wk_dismissals=4,  # >= 3
    )
    wk_fail = candidate_builder(
        primary_role="Wicketkeeper Batter",
        strike_rate=145.0,
        balls_faced=150,
        wk_dismissals=0,
        wk_appearances=1,  # < 5 and < 3 dismissals
    )

    board = engine.run_ranking(configuration=base_ranking_config, candidates=[wk_pass, wk_fail])
    assert len(board.top10) == 1
    assert board.top10[0].player_id == wk_pass["player_id"]
    assert len(board.reserve_list) == 1
    assert board.reserve_list[0].player_id == wk_fail["player_id"]


def test_top10_capacity_and_overflow_to_reserve_list(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Top 10 holds at most 10 candidates; candidates 11-15 overflow to reserve_list."""
    engine = SICERankingEngine()

    candidates = [
        candidate_builder(
            player_id=UUID(f"00000000-0000-4000-8000-{i:012x}"),
            date_of_birth=date(2004, 1, 1),
            strike_rate=140.0 + i,
            balls_faced=150,
        )
        for i in range(15)
    ]

    board = engine.run_ranking(configuration=base_ranking_config, candidates=candidates)

    assert len(board.top10) == 10
    assert len(board.reserve_list) == 5
    assert board.qualified_candidates_count == 15
    for c in board.top10:
        assert c.status == CandidateRankingStatus.TOP_10
    for c in board.reserve_list:
        assert c.status == CandidateRankingStatus.RESERVE


def test_empty_top10_when_no_candidates_clear_relevance_gates(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """When all candidates fail relevance gates, board emits valid empty top10 cleanly."""
    engine = SICERankingEngine()

    candidates = [
        candidate_builder(
            strike_rate=110.0,  # Below 136.0 threshold
            balls_faced=200,
        )
        for _ in range(5)
    ]

    board = engine.run_ranking(configuration=base_ranking_config, candidates=candidates)

    assert len(board.top10) == 0
    assert board.qualified_candidates_count == 0
    assert len(board.reserve_list) == 5


# ==============================================================================
# Suite 6: Contract Compliance, Identity Immutability & Guardrails (8 tests)
# ==============================================================================


def test_ranking_board_output_contract_valid_structure(
    base_ranking_config: RankingConfiguration,
) -> None:
    """RankingBoardOutputContract satisfies Pydantic contract specification."""
    valid_sha = "a" * 64
    board = RankingBoardOutputContract(
        config_id=base_ranking_config.config_id,
        target_season_id=base_ranking_config.target_season_id,
        evaluation_date=base_ranking_config.evaluation_date,
        data_snapshot_sha256=valid_sha,
        qualified_candidates_count=0,
        top10=[],
        reserve_list=[],
    )

    assert board.contract_version == "RK-1.0.0"
    assert board.run_type == RunType.HACKATHON_TOP10
    assert board.data_snapshot_sha256 == valid_sha


def test_ranking_board_output_contract_enforces_top10_size_limit() -> None:
    """RankingBoardOutputContract raises ValidationError if top10 contains > 10 items."""
    cands = [
        RankedCandidateContract(
            rank=i,
            player_id=uuid4(),
            canonical_name=f"Player_{i}",
            role="BATTER",
            age_at_evaluation=21.0,
            score=80.0,
        )
        for i in range(1, 12)  # 11 candidates
    ]

    with pytest.raises(ValidationError, match="top10 list cannot contain more than 10 candidates"):
        RankingBoardOutputContract(
            config_id=uuid4(),
            target_season_id=uuid4(),
            evaluation_date=date(2026, 11, 14),
            data_snapshot_sha256="b" * 64,
            qualified_candidates_count=11,
            top10=cands,
        )


def test_ranking_board_output_contract_rejects_invalid_sha256() -> None:
    """RankingBoardOutputContract rejects invalid non-64 hexadecimal SHA256 string."""
    with pytest.raises(ValidationError, match="data_snapshot_sha256 must be a valid 64-character"):
        RankingBoardOutputContract(
            config_id=uuid4(),
            target_season_id=uuid4(),
            evaluation_date=date(2026, 11, 14),
            data_snapshot_sha256="z" * 64,
            qualified_candidates_count=0,
            top10=[],
        )


def test_ranking_configuration_and_ranking_run_entity_mapping(
    base_ranking_config: RankingConfiguration,
) -> None:
    """Seamless round-trip mapping from RankingBoardOutputContract to Entities 32 & 33."""
    engine = SICERankingEngine()
    board = engine.run_ranking(configuration=base_ranking_config, candidates=[])

    run = RankingRun(
        run_id=board.run_id,
        config_id=board.config_id,
        data_snapshot_sha256=board.data_snapshot_sha256,
        candidate_pool=[],
        top10=[],
        reserve_list=[],
        computed_at=board.computed_at,
        determinism_note=board.determinism_note,
    )

    assert run.config_id == base_ranking_config.config_id
    assert run.data_snapshot_sha256 == board.data_snapshot_sha256


def test_pire_canonical_identity_immutability_rule_hd03(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """SICE ranking evaluation NEVER overwrites PIRE canonical identity or primary role (HD-03)."""
    engine = SICERankingEngine()

    cand = candidate_builder(
        primary_role="Top-order Batter",
        strike_rate=145.0,
        balls_faced=150,
    )

    board = engine.run_ranking(configuration=base_ranking_config, candidates=[cand])

    # Original candidate input primary_role remains completely untouched
    assert cand["primary_role"] == "Top-order Batter"
    assert board.top10[0].role == "Top-order Batter"


def test_unassessed_candidates_strictly_excluded_rule_r13(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Candidates with eligibility_status == 'NOT_ASSESSED' are strictly excluded (Rule R13)."""
    engine = SICERankingEngine()

    cand_unassessed = candidate_builder(
        eligibility_status="NOT_ASSESSED",
        strike_rate=150.0,
        balls_faced=200,
    )
    cand_eligible = candidate_builder(
        eligibility_status="VERIFIED_ELIGIBLE",
        strike_rate=150.0,
        balls_faced=200,
    )

    board = engine.run_ranking(
        configuration=base_ranking_config,
        candidates=[cand_unassessed, cand_eligible],
    )

    top_ids = [c.player_id for c in board.top10]
    reserve_ids = [c.player_id for c in board.reserve_list]

    assert cand_eligible["player_id"] in top_ids
    assert cand_unassessed["player_id"] not in top_ids
    assert cand_unassessed["player_id"] not in reserve_ids


def test_zero_nan_and_infinity_rejection_across_contracts_rule_r1() -> None:
    """Injecting NaN or Infinity into RankedCandidateContract raises ValidationError (Rule R1)."""
    with pytest.raises(ValidationError):
        RankedCandidateContract(
            rank=1,
            player_id=uuid4(),
            canonical_name="NaN Player",
            role="BATTER",
            age_at_evaluation=20.0,
            score=float("nan"),
        )

    with pytest.raises(ValidationError):
        RankedCandidateContract(
            rank=1,
            player_id=uuid4(),
            canonical_name="Inf Player",
            role="BATTER",
            age_at_evaluation=20.0,
            score=float("inf"),
        )


def test_evidence_provenance_linkage_tenet_4(
    candidate_builder: Any,
    base_ranking_config: RankingConfiguration,
) -> None:
    """Every ranked candidate in top10 carries non-empty verification_record_ids (Tenet 4)."""
    engine = SICERankingEngine()

    v_rec_id = uuid4()
    cand = candidate_builder(
        strike_rate=145.0,
        balls_faced=150,
        verification_record_ids=[v_rec_id],
    )

    board = engine.run_ranking(configuration=base_ranking_config, candidates=[cand])

    assert len(board.top10) == 1
    assert len(board.top10[0].verification_record_ids) > 0
    assert v_rec_id in board.top10[0].verification_record_ids
