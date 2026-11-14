"""CPPAE Batting Pressure Performance Engine (Phase 1B - Workstream E).

Computes dataset-observed batting baseline metrics, pressure strike rates, pressure
averages, dot-ball suppression, boundary execution, and delta strike rates.
Applies Empirical Bayes shrinkage (K_bat = 30) and normalizes components into BPPS [0, 100].
"""

from dataclasses import dataclass
from typing import Any

from src.cmie.match_context import PreDeliveryState
from src.ingestion.normalizer import is_ball_faced, is_valid_wicket


@dataclass
class BatterPressureMetrics:
    """Detailed statistical and pressure metrics for an individual batter."""

    player_id: str
    canonical_name: str
    match_appearances: int
    balls_faced_total: int
    runs_total: int
    sr_total: float | None
    avg_total: float | None
    balls_faced_pressure: int
    runs_pressure: int
    fours_pressure: int
    sixes_pressure: int
    dots_pressure: int
    dismissals_pressure: int
    sr_pressure_raw: float | None
    avg_pressure_raw: float | None
    sr_pressure_shrunk: float | None
    avg_pressure_shrunk: float | None
    dot_pct_pressure: float | None
    boundary_pct_pressure: float | None
    delta_sr: float | None
    bpps: float  # [0.0, 100.0]
    is_qualified: bool = False
    profile_tag: str | None = None


