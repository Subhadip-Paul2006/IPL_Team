"""SICE (Squad Intelligence & Composition Engine) Adapter for MIE (Engine 06).

Wraps SICEEngine, SICERankingEngine (RK-1.0.0), and TeamBuilderService (Service E),
providing squad balance analysis, 16-dimension replacement comparison, and ranking.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.contracts.sice import (
    RankingBoardOutputContract,
    ReplacementComparisonOutputContract,
    ReplacementComparisonRequest,
    SICEOutputContract,
)
from src.mie.adapters.base import EngineAdapter
from src.mie.contracts import EngineName
from src.sice.engine import SICEEngine
from src.sice.ranking_engine import SICERankingEngine
from src.sice.team_builder import TeamBuilderService


class SICEAdapter(EngineAdapter):
    """Adapter managing SICE Engine 06 operations."""

    def __init__(
        self,
        sice_engine: SICEEngine | None = None,
        ranking_engine: SICERankingEngine | None = None,
        team_builder: TeamBuilderService | None = None,
    ) -> None:
        super().__init__(EngineName.SICE)
        self.ranking_engine = ranking_engine or SICERankingEngine()
        self.team_builder = team_builder or TeamBuilderService()
        self.sice = sice_engine or SICEEngine(
            ranking_engine=self.ranking_engine,
            team_builder=self.team_builder,
        )

    def is_available(self) -> bool:
        """Check availability of SICE engine."""
        return self.sice is not None

    def health_check(self) -> dict[str, Any]:
        """Return diagnostic health check for SICE."""
        return {
            "engine": self.engine_name.value,
            "status": "HEALTHY",
            "sice_health": self.sice.health_check()
            if hasattr(self.sice, "health_check")
            else "ready",
        }

    def evaluate_squad(
        self,
        user_team_id: UUID,
        **kwargs: Any,
    ) -> SICEOutputContract | None:
        """Evaluate complete user squad composition across 16 balance dimensions."""
        if hasattr(self.sice, "evaluate_squad"):
            result = self.sice.evaluate_squad(team_id=user_team_id, **kwargs)
            if isinstance(result, SICEOutputContract):
                return result
        return None

    def compare_replacement(
        self,
        request: ReplacementComparisonRequest,
        **kwargs: Any,
    ) -> ReplacementComparisonOutputContract | None:
        """Execute 16-dimension role-aware incumbent replacement evaluation (AC-30)."""
        if hasattr(self.sice, "compare_replacement"):
            result = self.sice.compare_replacement(request=request, **kwargs)
            if isinstance(result, ReplacementComparisonOutputContract):
                return result
        return None

    def run_ranking(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> RankingBoardOutputContract:
        """Execute versioned Top-10 uncapped candidate ranking board (RK-1.0.0)."""
        return self.ranking_engine.run_ranking(*args, **kwargs)

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """General execution entry point based on kwargs."""
        if "user_team_id" in kwargs:
            return self.evaluate_squad(kwargs["user_team_id"])
        if "replacement_request" in kwargs:
            return self.compare_replacement(kwargs["replacement_request"])
        if "ranking_config" in kwargs:
            return self.run_ranking(*args, **kwargs)
        return None

    def get_fallback_result(self, *args: Any, **kwargs: Any) -> Any:
        """Fallback returning None when squad analysis cannot be performed."""
        return None
