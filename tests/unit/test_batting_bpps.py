"""Unit tests for CPPAE Batting Performance and BPPS calculation (Workstream E)."""

from src.cmie.match_context import PreDeliveryState
from src.cppae.batting_performance import BattingPerformanceEngine


def test_batting_performance_bpps_and_shrinkage():
    """Verify batting BPPS calculation, Empirical Bayes shrinkage, and qualification gates."""
    engine = BattingPerformanceEngine(k_bat=30.0)

    # Synthetic player with 150 total balls faced, 50 pressure balls, 12 matches
    deliveries = []
    states = []

    # 100 non-pressure balls: 150 runs (SR 150)
    for i in range(100):
        deliveries.append({"runs": "2" if i % 2 == 0 else "1", "extras_type": "None", "is_wicket": "false", "dismissed_player_id": ""})
        states.append(PreDeliveryState(
            match_id=f"M_{i // 10}", innings=1, overid=1, over_ball_num=1, innings_ball_num=i,
            striker_id="BAT_1", bowler_id="B1", legal_balls_bowled=i, legal_balls_remaining=120 - i,
            current_runs=float(i * 1.5), current_wickets=0, wickets_in_hand=10, crr=9.0, cdpi=0.30, mpt="LOW", is_pressure=False
        ))

    # 50 pressure balls: 100 runs (Raw Press SR 200, 10 fours, 5 sixes, 1 dismissal)
    for i in range(50):
        runs = "4" if i < 10 else ("6" if i < 15 else "1")
        is_w = "true" if i == 49 else "false"
        d_type = "bowled" if is_w == "true" else ""
        deliveries.append({"runs": runs, "extras_type": "None", "is_wicket": is_w, "dismissal_type": d_type, "dismissed_player_id": "BAT_1" if is_w == "true" else ""})
        states.append(PreDeliveryState(
            match_id=f"M_{10 + (i // 5)}", innings=2, overid=18, over_ball_num=1, innings_ball_num=i,
            striker_id="BAT_1", bowler_id="B1", legal_balls_bowled=100 + i, legal_balls_remaining=20 - (i % 20),
            current_runs=150.0 + float(i * 2), current_wickets=5, wickets_in_hand=5, crr=9.0, cdpi=0.75, mpt="HIGH", is_pressure=True
        ))

    names = {"BAT_1": "Elite Finisher"}
    appearances = {"BAT_1": 15}

    results = engine.calculate_metrics(deliveries, states, names, appearances, min_balls_faced=120, min_pressure_balls=40, min_matches=10)
    assert len(results) == 1

    r = results[0]
    assert r.player_id == "BAT_1"
    assert r.is_qualified is True
    assert r.balls_faced_total == 150
    assert r.balls_faced_pressure == 50
    assert r.sr_pressure_raw is not None and r.sr_pressure_raw > 150.0
    # Shrunk SR should be pulled slightly towards prior but remain strong
    assert r.sr_pressure_shrunk is not None
    assert 0.0 <= r.bpps <= 100.0


def test_batting_under_threshold_is_not_qualified():
    """Verify player with insufficient volume fails eligibility gate."""
    engine = BattingPerformanceEngine(k_bat=30.0)
    deliveries = [{"runs": "1", "extras_type": "None", "is_wicket": "false", "dismissed_player_id": ""}]
    states = [PreDeliveryState(
        match_id="M1", innings=1, overid=1, over_ball_num=1, innings_ball_num=1,
        striker_id="LOW_VOL", bowler_id="B1", legal_balls_bowled=0, legal_balls_remaining=120,
        current_runs=0.0, current_wickets=0, wickets_in_hand=10, crr=0.0, cdpi=0.85, mpt="EXTREME", is_pressure=True
    )]
    results = engine.calculate_metrics(deliveries, states, {"LOW_VOL": "Low Volume"}, {"LOW_VOL": 1})
    assert len(results) == 1
    assert results[0].is_qualified is False


def test_non_striker_run_out_credited_to_non_striker():
    """Verify non-striker run out is credited to dismissed batsman, not striker."""
    engine = BattingPerformanceEngine(k_bat=30.0)
    deliveries = [
        # Ball 1: Striker S1 faces, non-striker NS1 is run out!
        {
            "runs": "1",
            "extras_type": "None",
            "is_wicket": "true",
            "dismissal_type": "run out",
            "dismissed_player_id": "NS1",
        },
    ]
    states = [
        PreDeliveryState(
            match_id="M1", innings=2, overid=19, over_ball_num=1, innings_ball_num=115,
            striker_id="S1", bowler_id="B1", legal_balls_bowled=114, legal_balls_remaining=6,
            current_runs=150.0, current_wickets=4, wickets_in_hand=6, crr=7.8, cdpi=0.85, mpt="EXTREME", is_pressure=True
        ),
    ]
    results = engine.calculate_metrics(
        deliveries, states, {"S1": "Striker", "NS1": "Non Striker"}, {"S1": 15, "NS1": 15}
    )
    s1_res = next(r for r in results if r.player_id == "S1")
    ns1_res = next(r for r in results if r.player_id == "NS1")

    # Striker faced 1 ball, scored 1 run, NOT dismissed
    assert s1_res.balls_faced_total == 1
    assert s1_res.dismissals_pressure == 0

    # Non-striker faced 0 balls, but WAS dismissed under pressure
    assert ns1_res.balls_faced_total == 0
    assert ns1_res.dismissals_pressure == 1
