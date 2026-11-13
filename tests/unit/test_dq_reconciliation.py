"""Unit tests for Data Quality and Delivery Reconciliation Engine.

Part of Track A — Phase 1 Historical Data Pipeline Closure.
"""

from uuid import uuid4

import pytest
from src.contracts.match import Delivery, Innings
from src.quality.reconciliation import DataQualityReconciliationService


@pytest.fixture
def dq_service() -> DataQualityReconciliationService:
    return DataQualityReconciliationService()


def make_delivery(
    innings_id,
    over_number: int,
    ball_in_over: int,
    runs_batter: int = 1,
    runs_extras: int = 0,
    is_wide: bool = False,
    is_wicket: bool = False,
    wicket_kind: str | None = None,
) -> Delivery:
    pid1 = uuid4()
    pid2 = uuid4()
    return Delivery(
        innings_id=innings_id,
        season_year="2023",
        over_number=over_number,
        ball_in_over=ball_in_over,
        delivery_sequence=over_number * 6 + ball_in_over,
        batter_id=pid1,
        bowler_id=pid2,
        non_striker_id=uuid4(),
        runs_batter=runs_batter,
        runs_extras=runs_extras,
        runs_total=runs_batter + runs_extras,
        is_wide=is_wide,
        runs_wides=runs_extras if is_wide else 0,
        is_wicket=is_wicket,
        wicket_kind=wicket_kind,
        player_out_id=pid1 if is_wicket else None,
        is_bowler_credited_wicket=bool(wicket_kind and wicket_kind in ("bowled", "caught", "lbw")),
    )


def test_reconcile_innings_deliveries_perfect_match(dq_service: DataQualityReconciliationService):
    """Test reconciliation passes when deliveries aggregate matches innings scorecard."""
    match_id = uuid4()
    inn_id = uuid4()

    innings = Innings(
        innings_id=inn_id,
        match_id=match_id,
        innings_number=1,
        batting_team_id=uuid4(),
        bowling_team_id=uuid4(),
        total_runs=10,
        total_extras=2,
        total_wickets=1,
        total_legal_deliveries=3,
    )

    # 4 deliveries: 3 legal (1 run each + 1 wicket), 1 wide (2 extras) -> total 5 runs? Wait:
    # Let's make totals: 3 legal with (runs_batter: 2, 3, 3) + 1 wide (runs_extras: 2, runs_batter: 0) = total 10 runs
    delivs = [
        make_delivery(inn_id, 0, 1, runs_batter=2, runs_extras=0),
        make_delivery(inn_id, 0, 2, runs_batter=0, runs_extras=2, is_wide=True),
        make_delivery(inn_id, 0, 3, runs_batter=3, runs_extras=0),
        make_delivery(inn_id, 0, 4, runs_batter=3, runs_extras=0, is_wicket=True, wicket_kind="bowled"),
    ]

    dq_service.register_innings(innings, delivs)
    result = dq_service.reconcile_innings_deliveries(str(inn_id))

    assert result["found"] is True
    assert result["is_reconciled"] is True
    assert result["runs"]["match"] is True
    assert result["extras"]["match"] is True
    assert result["wickets"]["match"] is True
    assert result["legal_balls"]["match"] is True


def test_reconcile_innings_deliveries_discrepancy(dq_service: DataQualityReconciliationService):
    """Test reconciliation flags discrepancy when delivery total runs differ from innings."""
    match_id = uuid4()
    inn_id = uuid4()

    innings = Innings(
        innings_id=inn_id,
        match_id=match_id,
        innings_number=1,
        batting_team_id=uuid4(),
        bowling_team_id=uuid4(),
        total_runs=15,  # Mismatched expected total
        total_extras=0,
        total_wickets=0,
        total_legal_deliveries=2,
    )

    delivs = [
        make_delivery(inn_id, 0, 1, runs_batter=4),
        make_delivery(inn_id, 0, 2, runs_batter=6),
    ]

    dq_service.register_innings(innings, delivs)
    result = dq_service.reconcile_innings_deliveries(str(inn_id))

    assert result["found"] is True
    assert result["is_reconciled"] is False
    assert result["runs"]["match"] is False
    assert result["runs"]["innings_total"] == 15
    assert result["runs"]["deliveries_sum"] == 10


def test_validate_invariants_deliveries(dq_service: DataQualityReconciliationService):
    """Test delivery relational invariants validation."""
    valid_record = {
        "runs_batter": 4,
        "runs_extras": 0,
        "runs_total": 4,
        "is_wicket": False,
        "player_out_id": None,
    }
    assert dq_service.validate_invariants("deliveries", [valid_record]) is True

    # Invariant failure: runs_total != runs_batter + runs_extras
    invalid_record = {
        "runs_batter": 4,
        "runs_extras": 1,
        "runs_total": 4,
        "is_wicket": False,
        "player_out_id": None,
    }
    assert dq_service.validate_invariants("deliveries", [invalid_record]) is False

    # Invariant failure: player_out_id set when is_wicket is False
    ghost_record = {
        "runs_batter": 0,
        "runs_extras": 0,
        "runs_total": 0,
        "is_wicket": False,
        "player_out_id": str(uuid4()),
    }
    assert dq_service.validate_invariants("deliveries", [ghost_record]) is False


def test_validate_invariants_batting_innings(dq_service: DataQualityReconciliationService):
    """Test batting innings invariant validation (e.g. DNB rules)."""
    valid_dnb = {"did_not_bat": True, "balls_faced": 0, "dot_balls_faced": 0}
    assert dq_service.validate_invariants("batting_innings", [valid_dnb]) is True

    invalid_dnb = {"did_not_bat": True, "balls_faced": 5, "dot_balls_faced": 2}
    assert dq_service.validate_invariants("batting_innings", [invalid_dnb]) is False

    invalid_dots = {"did_not_bat": False, "balls_faced": 10, "dot_balls_faced": 12}
    assert dq_service.validate_invariants("batting_innings", [invalid_dots]) is False


def test_validate_invariants_matches(dq_service: DataQualityReconciliationService):
    """Test match invariants (home_team != away_team)."""
    tid1 = str(uuid4())
    tid2 = str(uuid4())
    assert dq_service.validate_invariants("matches", [{"home_team_id": tid1, "away_team_id": tid2}]) is True
    assert dq_service.validate_invariants("matches", [{"home_team_id": tid1, "away_team_id": tid1}]) is False
