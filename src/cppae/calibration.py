"""CPPAE Statistical Calibration Engine (TRD §6, §10, Phase 1B/Phase 5).

Implements:
1. Role-stratified Empirical Bayes priors with hierarchical fallback
2. Shrinkage sensitivity analysis (K_bat in [20, 30, 40], K_bowl in [30, 40, 50])
3. Clustered match-level block bootstrap for confidence intervals and rank stability
"""

import math
import random
from dataclasses import dataclass, field
from typing import Any

from src.cmie.match_context import PreDeliveryState
from src.cppae.batting_performance import BattingPerformanceEngine
from src.cppae.bowling_performance import BowlingPerformanceEngine
from src.ingestion.normalizer import (
    is_ball_faced,
    is_bowler_credited_wicket,
    is_legal_ball,
    is_valid_wicket,
    parse_runs_breakdown,
)


@dataclass
class RolePrior:
    """Prior expectations for a specific player role and format."""

    role: str
    format_tag: str
    batting_sr_prior: float
    batting_avg_prior: float
    bowling_econ_prior: float
    bowling_wkt_rate_prior: float


# Default role-stratified prior tables per TRD statistical guidelines
DEFAULT_ROLE_PRIORS: dict[tuple[str, str], RolePrior] = {
    # T20 format
    ("TOP_ORDER", "T20"): RolePrior("TOP_ORDER", "T20", 135.0, 32.0, 9.2, 3.5),
    ("MIDDLE_ORDER", "T20"): RolePrior("MIDDLE_ORDER", "T20", 142.0, 27.0, 9.0, 4.0),
    ("LOWER_ORDER", "T20"): RolePrior("LOWER_ORDER", "T20", 120.0, 15.0, 8.2, 5.0),
    ("BATTER", "T20"): RolePrior("BATTER", "T20", 138.0, 30.0, 9.5, 3.0),
    ("BOWLER", "T20"): RolePrior("BOWLER", "T20", 110.0, 12.0, 8.0, 5.5),
    ("ALL_ROUNDER", "T20"): RolePrior("ALL_ROUNDER", "T20", 136.0, 24.0, 8.6, 4.8),
    ("WICKETKEEPER", "T20"): RolePrior("WICKETKEEPER", "T20", 134.0, 28.0, 10.0, 2.0),
    # The Hundred format (5-ball overs)
    ("TOP_ORDER", "HUNDRED"): RolePrior("TOP_ORDER", "HUNDRED", 138.0, 30.0, 7.5, 3.5),
    ("MIDDLE_ORDER", "HUNDRED"): RolePrior("MIDDLE_ORDER", "HUNDRED", 145.0, 25.0, 7.3, 4.0),
    ("LOWER_ORDER", "HUNDRED"): RolePrior("LOWER_ORDER", "HUNDRED", 122.0, 14.0, 6.8, 5.0),
    ("BATTER", "HUNDRED"): RolePrior("BATTER", "HUNDRED", 140.0, 28.0, 7.8, 3.0),
    ("BOWLER", "HUNDRED"): RolePrior("BOWLER", "HUNDRED", 112.0, 11.0, 6.7, 5.5),
    ("ALL_ROUNDER", "HUNDRED"): RolePrior("ALL_ROUNDER", "HUNDRED", 138.0, 23.0, 7.1, 4.8),
    ("WICKETKEEPER", "HUNDRED"): RolePrior("WICKETKEEPER", "HUNDRED", 136.0, 26.0, 8.0, 2.0),
}


@dataclass
class BootstrapResult:
    """Confidence intervals and stability metrics from clustered bootstrap."""

    player_id: str
    role: str
    replicates: int
    score_mean: float
    score_median: float
    score_ci_lower_95: float
    score_ci_upper_95: float
    rank_stability_pct: float
    iteration_scores: list[float] = field(default_factory=list)


