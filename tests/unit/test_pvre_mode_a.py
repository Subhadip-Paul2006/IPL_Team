"""Unit tests for PVRE Mode A: Existing RR Player Replacement Intelligence.

Tests Module A1 (RR Historical Performance), Module A2 (Recent Global Form),
and Module A3 (Replaceability Evidence Assessment) in strict compliance with
TRD §9.3, PRD FR-PV2..FR-PV4, DATA_DICTIONARY §9, §10, and AI_INSTRUCTIONS R1..R22.
"""

from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

import pytest
from src.contracts.pvre import (
    PVREOutputContract,
    PVREReviewStatus,
    ReplaceabilitySignal,
    ResearchMode,
    RouteStatus,
)
from src.pvre.mode_a_incumbent import (
    NOT_COMPUTABLE_TOKEN,
    GapCode,
    ModeAExecutionResult,
    ModeAIncumbentEngine,
    ModuleA1RRHistory,
    ModuleA2GlobalPerformance,
    ModuleA3ReplaceabilityAssessor,
    calculate_time_decay_weight,
)

from tests.fixtures.pvre_contract_fixtures import (
    build_mode_a_incumbent_request,
    build_pvre_request,
)

# Deterministic fixtures
SAMPLE_PLAYER_ID_SANJU = UUID("10000000-0000-0000-0000-000000000001")
SAMPLE_PLAYER_ID_ALUMNUS = UUID("10000000-0000-0000-0000-000000000002")
EVALUATION_DATE = date(2025, 3, 1)


# ==============================================================================
# Helper Fixtures & Builders for Match Data
# ==============================================================================


def make_rr_match(
    season: int,
    match_date: date,
    runs: int = 35,
    balls: int = 24,
    dismissed: bool = True,
    fours: int = 3,
    sixes: int = 1,
    dots: int = 6,
    legal_balls: int = 0,
    runs_conceded: int = 0,
    wickets: int = 0,
    catches: int = 1,
    is_super_over: bool = False,
    granularity: str = "BALL_BY_BALL",
    competition_name: str = "Indian Premier League",
) -> dict:
    """Build a mock match record for Rajasthan Royals."""
    return {
        "match_id": f"RR-{season}-{match_date.isoformat()}",
        "match_date": match_date,
        "season": season,
        "team_code": "RR",
        "team_name": "Rajasthan Royals",
        "competition_name": competition_name,
        "format_tag": "T20",
        "batted": balls > 0 or runs > 0,
        "runs": runs,
        "balls_faced": balls,
        "dismissed": dismissed,
        "fours": fours,
        "sixes": sixes,
        "dot_balls": dots,
        "bowled": legal_balls > 0,
        "legal_balls": legal_balls,
        "runs_conceded": runs_conceded,
        "wickets": wickets,
        "dot_balls_bowled": 0,
        "catches": catches,
        "run_outs": 0,
        "stumpings": 0,
        "is_super_over": is_super_over,
        "granularity": granularity,
        "powerplay_runs": int(runs * 0.4),
        "powerplay_balls": int(balls * 0.4),
        "middle_runs": int(runs * 0.4),
        "middle_balls": int(balls * 0.4),
        "death_runs": int(runs * 0.2),
        "death_balls": int(balls * 0.2),
        "powerplay_legal_balls": int(legal_balls * 0.5),
        "powerplay_runs_conceded": int(runs_conceded * 0.5),
        "powerplay_wickets": wickets,
        "middle_legal_balls": int(legal_balls * 0.5),
        "middle_runs_conceded": int(runs_conceded * 0.5),
        "middle_wickets": 0,
        "death_legal_balls": 0,
        "death_runs_conceded": 0,
        "death_wickets": 0,
    }


# ==============================================================================
# 1. Module A1 Tests: RR Historical Performance & Squad Separation
# ==============================================================================


