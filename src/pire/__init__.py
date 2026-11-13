"""Player Identity Resolution Engine (PIRE) module initialization."""

from src.pire.alias_registry import AliasRegistry, clean_name
from src.pire.models import (
    ConflictRecord,
    IdentityStatus,
    ResolutionResult,
    ResolutionTier,
    ReviewQueueItem,
    SourceScopedPlayer,
)
from src.pire.player_identity import (
    IdentityResolutionReport,
    PlayerIdentity,
    PlayerIdentityResolver,
)
from src.pire.resolver import UnifiedPIRE
from src.pire.review_queue import HumanReviewQueue

__all__ = [
    "AliasRegistry",
    "ConflictRecord",
    "IdentityResolutionReport",
    "IdentityStatus",
    "PlayerIdentity",
    "PlayerIdentityResolver",
    "ResolutionResult",
    "ResolutionTier",
    "ReviewQueueItem",
    "SourceScopedPlayer",
    "UnifiedPIRE",
    "HumanReviewQueue",
    "clean_name",
]
