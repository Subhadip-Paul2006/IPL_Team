"""Unit tests for CPPAE Batting Analytics Engine (B01–B17 & BPPS)."""

from uuid import uuid4

from src.cmie.match_context import PreDeliveryState
from src.contracts.scorecard import BattingInnings
from src.cppae.batting_engine import BattingEngine


def test_batting_engine_b01_to_b09_and_null_safety():
    """Verify B01-B09 career aggregation and zero-sample NULL rules."""
    engine = BattingEngine()
    pid = uuid4()
    mid1 = "MATCH_1"
    mid2 = "MATCH_2"

    deliveries = [
        # Match 1: 5 balls faced: 4, 0, 6, 1, 0 -> 11 runs, 1 four, 1 six, 2 dots, 0 dismissals
        {"match_id": mid1, "striker_id": str(pid), "bowler_id": "BOWL_1", "runs": 4, "extras_type": "None", "is_wicket": "false", "dismissal_type": ""},
        {"match_id": mid1, "striker_id": str(pid), "bowler_id": "BOWL_1", "runs": 0, "extras_type": "None", "is_wicket": "false", "dismissal_type": ""},
        {"match_id": mid1, "striker_id": str(pid), "bowler_id": "BOWL_1", "runs": 6, "extras_type": "None", "is_wicket": "false", "dismissal_type": ""},
        {"match_id": mid1, "striker_id": str(pid), "bowler_id": "BOWL_1", "runs": 1, "extras_type": "None", "is_wicket": "false", "dismissal_type": ""},
        {"match_id": mid1, "striker_id": str(pid), "bowler_id": "BOWL_1", "runs": 0, "extras_type": "None", "is_wicket": "false", "dismissal_type": ""},
        # Match 2: 5 balls faced: 0, 4, 1, 0, 0 (wicket on 5th ball) -> 5 runs, 1 four, 3 dots, 1 dismissal
        {"match_id": mid2, "striker_id": str(pid), "bowler_id": "BOWL_2", "runs": 0, "extras_type": "None", "is_wicket": "false", "dismissal_type": ""},
        {"match_id": mid2, "striker_id": str(pid), "bowler_id": "BOWL_2", "runs": 4, "extras_type": "None", "is_wicket": "false", "dismissal_type": ""},
        {"match_id": mid2, "striker_id": str(pid), "bowler_id": "BOWL_2", "runs": 1, "extras_type": "None", "is_wicket": "false", "dismissal_type": ""},
        {"match_id": mid2, "striker_id": str(pid), "bowler_id": "BOWL_2", "runs": 0, "extras_type": "None", "is_wicket": "false", "dismissal_type": ""},
        {"match_id": mid2, "striker_id": str(pid), "bowler_id": "BOWL_2", "runs": 0, "extras_type": "None", "is_wicket": "true", "dismissal_type": "bowled", "dismissed_player_id": str(pid)},
    ]

    profile = engine.calculate_profile(
        player_id=pid,
        deliveries=deliveries,
        player_names={str(pid): "Test Batter"},
    )

    # B01 Matches
    assert profile.matches == 2
    # B03 Runs: 11 + 5 = 16
    assert profile.runs == 16
    # B04 Balls: 10
    assert profile.balls_faced == 10
    # B05 Average: 16 / 1 = 16.0
    assert profile.batting_average == 16.0
    # B06 Strike Rate: 16 / 10 * 100 = 160.0
    assert profile.strike_rate == 160.0
    # B07 Boundaries: 2 fours, 1 six = 3 boundaries
    assert profile.fours == 2
    assert profile.sixes == 1
    assert profile.boundaries == 3
    # B08 Boundary %: (2*4 + 1*6) / 16 * 100 = 14 / 16 * 100 = 87.5
    assert profile.boundary_pct == 87.5
    # B09 Dot-ball %: 5 dots / 10 balls * 100 = 50.0
    assert profile.dot_balls == 5
    assert profile.dot_pct == 50.0


