"""CPPAE Bowling Analytics Engine (TRD §6, DATA_DICTIONARY §2 W01–W12, BWPS & HLES).

Calculates comprehensive bowling profiles, format-aware economy (supporting The Hundred 5-ball overs),
overs display conversion, phase analytics, batter matchups, delivery speed, line/length tracking,
BWPS with Empirical Bayes shrinkage (K_bowl = 40), and High-Leverage Execution Score (HLES).
"""

from typing import Any
from uuid import UUID

from src.cmie.match_context import PreDeliveryState
from src.contracts.cppae import (
    BowlingPhaseSplit,
    BowlingProfile,
    DeliverySpeedSummary,
    HeadToHeadMatchup,
    LineLengthSummary,
)
from src.contracts.scorecard import BowlingSpell
from src.ingestion.cricsheet_parser import determine_match_phase
from src.ingestion.normalizer import (
    is_bowler_credited_wicket,
    is_legal_ball,
    is_valid_wicket,
    parse_runs_breakdown,
    sanitize_bowl_speed,
)


class BowlingEngine:
    """Core analytics engine for Bowling Profile (W01–W12, BWPS & HLES)."""

    def __init__(
        self,
        k_bowl: float = 40.0,
        balls_per_over: int = 6,
    ) -> None:
        self.k_bowl = k_bowl
        self.balls_per_over = balls_per_over

    def calculate_profile(
        self,
        player_id: UUID | str,
        deliveries: list[dict[str, Any]],
        states: list[PreDeliveryState] | None = None,
        bowling_spells: list[BowlingSpell | dict[str, Any]] | None = None,
        matches: list[dict[str, Any]] | None = None,
        player_names: dict[str, str] | None = None,
        format_tag: str = "T20",
    ) -> BowlingProfile:
        """Compute complete BowlingProfile for player_id."""
        pid_str = str(player_id)
        names = player_names or {}
        bpo = 5 if (format_tag == "HUNDRED" or self.balls_per_over == 5) else 6

        states_aligned: list[PreDeliveryState | None] = (
            list(states) if states is not None else [None] * len(deliveries)
        )

        match_outcomes: dict[str, dict[str, Any]] = {}
        if matches:
            for m in matches:
                mid = str(m.get("match_id", ""))
                match_outcomes[mid] = m

        # 1. Total bowling counters (W02, W03, W04, W08)
        matches_bowled: set[str] = set()
        total_legal_balls = 0
        total_runs_conceded = 0
        total_wickets = 0
        total_dots = 0

        # Phase tracking (W09)
        phase_data: dict[str, dict[str, int]] = {
            "Powerplay": {"balls": 0, "runs": 0, "wickets": 0, "dots": 0},
            "Middle": {"balls": 0, "runs": 0, "wickets": 0, "dots": 0},
            "Death": {"balls": 0, "runs": 0, "wickets": 0, "dots": 0},
        }

        # Batter matchups (W10)
        batter_stats: dict[str, dict[str, int]] = {}

        # Speed metrics (W11)
        speed_list: list[float] = []
        total_deliveries_bowled = 0

        # Line and Length tracking (W12)
        tracked_balls = 0
        length_buckets: dict[str, int] = {
            "Yorker": 0,
            "Full": 0,
            "Good Length": 0,
            "Short": 0,
            "Bouncer": 0,
        }
        line_buckets: dict[str, int] = {
            "Outside Off": 0,
            "Stumps": 0,
            "Down Leg": 0,
        }

        # Pressure subset tracking for BWPS
        p_legal_balls = 0
        p_runs_conceded = 0
        p_dots = 0
        p_boundaries_conceded = 0
        p_wickets = 0

        # Population priors
        pop_p_runs = 0
        pop_p_lb = 0

        # Outcome splits
        outcome_data: dict[str, dict[str, Any]] = {
            "win": {"matches": set(), "balls": 0, "runs": 0, "wickets": 0, "dots": 0},
            "loss": {"matches": set(), "balls": 0, "runs": 0, "wickets": 0, "dots": 0},
            "tie": {"matches": set(), "balls": 0, "runs": 0, "wickets": 0, "dots": 0},
            "no_result": {"matches": set(), "balls": 0, "runs": 0, "wickets": 0, "dots": 0},
        }

        for d, st in zip(deliveries, states_aligned, strict=False):
            mpt = getattr(st, "mpt", "") if st else ""
            if mpt == "SUPER_OVER":
                continue
            if str(d.get("match_phase", "")).upper() == "SUPER_OVER":
                continue

            bowler = str(d.get("bowler_id", "") or (st.bowler_id if st else "")).strip()
            striker = str(d.get("striker_id", "") or (st.striker_id if st else "")).strip()
            mid = str(d.get("match_id", "") or (st.match_id if st else ""))

            et = str(d.get("extras_type", "None")).strip().lower()
            is_leg = is_legal_ball(et)
            is_press = getattr(st, "is_pressure", False) if st else False

            # Bowler runs conceded (Rule R5 / P5: bat + wides + noballs; excludes byes, leg-byes, penalty)
            _, bowler_runs, _ = parse_runs_breakdown(d)
            runs_bat = int(d.get("runs", 0) or 0)

            # Bowler credited wicket check
            dt = str(d.get("dismissal_type", "")).strip()
            is_w = is_valid_wicket(d) and is_bowler_credited_wicket(dt)

            # Population pressure accumulation
            if is_press and is_leg:
                pop_p_lb += 1
                pop_p_runs += bowler_runs

            if bowler != pid_str:
                continue

            total_deliveries_bowled += 1
            matches_bowled.add(mid)

            # Speed tracking (W11)
            sanitized_spd = sanitize_bowl_speed(d.get("ball_speed_kph"))
            if sanitized_spd is not None:
                speed_list.append(sanitized_spd)

            # Line & Length tracking (W12)
            px = d.get("pitch_coordinate_x")
            py = d.get("pitch_coordinate_y")
            if px is not None and py is not None:
                try:
                    x_val = float(px)
                    y_val = float(py)
                    # Enforce plausible physical pitch bounds: 0.0 <= y <= 22.0 metres, |x| <= 3.0 metres
                    if 0.0 <= y_val <= 22.0 and abs(x_val) <= 3.0:
                        tracked_balls += 1

                        # Length classification based on pitch y-coordinate (metres from stumps)
                        if y_val < 2.5:
                            length_buckets["Yorker"] += 1
                        elif y_val < 5.0:
                            length_buckets["Full"] += 1
                        elif y_val < 8.0:
                            length_buckets["Good Length"] += 1
                        elif y_val < 11.0:
                            length_buckets["Short"] += 1
                        else:
                            length_buckets["Bouncer"] += 1

                        # Line classification based on pitch x-coordinate
                        if x_val > 0.3:
                            line_buckets["Outside Off"] += 1
                        elif x_val < -0.3:
                            line_buckets["Down Leg"] += 1
                        else:
                            line_buckets["Stumps"] += 1
                except (ValueError, TypeError):
                    pass

            # Outcome setup
            m_info = match_outcomes.get(mid, {})
            ot = str(m_info.get("outcome_type", "")).lower()
            winner = str(m_info.get("winner_id", "") or m_info.get("winner", ""))
            bowler_team = str(d.get("bowling_team_id", "") or d.get("team_id", ""))
            out_key = "tie" if ot == "tie" else ("no_result" if ot in ("no_result", "") else ("win" if winner == bowler_team and winner else "loss"))

            # Over & phase
            ov = int(d.get("over_number", 0) or (st.overid - 1 if st and st.overid > 0 else 0))
            ph = determine_match_phase(ov, match_type=format_tag, balls_per_over=bpo)

            if is_leg:
                total_legal_balls += 1
                total_runs_conceded += bowler_runs
                is_dot = (bowler_runs == 0)
                if is_dot:
                    total_dots += 1
                if is_w:
                    total_wickets += 1

                # Phase accumulation
                if ph in phase_data:
                    phase_data[ph]["balls"] += 1
                    phase_data[ph]["runs"] += bowler_runs
                    if is_dot:
                        phase_data[ph]["dots"] += 1
                    if is_w:
                        phase_data[ph]["wickets"] += 1

                # Batter matchup
                if striker:
                    if striker not in batter_stats:
                        batter_stats[striker] = {"balls": 0, "runs": 0, "wickets": 0, "dots": 0, "fours": 0, "sixes": 0}
                    batter_stats[striker]["balls"] += 1
                    batter_stats[striker]["runs"] += bowler_runs
                    if is_dot:
                        batter_stats[striker]["dots"] += 1
                    if is_w:
                        batter_stats[striker]["wickets"] += 1
                    if runs_bat == 4:
                        batter_stats[striker]["fours"] += 1
                    elif runs_bat == 6:
                        batter_stats[striker]["sixes"] += 1

                # Outcome split
                if out_key in outcome_data:
                    outcome_data[out_key]["matches"].add(mid)
                    outcome_data[out_key]["balls"] += 1
                    outcome_data[out_key]["runs"] += bowler_runs
                    if is_dot:
                        outcome_data[out_key]["dots"] += 1
                    if is_w:
                        outcome_data[out_key]["wickets"] += 1

                # Pressure subset
                if is_press:
                    p_legal_balls += 1
                    p_runs_conceded += bowler_runs
                    if is_dot:
                        p_dots += 1
                    if runs_bat in (4, 6):
                        p_boundaries_conceded += 1
                    if is_w:
                        p_wickets += 1
            else:
                # Wides and no-balls add to bowler runs conceded even though not legal balls
                total_runs_conceded += bowler_runs
                if ph in phase_data:
                    phase_data[ph]["runs"] += bowler_runs
                if striker and striker in batter_stats:
                    batter_stats[striker]["runs"] += bowler_runs
                if out_key in outcome_data:
                    outcome_data[out_key]["runs"] += bowler_runs
                if is_press:
                    p_runs_conceded += bowler_runs

        # 2. Innings count from bowling spells or matches bowled
        innings_bowled = len(bowling_spells) if bowling_spells else len(matches_bowled)

        # 3. W01: Format-aware over display
        # floor(balls / bpo) + (balls % bpo) / 10
        completed_overs = total_legal_balls // bpo
        balls_in_over = total_legal_balls % bpo
        overs_display = f"{completed_overs}.{balls_in_over}"

        # 4. W05, W06, W07, W08
        bowling_avg = round(total_runs_conceded / total_wickets, 2) if total_wickets > 0 else None
        bowling_sr = round(total_legal_balls / total_wickets, 2) if total_wickets > 0 else None
        dot_pct_career = round(total_dots / total_legal_balls * 100.0, 2) if total_legal_balls > 0 else None

        # W06: Economy rate in the format's over-length: (bpo * runs) / legal_balls
        economy_career = (
            round((total_runs_conceded / total_legal_balls) * bpo, 2)
            if total_legal_balls > 0
            else None
        )

        # 5. Phase-specific bowling splits (W09)
        phase_splits_map: dict[str, BowlingPhaseSplit] = {}
        for ph, p_dict in phase_data.items():
            lb_ph = p_dict["balls"]
            r_ph = p_dict["runs"]
            w_ph = p_dict["wickets"]
            dots_ph = p_dict["dots"]

            ov_ph = f"{lb_ph // bpo}.{lb_ph % bpo}"
            econ_ph = round((r_ph / lb_ph) * bpo, 2) if lb_ph > 0 else None
            avg_ph = round(r_ph / w_ph, 2) if w_ph > 0 else None
            sr_ph = round(lb_ph / w_ph, 2) if w_ph > 0 else None
            dot_pct_ph = round(dots_ph / lb_ph * 100.0, 2) if lb_ph > 0 else None

            phase_splits_map[ph] = BowlingPhaseSplit(
                phase=ph,
                legal_balls=lb_ph,
                overs_display=ov_ph,
                runs_conceded=r_ph,
                wickets=w_ph,
                dot_balls=dots_ph,
                economy_rate=econ_ph,
                bowling_average=avg_ph,
                bowling_strike_rate=sr_ph,
                dot_pct=dot_pct_ph,
            )

        # 6. Batter-specific matchups (W10)
        batter_matchups_map: dict[str, HeadToHeadMatchup] = {}
        for s_id, s_dict in batter_stats.items():
            b_cnt = s_dict["balls"]
            r_cnt = s_dict["runs"]
            w_cnt = s_dict["wickets"]
            dots_cnt = s_dict["dots"]

            econ_bm = round((r_cnt / b_cnt) * bpo, 2) if b_cnt > 0 else None
            avg_bm = round(r_cnt / w_cnt, 2) if w_cnt > 0 else None
            sr_bm = round(r_cnt / b_cnt * 100.0, 2) if b_cnt > 0 else None
            dot_pct_bm = round(dots_cnt / b_cnt * 100.0, 2) if b_cnt > 0 else None

            batter_matchups_map[s_id] = HeadToHeadMatchup(
                opponent_id=s_id,
                opponent_name=names.get(s_id, f"Batter_{s_id}"),
                balls=b_cnt,
                runs=r_cnt,
                dismissals=w_cnt,
                dots=dots_cnt,
                fours=s_dict["fours"],
                sixes=s_dict["sixes"],
                strike_rate=sr_bm,
                economy_rate=econ_bm,
                average=avg_bm,
                dot_pct=dot_pct_bm,
                warning_flag="SMALL_SAMPLE_WARNING" if b_cnt < 18 else None,
            )

        # 7. Speed summary (W11)
        speed_summary: DeliverySpeedSummary | None = None
        if total_deliveries_bowled > 0:
            rec_count = len(speed_list)
            cov_pct = round(rec_count / total_deliveries_bowled * 100.0, 2)
            if rec_count > 0:
                speed_summary = DeliverySpeedSummary(
                    recorded_balls=rec_count,
                    total_balls=total_deliveries_bowled,
                    coverage_pct=cov_pct,
                    mean_speed_kph=round(sum(speed_list) / rec_count, 1),
                    min_speed_kph=round(min(speed_list), 1),
                    max_speed_kph=round(max(speed_list), 1),
                    status="OBSERVED",
                )
            else:
                speed_summary = DeliverySpeedSummary(
                    recorded_balls=0,
                    total_balls=total_deliveries_bowled,
                    coverage_pct=0.0,
                    mean_speed_kph=None,
                    min_speed_kph=None,
                    max_speed_kph=None,
                    status="NOT_COMPUTABLE",
                )

        # 8. Line and length summary (W12)
        line_length_summary: LineLengthSummary | None = None
        if total_deliveries_bowled > 0:
            ll_cov_pct = round(tracked_balls / total_deliveries_bowled * 100.0, 2)
            line_length_summary = LineLengthSummary(
                tracked_balls=tracked_balls,
                total_balls=total_deliveries_bowled,
                coverage_pct=ll_cov_pct,
                length_buckets=length_buckets,
                line_buckets=line_buckets,
                status="OBSERVED" if tracked_balls > 0 else "NOT_COMPUTABLE",
            )

        # 9. BWPS and HLES calculation
        prior_econ = (pop_p_runs / max(1, pop_p_lb) * bpo) if pop_p_lb > 0 else (1.5 * bpo)
        econ_p_raw = (p_runs_conceded / p_legal_balls * bpo) if p_legal_balls > 0 else None

        if p_legal_balls > 0:
            econ_p_shrunk = (p_legal_balls / (p_legal_balls + self.k_bowl)) * (econ_p_raw or 0.0) + (self.k_bowl / (p_legal_balls + self.k_bowl)) * prior_econ
        else:
            econ_p_shrunk = prior_econ

        dot_pct_p = (p_dots / p_legal_balls * 100.0) if p_legal_balls > 0 else 0.0
        bnd_pct_p = (p_boundaries_conceded / p_legal_balls * 100.0) if p_legal_balls > 0 else 0.0
        wkt_rate_p = (p_wickets / p_legal_balls * 100.0) if p_legal_balls > 0 else 0.0
        delta_econ = (economy_career - econ_p_raw) if (economy_career is not None and econ_p_raw is not None) else 0.0

        b_econ = max(0.0, min(100.0, (13.5 - econ_p_shrunk) * 13.0))
        b_dot = max(0.0, min(100.0, dot_pct_p * 2.0))
        b_bnd = max(0.0, min(100.0, (25.0 - bnd_pct_p) * 5.0))
        b_wkt = max(0.0, min(100.0, wkt_rate_p * 12.0))
        b_delta = max(0.0, min(100.0, 50.0 + delta_econ * 10.0))

        bwps = 0.35 * b_econ + 0.25 * b_dot + 0.15 * b_bnd + 0.15 * b_wkt + 0.10 * b_delta

        # HLES: High-Leverage Execution Score
        # T20 only: ((2.0 * w + 1.0 * dot) / legal_balls)
        # Non-T20: Retained as DEFERRED / None per TRD Invariant R8
        hles: float | None = None
        if format_tag in ("T20", "IT20", "IPL"):
            hles = round(((2.0 * p_wickets + 1.0 * p_dots) / p_legal_balls), 4) if p_legal_balls > 0 else 0.0
        else:
            hles = None  # DEFERRED for non-T20

        # Outcome splits
        outcome_splits_map: dict[str, dict[str, Any]] = {}
        for out_k, o_dict in outcome_data.items():
            m_set = o_dict["matches"]
            m_cnt = len(m_set)
            b_cnt = o_dict["balls"]
            r_cnt = o_dict["runs"]
            w_cnt = o_dict["wickets"]
            if m_cnt == 0 and b_cnt == 0:
                outcome_splits_map[out_k] = {
                    "matches": 0,
                    "overs_display": "0.0",
                    "legal_balls": 0,
                    "runs_conceded": 0,
                    "wickets": 0,
                    "economy_rate": None,
                    "bowling_average": None,
                }
            else:
                ov_str = f"{b_cnt // bpo}.{b_cnt % bpo}"
                outcome_splits_map[out_k] = {
                    "matches": m_cnt,
                    "overs_display": ov_str,
                    "legal_balls": b_cnt,
                    "runs_conceded": r_cnt,
                    "wickets": w_cnt,
                    "economy_rate": round((r_cnt / b_cnt) * bpo, 2) if b_cnt > 0 else None,
                    "bowling_average": round(r_cnt / w_cnt, 2) if w_cnt > 0 else None,
                }

        return BowlingProfile(
            matches=len(matches_bowled),
            innings=innings_bowled,
            legal_balls_bowled=total_legal_balls,
            overs_display=overs_display,
            balls_per_over=bpo,
            runs_conceded=total_runs_conceded,
            wickets_taken=total_wickets,
            bowler_credited_wickets=total_wickets,
            dot_balls_bowled=total_dots,
            bowling_average=bowling_avg,
            economy_rate=economy_career,
            bowling_strike_rate=bowling_sr,
            dot_pct=dot_pct_career,
            bwps=round(bwps, 2),
            hles=hles,
            phase_splits=phase_splits_map,
            batter_matchups=batter_matchups_map,
            speed_summary=speed_summary,
            line_length_summary=line_length_summary,
            outcome_splits=outcome_splits_map,
        )
