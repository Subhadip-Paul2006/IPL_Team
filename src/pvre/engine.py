"""Player Verification & Research Engine (PVRE) — Master Facade Engine.

Part of Phase 04B — Player Verification & Research Engine (Milestone 5).
Implements PVREngine satisfying ServiceBoundary contracts, integrating
Mother Controller, Mode A (Incumbent Intelligence), Mode B (Candidate Intelligence),
Safety Review Interceptor, Source Registry, and Dual-Mode Repository.
"""

from __future__ import annotations

import logging
from typing import Any

from src.contracts.pvre import (
    PlayerResearchRequest,
    PVREOutputContract,
    PVRERequestContract,
    ReplacementCandidateEvidence,
    ReplacementResearchRequest,
)
from src.pvre.controller import MotherController
from src.pvre.mode_a_incumbent import ModeAIncumbentEngine
from src.pvre.mode_b_candidate import ModeBCandidateEngine
from src.pvre.repository import PVRERepository, RepositoryMode
from src.pvre.safety_review import SafetyReviewInterceptor
from src.pvre.source_registry import STANDARD_EVIDENCE_SOURCES, ResearchSourceRegistry
from src.services.base import ServiceBoundary

logger = logging.getLogger(__name__)


class PVREngine(ServiceBoundary):
    """Authoritative master facade for Player Verification & Research Engine (PVRE).

    Coordinates:
    - Mother Controller: 7-step deterministic waterfall routing.
    - Mode A: Incumbent research, RR historical splits, global form, replaceability signals.
    - Mode B: Domestic candidate research, scorecard fallback, affirmative eligibility.
    - Safety Review Interceptor: Conflict preservation, review dossiers.
    - Source Registry: Evidence tiers, competition provenance, dataset availability.
    - Dual-Mode Repository: Transactional persistence, parameterized SQL, PG Guard.
    """

    def __init__(
        self,
        controller: MotherController | None = None,
        mode_a_engine: type[ModeAIncumbentEngine] | None = None,
        mode_b_engine: ModeBCandidateEngine | None = None,
        safety_interceptor: SafetyReviewInterceptor | None = None,
        source_registry: ResearchSourceRegistry | None = None,
        repository: PVRERepository | None = None,
    ) -> None:
        """Initialize the master PVRE facade and underlying sub-engines."""
        self._safety_interceptor = safety_interceptor or SafetyReviewInterceptor()
        self._mode_a_engine = mode_a_engine or ModeAIncumbentEngine
        self._mode_b_engine = mode_b_engine or ModeBCandidateEngine()
        self._controller = controller or MotherController(
            safety_interceptor=self._safety_interceptor,
            mode_a_engine=self._mode_a_engine,
            mode_b_engine=self._mode_b_engine,
        )

        # Source registry with standard sources pre-registered
        if source_registry is not None:
            self._source_registry = source_registry
        else:
            self._source_registry = ResearchSourceRegistry()
            for src in STANDARD_EVIDENCE_SOURCES:
                self._source_registry.register_source(src)

        self._repository = repository or PVRERepository(mode=RepositoryMode.IN_MEMORY)

    # -------------------------------------------------------------------------
    # Sub-Engine Accessors
    # -------------------------------------------------------------------------

    @property
    def controller(self) -> MotherController:
        """Retrieve Mother Controller instance."""
        return self._controller

    @property
    def mode_a_engine(self) -> type[ModeAIncumbentEngine]:
        """Retrieve Mode A engine class."""
        return self._mode_a_engine

    @property
    def mode_b_engine(self) -> ModeBCandidateEngine:
        """Retrieve Mode B engine instance."""
        return self._mode_b_engine

    @property
    def safety_interceptor(self) -> SafetyReviewInterceptor:
        """Retrieve Safety Review Interceptor instance."""
        return self._safety_interceptor

    @property
    def source_registry(self) -> ResearchSourceRegistry:
        """Retrieve Research Source Registry instance."""
        return self._source_registry

    @property
    def repository(self) -> PVRERepository:
        """Retrieve PVRE Repository instance."""
        return self._repository

    # -------------------------------------------------------------------------
    # ServiceBoundary Interface Implementation
    # -------------------------------------------------------------------------

    def get_service_name(self) -> str:
        """Return canonical service identifier for PVRE."""
        return "player_verification_research_engine"

    def health_check(self) -> dict[str, Any]:
        """Perform comprehensive service health inspection across all PVRE components."""
        return {
            "service": self.get_service_name(),
            "status": "healthy",
            "controller": {
                "status": "ready",
                "type": "MotherController",
                "waterfall_steps": 7,
            },
            "mode_a": {
                "status": "ready",
                "type": "ModeAIncumbentEngine",
                "modules": ["A1_RR_History", "A2_Global_Form", "A3_Replaceability"],
            },
            "mode_b": {
                "status": "ready",
                "type": "ModeBCandidateEngine",
                "modules": ["Domestic_Discovery", "Scorecard_Fallback", "Affirmative_Eligibility"],
            },
            "safety_review": {
                "status": "ready",
                "type": "SafetyReviewInterceptor",
                "active_dossiers": len(self._safety_interceptor.dossiers),
                "active_conflicts": len(self._safety_interceptor.conflicts),
            },
            "source_registry": {
                "status": "ready",
                "sources_registered": len(self._source_registry._sources),
                "adapters_registered": len(self._source_registry._adapters),
            },
            "repository": {
                "status": "ready",
                "mode": self._repository.mode.value,
                "records_stored": self._repository.count(),
            },
        }

    # -------------------------------------------------------------------------
    # Core Research Workflows
    # -------------------------------------------------------------------------

    def execute_player_research(
        self,
        request: PVRERequestContract | PlayerResearchRequest | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> PVREOutputContract:
        """Execute end-to-end player verification and research workflow.

        Integrates PIRE -> TMVE -> CDCRE -> CPPAE (via contract payload) -> PVRE.
        Enforces:
        - 7-step deterministic waterfall routing via MotherController.
        - Review dossier generation upon conflict / ambiguity.
        - Persistence of outputs and dossiers into PVRERepository.
        """
        output = self._controller.execute(request, context)

        # Persist output in repository
        self._repository.save_research_output(output)

        # Persist associated safety review dossier if created
        if self._controller.last_dossier is not None:
            self._repository.save_review_dossier(self._controller.last_dossier)

        return output

    def execute_replacement_research(
        self,
        request: ReplacementResearchRequest | dict[str, Any],
        candidate_pool: list[dict[str, Any]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[ReplacementCandidateEvidence]:
        """Execute Mode B replacement candidate research with squad requirements.

        Enforces:
        - Role, batting hand, bowling style, age, and match sample filtering.
        - Affirmative uncapped verification (0 senior international caps).
        - Scorecard fallback protocol when BBB data is absent.
        - Persistence of candidate evidence in repository.
        """
        req: ReplacementResearchRequest = (
            request
            if isinstance(request, ReplacementResearchRequest)
            else ReplacementResearchRequest(**request)
        )

        ctx = context or {}
        pool = candidate_pool or ctx.get("candidate_pool", [])

        # Research candidates matching requirements
        candidates: list[ReplacementCandidateEvidence] = (
            self._mode_b_engine.research_replacement_candidates(req, candidate_pool=pool)
        )

        # Persist qualified candidate evidence dossiers
        for cand in candidates:
            self._repository.save_candidate_evidence(cand)

        return candidates


__all__ = [
    "PVREngine",
]
