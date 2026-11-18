"""CPPAE Batting Analytics Engine (TRD §6, DATA_DICTIONARY §1 B01–B17 & BPPS).

Calculates comprehensive batting profiles, position splits, phase analytics,
head-to-head bowler matchups, pace/spin splits, partnerships, win/loss splits,
and Batting Pressure Performance Score (BPPS) with Option B undefeated batter support.
"""

import re
from typing import Any
from uuid import UUID

from src.cmie.match_context import PreDeliveryState
from src.contracts.cppae import (
    BattingPhaseSplit,
    BattingPositionSplit,
    BattingProfile,
    HeadToHeadMatchup,
    PartnershipRecord,
)
from src.contracts.scorecard import BattingInnings
from src.ingestion.cricsheet_parser import determine_match_phase
from src.ingestion.normalizer import is_ball_faced, is_valid_wicket


def classify_bowling_style(style_str: str | None) -> str:
    """Classify a raw bowling style into 'PACE', 'SPIN', or 'UNKNOWN'."""
    if not style_str:
        return "UNKNOWN"
    s = style_str.lower().strip()
    words = set(re.findall(r"[a-zA-Z]+", s))
    spin_words = {
        "spin", "spinner", "break", "orthodox", "unorthodox", "chinaman", "googly",
        "sla", "slc", "os", "ob", "lb", "lbg", "lac", "wrist", "wristspin", "slow", "finger",
    }
    pace_words = {"fast", "medium", "pace", "seam", "raf", "laf", "rmf", "lmf", "rf", "lf", "rm", "lm"}

    if any(w in spin_words for w in words) or "spin" in s or "orthodox" in s or "break" in s or "slow" in s or "chinaman" in s:
        return "SPIN"
    if any(w in pace_words for w in words) or "pace" in s or "fast" in s or "medium" in s or "seam" in s:
        return "PACE"
    return "UNKNOWN"


def normalize_style_group(style_str: str | None) -> str:
    """Map raw bowling style to standard canonical groups."""
    if not style_str:
        return "Unknown Style"
    s = style_str.lower().strip()
    # Left-arm wrist spin (check unorthodox/chinaman/wrist before orthodox)
    if "left" in s and ("chinaman" in s or "wrist" in s or "unorthodox" in s or "slc" in s or "lac" in s):
        return "Left-arm Wrist Spin"
    # Left-arm orthodox finger spin
    if "left" in s and ("spin" in s or "orthodox" in s or "sla" in s or "slow" in s):
        return "Left-arm Orthodox"
    if "left" in s and ("fast" in s or "pace" in s or "laf" in s or "lf" in s):
        return "Left-arm Fast"
    if "left" in s and ("medium" in s or "lmf" in s or "lm" in s):
        return "Left-arm Medium"
    if "right" in s and ("leg" in s or "wrist" in s or "lbg" in s or "lb" in s):
        return "Right-arm Leg-break"
    if "right" in s and ("off" in s or "finger" in s or "os" in s or "ob" in s):
        return "Right-arm Off-break"
    if "right" in s and ("fast" in s or "pace" in s or "raf" in s or "rf" in s):
        return "Right-arm Fast"
    if "right" in s and ("medium" in s or "rmf" in s or "rm" in s):
        return "Right-arm Medium"
    if "slow" in s and "left" in s:
        return "Left-arm Orthodox"
    if "slow" in s and "right" in s:
        return "Right-arm Off-break"
    if "spin" in s or "orthodox" in s:
        return "Spin Unspecified"
    if "pace" in s or "fast" in s or "medium" in s:
        return "Pace Unspecified"
    return style_str.strip().title()