class BattingPerformanceEngine:
    """Calculates BPPS and detailed batting pressure metrics."""

    def __init__(self, k_bat: float = 30.0, k_bat_avg: float = 5.0) -> None:
        self.k_bat = k_bat
        self.k_bat_avg = k_bat_avg

    def calculate_metrics(
        self,
        deliveries: list[dict[str, Any]],
        states: list[PreDeliveryState],
        player_names: dict[str, str],
        match_appearances: dict[str, int],
        min_balls_faced: int = 120,
        min_pressure_balls: int = 40,
        min_matches: int = 10,
    ) -> list[BatterPressureMetrics]:
        """Aggregate delivery statistics and compute BPPS scores."""
        bf_all: dict[str, int] = {}
        runs_all: dict[str, int] = {}
        dismissals_all: dict[str, int] = {}

        bf_p: dict[str, int] = {}
        runs_p: dict[str, int] = {}
        fours_p: dict[str, int] = {}
        sixes_p: dict[str, int] = {}
        dots_p: dict[str, int] = {}
        dismissals_p: dict[str, int] = {}

        for d, st in zip(deliveries, states, strict=False):
            if st.mpt == "SUPER_OVER":
                continue  # Quarantined

            et = str(d.get("extras_type", "None")).strip().lower()
            s_id = st.striker_id
            runs_bat = int(d.get("runs", 0) or 0)
            is_w = is_valid_wicket(d)
            dismissed_pid = str(d.get("dismissed_player_id", "")).strip()

            # Record dismissal for the batsman who was actually dismissed (striker or non-striker)
            if is_w and dismissed_pid:
                dismissals_all[dismissed_pid] = dismissals_all.get(dismissed_pid, 0) + 1
                if st.is_pressure:
                    dismissals_p[dismissed_pid] = dismissals_p.get(dismissed_pid, 0) + 1

            if not is_ball_faced(et):
                continue

            bf_all[s_id] = bf_all.get(s_id, 0) + 1
            runs_all[s_id] = runs_all.get(s_id, 0) + runs_bat

            if st.is_pressure:
                bf_p[s_id] = bf_p.get(s_id, 0) + 1
                runs_p[s_id] = runs_p.get(s_id, 0) + runs_bat
                if runs_bat == 0 and et != "overstep":
                    dots_p[s_id] = dots_p.get(s_id, 0) + 1
                elif runs_bat == 4:
                    fours_p[s_id] = fours_p.get(s_id, 0) + 1
                elif runs_bat == 6:
                    sixes_p[s_id] = sixes_p.get(s_id, 0) + 1

        # Calculate population priors for Empirical Bayes
        total_p_runs = sum(runs_p.values())
        total_p_bf = sum(bf_p.values())
        total_p_dismissals = sum(dismissals_p.values())

        prior_sr = (total_p_runs / max(1, total_p_bf)) * 100.0 if total_p_bf > 0 else 140.0
        prior_avg = (total_p_runs / max(1, total_p_dismissals)) if total_p_dismissals > 0 else 20.0

        results: list[BatterPressureMetrics] = []

        all_batter_ids = set(bf_all.keys()) | set(dismissals_all.keys())
        for p in all_batter_ids:
            total_bf = bf_all.get(p, 0)
            total_r = runs_all.get(p, 0)
            total_d = dismissals_all.get(p, 0)
            p_bf = bf_p.get(p, 0)
            p_r = runs_p.get(p, 0)
            p_4 = fours_p.get(p, 0)
            p_6 = sixes_p.get(p, 0)
            p_dot = dots_p.get(p, 0)
            p_d = dismissals_p.get(p, 0)
            matches = match_appearances.get(p, 0)

            sr_all = (total_r / total_bf * 100.0) if total_bf > 0 else None
            avg_all = (total_r / total_d) if total_d > 0 else None

            sr_p_raw = (p_r / p_bf * 100.0) if p_bf > 0 else None
            avg_p_raw = (p_r / p_d) if p_d > 0 else None

            # Empirical Bayes shrinkage
            if p_bf > 0:
                sr_p_shrunk = (p_bf / (p_bf + self.k_bat)) * (sr_p_raw or 0.0) + (self.k_bat / (p_bf + self.k_bat)) * prior_sr
            else:
                sr_p_shrunk = prior_sr

            if p_d > 0:
                avg_p_shrunk = (p_d / (p_d + self.k_bat_avg)) * (avg_p_raw or 0.0) + (self.k_bat_avg / (p_d + self.k_bat_avg)) * prior_avg
            else:
                avg_p_shrunk = None

            dot_pct = (p_dot / p_bf * 100.0) if p_bf > 0 else 0.0
            bnd_pct = ((p_4 * 4 + p_6 * 6) / max(1, p_r) * 100.0) if p_r > 0 else 0.0
            delta_sr = (sr_p_raw - sr_all) if (sr_p_raw is not None and sr_all is not None) else 0.0

            # Component scoring
            c_sr = max(0.0, min(100.0, (sr_p_shrunk - 80.0) / 1.20))
            c_dot = max(0.0, min(100.0, 100.0 - dot_pct * 1.5))
            c_bnd = max(0.0, min(100.0, bnd_pct * 1.25))
            c_delta = max(0.0, min(100.0, 50.0 + delta_sr * 1.5))

            if p_d > 0 and avg_p_shrunk is not None:
                c_avg = max(0.0, min(100.0, (avg_p_shrunk - 10.0) * 2.0))
                bpps = 0.35 * c_sr + 0.25 * c_avg + 0.15 * c_dot + 0.15 * c_bnd + 0.10 * c_delta
                profile_tag = None
            else:
                # Decision 1 — Option B: Proportional reweighting across four observed components for undefeated batters
                bpps = 0.4667 * c_sr + 0.2000 * c_dot + 0.2000 * c_bnd + 0.1333 * c_delta
                profile_tag = "UNDEFEATED_IN_WINDOW"

            is_qual = (total_bf >= min_balls_faced) and (p_bf >= min_pressure_balls) and (matches >= min_matches)

            results.append(BatterPressureMetrics(
                player_id=p,
                canonical_name=player_names.get(p, f"Player_{p}"),
                match_appearances=matches,
                balls_faced_total=total_bf,
                runs_total=total_r,
                sr_total=round(sr_all, 2) if sr_all is not None else None,
                avg_total=round(avg_all, 2) if avg_all is not None else None,
                balls_faced_pressure=p_bf,
                runs_pressure=p_r,
                fours_pressure=p_4,
                sixes_pressure=p_6,
                dots_pressure=p_dot,
                dismissals_pressure=p_d,
                sr_pressure_raw=round(sr_p_raw, 2) if sr_p_raw is not None else None,
                avg_pressure_raw=round(avg_p_raw, 2) if avg_p_raw is not None else None,
                sr_pressure_shrunk=round(sr_p_shrunk, 2) if sr_p_shrunk is not None else None,
                avg_pressure_shrunk=round(avg_p_shrunk, 2) if avg_p_shrunk is not None else None,
                dot_pct_pressure=round(dot_pct, 2),
                boundary_pct_pressure=round(bnd_pct, 2),
                delta_sr=round(delta_sr, 2),
                bpps=round(bpps, 2),
                is_qualified=is_qual,
                profile_tag=profile_tag,
            ))

        return results
