"""CPPAE Match Contribution Analytics Engine (TRD §6, DATA_DICTIONARY §6 M01–M07).

Computes measurable match contribution metrics:
- M01: Player of the Match awards (input signal only, never total impact)
- M02: Batting contribution (team-run share)
- M03: Bowling contribution (team-wicket share and run-suppression share)
- M04: Match situation context (chase vs defend, entry phase)
- M05: Performance in wins vs losses
- M06: Measurable high-leverage contribution (T20 calibrated; non-T20 DEFERRED)
- M07: Additive match composite (M02 + M03 without arbitrary weights)
"""

from typing import Any
from uuid import UUID

from src.cmie.match_context import PreDeliveryState
from src.contracts.career import PlayerAward
from src.contracts.cppae import MatchContributionProfile
from src.ingestion.normalizer import (
    is_ball_faced,
    is_bowler_credited_wicket,
    is_legal_ball,
    is_valid_wicket,
    parse_runs_breakdown,
)


class MatchContributionEngine:
    """Core analytics engine for Match Contribution (M01–M07)."""

    def __init__(self) -> None:
        pass

    def calculate_profile(
        self,
        player_id: UUID | str,
        deliveries: list[dict[str, Any]],
        states: list[PreDeliveryState] | None = None,
        matches: list[dict[str, Any]] | None = None,
        player_awards: list[PlayerAward | dict[str, Any]] | None = None,
        format_tag: str = "T20",
    ) -> MatchContributionProfile:
        """Compute MatchContributionProfile for player_id."""
        pid_str = str(player_id)
        match_list = matches or []
        awards = player_awards or []
        states_aligned = list(states) if states is not None else [None] * len(deliveries)

        # M01: Player of Match awards
        potm_count = 0
        for aw in awards:
            aw_pid = str(getattr(aw, "player_id", None) or (aw.get("player_id") if isinstance(aw, dict) else ""))
            aw_type = str(getattr(aw, "award_type", "") or (aw.get("award_type", "") if isinstance(aw, dict) else ""))
            if aw_pid == pid_str and "player of the match" in aw_type.lower():
                potm_count += 1

        # Also check matches metadata if awards not explicitly passed
        if potm_count == 0 and match_list:
            for m in match_list:
                pom = str(m.get("player_of_match_id", "") or m.get("player_of_match", "") or "")
                if pom == pid_str or (isinstance(m.get("player_of_match"), list) and pid_str in [str(x) for x in m.get("player_of_match", [])]):
                    potm_count += 1

        # Map match outcomes: match_id -> match info
        match_map: dict[str, dict[str, Any]] = {}
        for m in match_list:
            mid = str(m.get("match_id", ""))
            match_map[mid] = m

        # Group deliveries by match and innings
        # (match_id, innings) -> list of (d, st)
        match_innings_delivs: dict[tuple[str, int], list[tuple[dict[str, Any], PreDeliveryState | None]]] = {}

        for d, st in zip(deliveries, states_aligned, strict=False):
            mpt = getattr(st, "mpt", "") if st else ""
            if mpt == "SUPER_OVER":
                continue
            if str(d.get("match_phase", "")).upper() == "SUPER_OVER":
                continue

            mid = str(d.get("match_id", "") or (st.match_id if st else ""))
            inn = int(d.get("innings", 1) or (st.innings if st else 1))
            key = (mid, inn)
            if key not in match_innings_delivs:
                match_innings_delivs[key] = []
            match_innings_delivs[key].append((d, st))

        # M02: Batting contribution (team run share across matches)
        # M03: Bowling contribution (team wicket share & run suppression)
        # M04: Situation context (first innings / defending vs second innings / chasing)
        # M05: Win / Loss performance
        # M06: High-leverage contribution
        # M07: Additive composite

        total_player_runs = 0
        total_team_runs_faced = 0

        total_player_wickets = 0
        total_team_wickets_taken = 0
        total_player_runs_conceded = 0
        total_team_runs_conceded = 0

        situation_context: dict[str, Any] = {
            "batting_first_innings": 0,
            "batting_second_innings": 0,
            "bowling_first_innings": 0,
            "bowling_second_innings": 0,
        }

        win_loss_performance: dict[str, Any] = {
            "wins": {"matches": 0, "runs": 0, "balls": 0, "wickets": 0, "legal_balls": 0, "runs_conceded": 0},
            "losses": {"matches": 0, "runs": 0, "balls": 0, "wickets": 0, "legal_balls": 0, "runs_conceded": 0},
        }

        # High leverage (M06)
        # T20: calibrated; Non-T20: DEFERRED per TRD Invariant R8
        hl_runs = 0
        hl_balls_faced = 0
        hl_wickets = 0
        hl_balls_bowled = 0
        hl_status = "DERIVED" if format_tag in ("T20", "IT20", "IPL") else "DEFERRED"

        # Per match contribution composites (M07)
        # match_id -> {"m02": float, "m03_w": float, "m03_r": float, "m07": float, "outcome": str}
        per_match_composite: dict[str, dict[str, Any]] = {}

        # Pre-scan deliveries to map player's team per match
        match_player_team: dict[str, str] = {}
        for d in deliveries:
            mid = str(d.get("match_id", ""))
            s_id = str(d.get("striker_id", "")).strip()
            ns_id = str(d.get("non_striker_id", "")).strip()
            b_id = str(d.get("bowler_id", "")).strip()
            w_id = str(d.get("dismissed_player_id", "")).strip()
            if s_id == pid_str or ns_id == pid_str or w_id == pid_str:
                t_id = str(d.get("batting_team_id", "") or d.get("team_id", "")).strip()
                if t_id:
                    match_player_team[mid] = t_id
            elif b_id == pid_str:
                t_id = str(d.get("bowling_team_id", "") or d.get("team_id", "")).strip()
                if t_id:
                    match_player_team[mid] = t_id

        win_matches: set[str] = set()
        loss_matches: set[str] = set()

        # Process each innings
        for (mid, inn), d_list in match_innings_delivs.items():
            m_info = match_map.get(mid, {})
            winner = str(m_info.get("winner_id", "") or m_info.get("winner", ""))
            outcome = str(m_info.get("outcome_type", "")).lower()
            player_team_id = match_player_team.get(mid)

            team_inn_runs = 0
            team_inn_wickets = 0
            player_inn_runs = 0
            player_inn_bf = 0

            team_bowl_runs = 0
            player_bowl_runs = 0
            player_bowl_wickets = 0
            player_bowl_lb = 0

            player_batted = False
            player_bowled = False

            for d, st in d_list:
                s_id = str(d.get("striker_id", "") or (st.striker_id if st else "")).strip()
                b_id = str(d.get("bowler_id", "") or (st.bowler_id if st else "")).strip()
                et = str(d.get("extras_type", "None")).strip().lower()
                is_leg = is_legal_ball(et)
                r_bat, b_runs, d_team_runs = parse_runs_breakdown(d)
                dt = str(d.get("dismissal_type", "")).strip()
                is_w = is_valid_wicket(d)
                is_bowler_w = is_w and is_bowler_credited_wicket(dt)

                # Total runs off the bat + extras for team total
                team_inn_runs += int(d_team_runs)
                if is_w:
                    team_inn_wickets += 1

                # High leverage check for M06
                # T20 threshold: RRR > 10.0 or wickets_in_hand <= 3 or is_pressure == True
                is_hl = bool(
                    format_tag in ("T20", "IT20", "IPL")
                    and st
                    and (st.is_pressure or st.wickets_in_hand <= 3)
                )

                # Batting tracking
                if s_id == pid_str:
                    player_batted = True
                    player_team_id = str(d.get("batting_team_id", "") or d.get("team_id", ""))
                    if is_ball_faced(et):
                        player_inn_bf += 1
                        player_inn_runs += r_bat
                        if is_hl:
                            hl_balls_faced += 1
                            hl_runs += r_bat

                # Bowling tracking
                if b_id == pid_str:
                    player_bowled = True
                    player_bowl_runs += b_runs
                    if is_leg:
                        player_bowl_lb += 1
                        if is_bowler_w:
                            player_bowl_wickets += 1
                        if is_hl:
                            hl_balls_bowled += 1
                            if is_bowler_w:
                                hl_wickets += 1
                else:
                    team_bowl_runs += b_runs

            # Update match situation context (M04)
            if player_batted:
                if inn == 1:
                    situation_context["batting_first_innings"] += 1
                else:
                    situation_context["batting_second_innings"] += 1
                total_player_runs += player_inn_runs
                total_team_runs_faced += team_inn_runs

            if player_bowled:
                if inn == 1:
                    situation_context["bowling_first_innings"] += 1
                else:
                    situation_context["bowling_second_innings"] += 1
                total_player_wickets += player_bowl_wickets
                total_team_wickets_taken += team_inn_wickets
                total_player_runs_conceded += player_bowl_runs
                total_team_runs_conceded += (team_bowl_runs + player_bowl_runs)

            # Match outcome recording (M05)
            is_win = (winner == player_team_id and winner != "")
            is_loss = (winner != player_team_id and winner != "" and outcome not in ("tie", "no_result"))

            out_cat = "wins" if is_win else ("losses" if is_loss else None)
            if out_cat:
                win_loss_performance[out_cat]["runs"] += player_inn_runs
                win_loss_performance[out_cat]["balls"] += player_inn_bf
                win_loss_performance[out_cat]["wickets"] += player_bowl_wickets
                win_loss_performance[out_cat]["legal_balls"] += player_bowl_lb
                win_loss_performance[out_cat]["runs_conceded"] += player_bowl_runs
                if player_batted or player_bowled:
                    if is_win:
                        win_matches.add(mid)
                    elif is_loss:
                        loss_matches.add(mid)

            # Per match composite tracking (M07)
            if mid not in per_match_composite:
                per_match_composite[mid] = {
                    "m02": 0.0,
                    "m03_w": 0.0,
                    "m03_r": 0.0,
                    "m07": 0.0,
                    "outcome": outcome,
                    "is_win": is_win,
                }

            if player_batted and team_inn_runs > 0:
                m02_match = round(player_inn_runs / team_inn_runs * 100.0, 2)
                per_match_composite[mid]["m02"] = m02_match
                per_match_composite[mid]["m07"] = round(per_match_composite[mid]["m07"] + m02_match, 2)

            if player_bowled:
                if team_inn_wickets > 0:
                    m03_w_match = round(player_bowl_wickets / max(1, team_inn_wickets) * 100.0, 2)
                    per_match_composite[mid]["m03_w"] = m03_w_match
                    per_match_composite[mid]["m07"] = round(per_match_composite[mid]["m07"] + m03_w_match, 2)
                if (team_bowl_runs + player_bowl_runs) > 0:
                    m03_r_match = round(player_bowl_runs / (team_bowl_runs + player_bowl_runs) * 100.0, 2)
                    per_match_composite[mid]["m03_r"] = m03_r_match

        win_loss_performance["wins"]["matches"] = len(win_matches)
        win_loss_performance["losses"]["matches"] = len(loss_matches)

        # Aggregated M02: Batting contribution
        bat_contrib_pct = (
            round(total_player_runs / total_team_runs_faced * 100.0, 2)
            if total_team_runs_faced > 0
            else None
        )

        # Aggregated M03: Bowling contribution
        bowl_wicket_share_pct = (
            round(total_player_wickets / total_team_wickets_taken * 100.0, 2)
            if total_team_wickets_taken > 0
            else None
        )
        bowl_run_suppress_pct = (
            round(total_player_runs_conceded / total_team_runs_conceded * 100.0, 2)
            if total_team_runs_conceded > 0
            else None
        )

        # M06: High leverage dictionary
        high_leverage_dict: dict[str, Any]
        if hl_status == "DERIVED":
            high_leverage_dict = {
                "status": "DERIVED",
                "format_tag": format_tag,
                "high_leverage_runs": hl_runs,
                "high_leverage_balls_faced": hl_balls_faced,
                "high_leverage_wickets": hl_wickets,
                "high_leverage_balls_bowled": hl_balls_bowled,
                "batting_strike_rate": round(hl_runs / hl_balls_faced * 100.0, 2) if hl_balls_faced > 0 else None,
                "bowling_strike_rate": round(hl_balls_bowled / hl_wickets, 2) if hl_wickets > 0 else None,
            }
        else:
            # Retain non-T20 high-leverage thresholds as DEFERRED per TRD Invariant R8
            high_leverage_dict = {
                "status": "DEFERRED",
                "format_tag": format_tag,
                "high_leverage_runs": None,
                "high_leverage_wickets": None,
                "note": "Non-T20 high-leverage thresholds retained as DEFERRED per TRD Invariant R8.",
            }

        # M07: Additive match composite
        # M07 = M02 + M03 without arbitrary weights. If both None -> None.
        additive_composite: float | None = None
        if bat_contrib_pct is not None or bowl_wicket_share_pct is not None:
            c_bat = bat_contrib_pct or 0.0
            c_bowl = bowl_wicket_share_pct or 0.0
            additive_composite = round(c_bat + c_bowl, 2)

        return MatchContributionProfile(
            player_of_match_awards=potm_count,
            batting_contribution_pct=bat_contrib_pct,
            bowling_wicket_share_pct=bowl_wicket_share_pct,
            bowling_run_suppression_pct=bowl_run_suppress_pct,
            situation_context=situation_context,
            win_loss_performance=win_loss_performance,
            high_leverage_contribution=high_leverage_dict,
            additive_composite=additive_composite,
            per_match_composite=per_match_composite,
        )