def test_module_a1_verified_incumbent_profile() -> None:
    """Test Module A1 historical profile for a verified RR incumbent (e.g. Sanju Samson)."""
    squad_records = [
        {"season": "2021", "contract_type": "Retained", "appearances": 14, "tactical_role": "TOP_ORDER_BATTER_WK"},
        {"season": "2022", "contract_type": "Retained", "appearances": 17, "tactical_role": "TOP_ORDER_BATTER_WK"},
        {"season": "2023", "contract_type": "Retained", "appearances": 14, "tactical_role": "TOP_ORDER_BATTER_WK"},
        {"season": "2024", "contract_type": "Retained", "appearances": 15, "tactical_role": "TOP_ORDER_BATTER_WK"},
    ]

    match_records = [
        make_rr_match(2021, date(2021, 4, 12), runs=119, balls=63, fours=12, sixes=7, dots=15),
        make_rr_match(2022, date(2022, 4, 10), runs=48, balls=30, fours=4, sixes=2, dots=8),
        make_rr_match(2023, date(2023, 4, 15), runs=60, balls=32, fours=3, sixes=4, dots=7),
        make_rr_match(2024, date(2024, 4, 20), runs=82, balls=50, fours=7, sixes=4, dots=10),
    ]

    profile = ModuleA1RRHistory.analyze(
        player_id=SAMPLE_PLAYER_ID_SANJU,
        canonical_name="Sanju Samson",
        squad_records=squad_records,
        match_records=match_records,
        provenance_ids=[101, 102],
    )

    assert profile.canonical_name == "Sanju Samson"
    assert profile.player_id == SAMPLE_PLAYER_ID_SANJU
    assert profile.total_seasons == 4
    assert profile.seasons_active == ["2021", "2022", "2023", "2024"]
    assert profile.squad_only_seasons == []
    assert profile.suspension_seasons_excluded == []
    assert profile.total_matches == 60  # sum of appearances (14 + 17 + 14 + 15)
    assert profile.total_runs == 119 + 48 + 60 + 82
    assert profile.total_balls_faced == 63 + 30 + 32 + 50
    assert profile.strike_rate is not None
    assert profile.strike_rate == pytest.approx(100.0 * profile.total_runs / profile.total_balls_faced, 0.01)
    assert profile.batting_average is not None
    assert profile.boundary_pct is not None
    assert profile.dot_ball_pct is not None
    assert profile.fielding_summary["catches"] == 4
    assert len(profile.role_evolution) == 4
    assert profile.role_evolution[0]["role"] == "TOP_ORDER_BATTER_WK"
    assert profile.provenance_ids == [101, 102]


def test_module_a1_squad_only_alumnus_zero_stats_rule() -> None:
    """CRITICAL RULE: Squad-only alumni with 0 appearances must be credited with STRICTLY ZERO stats.

    Compliance: TRD §9.3.1, PRD FR-PV2, AI_INSTRUCTIONS R19, AC-25.
    """
    squad_records = [
        {"season": "2020", "contract_type": "Squad Inclusion", "appearances": 0, "tactical_role": "MIDDLE_ORDER_BATTER"},
        {"season": "2021", "contract_type": "Squad Inclusion", "appearances": 0, "tactical_role": "MIDDLE_ORDER_BATTER"},
    ]

    # No match appearances
    match_records: list[dict] = []

    profile = ModuleA1RRHistory.analyze(
        player_id=SAMPLE_PLAYER_ID_ALUMNUS,
        canonical_name="Reserve Prospect",
        squad_records=squad_records,
        match_records=match_records,
    )

    assert profile.canonical_name == "Reserve Prospect"
    assert profile.total_matches == 0
    assert profile.seasons_active == []
    assert profile.squad_only_seasons == ["2020", "2021"]
    assert profile.total_seasons == 2

    # STRICT ZERO BATTING & BOWLING STATS
    assert profile.total_runs == 0
    assert profile.total_balls_faced == 0
    assert profile.total_legal_balls == 0
    assert profile.total_runs_conceded == 0
    assert profile.total_wickets == 0

    # Rate metrics must be None (NULL per Rule R1, not 0.0)
    assert profile.strike_rate is None
    assert profile.batting_average is None
    assert profile.boundary_pct is None
    assert profile.dot_ball_pct is None
    assert profile.economy_rate is None
    assert profile.bowling_average is None
    assert profile.bowling_strike_rate is None

    # Inspect season splits
    for s_split in profile.season_splits:
        assert s_split["is_squad_only"] is True
        assert s_split["appearances"] == 0
        assert s_split["batting"]["runs"] == 0
        assert s_split["batting"]["balls_faced"] == 0
        assert s_split["batting"]["strike_rate"] is None
        assert s_split["bowling"]["legal_balls"] == 0
        assert s_split["bowling"]["wickets"] == 0
        assert s_split["bowling"]["economy_rate"] is None


def test_module_a1_suspension_seasons_handling() -> None:
    """Test that RR 2016 and 2017 franchise suspension seasons are strictly excluded."""
    squad_records = [
        {"season": "2015", "contract_type": "Retained", "appearances": 14, "tactical_role": "BATTER"},
        {"season": "2016", "contract_type": "Retained", "appearances": 0, "tactical_role": "BATTER"},
        {"season": "2017", "contract_type": "Retained", "appearances": 0, "tactical_role": "BATTER"},
        {"season": "2018", "contract_type": "Auction Buy", "appearances": 15, "tactical_role": "BATTER"},
    ]

    # Include an invalid 2016 record to ensure it is quarantined/excluded
    match_records = [
        make_rr_match(2015, date(2015, 5, 1), runs=50, balls=35),
        make_rr_match(2016, date(2016, 5, 1), runs=99, balls=50),  # Should be excluded
        make_rr_match(2018, date(2018, 5, 1), runs=60, balls=40),
    ]

    profile = ModuleA1RRHistory.analyze(
        player_id=SAMPLE_PLAYER_ID_SANJU,
        canonical_name="Sanju Samson",
        squad_records=squad_records,
        match_records=match_records,
    )

    assert "2016" in profile.suspension_seasons_excluded
    assert "2017" in profile.suspension_seasons_excluded
    assert "2016" not in profile.seasons_active
    assert "2017" not in profile.seasons_active
    assert profile.seasons_active == ["2015", "2018"]

    # 2016 runs (99) must NOT be counted in total_runs
    assert profile.total_runs == 50 + 60
    assert profile.total_balls_faced == 35 + 40


