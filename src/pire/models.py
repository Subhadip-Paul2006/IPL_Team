"""Data models and enumerated types for the unified PIRE engine.

Part of Phase 2 Unified Database & PIRE (Track B).
Implements source-scoped player models, resolution tiers, conflict tracking,
and review queue items preserving provenance and anti-merge invariants.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4


class IdentityStatus(StrEnum):
    """Authoritative identity resolution lifecycle states."""

    RESOLVED = "RESOLVED"
    PROVISIONAL = "PROVISIONAL"
    UNRESOLVED = "UNRESOLVED"


class ResolutionTier(StrEnum):
    """Cascading deterministic resolution tiers."""

    TIER_1_CANONICAL_EXTERNAL_KEY = "TIER_1_CANONICAL_EXTERNAL_KEY"  # 1.00
    TIER_2_VERIFIED_ALIAS_EXACT = "TIER_2_VERIFIED_ALIAS_EXACT"      # 0.95
    TIER_3_CONTEXTUAL_INTERSECTION = "TIER_3_CONTEXTUAL_INTERSECTION" # 0.80 - 0.90
    TIER_4_FUZZY_CORROBORATED = "TIER_4_FUZZY_CORROBORATED"          # < 0.80
    UNRESOLVED_DISPATCH = "UNRESOLVED_DISPATCH"                      # 0.00


@dataclass
class SourceScopedPlayer:
    """Source-scoped player record maintaining provider provenance."""

    canonical_player_id: str
    canonical_name: str
    source_id: str = "organizer_pack"
    source_player_id: str = ""
    external_hashes: dict[str, str] = field(default_factory=dict)  # provider -> hash/id
    aliases: set[str] = field(default_factory=set)
    teams: set[str] = field(default_factory=set)
    competitions: set[str] = field(default_factory=set)
    playing_role: str | None = None
    batting_hand: str | None = None
    bowling_style: str | None = None
    birth_year: int | None = None
    match_appearances: int = 0
    identity_status: IdentityStatus = IdentityStatus.RESOLVED
    is_name_collision: bool = False
    collision_sibling_ids: list[str] = field(default_factory=list)


@dataclass
class ResolutionResult:
    """Result of an identity resolution inquiry."""

    player_id: str
    canonical_name: str
    status: IdentityStatus
    tier: ResolutionTier
    confidence: float
    calibrated: bool = False
    matched_alias: str | None = None
    matched_source: str | None = None
    needs_review: bool = False
    review_reason: str | None = None
    candidate_matches: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ConflictRecord:
    """Preserved conflicting evidence and collision record."""

    conflict_id: str = field(default_factory=lambda: str(uuid4()))
    subject_name: str = ""
    conflicting_ids: list[str] = field(default_factory=list)
    conflicting_sources: list[str] = field(default_factory=list)
    conflict_type: str = "NAME_COLLISION_AMBIGUITY"
    evidence: dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_notes: str | None = None


@dataclass
class ReviewQueueItem:
    """Item staged for human analyst review."""

    queue_id: str = field(default_factory=lambda: str(uuid4()))
    raw_name: str = ""
    source_id: str = ""
    external_id: str | None = None
    context_teams: list[str] = field(default_factory=list)
    context_comp: str | None = None
    candidate_ids: list[str] = field(default_factory=list)
    trigger_reason: str = ""
    staged_at: str = ""
    status: str = "PENDING"  # PENDING, RESOLVED, REJECTED
