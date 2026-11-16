"""Unit test suite for SICE Milestone 4: Squad Composition & 16-Dimension Balance Evaluator.

Organized into 8 dedicated suites (50 unit tests):
- Suite 1: 16 Balance Dimensions (DIM-01 to DIM-16) + Bounds Test [17 tests]
- Suite 2: Squad Health Index (SHI) & HD-09 Tolerance [6 tests]
- Suite 3: Playing XI Core Optimization [5 tests]
- Suite 4: Dual-Mode Impact Player (HD-06) [5 tests]
- Suite 5: Wicketkeeper Policy (HD-08) [4 tests]
- Suite 6: Deterministic Tiebreaker (HD-10) [4 tests]
- Suite 7: Squad Certification & Roster Governance (HD-05) [4 tests]
- Suite 8: Bowling Balance & Phase Tactical Tests [5 tests]
"""

from __future__ import annotations

import copy
import math
import random
from typing import Any
from uuid import UUID, uuid4

import pytest
from src.contracts.sice import (
    LineupType,
    RosterStatus,
    RunType,
    UncertaintyFlag,
)
from src.contracts.team_builder import UserTeamPlayer
from src.sice.balance_evaluator import SquadBalanceEvaluator
from src.sice.squad_composition import SquadCompositionEngine

# Deterministic fixed test team UUID
TEST_TEAM_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def sample_rr_squad_25() -> list[UserTeamPlayer]:
    """Authentic 25-player Rajasthan Royals squad fixture."""
    players: list[UserTeamPlayer] = []
    # 25 deterministic UUIDs
    for i in range(1, 26):
        pid = UUID(f"10000000-0000-0000-0000-{i:012d}")
        is_capt = i == 1  # Sanju Samson is captain
        role = "Top-order Batter"
        if i in {1, 3, 5, 19}:
            role = "Wicketkeeper Batter"
        elif i in {2, 24, 25}:
            role = "Top-order Batter"
        elif i in {6, 15, 17, 23}:
            role = "Middle-order Batter"
        elif i in {4, 7}:
            role = "Batting All-rounder"
        elif i in {8, 16}:
            role = "Bowling All-rounder"
        elif i in {10, 11, 12, 13, 14, 20, 21, 22}:
            role = "Pace Bowler"
        elif i in {9, 18}:
            role = "Spin Bowler"

        players.append(
            UserTeamPlayer(
                id=uuid4(),
                user_team_id=TEST_TEAM_ID,
                player_id=pid,
                assigned_role=role,
                batting_order=i if i <= 11 else None,
                is_designated_wk=(i == 1),
                is_captain=is_capt,
            )
        )
    return players