def test_module_a1_future_season_2027_handling() -> None:
    """Test that future unpromulgated season 2027 is excluded from historical career stats."""
    squad_records = [
        {"season": "2024", "contract_type": "Retained", "appearances": 15, "tactical_role": "BATTER"},
        {"season": "2027", "contract_type": "Draft", "appearances": 0, "tactical_role": "BATTER"},
    ]
    match_records = [make_rr_match(2024, date(2024, 4, 1), runs=45, balls=30)]

    profile = ModuleA1RRHistory.analyze(
        player_id=SAMPLE_PLAYER_ID_SANJU,
        canonical_name="Sanju Samson",
        squad_records=squad_records,
        match_records=match_records,
    )

    assert "2027" not in profile.seasons_active
    assert "2027" not in profile.squad_only_seasons
    assert profile.seasons_active == ["2024"]


# ==============================================================================
# 2. Module A2 Tests: Recent Global Form & Time-Decay Math
# ==============================================================================


def test_exponential_time_decay_exact_values() -> None:
    """Test exponential time-decay weighting function matches formula in DATA_DICTIONARY §9.1."""
    eval_date = date(2025, 3, 1)

    # 1. Match on evaluation date (delta = 0) -> weight = 1.0
    w0 = calculate_time_decay_weight(eval_date, eval_date, window_years=3, t_half_days=365.0)
    assert w0 == pytest.approx(1.0, 1e-6)

    # 2. Match 365 days before evaluation date (1 half-life) -> weight = 0.5
    d365 = eval_date - timedelta(days=365)
    w1 = calculate_time_decay_weight(d365, eval_date, window_years=3, t_half_days=365.0)
    assert w1 == pytest.approx(0.5, 1e-5)

    # 3. Match 730 days before evaluation date (2 half-lives) -> weight = 0.25
    d730 = eval_date - timedelta(days=730)
    w2 = calculate_time_decay_weight(d730, eval_date, window_years=3, t_half_days=365.0)
    assert w2 == pytest.approx(0.25, 1e-5)

    # 4. Match 1095 days before evaluation date (3 half-lives) -> weight = 0.125
    d1095 = eval_date - timedelta(days=1095)
    w3 = calculate_time_decay_weight(d1095, eval_date, window_years=3, t_half_days=365.0)
    assert w3 == pytest.approx(0.125, 1e-5)

    # 5. Match after evaluation date -> weight = 0.0 (strictly excluded)
    future_date = eval_date + timedelta(days=5)
    w_future = calculate_time_decay_weight(future_date, eval_date, window_years=3)
    assert w_future == 0.0

    # 6. Match older than window (e.g. 4 years ago for a 3-year window) -> weight = 0.0
    old_date = eval_date - timedelta(days=1500)
    w_old = calculate_time_decay_weight(old_date, eval_date, window_years=3)
    assert w_old == 0.0


def test_module_a2_window_bounds_exclusion() -> None:
    """Test matches outside window bounds (too old or in future) are excluded from R01–R06."""
    eval_date = date(2025, 3, 1)

    matches = [
        # Inside window (2024, 2023)
        make_rr_match(2024, date(2024, 5, 1), runs=60, balls=40),
        make_rr_match(2023, date(2023, 5, 1), runs=40, balls=30),
        # Strictly in future (after eval_date) -> MUST BE EXCLUDED
        make_rr_match(2025, date(2025, 4, 1), runs=100, balls=50),
        # Outside window (older than 3 years) -> MUST BE EXCLUDED
        make_rr_match(2020, date(2020, 5, 1), runs=80, balls=40),
    ]

    profile = ModuleA2GlobalPerformance.analyze(
        evaluation_date=eval_date,
        window_years=3,
        match_records=matches,
    )

    # Only 2 matches inside window
    assert profile.sample_indicators["matches"] == 2
    assert profile.sample_indicators["runs_scored"] == 60 + 40
    assert profile.sample_indicators["balls_faced"] == 40 + 30


