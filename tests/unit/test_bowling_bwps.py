"""Unit tests for CPPAE Bowling Performance and BWPS calculation (Workstream F)."""

from src.cmie.match_context import PreDeliveryState
from src.cppae.bowling_performance import BowlingPerformanceEngine


def test_bowling_performance_bwps_and_hles():
    """Verify bowling BWPS calculation, HLES score, and bowler wicket credit."""
    engine = BowlingPerformanceEngine(k_bowl=40.0)

    deliveries = []
    states = []

    # 100 non-pressure balls: 120 runs, 5 wickets
    for i in range(100):
        is_w = "true" if i % 20 == 0 else "false"
        deliveries.append({"runs": "1", "extras_type": "None", "is_wicket": is_w, "dismissal_type": "caught" if is_w == "true" else ""})
        states.append(PreDeliveryState(
            match_id=f"M_{i // 10}", innings=1, overid=5, over_ball_num=1, innings_ball_num=i,
            striker_id="S1", bowler_id="BOWL_1", legal_balls_bowled=i, legal_balls_remaining=120 - i,
            current_runs=float(i * 1.2), current_wickets=0, wickets_in_hand=10, crr=7.2, cdpi=0.30, mpt="LOW", is_pressure=False
        ))

    # 50 pressure balls: 30 dots, 40 runs (Econ 4.8), 6 wickets (5 caught, 1 run out which should NOT credit bowler)
    for i in range(50):
        runs = "0" if i < 30 else "2"
        is_w = "true" if i in (10, 20, 30, 40, 45, 48) else "false"
        # Delivery 48 is a run-out: should NOT credit to bowler!
        d_type = "run out" if i == 48 else ("bowled" if is_w == "true" else "")
        deliveries.append({"runs": runs, "extras_type": "None", "is_wicket": is_w, "dismissal_type": d_type})
        states.append(PreDeliveryState(
            match_id=f"M_{10 + (i // 5)}", innings=2, overid=19, over_ball_num=1, innings_ball_num=i,
            striker_id="S1", bowler_id="BOWL_1", legal_balls_bowled=100 + i, legal_balls_remaining=20 - (i % 20),
            current_runs=150.0 + float(i * 1.5), current_wickets=6, wickets_in_hand=4, crr=8.0, cdpi=0.85, mpt="EXTREME", is_pressure=True
        ))

    names = {"BOWL_1": "Elite Death Bowler"}
    appearances = {"BOWL_1": 15}

    results = engine.calculate_metrics(deliveries, states, names, appearances, min_legal_balls=120, min_pressure_balls=36, min_matches=10)
    assert len(results) == 1

    r = results[0]
    assert r.player_id == "BOWL_1"
    assert r.is_qualified is True
    assert r.legal_balls_total == 150
    assert r.legal_balls_pressure == 50
    # Bowler credited wickets under pressure should be 5, NOT 6 (run out excluded!)
    assert r.wickets_pressure == 5
    assert r.econ_pressure_raw is not None and r.econ_pressure_raw < 6.0
    assert r.hles is not None and r.hles > 0.5
    assert 0.0 <= r.bwps <= 100.0


def test_bowler_byes_do_not_inflate_runs_conceded():
    """Verify byes and leg-byes are not attributed to bowler runs conceded (Rule R5 / P5)."""
    engine = BowlingPerformanceEngine(k_bowl=40.0)
    deliveries = [
        {"runs": "0", "extras_type": "byes", "extras_2_runs": "4", "is_wicket": "false", "dismissal_type": ""},
        {"runs": "0", "extras_type": "legbyes", "extras_2_runs": "1", "is_wicket": "false", "dismissal_type": ""},
    ]
    states = [
        PreDeliveryState(match_id="M1", innings=1, overid=1, over_ball_num=1, innings_ball_num=1, striker_id="S1", bowler_id="B1", legal_balls_bowled=0, legal_balls_remaining=120, current_runs=0.0, current_wickets=0, wickets_in_hand=10, crr=0.0, cdpi=0.70, mpt="HIGH", is_pressure=True),
        PreDeliveryState(match_id="M1", innings=1, overid=1, over_ball_num=2, innings_ball_num=2, striker_id="S1", bowler_id="B1", legal_balls_bowled=1, legal_balls_remaining=119, current_runs=5.0, current_wickets=0, wickets_in_hand=10, crr=0.0, cdpi=0.70, mpt="HIGH", is_pressure=True),
    ]
    results = engine.calculate_metrics(deliveries, states, {"B1": "Bowler 1"}, {"B1": 1})
    assert len(results) == 1
    # Runs conceded should be 0, not 5!
    assert results[0].runs_conceded_total == 0
    assert results[0].runs_conceded_pressure == 0
