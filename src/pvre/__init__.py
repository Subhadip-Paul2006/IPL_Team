"""Player Verification & Research Engine (PVRE) Package.

Engine 07 in the Rajasthan Royals Squad Intelligence Platform (v2.2.0).
Provides dual-mode player verification and research:
- Mother Controller: Deterministic 7-step precedence waterfall.
- Mode A: Incumbent research, RR historical splits, global form, replaceability signals.
- Mode B: Domestic candidate research, scorecard fallback, affirmative eligibility.
- Safety Review Interceptor: Conflict preservation, review dossiers.
- Source Registry: Evidence tiers, competition provenance, dataset availability.
- Dual-Mode Repository: Transactional persistence, parameterized SQL, PG Guard.
"""

from __future__ import annotations

from src.contracts.pvre import (
    CareerCoverageState,
    CareerVerification,
    EvidenceSource,
    EvidenceTier,
    PlayerCappedStatus,
    PlayerResearchOutput,
    PlayerResearchRequest,
    PVREOutputContract,
    PVRERequestContract,
    PVREReviewDossierContract,
    PVREReviewStatus,
    PVREVerificationStatus,
    ReplaceabilitySignal,
    ReplacementCandidateEvidence,
    ReplacementResearchRequest,
    ResearchConflict,
    ResearchCoverage,
    ResearchMode,
    ReviewDossierContract,
    RouteStatus,
    SourceReliability,
    VerificationClaim,
    VerificationStatus,
)
from src.pvre.controller import MotherController
from src.pvre.engine import PVREngine
from src.pvre.mode_a_incumbent import ModeAIncumbentEngine
from src.pvre.mode_b_candidate import ModeBCandidateEngine
from src.pvre.repository import (
    DatabaseEnvironmentGuardError,
    PVRERepository,
    RepositoryMode,
)
from src.pvre.safety_review import (
    SafetyReviewInterceptor,
    SafetyReviewReasonCode,
)
from src.pvre.source_registry import ResearchSourceRegistry

__all__ = [
    # Facade Engine
    "PVREngine",
    # Mother Controller
    "MotherController",
    # Sub-engines & Interceptors
    "ModeAIncumbentEngine",
    "ModeBCandidateEngine",
    "SafetyReviewInterceptor",
    "SafetyReviewReasonCode",
    # Registry & Repository
    "ResearchSourceRegistry",
    "PVRERepository",
    "RepositoryMode",
    "DatabaseEnvironmentGuardError",
    # Core Contracts
    "PVRERequestContract",
    "PVREOutputContract",
    "ReviewDossierContract",
    "PVREReviewDossierContract",
    "ReplacementCandidateEvidence",
    "PlayerResearchRequest",
    "PlayerResearchOutput",
    "ReplacementResearchRequest",
    "VerificationClaim",
    "EvidenceSource",
    "ResearchConflict",
    "CareerVerification",
    "ResearchCoverage",
    # Domain Taxonomy & Enums
    "ResearchMode",
    "RouteStatus",
    "ReplaceabilitySignal",
    "CareerCoverageState",
    "PlayerCappedStatus",
    "PVREVerificationStatus",
    "VerificationStatus",
    "PVREReviewStatus",
    "SourceReliability",
    "EvidenceTier",
]