def test_batting_undefeated_option_b_preservation():
    """Verify that an undefeated batter strictly gets NULL average and Option B BPPS."""
    engine = BattingEngine()
    pid = uuid4()

    deliveries = [
        {"match_id": "M1", "striker_id": str(pid), "bowler_id": "B1", "runs": 4, "extras_type": "None", "is_wicket": "false", "dismissal_type": ""},
        {"match_id": "M1", "striker_id": str(pid), "bowler_id": "B1", "runs": 6, "extras_type": "None", "is_wicket": "false", "dismissal_type": ""},
        {"match_id": "M1", "striker_id": str(pid), "bowler_id": "B1", "runs": 1, "extras_type": "None", "is_wicket": "false", "dismissal_type": ""},
    ]

    states = [
        PreDeliveryState(match_id="M1", innings=1, overid=1, over_ball_num=1, innings_ball_num=1, striker_id=str(pid), bowler_id="B1", legal_balls_bowled=0, legal_balls_remaining=120, current_runs=0.0, current_wickets=0, wickets_in_hand=10, crr=0.0, cdpi=0.8, mpt="HIGH", is_pressure=True),
        PreDeliveryState(match_id="M1", innings=1, overid=1, over_ball_num=2, innings_ball_num=2, striker_id=str(pid), bowler_id="B1", legal_balls_bowled=1, legal_balls_remaining=119, current_runs=4.0, current_wickets=0, wickets_in_hand=10, crr=0.0, cdpi=0.8, mpt="HIGH", is_pressure=True),
        PreDeliveryState(match_id="M1", innings=1, overid=1, over_ball_num=3, innings_ball_num=3, striker_id=str(pid), bowler_id="B1", legal_balls_bowled=2, legal_balls_remaining=118, current_runs=10.0, current_wickets=0, wickets_in_hand=10, crr=0.0, cdpi=0.8, mpt="HIGH", is_pressure=True),
    ]

    profile = engine.calculate_profile(player_id=pid, deliveries=deliveries, states=states)

    assert profile.dismissals == 0
    # Average must strictly be None (NULL) per Decision 1 and domain rule
    assert profile.batting_average is None
    # Option B profile tag must be applied
    assert profile.profile_tag == "UNDEFEATED_IN_WINDOW"
    assert profile.bpps > 0.0


def test_batting_dnb_and_zero_ball_batted_distinction():
    """Verify DNB (did_not_bat=True) vs zero-ball batted appearance (did_not_bat=False, balls_faced=0)."""
    engine = BattingEngine()
    pid = uuid4()
    inns_id = uuid4()
    team_id = uuid4()

    innings = [
        BattingInnings(
            batting_innings_id=uuid4(),
            innings_id=inns_id,
            player_id=pid,
            team_id=team_id,
            did_not_bat=True,
            balls_faced=0,
            runs_scored=0,
            is_not_out=True,
        ),
        BattingInnings(
            batting_innings_id=uuid4(),
            innings_id=inns_id,
            player_id=pid,
            team_id=team_id,
            did_not_bat=False,
            balls_faced=0,
            runs_scored=0,
            is_not_out=False,  # timed out or walkover before facing a ball
        ),
    ]

    profile = engine.calculate_profile(
        player_id=pid,
        deliveries=[],
        batting_innings=innings,
    )

    assert profile.dnb_count == 1
    assert profile.zero_ball_batted_count == 1
    assert profile.innings == 1


def test_batting_phase_splits_and_the_hundred_boundaries():
    """Verify format-aware phase splits for T20 vs The Hundred."""
    engine = BattingEngine()
    pid = uuid4()

    # The Hundred: overs 0-4 (Powerplay), overs 5-17 (Middle), overs 18-19 (Death)
    deliveries_hundred = [
        {"match_id": "M_HND", "over_number": 4, "striker_id": str(pid), "bowler_id": "B1", "runs": 4, "extras_type": "None", "is_wicket": "false"},
        {"match_id": "M_HND", "over_number": 5, "striker_id": str(pid), "bowler_id": "B1", "runs": 1, "extras_type": "None", "is_wicket": "false"},
        {"match_id": "M_HND", "over_number": 18, "striker_id": str(pid), "bowler_id": "B1", "runs": 6, "extras_type": "None", "is_wicket": "false"},
    ]

    profile_hnd = engine.calculate_profile(
        player_id=pid,
        deliveries=deliveries_hundred,
        format_tag="HUNDRED",
    )

    assert profile_hnd.phase_splits["Powerplay"].balls_faced == 1
    assert profile_hnd.phase_splits["Powerplay"].runs_scored == 4
    assert profile_hnd.phase_splits["Middle"].balls_faced == 1
    assert profile_hnd.phase_splits["Middle"].runs_scored == 1
    assert profile_hnd.phase_splits["Death"].balls_faced == 1
    assert profile_hnd.phase_splits["Death"].runs_scored == 6


def test_batting_matchups_and_insufficient_sample():
    """Verify B13-B15 matchups, pace vs spin, and sample size warning flags."""
    engine = BattingEngine()
    pid = uuid4()
    pacer_id = "PACER_1"
    spinner_id = "SPINNER_1"

    deliveries = []
    # 25 balls vs pacer (sufficient sample >= 24)
    for _ in range(25):
        deliveries.append({"match_id": "M1", "striker_id": str(pid), "bowler_id": pacer_id, "runs": 2, "extras_type": "None", "is_wicket": "false"})
    # 10 balls vs spinner (insufficient sample < 24)
    for _ in range(10):
        deliveries.append({"match_id": "M1", "striker_id": str(pid), "bowler_id": spinner_id, "runs": 1, "extras_type": "None", "is_wicket": "false"})

    styles = {
        pacer_id: "Right-arm Fast",
        spinner_id: "Left-arm Orthodox",
    }

    profile = engine.calculate_profile(
        player_id=pid,
        deliveries=deliveries,
        bowling_styles=styles,
    )

    # Bowler matchups
    assert profile.bowler_matchups[pacer_id].balls == 25
    assert profile.bowler_matchups[pacer_id].warning_flag is None
    assert profile.bowler_matchups[spinner_id].balls == 10
    assert profile.bowler_matchups[spinner_id].warning_flag == "INSUFFICIENT_SAMPLE"

    # Pace vs Spin
    assert profile.pace_vs_spin["PACE"].balls == 25
    assert profile.pace_vs_spin["PACE"].warning_flag is None
    assert profile.pace_vs_spin["SPIN"].balls == 10
    assert profile.pace_vs_spin["SPIN"].warning_flag == "INSUFFICIENT_SAMPLE"


