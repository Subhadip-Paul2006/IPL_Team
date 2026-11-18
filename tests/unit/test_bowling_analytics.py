"""Unit tests for CPPAE Bowling Analytics Engine (W01–W12, BWPS & HLES)."""

from uuid import uuid4

from src.cmie.match_context import PreDeliveryState
from src.cppae.bowling_engine import BowlingEngine


def test_bowling_five_ball_vs_six_ball_economy_and_overs_display():
    """Verify W01 overs display and W06 economy rate with five-ball vs six-ball semantics."""
    pid = uuid4()

    # 17 legal balls, 20 runs conceded
    delivs = []
    for i in range(17):
        r = 2 if i < 10 else 0
        delivs.append({"match_id": "M1", "bowler_id": str(pid), "striker_id": "S1", "runs": r, "extras_type": "None", "is_wicket": "false"})

    # Six-ball format (T20)
    engine_t20 = BowlingEngine(balls_per_over=6)
    prof_t20 = engine_t20.calculate_profile(player_id=pid, deliveries=delivs, format_tag="T20")

    # W01 display: 17 // 6 = 2, 17 % 6 = 5 -> "2.5"
    assert prof_t20.overs_display == "2.5"
    # W06 economy: (20 / 17) * 6 = 7.06
    assert prof_t20.economy_rate == 7.06

    # Five-ball format (The Hundred)
    engine_hnd = BowlingEngine(balls_per_over=5)
    prof_hnd = engine_hnd.calculate_profile(player_id=pid, deliveries=delivs, format_tag="HUNDRED")

    # W01 display: 17 // 5 = 3, 17 % 5 = 2 -> "3.2" (DATA_DICTIONARY W01)
    assert prof_hnd.overs_display == "3.2"
    # W06 economy: (20 / 17) * 5 = 5.88 (NOT inflated by * 6.0)
    assert prof_hnd.economy_rate == 5.88


def test_bowling_null_safety_zero_wickets_and_zero_balls():
    """Verify zero-denominator null safety: 0 wickets -> NULL avg/sr; 0 balls -> NULL econ/dot%."""
    engine = BowlingEngine()
    pid = uuid4()

    # Bowler bowled 12 legal balls, conceded 15 runs, took 0 wickets
    delivs = []
    for _ in range(12):
        delivs.append({"match_id": "M1", "bowler_id": str(pid), "striker_id": "S1", "runs": 1, "extras_type": "None", "is_wicket": "false"})

    profile = engine.calculate_profile(player_id=pid, deliveries=delivs)

    assert profile.legal_balls_bowled == 12
    assert profile.wickets_taken == 0
    # Average and strike rate must be None (NULL)
    assert profile.bowling_average is None
    assert profile.bowling_strike_rate is None
    assert profile.economy_rate is not None

    # Zero balls bowled
    empty_profile = engine.calculate_profile(player_id=pid, deliveries=[])
    assert empty_profile.legal_balls_bowled == 0
    assert empty_profile.economy_rate is None
    assert empty_profile.bowling_average is None
    assert empty_profile.bowling_strike_rate is None
    assert empty_profile.dot_pct is None


def test_bowling_byes_and_runouts_excluded():
    """Verify byes/leg-byes excluded from runs conceded and runouts excluded from wickets."""
    engine = BowlingEngine()
    pid = uuid4()

    delivs = [
        # Delivery 1: 4 byes (runs=0, extras_type=byes, extras_2_runs=4)
        {"match_id": "M1", "bowler_id": str(pid), "striker_id": "S1", "runs": 0, "extras_type": "byes", "extras_2_runs": 4, "is_wicket": "false"},
        # Delivery 2: 4 runs off bat
        {"match_id": "M1", "bowler_id": str(pid), "striker_id": "S1", "runs": 4, "extras_type": "None", "is_wicket": "false"},
        # Delivery 3: Run out (should NOT credit to bowler!)
        {"match_id": "M1", "bowler_id": str(pid), "striker_id": "S1", "runs": 0, "extras_type": "None", "is_wicket": "true", "dismissal_type": "run out", "dismissed_player_id": "S1"},
        # Delivery 4: Bowled (credits to bowler!)
        {"match_id": "M1", "bowler_id": str(pid), "striker_id": "S1", "runs": 0, "extras_type": "None", "is_wicket": "true", "dismissal_type": "bowled", "dismissed_player_id": "S1"},
    ]

    profile = engine.calculate_profile(player_id=pid, deliveries=delivs)

    # Runs conceded should be exactly 4 (byes excluded!)
    assert profile.runs_conceded == 4
    # Bowler credited wickets should be 1, NOT 2 (run out excluded!)
    assert profile.wickets_taken == 1
    assert profile.bowler_credited_wickets == 1


