"""CPPAE Bowling Pressure Performance Engine (Phase 1B - Workstream F).

Computes dataset-observed bowling baseline metrics, pressure economy rates, dot-ball %,
boundary suppression, bowler-credited dismissals (excluding run outs and non-bowler wickets),
and High-Leverage Execution Score (HLES).
Applies Empirical Bayes shrinkage (K_bowl = 40) and normalizes components into BWPS [0, 100].
"""

from dataclasses import dataclass
from typing import Any

from src.cmie.match_context import PreDeliveryState
from src.ingestion.normalizer import (
    is_bowler_credited_wicket,
    is_legal_ball,
    is_valid_wicket,
    parse_runs_breakdown,
)


@dataclass
class BowlerPressureMetrics:
    """Detailed statistical and pressure metrics for an individual bowler."""

    player_id: str
    canonical_name: str
    match_appearances: int
    legal_balls_total: int
    runs_conceded_total: int
    wickets_total: int
    econ_total: float | None
    legal_balls_pressure: int
    runs_conceded_pressure: int
    dots_pressure: int
    boundaries_conceded_pressure: int
    wickets_pressure: int
    econ_pressure_raw: float | None
    econ_pressure_shrunk: float | None
    dot_pct_pressure: float | None
    boundary_pct_pressure: float | None
    hles: float | None
    delta_econ: float | None
    bwps: float  # [0.0, 100.0]
    is_qualified: bool = False
    balls_per_over: int = 6
    overs_display: str = "0.0"
    bowling_avg_total: float | None = None
    bowling_sr_total: float | None = None
    dot_pct_total: float | None = None


