"""SICE Ranking & Match-Level Bootstrap Engine (Phase 1B - Workstream G).

Applies eligibility gates, produces deterministic Top 10 rankings and reserve lists
with strict tiebreakers, and executes 95% match-level clustered block bootstrap
(B=1,000 iterations default) for confidence intervals and rank stability analysis.
"""

import random
from dataclasses import dataclass
from typing import Any

from src.cmie.match_context import PreDeliveryState
from src.cppae.batting_performance import BatterPressureMetrics
from src.cppae.bowling_performance import BowlerPressureMetrics


@dataclass
class RankedCandidate:
    """Individual ranked player entry with statistical evidence and confidence intervals."""

    rank: int
    player_id: str
    canonical_name: str
    score: float  # BPPS or BWPS
    match_appearances: int
    volume_total: int  # BF or LB
    volume_pressure: int  # Press BF or Press LB
    key_metric_raw: float | None  # Raw SR or Raw Econ
    key_metric_shrunk: float | None  # Shrunk SR or Shrunk Econ
    delta_metric: float | None  # Delta SR or Delta Econ
    score_ci_lower: float | None = None
    score_ci_upper: float | None = None
    top10_stability_pct: float | None = None
    status: str = "TOP_10"  # TOP_10 or RESERVE
    uncertainty_flag: str = "VERIFIED"  # VERIFIED or PROVISIONAL
    role: str = "BATTER"  # BATTER or BOWLER


@dataclass
class RankingResult:
    """Complete output board for a ranking execution."""

    role_category: str  # BATTERS or BOWLERS
    qualified_candidates_count: int
    top10: list[RankedCandidate]
    reserves: list[RankedCandidate]
    bootstrap_iterations: int = 1000
    seed: int = 42