class BattingEngine:
    """Core analytics engine for Batting Profile (B01–B17 & BPPS)."""

    def __init__(
        self,
        k_bat: float = 30.0,
        k_bat_avg: float = 5.0,
        balls_per_over: int = 6,
    ) -> None:
        self.k_bat = k_bat
        self.k_bat_avg = k_bat_avg
        self.balls_per_over = balls_per_over

    def calculate_profile(
        self,
        player_id: UUID | str,
        deliveries: list[dict[str, Any]],
        states: list[PreDeliveryState] | None = None,
        batting_innings: list[BattingInnings | dict[str, Any]] | None = None,
        matches: list[dict[str, Any]] | None = None,
        player_names: dict[str, str] | None = None,
        bowling_styles: dict[str, str] | None = None,
        format_tag: str = "T20",
    ) -> BattingProfile:
        """Compute complete BattingProfile for player_id."""
        pid_str = str(player_id)
        names = player_names or {}
        styles = bowling_styles or {}
        bpo = 5 if (format_tag == "HUNDRED" or self.balls_per_over == 5) else 6

        # Filter deliveries where player was involved (striker or non-striker or dismissed)
        # Note: Super Over is quarantined per DATA_DICTIONARY §4.3
        states_aligned: list[PreDeliveryState | None] = (
            list(states) if states is not None else [None] * len(deliveries)
        )

        # Match outcome lookup: match_id -> outcome dict
        match_outcomes: dict[str, dict[str, Any]] = {}
        if matches:
            for m in matches:
                mid = str(m.get("match_id", ""))
                match_outcomes[mid] = m

        # 1. Innings and match tracking (B01, B02)
        matches_faced: set[str] = set()
        total_runs = 0
        total_balls = 0
        total_fours = 0
        total_sixes = 0
        total_dots = 0
        total_dismissals = 0

        # Phase tracking (B12)
        phase_data: dict[str, dict[str, int]] = {
            "Powerplay": {"balls": 0, "runs": 0, "dismissals": 0, "fours": 0, "sixes": 0, "dots": 0},
            "Middle": {"balls": 0, "runs": 0, "dismissals": 0, "fours": 0, "sixes": 0, "dots": 0},
            "Death": {"balls": 0, "runs": 0, "dismissals": 0, "fours": 0, "sixes": 0, "dots": 0},
        }

        # Matchups (B13, B14, B15)
        # bowler_id -> {balls, runs, dismissals, dots, fours, sixes}
        bowler_stats: dict[str, dict[str, int]] = {}
        pace_stats: dict[str, dict[str, int]] = {
            "PACE": {"balls": 0, "runs": 0, "dismissals": 0, "dots": 0, "fours": 0, "sixes": 0},
            "SPIN": {"balls": 0, "runs": 0, "dismissals": 0, "dots": 0, "fours": 0, "sixes": 0},
        }
        style_stats: dict[str, dict[str, int]] = {}

        # Outcome splits (B17)
        # outcome -> {matches: set, balls, runs, dismissals, dots, fours, sixes}
        outcome_data: dict[str, dict[str, Any]] = {
            "win": {"matches": set(), "balls": 0, "runs": 0, "dismissals": 0, "dots": 0, "fours": 0, "sixes": 0},
            "loss": {"matches": set(), "balls": 0, "runs": 0, "dismissals": 0, "dots": 0, "fours": 0, "sixes": 0},
            "tie": {"matches": set(), "balls": 0, "runs": 0, "dismissals": 0, "dots": 0, "fours": 0, "sixes": 0},
            "no_result": {"matches": set(), "balls": 0, "runs": 0, "dismissals": 0, "dots": 0, "fours": 0, "sixes": 0},
        }

        # Pressure subset tracking for BPPS
        p_balls = 0
        p_runs = 0
        p_fours = 0
        p_sixes = 0
        p_dots = 0
        p_dismissals = 0

        # Population priors counters (for pressure shrinkage)
        pop_p_runs = 0
        pop_p_balls = 0
        pop_p_dismissals = 0

        # Partnership tracking (B16)
        # Group deliveries by (match_id, innings) to track contiguous windows
        innings_deliveries: dict[tuple[str, int], list[tuple[dict[str, Any], PreDeliveryState | None]]] = {}

        for d, st in zip(deliveries, states_aligned, strict=False):
            # Check super over
            mpt = getattr(st, "mpt", "") if st else ""
            if mpt == "SUPER_OVER":
                continue
            if str(d.get("match_phase", "")).upper() == "SUPER_OVER":
                continue

            mid = str(d.get("match_id", "") or (st.match_id if st else ""))
            inn = int(d.get("innings", 1) or (st.innings if st else 1))
            inn_key = (mid, inn)
            if inn_key not in innings_deliveries:
                innings_deliveries[inn_key] = []
            innings_deliveries[inn_key].append((d, st))

            striker = str(d.get("striker_id", "") or (st.striker_id if st else "")).strip()
            bowler = str(d.get("bowler_id", "") or (st.bowler_id if st else "")).strip()
            dismissed_pid = str(d.get("dismissed_player_id", "")).strip()
            is_w = is_valid_wicket(d)

            et = str(d.get("extras_type", "None")).strip().lower()
            runs_bat = int(d.get("runs", 0) or 0)
            is_bf = is_ball_faced(et)
            is_press = getattr(st, "is_pressure", False) if st else False

            # Population pressure accumulation
            if is_press and is_bf:
                pop_p_balls += 1
                pop_p_runs += runs_bat
            if is_press and is_w and dismissed_pid:
                pop_p_dismissals += 1

            # Check if this player was dismissed on this ball (even if non-striker, e.g. run out)
            if is_w and dismissed_pid == pid_str:
                total_dismissals += 1
                if is_press:
                    p_dismissals += 1

                # Record dismissal in phase
                ov = int(d.get("over_number", 0) or (st.overid - 1 if st and st.overid > 0 else 0))
                ph = determine_match_phase(ov, match_type=format_tag, balls_per_over=bpo)
                if ph in phase_data:
                    phase_data[ph]["dismissals"] += 1

                # Record dismissal in bowler matchup if dismissed by bowler
                if bowler:
                    if bowler not in bowler_stats:
                        bowler_stats[bowler] = {"balls": 0, "runs": 0, "dismissals": 0, "dots": 0, "fours": 0, "sixes": 0}
                    bowler_stats[bowler]["dismissals"] += 1
                    b_style = styles.get(bowler)
                    cls_style = classify_bowling_style(b_style)
                    if cls_style in pace_stats:
                        pace_stats[cls_style]["dismissals"] += 1
                    grp_style = normalize_style_group(b_style)
                    if grp_style not in style_stats:
                        style_stats[grp_style] = {"balls": 0, "runs": 0, "dismissals": 0, "dots": 0, "fours": 0, "sixes": 0}
                    style_stats[grp_style]["dismissals"] += 1

                # Record dismissal in outcome
                m_info = match_outcomes.get(mid, {})
                ot = str(m_info.get("outcome_type", "")).lower()
                winner = str(m_info.get("winner_id", "") or m_info.get("winner", ""))
                player_team = str(d.get("batting_team_id", "") or d.get("team_id", ""))
                out_key = "tie" if ot == "tie" else ("no_result" if ot in ("no_result", "") else ("win" if winner == player_team and winner else "loss"))
                if out_key in outcome_data:
                    outcome_data[out_key]["dismissals"] += 1

            # Now process balls faced by this player as striker
            if striker == pid_str and is_bf:
                matches_faced.add(mid)
                total_balls += 1
                total_runs += runs_bat
                is_dot = (runs_bat == 0 and et != "overstep")
                is_four = (runs_bat == 4)
                is_six = (runs_bat == 6)

                if is_dot:
                    total_dots += 1
                elif is_four:
                    total_fours += 1
                elif is_six:
                    total_sixes += 1

                # Phase assignment
                ov = int(d.get("over_number", 0) or (st.overid - 1 if st and st.overid > 0 else 0))
                ph = determine_match_phase(ov, match_type=format_tag, balls_per_over=bpo)
                if ph in phase_data:
                    phase_data[ph]["balls"] += 1
                    phase_data[ph]["runs"] += runs_bat
                    if is_dot:
                        phase_data[ph]["dots"] += 1
                    elif is_four:
                        phase_data[ph]["fours"] += 1
                    elif is_six:
                        phase_data[ph]["sixes"] += 1

                # Bowler matchup
                if bowler:
                    if bowler not in bowler_stats:
                        bowler_stats[bowler] = {"balls": 0, "runs": 0, "dismissals": 0, "dots": 0, "fours": 0, "sixes": 0}
                    bowler_stats[bowler]["balls"] += 1
                    bowler_stats[bowler]["runs"] += runs_bat
                    if is_dot:
                        bowler_stats[bowler]["dots"] += 1
                    elif is_four:
                        bowler_stats[bowler]["fours"] += 1
                    elif is_six:
                        bowler_stats[bowler]["sixes"] += 1

                    # Pace vs Spin
                    b_style = styles.get(bowler)
                    cls_style = classify_bowling_style(b_style)
                    if cls_style in pace_stats:
                        pace_stats[cls_style]["balls"] += 1
                        pace_stats[cls_style]["runs"] += runs_bat
                        if is_dot:
                            pace_stats[cls_style]["dots"] += 1
                        elif is_four:
                            pace_stats[cls_style]["fours"] += 1
                        elif is_six:
                            pace_stats[cls_style]["sixes"] += 1

                    # Style group matchup
                    grp_style = normalize_style_group(b_style)
                    if grp_style not in style_stats:
                        style_stats[grp_style] = {"balls": 0, "runs": 0, "dismissals": 0, "dots": 0, "fours": 0, "sixes": 0}
                    style_stats[grp_style]["balls"] += 1
                    style_stats[grp_style]["runs"] += runs_bat
                    if is_dot:
                        style_stats[grp_style]["dots"] += 1
                    elif is_four:
                        style_stats[grp_style]["fours"] += 1
                    elif is_six:
                        style_stats[grp_style]["sixes"] += 1

                # Outcome split
                m_info = match_outcomes.get(mid, {})
                ot = str(m_info.get("outcome_type", "")).lower()
                winner = str(m_info.get("winner_id", "") or m_info.get("winner", ""))
                player_team = str(d.get("batting_team_id", "") or d.get("team_id", ""))
                out_key = "tie" if ot == "tie" else ("no_result" if ot in ("no_result", "") else ("win" if winner == player_team and winner else "loss"))
                if out_key in outcome_data:
                    outcome_data[out_key]["matches"].add(mid)
                    outcome_data[out_key]["balls"] += 1
                    outcome_data[out_key]["runs"] += runs_bat
                    if is_dot:
                        outcome_data[out_key]["dots"] += 1
                    elif is_four:
                        outcome_data[out_key]["fours"] += 1
                    elif is_six:
                        outcome_data[out_key]["sixes"] += 1

                # Pressure stats
                if is_press:
                    p_balls += 1
                    p_runs += runs_bat
                    if is_dot:
                        p_dots += 1
                    elif is_four:
                        p_fours += 1
                    elif is_six:
                        p_sixes += 1

        # 2. Partnership calculation (B16)
        partnerships_list: list[PartnershipRecord] = []
        for (mid, _inn), d_list in innings_deliveries.items():
            # Sort deliveries chronologically to ensure contiguous crease window integrity
            d_list.sort(
                key=lambda item: (
                    int(item[0].get("over_number", 0) or 0),
                    int(item[0].get("delivery_sequence", 0) or item[0].get("over_ball_num", 0) or (item[1].innings_ball_num if item[1] else 0)),
                )
            )

            # Extract contiguous windows where player is at crease with a partner
            current_partner: str | None = None
            p_runs_window = 0
            partner_runs_window = 0
            extras_window = 0
            balls_window = 0

            for d, _st in d_list:
                s_id = str(d.get("striker_id", "")).strip()
                ns_id = str(d.get("non_striker_id", "")).strip()
                if pid_str not in (s_id, ns_id):
                    # Player not at crease
                    if current_partner is not None:
                        # Flush partnership
                        partnerships_list.append(PartnershipRecord(
                            partner_id=current_partner,
                            partner_name=names.get(current_partner, f"Player_{current_partner}"),
                            match_id=mid,
                            player_runs=p_runs_window,
                            partner_runs=partner_runs_window,
                            extras_runs=extras_window,
                            total_partnership_runs=p_runs_window + partner_runs_window + extras_window,
                            balls_faced=balls_window,
                            unbroken=False,
                        ))
                        current_partner = None
                        p_runs_window = 0
                        partner_runs_window = 0
                        extras_window = 0
                        balls_window = 0
                    continue

                # Player is at crease
                partner_id = ns_id if s_id == pid_str else s_id
                if current_partner is None:
                    current_partner = partner_id
                elif current_partner != partner_id:
                    # Partner changed (dismissal of previous partner)
                    partnerships_list.append(PartnershipRecord(
                        partner_id=current_partner,
                        partner_name=names.get(current_partner, f"Player_{current_partner}"),
                        match_id=mid,
                        player_runs=p_runs_window,
                        partner_runs=partner_runs_window,
                        extras_runs=extras_window,
                        total_partnership_runs=p_runs_window + partner_runs_window + extras_window,
                        balls_faced=balls_window,
                        unbroken=False,
                    ))
                    current_partner = partner_id
                    p_runs_window = 0
                    partner_runs_window = 0
                    extras_window = 0
                    balls_window = 0

                # Accumulate ball in window
                r_bat = int(d.get("runs", 0) or 0)
                et = str(d.get("extras_type", "None")).strip().lower()
                r_ext = int(d.get("extras_2_runs", 0) or 0) if et != "none" else 0
                if s_id == pid_str:
                    p_runs_window += r_bat
                    if is_ball_faced(et):
                        balls_window += 1
                else:
                    partner_runs_window += r_bat

                extras_window += r_ext

                # Check if a wicket fell ending this partnership
                if is_valid_wicket(d):
                    w_pid = str(d.get("dismissed_player_id", "")).strip()
                    if w_pid in (pid_str, current_partner):
                        partnerships_list.append(PartnershipRecord(
                            partner_id=current_partner,
                            partner_name=names.get(current_partner, f"Player_{current_partner}"),
                            match_id=mid,
                            player_runs=p_runs_window,
                            partner_runs=partner_runs_window,
                            extras_runs=extras_window,
                            total_partnership_runs=p_runs_window + partner_runs_window + extras_window,
                            balls_faced=balls_window,
                            unbroken=False,
                        ))
                        current_partner = None
                        p_runs_window = 0
                        partner_runs_window = 0
                        extras_window = 0
                        balls_window = 0

            # Flush any unbroken partnership at end of innings
            if current_partner is not None:
                partnerships_list.append(PartnershipRecord(
                    partner_id=current_partner,
                    partner_name=names.get(current_partner, f"Player_{current_partner}"),
                    match_id=mid,
                    player_runs=p_runs_window,
                    partner_runs=partner_runs_window,
                    extras_runs=extras_window,
                    total_partnership_runs=p_runs_window + partner_runs_window + extras_window,
                    balls_faced=balls_window,
                    unbroken=True,
                ))

        # 3. Position splits (B10, B11)
        pos_splits: dict[str, BattingPositionSplit] = {}
        dnb_count = 0
        zero_ball_batted = 0
        non_dnb_innings = 0

        if batting_innings:
            for bi in batting_innings:
                b_pid = str(getattr(bi, "player_id", None) or (bi.get("player_id") if isinstance(bi, dict) else ""))
                if b_pid != pid_str:
                    continue

                dnb = bool(getattr(bi, "did_not_bat", False) or (bi.get("did_not_bat", False) if isinstance(bi, dict) else False))
                bf = int(getattr(bi, "balls_faced", 0) or (bi.get("balls_faced", 0) if isinstance(bi, dict) else 0))
                r = int(getattr(bi, "runs_scored", 0) or (bi.get("runs_scored", 0) if isinstance(bi, dict) else 0))
                f4 = int(getattr(bi, "fours", 0) or (bi.get("fours", 0) if isinstance(bi, dict) else 0))
                s6 = int(getattr(bi, "sixes", 0) or (bi.get("sixes", 0) if isinstance(bi, dict) else 0))
                dots = int(getattr(bi, "dot_balls_faced", 0) or (bi.get("dot_balls_faced", 0) if isinstance(bi, dict) else 0))
                is_no = bool(getattr(bi, "is_not_out", False) or (bi.get("is_not_out", False) if isinstance(bi, dict) else False))
                pos = getattr(bi, "batting_position", None) or (bi.get("batting_position") if isinstance(bi, dict) else None)

                if dnb:
                    dnb_count += 1
                    continue

                non_dnb_innings += 1
                if bf == 0:
                    zero_ball_batted += 1

                if pos is not None:
                    pos_key = str(pos)
                    if pos_key not in pos_splits:
                        pos_splits[pos_key] = BattingPositionSplit(position=int(pos))
                    ps = pos_splits[pos_key]
                    ps.innings_count += 1
                    ps.balls_faced += bf
                    ps.runs_scored += r
                    ps.fours += f4
                    ps.sixes += s6
                    ps.dot_balls += dots
                    if not is_no:
                        ps.dismissals += 1

            # Compute position rates and insufficient sample flags
            for ps in pos_splits.values():
                ps.strike_rate = round(ps.runs_scored / ps.balls_faced * 100.0, 2) if ps.balls_faced > 0 else None
                ps.batting_average = round(ps.runs_scored / ps.dismissals, 2) if ps.dismissals > 0 else None
                ps.dot_pct = round(ps.dot_balls / ps.balls_faced * 100.0, 2) if ps.balls_faced > 0 else None
                ps.boundary_pct = round((ps.fours * 4 + ps.sixes * 6) / ps.runs_scored * 100.0, 2) if ps.runs_scored > 0 else None
                ps.insufficient_sample = ps.balls_faced < 20
        else:
            # Fallback if no explicit BattingInnings list: estimate non_dnb_innings from matches faced
            non_dnb_innings = len(matches_faced)

        # 4. Phase split contracts (B12)
        phase_splits_map: dict[str, BattingPhaseSplit] = {}
        for ph, p_dict in phase_data.items():
            b_cnt = p_dict["balls"]
            r_cnt = p_dict["runs"]
            d_cnt = p_dict["dismissals"]
            phase_splits_map[ph] = BattingPhaseSplit(
                phase=ph,
                balls_faced=b_cnt,
                runs_scored=r_cnt,
                dismissals=d_cnt,
                fours=p_dict["fours"],
                sixes=p_dict["sixes"],
                dot_balls=p_dict["dots"],
                strike_rate=round(r_cnt / b_cnt * 100.0, 2) if b_cnt > 0 else None,
                batting_average=round(r_cnt / d_cnt, 2) if d_cnt > 0 else None,
                dot_pct=round(p_dict["dots"] / b_cnt * 100.0, 2) if b_cnt > 0 else None,
                boundary_pct=round((p_dict["fours"] * 4 + p_dict["sixes"] * 6) / r_cnt * 100.0, 2) if r_cnt > 0 else None,
            )

        # 5. Head-to-head bowler matchups (B13)
        bowler_matchups_map: dict[str, HeadToHeadMatchup] = {}
        for b_id, b_dict in bowler_stats.items():
            b_cnt = b_dict["balls"]
            r_cnt = b_dict["runs"]
            d_cnt = b_dict["dismissals"]
            bowler_matchups_map[b_id] = HeadToHeadMatchup(
                opponent_id=b_id,
                opponent_name=names.get(b_id, f"Bowler_{b_id}"),
                balls=b_cnt,
                runs=r_cnt,
                dismissals=d_cnt,
                dots=b_dict["dots"],
                fours=b_dict["fours"],
                sixes=b_dict["sixes"],
                strike_rate=round(r_cnt / b_cnt * 100.0, 2) if b_cnt > 0 else None,
                average=round(r_cnt / d_cnt, 2) if d_cnt > 0 else None,
                dot_pct=round(b_dict["dots"] / b_cnt * 100.0, 2) if b_cnt > 0 else None,
                warning_flag="INSUFFICIENT_SAMPLE" if b_cnt < 24 else None,
            )

        # 6. Pace vs Spin matchups (B14)
        pace_spin_map: dict[str, HeadToHeadMatchup] = {}
        for p_cls in ("PACE", "SPIN"):
            p_dict = pace_stats[p_cls]
            b_cnt = p_dict["balls"]
            r_cnt = p_dict["runs"]
            d_cnt = p_dict["dismissals"]
            pace_spin_map[p_cls] = HeadToHeadMatchup(
                opponent_id=p_cls,
                opponent_name=f"All {p_cls.title()} Bowling",
                balls=b_cnt,
                runs=r_cnt,
                dismissals=d_cnt,
                dots=p_dict["dots"],
                fours=p_dict["fours"],
                sixes=p_dict["sixes"],
                strike_rate=round(r_cnt / b_cnt * 100.0, 2) if b_cnt > 0 else None,
                average=round(r_cnt / d_cnt, 2) if d_cnt > 0 else None,
                dot_pct=round(p_dict["dots"] / b_cnt * 100.0, 2) if b_cnt > 0 else None,
                warning_flag="INSUFFICIENT_SAMPLE" if b_cnt < 24 else None,
            )

        # 7. Bowling Style matchups (B15)
        style_matchups_map: dict[str, HeadToHeadMatchup] = {}
        for s_grp, s_dict in style_stats.items():
            b_cnt = s_dict["balls"]
            r_cnt = s_dict["runs"]
            d_cnt = s_dict["dismissals"]
            style_matchups_map[s_grp] = HeadToHeadMatchup(
                opponent_id=s_grp,
                opponent_name=s_grp,
                balls=b_cnt,
                runs=r_cnt,
                dismissals=d_cnt,
                dots=s_dict["dots"],
                fours=s_dict["fours"],
                sixes=s_dict["sixes"],
                strike_rate=round(r_cnt / b_cnt * 100.0, 2) if b_cnt > 0 else None,
                average=round(r_cnt / d_cnt, 2) if d_cnt > 0 else None,
                dot_pct=round(s_dict["dots"] / b_cnt * 100.0, 2) if b_cnt > 0 else None,
                warning_flag="SMALL_SAMPLE_WARNING" if b_cnt < 18 else None,
            )

        # 8. Win / Loss splits (B17)
        outcome_splits_map: dict[str, dict[str, Any]] = {}
        for out_k, o_dict in outcome_data.items():
            m_set = o_dict["matches"]
            m_cnt = len(m_set)
            b_cnt = o_dict["balls"]
            r_cnt = o_dict["runs"]
            d_cnt = o_dict["dismissals"]
            if m_cnt == 0 and b_cnt == 0:
                outcome_splits_map[out_k] = {
                    "matches": 0,
                    "runs": 0,
                    "balls": 0,
                    "strike_rate": None,
                    "batting_average": None,
                }
            else:
                outcome_splits_map[out_k] = {
                    "matches": m_cnt,
                    "runs": r_cnt,
                    "balls": b_cnt,
                    "strike_rate": round(r_cnt / b_cnt * 100.0, 2) if b_cnt > 0 else None,
                    "batting_average": round(r_cnt / d_cnt, 2) if d_cnt > 0 else None,
                }

        # 9. BPPS Calculation (Option B Undefeated Batter preservation)
        sr_all = (total_runs / total_balls * 100.0) if total_balls > 0 else None
        avg_all = (total_runs / total_dismissals) if total_dismissals > 0 else None

        sr_p_raw = (p_runs / p_balls * 100.0) if p_balls > 0 else None
        avg_p_raw = (p_runs / p_dismissals) if p_dismissals > 0 else None

        prior_sr = (pop_p_runs / max(1, pop_p_balls) * 100.0) if pop_p_balls > 0 else 140.0
        prior_avg = (pop_p_runs / max(1, pop_p_dismissals)) if pop_p_dismissals > 0 else 20.0

        if p_balls > 0:
            sr_p_shrunk = (p_balls / (p_balls + self.k_bat)) * (sr_p_raw or 0.0) + (self.k_bat / (p_balls + self.k_bat)) * prior_sr
        else:
            sr_p_shrunk = prior_sr

        if p_dismissals > 0:
            avg_p_shrunk = (p_dismissals / (p_dismissals + self.k_bat_avg)) * (avg_p_raw or 0.0) + (self.k_bat_avg / (p_dismissals + self.k_bat_avg)) * prior_avg
        else:
            avg_p_shrunk = None

        dot_pct_p = (p_dots / p_balls * 100.0) if p_balls > 0 else 0.0
        bnd_pct_p = ((p_fours * 4 + p_sixes * 6) / max(1, p_runs) * 100.0) if p_runs > 0 else 0.0
        delta_sr = (sr_p_raw - sr_all) if (sr_p_raw is not None and sr_all is not None) else 0.0

        c_sr = max(0.0, min(100.0, (sr_p_shrunk - 80.0) / 1.20))
        c_dot = max(0.0, min(100.0, 100.0 - dot_pct_p * 1.5))
        c_bnd = max(0.0, min(100.0, bnd_pct_p * 1.25))
        c_delta = max(0.0, min(100.0, 50.0 + delta_sr * 1.5))

        if p_dismissals > 0 and avg_p_shrunk is not None:
            c_avg = max(0.0, min(100.0, (avg_p_shrunk - 10.0) * 2.0))
            bpps = 0.35 * c_sr + 0.25 * c_avg + 0.15 * c_dot + 0.15 * c_bnd + 0.10 * c_delta
            profile_tag = None
        else:
            # Option B proportional reweighting for undefeated batter in window
            bpps = 0.4667 * c_sr + 0.2000 * c_dot + 0.2000 * c_bnd + 0.1333 * c_delta
            profile_tag = "UNDEFEATED_IN_WINDOW"

        # Career rates
        strike_rate_career = round(sr_all, 2) if sr_all is not None else None
        batting_avg_career = round(avg_all, 2) if avg_all is not None else None
        dot_pct_career = round(total_dots / total_balls * 100.0, 2) if total_balls > 0 else None
        boundary_pct_career = round((total_fours * 4 + total_sixes * 6) / total_runs * 100.0, 2) if total_runs > 0 else None
        not_outs = max(0, non_dnb_innings - total_dismissals)

        return BattingProfile(
            matches=len(matches_faced),
            innings=non_dnb_innings,
            dnb_count=dnb_count,
            zero_ball_batted_count=zero_ball_batted,
            runs=total_runs,
            balls_faced=total_balls,
            dismissals=total_dismissals,
            not_outs=not_outs,
            batting_average=batting_avg_career,
            strike_rate=strike_rate_career,
            fours=total_fours,
            sixes=total_sixes,
            boundaries=total_fours + total_sixes,
            boundary_pct=boundary_pct_career,
            dot_balls=total_dots,
            dot_pct=dot_pct_career,
            bpps=round(bpps, 2),
            profile_tag=profile_tag,
            phase_splits=phase_splits_map,
            position_splits=pos_splits,
            bowler_matchups=bowler_matchups_map,
            pace_vs_spin=pace_spin_map,
            bowling_style_matchups=style_matchups_map,
            partnerships=partnerships_list,
            outcome_splits=outcome_splits_map,
        )
