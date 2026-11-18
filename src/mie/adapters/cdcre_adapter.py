"""CDCRE (Career Discovery & Competition Research Engine) Adapter for MIE (Engine 03).

Provides dual capabilities:
1. Pre-identity candidate discovery from raw name (`discover_candidates`, AC-10).
2. Post-identity career retrieval and 4-state coverage evaluation (`discover_career`, AC-11).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.cdcre.engine import CDCREngine
from src.contracts.cdcre import (
    CandidateDiscoveryResult,
    CareerDataCoverage,
    CoverageStatus,
)
from src.mie.adapters.base import EngineAdapter
from src.mie.contracts import EngineName


class CDCREAdapter(EngineAdapter):
    """Adapter managing CDCRE Engine 03 operations."""

    def __init__(self, cdcre_engine: CDCREngine | None = None) -> None:
        super().__init__(EngineName.CDCRE)
        self.cdcre = cdcre_engine or CDCREngine()

    def is_available(self) -> bool:
        """Check availability of CDCRE engine."""
        return self.cdcre is not None

    def health_check(self) -> dict[str, Any]:
        """Return diagnostic health check for CDCRE."""
        return {
            "engine": self.engine_name.value,
            "status": "HEALTHY",
            "cdcre_health": self.cdcre.health_check(),
        }

    def discover_candidates(self, raw_name: str) -> CandidateDiscoveryResult:
        """Execute pre-identity candidate discovery from raw query name (Capability 1, AC-10)."""
        return self.cdcre.discover_candidates(raw_name=raw_name)

    def execute(
        self,
        player_id: UUID,
        **kwargs: Any,
    ) -> CareerDataCoverage:
        """Execute post-identity career retrieval and coverage evaluation (Capability 2, AC-10/11)."""
        return self.cdcre.discover_career(canonical_player_id=player_id, **kwargs)

    def get_fallback_result(self, *args: Any, **kwargs: Any) -> CareerDataCoverage:
        """Fallback returning conservative NOT_ESTABLISHED career coverage."""
        pid = (
            args[0]
            if args
            else kwargs.get("player_id", UUID("00000000-0000-0000-0000-000000000000"))
        )
        return CareerDataCoverage(
            canonical_player_id=pid,
            competitions_evaluated_count=0,
            competitions_covered=[],
            coverage_summary={CoverageStatus.NOT_ESTABLISHED: 0},
            career_gaps=[],
        )
