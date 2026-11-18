"""CPPAE (Complete Player Performance Analytics Engine) Adapter for MIE (Engine 04).

Wraps CPPAEEngine, computing DATA_DICTIONARY-governed batting, bowling, fielding,
and match contribution metrics with visible sample sizes and null safety (Rule R1).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.contracts.cppae import CPPAEOutput, SampleSizes
from src.cppae.engine import CPPAEEngine
from src.mie.adapters.base import EngineAdapter
from src.mie.contracts import EngineName


class CPPAEAdapter(EngineAdapter):
    """Adapter managing CPPAE Engine 04 operations."""

    def __init__(self, cppae_engine: CPPAEEngine | None = None) -> None:
        super().__init__(EngineName.CPPAE)
        self.cppae = cppae_engine or CPPAEEngine()

    def is_available(self) -> bool:
        """Check availability of CPPAE engine."""
        return self.cppae is not None

    def health_check(self) -> dict[str, Any]:
        """Return diagnostic health check for CPPAE."""
        return {
            "engine": self.engine_name.value,
            "status": "HEALTHY",
            "model_version": getattr(self.cppae, "model_version", "v2.1"),
        }

    def execute(
        self,
        player_id: UUID,
        deliveries: list[dict[str, Any]] | None = None,
        states: list[Any] | None = None,
        batting_innings: list[Any] | None = None,
        bowling_spells: list[Any] | None = None,
        fielding_events: list[Any] | None = None,
        wk_events: list[Any] | None = None,
        matches: list[dict[str, Any]] | None = None,
        player_awards: list[Any] | None = None,
        player_names: dict[str, str] | None = None,
        format_tag: str = "T20",
        window: str = "career",
        **kwargs: Any,
    ) -> CPPAEOutput:
        """Execute CPPAE performance calculation."""
        delivs = deliveries or []
        output = self.cppae.analyse(
            player_id=player_id,
            deliveries=delivs,
            states=states,
            batting_innings=batting_innings,
            bowling_spells=bowling_spells,
            fielding_events=fielding_events,
            wk_events=wk_events,
            matches=matches,
            player_awards=player_awards,
            player_names=player_names,
            format_tag=format_tag,
            window=window,
            **kwargs,
        )
        return output

    def get_fallback_result(self, *args: Any, **kwargs: Any) -> CPPAEOutput:
        """Fallback returning valid CPPAEOutput with 0 samples and NULL rates (Rule R1)."""
        pid = (
            args[0]
            if args
            else kwargs.get("player_id", UUID("00000000-0000-0000-0000-000000000000"))
        )
        p_names = kwargs.get("player_names", {})
        cname = p_names.get(str(pid), f"Player_{str(pid)[:8]}")
        return CPPAEOutput(
            player_id=pid,
            canonical_name=cname,
            format_tag="T20",
            window="career",
            samples=SampleSizes(matches=0, innings=0, balls_faced=0, legal_balls_bowled=0),
            per_stat={},
        )
