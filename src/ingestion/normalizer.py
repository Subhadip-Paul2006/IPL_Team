"""Data Semantics & Delivery Normalizer (Phase 1B - Workstream B).

Implements strict cricket semantic rules:
1. extras1_runs as categorical enum mapping (never an extra-run count).
2. Revised overs as integer ball counts (e.g. 114.0 = 19.0 overs = 114 balls).
3. bowl_speed sanitization (values <= 0 or > 165 km/h sanitized to None).
4. Ghost dismissal rule (dismissed_player_id set with is_wicket=False ignored as non-wicket).
5. Bowler-credited dismissal discrimination (excludes run-outs and non-bowler wickets).
6. Runs separation: batter runs, bowler runs conceded (excludes byes/leg-byes/penalties), and team runs.
7. Legal balls vs balls faced (no-balls count as balls faced; wides do not).
"""

from typing import Any

# Authoritative categorical enum mapping for extras1_runs in ball_by_ball.csv
EXTRAS1_ENUM: dict[str, str] = {
    "1": "Overstep",
    "2": "wide",
    "3": "legbyes",
    "4": "byes",
    "5": "other",
    "6": "None",
    "7": "Penalty",
}

# Dismissals credited to the bowler in cricket laws (includes Stump/stumped)
BOWLER_CREDITED_DISMISSALS: frozenset[str] = frozenset({
    "bowled",
    "caught",
    "caught and bowled",
    "lbw",
    "stump",
    "stumped",
    "hit wicket",
})


def sanitize_bowl_speed(speed_val: Any) -> float | None:
    """Sanitize bowl_speed: values <= 0 or > 165 km/h become None (R1: missing = NULL)."""
    if speed_val is None:
        return None
    val_str = str(speed_val).strip()
    if not val_str:
        return None
    try:
        val = float(val_str)
        if val <= 0.0 or val > 165.0:
            return None
        return val
    except ValueError:
        return None


def parse_revised_balls(overs_val: Any) -> int | None:
    """Parse revised overs field from matches.csv as integer ball count."""
    if overs_val is None:
        return None
    val_str = str(overs_val).strip()
    if not val_str:
        return None
    try:
        val_float = float(val_str)
        return int(round(val_float))
    except ValueError:
        return None


def is_ghost_dismissal(row: dict[str, Any]) -> bool:
    """Detect ghost dismissal: dismissed_player_id populated with is_wicket == False."""
    dismissed_pid = str(row.get("dismissed_player_id", "")).strip()
    is_w = str(row.get("is_wicket", "")).strip().lower() == "true"
    return bool(dismissed_pid) and not is_w


def is_valid_wicket(row: dict[str, Any]) -> bool:
    """Verify true dismissal event: is_wicket == True AND dismissal_type IS NOT NULL."""
    is_w = str(row.get("is_wicket", "")).strip().lower() == "true"
    dt = str(row.get("dismissal_type", "")).strip()
    return is_w and bool(dt)


def is_bowler_credited_wicket(dismissal_type: str | None) -> bool:
    """Check if dismissal is credited to the bowler (excludes run outs, retired hurt, etc.)."""
    if not dismissal_type:
        return False
    return dismissal_type.strip().lower() in BOWLER_CREDITED_DISMISSALS


def is_legal_ball(extras_type: str | None) -> bool:
    """Determine if a delivery is a legal ball (excludes wides and oversteps/no-balls)."""
    if not extras_type:
        return True
    return extras_type.strip().lower() not in ("wide", "overstep")


def is_ball_faced(extras_type: str | None) -> bool:
    """Determine if delivery counts as a ball faced by the batter (wides excluded; no-balls included)."""
    if not extras_type:
        return True
    return extras_type.strip().lower() != "wide"


def parse_runs_breakdown(
    row: dict[str, Any],
    bye_legbye_run_value: float = 1.0,
) -> tuple[int, int, float]:
    """Calculate the strict three-way runs breakdown for a delivery.

    Returns:
        (batter_runs, bowler_runs_conceded, team_runs)
    """
    bat_runs = int(row.get("runs", 0) or 0)
    et = str(row.get("extras_type", "None")).strip().lower()
    e2 = int(row.get("extras_2_runs", 0) or 0)

    # Bowler conceded runs: bat runs + wide penalties + no-ball penalties
    # Crucial Rule R5 / P5: NEVER attribute byes, leg-byes, or penalties to bowler!
    bowler_runs = bat_runs
    if et in ("wide", "overstep"):
        bowler_runs += 1 + e2

    # Team runs: bat runs + all extras
    team_runs: float = float(bat_runs)
    if et in ("wide", "overstep", "penalty"):
        team_runs += 1.0 + float(e2)
    elif et in ("byes", "legbyes"):
        team_runs += float(bye_legbye_run_value) + float(e2)
    else:
        team_runs += float(e2)

    return bat_runs, bowler_runs, team_runs
