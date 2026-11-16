"""Squad Intelligence & Composition Engine (SICE) package.

Exposes master facade SICEEngine, Pydantic v2 data contracts, domain exceptions,
persistence repository SICERepository, and Service E TeamBuilderService while
preserving backwards compatibility with Phase 1B prototype ranking exports.
"""

from src.contracts.sice import (
    AnalyticalRecommendation,
    CandidateRankingStatus,
    CandidateReplacementEvaluation,
    DimensionAdvantage,
    DimensionComparisonResult,
    DimensionStatus,
    LineupEvaluationResult,
    LineupType,
    RankedCandidateContract,
    RankingBoardOutputContract,
    RecommendationLabel,
    RecommendationState,
    ReplacementComparisonOutputContract,
    ReplacementComparisonRequest,
    RosterStatus,
    RunType,
    SICEContractVersion,
    SICEOutputContract,
    SquadBalanceDimensions,
    UncertaintyFlag,
)
from src.sice import models
from src.sice.balance_evaluator import (
    BalanceEvaluator,
    SquadBalanceEvaluator,
)
from src.sice.engine import SICEEngine
from src.sice.exceptions import (
    DatabaseEnvironmentGuardError,
    GateFailureError,
    IncompleteRosterError,
    RankingDeterminismError,
    RoleCompatibilityError,
    SafetyReviewInterceptionError,
    ScorecardGranularityError,
    SICEError,
    SquadConstraintViolationError,
)

# Ranking Engine (RK-1.0.0) & Backwards compatibility with Phase 1B prototype tests
from src.sice.ranking_engine import (
    RankedCandidate,
    RankedCandidateDossier,
    RankingResult,
    SICERankingEngine,
    SiceRankingEngine,
)
from src.sice.replacement_engine import (
    ReplacementCandidateCategory,
    ReplacementEngine,
)
from src.sice.repository import (
    RepositoryMode,
    SICERepository,
)
from src.sice.role_compatibility import (
    CanonicalRole,
    RoleCompatibilityEvaluator,
    RoleCompatibilityMatrix,
    RoleTransitionCategory,
    evaluate_role_compatibility,
)
from src.sice.similarity import (
    AttributeSpec,
    SimilarityCalculator,
    SubspaceDistanceResult,
    cosine_similarity,
    gower_similarity,
    regularized_mahalanobis_distance,
    subspace_weighted_euclidean_distance,
    tactical_phase_similarity,
)
from src.sice.squad_composition import (
    PlayingXIOptimizationResult,
    RosterPlayerContract,
    SquadCompositionEngine,
    SquadCompositionResult,
)
from src.sice.team_builder import TeamBuilderService

# Aliases for calculator sub-interfaces
CosineSimilarityCalculator = SimilarityCalculator
GowerSimilarityCalculator = SimilarityCalculator
SubspaceDistanceCalculator = SimilarityCalculator

__all__ = [
    # Models Module
    "models",
    # Engine Facade
    "SICEEngine",
    # Milestone 5: Replacement Engine & Similarity
    "ReplacementEngine",
    "ReplacementCandidateCategory",
    "RoleCompatibilityEvaluator",
    "RoleCompatibilityMatrix",
    "CanonicalRole",
    "RoleTransitionCategory",
    "evaluate_role_compatibility",
    "SimilarityCalculator",
    "CosineSimilarityCalculator",
    "GowerSimilarityCalculator",
    "SubspaceDistanceCalculator",
    "AttributeSpec",
    "SubspaceDistanceResult",
    "cosine_similarity",
    "gower_similarity",
    "regularized_mahalanobis_distance",
    "subspace_weighted_euclidean_distance",
    "tactical_phase_similarity",
    # Milestone 4: Squad Composition & Balance
    "SquadCompositionEngine",
    "SquadBalanceEvaluator",
    "BalanceEvaluator",
    "SquadCompositionResult",
    "PlayingXIOptimizationResult",
    "RosterPlayerContract",
    # Service E & Persistence
    "TeamBuilderService",
    "SICERepository",
    "RepositoryMode",
    # Domain Exceptions
    "DatabaseEnvironmentGuardError",
    "GateFailureError",
    "IncompleteRosterError",
    "RankingDeterminismError",
    "RoleCompatibilityError",
    "SafetyReviewInterceptionError",
    "ScorecardGranularityError",
    "SICEError",
    "SquadConstraintViolationError",
    # Enums & Models
    "AnalyticalRecommendation",
    "CandidateRankingStatus",
    "CandidateReplacementEvaluation",
    "DimensionAdvantage",
    "DimensionComparisonResult",
    "DimensionStatus",
    "LineupEvaluationResult",
    "LineupType",
    "RankedCandidateContract",
    "RankingBoardOutputContract",
    "RecommendationLabel",
    "RecommendationState",
    "ReplacementComparisonOutputContract",
    "ReplacementComparisonRequest",
    "RosterStatus",
    "RunType",
    "SICEContractVersion",
    "SICEOutputContract",
    "SquadBalanceDimensions",
    "UncertaintyFlag",
    # Ranking Engine (RK-1.0.0) & Legacy Exports
    "SICERankingEngine",
    "SiceRankingEngine",
    "RankedCandidate",
    "RankedCandidateDossier",
    "RankingResult",
]
