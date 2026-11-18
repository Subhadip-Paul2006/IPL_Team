"""Squad Intelligence & Composition Engine (SICE) Models Module.

Unified re-export module for all authoritative SICE Pydantic v2 data contracts,
domain enumerations, role compatibility structures, similarity specifications,
and replacement intelligence models in accordance with docs/TRD.md §8,
docs/RANKING_SPEC.md, and docs/DATA_DICTIONARY.md.
"""

from __future__ import annotations

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
from src.sice.replacement_engine import (
    ReplacementCandidateCategory,
)
from src.sice.role_compatibility import (
    CanonicalRole,
    RoleCompatibilityResult,
    RoleTransitionCategory,
)
from src.sice.similarity import (
    AttributeSpec,
    SubspaceDistanceResult,
)
from src.sice.squad_composition import (
    PlayingXIOptimizationResult,
    RosterPlayerContract,
    SquadCompositionResult,
)

__all__ = [
    # SICE Core Contracts & Enums
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
    # Role Compatibility Models
    "CanonicalRole",
    "RoleCompatibilityResult",
    "RoleTransitionCategory",
    # Similarity Models
    "AttributeSpec",
    "SubspaceDistanceResult",
    # Replacement Models
    "ReplacementCandidateCategory",
    # Squad Composition Models
    "PlayingXIOptimizationResult",
    "RosterPlayerContract",
    "SquadCompositionResult",
]