class StatisticalCalibrationEngine:
    """Orchestrates Empirical Bayes priors, hierarchical fallback, and bootstrap validation."""

    def __init__(
        self,
        k_bat: float = 30.0,
        k_bat_avg: float = 5.0,
        k_bowl: float = 40.0,
        seed: int = 42,
    ) -> None:
        self.k_bat = k_bat
        self.k_bat_avg = k_bat_avg
        self.k_bowl = k_bowl
        self.seed = seed

    def resolve_prior(
        self,
        role: str,
        format_tag: str,
        observed_p_runs: int = 0,
        observed_p_balls: int = 0,
        observed_p_dismissals: int = 0,
        observed_p_bowl_runs: int = 0,
        observed_p_bowl_lb: int = 0,
        balls_per_over: int = 6,
    ) -> RolePrior:
        """Resolve role prior with hierarchical fallback:

        Level 1: (Role, Format) empirical dataset prior if sufficient sample
        Level 2: (Role, Format) tabulated default
        Level 3: (Role, "T20") default scaled by balls_per_over
        Level 4: Universal default prior
        """
        role_clean = role.upper().replace(" ", "_").strip()
        fmt_clean = format_tag.upper().strip()

        # Check empirical population sample first if provided
        if observed_p_balls >= 500 and observed_p_dismissals >= 20 and observed_p_bowl_lb >= 500:
            emp_sr = (observed_p_runs / observed_p_balls) * 100.0
            emp_avg = observed_p_runs / observed_p_dismissals
            emp_econ = (observed_p_bowl_runs / observed_p_bowl_lb) * balls_per_over
            return RolePrior(
                role=role_clean,
                format_tag=fmt_clean,
                batting_sr_prior=round(emp_sr, 2),
                batting_avg_prior=round(emp_avg, 2),
                bowling_econ_prior=round(emp_econ, 2),
                bowling_wkt_rate_prior=5.0,
            )

        # Level 2: Tabulated default
        key = (role_clean, fmt_clean)
        if key in DEFAULT_ROLE_PRIORS:
            return DEFAULT_ROLE_PRIORS[key]

        # Level 3: T20 fallback scaled by format
        t20_key = (role_clean, "T20")
        if t20_key in DEFAULT_ROLE_PRIORS:
            base = DEFAULT_ROLE_PRIORS[t20_key]
            econ_scaled = base.bowling_econ_prior * (balls_per_over / 6.0)
            return RolePrior(
                role=role_clean,
                format_tag=fmt_clean,
                batting_sr_prior=base.batting_sr_prior,
                batting_avg_prior=base.batting_avg_prior,
                bowling_econ_prior=round(econ_scaled, 2),
                bowling_wkt_rate_prior=base.bowling_wkt_rate_prior,
            )

        # Level 4: Universal default
        base_econ = 8.5 * (balls_per_over / 6.0)
        return RolePrior(
            role=role_clean,
            format_tag=fmt_clean,
            batting_sr_prior=135.0,
            batting_avg_prior=25.0,
            bowling_econ_prior=round(base_econ, 2),
            bowling_wkt_rate_prior=5.0,
        )

    def shrink_batting_metrics(
        self,
        raw_sr: float | None,
        raw_avg: float | None,
        balls_faced: int,
        dismissals: int,
        prior: RolePrior,
    ) -> tuple[float | None, float | None]:
        """Apply Empirical Bayes shrinkage to batting SR and average."""
        if balls_faced > 0 and raw_sr is not None:
            shrunk_sr = (balls_faced / (balls_faced + self.k_bat)) * raw_sr + (self.k_bat / (balls_faced + self.k_bat)) * prior.batting_sr_prior
        else:
            shrunk_sr = prior.batting_sr_prior

        if dismissals > 0 and raw_avg is not None:
            shrunk_avg = (dismissals / (dismissals + self.k_bat_avg)) * raw_avg + (self.k_bat_avg / (dismissals + self.k_bat_avg)) * prior.batting_avg_prior
        else:
            shrunk_avg = None  # Preserves Option B NULL average for undefeated batters

        return (
            round(shrunk_sr, 2) if shrunk_sr is not None else None,
            round(shrunk_avg, 2) if shrunk_avg is not None else None,
        )

    def shrink_bowling_economy(
        self,
        raw_econ: float | None,
        legal_balls: int,
        prior: RolePrior,
    ) -> float:
        """Apply Empirical Bayes shrinkage to bowling economy rate."""
        if legal_balls > 0 and raw_econ is not None:
            shrunk_econ = (legal_balls / (legal_balls + self.k_bowl)) * raw_econ + (self.k_bowl / (legal_balls + self.k_bowl)) * prior.bowling_econ_prior
        else:
            shrunk_econ = prior.bowling_econ_prior
        return round(shrunk_econ, 2)

    def run_shrinkage_sensitivity(
        self,
        deliveries: list[dict[str, Any]],
        states: list[PreDeliveryState],
        player_names: dict[str, str],
        match_appearances: dict[str, int],
        k_bat_grid: tuple[float, float, float] = (20.0, 30.0, 40.0),
        k_bowl_grid: tuple[float, float, float] = (30.0, 40.0, 50.0),
        top_n: int = 10,
    ) -> dict[str, Any]:
        """Evaluate sensitivity of candidate rankings across shrinkage grid."""
        # Batting sensitivity
        bat_top_sets: dict[int, set[str]] = {}
        for k in k_bat_grid:
            b_eng = BattingPerformanceEngine(k_bat=k)
            b_mets = b_eng.calculate_metrics(deliveries, states, player_names, match_appearances)
            qual = [c for c in b_mets if c.is_qualified]
            qual.sort(key=lambda c: (c.bpps, c.balls_faced_pressure), reverse=True)
            bat_top_sets[int(k)] = {c.player_id for c in qual[:top_n]}

        # Bowling sensitivity
        bowl_top_sets: dict[int, set[str]] = {}
        for k in k_bowl_grid:
            w_eng = BowlingPerformanceEngine(k_bowl=k)
            w_mets = w_eng.calculate_metrics(deliveries, states, player_names, match_appearances)
            qual_w = [c for c in w_mets if c.is_qualified]
            qual_w.sort(key=lambda c: (c.bwps, c.legal_balls_pressure), reverse=True)
            bowl_top_sets[int(k)] = {c.player_id for c in qual_w[:top_n]}

        def overlap_pct(s1: set[str], s2: set[str]) -> float:
            if not s1 or not s2:
                return 100.0
            return round(len(s1.intersection(s2)) / float(top_n) * 100.0, 2)

        return {
            "batting_k_grid": list(k_bat_grid),
            "bowling_k_grid": list(k_bowl_grid),
            "batting_overlap_k20_k30": overlap_pct(bat_top_sets[int(k_bat_grid[0])], bat_top_sets[int(k_bat_grid[1])]),
            "batting_overlap_k30_k40": overlap_pct(bat_top_sets[int(k_bat_grid[1])], bat_top_sets[int(k_bat_grid[2])]),
            "bowling_overlap_k30_k40": overlap_pct(bowl_top_sets[int(k_bowl_grid[0])], bowl_top_sets[int(k_bowl_grid[1])]),
            "bowling_overlap_k40_k50": overlap_pct(bowl_top_sets[int(k_bowl_grid[1])], bowl_top_sets[int(k_bowl_grid[2])]),
        }

    def run_clustered_bootstrap(
        self,
        deliveries_by_match: dict[str, list[dict[str, Any]]],
        states_by_match: dict[str, list[PreDeliveryState]],
        target_player_ids: list[str],
        role: str = "BATTER",
        n_iterations: int = 100,
        balls_per_over: int = 6,
    ) -> dict[str, BootstrapResult]:
        """Execute clustered block bootstrap resampling matches with replacement."""
        rng = random.Random(self.seed)
        match_keys = list(deliveries_by_match.keys())
        n_matches = len(match_keys)

        if n_matches == 0:
            return {}

        # Pre-aggregate match-level counters
        # Batting: {mid: {pid: [bf_all, runs_all, bf_p, runs_p, dots_p, fours_p, sixes_p, d_p]}}
        # Bowling: {mid: {pid: [lb_all, runs_all, lb_p, runs_p, dots_p, bnd_p, w_p]}}
        bat_by_m: dict[str, dict[str, list[int]]] = {}
        bowl_by_m: dict[str, dict[str, list[int]]] = {}

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
                r_bat = int(d.get("runs", 0) or 0)
                _, b_runs, _ = parse_runs_breakdown(d)
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
                    bat_m[s_id][1] += r_bat
                    if st.is_pressure:
                        bat_m[s_id][2] += 1
                        bat_m[s_id][3] += r_bat
                        if r_bat == 0 and et != "overstep":
                            bat_m[s_id][4] += 1
                        elif r_bat == 4:
                            bat_m[s_id][5] += 1
                        elif r_bat == 6:
                            bat_m[s_id][6] += 1

                if is_leg:
                    if b_id not in bowl_m:
                        bowl_m[b_id] = [0, 0, 0, 0, 0, 0, 0]
                    bowl_m[b_id][0] += 1
                    bowl_m[b_id][1] += b_runs
                    if st.is_pressure:
                        bowl_m[b_id][2] += 1
                        bowl_m[b_id][3] += b_runs
                        if b_runs == 0:
                            bowl_m[b_id][4] += 1
                        if r_bat in (4, 6):
                            bowl_m[b_id][5] += 1
                        if is_bowler_w:
                            bowl_m[b_id][6] += 1
                else:
                    if b_id not in bowl_m:
                        bowl_m[b_id] = [0, 0, 0, 0, 0, 0, 0]
                    bowl_m[b_id][1] += b_runs
                    if st.is_pressure:
                        bowl_m[b_id][3] += b_runs

            bat_by_m[mid] = bat_m
            bowl_by_m[mid] = bowl_m

        scores_by_pid: dict[str, list[float]] = {pid: [] for pid in target_player_ids}
        in_top_count: dict[str, int] = dict.fromkeys(target_player_ids, 0)

        for _ in range(n_iterations):
            sampled_matches = [rng.choice(match_keys) for _ in range(n_matches)]

            if role.upper() == "BATTER":
                agg: dict[str, list[int]] = {}
                tot_p_runs = 0
                tot_p_bf = 0
                tot_p_d = 0

                for sm in sampled_matches:
                    m_data = bat_by_m.get(sm, {})
                    for pid, stats in m_data.items():
                        if pid not in agg:
                            agg[pid] = [0, 0, 0, 0, 0, 0, 0, 0]
                        for idx in range(8):
                            agg[pid][idx] += stats[idx]
                        tot_p_bf += stats[2]
                        tot_p_runs += stats[3]
                        tot_p_d += stats[7]

                prior_sr = (tot_p_runs / max(1, tot_p_bf)) * 100.0 if tot_p_bf > 0 else 140.0
                prior_avg = (tot_p_runs / max(1, tot_p_d)) if tot_p_d > 0 else 20.0

                it_scores: dict[str, float] = {}
                for pid in target_player_ids:
                    s = agg.get(pid, [0, 0, 0, 0, 0, 0, 0, 0])
                    bf_all, r_all, bf_p, r_p, dots_p, f4_p, s6_p, d_p = s
                    sr_all = (r_all / bf_all * 100.0) if bf_all > 0 else None
                    sr_p_raw = (r_p / bf_p * 100.0) if bf_p > 0 else None
                    avg_p_raw = (r_p / d_p) if d_p > 0 else None

                    sr_shrunk = (bf_p / (bf_p + self.k_bat)) * (sr_p_raw or 0.0) + (self.k_bat / (bf_p + self.k_bat)) * prior_sr if bf_p > 0 else prior_sr
                    avg_shrunk = (d_p / (d_p + self.k_bat_avg)) * (avg_p_raw or 0.0) + (self.k_bat_avg / (d_p + self.k_bat_avg)) * prior_avg if d_p > 0 else None

                    dot_pct = (dots_p / bf_p * 100.0) if bf_p > 0 else 0.0
                    bnd_pct = ((f4_p * 4 + s6_p * 6) / max(1, r_p) * 100.0) if r_p > 0 else 0.0
                    delta_sr = (sr_p_raw - sr_all) if (sr_p_raw is not None and sr_all is not None) else 0.0

                    c_sr = max(0.0, min(100.0, (sr_shrunk - 80.0) / 1.20))
                    c_dot = max(0.0, min(100.0, 100.0 - dot_pct * 1.5))
                    c_bnd = max(0.0, min(100.0, bnd_pct * 1.25))
                    c_delta = max(0.0, min(100.0, 50.0 + delta_sr * 1.5))

                    if d_p > 0 and avg_shrunk is not None:
                        c_avg = max(0.0, min(100.0, (avg_shrunk - 10.0) * 2.0))
                        score = 0.35 * c_sr + 0.25 * c_avg + 0.15 * c_dot + 0.15 * c_bnd + 0.10 * c_delta
                    else:
                        score = 0.4667 * c_sr + 0.2000 * c_dot + 0.2000 * c_bnd + 0.1333 * c_delta

                    it_scores[pid] = score
                    scores_by_pid[pid].append(round(score, 2))

                # Track top rank stability
                sorted_pids = sorted(it_scores.keys(), key=lambda x: it_scores[x], reverse=True)
                for rank_idx, pid in enumerate(sorted_pids):
                    if rank_idx < 10:
                        in_top_count[pid] += 1
            else:
                # Bowler bootstrap
                agg_b: dict[str, list[int]] = {}
                tot_p_runs_b = 0
                tot_p_lb_b = 0

                for sm in sampled_matches:
                    m_data_b = bowl_by_m.get(sm, {})
                    for pid, stats in m_data_b.items():
                        if pid not in agg_b:
                            agg_b[pid] = [0, 0, 0, 0, 0, 0, 0]
                        for idx in range(7):
                            agg_b[pid][idx] += stats[idx]
                        tot_p_lb_b += stats[2]
                        tot_p_runs_b += stats[3]

                prior_econ = (tot_p_runs_b / max(1, tot_p_lb_b) * balls_per_over) if tot_p_lb_b > 0 else (1.5 * balls_per_over)

                it_scores_b: dict[str, float] = {}
                for pid in target_player_ids:
                    s_b = agg_b.get(pid, [0, 0, 0, 0, 0, 0, 0])
                    lb_all, r_all, lb_p, r_p, dots_p, bnd_p, w_p = s_b
                    econ_all = (r_all / lb_all * balls_per_over) if lb_all > 0 else None
                    econ_p_raw = (r_p / lb_p * balls_per_over) if lb_p > 0 else None

                    econ_shrunk = (lb_p / (lb_p + self.k_bowl)) * (econ_p_raw or 0.0) + (self.k_bowl / (lb_p + self.k_bowl)) * prior_econ if lb_p > 0 else prior_econ

                    dot_pct = (dots_p / lb_p * 100.0) if lb_p > 0 else 0.0
                    bnd_pct = (bnd_p / lb_p * 100.0) if lb_p > 0 else 0.0
                    wkt_rate = (w_p / lb_p * 100.0) if lb_p > 0 else 0.0
                    delta_econ = (econ_all - econ_p_raw) if (econ_all is not None and econ_p_raw is not None) else 0.0

                    b_econ = max(0.0, min(100.0, (13.5 - econ_shrunk) * 13.0))
                    b_dot = max(0.0, min(100.0, dot_pct * 2.0))
                    b_bnd = max(0.0, min(100.0, (25.0 - bnd_pct) * 5.0))
                    b_wkt = max(0.0, min(100.0, wkt_rate * 12.0))
                    b_delta = max(0.0, min(100.0, 50.0 + delta_econ * 10.0))

                    score_b = 0.35 * b_econ + 0.25 * b_dot + 0.15 * b_bnd + 0.15 * b_wkt + 0.10 * b_delta
                    it_scores_b[pid] = score_b
                    scores_by_pid[pid].append(round(score_b, 2))

                sorted_pids_b = sorted(it_scores_b.keys(), key=lambda x: it_scores_b[x], reverse=True)
                for rank_idx, pid in enumerate(sorted_pids_b):
                    if rank_idx < 10:
                        in_top_count[pid] += 1

        results: dict[str, BootstrapResult] = {}
        for pid in target_player_ids:
            s_list = sorted(scores_by_pid[pid])
            if not s_list:
                continue
            n_vals = len(s_list)
            mean_val = sum(s_list) / float(n_vals)
            med_val = s_list[n_vals // 2]
            idx_low = max(0, int(math.floor(0.025 * n_vals)))
            idx_high = min(n_vals - 1, int(math.ceil(0.975 * n_vals)))
            stab_pct = (in_top_count[pid] / float(n_iterations)) * 100.0

            results[pid] = BootstrapResult(
                player_id=pid,
                role=role.upper(),
                replicates=n_iterations,
                score_mean=round(mean_val, 2),
                score_median=round(med_val, 2),
                score_ci_lower_95=round(s_list[idx_low], 2),
                score_ci_upper_95=round(s_list[idx_high], 2),
                rank_stability_pct=round(stab_pct, 2),
                iteration_scores=s_list,
            )

        return results