def test_module_a2_format_aware_economy_the_hundred() -> None:
    """Test format-aware economy rate (R02) respects balls_per_over = 5 for The Hundred."""
    eval_date = date(2025, 3, 1)

    # The Hundred match: 20 legal balls bowled, 25 runs conceded, bpo = 5
    hundred_match = {
        "match_id": "HND-01",
        "match_date": eval_date - timedelta(days=10),
        "competition_name": "The Hundred Men",
        "format_tag": "The Hundred",
        "balls_per_over": 5,
        "bowled": True,
        "legal_balls": 20,
        "runs_conceded": 25,
        "wickets": 2,
    }

    # Standard T20 match: 24 legal balls bowled, 32 runs conceded, bpo = 6
    t20_match = {
        "match_id": "IPL-01",
        "match_date": eval_date - timedelta(days=10),
        "competition_name": "Indian Premier League",
        "format_tag": "T20",
        "balls_per_over": 6,
        "bowled": True,
        "legal_balls": 24,
        "runs_conceded": 32,
        "wickets": 1,
    }

    profile_hundred_only = ModuleA2GlobalPerformance.analyze(
        evaluation_date=eval_date,
        window_years=3,
        match_records=[hundred_match],
    )

    # For The Hundred: Economy = (5 * 25) / 20 = 6.25 runs per 5 balls
    assert profile_hundred_only.weighted_economy == pytest.approx(6.25, 0.01)

    profile_t20_only = ModuleA2GlobalPerformance.analyze(
        evaluation_date=eval_date,
        window_years=3,
        match_records=[t20_match],
    )

    # For T20: Economy = (6 * 32) / 24 = 8.00 runs per 6 balls
    assert profile_t20_only.weighted_economy == pytest.approx(8.00, 0.01)


def test_module_a2_super_over_strict_isolation() -> None:
    """Test that Super Over innings/matches are strictly excluded from career & window metrics."""
    eval_date = date(2025, 3, 1)

    regular_match = make_rr_match(2024, date(2024, 4, 1), runs=50, balls=30, fours=4, sixes=2)
    # Super over match (tied match deciding over, 1 over)
    super_over_match = make_rr_match(
        2024,
        date(2024, 4, 1),
        runs=18,
        balls=6,
        fours=1,
        sixes=2,
        is_super_over=True,
    )

    profile = ModuleA2GlobalPerformance.analyze(
        evaluation_date=eval_date,
        window_years=3,
        match_records=[regular_match, super_over_match],
    )

    assert profile.super_overs_excluded_count == 1
    assert profile.sample_indicators["matches"] == 1
    assert profile.sample_indicators["runs_scored"] == 50
    assert profile.sample_indicators["balls_faced"] == 30


def test_module_a2_dot_ball_not_computable_for_scorecard_only() -> None:
    """Test dot ball % (R04) returns NOT_COMPUTABLE for scorecard-only data without ball-by-ball dots."""
    eval_date = date(2025, 3, 1)

    scorecard_match = {
        "match_id": "RANJI-01",
        "match_date": eval_date - timedelta(days=50),
        "competition_name": "Ranji Trophy",
        "format_tag": "First-Class",
        "granularity": "SCORECARD_ONLY",
        "batted": True,
        "runs": 85,
        "balls_faced": 140,
        "fours": 10,
        "sixes": 0,
        "dot_balls": None,  # Scorecard-only lacks delivery-level dots
    }

    profile = ModuleA2GlobalPerformance.analyze(
        evaluation_date=eval_date,
        window_years=3,
        match_records=[scorecard_match],
    )

    assert profile.dot_ball_pct == NOT_COMPUTABLE_TOKEN


def test_module_a2_career_gap_taxonomy_all_5_codes() -> None:
    """Test Career Gap & Absence Taxonomy (R05) accurately classifies all 5 gap codes."""
    eval_date = date(2025, 3, 1)

    injuries = [
        {
            "injury_id": "INJ-01",
            "start_date": date(2024, 3, 1),
            "end_date": date(2024, 4, 15),
            "verified": True,
            "injury_type": "Hamstring Tear",
        }
    ]

    absences = [
        # 1. Verified Injury
        {"match_id": "M1", "match_date": date(2024, 3, 20), "competition_name": "IPL", "reason_hint": "Unavailable"},
        # 2. National Duty
        {"match_id": "M2", "match_date": date(2024, 7, 10), "competition_name": "IPL", "reason_hint": "National Duty with India"},
        # 3. Domestic Clash
        {"match_id": "M3", "match_date": date(2024, 9, 5), "competition_name": "CPL", "reason_hint": "Tournament Clash with Duleep Trophy"},
        # 4. Not Selected / Bench
        {"match_id": "M4", "match_date": date(2024, 10, 1), "competition_name": "SMAT", "reason_hint": "Bench / Squad Only"},
        # 5. Unknown / Unexplained
        {"match_id": "M5", "match_date": date(2024, 11, 1), "competition_name": "SMAT", "reason_hint": ""},
    ]

    profile = ModuleA2GlobalPerformance.analyze(
        evaluation_date=eval_date,
        window_years=3,
        match_records=[],
        injury_records=injuries,
        absence_records=absences,
    )

    gap_codes = [g["gap_code"] for g in profile.gap_records]
    assert GapCode.GAP_VERIFIED_INJURY.value in gap_codes
    assert GapCode.GAP_NATIONAL_DUTY.value in gap_codes
    assert GapCode.GAP_DOMESTIC_CLASH.value in gap_codes
    assert GapCode.GAP_NOT_SELECTED.value in gap_codes
    assert GapCode.GAP_UNKNOWN_UNEXPLAINED.value in gap_codes