@pytest.fixture
def sample_rr_player_metadata_25(
    sample_rr_squad_25: list[UserTeamPlayer],
) -> dict[UUID, dict[str, Any]]:
    """Performance metrics and identities for 25 RR players."""
    meta: dict[UUID, dict[str, Any]] = {}
    # Overseas players: 3 (Buttler), 6 (Hetmyer), 7 (Powell), 10 (Boult), 14 (Burger), 15 (Ferreira)
    overseas_indices = {3, 6, 7, 10, 14, 15}
    # Uncapped domestic: 16 (Kotian), 17 (Dubey), 18 (Mushtaq), 19 (Rathore), 21 (Sen), 22 (Arora), 23 (A. Sharma), 24 (Raghuvanshi)
    uncapped_indices = {16, 17, 18, 19, 21, 22, 23, 24}

    for i, p in enumerate(sample_rr_squad_25, start=1):
        pid = p.player_id
        is_os = i in overseas_indices
        is_uncapped = i in uncapped_indices
        is_wk = i in {1, 3, 5, 19}

        # Batting metrics
        if i in {1, 2, 3, 5, 6}:
            sr, avg, bf = 150.0, 36.0, 1500
        elif i in {4, 7, 15, 23}:
            sr, avg, bf = 145.0, 28.0, 800
        elif i in {8, 16, 17, 19, 24, 25}:
            sr, avg, bf = 130.0, 24.0, 400
        else:  # Tail / pure bowlers
            sr, avg, bf = 85.0, 8.0, 80

        # Bowling metrics
        style = "None"
        balls, apps, econ = 0, 20, 8.5
        if i in {10, 14}:
            style = "Left-arm fast"
            balls, econ = 1200, 8.1
        elif i in {11, 12, 13, 20, 21, 22}:
            style = "Right-arm fast"
            balls, econ = 1200, 8.4
        elif i in {7}:
            style = "Right-arm medium"
            balls, econ = 240, 8.9
        elif i in {8, 16}:
            style = "Right-arm off-break"
            balls, econ = 1400, 7.2
        elif i in {9}:
            style = "Right-arm leg-break"
            balls, econ = 1600, 7.6
        elif i in {18}:
            style = "Slow left-arm orthodox"
            balls, econ = 600, 7.4
        elif i in {4}:
            style = "Right-arm off-break"
            balls, econ = 300, 8.2

        # Handedness: 2 (Jaiswal), 6 (Hetmyer), 14 (Burger), 17 (Dubey), 18 (Mushtaq), 19 (Rathore) are Left
        hand = "Left-hand bat" if i in {2, 6, 14, 17, 18, 19} else "Right-hand bat"

        # Age
        age = 26.5 + (i % 7) - 3.0

        meta[pid] = {
            "name": f"Player_{i}",
            "nationality": "England"
            if i == 3
            else ("West Indies" if i in {6, 7} else ("South Africa" if i in {14, 15} else "India")),
            "is_overseas": is_os,
            "capped_status": "UNCAPPED" if is_uncapped else "CAPPED",
            "eligibility_status": "VERIFIED_ELIGIBLE",
            "identity_status": "RESOLVED",
            "uncertainty_flag": UncertaintyFlag.VERIFIED,
            "batting_strike_rate": sr,
            "batting_average": avg,
            "career_balls_faced": bf,
            "career_balls_bowled": balls,
            "matches": apps,
            "bowling_economy": econ,
            "bowling_style": style,
            "batting_hand": hand,
            "age": age,
            "is_designated_wk": is_wk,
            "phase_balls": {"powerplay": balls // 3, "middle": balls // 2, "death": balls // 6},
            "phase_economy": {"powerplay": econ - 0.3, "middle": econ - 0.5, "death": econ + 1.2},
            "position_innings": {
                1: 10 if i in {1, 2, 3} else 0,
                2: 10 if i in {1, 2, 3} else 0,
                3: 10 if i in {1, 4, 24} else 0,
                4: 10 if i in {4, 5, 6} else 0,
                5: 10 if i in {5, 6, 7} else 0,
                6: 10 if i in {6, 7, 8} else 0,
                7: 10 if i in {7, 8, 16} else 0,
            },
        }

    return meta


# =============================================================================
# Suite 1: Individual Dimension Tests (DIM-01 to DIM-16) [17 tests]
# =============================================================================


def test_dim01_roster_and_overseas_balance(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    score, status, n, os_count, os_ratio, dom_count, flags = (
        evaluator.calculate_dim01_roster_overseas(sample_rr_squad_25, sample_rr_player_metadata_25)
    )
    assert status == RosterStatus.ROSTER_VALID
    assert n == 25
    assert os_count == 6
    assert dom_count == 19
    assert os_ratio == pytest.approx(6 / 25, rel=1e-3)
    assert score == 100.0

    # Variant: Breach overseas limit
    meta_copy = copy.deepcopy(sample_rr_player_metadata_25)
    for i in [0, 1, 3]:
        meta_copy[sample_rr_squad_25[i].player_id]["is_overseas"] = True
    score_breach, status_breach, _, os_c, _, _, flags_breach = (
        evaluator.calculate_dim01_roster_overseas(sample_rr_squad_25, meta_copy)
    )
    assert status_breach == RosterStatus.OVERSEAS_BREACH
    assert os_c == 9
    assert score_breach < 80.0
    assert "OVERSEAS_BREACH" in flags_breach


def test_dim02_role_distribution_and_entropy(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    score, entropy, role_counts, flags = evaluator.calculate_dim02_role_distribution(
        sample_rr_squad_25, sample_rr_player_metadata_25
    )
    assert entropy > 0.70
    assert score >= 75.0

    # Mutate to create role vacuum
    meta_copy = copy.deepcopy(sample_rr_player_metadata_25)
    for p in sample_rr_squad_25:
        meta_copy[p.player_id]["bowling_style"] = "Right-arm fast"
        p_role = p.assigned_role or ""
        if "spin" in p_role.lower():
            p.assigned_role = "Pace Bowler"
    score_vac, _, _, flags_vac = evaluator.calculate_dim02_role_distribution(
        sample_rr_squad_25, meta_copy
    )
    assert "ROLE_VACUUM" in flags_vac


def test_dim03_batting_depth_index_and_lorm(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    score, bdi, lorm, flags = evaluator.calculate_dim03_batting_depth(
        sample_rr_squad_25, sample_rr_player_metadata_25
    )
    assert score is not None and score >= 60.0
    assert bdi is not None and bdi >= 50.0
    assert lorm is not None

    # Test small balls faced exclusion
    meta_copy = copy.deepcopy(sample_rr_player_metadata_25)
    for p in sample_rr_squad_25[:22]:
        meta_copy[p.player_id]["career_balls_faced"] = 15  # < 30
    score_insuf, _, _, flags_insuf = evaluator.calculate_dim03_batting_depth(
        sample_rr_squad_25, meta_copy
    )
    assert score_insuf is None
    assert "INSUFFICIENT_BATTING_DATA" in flags_insuf


def test_dim04_bowling_depth_and_over_cushion(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    score, soc, fbo, sbo, flags = evaluator.calculate_dim04_bowling_depth(
        sample_rr_squad_25, sample_rr_player_metadata_25
    )
    assert soc >= 35.0
    assert fbo >= 6
    assert score >= 80.0


def test_dim05_pace_vs_spin_balance_ratio(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    score, pace_c, spin_c, psr, flags = evaluator.calculate_dim05_pace_spin(
        sample_rr_squad_25, sample_rr_player_metadata_25
    )
    assert pace_c >= 5
    assert spin_c >= 2
    assert psr is not None
    assert score >= 80.0


def test_dim06_bowling_phase_specialisation(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    score, phase_caps, flags = evaluator.calculate_dim06_bowling_phase(
        sample_rr_squad_25, sample_rr_player_metadata_25
    )
    assert "powerplay" in phase_caps
    assert "middle" in phase_caps
    assert "death" in phase_caps
    assert score >= 60.0


def test_dim07_wicketkeeper_security(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    # RR squad has 4 wicketkeepers
    score, wk_count, flags = evaluator.calculate_dim07_wicketkeeper_security(
        sample_rr_squad_25, sample_rr_player_metadata_25
    )
    assert wk_count == 4
    assert "SLOT_WASTE" in flags

    # Mutate to 2 keepers
    squad_2wk = copy.deepcopy(sample_rr_squad_25)
    meta_2wk = copy.deepcopy(sample_rr_player_metadata_25)
    for p in squad_2wk[3:]:
        p.is_designated_wk = False
        meta_2wk[p.player_id]["is_designated_wk"] = False
        p.assigned_role = "Middle-order Batter"
        meta_2wk[p.player_id]["role"] = "Middle-order Batter"
    score_2, wk_c2, _ = evaluator.calculate_dim07_wicketkeeper_security(squad_2wk, meta_2wk)
    assert wk_c2 == 2
    assert score_2 >= 90.0


def test_dim08_all_rounder_balance(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    score, ar_count, flags = evaluator.calculate_dim08_all_rounder_balance(
        sample_rr_squad_25, sample_rr_player_metadata_25
    )
    assert ar_count == 4
    assert score >= 80.0


def test_dim09_batting_handedness_diversity(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    score, lhr_top7, flags = evaluator.calculate_dim09_handedness_diversity(
        sample_rr_squad_25, sample_rr_player_metadata_25
    )
    assert 0.14 <= lhr_top7 <= 0.60
    assert score >= 60.0


def test_dim10_bowling_style_diversity(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    score, sds, flags = evaluator.calculate_dim10_bowling_style_diversity(
        sample_rr_squad_25, sample_rr_player_metadata_25
    )
    assert sds >= 4
    assert score >= 80.0


def test_dim11_age_and_squad_longevity(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    score, mean_age, vfe, flags = evaluator.calculate_dim11_age_squad_longevity(
        sample_rr_squad_25, sample_rr_player_metadata_25
    )
    assert mean_age is not None
    assert 24.0 <= mean_age <= 30.0
    assert score is not None and score >= 70.0


def test_dim12_verified_uncapped_domestic_quota(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    score, uncapped_c, flags = evaluator.calculate_dim12_uncapped_quota(
        sample_rr_squad_25, sample_rr_player_metadata_25
    )
    assert uncapped_c == 8
    assert score == 100.0


def test_dim13_role_redundancy_and_cannibalization(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    score, cannibal_flags, flags = evaluator.calculate_dim13_role_redundancy(
        sample_rr_squad_25, sample_rr_player_metadata_25
    )
    assert score >= 60.0


def test_dim14_positional_coverage_continuity(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    score, pcd, flags = evaluator.calculate_dim14_positional_coverage(
        sample_rr_squad_25, sample_rr_player_metadata_25
    )
    assert pcd == 0
    assert score == 100.0


def test_dim15_tactical_versatility_index(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    score, vi, flags = evaluator.calculate_dim15_tactical_versatility(
        sample_rr_squad_25, sample_rr_player_metadata_25
    )
    assert vi >= 0.50
    assert score >= 50.0


def test_dim16_evidentiary_health_score(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    score, sehs, flags = evaluator.calculate_dim16_evidentiary_health(
        sample_rr_squad_25, sample_rr_player_metadata_25
    )
    assert sehs == 1.0
    assert score == 100.0


def test_dim_score_bounds_and_nan_rejection(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    dims = evaluator.evaluate_all_dimensions(sample_rr_squad_25, sample_rr_player_metadata_25)
    for dim_name, score in dims.dimension_scores.items():
        if score is not None:
            assert not math.isnan(score), f"{dim_name} yielded NaN"
            assert not math.isinf(score), f"{dim_name} yielded Inf"
            assert 0.0 <= score <= 100.0, f"{dim_name} yielded out of bounds {score}"


# =============================================================================
# Suite 2: Squad Health Index (SHI) & HD-09 Tolerance [6 tests]
# =============================================================================


def test_shi_weighted_aggregation_accuracy() -> None:
    evaluator = SquadBalanceEvaluator()
    # Dimension scores all equal to 80.0
    dim_scores = {f"DIM-{i:02d}": 80.0 for i in range(1, 17)}
    shi = evaluator.calculate_squad_health_index(dim_scores, squad_size=25)
    assert shi == pytest.approx(80.0, rel=1e-3)


def test_shi_dynamic_reweighting_on_missing_dimensions() -> None:
    evaluator = SquadBalanceEvaluator()
    dim_scores = {f"DIM-{i:02d}": 80.0 for i in range(1, 17)}
    dim_scores["DIM-14"] = None
    dim_scores["DIM-15"] = None
    shi = evaluator.calculate_squad_health_index(dim_scores, squad_size=25)
    assert shi is not None
    assert shi == pytest.approx(80.0, rel=1e-3)


def test_shi_suppression_when_insufficient_dimensions() -> None:
    evaluator = SquadBalanceEvaluator()
    dim_scores = {f"DIM-{i:02d}": 80.0 for i in range(1, 17)}
    # Suppress 5 dimensions -> only 11 left < 12
    for i in range(1, 6):
        dim_scores[f"DIM-{i:02d}"] = None
    shi = evaluator.calculate_squad_health_index(dim_scores, squad_size=25)
    assert shi is None


def test_shi_hd09_suppression_for_undersized_draft_squad(
    sample_rr_squad_25: list[UserTeamPlayer],
) -> None:
    evaluator = SquadBalanceEvaluator()
    dim_scores = {f"DIM-{i:02d}": 80.0 for i in range(1, 17)}
    # HD-09: If squad size < 18, SHI MUST evaluate to None
    shi = evaluator.calculate_squad_health_index(dim_scores, squad_size=14)
    assert shi is None


def test_shi_valid_range_for_full_squad_n18_to_25(
    sample_rr_squad_25: list[UserTeamPlayer],
) -> None:
    evaluator = SquadBalanceEvaluator()
    dim_scores = {f"DIM-{i:02d}": 85.0 for i in range(1, 17)}
    for size in [18, 21, 25]:
        shi = evaluator.calculate_squad_health_index(dim_scores, squad_size=size)
        assert shi is not None
        assert 0.0 <= shi <= 100.0


def test_shi_hd09_oversized_squad_rejection(
    sample_rr_squad_25: list[UserTeamPlayer],
) -> None:
    engine = SquadCompositionEngine()
    players_26 = list(sample_rr_squad_25)
    extra_player = copy.deepcopy(sample_rr_squad_25[0])
    extra_player.player_id = uuid4()
    players_26.append(extra_player)

    output = engine.evaluate_squad(TEST_TEAM_ID, context={"players": players_26})
    assert output.is_valid_ipl_roster is False
    assert output.roster_status == RosterStatus.ROSTER_OVERSIZED


# =============================================================================
# Suite 3: Playing XI Statutory Constraint Tests [5 tests]
# =============================================================================


def test_playing_xi_exact_11_players_selected(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    engine = SquadCompositionEngine()
    lineups = engine.optimize_playing_xi(
        sample_rr_squad_25, sample_rr_player_metadata_25, enable_impact_player=False
    )
    lineup = lineups[0]
    assert len(lineup.starting_xi_player_ids) == 11
    assert len(set(lineup.starting_xi_player_ids)) == 11
    assert lineup.is_valid_ipl_lineup is True


def test_playing_xi_overseas_player_limit_max_4(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    engine = SquadCompositionEngine()
    lineups = engine.optimize_playing_xi(
        sample_rr_squad_25, sample_rr_player_metadata_25, enable_impact_player=False
    )
    lineup = lineups[0]
    assert lineup.overseas_count <= 4
    assert len(lineup.overseas_player_ids) <= 4


def test_playing_xi_minimum_bowling_quota_5_bowlers_20_overs(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    engine = SquadCompositionEngine()
    lineups = engine.optimize_playing_xi(
        sample_rr_squad_25, sample_rr_player_metadata_25, enable_impact_player=False
    )
    lineup = lineups[0]
    assert lineup.bowling_overs_capacity >= 20.0
    assert lineup.frontline_bowlers_count >= 5


def test_playing_xi_batting_order_unique_slots_1_to_11(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    engine = SquadCompositionEngine()
    lineups = engine.optimize_playing_xi(
        sample_rr_squad_25, sample_rr_player_metadata_25, enable_impact_player=False
    )
    lineup = lineups[0]
    assert len(lineup.batting_order) == 11
    assert len(set(lineup.batting_order)) == 11


def test_playing_xi_single_captain_designation(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    engine = SquadCompositionEngine()
    lineups = engine.optimize_playing_xi(
        sample_rr_squad_25, sample_rr_player_metadata_25, enable_impact_player=False
    )
    lineup = lineups[0]
    assert lineup.captain_player_id == sample_rr_squad_25[0].player_id
    assert lineup.captain_player_id in lineup.starting_xi_player_ids


# =============================================================================
# Suite 4: Dual-Mode Impact Player Tests (HD-06) [5 tests]
# =============================================================================


def test_impact_player_disabled_traditional_xi(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    engine = SquadCompositionEngine()
    lineups = engine.optimize_playing_xi(
        sample_rr_squad_25, sample_rr_player_metadata_25, enable_impact_player=False
    )
    assert len(lineups) == 1
    lineup = lineups[0]
    assert lineup.lineup_type == LineupType.TRADITIONAL_XI
    assert len(lineup.starting_xi_player_ids) == 11
    assert lineup.nominated_substitute_ids == []
    assert lineup.impact_player_id is None
    assert lineup.impact_sub_out_id is None


def test_impact_player_enabled_nominates_5_substitutes(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    engine = SquadCompositionEngine()
    lineups = engine.optimize_playing_xi(
        sample_rr_squad_25, sample_rr_player_metadata_25, enable_impact_player=True
    )
    lineup = lineups[0]
    assert len(lineup.starting_xi_player_ids) == 11
    assert len(lineup.nominated_substitute_ids) == 5
    assert set(lineup.starting_xi_player_ids) & set(lineup.nominated_substitute_ids) == set()
    assert lineup.impact_player_id is not None
    assert lineup.impact_player_id in lineup.nominated_substitute_ids
    assert lineup.impact_sub_out_id in lineup.starting_xi_player_ids


def test_impact_player_rule_4_overseas_starters_requires_indian_sub(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    engine = SquadCompositionEngine()
    meta_copy = copy.deepcopy(sample_rr_player_metadata_25)
    # Ensure starting XI contains exactly 4 overseas
    for p in sample_rr_squad_25[:4]:
        meta_copy[p.player_id]["is_overseas"] = True

    lineups = engine.optimize_playing_xi(sample_rr_squad_25, meta_copy, enable_impact_player=True)
    lineup = lineups[0]
    if lineup.overseas_count == 4:
        # Designated impact player MUST be Indian
        impact_id = lineup.impact_player_id
        assert impact_id is not None
        assert meta_copy[impact_id]["is_overseas"] is False


def test_impact_player_rule_3_or_fewer_overseas_starters_permits_overseas_sub(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    engine = SquadCompositionEngine()
    meta_copy = copy.deepcopy(sample_rr_player_metadata_25)
    # Make sure starters have <= 3 overseas
    for p in sample_rr_squad_25:
        meta_copy[p.player_id]["is_overseas"] = False
    meta_copy[sample_rr_squad_25[2].player_id]["is_overseas"] = True  # Jos Buttler
    meta_copy[sample_rr_squad_25[9].player_id]["is_overseas"] = True  # Trent Boult

    lineups = engine.optimize_playing_xi(sample_rr_squad_25, meta_copy, enable_impact_player=True)
    lineup = lineups[0]
    assert lineup.overseas_count <= 3
    assert lineup.is_valid_ipl_lineup is True


def test_impact_player_tactical_packages_bat_and_bowl_first(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    engine = SquadCompositionEngine()
    bat_lineup = engine.optimize_playing_xi(
        sample_rr_squad_25,
        sample_rr_player_metadata_25,
        enable_impact_player=True,
        tactical_scenario="BAT_FIRST",
    )[0]
    assert bat_lineup.lineup_type == LineupType.BAT_FIRST_IMPACT
    assert bat_lineup.impact_player_id is not None
    assert bat_lineup.impact_sub_out_id is not None

    bowl_lineup = engine.optimize_playing_xi(
        sample_rr_squad_25,
        sample_rr_player_metadata_25,
        enable_impact_player=True,
        tactical_scenario="BOWL_FIRST",
    )[0]
    assert bowl_lineup.lineup_type == LineupType.BOWL_FIRST_IMPACT
    assert bowl_lineup.impact_player_id is not None
    assert bowl_lineup.impact_sub_out_id is not None


# =============================================================================
# Suite 5: Wicketkeeper Quota & Role Tests (HD-08) [4 tests]
# =============================================================================


def test_wk_policy_exactly_one_designated_wk_in_playing_xi(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    engine = SquadCompositionEngine()
    lineups = engine.optimize_playing_xi(
        sample_rr_squad_25, sample_rr_player_metadata_25, enable_impact_player=False
    )
    lineup = lineups[0]
    assert lineup.designated_wicketkeeper_player_id is not None
    assert lineup.designated_wicketkeeper_player_id in lineup.starting_xi_player_ids


def test_wk_policy_zero_wk_in_squad_fails_validation(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    engine = SquadCompositionEngine()
    squad_nowk = copy.deepcopy(sample_rr_squad_25)
    meta_nowk = copy.deepcopy(sample_rr_player_metadata_25)
    for p in squad_nowk:
        p.is_designated_wk = False
        p.assigned_role = "Middle-order Batter"
        meta_nowk[p.player_id]["is_designated_wk"] = False
        meta_nowk[p.player_id]["role"] = "Middle-order Batter"

    lineups = engine.optimize_playing_xi(squad_nowk, meta_nowk, enable_impact_player=False)
    lineup = lineups[0]
    assert lineup.is_valid_ipl_lineup is False
    assert "CRITICAL_WK_SHORTAGE" in lineup.violations


def test_wk_policy_two_plus_wks_secondary_can_play_as_batter(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    engine = SquadCompositionEngine()
    lineups = engine.optimize_playing_xi(
        sample_rr_squad_25, sample_rr_player_metadata_25, enable_impact_player=False
    )
    lineup = lineups[0]
    assert lineup.designated_wicketkeeper_player_id == sample_rr_squad_25[0].player_id
    # Other keeper (e.g. Buttler or Jurel) selected in starting XI as pure batter
    assert sample_rr_squad_25[2].player_id in lineup.starting_xi_player_ids
    assert lineup.is_valid_ipl_lineup is True


def test_wk_policy_squad_level_shortage_and_waste_warnings(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    engine = SquadCompositionEngine()
    # Case 1: 1 keeper
    squad_1wk = copy.deepcopy(sample_rr_squad_25)
    meta_1wk = copy.deepcopy(sample_rr_player_metadata_25)
    for p in squad_1wk[1:]:
        p.is_designated_wk = False
        meta_1wk[p.player_id]["is_designated_wk"] = False
        p.assigned_role = "Pace Bowler"
        meta_1wk[p.player_id]["role"] = "Pace Bowler"

    res_1 = engine.evaluate_squad(
        TEST_TEAM_ID, context={"players": squad_1wk, "player_metadata": meta_1wk}
    )
    assert "VULNERABILITY_NO_BACKUP_WK" in res_1.weaknesses

    # Case 2: 4 keepers (already in sample_rr_squad_25: Samson, Buttler, Jurel, Rathore)
    res_4 = engine.evaluate_squad(
        TEST_TEAM_ID,
        context={"players": sample_rr_squad_25, "player_metadata": sample_rr_player_metadata_25},
    )
    assert "SLOT_WASTE" in res_4.weaknesses


# =============================================================================
# Suite 6: Deterministic Tiebreaker Tests (HD-10) [4 tests]
# =============================================================================


def test_tiebreaker_tb1_higher_lorm_wins() -> None:
    engine = SquadCompositionEngine()
    # 12 players where player 11 has higher LORM than player 12
    base_players: list[UserTeamPlayer] = []
    meta: dict[UUID, dict[str, Any]] = {}
    for i in range(1, 13):
        pid = UUID(f"20000000-0000-0000-0000-{i:012d}")
        base_players.append(
            UserTeamPlayer(
                id=uuid4(),
                user_team_id=TEST_TEAM_ID,
                player_id=pid,
                assigned_role="Pace Bowler"
                if i in range(1, 6)
                else ("Wicketkeeper Batter" if i == 6 else "Middle-order Batter"),
                is_designated_wk=(i == 6),
                is_captain=(i == 1),
            )
        )
        # Players 11 and 12 have equal utility, but player 11 has higher LORM/IBC
        ibc = 55.0 if i == 11 else (40.0 if i == 12 else 60.0)
        meta[pid] = {
            "is_overseas": False,
            "ibc": ibc,
            "career_balls_bowled": 1200 if i in range(1, 6) else 0,
            "matches": 20,
            "bowling_economy": 8.0,
            "bowling_style": "Right-arm fast" if i in range(1, 6) else "None",
            "is_designated_wk": (i == 6),
        }

    lineup = engine.optimize_playing_xi(base_players, meta, enable_impact_player=False)[0]
    assert base_players[10].player_id in lineup.starting_xi_player_ids  # Player 11 chosen over 12


def test_tiebreaker_tb2_lower_pds_wins() -> None:
    engine = SquadCompositionEngine()
    base_players: list[UserTeamPlayer] = []
    meta: dict[UUID, dict[str, Any]] = {}
    for i in range(1, 13):
        pid = UUID(f"30000000-0000-0000-0000-{i:012d}")
        base_players.append(
            UserTeamPlayer(
                id=uuid4(),
                user_team_id=TEST_TEAM_ID,
                player_id=pid,
                assigned_role="Pace Bowler"
                if i in range(1, 6)
                else ("Wicketkeeper Batter" if i == 6 else "Middle-order Batter"),
                is_designated_wk=(i == 6),
                is_captain=(i == 1),
            )
        )
        # Players 11 and 12 have identical IBC/utility, but player 11 has death bowling competency (lower PDS)
        meta[pid] = {
            "is_overseas": False,
            "ibc": 50.0,
            "career_balls_bowled": 1200 if i in range(1, 6) or i == 11 else 0,
            "matches": 20,
            "bowling_economy": 8.0,
            "bowling_style": "Right-arm fast" if i in range(1, 6) or i == 11 else "None",
            "is_designated_wk": (i == 6),
            "phase_balls": {"powerplay": 300, "middle": 400, "death": 500 if i == 11 else 0},
            "phase_economy": {"powerplay": 7.5, "middle": 8.0, "death": 9.0},
        }

    lineup = engine.optimize_playing_xi(base_players, meta, enable_impact_player=False)[0]
    assert base_players[10].player_id in lineup.starting_xi_player_ids


def test_tiebreaker_tb3_lexicographical_uuid_total_order() -> None:
    engine = SquadCompositionEngine()
    base_players: list[UserTeamPlayer] = []
    meta: dict[UUID, dict[str, Any]] = {}
    # 10 core players
    for i in range(1, 11):
        pid = UUID(f"40000000-0000-0000-0000-{i:012d}")
        base_players.append(
            UserTeamPlayer(
                id=uuid4(),
                user_team_id=TEST_TEAM_ID,
                player_id=pid,
                assigned_role="Pace Bowler"
                if i in range(1, 6)
                else ("Wicketkeeper Batter" if i == 6 else "Middle-order Batter"),
                is_designated_wk=(i == 6),
                is_captain=(i == 1),
            )
        )
        meta[pid] = {
            "is_overseas": False,
            "ibc": 50.0,
            "career_balls_bowled": 1200 if i in range(1, 6) else 0,
            "matches": 20,
            "bowling_economy": 8.0,
            "is_designated_wk": (i == 6),
        }

    # Two exactly identical candidates for 11th slot:
    # Player A: 00000000-aaaa-..., Player B: ffffffff-bbbb-...
    pid_a = UUID("00000000-aaaa-0000-0000-000000000001")
    pid_b = UUID("ffffffff-bbbb-0000-0000-000000000002")
    for pid in [pid_a, pid_b]:
        base_players.append(
            UserTeamPlayer(
                id=uuid4(),
                user_team_id=TEST_TEAM_ID,
                player_id=pid,
                assigned_role="Middle-order Batter",
            )
        )
        meta[pid] = {
            "is_overseas": False,
            "ibc": 50.0,
            "career_balls_bowled": 0,
            "matches": 20,
            "bowling_economy": 8.0,
            "is_designated_wk": False,
        }

    lineup = engine.optimize_playing_xi(base_players, meta, enable_impact_player=False)[0]
    # Lexicographically smaller UUID (pid_a) must be selected
    assert pid_a in lineup.starting_xi_player_ids
    assert pid_b not in lineup.starting_xi_player_ids


def test_tiebreaker_roster_shuffle_permutation_invariance(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    engine = SquadCompositionEngine()
    baseline_lineup = engine.optimize_playing_xi(
        sample_rr_squad_25, sample_rr_player_metadata_25, enable_impact_player=True, seed=42
    )[0]

    for seed_i in range(10):
        shuffled_squad = list(sample_rr_squad_25)
        random.Random(seed_i).shuffle(shuffled_squad)
        shuffled_lineup = engine.optimize_playing_xi(
            shuffled_squad, sample_rr_player_metadata_25, enable_impact_player=True, seed=42
        )[0]

        assert baseline_lineup.starting_xi_player_ids == shuffled_lineup.starting_xi_player_ids
        assert baseline_lineup.batting_order == shuffled_lineup.batting_order
        assert baseline_lineup.impact_player_id == shuffled_lineup.impact_player_id


# =============================================================================
# Suite 7: Squad Certification & Roster Governance Tests (HD-05) [4 tests]
# =============================================================================


def test_squad_certification_official_success_on_verified_roster(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    engine = SquadCompositionEngine()
    output = engine.evaluate_squad(
        TEST_TEAM_ID,
        context={
            "players": sample_rr_squad_25,
            "player_metadata": sample_rr_player_metadata_25,
            "run_type": RunType.SQUAD_EVALUATION,
        },
    )
    assert output.is_valid_ipl_roster is True
    assert output.roster_status == RosterStatus.ROSTER_VALID
    assert output.uncertainty_badge == "VERIFIED"


def test_squad_certification_blocks_provisional_identities_in_official(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    engine = SquadCompositionEngine()
    meta_copy = copy.deepcopy(sample_rr_player_metadata_25)
    # Mark player 25 as PROVISIONAL
    p25_id = sample_rr_squad_25[24].player_id
    meta_copy[p25_id]["identity_status"] = "PROVISIONAL"
    meta_copy[p25_id]["uncertainty_flag"] = UncertaintyFlag.PROVISIONAL

    output = engine.evaluate_squad(
        TEST_TEAM_ID,
        context={
            "players": sample_rr_squad_25,
            "player_metadata": meta_copy,
            "run_type": RunType.SQUAD_EVALUATION,
        },
    )
    assert output.is_valid_ipl_roster is False
    assert "PROVISIONAL_SQUAD_INTELLIGENCE" in output.weaknesses


def test_squad_certification_draft_exploration_permits_provisional_and_incomplete(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    engine = SquadCompositionEngine()
    draft_players = sample_rr_squad_25[:14]  # 14 players < 18
    meta_copy = copy.deepcopy(sample_rr_player_metadata_25)
    meta_copy[draft_players[0].player_id]["identity_status"] = "PROVISIONAL"

    output = engine.evaluate_squad(
        TEST_TEAM_ID,
        context={
            "players": draft_players,
            "player_metadata": meta_copy,
            "run_type": RunType.DRAFT_EXPLORATION,
        },
    )
    assert output.is_valid_ipl_roster is False
    assert output.roster_status == RosterStatus.ROSTER_INCOMPLETE
    assert output.squad_health_index is None
    assert output.balance_dimensions.squad_size == 14


def test_squad_certification_overseas_breach_blocked(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    engine = SquadCompositionEngine()
    meta_copy = copy.deepcopy(sample_rr_player_metadata_25)
    # Set 9 overseas players
    for p in sample_rr_squad_25[:9]:
        meta_copy[p.player_id]["is_overseas"] = True

    output = engine.evaluate_squad(
        TEST_TEAM_ID,
        context={
            "players": sample_rr_squad_25,
            "player_metadata": meta_copy,
            "run_type": RunType.SQUAD_EVALUATION,
        },
    )
    assert output.is_valid_ipl_roster is False
    assert output.roster_status == RosterStatus.OVERSEAS_BREACH


# =============================================================================
# Suite 8: Bowling Balance & Phase Tactical Tests [5 tests]
# =============================================================================


def test_bowling_balance_pace_to_spin_ratio_normal(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    score, pace_c, spin_c, psr, flags = evaluator.calculate_dim05_pace_spin(
        sample_rr_squad_25, sample_rr_player_metadata_25
    )
    assert psr is not None
    assert "PACE_DEFICIT" not in flags
    assert "SPIN_DEFICIT" not in flags


def test_bowling_balance_pace_deficit_flag(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    meta_copy = copy.deepcopy(sample_rr_player_metadata_25)
    # 2 pacers and 6 spinners -> PSR = 2/6 = 0.33 < 0.8
    for i, p in enumerate(sample_rr_squad_25):
        if i < 2:
            meta_copy[p.player_id]["bowling_style"] = "Right-arm fast"
        elif i < 8:
            meta_copy[p.player_id]["bowling_style"] = "Right-arm leg-break"
        else:
            meta_copy[p.player_id]["bowling_style"] = "None"
            meta_copy[p.player_id]["career_balls_bowled"] = 0

    score, pace_c, spin_c, psr, flags = evaluator.calculate_dim05_pace_spin(
        sample_rr_squad_25, meta_copy
    )
    assert psr is not None and psr < 0.8
    assert "PACE_DEFICIT" in flags


def test_bowling_balance_spin_deficit_flag(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    meta_copy = copy.deepcopy(sample_rr_player_metadata_25)
    # 9 pacers and 1 spinner -> PSR = 9/1 = 9.0 > 2.5
    for i, p in enumerate(sample_rr_squad_25):
        if i < 9:
            meta_copy[p.player_id]["bowling_style"] = "Right-arm fast"
        elif i == 9:
            meta_copy[p.player_id]["bowling_style"] = "Right-arm leg-break"
        else:
            meta_copy[p.player_id]["bowling_style"] = "None"
            meta_copy[p.player_id]["career_balls_bowled"] = 0

    score, pace_c, spin_c, psr, flags = evaluator.calculate_dim05_pace_spin(
        sample_rr_squad_25, meta_copy
    )
    assert psr is not None and psr > 2.5
    assert "SPIN_DEFICIT" in flags


def test_bowling_balance_overs_cushion_adequacy(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    # High cushion
    score_high, soc_high, _, _, flags_high = evaluator.calculate_dim04_bowling_depth(
        sample_rr_squad_25, sample_rr_player_metadata_25
    )
    assert soc_high >= 35.0
    assert "BOWLING_CUSHION_DEFICIT" not in flags_high

    # Low cushion
    meta_low = copy.deepcopy(sample_rr_player_metadata_25)
    for p in sample_rr_squad_25:
        meta_low[p.player_id]["career_balls_bowled"] = 60
        meta_low[p.player_id]["matches"] = 20
    score_low, soc_low, _, _, flags_low = evaluator.calculate_dim04_bowling_depth(
        sample_rr_squad_25, meta_low
    )
    assert soc_low < 30.0
    assert "BOWLING_CUSHION_DEFICIT" in flags_low


def test_phase_deficit_death_bowling_critical_flag(
    sample_rr_squad_25: list[UserTeamPlayer],
    sample_rr_player_metadata_25: dict[UUID, dict[str, Any]],
) -> None:
    evaluator = SquadBalanceEvaluator()
    meta_nodeath = copy.deepcopy(sample_rr_player_metadata_25)
    for p in sample_rr_squad_25:
        meta_nodeath[p.player_id]["phase_balls"] = {"powerplay": 200, "middle": 200, "death": 0}
        meta_nodeath[p.player_id]["phase_economy"] = {
            "powerplay": 7.5,
            "middle": 7.5,
            "death": 14.0,
        }
        meta_nodeath[p.player_id]["bowling_economy"] = 10.5

    score, phase_caps, flags = evaluator.calculate_dim06_bowling_phase(
        sample_rr_squad_25, meta_nodeath
    )
    assert "CRITICAL_DEATH_BOWLING_DEFICIT" in flags
