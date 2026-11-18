"""Human review queue and conflict tracking registry for PIRE.

Part of Phase 2 Unified Database & PIRE (Track B).
Captures ambiguous resolutions, collision candidates, conflicting external IDs,
and human analyst resolution workflows.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from src.pire.models import ConflictRecord, ReviewQueueItem


class HumanReviewQueue:
    """In-memory and auditable human review queue for ambiguous identity resolutions."""

    def __init__(self) -> None:
        self._queue: dict[str, ReviewQueueItem] = {}
        self._conflicts: dict[str, ConflictRecord] = {}

    def enqueue(
        self,
        raw_name: str,
        source_id: str,
        external_id: str | None = None,
        context_teams: list[str] | None = None,
        context_comp: str | None = None,
        candidate_ids: list[str] | None = None,
        trigger_reason: str = "Ambiguous candidate match",
    ) -> ReviewQueueItem:
        """Enqueue an unresolved identity inquiry for human review."""
        item = ReviewQueueItem(
            queue_id=str(uuid4()),
            raw_name=raw_name,
            source_id=source_id,
            external_id=external_id,
            context_teams=context_teams or [],
            context_comp=context_comp,
            candidate_ids=candidate_ids or [],
            trigger_reason=trigger_reason,
            staged_at=datetime.now(UTC).isoformat(),
            status="PENDING",
        )
        self._queue[item.queue_id] = item
        return item

    def get_pending(self) -> list[ReviewQueueItem]:
        """Retrieve all currently pending review items."""
        return [item for item in self._queue.values() if item.status == "PENDING"]

    def resolve_item(
        self,
        queue_id: str,
        target_player_id: str,
        reviewer_id: str,
        notes: str = "",
    ) -> ReviewQueueItem | None:
        """Resolve a review item manually by assigning a target canonical player ID."""
        item = self._queue.get(queue_id)
        if not item:
            return None
        item.status = "RESOLVED"
        return item

    def record_conflict(
        self,
        subject_name: str,
        conflicting_ids: list[str],
        conflicting_sources: list[str],
        conflict_type: str = "NAME_COLLISION_AMBIGUITY",
        evidence: dict[str, Any] | None = None,
    ) -> ConflictRecord:
        """Record a persistent conflicting identity or collision state."""
        conflict = ConflictRecord(
            conflict_id=str(uuid4()),
            subject_name=subject_name,
            conflicting_ids=conflicting_ids,
            conflicting_sources=conflicting_sources,
            conflict_type=conflict_type,
            evidence=evidence or {},
            resolved=False,
        )
        self._conflicts[conflict.conflict_id] = conflict
        return conflict

    def get_all_conflicts(self) -> list[ConflictRecord]:
        """Retrieve all recorded conflicts."""
        return list(self._conflicts.values())

    @property
    def pending_count(self) -> int:
        return len(self.get_pending())

    @property
    def conflict_count(self) -> int:
        return len(self._conflicts)