def test_module_a2_zero_denominators_return_none() -> None:
    """Test strict Rule R1: zero denominators return None (NULL), never 0.0."""
    eval_date = date(2025, 3, 1)

    profile = ModuleA2GlobalPerformance.analyze(
        evaluation_date=eval_date,
        window_years=3,
        match_records=[],
    )

    assert profile.weighted_strike_rate is None
    assert profile.weighted_economy is None
    assert profile.boundary_pct is None
    assert profile.dot_ball_pct is None
    assert profile.sample_indicators["balls_faced"] == 0
    assert profile.sample_indicators["legal_balls_bowled"] == 0
    assert profile.sample_indicators["insufficient_sample_flag"] is True


# ==============================================================================
# 3. Module A3 Tests: Replaceability Assessment Signals & Non-Decision Rule
# ==============================================================================


def test_module_a3_retain_signal_for_elite_incumbent() -> None:
    """Test Module A3 evaluates elite performer as RETAIN_SIGNAL."""
    rr_profile = {
        "canonical_name": "Sanju Samson",
        "total_matches": 60,
        "strike_rate": 142.5,
        "economy_rate": None,
    }
    global_profile = {
        "weighted_strike_rate": 146.0,  # +10 vs 136 benchmark
        "weighted_economy": None,
        "boundary_pct": 21.0,
        "sample_indicators": {"balls_faced": 550, "legal_balls_bowled": 0},
    }

    assessment = ModuleA3ReplaceabilityAssessor.assess(
        rr_profile=rr_profile,
        global_profile=global_profile,
        primary_role="TOP_ORDER_BATTER_WK",
        age_at_evaluation=30.0,  # Prime age
    )

    assert assessment.signal == ReplaceabilitySignal.RETAIN_SIGNAL
    assert "clear evidence against replacement" in assessment.signal_rationale.lower()
    assert assessment.insufficient_sample_flag is False
    assert assessment.review_required_flag is False
    assert assessment.forward_to_sice is True


def test_module_a3_sample_size_guardrail_insufficient_evidence() -> None:
    """Test sample size guardrail (<20 balls faced or <30 balls bowled) emits INSUFFICIENT_EVIDENCE."""
    rr_profile = {"canonical_name": "Sample Prospect", "total_matches": 5, "strike_rate": 120.0}
    # Only 15 balls faced in window (< 20 threshold)
    global_profile = {
        "weighted_strike_rate": 150.0,
        "weighted_economy": None,
        "boundary_pct": 20.0,
        "sample_indicators": {"balls_faced": 15, "legal_balls_bowled": 0},
    }

    assessment = ModuleA3ReplaceabilityAssessor.assess(
        rr_profile=rr_profile,
        global_profile=global_profile,
        primary_role="TOP_ORDER_BATTER",
        age_at_evaluation=24.0,
    )

    assert assessment.signal == ReplaceabilitySignal.INSUFFICIENT_EVIDENCE
    assert assessment.insufficient_sample_flag is True
    assert "sample size below evaluation threshold" in assessment.signal_rationale.lower()


def test_module_a3_potentially_replaceable_signal() -> None:
    """Test aging incumbent with severely declining strike rate evaluates as POTENTIALLY_REPLACEABLE."""
    rr_profile = {
        "canonical_name": "Veteran Batter",
        "total_matches": 30,
        "strike_rate": 122.0,
    }
    global_profile = {
        "weighted_strike_rate": 118.0,  # -18 vs 136 benchmark
        "weighted_economy": None,
        "boundary_pct": 12.0,
        "sample_indicators": {"balls_faced": 180, "legal_balls_bowled": 0},
    }

    assessment = ModuleA3ReplaceabilityAssessor.assess(
        rr_profile=rr_profile,
        global_profile=global_profile,
        primary_role="TOP_ORDER_BATTER",
        age_at_evaluation=36.5,  # Advanced age
    )

    assert assessment.signal == ReplaceabilitySignal.POTENTIALLY_REPLACEABLE
    assert "declining multi-season performance" in assessment.signal_rationale.lower()
    assert assessment.insufficient_sample_flag is False


