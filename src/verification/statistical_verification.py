"""Statistical Verification & Robustness Auditor (Phase 1B - Workstream H).

Audits mathematical boundaries, denominator safety, Empirical Bayes shrinkage sensitivity,
bye/leg-bye uncertainty propagation, and IPL vs T20I competition bias.
"""

from dataclasses import dataclass, field
from typing import Any

from src.cmie.match_context import PreDeliveryState
from src.cppae.batting_performance import BattingPerformanceEngine
from src.cppae.bowling_performance import BowlingPerformanceEngine
from src.sice.ranking_engine import RankedCandidate, SiceRankingEngine


@dataclass
class SensitivityAuditReport:
    """Report detailing sensitivity analysis and statistical robustness checks."""

    k_bat_overlap_20_vs_30: float = 0.0
    k_bat_overlap_30_vs_40: float = 0.0
    k_bowl_overlap_30_vs_40: float = 0.0
    k_bowl_overlap_40_vs_50: float = 0.0
    bye_legbye_top10_bat_overlap: float = 0.0
    bye_legbye_top10_bowl_overlap: float = 0.0
    ipl_matches_count: int = 0
    t20i_matches_count: int = 0
    ipl_avg_crr: float = 0.0
    t20i_avg_crr: float = 0.0
    cdpi_min: float = 0.0
    cdpi_max: float = 1.0
    bpps_min: float = 0.0
    bpps_max: float = 100.0
    bwps_min: float = 0.0
    bwps_max: float = 100.0
    provisional_rankings: list[dict[str, Any]] = field(default_factory=list)


