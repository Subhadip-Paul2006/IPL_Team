"""Career Discovery & Competition Research Engine (CDCRE).

Provides pre-identity candidate discovery (Milestone 2), post-identity
career retrieval (Milestone 3), coverage evaluation & career gap detection
(Milestone 4), dual-mode repository persistence, and provenance tracking (Milestone 5)
for the Rajasthan Royals squad intelligence platform.
"""

from src.cdcre.candidate_discovery import (
    CandidateDiscoveryEngine,
    PreIdentityCandidateDiscovery,
    derive_player_uuid,
    discover_candidates,
    get_candidate_discovery_engine,
)
from src.cdcre.career_retrieval import (
    CareerRetrievalEngine,
    discover_career,
    get_career_retrieval_engine,
)
from src.cdcre.competition_registry import (
    BBL_COMPETITION_UUID,
    BPL_COMPETITION_UUID,
    HUNDRED_COMPETITION_UUID,
    IPL_COMPETITION_UUID,
    SMAT_COMPETITION_UUID,
    CompetitionRegistry,
    derive_competition_uuid,
    derive_provenance_uuid,
    get_competition_registry,
    normalize_competition_name,
    normalize_format_tag,
    normalize_season_year,
)
from src.cdcre.coverage_evaluator import (
    CoverageEvaluator,
    enrich_career_coverage,
    evaluate_competition_coverage,
    evaluate_coverage,
)
from src.cdcre.engine import (
    CDCREngine,
    get_cdcre_engine,
)
from src.cdcre.gap_detector import (
    CareerGapDetector,
    detect_career_gaps,
    format_gap_season,
    parse_season_start_year,
)
from src.cdcre.provenance import (
    CDCREProvenanceService,
)
from src.cdcre.repository import (
    CDCRERepository,
)

__all__ = [
    # M2: Candidate Discovery
    "discover_candidates",
    "CandidateDiscoveryEngine",
    "PreIdentityCandidateDiscovery",
    "derive_player_uuid",
    "get_candidate_discovery_engine",
    # M3: Career Retrieval & Competition Registry
    "discover_career",
    "CareerRetrievalEngine",
    "get_career_retrieval_engine",
    "CompetitionRegistry",
    "get_competition_registry",
    "derive_competition_uuid",
    "derive_provenance_uuid",
    "normalize_competition_name",
    "normalize_season_year",
    "normalize_format_tag",
    "IPL_COMPETITION_UUID",
    "SMAT_COMPETITION_UUID",
    "HUNDRED_COMPETITION_UUID",
    "BBL_COMPETITION_UUID",
    "BPL_COMPETITION_UUID",
    # M4: Coverage Evaluation & Career Gap Detection
    "CoverageEvaluator",
    "evaluate_coverage",
    "evaluate_competition_coverage",
    "enrich_career_coverage",
    "CareerGapDetector",
    "detect_career_gaps",
    "format_gap_season",
    "parse_season_start_year",
    # M5: Integration, Repository & Provenance
    "CDCREngine",
    "get_cdcre_engine",
    "CDCRERepository",
    "CDCREProvenanceService",
]