def test_batting_partnership_window_contiguous():
    """Verify B16 contiguous delivery window calculation without delivery attribution inference."""
    engine = BattingEngine()
    pid = uuid4()
    partner_a = "PARTNER_A"
    partner_b = "PARTNER_B"

    deliveries = [
        # Partnership with Partner A: 3 balls
        {"match_id": "M1", "innings": 1, "striker_id": str(pid), "non_striker_id": partner_a, "runs": 4, "extras_type": "None", "is_wicket": "false"},
        {"match_id": "M1", "innings": 1, "striker_id": partner_a, "non_striker_id": str(pid), "runs": 1, "extras_type": "None", "is_wicket": "false"},
        # Partner A is out on 3rd ball
        {"match_id": "M1", "innings": 1, "striker_id": partner_a, "non_striker_id": str(pid), "runs": 0, "extras_type": "None", "is_wicket": "true", "dismissed_player_id": partner_a},
        # Partner B arrives: 2 balls
        {"match_id": "M1", "innings": 1, "striker_id": str(pid), "non_striker_id": partner_b, "runs": 6, "extras_type": "None", "is_wicket": "false"},
        {"match_id": "M1", "innings": 1, "striker_id": partner_b, "non_striker_id": str(pid), "runs": 2, "extras_type": "None", "is_wicket": "false"},
    ]

    profile = engine.calculate_profile(player_id=pid, deliveries=deliveries)

    assert len(profile.partnerships) == 2
    # First partnership with Partner A: 4 (player) + 1 (partner) = 5
    assert profile.partnerships[0].partner_id == partner_a
    assert profile.partnerships[0].total_partnership_runs == 5
    assert profile.partnerships[0].unbroken is False

    # Second partnership with Partner B: 6 (player) + 2 (partner) = 8
    assert profile.partnerships[1].partner_id == partner_b
    assert profile.partnerships[1].total_partnership_runs == 8
    assert profile.partnerships[1].unbroken is True


def test_bowling_style_classification_and_unorthodox_wrist_spin():
    """Verify that slow bowling styles and unorthodox wrist spin are correctly classified."""
    from src.cppae.batting_engine import classify_bowling_style, normalize_style_group

    # Slow bowling classifications
    assert classify_bowling_style("Slow Left-Arm") == "SPIN"
    assert classify_bowling_style("Slow Left Arm") == "SPIN"
    assert classify_bowling_style("Slow Left-Arm Orthodox") == "SPIN"

    # Unorthodox wrist spinners (Kuldeep Yadav / Tabraiz Shamsi) must NOT be classified as Orthodox
    assert normalize_style_group("Slow left-arm unorthodox") == "Left-arm Wrist Spin"
    assert normalize_style_group("Left-arm unorthodox") == "Left-arm Wrist Spin"
    assert normalize_style_group("Left-arm chinaman") == "Left-arm Wrist Spin"

    # Finger spin
    assert normalize_style_group("Slow Left-Arm") == "Left-arm Orthodox"
    assert normalize_style_group("Left-arm orthodox") == "Left-arm Orthodox"


def test_batting_partnership_window_disordered_deliveries():
    """Verify partnership calculation produces correct results even if deliveries are passed out-of-order."""
    engine = BattingEngine()
    pid = uuid4()
    partner_a = "PARTNER_A"

    # Deliveries shuffled: over 1 ball 2, then over 0 ball 1, etc.
    deliveries = [
        {"match_id": "M1", "innings": 1, "over_number": 1, "delivery_sequence": 8, "striker_id": partner_a, "non_striker_id": str(pid), "runs": 1, "extras_type": "None", "is_wicket": "false"},
        {"match_id": "M1", "innings": 1, "over_number": 0, "delivery_sequence": 1, "striker_id": str(pid), "non_striker_id": partner_a, "runs": 4, "extras_type": "None", "is_wicket": "false"},
        {"match_id": "M1", "innings": 1, "over_number": 1, "delivery_sequence": 9, "striker_id": partner_a, "non_striker_id": str(pid), "runs": 0, "extras_type": "None", "is_wicket": "true", "dismissal_type": "bowled", "dismissed_player_id": partner_a},
    ]

    profile = engine.calculate_profile(player_id=pid, deliveries=deliveries)

    assert len(profile.partnerships) == 1
    assert profile.partnerships[0].partner_id == partner_a
    assert profile.partnerships[0].total_partnership_runs == 5
    assert profile.partnerships[0].balls_faced == 1  # 1 ball faced by pid
    assert profile.partnerships[0].unbroken is False