def test_hles_t20_vs_non_t20_deferred():
    """Verify HLES is calculated for T20 but retained as DEFERRED for non-T20."""
    pid = uuid4()
    delivs = [
        {"match_id": "M1", "bowler_id": str(pid), "striker_id": "S1", "runs": 0, "extras_type": "None", "is_wicket": "true", "dismissal_type": "bowled", "dismissed_player_id": "S1"},
        {"match_id": "M1", "bowler_id": str(pid), "striker_id": "S1", "runs": 0, "extras_type": "None", "is_wicket": "false"},
    ]
    states = [
        PreDeliveryState(match_id="M1", innings=1, overid=19, over_ball_num=1, innings_ball_num=1, striker_id="S1", bowler_id=str(pid), legal_balls_bowled=0, legal_balls_remaining=2, current_runs=160.0, current_wickets=8, wickets_in_hand=2, crr=8.4, cdpi=0.85, mpt="EXTREME", is_pressure=True),
        PreDeliveryState(match_id="M1", innings=1, overid=19, over_ball_num=2, innings_ball_num=2, striker_id="S1", bowler_id=str(pid), legal_balls_bowled=1, legal_balls_remaining=1, current_runs=160.0, current_wickets=9, wickets_in_hand=1, crr=8.4, cdpi=0.85, mpt="EXTREME", is_pressure=True),
    ]

    # In T20: HLES = (2*1 + 1*2) / 2 = 2.0
    engine = BowlingEngine()
    prof_t20 = engine.calculate_profile(player_id=pid, deliveries=delivs, states=states, format_tag="T20")
    assert prof_t20.hles is not None
    assert prof_t20.hles == 2.0

    # In ODI / The Hundred: HLES is DEFERRED per TRD Invariant R8
    prof_hnd = engine.calculate_profile(player_id=pid, deliveries=delivs, states=states, format_tag="HUNDRED")
    assert prof_hnd.hles is None


def test_bowling_speed_and_line_length_metrics():
    """Verify W11 delivery speed and W12 line/length pitch coordinate tracking."""
    engine = BowlingEngine()
    pid = uuid4()

    delivs = [
        # Speed: 142.5 kph, Good Length, Stumps
        {"match_id": "M1", "bowler_id": str(pid), "striker_id": "S1", "runs": 0, "extras_type": "None", "ball_speed_kph": 142.5, "pitch_coordinate_x": 0.05, "pitch_coordinate_y": 6.2},
        # Speed: 138.0 kph, Yorker, Outside Off
        {"match_id": "M1", "bowler_id": str(pid), "striker_id": "S1", "runs": 0, "extras_type": "None", "ball_speed_kph": 138.0, "pitch_coordinate_x": 0.65, "pitch_coordinate_y": 1.8},
        # Untracked speed and coordinates
        {"match_id": "M1", "bowler_id": str(pid), "striker_id": "S1", "runs": 1, "extras_type": "None", "ball_speed_kph": None, "pitch_coordinate_x": None, "pitch_coordinate_y": None},
    ]

    profile = engine.calculate_profile(player_id=pid, deliveries=delivs)

    # W11 Speed summary
    assert profile.speed_summary is not None
    assert profile.speed_summary.recorded_balls == 2
    assert profile.speed_summary.total_balls == 3
    assert profile.speed_summary.coverage_pct == 66.67
    assert profile.speed_summary.min_speed_kph == 138.0
    assert profile.speed_summary.max_speed_kph == 142.5
    assert profile.speed_summary.mean_speed_kph == 140.2

    # W12 Line and Length
    assert profile.line_length_summary is not None
    assert profile.line_length_summary.tracked_balls == 2
    assert profile.line_length_summary.coverage_pct == 66.67
    assert profile.line_length_summary.length_buckets["Yorker"] == 1
    assert profile.line_length_summary.length_buckets["Good Length"] == 1
    assert profile.line_length_summary.line_buckets["Outside Off"] == 1
    assert profile.line_length_summary.line_buckets["Stumps"] == 1


def test_bowling_speed_and_coordinates_sanitization_boundaries():
    """Verify that impossible speeds (>165 or <=0) and invalid coordinates are rejected."""
    engine = BowlingEngine()
    pid = uuid4()

    delivs = [
        # Impossible speed: 250 kph (sensor spike) -> must be rejected
        {"match_id": "M1", "bowler_id": str(pid), "striker_id": "S1", "runs": 0, "extras_type": "None", "ball_speed_kph": 250.0},
        # Impossible speed: -10 kph -> must be rejected
        {"match_id": "M1", "bowler_id": str(pid), "striker_id": "S1", "runs": 0, "extras_type": "None", "ball_speed_kph": -10.0},
        # Valid speed: 135.0 kph
        {"match_id": "M1", "bowler_id": str(pid), "striker_id": "S1", "runs": 0, "extras_type": "None", "ball_speed_kph": 135.0},
        # Impossible pitch coordinate: y = -5.0 (behind stumps)
        {"match_id": "M1", "bowler_id": str(pid), "striker_id": "S1", "runs": 0, "extras_type": "None", "pitch_coordinate_x": 0.0, "pitch_coordinate_y": -5.0},
        # Impossible pitch coordinate: y = 45.0 (beyond pitch length)
        {"match_id": "M1", "bowler_id": str(pid), "striker_id": "S1", "runs": 0, "extras_type": "None", "pitch_coordinate_x": 0.0, "pitch_coordinate_y": 45.0},
        # Valid coordinates: x = 0.1, y = 5.5 (Good Length, Stumps)
        {"match_id": "M1", "bowler_id": str(pid), "striker_id": "S1", "runs": 0, "extras_type": "None", "pitch_coordinate_x": 0.1, "pitch_coordinate_y": 5.5},
    ]

    profile = engine.calculate_profile(player_id=pid, deliveries=delivs)

    # Speed: only the 135.0 delivery is accepted
    assert profile.speed_summary is not None
    assert profile.speed_summary.recorded_balls == 1
    assert profile.speed_summary.mean_speed_kph == 135.0

    # Line/length: only the 1 valid delivery is counted
    assert profile.line_length_summary is not None
    assert profile.line_length_summary.tracked_balls == 1
    assert profile.line_length_summary.length_buckets["Good Length"] == 1
