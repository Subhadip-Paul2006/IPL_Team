"""Data Quality and Reconciliation Service (Historical & Multi-Source).

Part of Phase 1 Historical Data Pipeline Closure (Track A).
Implements BaseDataQualityService for delivery-to-innings reconciliation,
cricket invariant validation, extras consistency, and historical DQ reporting.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.contracts.match import Delivery, Innings, Match
from src.quality.base import BaseDataQualityService


class ReconciliationReport:
    """Detailed reconciliation report for match and innings deliveries."""

    def __init__(self) -> None:
        self.innings_reconciliations: list[dict[str, Any]] = []
        self.invariant_failures: list[dict[str, Any]] = []
        self.total_matches: int = 0
        self.reconciled_matches: int = 0
        self.discrepancy_matches: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_matches": self.total_matches,
            "reconciled_matches": self.reconciled_matches,
            "discrepancy_matches": self.discrepancy_matches,
            "reconciliation_rate": (
                round(self.reconciled_matches / self.total_matches * 100, 2)
                if self.total_matches > 0
                else 100.0
            ),
            "invariant_failure_count": len(self.invariant_failures),
            "innings_count": len(self.innings_reconciliations),
            "discrepancy_details": [
                r for r in self.innings_reconciliations if not r["is_reconciled"]
            ],
        }


class DataQualityReconciliationService(BaseDataQualityService):
    """Data Quality verification and delivery reconciliation engine."""

    def __init__(self) -> None:
        self._innings_registry: dict[str, Innings] = {}
        self._deliveries_by_innings: dict[str, list[Delivery]] = {}

    def get_service_name(self) -> str:
        return "data_quality_reconciliation_service"

    def health_check(self) -> dict[str, Any]:
        return {
            "service": self.get_service_name(),
            "status": "operational",
            "registered_innings": len(self._innings_registry),
        }

    def register_innings(self, innings: Innings, deliveries: list[Delivery]) -> None:
        """Register an innings and its deliveries for in-memory reconciliation."""
        inn_key = str(innings.innings_id)
        self._innings_registry[inn_key] = innings
        self._deliveries_by_innings[inn_key] = deliveries

    def validate_invariants(self, table_name: str, records: list[dict[str, Any]]) -> bool:
        """Validate relational invariants and null-safety rules across record dictionaries."""
        tbl = table_name.lower().strip()

        for rec in records:
            if tbl == "deliveries":
                # Invariant 1: runs_total == runs_batter + runs_extras
                runs_batter = int(rec.get("runs_batter") or 0)
                runs_extras = int(rec.get("runs_extras") or 0)
                runs_total = int(rec.get("runs_total") or 0)
                if runs_total != runs_batter + runs_extras:
                    return False

                # Invariant 2: player_out_id cannot exist if is_wicket is False
                is_wicket = bool(rec.get("is_wicket", False))
                player_out_id = rec.get("player_out_id")
                if not is_wicket and player_out_id is not None:
                    return False

                # Invariant 3: non-negative runs
                if runs_batter < 0 or runs_extras < 0 or runs_total < 0:
                    return False

            elif tbl == "batting_innings":
                # Invariant: did_not_bat with balls_faced > 0 is invalid
                did_not_bat = bool(rec.get("did_not_bat", False))
                balls_faced = int(rec.get("balls_faced") or 0)
                if did_not_bat and balls_faced > 0:
                    return False

                # Invariant: dot_balls_faced <= balls_faced
                dot_balls = int(rec.get("dot_balls_faced") or 0)
                if dot_balls > balls_faced:
                    return False

            elif tbl == "matches":
                # Invariant: home_team_id != away_team_id
                home = str(rec.get("home_team_id", ""))
                away = str(rec.get("away_team_id", ""))
                if home and away and home == away:
                    return False

        return True

    def reconcile_innings_deliveries(self, innings_id: str) -> dict[str, Any]:
        """Reconcile scorecard totals against aggregated delivery events for a given innings."""
        inn_key = str(innings_id)
        innings = self._innings_registry.get(inn_key)
        deliveries = self._deliveries_by_innings.get(inn_key, [])

        if not innings:
            return {
                "innings_id": innings_id,
                "found": False,
                "is_reconciled": False,
                "reason": "Innings not registered in service",
            }

        calc_runs = sum(d.runs_total for d in deliveries)
        calc_extras = sum(d.runs_extras for d in deliveries)
        calc_wickets = sum(1 for d in deliveries if d.is_wicket)
        calc_legal_balls = sum(1 for d in deliveries if not d.is_wide and not d.is_noball)

        runs_match = calc_runs == innings.total_runs
        extras_match = calc_extras == innings.total_extras
        wickets_match = calc_wickets == innings.total_wickets
        legal_balls_match = calc_legal_balls == innings.total_legal_deliveries

        is_reconciled = runs_match and extras_match and wickets_match and legal_balls_match

        return {
            "innings_id": inn_key,
            "found": True,
            "is_reconciled": is_reconciled,
            "runs": {
                "innings_total": innings.total_runs,
                "deliveries_sum": calc_runs,
                "match": runs_match,
            },
            "extras": {
                "innings_total": innings.total_extras,
                "deliveries_sum": calc_extras,
                "match": extras_match,
            },
            "wickets": {
                "innings_total": innings.total_wickets,
                "deliveries_sum": calc_wickets,
                "match": wickets_match,
            },
            "legal_balls": {
                "innings_total": innings.total_legal_deliveries,
                "deliveries_sum": calc_legal_balls,
                "match": legal_balls_match,
            },
            "total_deliveries_count": len(deliveries),
        }

    def reconcile_match(
        self,
        match: Match,
        innings_list: list[Innings],
        deliveries_list: list[Delivery],
    ) -> dict[str, Any]:
        """Perform end-to-end reconciliation for a parsed match."""
        # Index deliveries by innings_id
        delivs_by_inn: dict[UUID, list[Delivery]] = {}
        for d in deliveries_list:
            if d.innings_id not in delivs_by_inn:
                delivs_by_inn[d.innings_id] = []
            delivs_by_inn[d.innings_id].append(d)

        innings_results: list[dict[str, Any]] = []
        all_reconciled = True

        for inn in innings_list:
            self.register_innings(inn, delivs_by_inn.get(inn.innings_id, []))
            rec_result = self.reconcile_innings_deliveries(str(inn.innings_id))
            innings_results.append(rec_result)
            if not rec_result["is_reconciled"]:
                all_reconciled = False

        return {
            "match_id": str(match.match_id),
            "external_id": match.external_cricsheet_id,
            "is_reconciled": all_reconciled,
            "innings_count": len(innings_list),
            "deliveries_count": len(deliveries_list),
            "innings_details": innings_results,
        }
