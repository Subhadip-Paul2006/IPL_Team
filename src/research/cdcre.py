"""Unified Research Entry Point for CDCRE.

Part of Phase 04A — Career Discovery & Competition Research Engine (Milestone 5).
Composes end-to-end player intelligence:
PIRE (Identity candidate resolution) ->
TMVE (RR Membership & Eligibility) ->
CDCRE (Career discovery, coverage evaluation, gap detection) ->
CDCREOutputContract.

Enforces:
- AC-10: Pre-identity discovery accepts raw name string only; career discovery requires UUID.
- AC-11: Missing datasets produce DATASET_UNAVAILABLE, never zero appearances or fabricated records.
- R6 Anti-Merge: Ambiguous name collisions (including the 7 known collision fixtures) emit
  AmbiguityStatus.MULTIPLE and halt post-identity retrieval to prevent identity corruption.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from src.cdcre.engine import CDCREngine, get_cdcre_engine
from src.contracts.cdcre import (
    AmbiguityStatus,
    CDCREOutputContract,
)
from src.membership.participation import (
    CANONICAL_RR_TEAM_ID,
)
from src.membership.tmve import (
    TeamMembershipVerificationEngine,
)
from src.pire.resolver import UnifiedPIRE

logger = logging.getLogger(__name__)


def research_player_profile(
    raw_name: str,
    preferred_seasons: list[str] | None = None,
    cdcre_engine: CDCREngine | None = None,
    pire_engine: UnifiedPIRE | None = None,
    tmve_engine: TeamMembershipVerificationEngine | None = None,
) -> CDCREOutputContract:
    """Perform comprehensive end-to-end player research across PIRE, TMVE, and CDCRE.

    Pipeline execution sequence:
    1. Pre-Identity Candidate Discovery (CDCRE M2) & PIRE candidate disambiguation.
    2. Anti-merge verification: If collision detected (AmbiguityStatus.MULTIPLE),
       halts post-identity progression and returns safety contract.
    3. RR Membership & Eligibility verification via TMVE (Phase 3).
    4. Post-Identity career discovery, four-state coverage evaluation, and career
       gap detection (CDCRE M3 & M4).
    5. Assembly into authoritative CDCREOutputContract.

    Args:
        raw_name: Raw player name query string.
        preferred_seasons: Optional list of seasons to highlight or prioritize.
        cdcre_engine: Optional injected CDCREngine instance.
        pire_engine: Optional injected UnifiedPIRE instance.
        tmve_engine: Optional injected TeamMembershipVerificationEngine instance.

    Returns:
        Authoritative CDCREOutputContract with candidate discovery, career coverage,
        and integrated research metadata.

    Raises:
        TypeError: If raw_name is not a string (AC-10).
        ValueError: If raw_name is empty or whitespace.
    """
    if not isinstance(raw_name, str):
        raise TypeError(
            f"research_player_profile strictly requires raw_name as str (AC-10), "
            f"got {type(raw_name).__name__}: {raw_name!r}"
        )

    if not raw_name.strip():
        raise ValueError("raw_name cannot be empty or whitespace only")

    # Initialize or reuse engines
    engine = cdcre_engine or get_cdcre_engine()
    _ = pire_engine or UnifiedPIRE()
    tmve = tmve_engine or TeamMembershipVerificationEngine()

    metadata: dict[str, Any] = {
        "pipeline": "PIRE -> TMVE -> CDCRE",
        "raw_name_query": raw_name,
        "preferred_seasons": preferred_seasons or [],
    }

    # Step 1: Pre-identity candidate discovery (AC-10)
    candidate_res = engine.discover_candidates(raw_name)
    metadata["ambiguity_status"] = candidate_res.ambiguity_status.value
    metadata["collision_detected"] = candidate_res.collision_detected
    metadata["candidates_found"] = len(candidate_res.candidates)

    # Step 2: Anti-Merge Guardrail (R6)
    if candidate_res.ambiguity_status == AmbiguityStatus.MULTIPLE or candidate_res.collision_detected:
        metadata["anti_merge_triggered"] = True
        metadata["status"] = "COLLISION_DETECTED"
        metadata["action_required"] = "DISAMBIGUATION_REQUIRED_BEFORE_CAREER_RETRIEVAL"
        return CDCREOutputContract(
            candidate_discovery=candidate_res,
            career_coverage=None,
            metadata=metadata,
        )

    if candidate_res.ambiguity_status == AmbiguityStatus.NONE or not candidate_res.candidates:
        metadata["status"] = "NO_CANDIDATES_FOUND"
        return CDCREOutputContract(
            candidate_discovery=candidate_res,
            career_coverage=None,
            metadata=metadata,
        )

    # Step 3: Single corroborated candidate identity
    candidate = candidate_res.candidates[0]
    canonical_pid: UUID | None = candidate.player_id

    if canonical_pid is None:
        metadata["status"] = "UNRESOLVED_PLAYER_ID"
        return CDCREOutputContract(
            candidate_discovery=candidate_res,
            career_coverage=None,
            metadata=metadata,
        )

    metadata["canonical_player_id"] = str(canonical_pid)
    metadata["canonical_name"] = candidate.canonical_name
    metadata["source_id"] = candidate.source_id
    metadata["confidence"] = candidate.confidence

    # Step 4: TMVE Membership & Relationship Verification
    tmve.register_rr_team_id(CANONICAL_RR_TEAM_ID)
    tmve_output = tmve.verify_player_membership(canonical_pid)

    metadata["tmve"] = {
        "rr_relationship_state": tmve_output.rr_relationship_state.value,
        "rr_current_state": tmve_output.rr_current_state.value,
        "verified_rr_appearances": tmve_output.verified_rr_appearances,
        "review_status": tmve_output.review_status,
    }

    # Step 5: CDCRE Career Discovery, Coverage Evaluation, and Gap Detection
    team_affiliations = list(candidate.teams)
    if "Rajasthan Royals" not in team_affiliations and tmve_output.verified_rr_appearances > 0:
        team_affiliations.append("Rajasthan Royals")

    career_coverage = engine.discover_career(
        canonical_player_id=canonical_pid,
        team_affiliations=team_affiliations,
        detect_gaps=True,
    )

    metadata["career_retrieval"] = {
        "competitions_evaluated_count": career_coverage.competitions_evaluated_count,
        "the_hundred_appearances_deferred": career_coverage.the_hundred_appearances_deferred,
        "gaps_count": len(career_coverage.career_gaps),
    }

    return CDCREOutputContract(
        candidate_discovery=candidate_res,
        career_coverage=career_coverage,
        metadata=metadata,
    )


__all__ = [
    "research_player_profile",
]
