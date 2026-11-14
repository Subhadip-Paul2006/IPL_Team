"""CDCRE Master Facade Engine.

Part of Phase 04A — Career Discovery & Competition Research Engine (Milestone 5).
Implements CDCREngine satisfying ServiceBoundary contracts, uniting pre-identity
candidate discovery (M2), post-identity career retrieval (M3), coverage evaluation
and gap detection (M4), dual-mode repository persistence, and provenance tracking (M5).

Guarantees:
- Strict AC-10 compliance: discover_candidates accepts raw name only, discover_career requires UUID.
- Strict AC-11 compliance: missing datasets emit DATASET_UNAVAILABLE without fabricated appearances.
- Zero auto-merging: name collisions emit AmbiguityStatus.MULTIPLE without merged identities.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from uuid import UUID

from src.cdcre.candidate_discovery import (
    CandidateDiscoveryEngine,
    get_candidate_discovery_engine,
)
from src.cdcre.career_retrieval import (
    CareerRetrievalEngine,
    get_career_retrieval_engine,
)
from src.cdcre.competition_registry import (
    CompetitionRegistry,
    get_competition_registry,
)
from src.cdcre.coverage_evaluator import (
    enrich_career_coverage,
    evaluate_coverage,
)
from src.cdcre.gap_detector import (
    detect_career_gaps,
)
from src.cdcre.provenance import CDCREProvenanceService
from src.cdcre.repository import CDCRERepository, RepositoryMode
from src.contracts.career import PlayerAvailability, PlayerInjury
from src.contracts.cdcre import (
    AmbiguityStatus,
    CandidateDiscoveryResult,
    CareerDataCoverage,
    CareerGapRecord,
    CDCREOutputContract,
    CompetitionHistoryRecord,
    CoverageStatus,
)
from src.services.base import ServiceBoundary

logger = logging.getLogger(__name__)


class CDCREngine(ServiceBoundary):
    """Authoritative master facade for Career Discovery & Competition Research Engine.

    Unifies candidate discovery, career retrieval, coverage evaluation, career gap
    classification, repository persistence, and provenance tracking.
    """

    def __init__(
        self,
        candidate_engine: CandidateDiscoveryEngine | None = None,
        career_engine: CareerRetrievalEngine | None = None,
        registry: CompetitionRegistry | None = None,
        repository: CDCRERepository | None = None,
        provenance_service: CDCREProvenanceService | None = None,
        datasets_dir: Path | str | None = None,
    ) -> None:
        """Initialize the master CDCRE engine and underlying sub-engines."""
        self._registry = registry or get_competition_registry(datasets_dir=datasets_dir)
        self._candidate_discovery = candidate_engine or get_candidate_discovery_engine(datasets_dir=datasets_dir)
        self._career_retrieval = career_engine or get_career_retrieval_engine(
            registry=self._registry,
            datasets_dir=datasets_dir,
        )
        self._repository = repository or CDCRERepository(mode=RepositoryMode.IN_MEMORY)
        self._provenance_service = provenance_service or CDCREProvenanceService()

    # -------------------------------------------------------------------------
    # ServiceBoundary Interface Implementation
    # -------------------------------------------------------------------------

    def get_service_name(self) -> str:
        """Return the canonical service identifier."""
        return "career_discovery_competition_research_engine"

    def health_check(self) -> dict[str, Any]:
        """Perform comprehensive service health inspection across all sub-engines."""
        return {
            "service": self.get_service_name(),
            "status": "healthy",
            "candidate_discovery": {
                "ingested": getattr(self._candidate_discovery, "_ingested", True),
                "candidates_indexed": len(getattr(self._candidate_discovery, "_candidate_records", {})),
            },
            "career_retrieval": {
                "status": "operational",
            },
            "competition_registry": {
                "competitions_count": len(getattr(self._registry, "_registered_competitions", set())),
                "players_indexed": len(getattr(self._registry, "_player_careers", {})),
            },
            "repository": {
                "mode": self._repository.mode.value,
                "records_stored": self._repository.count(),
            },
            "provenance_service": self._provenance_service.health_check(),
        }

    # -------------------------------------------------------------------------
    # Sub-Engine Accessors
    # -------------------------------------------------------------------------

    @property
    def candidate_discovery(self) -> CandidateDiscoveryEngine:
        """Return the pre-identity candidate discovery sub-engine."""
        return self._candidate_discovery

    @property
    def career_retrieval(self) -> CareerRetrievalEngine:
        """Return the post-identity career retrieval sub-engine."""
        return self._career_retrieval

    @property
    def registry(self) -> CompetitionRegistry:
        """Return the competition registry."""
        return self._registry

    @property
    def repository(self) -> CDCRERepository:
        """Return the dual-mode repository."""
        return self._repository

    @property
    def provenance_service(self) -> CDCREProvenanceService:
        """Return the provenance service."""
        return self._provenance_service

    # -------------------------------------------------------------------------
    # Master Facade Methods
    # -------------------------------------------------------------------------

    def discover_candidates(self, raw_name: str, **kwargs: Any) -> CandidateDiscoveryResult:
        """Discover pre-identity candidate players from raw query name (Milestone 2).

        Strictly enforces AC-10: accepts raw name only, never accepts player_id.

        Args:
            raw_name: Raw player name query string.
            **kwargs: Extra keyword arguments forbidden to prevent parameter leakage.

        Returns:
            CandidateDiscoveryResult with ambiguity status and discovered candidate records.

        Raises:
            TypeError: If raw_name is not str, or if forbidden kwargs (e.g. player_id) are passed.
        """
        if kwargs:
            forbidden_keys = list(kwargs.keys())
            raise TypeError(
                f"discover_candidates accepts raw_name only (AC-10); forbidden keyword arguments: {forbidden_keys}"
            )

        if not isinstance(raw_name, str):
            raise TypeError(
                f"discover_candidates expects raw_name as str (AC-10), got {type(raw_name).__name__}"
            )

        return self._candidate_discovery.discover(raw_name)

    def discover_career(
        self,
        canonical_player_id: UUID,
        injuries: list[PlayerInjury] | None = None,
        availability: list[PlayerAvailability] | None = None,
        team_affiliations: list[str] | None = None,
        detect_gaps: bool = True,
    ) -> CareerDataCoverage:
        """Retrieve verified career coverage and classified career gaps (Milestones 3 & 4).

        Strictly enforces AC-10: requires a valid canonical UUID instance.
        Enforces AC-11: missing datasets evaluate to DATASET_UNAVAILABLE.

        Args:
            canonical_player_id: Canonical UUID instance identifying the player.
            injuries: Optional player injury evidence for gap corroboration.
            availability: Optional player NOC / availability evidence for gap corroboration.
            team_affiliations: Optional team affiliations for franchise suspension classification.
            detect_gaps: Whether to perform multi-season career gap detection. Defaults to True.

        Returns:
            Validated CareerDataCoverage contract containing verified competition history
            and classified career gaps.

        Raises:
            TypeError: If canonical_player_id is not a valid UUID instance (AC-10).
        """
        if canonical_player_id is None:
            raise TypeError("canonical_player_id cannot be None; a valid UUID instance is required (AC-10)")

        if not isinstance(canonical_player_id, UUID):
            raise TypeError(
                f"discover_career strictly requires a valid UUID instance (AC-10), "
                f"got {type(canonical_player_id).__name__}: {canonical_player_id!r}"
            )

        # Retrieve base career coverage from M3
        base_coverage = self._career_retrieval.discover_career(canonical_player_id)

        # Enrich coverage and detect gaps from M4
        enriched_coverage = enrich_career_coverage(
            career_coverage=base_coverage,
            detect_gaps=detect_gaps,
            injuries=injuries,
            availability=availability,
            team_affiliations=team_affiliations,
        )

        return enriched_coverage

    def evaluate_coverage(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> CoverageStatus:
        """Evaluate tournament participation into the authoritative four-state model (Milestone 4).

        Taxonomy:
        1. VERIFIED_PARTICIPATION: dataset exists and appearances > 0.
        2. DATASET_UNAVAILABLE: dataset is missing / unavailable (AC-11).
        3. NOT_ESTABLISHED: dataset exists, but appearances is None or ambiguous.
        4. CONFIRMED_NON_PARTICIPATION: dataset exists and complete, appearances == 0.
        """
        return evaluate_coverage(*args, **kwargs)

    def detect_career_gaps(
        self,
        player_id: UUID,
        history: list[CompetitionHistoryRecord],
        injuries: list[PlayerInjury] | None = None,
        availability: list[PlayerAvailability] | None = None,
        team_affiliations: list[str] | None = None,
    ) -> list[CareerGapRecord]:
        """Detect multi-season career gaps and classify them into GapType taxonomies (Milestone 4).

        Classification precedence:
        1. FRANCHISE_SUSPENSION: RR absence in 2016-2017 per Supreme Court Order.
        2. INJURY: Corroborated with player_injuries evidence.
        3. NOC_DENIED: Corroborated with national board NOC denial in player_availability.
        4. UNAVAILABLE: Corroborated with personal reasons / unavailable status.
        5. UNEXPLAINED_GAP: Default uncorroborated gap.
        """
        return detect_career_gaps(
            player_id=player_id,
            history=history,
            injuries=injuries,
            availability=availability,
            team_affiliations=team_affiliations,
        )

    def research_player(
        self,
        raw_name: str | None = None,
        canonical_player_id: UUID | None = None,
        injuries: list[PlayerInjury] | None = None,
        availability: list[PlayerAvailability] | None = None,
        team_affiliations: list[str] | None = None,
    ) -> CDCREOutputContract:
        """Perform end-to-end research on a player by raw name, canonical UUID, or both.

        Integration logic:
        - If canonical_player_id is provided:
            Discovers career coverage directly. If raw_name is also provided, runs
            candidate discovery for metadata corroboration.
        - If only raw_name is provided:
            Discovers candidates. If single corroborated candidate with player_id exists,
            retrieves career coverage. If multiple candidates (collision) or no candidate
            is found, guarantees zero auto-merging and returns candidate discovery with
            career_coverage=None.

        Args:
            raw_name: Optional raw query name string.
            canonical_player_id: Optional canonical player UUID instance.
            injuries: Optional player injury evidence.
            availability: Optional player NOC / availability evidence.
            team_affiliations: Optional player team affiliations.

        Returns:
            CDCREOutputContract containing candidate discovery result, career coverage,
            and research metadata.

        Raises:
            ValueError: If neither raw_name nor canonical_player_id is provided.
            TypeError: If canonical_player_id is provided but is not a UUID instance.
        """
        if raw_name is None and canonical_player_id is None:
            raise ValueError(
                "Either raw_name or canonical_player_id must be provided to research_player"
            )

        candidate_discovery_res: CandidateDiscoveryResult | None = None
        career_coverage_res: CareerDataCoverage | None = None
        metadata: dict[str, Any] = {
            "engine": self.get_service_name(),
        }

        # Step 1: Pre-identity candidate discovery if raw_name provided
        if raw_name is not None:
            candidate_discovery_res = self.discover_candidates(raw_name)
            metadata["raw_name_query"] = raw_name
            metadata["ambiguity_status"] = candidate_discovery_res.ambiguity_status.value
            metadata["collision_detected"] = candidate_discovery_res.collision_detected
            metadata["candidates_count"] = len(candidate_discovery_res.candidates)

        # Step 2: Post-identity career retrieval
        target_uuid: UUID | None = canonical_player_id

        if (
            target_uuid is None
            and candidate_discovery_res is not None
            and candidate_discovery_res.ambiguity_status == AmbiguityStatus.SINGLE_CORROBORATED
            and candidate_discovery_res.candidates
        ):
            target_uuid = candidate_discovery_res.candidates[0].player_id
            if target_uuid is not None:
                metadata["resolved_from_candidate"] = str(target_uuid)

        if target_uuid is not None:
            if not isinstance(target_uuid, UUID):
                raise TypeError(
                    f"canonical_player_id must be a UUID instance, got {type(target_uuid).__name__}"
                )

            career_coverage_res = self.discover_career(
                canonical_player_id=target_uuid,
                injuries=injuries,
                availability=availability,
                team_affiliations=team_affiliations,
            )
            metadata["career_evaluated_count"] = career_coverage_res.competitions_evaluated_count
            metadata["gaps_detected_count"] = len(career_coverage_res.career_gaps)
        else:
            # Collision or uncorroborated: career coverage is not retrieved without identity disambiguation
            if candidate_discovery_res is not None and candidate_discovery_res.collision_detected:
                metadata["anti_merge_triggered"] = True
                metadata["note"] = "Identity collision detected. Post-identity career discovery deferred."

        return CDCREOutputContract(
            candidate_discovery=candidate_discovery_res,
            career_coverage=career_coverage_res,
            metadata=metadata,
        )

    def persist_career_coverage(
        self,
        career_coverage: CareerDataCoverage,
    ) -> list[dict[str, Any]]:
        """Persist all competition history records from a CareerDataCoverage to the repository."""
        player_id = career_coverage.canonical_player_id
        return self._repository.save_batch(
            records=career_coverage.competitions_covered,
            player_id=player_id,
        )


# Global singleton engine instance
_default_cdcre_engine: CDCREngine | None = None


def get_cdcre_engine(
    datasets_dir: Path | str | None = None,
    repository: CDCRERepository | None = None,
    provenance_service: CDCREProvenanceService | None = None,
) -> CDCREngine:
    """Retrieve or initialize the singleton CDCREngine instance."""
    global _default_cdcre_engine
    if datasets_dir is not None or repository is not None or provenance_service is not None:
        return CDCREngine(
            datasets_dir=datasets_dir,
            repository=repository,
            provenance_service=provenance_service,
        )
    if _default_cdcre_engine is None:
        _default_cdcre_engine = CDCREngine()
    return _default_cdcre_engine


__all__ = [
    "CDCREngine",
    "get_cdcre_engine",
]
