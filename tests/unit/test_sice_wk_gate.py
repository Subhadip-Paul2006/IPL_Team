"""Targeted unit tests for SICE Squad Certification Wicketkeeper Gate (HD-08)."""

from __future__ import annotations

import copy
from typing import Any
from uuid import UUID, uuid4

import pytest
from src.contracts.sice import (
    RosterStatus,
    RunType,
)
from src.contracts.team_builder import UserTeamPlayer
from src.sice.exceptions import SquadConstraintViolationError
from src.sice.squad_composition import SquadCompositionEngine

TEST_TEAM_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def base_25_squad() -> list[UserTeamPlayer]:
    """25-player squad fixture with 2 WKs (indices 1 and 2)."""
    players: list[UserTeamPlayer] = []
    for i in range(1, 26):
        pid = UUID(f"20000000-0000-0000-0000-{i:012d}")
        is_wk = i in {1, 2}
        players.append(
            UserTeamPlayer(
                id=uuid4(),
                user_team_id=TEST_TEAM_ID,
                player_id=pid,
                assigned_role="Wicketkeeper Batter"
                if is_wk
                else ("Top-order Batter" if i <= 10 else "Bowler"),
                batting_order=i if i <= 11 else None,
                is_designated_wk=is_wk,
                is_captain=(i == 1),
            )
        )
    return players


@pytest.fixture
def base_25_meta(base_25_squad: list[UserTeamPlayer]) -> dict[UUID, dict[str, Any]]:
    """Metadata for 25-player squad with 2 WKs (indices 1 and 2)."""
    meta: dict[UUID, dict[str, Any]] = {}
    overseas_indices = {3, 6, 7, 10, 14, 15}  # 6 overseas, well within max 8
    for i, p in enumerate(base_25_squad, start=1):
        pid = p.player_id
        is_os = i in overseas_indices
        is_wk = i in {1, 2}
        meta[pid] = {
            "player_id": pid,
            "canonical_name": f"Player_{i}",
            "role": "Wicketkeeper Batter"
            if is_wk
            else ("Top-order Batter" if i <= 10 else "Bowler"),
            "bowling_style": "Right-arm fast"
            if (i > 15 and i % 2 == 0)
            else ("Right-arm leg-break" if i > 15 else "None"),
            "batting_hand": "Right-hand bat",
            "is_overseas": is_os,
            "identity_status": "RESOLVED",
            "uncertainty_flag": "VERIFIED",
            "batting_average": 30.0,
            "batting_strike_rate": 135.0,
            "career_balls_faced": 500,
            "career_balls_bowled": 300 if i > 15 else 0,
            "matches": 30,
        }
    return meta


def test_official_squad_with_one_wk_fails_certification(
    base_25_squad: list[UserTeamPlayer],
    base_25_meta: dict[UUID, dict[str, Any]],
) -> None:
    """HD-08: Full squad with only 1 WK cannot receive official certification."""
    engine = SquadCompositionEngine()
    meta = copy.deepcopy(base_25_meta)
    squad = copy.deepcopy(base_25_squad)

    # Change player 2 so they are not a wicketkeeper
    p2 = squad[1]
    p2.is_designated_wk = False
    p2.assigned_role = "Top-order Batter"
    meta[p2.player_id]["role"] = "Top-order Batter"

    output = engine.evaluate_squad(
        TEST_TEAM_ID,
        context={
            "players": squad,
            "player_metadata": meta,
            "run_type": RunType.SQUAD_EVALUATION,
        },
    )
    assert output.is_valid_ipl_roster is False
    assert output.balance_dimensions.wicketkeeper_count == 1
    assert "VULNERABILITY_NO_BACKUP_WK" in output.weaknesses


def test_official_squad_with_zero_wk_fails_certification(
    base_25_squad: list[UserTeamPlayer],
    base_25_meta: dict[UUID, dict[str, Any]],
) -> None:
    """HD-08: Full squad with 0 WKs cannot receive official certification."""
    engine = SquadCompositionEngine()
    meta = copy.deepcopy(base_25_meta)
    squad = copy.deepcopy(base_25_squad)

    # Remove all wicketkeepers
    for p in squad:
        p.is_designated_wk = False
        p.assigned_role = "Top-order Batter"
        meta[p.player_id]["role"] = "Top-order Batter"

    output = engine.evaluate_squad(
        TEST_TEAM_ID,
        context={
            "players": squad,
            "player_metadata": meta,
            "run_type": RunType.SQUAD_EVALUATION,
        },
    )
    assert output.is_valid_ipl_roster is False
    assert output.balance_dimensions.wicketkeeper_count == 0
    assert "CRITICAL_WK_SHORTAGE" in output.critical_deficits


def test_official_squad_with_two_wk_passes_certification(
    base_25_squad: list[UserTeamPlayer],
    base_25_meta: dict[UUID, dict[str, Any]],
) -> None:
    """HD-08: Full squad with 2 WKs satisfies official certification."""
    engine = SquadCompositionEngine()
    output = engine.evaluate_squad(
        TEST_TEAM_ID,
        context={
            "players": base_25_squad,
            "player_metadata": base_25_meta,
            "run_type": RunType.SQUAD_EVALUATION,
        },
    )
    assert output.is_valid_ipl_roster is True
    assert output.balance_dimensions.wicketkeeper_count == 2
    assert output.roster_status == RosterStatus.ROSTER_VALID


def test_official_squad_strict_mode_with_one_wk_raises(
    base_25_squad: list[UserTeamPlayer],
    base_25_meta: dict[UUID, dict[str, Any]],
) -> None:
    """HD-08: Strict official mode raises SquadConstraintViolationError when < 2 WKs."""
    engine = SquadCompositionEngine()
    meta = copy.deepcopy(base_25_meta)
    squad = copy.deepcopy(base_25_squad)

    # Change player 2 so they are not a wicketkeeper
    p2 = squad[1]
    p2.is_designated_wk = False
    p2.assigned_role = "Top-order Batter"
    meta[p2.player_id]["role"] = "Top-order Batter"

    with pytest.raises(SquadConstraintViolationError) as exc_info:
        engine.evaluate_squad(
            TEST_TEAM_ID,
            context={
                "players": squad,
                "player_metadata": meta,
                "run_type": RunType.SQUAD_EVALUATION,
                "strict_official": True,
            },
        )
    assert exc_info.value.violation_type == "INSUFFICIENT_WICKETKEEPERS"
    assert "HD-08" in exc_info.value.message


def test_draft_squad_with_zero_wk_still_valid_draft(
    base_25_squad: list[UserTeamPlayer],
    base_25_meta: dict[UUID, dict[str, Any]],
) -> None:
    """HD-09: Draft exploration mode handles incomplete rosters gracefully without strict error."""
    engine = SquadCompositionEngine()
    draft_players = base_25_squad[:12]  # 12 players
    meta = copy.deepcopy(base_25_meta)

    output = engine.evaluate_squad(
        TEST_TEAM_ID,
        context={
            "players": draft_players,
            "player_metadata": meta,
            "run_type": RunType.DRAFT_EXPLORATION,
        },
    )
    assert output.is_valid_ipl_roster is False
    assert output.roster_status == RosterStatus.ROSTER_INCOMPLETE
    assert output.squad_health_index is None