def test_module_a3_monitor_signal_for_moderate_form() -> None:
    """Test moderate performer evaluates as MONITOR_SIGNAL."""
    rr_profile = {
        "canonical_name": "Steady Contributor",
        "total_matches": 25,
        "strike_rate": 134.0,
    }
    global_profile = {
        "weighted_strike_rate": 133.0,  # Near benchmark 136
        "weighted_economy": None,
        "boundary_pct": 16.5,
        "sample_indicators": {"balls_faced": 220, "legal_balls_bowled": 0},
    }

    assessment = ModuleA3ReplaceabilityAssessor.assess(
        rr_profile=rr_profile,
        global_profile=global_profile,
        primary_role="TOP_ORDER_BATTER",
        age_at_evaluation=29.0,
    )

    assert assessment.signal == ReplaceabilitySignal.MONITOR_SIGNAL
    assert "continued observation" in assessment.signal_rationale.lower()


def test_module_a3_review_required_signal() -> None:
    """Test that safety review reasons force ReplaceabilitySignal.REVIEW_REQUIRED."""
    rr_profile = {"canonical_name": "Contested Player", "total_matches": 10}
    global_profile = {
        "weighted_strike_rate": 140.0,
        "sample_indicators": {"balls_faced": 100, "legal_balls_bowled": 0},
    }

    assessment = ModuleA3ReplaceabilityAssessor.assess(
        rr_profile=rr_profile,
        global_profile=global_profile,
        primary_role="TOP_ORDER_BATTER",
        age_at_evaluation=25.0,
        review_required_reasons=["CONFLICT_DOB_RECORD", "UNRESOLVED_MEMBERSHIP_CLAIM"],
    )

    assert assessment.signal == ReplaceabilitySignal.REVIEW_REQUIRED
    assert assessment.review_required_flag is True
    assert "safety gateway triggered" in assessment.signal_rationale.lower()


def test_module_a3_non_decision_rule_no_replacement_probabilities() -> None:
    """CRITICAL RULE: PVRE produces analytical signals only.

    Strictly prohibited from generating scalar replacement probabilities or release decisions.
    Compliance: TRD §9.3.3, PRD FR-PV4, AI_INSTRUCTIONS R20.
    """
    rr_profile = {"canonical_name": "Test Player", "total_matches": 20, "strike_rate": 135.0}
    global_profile = {
        "weighted_strike_rate": 140.0,
        "sample_indicators": {"balls_faced": 100, "legal_balls_bowled": 0},
    }

    assessment = ModuleA3ReplaceabilityAssessor.assess(
        rr_profile=rr_profile,
        global_profile=global_profile,
        primary_role="TOP_ORDER_BATTER",
        age_at_evaluation=28.0,
    )

    assessment_dict = assessment.model_dump()

    # MUST NOT contain scalar probability or recruitment decision keys
    forbidden_keys = {
        "replacement_probability",
        "probability_of_replacement",
        "replaceability_score",
        "release_decision",
        "retention_decision",
        "auction_price_estimate",
    }

    for key in forbidden_keys:
        assert key not in assessment_dict, f"Forbidden key '{key}' found in ReplaceabilityAssessment!"


# ==============================================================================
# 4. End-to-End Mode A Engine & Output Contract Compilation
# ==============================================================================


