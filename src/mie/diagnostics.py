"""MIE Structured Diagnostics & Observability Service.

Provides structured JSON logging, trace collection, latency tracking,
and execution anomaly reporting for the Mother Intelligence Engine.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from src.mie.contracts import EngineExecutionRecord, ExecutionState

logger = logging.getLogger("mie.diagnostics")


class MIEDiagnostics:
    """Manages telemetry, engine execution profiling, and diagnostic reporting."""

    def __init__(self) -> None:
        self._execution_history: list[dict[str, Any]] = []

    def record_run(
        self,
        request_id: UUID,
        player_query: str,
        total_time_ms: float,
        engine_executions: dict[str, EngineExecutionRecord],
        overall_status: str,
    ) -> dict[str, Any]:
        """Record and log an end-to-end orchestration execution event."""
        diag_entry = {
            "request_id": str(request_id),
            "query_length": len(player_query),
            "total_time_ms": round(total_time_ms, 3),
            "overall_status": overall_status,
            "timestamp": datetime.now(UTC).isoformat(),
            "engine_breakdown": {
                name: {
                    "state": rec.state.value,
                    "time_ms": rec.execution_time_ms,
                    "records_count": rec.records_processed_count,
                    "error": rec.error_message,
                }
                for name, rec in engine_executions.items()
            },
        }

        self._execution_history.append(diag_entry)
        logger.info(
            "MIE orchestration completed",
            extra={"mie_event": diag_entry},
        )

        return diag_entry

    def get_summary_statistics(self) -> dict[str, Any]:
        """Compute aggregate performance and error metrics across recorded executions."""
        if not self._execution_history:
            return {"total_runs": 0, "average_time_ms": 0.0, "error_rate": 0.0}

        total_runs = len(self._execution_history)
        avg_time = sum(e["total_time_ms"] for e in self._execution_history) / total_runs
        failed_runs = sum(
            1
            for e in self._execution_history
            if any(
                eng["state"] == ExecutionState.FAILED.value
                for eng in e["engine_breakdown"].values()
            )
        )

        return {
            "total_runs": total_runs,
            "average_time_ms": round(avg_time, 2),
            "error_rate": round(failed_runs / total_runs, 3),
            "failed_runs_count": failed_runs,
        }
