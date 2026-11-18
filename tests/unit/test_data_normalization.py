"""Unit tests for data semantics and normalization (Workstream B)."""

from src.ingestion.normalizer import (
    EXTRAS1_ENUM,
    is_ball_faced,
    is_bowler_credited_wicket,
    is_ghost_dismissal,
    is_legal_ball,
    is_valid_wicket,
    parse_revised_balls,
    parse_runs_breakdown,
    sanitize_bowl_speed,
)


def test_extras1_enum_mapping():
    """Verify extras1_runs enum dictionary mapping."""
    assert EXTRAS1_ENUM["1"] == "Overstep"
    assert EXTRAS1_ENUM["2"] == "wide"
    assert EXTRAS1_ENUM["3"] == "legbyes"
    assert EXTRAS1_ENUM["4"] == "byes"
    assert EXTRAS1_ENUM["5"] == "other"
    assert EXTRAS1_ENUM["6"] == "None"
    assert EXTRAS1_ENUM["7"] == "Penalty"


def test_sanitize_bowl_speed():
    """Verify bowl_speed sanitization: <=0 or >165 km/h become None (R1)."""
    assert sanitize_bowl_speed(None) is None
    assert sanitize_bowl_speed("") is None
    assert sanitize_bowl_speed("0") is None
    assert sanitize_bowl_speed("-1.0") is None
    assert sanitize_bowl_speed("165.1") is None
    assert sanitize_bowl_speed("1456.1") is None
    assert sanitize_bowl_speed("corrupt") is None
    assert sanitize_bowl_speed("142.5") == 142.5
    assert sanitize_bowl_speed("165.0") == 165.0
    assert sanitize_bowl_speed(138.2) == 138.2


def test_parse_revised_balls():
    """Verify revised overs parsed as integer balls."""
    assert parse_revised_balls(None) is None
    assert parse_revised_balls("") is None
    assert parse_revised_balls("114.0") == 114
    assert parse_revised_balls("90") == 90
    assert parse_revised_balls("30.0") == 30
    assert parse_revised_balls("invalid") is None


def test_ghost_dismissal_rule():
    """Verify ghost dismissals (dismissed_player_id set with is_wicket=False)."""
    assert is_ghost_dismissal({"dismissed_player_id": "1440", "is_wicket": "false"}) is True
    assert is_ghost_dismissal({"dismissed_player_id": "1440", "is_wicket": "False"}) is True
    assert is_ghost_dismissal({"dismissed_player_id": "1440", "is_wicket": "true"}) is False
    assert is_ghost_dismissal({"dismissed_player_id": "", "is_wicket": "false"}) is False


def test_is_valid_wicket():
    """Verify true dismissal event requires is_wicket=True and non-empty dismissal_type."""
    assert is_valid_wicket({"is_wicket": "true", "dismissal_type": "bowled"}) is True
    assert is_valid_wicket({"is_wicket": "true", "dismissal_type": ""}) is False
    assert is_valid_wicket({"is_wicket": "false", "dismissal_type": "bowled"}) is False


def test_bowler_credited_dismissals():
    """Verify bowler-credited dismissals include Stump/stumped and exclude run-outs, retired hurt, etc."""
    assert is_bowler_credited_wicket("bowled") is True
    assert is_bowler_credited_wicket("caught") is True
    assert is_bowler_credited_wicket("caught and bowled") is True
    assert is_bowler_credited_wicket("lbw") is True
    assert is_bowler_credited_wicket("stump") is True
    assert is_bowler_credited_wicket("Stump") is True
    assert is_bowler_credited_wicket("stumped") is True
    assert is_bowler_credited_wicket("hit wicket") is True

    assert is_bowler_credited_wicket("run out") is False
    assert is_bowler_credited_wicket("retired hurt") is False
    assert is_bowler_credited_wicket("obstructing the field") is False
    assert is_bowler_credited_wicket(None) is False


def test_legal_ball_and_ball_faced():
    """Verify legal balls exclude wide and overstep; balls faced exclude wides only."""
    assert is_legal_ball("None") is True
    assert is_legal_ball("legbyes") is True
    assert is_legal_ball("byes") is True
    assert is_legal_ball("wide") is False
    assert is_legal_ball("Overstep") is False

    assert is_ball_faced("None") is True
    assert is_ball_faced("Overstep") is True  # Batter faces a no-ball!
    assert is_ball_faced("legbyes") is True
    assert is_ball_faced("wide") is False  # Wide is not faced!


def test_runs_breakdown_never_attributes_byes_to_bowler():
    """Verify Rule R5 / P5: bowler conceded runs NEVER includes byes, leg-byes, or penalties."""
    # Standard ball: 4 runs off bat
    b, w, t = parse_runs_breakdown({"runs": "4", "extras_type": "None", "extras_2_runs": "0"})
    assert b == 4 and w == 4 and t == 4.0

    # Wide ball: 0 bat, 1 wide -> bowler conceded = 1, team = 1
    b, w, t = parse_runs_breakdown({"runs": "0", "extras_type": "wide", "extras_2_runs": "0"})
    assert b == 0 and w == 1 and t == 1.0

    # Overstep with 6 off the bat: bat = 6, bowler conceded = 7 (6 + 1 penalty), team = 7
    b, w, t = parse_runs_breakdown({"runs": "6", "extras_type": "Overstep", "extras_2_runs": "0"})
    assert b == 6 and w == 7 and t == 7.0

    # Bye: bat = 0, bowler conceded = 0 (NOT bowler's fault!), team = 1.0
    b, w, t = parse_runs_breakdown({"runs": "0", "extras_type": "byes", "extras_2_runs": "0"})
    assert b == 0 and w == 0 and t == 1.0

    # Leg-bye with expected value 1.40: bowler conceded = 0, team = 1.40
    b, w, t = parse_runs_breakdown({"runs": "0", "extras_type": "legbyes", "extras_2_runs": "0"}, bye_legbye_run_value=1.40)
    assert b == 0 and w == 0 and t == 1.40
