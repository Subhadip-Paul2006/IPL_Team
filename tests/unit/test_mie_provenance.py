"""Provenance graph assembly coverage across MIE engine outputs."""

from __future__ import annotations

from uuid import uuid4

from src.contracts.cdcre import (
    AmbiguityStatus,
    CandidateDiscoveryResult,
    CareerDataCoverage,
    CompetitionHistoryRecord,
    CoverageStatus,
)
from src.contracts.tmve import EligibilityOutputContract, EligibilityStatus
from src.mie.provenance import ProvenanceGraphBuilder
from src.pire.models import IdentityStatus, ResolutionResult, ResolutionTier


def test_provenance_graph_assembles_identity_career_and_eligibility_sources() -> None:
    """Service C graph includes source IDs and verification IDs from upstream contracts."""
    player_id = uuid4()
    source_record_id = uuid4()
    verification_id = uuid4()
    discovery = CandidateDiscoveryResult(
        raw_name_query="Fixture Player",
        ambiguity_status=AmbiguityStatus.SINGLE_CORROBORATED,
        candidates=[
            {
                "player_id": player_id,
                "canonical_name": "Fixture Player",
                "source_id": "cricsheet-register",
            }
        ],
    )
    career = CareerDataCoverage(
        canonical_player_id=player_id,
        competitions_covered=[
            CompetitionHistoryRecord(
                competition_id=uuid4(),
                competition_name="Domestic T20",
                season_year="2024",
                format_tag="T20",
                coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
                provenance_record_id=source_record_id,
            )
        ],
    )
    eligibility = EligibilityOutputContract(
        player_id=player_id,
        target_season_id=uuid4(),
        eligibility_status=EligibilityStatus.VERIFIED_ELIGIBLE,
        verified=True,
        verification_id=verification_id,
        rule_source="Official IPL policy",
    )
    identity = ResolutionResult(
        player_id=str(player_id),
        canonical_name="Fixture Player",
        status=IdentityStatus.RESOLVED,
        tier=ResolutionTier.TIER_2_VERIFIED_ALIAS_EXACT,
        confidence=0.95,
        matched_source="internal-player-registry",
    )

    graph = ProvenanceGraphBuilder.build_provenance_graph(
        identity_output=identity,
        candidate_discovery=discovery,
        career_coverage=career,
        eligibility_output=eligibility,
    )

    assert str(source_record_id) in graph.source_record_ids
    assert str(verification_id) in graph.verification_record_ids
    assert "cricsheet-register" in graph.primary_sources
    assert "internal-player-registry" in graph.primary_sources
    assert "Official IPL policy" in graph.primary_sources