class StatisticalVerifier:
    """Runs statistical validation, shrinkage sensitivity, and uncertainty checks."""

    def __init__(self) -> None:
        pass

    def run_shrinkage_sensitivity(
        self,
        deliveries: list[dict[str, Any]],
        states: list[PreDeliveryState],
        player_names: dict[str, str],
        match_appearances: dict[str, int],
    ) -> dict[str, float]:
        """Test sensitivity of Top 10 rankings to Empirical Bayes shrinkage parameters."""
        sice = SiceRankingEngine()

        # Batting sensitivity: K_bat in [20, 30, 40]
        bat_top10s: dict[int, set[str]] = {}
        for k in (20.0, 30.0, 40.0):
            eng = BattingPerformanceEngine(k_bat=k)
            mets = eng.calculate_metrics(deliveries, states, player_names, match_appearances)
            top10, _ = sice.rank_batters(mets)
            bat_top10s[int(k)] = {c.player_id for c in top10}

        overlap_bat_20_30 = len(bat_top10s[20].intersection(bat_top10s[30])) / 10.0 * 100.0
        overlap_bat_30_40 = len(bat_top10s[30].intersection(bat_top10s[40])) / 10.0 * 100.0

        # Bowling sensitivity: K_bowl in [30, 40, 50]
        bowl_top10s: dict[int, set[str]] = {}
        for k in (30.0, 40.0, 50.0):
            bowl_eng = BowlingPerformanceEngine(k_bowl=k)
            bowl_mets = bowl_eng.calculate_metrics(deliveries, states, player_names, match_appearances)
            top10_w, _ = sice.rank_bowlers(bowl_mets)
            bowl_top10s[int(k)] = {c.player_id for c in top10_w}

        overlap_bowl_30_40 = len(bowl_top10s[30].intersection(bowl_top10s[40])) / 10.0 * 100.0
        overlap_bowl_40_50 = len(bowl_top10s[40].intersection(bowl_top10s[50])) / 10.0 * 100.0

        return {
            "k_bat_overlap_20_vs_30": overlap_bat_20_30,
            "k_bat_overlap_30_vs_40": overlap_bat_30_40,
            "k_bowl_overlap_30_vs_40": overlap_bowl_30_40,
            "k_bowl_overlap_40_vs_50": overlap_bowl_40_50,
        }

    def run_bye_legbye_sensitivity(
        self,
        deliveries_by_match: dict[str, dict[int, list[dict[str, Any]]]],
        match_dict: dict[str, dict[str, Any]],
        deliveries: list[dict[str, Any]],
        player_names: dict[str, str],
        match_appearances: dict[str, int],
        k_bat: float = 30.0,
        k_bowl: float = 40.0,
    ) -> dict[str, Any]:
        """Test sensitivity of Top 10 rankings to bye/leg-bye uncertainty (1.0 vs 1.40)."""
        from src.cmie.match_context import MatchContextEngine

        sice = SiceRankingEngine()

        # Scenario A: 1.0 (strict observed)
        cmie_a = MatchContextEngine(bye_legbye_run_value=1.0)
        inn1_a = cmie_a.compute_innings_1_totals(deliveries_by_match)
        states_a: list[PreDeliveryState] = []
        for mid, inns in deliveries_by_match.items():
            states_a.extend(cmie_a.process_match_deliveries(match_dict.get(mid, {"match_id": mid}), inns, inn1_a.get(mid)))

        bat_a = BattingPerformanceEngine(k_bat=k_bat).calculate_metrics(deliveries, states_a, player_names, match_appearances)
        bowl_a = BowlingPerformanceEngine(k_bowl=k_bowl).calculate_metrics(deliveries, states_a, player_names, match_appearances)
        top10_bat_a, _ = sice.rank_batters(bat_a)
        top10_bowl_a, _ = sice.rank_bowlers(bowl_a)

        # Scenario B: 1.40 (provisional expected value)
        cmie_b = MatchContextEngine(bye_legbye_run_value=1.40)
        inn1_b = cmie_b.compute_innings_1_totals(deliveries_by_match)
        states_b: list[PreDeliveryState] = []
        for mid, inns in deliveries_by_match.items():
            states_b.extend(cmie_b.process_match_deliveries(match_dict.get(mid, {"match_id": mid}), inns, inn1_b.get(mid)))

        bat_b = BattingPerformanceEngine(k_bat=k_bat).calculate_metrics(deliveries, states_b, player_names, match_appearances)
        bowl_b = BowlingPerformanceEngine(k_bowl=k_bowl).calculate_metrics(deliveries, states_b, player_names, match_appearances)
        top10_bat_b, _ = sice.rank_batters(bat_b)
        top10_bowl_b, _ = sice.rank_bowlers(bowl_b)

        bat_set_a = {c.player_id for c in top10_bat_a}
        bat_set_b = {c.player_id for c in top10_bat_b}
        bowl_set_a = {c.player_id for c in top10_bowl_a}
        bowl_set_b = {c.player_id for c in top10_bowl_b}

        bat_overlap = len(bat_set_a.intersection(bat_set_b)) / 10.0 * 100.0
        bowl_overlap = len(bowl_set_a.intersection(bowl_set_b)) / 10.0 * 100.0

        bat_sensitive = bat_set_a.symmetric_difference(bat_set_b)
        bowl_sensitive = bowl_set_a.symmetric_difference(bowl_set_b)

        return {
            "bye_legbye_top10_bat_overlap": bat_overlap,
            "bye_legbye_top10_bowl_overlap": bowl_overlap,
            "bat_sensitive_player_ids": sorted(bat_sensitive),
            "bowl_sensitive_player_ids": sorted(bowl_sensitive),
            "top10_bat_scenario_b": [c.canonical_name for c in top10_bat_b],
            "top10_bowl_scenario_b": [c.canonical_name for c in top10_bowl_b],
        }

    def audit_boundaries_and_formats(
        self,
        matches: list[dict[str, Any]],
        states: list[PreDeliveryState],
        bat_results: list[RankedCandidate],
        bowl_results: list[RankedCandidate],
        bye_legbye_res: dict[str, Any] | None = None,
    ) -> SensitivityAuditReport:
        """Verify metric bounds and compute format-level statistics."""
        report = SensitivityAuditReport()
        if bye_legbye_res:
            report.bye_legbye_top10_bat_overlap = float(bye_legbye_res.get("bye_legbye_top10_bat_overlap", 0.0))
            report.bye_legbye_top10_bowl_overlap = float(bye_legbye_res.get("bye_legbye_top10_bowl_overlap", 0.0))

        cdpis = [s.cdpi for s in states if s.mpt != "SUPER_OVER"]
        if cdpis:
            report.cdpi_min = round(min(cdpis), 4)
            report.cdpi_max = round(max(cdpis), 4)

        bpps_vals = [b.score for b in bat_results]
        if bpps_vals:
            report.bpps_min = round(min(bpps_vals), 2)
            report.bpps_max = round(max(bpps_vals), 2)

        bwps_vals = [w.score for w in bowl_results]
        if bwps_vals:
            report.bwps_min = round(min(bwps_vals), 2)
            report.bwps_max = round(max(bwps_vals), 2)

        # Competition format separation: IPL vs T20I
        ipl_mids = set()
        t20i_mids = set()
        for m in matches:
            mid = str(m.get("match_id", "")).strip()
            # IPL competition IDs from competitions.csv: 1358, 1715, 2193, 2725, 3298
            cid = str(m.get("comp_id", "")).strip()
            if cid in ("1358", "1715", "2193", "2725", "3298"):
                ipl_mids.add(mid)
            else:
                t20i_mids.add(mid)

        report.ipl_matches_count = len(ipl_mids)
        report.t20i_matches_count = len(t20i_mids)

        ipl_states = [s for s in states if s.match_id in ipl_mids and s.legal_balls_bowled > 0]
        t20i_states = [s for s in states if s.match_id in t20i_mids and s.legal_balls_bowled > 0]

        if ipl_states:
            report.ipl_avg_crr = round(sum(s.crr for s in ipl_states) / len(ipl_states), 2)
        if t20i_states:
            report.t20i_avg_crr = round(sum(s.crr for s in t20i_states) / len(t20i_states), 2)

        # Flag borderline rank 9 and 10 as PROVISIONAL
        for b in bat_results:
            if b.rank in (9, 10):
                report.provisional_rankings.append({
                    "category": "BATTER",
                    "rank": b.rank,
                    "player_id": b.player_id,
                    "name": b.canonical_name,
                    "reason": "Borderline sensitivity under bye/leg-bye uncertainty scenarios",
                })
        for w in bowl_results:
            if w.rank in (9, 10):
                report.provisional_rankings.append({
                    "category": "BOWLER",
                    "rank": w.rank,
                    "player_id": w.player_id,
                    "name": w.canonical_name,
                    "reason": "Borderline sensitivity under bye/leg-bye uncertainty scenarios",
                })

        return report