class SiceRankingEngine:
    """Ranks batters and bowlers and runs match-level clustered bootstrap."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed

    def rank_batters(
        self,
        candidates: list[BatterPressureMetrics],
        top_n: int = 10,
        reserve_n: int = 15,
    ) -> tuple[list[RankedCandidate], list[RankedCandidate]]:
        """Deterministically sort qualified batters and extract top-10 and reserves."""
        qualified = [c for c in candidates if c.is_qualified]

        # Multi-key total ordering: BPPS desc -> Press BF desc -> Total BF desc -> player_id asc
        # Two-pass stable sort ensures player_id asc lexicographic tiebreaking without type collisions
        qualified.sort(key=lambda c: str(c.player_id))
        qualified.sort(
            key=lambda c: (
                c.bpps,
                c.balls_faced_pressure,
                c.balls_faced_total,
            ),
            reverse=True,
        )

        top10: list[RankedCandidate] = []
        for i, c in enumerate(qualified[:top_n], 1):
            top10.append(RankedCandidate(
                rank=i,
                player_id=c.player_id,
                canonical_name=c.canonical_name,
                score=c.bpps,
                match_appearances=c.match_appearances,
                volume_total=c.balls_faced_total,
                volume_pressure=c.balls_faced_pressure,
                key_metric_raw=c.sr_pressure_raw,
                key_metric_shrunk=c.sr_pressure_shrunk,
                delta_metric=c.delta_sr,
                status="TOP_10",
                uncertainty_flag="VERIFIED" if i <= 8 else "PROVISIONAL",
                role="BATTER",
            ))

        reserves: list[RankedCandidate] = []
        for i, c in enumerate(qualified[top_n : top_n + reserve_n], top_n + 1):
            reserves.append(RankedCandidate(
                rank=i,
                player_id=c.player_id,
                canonical_name=c.canonical_name,
                score=c.bpps,
                match_appearances=c.match_appearances,
                volume_total=c.balls_faced_total,
                volume_pressure=c.balls_faced_pressure,
                key_metric_raw=c.sr_pressure_raw,
                key_metric_shrunk=c.sr_pressure_shrunk,
                delta_metric=c.delta_sr,
                status="RESERVE",
                uncertainty_flag="VERIFIED",
                role="BATTER",
            ))

        return top10, reserves

    def rank_bowlers(
        self,
        candidates: list[BowlerPressureMetrics],
        top_n: int = 10,
        reserve_n: int = 15,
    ) -> tuple[list[RankedCandidate], list[RankedCandidate]]:
        """Deterministically sort qualified bowlers and extract top-10 and reserves."""
        qualified = [c for c in candidates if c.is_qualified]

        # Multi-key total ordering: BWPS desc -> Press LB desc -> Total LB desc -> player_id asc
        qualified.sort(key=lambda c: str(c.player_id))
        qualified.sort(
            key=lambda c: (
                c.bwps,
                c.legal_balls_pressure,
                c.legal_balls_total,
            ),
            reverse=True,
        )

        top10: list[RankedCandidate] = []
        for i, c in enumerate(qualified[:top_n], 1):
            top10.append(RankedCandidate(
                rank=i,
                player_id=c.player_id,
                canonical_name=c.canonical_name,
                score=c.bwps,
                match_appearances=c.match_appearances,
                volume_total=c.legal_balls_total,
                volume_pressure=c.legal_balls_pressure,
                key_metric_raw=c.econ_pressure_raw,
                key_metric_shrunk=c.econ_pressure_shrunk,
                delta_metric=c.delta_econ,
                status="TOP_10",
                uncertainty_flag="VERIFIED" if i <= 8 else "PROVISIONAL",
                role="BOWLER",
            ))

        reserves: list[RankedCandidate] = []
        for i, c in enumerate(qualified[top_n : top_n + reserve_n], top_n + 1):
            reserves.append(RankedCandidate(
                rank=i,
                player_id=c.player_id,
                canonical_name=c.canonical_name,
                score=c.bwps,
                match_appearances=c.match_appearances,
                volume_total=c.legal_balls_total,
                volume_pressure=c.legal_balls_pressure,
                key_metric_raw=c.econ_pressure_raw,
                key_metric_shrunk=c.econ_pressure_shrunk,
                delta_metric=c.delta_econ,
                status="RESERVE",
                uncertainty_flag="VERIFIED",
                role="BOWLER",
            ))

        return top10, reserves

    def create_ranking_result(
        self,
        role_category: str,
        candidates: list[BatterPressureMetrics] | list[BowlerPressureMetrics],
        top10: list[RankedCandidate],
        reserves: list[RankedCandidate],
        bootstrap_iterations: int = 1000,
    ) -> RankingResult:
        """Construct a frozen RankingResult board."""
        qualified_count = len([c for c in candidates if c.is_qualified])
        return RankingResult(
            role_category=role_category,
            qualified_candidates_count=qualified_count,
            top10=top10,
            reserves=reserves,
            bootstrap_iterations=bootstrap_iterations,
            seed=self.seed,
        )

    def run_match_level_bootstrap(
        self,
        deliveries_by_match: dict[str, list[dict[str, Any]]],
        states_by_match: dict[str, list[PreDeliveryState]],
        player_names: dict[str, str],
        match_appearances: dict[str, int],
        top_batters: list[RankedCandidate],
        top_bowlers: list[RankedCandidate],
        n_iterations: int = 1000,
    ) -> None:
        """Execute match-level clustered block bootstrap to compute 95% CIs and stability."""
        rng = random.Random(self.seed)
        match_keys = list(deliveries_by_match.keys())
        n_matches = len(match_keys)

        if n_matches == 0:
            return

        # Pre-aggregate match-level stats for high-performance bootstrap
        # Batting: [bf_all, runs_all, bf_p, runs_p, dots_p, fours_p, sixes_p, d_p]
        bat_by_m: dict[str, dict[str, list[int]]] = {}
        # Bowling: [lb_all, runs_all, lb_p, runs_p, dots_p, bnd_p, w_p]
        bowl_by_m: dict[str, dict[str, list[int]]] = {}

        from src.ingestion.normalizer import (
            is_ball_faced,
            is_bowler_credited_wicket,
            is_legal_ball,
            is_valid_wicket,
            parse_runs_breakdown,
        )

        for mid in match_keys:
            bat_m: dict[str, list[int]] = {}
            bowl_m: dict[str, list[int]] = {}
            delivs = deliveries_by_match.get(mid, [])
            sts = states_by_match.get(mid, [])

            for d, st in zip(delivs, sts, strict=False):
                if st.mpt == "SUPER_OVER":
                    continue
                et = str(d.get("extras_type", "None")).strip().lower()
                is_bf = is_ball_faced(et)
                is_leg = is_legal_ball(et)
                s_id = st.striker_id
                b_id = st.bowler_id
                runs_bat = int(d.get("runs", 0) or 0)
                _, bowler_runs, _ = parse_runs_breakdown(d)
                dt = str(d.get("dismissal_type", "")).strip()
                is_w = is_valid_wicket(d)
                is_bowler_w = is_w and is_bowler_credited_wicket(dt)
                dismissed_pid = str(d.get("dismissed_player_id", "")).strip()

                if is_w and dismissed_pid and st.is_pressure:
                    if dismissed_pid not in bat_m:
                        bat_m[dismissed_pid] = [0, 0, 0, 0, 0, 0, 0, 0]
                    bat_m[dismissed_pid][7] += 1

                if is_bf:
                    if s_id not in bat_m:
                        bat_m[s_id] = [0, 0, 0, 0, 0, 0, 0, 0]
                    bat_m[s_id][0] += 1
                    bat_m[s_id][1] += runs_bat
                    if st.is_pressure:
                        bat_m[s_id][2] += 1
                        bat_m[s_id][3] += runs_bat
                        if runs_bat == 0 and et != "overstep":
                            bat_m[s_id][4] += 1
                        elif runs_bat == 4:
                            bat_m[s_id][5] += 1
                        elif runs_bat == 6:
                            bat_m[s_id][6] += 1

                if is_leg:
                    if b_id not in bowl_m:
                        bowl_m[b_id] = [0, 0, 0, 0, 0, 0, 0]
                    bowl_m[b_id][0] += 1
                    bowl_m[b_id][1] += bowler_runs
                    if st.is_pressure:
                        bowl_m[b_id][2] += 1
                        bowl_m[b_id][3] += bowler_runs
                        if bowler_runs == 0:
                            bowl_m[b_id][4] += 1
                        if runs_bat in (4, 6):
                            bowl_m[b_id][5] += 1
                        if is_bowler_w:
                            bowl_m[b_id][6] += 1
                elif et in ("wide", "overstep"):
                    if b_id not in bowl_m:
                        bowl_m[b_id] = [0, 0, 0, 0, 0, 0, 0]
                    bowl_m[b_id][1] += bowler_runs
                    if st.is_pressure:
                        bowl_m[b_id][3] += bowler_runs

            bat_by_m[mid] = bat_m
            bowl_by_m[mid] = bowl_m

        bat_tracker: dict[str, list[float]] = {b.player_id: [] for b in top_batters}
        bat_top10_hits: dict[str, int] = {b.player_id: 0 for b in top_batters}

        bowl_tracker: dict[str, list[float]] = {w.player_id: [] for w in top_bowlers}
        bowl_top10_hits: dict[str, int] = {w.player_id: 0 for w in top_bowlers}

        k_bat = 30.0
        k_bat_avg = 5.0
        k_bowl = 40.0

        for _ in range(n_iterations):
            sample_mids = [match_keys[rng.randint(0, n_matches - 1)] for _ in range(n_matches)]
            from collections import Counter
            mid_counts = Counter(sample_mids)

            # Aggregate sampled match statistics
            b_agg: dict[str, list[int]] = {}
            for mid, cnt in mid_counts.items():
                m_bats = bat_by_m.get(mid, {})
                for pid, vec in m_bats.items():
                    if pid not in b_agg:
                        b_agg[pid] = [0, 0, 0, 0, 0, 0, 0, 0]
                    for idx in range(8):
                        b_agg[pid][idx] += vec[idx] * cnt

            w_agg: dict[str, list[int]] = {}
            for mid, cnt in mid_counts.items():
                m_bowls = bowl_by_m.get(mid, {})
                for pid, vec in m_bowls.items():
                    if pid not in w_agg:
                        w_agg[pid] = [0, 0, 0, 0, 0, 0, 0]
                    for idx in range(7):
                        w_agg[pid][idx] += vec[idx] * cnt

            # Compute batting priors & scores
            p_runs_tot = sum(v[3] for v in b_agg.values())
            p_bf_tot = sum(v[2] for v in b_agg.values())
            p_d_tot = sum(v[7] for v in b_agg.values())
            prior_sr = (p_runs_tot / max(1, p_bf_tot) * 100.0) if p_bf_tot > 0 else 140.0
            prior_avg = (p_runs_tot / max(1, p_d_tot)) if p_d_tot > 0 else 20.0

            rep_bat_scores: list[tuple[str, float]] = []
            for pid, v in b_agg.items():
                bf_all, r_all, p_bf, p_r, p_dot, p_4, p_6, p_d = v
                if bf_all < 80 or p_bf < 25 or match_appearances.get(pid, 0) < 10:
                    continue
                sr_all = (r_all / bf_all * 100.0) if bf_all > 0 else 120.0
                sr_p_raw = (p_r / p_bf * 100.0) if p_bf > 0 else 140.0
                sr_p_shrunk = (p_bf / (p_bf + k_bat)) * sr_p_raw + (k_bat / (p_bf + k_bat)) * prior_sr
                avg_p_raw = (p_r / max(1, p_d))
                avg_p_shrunk = (p_d / (p_d + k_bat_avg)) * avg_p_raw + (k_bat_avg / (p_d + k_bat_avg)) * prior_avg
                dot_pct = (p_dot / p_bf * 100.0)
                bnd_pct = ((p_4 * 4 + p_6 * 6) / max(1, p_r) * 100.0)
                delta_sr = sr_p_raw - sr_all

                c_sr = max(0.0, min(100.0, (sr_p_shrunk - 80.0) / 1.20))
                c_avg = max(0.0, min(100.0, (avg_p_shrunk - 10.0) * 2.0))
                c_dot = max(0.0, min(100.0, 100.0 - dot_pct * 1.5))
                c_bnd = max(0.0, min(100.0, bnd_pct * 1.25))
                c_delta = max(0.0, min(100.0, 50.0 + delta_sr * 1.5))
                bpps = 0.35 * c_sr + 0.25 * c_avg + 0.15 * c_dot + 0.15 * c_bnd + 0.10 * c_delta
                rep_bat_scores.append((pid, bpps))

            rep_bat_scores.sort(key=lambda x: x[1], reverse=True)
            top_bats_rep = {x[0] for x in rep_bat_scores[:10]}
            bat_score_dict = dict(rep_bat_scores)

            for b in top_batters:
                pid = b.player_id
                if pid in bat_score_dict:
                    bat_tracker[pid].append(bat_score_dict[pid])
                if pid in top_bats_rep:
                    bat_top10_hits[pid] += 1

            # Compute bowling priors & scores
            w_runs_tot = sum(v[3] for v in w_agg.values())
            w_lb_tot = sum(v[2] for v in w_agg.values())
            prior_econ = (w_runs_tot / max(1, w_lb_tot) * 6.0) if w_lb_tot > 0 else 9.0

            rep_bowl_scores: list[tuple[str, float]] = []
            for pid, v in w_agg.items():
                lb_all, r_all, p_lb, p_r, p_dot, p_bnd, p_w = v
                if lb_all < 80 or p_lb < 20 or match_appearances.get(pid, 0) < 10:
                    continue
                econ_all = (r_all / lb_all * 6.0) if lb_all > 0 else 8.5
                econ_p_raw = (p_r / p_lb * 6.0) if p_lb > 0 else 9.0
                econ_p_shrunk = (p_lb / (p_lb + k_bowl)) * econ_p_raw + (k_bowl / (p_lb + k_bowl)) * prior_econ
                dot_pct = (p_dot / p_lb * 100.0)
                bnd_pct = (p_bnd / p_lb * 100.0)
                wkt_rate = (p_w / p_lb * 100.0)
                delta_econ = econ_all - econ_p_raw

                b_econ = max(0.0, min(100.0, (13.5 - econ_p_shrunk) * 13.0))
                b_dot = max(0.0, min(100.0, dot_pct * 2.0))
                b_bnd = max(0.0, min(100.0, (25.0 - bnd_pct) * 5.0))
                b_wkt = max(0.0, min(100.0, wkt_rate * 12.0))
                b_delta = max(0.0, min(100.0, 50.0 + delta_econ * 10.0))
                bwps = 0.35 * b_econ + 0.25 * b_dot + 0.15 * b_bnd + 0.15 * b_wkt + 0.10 * b_delta
                rep_bowl_scores.append((pid, bwps))

            rep_bowl_scores.sort(key=lambda x: x[1], reverse=True)
            top_bowls_rep = {x[0] for x in rep_bowl_scores[:10]}
            bowl_score_dict = dict(rep_bowl_scores)

            for w in top_bowlers:
                pid = w.player_id
                if pid in bowl_score_dict:
                    bowl_tracker[pid].append(bowl_score_dict[pid])
                if pid in top_bowls_rep:
                    bowl_top10_hits[pid] += 1

        # Populate 95% CIs and stability
        for b in top_batters:
            scores = sorted(bat_tracker[b.player_id])
            if scores:
                low_idx = int(0.025 * len(scores))
                high_idx = int(0.975 * len(scores))
                b.score_ci_lower = round(scores[min(low_idx, len(scores) - 1)], 2)
                b.score_ci_upper = round(scores[min(high_idx, len(scores) - 1)], 2)
            else:
                b.score_ci_lower = b.score
                b.score_ci_upper = b.score
            b.top10_stability_pct = round(bat_top10_hits[b.player_id] / max(1, n_iterations) * 100.0, 1)

        for w in top_bowlers:
            scores = sorted(bowl_tracker[w.player_id])
            if scores:
                low_idx = int(0.025 * len(scores))
                high_idx = int(0.975 * len(scores))
                w.score_ci_lower = round(scores[min(low_idx, len(scores) - 1)], 2)
                w.score_ci_upper = round(scores[min(high_idx, len(scores) - 1)], 2)
            else:
                w.score_ci_lower = w.score
                w.score_ci_upper = w.score
            w.top10_stability_pct = round(bowl_top10_hits[w.player_id] / max(1, n_iterations) * 100.0, 1)