def test_mode_a_engine_e2e_full_pipeline() -> None:
    """Test full Mode A pipeline execution and compilation of PVREOutputContract (26 fields)."""
    request = build_mode_a_incumbent_request(
        evaluation_date=EVALUATION_DATE,
        research_window_years=3,
    )

    squad_records = [
        {"season": "2022", "contract_type": "Retained", "appearances": 17, "tactical_role": "TOP_ORDER_BATTER_WK"},
        {"season": "2023", "contract_type": "Retained", "appearances": 14, "tactical_role": "TOP_ORDER_BATTER_WK"},
        {"season": "2024", "contract_type": "Retained", "appearances": 15, "tactical_role": "TOP_ORDER_BATTER_WK"},
    ]

    rr_matches = [
        make_rr_match(2022, date(2022, 4, 15), runs=55, balls=35, fours=5, sixes=2, dots=10),
        make_rr_match(2023, date(2023, 4, 20), runs=70, balls=42, fours=6, sixes=3, dots=9),
        make_rr_match(2024, date(2024, 4, 25), runs=85, balls=50, fours=8, sixes=4, dots=12),
    ]

    global_matches = [
        # SMAT match outside RR
        {
            "match_id": "SMAT-01",
            "match_date": date(2023, 10, 20),
            "competition_name": "Syed Mushtaq Ali Trophy",
            "format_tag": "T20",
            "batted": True,
            "runs": 45,
            "balls_faced": 28,
            "fours": 4,
            "sixes": 2,
            "dot_balls": 6,
        }
    ]

    result: ModeAExecutionResult = ModeAIncumbentEngine.execute(
        request=request,
        squad_records=squad_records,
        rr_match_records=rr_matches,
        global_match_records=global_matches,
        primary_role="TOP_ORDER_BATTER_WK",
        date_of_birth=date(1994, 11, 11),
        source_record_ids=[UUID("11111111-2222-3333-4444-555555555555")],
        verification_record_ids=[UUID("66666666-7777-8888-9999-000000000000")],
    )

    assert result.review_status == PVREReviewStatus.CLEAR.value
    assert result.replaceability_assessment.signal == ReplaceabilitySignal.RETAIN_SIGNAL

    # Compile authoritative 26-field PVREOutputContract
    output: PVREOutputContract = result.to_pvre_output(request)

    assert output.contract_version == "PVRE-2.2.0"
    assert output.canonical_name == "Sanju Samson"
    assert output.research_mode == ResearchMode.MODE_A.value
    assert output.route_status == RouteStatus.ROUTED_RR_INCUMBENT.value
    assert output.evaluation_date == EVALUATION_DATE
    assert output.rr_relationship_state == "CURRENT_RR"

    # Module outputs populated
    assert output.rr_historical_profile is not None
    assert output.recent_global_performance is not None
    assert output.replaceability_assessment is not None
    assert output.complete_career_profile is None  # None in Mode A

    # Research windows
    assert output.research_window_end == EVALUATION_DATE
    assert output.research_window_start < output.research_window_end

    # Provenance
    assert len(output.source_record_ids) >= 1
    assert len(output.verification_record_ids) >= 1
    assert output.review_status == "CLEAR"

    # Verify JSON serializability
    json_str = output.model_dump_json()
    assert "Sanju Samson" in json_str
    assert "RETAIN_SIGNAL" in json_str


def test_mode_a_engine_squad_only_alumnus_e2e() -> None:
    """Test full Mode A pipeline for squad-only alumnus producing 0 stats."""
    request = build_pvre_request(
        player_query="Squad Reserve",
        player_id=SAMPLE_PLAYER_ID_ALUMNUS,
        canonical_name="Squad Reserve",
        rr_relationship_state="HISTORICAL_RR_SQUAD_ONLY",
        rr_current_state="NOT_CURRENT",
        evaluation_date=EVALUATION_DATE,
    )

    squad_records = [
        {"season": "2021", "contract_type": "Squad Inclusion", "appearances": 0, "tactical_role": "BOWLER"},
    ]

    result: ModeAExecutionResult = ModeAIncumbentEngine.execute(
        request=request,
        squad_records=squad_records,
        rr_match_records=[],
        global_match_records=[],
        primary_role="PACE_BOWLER",
    )

    output = result.to_pvre_output(request)

    assert output.rr_historical_profile is not None
    assert output.replaceability_assessment is not None
    assert output.rr_historical_profile["total_matches"] == 0
    assert output.rr_historical_profile["total_runs"] == 0
    assert output.rr_historical_profile["total_wickets"] == 0
    assert output.rr_historical_profile["squad_only_seasons"] == ["2021"]
    assert output.replaceability_assessment["signal"] == ReplaceabilitySignal.INSUFFICIENT_EVIDENCE.value


# ==============================================================================
# 5. Enhanced Boundary & Combinatorial Edge Cases
# ==============================================================================


def test_boundary_exact_min_sample_threshold_batter() -> None:
    """Test exact boundary condition: 19 balls faced (insufficient) vs 20 balls faced (sufficient)."""
    rr_profile = {"canonical_name": "Boundary Batter", "total_matches": 10}

    # 19 balls faced -> INSUFFICIENT_EVIDENCE
    gp_19 = {
        "weighted_strike_rate": 150.0,
        "sample_indicators": {"balls_faced": 19, "legal_balls_bowled": 0},
    }
    res_19 = ModuleA3ReplaceabilityAssessor.assess(
        rr_profile=rr_profile,
        global_profile=gp_19,
        primary_role="MIDDLE_ORDER_BATTER",
    )
    assert res_19.signal == ReplaceabilitySignal.INSUFFICIENT_EVIDENCE
    assert res_19.insufficient_sample_flag is True

    # 20 balls faced -> Sufficient sample evaluated
    gp_20 = {
        "weighted_strike_rate": 155.0,
        "sample_indicators": {"balls_faced": 20, "legal_balls_bowled": 0},
    }
    res_20 = ModuleA3ReplaceabilityAssessor.assess(
        rr_profile=rr_profile,
        global_profile=gp_20,
        primary_role="MIDDLE_ORDER_BATTER",
    )
    assert res_20.signal != ReplaceabilitySignal.INSUFFICIENT_EVIDENCE
    assert res_20.insufficient_sample_flag is False


