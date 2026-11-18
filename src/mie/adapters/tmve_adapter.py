"""TMVE (Team Membership Verification Engine) & Eligibility Adapter for MIE (Engine 02).

Wraps TeamMembershipVerificationEngine (Dimensions 1 & 2) and EligibilityPolicyService
(Dimension 3), maintaining strict independence across relationship, currency, and eligibility.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from src.contracts.tmve import (
    EligibilityOutputContract,
    EligibilityStatus,
    RRCurrentState,
    RRRelationshipState,
    TMVEOutputContract,
)
from src.membership.eligibility_service import EligibilityPolicyService
from src.membership.tmve import TeamMembershipVerificationEngine
from src.mie.adapters.base import EngineAdapter
from src.mie.contracts import EngineName


class TMVEAdapter(EngineAdapter):
    """Adapter managing TMVE Engine 02 and Eligibility Service operations."""

    def __init__(
        self,
        tmve_engine: TeamMembershipVerificationEngine | None = None,
        eligibility_service: EligibilityPolicyService | None = None,
    ) -> None:
        super().__init__(EngineName.TMVE)
        self.tmve = tmve_engine or TeamMembershipVerificationEngine()
        self.eligibility_service = eligibility_service or EligibilityPolicyService()

    def is_available(self) -> bool:
        """Check availability of TMVE and Eligibility Service."""
        return self.tmve is not None and self.eligibility_service is not None

    def health_check(self) -> dict[str, Any]:
        """Return diagnostic health check for TMVE."""
        return {
            "engine": self.engine_name.value,
            "status": "HEALTHY",
            "tmve_health": self.tmve.health_check(),
            "eligibility_health": self.eligibility_service.health_check(),
        }

    def execute(
        self,
        player_id: UUID,
        as_of_date: date | None = None,
        target_season_id: UUID | None = None,
        **kwargs: Any,
    ) -> tuple[TMVEOutputContract, EligibilityOutputContract]:
        """Verify membership across Dimension 1 & 2 (TMVE) and evaluate Dimension 3 (Eligibility)."""
        eval_date = as_of_date or date.today()
        season_id = target_season_id or UUID("11111111-2222-3333-4444-555555555555")

        # 1. Resolve Dimensions 1 & 2 via TMVE
        tmve_output = self.tmve.verify_player_membership(
            player_id=player_id,
            as_of_date=eval_date,
            **kwargs,
        )

        # 2. Resolve Dimension 3 via Eligibility Policy Service
        elig_output = self.eligibility_service.evaluate_player_eligibility(
            player_id=player_id,
            season_id=season_id,
            as_of_date=eval_date,
        )

        return tmve_output, elig_output

    def get_fallback_result(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> tuple[TMVEOutputContract, EligibilityOutputContract]:
        """Fallback returning conservative UNKNOWN / NOT_ASSESSED status."""
        pid = (
            args[0]
            if args
            else kwargs.get("player_id", UUID("00000000-0000-0000-0000-000000000000"))
        )
        eval_date = args[1] if len(args) > 1 else kwargs.get("as_of_date", date.today())
        season_id = kwargs.get("target_season_id", UUID("11111111-2222-3333-4444-555555555555"))

        tmve_fallback = TMVEOutputContract(
            player_id=pid,
            as_of_date=eval_date,
            rr_relationship_state=RRRelationshipState.RR_RELATIONSHIP_UNKNOWN,
            rr_current_state=RRCurrentState.UNKNOWN,
            rr_seasons=[],
            other_ipl_teams=[],
            verified_rr_appearances=0,
            evidence_verification_ids=[],
            verification_date=eval_date,
            membership_confidence=None,
            negative_verification_met=False,
            review_status="REVIEW_REQUIRED",
            review_reason_codes=["TMVE_ADAPTER_FALLBACK"],
        )

        elig_fallback = EligibilityOutputContract(
            player_id=pid,
            target_season_id=season_id,
            eligibility_status=EligibilityStatus.NOT_ASSESSED,
            verified=False,
        )

        return tmve_fallback, elig_fallback