class BowlingPerformanceEngine:
    """Calculates BWPS and detailed bowling pressure metrics."""

    def __init__(self, k_bowl: float = 40.0, balls_per_over: int = 6) -> None:
        self.k_bowl = k_bowl
        self.balls_per_over = balls_per_over

    def calculate_metrics(
        self,
        deliveries: list[dict[str, Any]],
        states: list[PreDeliveryState],
        player_names: dict[str, str],
        match_appearances: dict[str, int],
        min_legal_balls: int = 120,
        min_pressure_balls: int = 36,
        min_matches: int = 10,
    ) -> list[BowlerPressureMetrics]:
        """Aggregate bowling deliveries and compute BWPS scores."""
        lb_all: dict[str, int] = {}
        runs_all: dict[str, int] = {}
        wickets_all: dict[str, int] = {}
        dots_all: dict[str, int] = {}

        lb_p: dict[str, int] = {}
        runs_p: dict[str, int] = {}
        dots_p: dict[str, int] = {}
        bnd_p: dict[str, int] = {}
        wickets_p: dict[str, int] = {}

        for d, st in zip(deliveries, states, strict=False):
            if st.mpt == "SUPER_OVER":
                continue  # Quarantined

            et = str(d.get("extras_type", "None")).strip().lower()
            is_legal = is_legal_ball(et)
            b_id = st.bowler_id

            # Crucial: bowler conceded runs (Rule R5: excludes byes, leg-byes, penalty)
            _, bowler_runs, _ = parse_runs_breakdown(d)
            runs_bat = int(d.get("runs", 0) or 0)

            # Bowler credited wicket check
            dt = str(d.get("dismissal_type", "")).strip()
            is_w = is_valid_wicket(d) and is_bowler_credited_wicket(dt)

            if is_legal:
                lb_all[b_id] = lb_all.get(b_id, 0) + 1
                runs_all[b_id] = runs_all.get(b_id, 0) + bowler_runs
                if bowler_runs == 0:
                    dots_all[b_id] = dots_all.get(b_id, 0) + 1
                if is_w:
                    wickets_all[b_id] = wickets_all.get(b_id, 0) + 1

                if st.is_pressure:
                    lb_p[b_id] = lb_p.get(b_id, 0) + 1
                    runs_p[b_id] = runs_p.get(b_id, 0) + bowler_runs
                    if bowler_runs == 0:
                        dots_p[b_id] = dots_p.get(b_id, 0) + 1
                    if runs_bat in (4, 6):
                        bnd_p[b_id] = bnd_p.get(b_id, 0) + 1
                    if is_w:
                        wickets_p[b_id] = wickets_p.get(b_id, 0) + 1
            else:
                # Wides and no-balls add to bowler runs conceded even if not legal balls
                runs_all[b_id] = runs_all.get(b_id, 0) + bowler_runs
                if st.is_pressure:
                    runs_p[b_id] = runs_p.get(b_id, 0) + bowler_runs

        # Calculate population prior for Empirical Bayes
        total_p_runs = sum(runs_p.values())
        total_p_lb = sum(lb_p.values())
        default_prior = 1.5 * self.balls_per_over
        prior_econ = (total_p_runs / max(1, total_p_lb) * self.balls_per_over) if total_p_lb > 0 else default_prior

        results: list[BowlerPressureMetrics] = []

        all_bowler_ids = set(lb_all.keys())
        for b in all_bowler_ids:
            total_lb = lb_all.get(b, 0)
            total_r = runs_all.get(b, 0)
            total_w = wickets_all.get(b, 0)
            total_dots = dots_all.get(b, 0)
            p_lb = lb_p.get(b, 0)
            p_r = runs_p.get(b, 0)
            p_dot = dots_p.get(b, 0)
            p_bnd = bnd_p.get(b, 0)
            p_w = wickets_p.get(b, 0)
            matches = match_appearances.get(b, 0)

            econ_all = (total_r / total_lb * self.balls_per_over) if total_lb > 0 else None
            econ_p_raw = (p_r / p_lb * self.balls_per_over) if p_lb > 0 else None

            # Empirical Bayes shrinkage on pressure economy
            if p_lb > 0:
                econ_p_shrunk = (p_lb / (p_lb + self.k_bowl)) * (econ_p_raw or 0.0) + (self.k_bowl / (p_lb + self.k_bowl)) * prior_econ
            else:
                econ_p_shrunk = prior_econ

            dot_pct = (p_dot / p_lb * 100.0) if p_lb > 0 else 0.0
            bnd_pct = (p_bnd / p_lb * 100.0) if p_lb > 0 else 0.0
            wkt_rate = (p_w / p_lb * 100.0) if p_lb > 0 else 0.0
            hles = ((2.0 * p_w + 1.0 * p_dot) / p_lb) if p_lb > 0 else 0.0
            delta_econ = (econ_all - econ_p_raw) if (econ_all is not None and econ_p_raw is not None) else 0.0

            # Component scoring
            b_econ = max(0.0, min(100.0, (13.5 - econ_p_shrunk) * 13.0))
            b_dot = max(0.0, min(100.0, dot_pct * 2.0))
            b_bnd = max(0.0, min(100.0, (25.0 - bnd_pct) * 5.0))
            b_wkt = max(0.0, min(100.0, wkt_rate * 12.0))
            b_delta = max(0.0, min(100.0, 50.0 + delta_econ * 10.0))

            bwps = 0.35 * b_econ + 0.25 * b_dot + 0.15 * b_bnd + 0.15 * b_wkt + 0.10 * b_delta

            is_qual = (total_lb >= min_legal_balls) and (p_lb >= min_pressure_balls) and (matches >= min_matches)

            overs_display = f"{total_lb // self.balls_per_over}.{total_lb % self.balls_per_over}"
            bowling_avg = round(total_r / total_w, 2) if total_w > 0 else None
            bowling_sr = round(total_lb / total_w, 2) if total_w > 0 else None
            dot_pct_all = round(total_dots / total_lb * 100.0, 2) if total_lb > 0 else None

            results.append(BowlerPressureMetrics(
                player_id=b,
                canonical_name=player_names.get(b, f"Player_{b}"),
                match_appearances=matches,
                legal_balls_total=total_lb,
                runs_conceded_total=total_r,
                wickets_total=total_w,
                econ_total=round(econ_all, 2) if econ_all is not None else None,
                legal_balls_pressure=p_lb,
                runs_conceded_pressure=p_r,
                dots_pressure=p_dot,
                boundaries_conceded_pressure=p_bnd,
                wickets_pressure=p_w,
                econ_pressure_raw=round(econ_p_raw, 2) if econ_p_raw is not None else None,
                econ_pressure_shrunk=round(econ_p_shrunk, 2),
                dot_pct_pressure=round(dot_pct, 2),
                boundary_pct_pressure=round(bnd_pct, 2),
                hles=round(hles, 4),
                delta_econ=round(delta_econ, 2),
                bwps=round(bwps, 2),
                is_qualified=is_qual,
                balls_per_over=self.balls_per_over,
                overs_display=overs_display,
                bowling_avg_total=bowling_avg,
                bowling_sr_total=bowling_sr,
                dot_pct_total=dot_pct_all,
            ))

        return results
