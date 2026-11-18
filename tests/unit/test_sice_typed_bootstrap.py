"""Unit tests verifying contribution-level per_match_composite bootstrap integration and temporal filtering."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

import pytest
from src.contracts.cppae import (
    CPPAEOutput,
    MatchContributionProfile,
)
from src.contracts.ranking import RankingConfiguration
from src.sice.ranking_engine import (
    _SMAT_BATTER_SR_P75_FALLBACK,
    SICERankingEngine,
)


@pytest.fixture
def eval_date() -> date:
    return date(2025, 4, 1)


@pytest.fixture
def sample_candidates() -> list[dict]:
    pids = [UUID(f"30000000-0000-0000-0000-{i:012d}") for i in range(1, 15)]
    cands = []
    for i, pid in enumerate(pids):
        cands.append(
            {
                "player_id": pid,
                "canonical_name": f"Youngster_{i}",
                "date_of_birth": date(2003, 1, (i % 25) + 1),
                "primary_role": "Top-order Batter",
                "bowling_style": "None",
                "batting_average": 35.0 - i * 0.5,
                "strike_rate": 140.0 - i * 0.5,
                "balls_faced": 600,
                "verified_innings": 20,
                "dnb_innings": 1,
                "total_cross_format_innings": 25,
            }
        )
    return cands


def test_bootstrap_with_typed_cppae_observations(
    sample_candidates: list[dict],
    eval_date: date,
) -> None:
    """Verify that contribution-level per_match_composite dictionaries are processed without error."""
    engine = SICERankingEngine(seed=42)
    profiles: dict[UUID, CPPAEOutput] = {}

    for cand in sample_candidates:
        pid = cand["player_id"]
        per_match = {
            f"match_{pid}_{m}": {
                "match_date": date(2025, 3, m),
                "format_tag": "T20",
                "m02": 30.0 + (m % 10),
                "m07": 35.0 + (m % 10),
                "runs_scored": 40,
                "balls_faced": 28,
            }
            for m in range(1, 6)
        }
        profiles[pid] = CPPAEOutput(
            player_id=pid,
            canonical_name=cand["canonical_name"],
            match_contribution=MatchContributionProfile(
                per_match_composite=per_match,
            ),
        )

    res = engine.run_match_level_bootstrap_resampling(
        candidates=sample_candidates,
        cppae_profiles=profiles,
        iterations=100,
        seed=42,
        evaluation_date=eval_date,
    )

    for pid in [c["player_id"] for c in sample_candidates]:
        assert pid in res
        r = res[pid]
        assert r["score_ci_lower"] is not None
        assert r["score_ci_upper"] is not None
        assert r["score_ci_lower"] <= r["score_ci_upper"]
        assert 0.0 <= r["top10_stability_pct"] <= 100.0


def test_bootstrap_temporal_filtering(
    sample_candidates: list[dict],
    eval_date: date,
) -> None:
    """Verify matches after evaluation_date are filtered out of the bootstrap."""
    engine = SICERankingEngine(seed=42)
    pid = sample_candidates[0]["player_id"]

    # 2 matches before eval_date (score=20), 2 matches after eval_date (score=99)
    per_match = {
        "past_1": {
            "match_date": date(2025, 2, 1),
            "m07": 20.0,
        },
        "past_2": {
            "match_date": date(2025, 3, 1),
            "m07": 20.0,
        },
        "future_1": {
            "match_date": date(2025, 5, 1),  # after eval_date
            "m07": 99.0,
        },
        "future_2": {
            "match_date": date(2025, 6, 1),  # after eval_date
            "m07": 99.0,
        },
    }

    profiles = {
        pid: CPPAEOutput(
            player_id=pid,
            canonical_name="Test",
            match_contribution=MatchContributionProfile(
                per_match_composite=per_match,
            ),
        )
    }

    res = engine.run_match_level_bootstrap_resampling(
        candidates=[sample_candidates[0]],
        cppae_profiles=profiles,
        iterations=50,
        seed=42,
        evaluation_date=eval_date,
    )

    r = res[pid]
    # If future matches were excluded, score_ci_upper should be around 20.0, not near 99.0
    assert r["score_ci_upper"] <= 30.0


def test_bootstrap_iso_string_and_datetime_filtering(
    sample_candidates: list[dict],
    eval_date: date,
) -> None:
    """Verify ISO strings (with T and Z) and datetime objects are parsed robustly."""
    engine = SICERankingEngine(seed=42)
    pid = sample_candidates[0]["player_id"]

    per_match = {
        "past_iso_tz": {
            "match_date": "2025-02-01T14:30:00Z",
            "m07": 25.0,
        },
        "past_plain_str": {
            "match_date": "2025-03-01",
            "m07": 25.0,
        },
        "past_datetime_obj": {
            "match_date": datetime(2025, 3, 15, 10, 0),
            "m07": 25.0,
        },
        "future_iso_tz": {
            "match_date": "2025-05-01T14:30:00Z",  # after eval_date
            "m07": 99.0,
        },
    }

    profiles = {
        pid: CPPAEOutput(
            player_id=pid,
            canonical_name="TestIso",
            match_contribution=MatchContributionProfile(
                per_match_composite=per_match,
            ),
        )
    }

    res = engine.run_match_level_bootstrap_resampling(
        candidates=[sample_candidates[0]],
        cppae_profiles=profiles,
        iterations=50,
        seed=42,
        evaluation_date=eval_date,
    )

    r = res[pid]
    assert r["score_ci_upper"] <= 35.0
    assert r["score_ci_lower"] >= 20.0


def test_ranking_snapshot_sha256_bit_for_bit_determinism(
    sample_candidates: list[dict],
    eval_date: date,
) -> None:
    """Verify data_snapshot_sha256 and candidate verification IDs are bit-for-bit deterministic."""
    engine = SICERankingEngine(seed=42)
    config = RankingConfiguration(
        config_version="RK-1.0.0",
        target_season_id=UUID("00000000-0000-0000-0000-000000002027"),
        policy_id=UUID("00000000-0000-0000-0000-000000000001"),
        evaluation_date=eval_date,
        ordering_json={"keys": ["age_asc", "consistency_desc", "b05_average_desc_nulls_last"]},
        tiebreakers_json={
            "tiebreakers": ["b06_strike_rate_desc", "b04_balls_faced_desc", "uuid_asc"]
        },
        seed=42,
    )

    board1 = engine.run_ranking(configuration=config, candidates=sample_candidates)
    board2 = engine.run_ranking(configuration=config, candidates=sample_candidates)

    # Identical SHA-256 snapshot
    assert board1.data_snapshot_sha256 == board2.data_snapshot_sha256
    assert len(board1.data_snapshot_sha256) == 64

    # Identical deterministic verification record IDs on Top 10
    v_ids_1 = [c.verification_record_ids for c in board1.top10]
    v_ids_2 = [c.verification_record_ids for c in board2.top10]
    assert v_ids_1 == v_ids_2


def test_cohort_percentiles_computed_from_pool() -> None:
    """Verify _compute_cohort_percentiles computes percentiles from pool or falls back."""
    engine = SICERankingEngine()

    # Empty pool falls back to SMAT constants
    empty_result = engine._compute_cohort_percentiles([])
    assert empty_result["_reference_source"] == "SMAT_2022_2024_FALLBACK"
    assert empty_result["batter_sr_p75"] == _SMAT_BATTER_SR_P75_FALLBACK

    # Non-empty pool computes from input data
    pool = [
        {"strike_rate": 110.0, "primary_role": "Top-order Batter"},
        {"strike_rate": 130.0, "primary_role": "Top-order Batter"},
        {"strike_rate": 150.0, "primary_role": "Top-order Batter"},
        {"strike_rate": 170.0, "primary_role": "Top-order Batter"},
    ]
    computed = engine._compute_cohort_percentiles(pool)
    assert "_reference_source" not in computed
    assert computed["batter_sr_p75"] == 170.0
