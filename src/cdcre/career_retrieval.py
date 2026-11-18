"""Post-Identity Career Retrieval for CDCRE.

Part of Phase 04A — Career Discovery & Competition Research Engine (Milestone 3).
Implements discover_career(canonical_player_id) requiring a valid canonical UUID
instance (AC-10), aggregating verified appearances across 13 tournament datasets
and 141 organizer competitions, and enforcing The Hundred 5-ball format semantics
(balls_per_over = 5, the_hundred_appearances_deferred = True).
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from src.cdcre.competition_registry import (
    CompetitionRegistry,
    get_competition_registry,
)
from src.contracts.cdcre import (
    CareerDataCoverage,
    CoverageStatus,
)


class CareerRetrievalEngine:
    """Engine aggregating verified post-identity career participation.

    Adheres strictly to AC-10 (requires canonical UUID instance, never accepts raw names),
    aggregates verified appearances across CricSheet and organizer competitions,
    and isolates The Hundred 5-ball semantics with deferred rate metrics.
    """

    def __init__(
        self,
        registry: CompetitionRegistry | None = None,
        datasets_dir: Path | str | None = None,
    ) -> None:
        if registry is not None:
            self.registry = registry
        else:
            self.registry = get_competition_registry(datasets_dir=datasets_dir)

    def discover_career(self, canonical_player_id: UUID) -> CareerDataCoverage:
        """Retrieve complete verified career data coverage for a canonical player UUID.

        Args:
            canonical_player_id: Canonical UUID instance identifying the player.

        Returns:
            CareerDataCoverage domain contract containing verified competition history.

        Raises:
            TypeError: If canonical_player_id is not a valid UUID instance (AC-10).
            ValueError: If canonical_player_id is invalid.
        """
        if canonical_player_id is None:
            raise TypeError("canonical_player_id cannot be None; a valid UUID instance is required (AC-10)")
        if not isinstance(canonical_player_id, UUID):
            raise TypeError(
                f"discover_career strictly requires a valid UUID instance (AC-10), "
                f"got {type(canonical_player_id).__name__}: {canonical_player_id!r}"
            )

        # Retrieve verified competition records from registry
        history_records = self.registry.get_career_history(canonical_player_id)

        # Ensure deterministic ordering: competition_name ASC, season_year ASC
        sorted_records = sorted(
            history_records,
            key=lambda r: (r.competition_name, r.season_year),
        )

        # Check for appearances in The Hundred (5-ball format semantics)
        the_hundred_deferred = any(
            (r.balls_per_over == 5 or "hundred" in r.competition_name.lower())
            and (r.appearances is not None and r.appearances > 0)
            for r in sorted_records
        )

        # Compute coverage summary dictionary
        coverage_summary: dict[CoverageStatus, int] = {}
        for r in sorted_records:
            coverage_summary[r.coverage_status] = coverage_summary.get(r.coverage_status, 0) + 1

        if not coverage_summary:
            coverage_summary = {CoverageStatus.VERIFIED_PARTICIPATION: 0}

        return CareerDataCoverage(
            canonical_player_id=canonical_player_id,
            competitions_evaluated_count=len(sorted_records),
            competitions_covered=sorted_records,
            coverage_summary=coverage_summary,
            career_gaps=[],  # Empty in M3; populated by M4 gap detector
            the_hundred_appearances_deferred=the_hundred_deferred,
        )


# Global singleton engine instance
_default_career_engine: CareerRetrievalEngine | None = None


def get_career_retrieval_engine(
    datasets_dir: Path | str | None = None,
    registry: CompetitionRegistry | None = None,
) -> CareerRetrievalEngine:
    """Retrieve or initialize the default career retrieval engine singleton."""
    global _default_career_engine
    if datasets_dir is not None or registry is not None:
        return CareerRetrievalEngine(registry=registry, datasets_dir=datasets_dir)
    if _default_career_engine is None:
        _default_career_engine = CareerRetrievalEngine()
    return _default_career_engine


def discover_career(canonical_player_id: UUID) -> CareerDataCoverage:
    """Post-identity career retrieval entry point (Requirement R3, AC-10).

    Strictly requires a valid canonical UUID player_id. Aggregates verified appearances
    across 13 CricSheet tournament datasets and 141 organizer competitions while preserving
    format and season metadata. Handles The Hundred verified appearances with 5-ball format
    semantics (balls_per_over = 5, the_hundred_appearances_deferred = True).

    Args:
        canonical_player_id: Canonical UUID instance identifying the player.

    Returns:
        Validated CareerDataCoverage domain contract.

    Raises:
        TypeError: If canonical_player_id is not a valid UUID instance.
        ValueError: If canonical_player_id is invalid.
    """
    if canonical_player_id is None:
        raise TypeError("canonical_player_id cannot be None; a valid UUID instance is required (AC-10)")
    if not isinstance(canonical_player_id, UUID):
        raise TypeError(
            f"discover_career strictly requires a valid UUID instance (AC-10), "
            f"got {type(canonical_player_id).__name__}: {canonical_player_id!r}"
        )

    engine = get_career_retrieval_engine()
    return engine.discover_career(canonical_player_id)


__all__ = [
    "CareerRetrievalEngine",
    "discover_career",
    "get_career_retrieval_engine",
]