def test_boundary_exact_min_sample_threshold_bowler() -> None:
    """Test exact boundary condition: 29 legal balls (insufficient) vs 30 legal balls (sufficient)."""
    rr_profile = {"canonical_name": "Boundary Bowler", "total_matches": 10}

    # 29 balls bowled -> INSUFFICIENT_EVIDENCE
    gp_29 = {
        "weighted_economy": 7.20,
        "sample_indicators": {"balls_faced": 0, "legal_balls_bowled": 29},
    }
    res_29 = ModuleA3ReplaceabilityAssessor.assess(
        rr_profile=rr_profile,
        global_profile=gp_29,
        primary_role="PACE_BOWLER",
    )
    assert res_29.signal == ReplaceabilitySignal.INSUFFICIENT_EVIDENCE
    assert res_29.insufficient_sample_flag is True

    # 30 balls bowled -> Sufficient sample evaluated
    gp_30 = {
        "weighted_economy": 7.20,
        "sample_indicators": {"balls_faced": 0, "legal_balls_bowled": 30},
    }
    res_30 = ModuleA3ReplaceabilityAssessor.assess(
        rr_profile=rr_profile,
        global_profile=gp_30,
        primary_role="PACE_BOWLER",
    )
    assert res_30.signal != ReplaceabilitySignal.INSUFFICIENT_EVIDENCE
    assert res_30.insufficient_sample_flag is False


def test_boundary_pct_all_boundaries_vs_all_singles() -> None:
    """Test weighted boundary % calculation when 100% of runs are boundaries vs 0%."""
    eval_date = date(2025, 3, 1)

    # All boundaries (2 fours, 2 sixes = 20 runs)
    match_all_boundaries = {
        "match_id": "M-BOUND-100",
        "match_date": eval_date - timedelta(days=1),
        "competition_name": "Indian Premier League",
        "format_tag": "T20",
        "batted": True,
        "runs": 20,
        "balls_faced": 8,
        "fours": 2,
        "sixes": 2,
    }
    profile_100 = ModuleA2GlobalPerformance.analyze(
        evaluation_date=eval_date,
        match_records=[match_all_boundaries],
    )
    assert profile_100.boundary_pct == pytest.approx(100.0, 0.01)

    # All singles (20 runs from 20 singles, 0 boundaries)
    match_all_singles = {
        "match_id": "M-SINGLES-0",
        "match_date": eval_date - timedelta(days=1),
        "competition_name": "Indian Premier League",
        "format_tag": "T20",
        "batted": True,
        "runs": 20,
        "balls_faced": 20,
        "fours": 0,
        "sixes": 0,
    }
    profile_0 = ModuleA2GlobalPerformance.analyze(
        evaluation_date=eval_date,
        match_records=[match_all_singles],
    )
    assert profile_0.boundary_pct == pytest.approx(0.0, 0.01)


def test_replaceability_all_rounder_synthesis() -> None:
    """Test Module A3 synthesis for ALL_ROUNDER archetype."""
    rr_profile = {"canonical_name": "Star All-Rounder", "total_matches": 35}

    # Elite batting + elite bowling -> RETAIN_SIGNAL
    gp_elite = {
        "weighted_strike_rate": 148.0,  # +13 vs 135 benchmark
        "weighted_economy": 7.60,       # +0.9 vs 8.50 benchmark
        "sample_indicators": {"balls_faced": 120, "legal_balls_bowled": 120},
    }
    res_elite = ModuleA3ReplaceabilityAssessor.assess(
        rr_profile=rr_profile,
        global_profile=gp_elite,
        primary_role="ALL_ROUNDER",
        age_at_evaluation=27.0,
    )
    assert res_elite.signal == ReplaceabilitySignal.RETAIN_SIGNAL

    # Poor batting + poor bowling + older age -> POTENTIALLY_REPLACEABLE
    gp_declining = {
        "weighted_strike_rate": 115.0,  # -20 vs 135 benchmark
        "weighted_economy": 10.20,      # -1.7 vs 8.50 benchmark
        "sample_indicators": {"balls_faced": 90, "legal_balls_bowled": 90},
    }
    res_declining = ModuleA3ReplaceabilityAssessor.assess(
        rr_profile=rr_profile,
        global_profile=gp_declining,
        primary_role="ALL_ROUNDER",
        age_at_evaluation=35.5,
    )
    assert res_declining.signal == ReplaceabilitySignal.POTENTIALLY_REPLACEABLE


def test_get_balls_per_over_recognizes_the_hundred() -> None:
    """Test get_balls_per_over helper recognizes The Hundred variations."""
    from src.pvre.mode_a_incumbent import get_balls_per_over

    assert get_balls_per_over("The Hundred") == 5
    assert get_balls_per_over("The Hundred Men") == 5
    assert get_balls_per_over("hnd_male_json") == 5
    assert get_balls_per_over("Indian Premier League") == 6
    assert get_balls_per_over("Big Bash League") == 6
    assert get_balls_per_over(None) == 6
