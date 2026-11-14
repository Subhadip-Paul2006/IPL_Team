"""Unit tests for CPPAE Match Contribution Analytics (M01–M07)."""

from uuid import uuid4

from src.cmie.match_context import PreDeliveryState
from src.contracts.career import PlayerAward
from src.cppae.match_contribution import MatchContributionEngine


def test_match_contribution_m01_to_m07_t20():
    """Verify M01-M07 metrics in T20 format with measurable high-leverage and additive composite."""
    engine = MatchContributionEngine()
    pid = uuid4()
    pid_str = str(pid)

    awards = [
        PlayerAward(
            player_id=pid,
            award_type="Player of the Match",
        ),
        PlayerAward(
            player_id=pid,
            award_type="Player of the Match",
        ),
    ]

    # Match 1: Player scores 50 runs out of 150 team runs (M02 = 33.33%)
    # Bowler takes 2 wickets out of 5 team wickets (M03_w = 40.0%), concedes 25 runs out of 140 team runs
    deliveries = [
        # Innings 1: Batting
        {"match_id": "M1", "innings": 1, "striker_id": pid_str, "bowler_id": "OPP_B1", "runs": 50, "extras_type": "None", "batting_team_id": "TEAM_RR", "is_wicket": "false"},
        {"match_id": "M1", "innings": 1, "striker_id": "OTHER_BAT", "bowler_id": "OPP_B1", "runs": 100, "extras_type": "None", "batting_team_id": "TEAM_RR", "is_wicket": "false"},
        # Innings 2: Bowling
        {"match_id": "M1", "innings": 2, "striker_id": "OPP_BAT", "bowler_id": pid_str, "runs": 25, "extras_type": "None", "bowling_team_id": "TEAM_RR", "is_wicket": "true", "dismissal_type": "bowled", "dismissed_player_id": "OPP_BAT"},
        {"match_id": "M1", "innings": 2, "striker_id": "OPP_BAT2", "bowler_id": pid_str, "runs": 0, "extras_type": "None", "bowling_team_id": "TEAM_RR", "is_wicket": "true", "dismissal_type": "caught", "dismissed_player_id": "OPP_BAT2"},
        {"match_id": "M1", "innings": 2, "striker_id": "OPP_BAT3", "bowler_id": "OTHER_BOWL", "runs": 115, "extras_type": "None", "bowling_team_id": "TEAM_RR", "is_wicket": "true", "dismissal_type": "bowled", "dismissed_player_id": "OPP_BAT3"},
        {"match_id": "M1", "innings": 2, "striker_id": "OPP_BAT4", "bowler_id": "OTHER_BOWL", "runs": 0, "extras_type": "None", "bowling_team_id": "TEAM_RR", "is_wicket": "true", "dismissal_type": "bowled", "dismissed_player_id": "OPP_BAT4"},
        {"match_id": "M1", "innings": 2, "striker_id": "OPP_BAT5", "bowler_id": "OTHER_BOWL", "runs": 0, "extras_type": "None", "bowling_team_id": "TEAM_RR", "is_wicket": "true", "dismissal_type": "bowled", "dismissed_player_id": "OPP_BAT5"},
    ]

    states = [
        PreDeliveryState(match_id="M1", innings=1, overid=5, over_ball_num=1, innings_ball_num=25, striker_id=pid_str, bowler_id="OPP_B1", legal_balls_bowled=24, legal_balls_remaining=96, current_runs=40.0, current_wickets=1, wickets_in_hand=9, crr=10.0, cdpi=0.75, mpt="HIGH", is_pressure=True),
        PreDeliveryState(match_id="M1", innings=1, overid=15, over_ball_num=1, innings_ball_num=85, striker_id="OTHER_BAT", bowler_id="OPP_B1", legal_balls_bowled=84, legal_balls_remaining=36, current_runs=100.0, current_wickets=2, wickets_in_hand=8, crr=7.1, cdpi=0.50, mpt="LOW", is_pressure=False),
        PreDeliveryState(match_id="M1", innings=2, overid=18, over_ball_num=1, innings_ball_num=102, striker_id="OPP_BAT", bowler_id=pid_str, legal_balls_bowled=101, legal_balls_remaining=19, current_runs=120.0, current_wickets=2, wickets_in_hand=8, crr=7.1, cdpi=0.85, mpt="EXTREME", is_pressure=True),
        PreDeliveryState(match_id="M1", innings=2, overid=18, over_ball_num=2, innings_ball_num=103, striker_id="OPP_BAT2", bowler_id=pid_str, legal_balls_bowled=102, legal_balls_remaining=18, current_runs=120.0, current_wickets=3, wickets_in_hand=7, crr=7.0, cdpi=0.85, mpt="EXTREME", is_pressure=True),
        PreDeliveryState(match_id="M1", innings=2, overid=19, over_ball_num=1, innings_ball_num=108, striker_id="OPP_BAT3", bowler_id="OTHER_BOWL", legal_balls_bowled=107, legal_balls_remaining=13, current_runs=130.0, current_wickets=4, wickets_in_hand=6, crr=7.2, cdpi=0.80, mpt="HIGH", is_pressure=True),
        PreDeliveryState(match_id="M1", innings=2, overid=19, over_ball_num=2, innings_ball_num=109, striker_id="OPP_BAT4", bowler_id="OTHER_BOWL", legal_balls_bowled=108, legal_balls_remaining=12, current_runs=130.0, current_wickets=5, wickets_in_hand=5, crr=7.2, cdpi=0.80, mpt="HIGH", is_pressure=True),
        PreDeliveryState(match_id="M1", innings=2, overid=19, over_ball_num=3, innings_ball_num=110, striker_id="OPP_BAT5", bowler_id="OTHER_BOWL", legal_balls_bowled=109, legal_balls_remaining=11, current_runs=130.0, current_wickets=6, wickets_in_hand=4, crr=7.1, cdpi=0.80, mpt="HIGH", is_pressure=True),
    ]

    matches = [
        {"match_id": "M1", "winner_id": "TEAM_RR", "outcome_type": "runs"}
    ]

    profile = engine.calculate_profile(
        player_id=pid,
        deliveries=deliveries,
        states=states,
        matches=matches,
        player_awards=awards,
        format_tag="T20",
    )

    # M01 POTM
    assert profile.player_of_match_awards == 2

    # M02 Batting contribution: 50 / 150 * 100 = 33.33%
    assert profile.batting_contribution_pct == 33.33

    # M03 Bowling contribution: 2 / 5 * 100 = 40.0% wickets
    assert profile.bowling_wicket_share_pct == 40.0
    # M03 Bowling run suppression: 25 / 140 * 100 = 17.86%
    assert profile.bowling_run_suppression_pct == 17.86

    # M04 Situation context
    assert profile.situation_context["batting_first_innings"] == 1
    assert profile.situation_context["bowling_second_innings"] == 1

    # M05 Win/loss performance
    assert profile.win_loss_performance["wins"]["matches"] == 1
    assert profile.win_loss_performance["wins"]["runs"] == 50
    assert profile.win_loss_performance["wins"]["wickets"] == 2

    # M06 Measurable high leverage in T20 (calibrated)
    assert profile.high_leverage_contribution["status"] == "DERIVED"
    assert profile.high_leverage_contribution["high_leverage_runs"] == 50
    assert profile.high_leverage_contribution["high_leverage_wickets"] == 2

    # M07 Additive composite = M02 + M03 = 33.33 + 40.0 = 73.33 (no arbitrary weights applied)
    assert profile.additive_composite == 73.33

    # M07 Per match composite records
    assert "M1" in profile.per_match_composite
    assert profile.per_match_composite["M1"]["m02"] == 33.33
    assert profile.per_match_composite["M1"]["m03_w"] == 40.0
    assert profile.per_match_composite["M1"]["m07"] == 73.33


def test_match_contribution_m06_non_t20_deferred():
    """Verify M06 high-leverage thresholds are preserved as DEFERRED for non-T20."""
    engine = MatchContributionEngine()
    pid = uuid4()

    profile_hnd = engine.calculate_profile(
        player_id=pid,
        deliveries=[],
        format_tag="HUNDRED",
    )

    # Must be DEFERRED per Decision 3 / TRD Invariant R8
    assert profile_hnd.high_leverage_contribution["status"] == "DEFERRED"
    assert profile_hnd.high_leverage_contribution["high_leverage_runs"] is None
