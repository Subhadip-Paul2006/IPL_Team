"""Base engine adapter interface for Mother Intelligence Engine (MIE).

Defines standard lifecycle, exception wrapping, health check, and execution protocol
enforcing strict boundary isolation across all seven specialized engines.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from src.mie.contracts import EngineExecutionRecord, EngineName, ExecutionState


class EngineAdapter(ABC):
    """Abstract base adapter establishing typed contract isolation for an engine."""

    def __init__(self, engine_name: EngineName) -> None:
        self.engine_name = engine_name

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the underlying engine instance is initialized and operational."""
        ...

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """Perform subsystem health inspection and return diagnostic summary."""
        ...

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the engine-specific capability under typed contract."""
        ...

    def execute_monitored(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> tuple[Any, EngineExecutionRecord]:
        """Execute with high-precision time tracking, exception isolation, and diagnostic recording."""
        start_time = time.perf_counter()
        warnings: list[str] = []
        error_msg: str | None = None
        state = ExecutionState.SUCCESS
        result: Any = None
        records_count = 0

        try:
            if not self.is_available():
                state = ExecutionState.SKIPPED
                warnings.append(f"Engine {self.engine_name.value} is unavailable or uninitialized.")
                result = self.get_fallback_result(*args, **kwargs)
            else:
                result = self.execute(*args, **kwargs)
                if hasattr(result, "matches"):
                    records_count = len(getattr(result, "matches", []))
                elif isinstance(result, list):
                    records_count = len(result)
                elif hasattr(result, "candidates"):
                    records_count = len(getattr(result, "candidates", []))
                else:
                    records_count = 1
        except Exception as exc:
            state = ExecutionState.FAILED
            error_msg = f"{type(exc).__name__}: engine adapter execution failed"
            warnings.append(f"Execution error trapped in {self.engine_name.value} adapter.")
            try:
                result = self.get_fallback_result(*args, **kwargs)
            except Exception as fallback_exc:
                error_msg = (
                    f"{type(exc).__name__}: engine adapter execution failed; "
                    f"{type(fallback_exc).__name__}: typed fallback failed"
                )
                result = None

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        diag = EngineExecutionRecord(
            engine=self.engine_name,
            state=state,
            execution_time_ms=round(duration_ms, 3),
            records_processed_count=records_count,
            error_message=error_msg,
            warnings=warnings,
        )

        return result, diag

    def get_fallback_result(self, *args: Any, **kwargs: Any) -> Any:
        """Provide graceful, type-safe fallback when an engine fails or is unavailable.

        Default implementation returns None or an empty container. Subclasses override.
        """
        return None
