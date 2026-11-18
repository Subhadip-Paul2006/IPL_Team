"""PIRE (Player Identity Resolution Engine) Adapter for MIE (Engine 01).

Wraps UnifiedPIRE and PlayerIdentityResolver, executing 4-tier deterministic resolution
with candidate corroboration from CDCRE and contextual attribute verification.
"""

from __future__ import annotations

from typing import Any

from src.mie.adapters.base import EngineAdapter
from src.mie.contracts import EngineName
from src.pire.models import (
    IdentityStatus,
    ResolutionResult,
    ResolutionTier,
)
from src.pire.resolver import UnifiedPIRE


class PIREAdapter(EngineAdapter):
    """Adapter isolating PIRE Engine 01 operations."""

    def __init__(self, resolver: UnifiedPIRE | None = None) -> None:
        super().__init__(EngineName.PIRE)
        self.resolver = resolver or UnifiedPIRE()

    def is_available(self) -> bool:
        """Check availability of PIRE engine."""
        return self.resolver is not None

    def health_check(self) -> dict[str, Any]:
        """Return diagnostic health check for PIRE."""
        pending = (
            len(self.resolver.review_queue.get_pending())
            if hasattr(self.resolver.review_queue, "get_pending")
            else 0
        )
        return {
            "engine": self.engine_name.value,
            "status": "HEALTHY",
            "registered_players_count": len(self.resolver.players),
            "review_queue_size": pending,
        }

    def execute(
        self,
        raw_name: str,
        candidates: list[Any] | None = None,
        context_teams: list[str] | None = None,
        context_competition: str | None = None,
        external_id: str | None = None,
    ) -> ResolutionResult:
        """Execute PIRE 4-tier deterministic identity resolution."""
        candidate_rows = list(candidates or [])
        if len(candidate_rows) > 1:
            return ResolutionResult(
                player_id="",
                canonical_name=raw_name,
                status=IdentityStatus.UNRESOLVED,
                tier=ResolutionTier.UNRESOLVED_DISPATCH,
                confidence=0.0,
                needs_review=True,
                review_reason="CDCRE returned multiple identity candidates",
                candidate_matches=[self._candidate_payload(item) for item in candidate_rows],
            )
        res = self.resolver.resolve(
            raw_name=raw_name,
            external_id=external_id,
            context_teams=context_teams,
            context_comp=context_competition,
        )
        if not isinstance(res, ResolutionResult):
            raise TypeError("PIRE returned a result outside the ResolutionResult contract")
        if candidate_rows:
            candidate = candidate_rows[0]
            candidate_id = getattr(candidate, "player_id", None)
            candidate_name = str(getattr(candidate, "canonical_name", "")).strip().casefold()
            if candidate_id is None and res.status != IdentityStatus.UNRESOLVED:
                return ResolutionResult(
                    player_id="",
                    canonical_name=raw_name,
                    status=IdentityStatus.UNRESOLVED,
                    tier=ResolutionTier.UNRESOLVED_DISPATCH,
                    confidence=0.0,
                    needs_review=True,
                    review_reason=(
                        "Candidate has no stable source identifier; name agreement cannot "
                        "establish identity linkage"
                    ),
                    candidate_matches=[self._candidate_payload(candidate)],
                )
            matches_candidate = (
                candidate_id is not None and str(candidate_id) == res.player_id
            ) or (candidate_id is None and candidate_name == res.canonical_name.strip().casefold())
            res.candidate_matches = [self._candidate_payload(candidate)]
            if res.status != IdentityStatus.UNRESOLVED and not matches_candidate:
                return ResolutionResult(
                    player_id="",
                    canonical_name=raw_name,
                    status=IdentityStatus.UNRESOLVED,
                    tier=ResolutionTier.UNRESOLVED_DISPATCH,
                    confidence=0.0,
                    needs_review=True,
                    review_reason="PIRE result conflicts with CDCRE candidate",
                    candidate_matches=[self._candidate_payload(candidate)],
                )
        return res

    @staticmethod
    def _candidate_payload(candidate: Any) -> dict[str, Any]:
        """Keep candidate identity and source provenance attached to PIRE's result."""
        if hasattr(candidate, "model_dump"):
            return {str(key): value for key, value in candidate.model_dump(mode="json").items()}
        return {
            "player_id": str(getattr(candidate, "player_id", "") or ""),
            "canonical_name": str(getattr(candidate, "canonical_name", "")),
            "source_id": getattr(candidate, "source_id", None),
        }

    def get_fallback_result(self, *args: Any, **kwargs: Any) -> ResolutionResult:
        """Fallback result on resolution failure or uninitialized engine."""
        raw_name = args[0] if args else kwargs.get("raw_name", "UNKNOWN_QUERY")
        return ResolutionResult(
            player_id="",
            canonical_name=str(raw_name),
            status=IdentityStatus.UNRESOLVED,
            tier=ResolutionTier.UNRESOLVED_DISPATCH,
            confidence=0.0,
            needs_review=True,
            review_reason="PIRE resolution failed or returned fallback",
        )
