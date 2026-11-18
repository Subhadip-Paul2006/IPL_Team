"""PVRE (Player Verification & Research Engine) Adapter for MIE (Engine 07).

Wraps PVREngine and MotherController, executing the deterministic 7-step routing waterfall:
- Mode A: Existing RR incumbent research, historical splits, global form, replaceability signals.
- Mode B: Verified uncapped candidate intelligence across domestic tournaments (Ranji/SMAT/VHT).
- Safety Review Interceptor: Mandatory REVIEW_REQUIRED gating for conflicting or incomplete evidence.
- Out of Scope: Non-RR capped player classification.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID, uuid4

from src.contracts.pvre import (
    CareerCoverageState,
    PlayerCappedStatus,
    PVREOutputContract,
    PVRERequestContract,
    PVREReviewStatus,
    ResearchMode,
    RouteStatus,
)
from src.mie.adapters.base import EngineAdapter
from src.mie.contracts import EngineName
from src.pvre.engine import PVREngine


class PVREAdapter(EngineAdapter):
    """Adapter managing PVRE Engine 07 operations."""

    def __init__(self, pvre_engine: PVREngine | None = None) -> None:
        super().__init__(EngineName.PVRE)
        self.pvre = pvre_engine or PVREngine()

    def is_available(self) -> bool:
        """Check availability of PVRE engine."""
        return self.pvre is not None

    def health_check(self) -> dict[str, Any]:
        """Return diagnostic health check for PVRE."""
        return {
            "engine": self.engine_name.value,
            "status": "HEALTHY",
            "pvre_health": self.pvre.health_check()
            if hasattr(self.pvre, "health_check")
            else "ready",
        }

    def execute(
        self,
        request: PVRERequestContract | dict[str, Any],
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> PVREOutputContract:
        """Execute PVRE deterministic research workflow."""
        return self.pvre.execute_player_research(request=request, context=context)

    def get_fallback_result(self, *args: Any, **kwargs: Any) -> PVREOutputContract:
        """Fallback returning mandatory REVIEW_REQUIRED safety dossier (Rule R18, AC-29)."""
        pid = kwargs.get("player_id")
        cname = kwargs.get("canonical_name", "UNKNOWN_PLAYER")
        eval_date = kwargs.get("evaluation_date", date.today())
        target_season = kwargs.get("target_season_id", UUID("11111111-2222-3333-4444-555555555555"))

        return PVREOutputContract(
            contract_version="PVRE-2.2.0",
            research_run_id=uuid4(),
            player_id=pid,
            canonical_name=cname,
            identity_status="UNRESOLVED",
            research_mode=ResearchMode.REVIEW_REQUIRED,
            route_status=RouteStatus.ROUTED_SAFETY_REVIEW,
            evaluation_date=eval_date,
            target_season_id=target_season,
            rr_relationship_state="RR_RELATIONSHIP_UNKNOWN",
            rr_current_state="UNKNOWN",
            player_capped_status=PlayerCappedStatus.UNVERIFIED,
            ipl_uncapped_eligibility="NOT_ASSESSED",
            research_window_start=date(eval_date.year - 3, eval_date.month, eval_date.day),
            research_window_end=eval_date,
            career_coverage_state=CareerCoverageState.REVIEW_REQUIRED,
            rr_historical_profile=None,
            recent_global_performance=None,
            complete_career_profile=None,
            replaceability_assessment=None,
            competition_coverage={},
            source_record_ids=[],
            verification_record_ids=[],
            review_status=PVREReviewStatus.REVIEW_REQUIRED,
            review_reason_codes=["PVRE_ADAPTER_FALLBACK", "UNVERIFIED_EVIDENCE"],
            data_quality_summary={
                "completeness_score": 0.0,
                "notes": "PVRE adapter fallback executed.",
            },
        )
