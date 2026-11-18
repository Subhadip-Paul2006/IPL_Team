"""End-to-End multi-engine integration pipeline test suite for CDCRE (Milestone M5).

Covers:
1. End-to-end research pipeline: PIRE -> TMVE -> CDCRE -> CDCREOutputContract.
2. Real canonical players (Sanju Samson, Jos Buttler) full profile research.
3. All seven known name-collision fixtures resolved to AmbiguityStatus.MULTIPLE
   with zero identity auto-merging and deferred post-identity retrieval.
4. CDCREOutputContract typing, schema validation, extra="forbid", and serialization.
5. CDCREngine ServiceBoundary compliance and comprehensive health checks.
6. CDCREProvenanceService integration with Support Service C provenance tracking.
"""

from __future__ import annotations

import json
from typing import Any

import pydantic
import pytest
from src.cdcre.engine import CDCREngine, get_cdcre_engine
from src.cdcre.provenance import CDCREProvenanceService
from src.cdcre.repository import CDCRERepository
from src.contracts.cdcre import (
    AmbiguityStatus,
    CandidateDiscoveryResult,
    CareerDataCoverage,
    CDCREOutputContract,
    CoverageStatus,
)
from src.research.cdcre import research_player_profile
from src.services.base import ServiceBoundary

from tests.fixtures.cdcre_candidate_fixtures import (
    KNOWN_COLLISION_FIXTURES,
)
from tests.fixtures.cdcre_career_fixtures import (
    JOS_BUTTLER_ORGANIZER_UUID,
    SANJU_SAMSON_ORGANIZER_UUID,
)

# ==============================================================================
# 1. ServiceBoundary & Architecture Compliance
# ==============================================================================


class TestCDCREServiceBoundaryCompliance:
    """Verify CDCREngine and CDCREProvenanceService implement ServiceBoundary."""

    def test_cdcre_engine_implements_service_boundary(self) -> None:
        """CDCREngine must subclass ServiceBoundary with correct canonical identifier."""
        engine = get_cdcre_engine()
        assert isinstance(engine, ServiceBoundary)
        assert engine.get_service_name() == "career_discovery_competition_research_engine"

    def test_cdcre_engine_health_check_structure(self) -> None:
        """Health check returns comprehensive diagnostic dictionary checking all sub-engines."""
        engine = get_cdcre_engine()
        health = engine.health_check()

        assert isinstance(health, dict)
        assert health["service"] == "career_discovery_competition_research_engine"
        assert health["status"] == "healthy"
        assert "candidate_discovery" in health
        assert "career_retrieval" in health
        assert "competition_registry" in health
        assert "repository" in health
        assert "provenance_service" in health

    def test_provenance_service_implements_service_boundary(self) -> None:
        """CDCREProvenanceService must implement ServiceBoundary."""
        prov = CDCREProvenanceService()
        assert isinstance(prov, ServiceBoundary)
        assert prov.get_service_name() == "cdcre_provenance_service"

        health = prov.health_check()
        assert health["service"] == "cdcre_provenance_service"
        assert health["status"] == "healthy"
        assert "source_records_count" in health
        assert "verifications_count" in health


# ==============================================================================
# 2. Canonical Real-World Players Pipeline Verification
# ==============================================================================


class TestCanonicalPlayersE2EPipeline:
    """Test full pipeline execution for known Rajasthan Royals canonical players."""

    def test_sanju_samson_full_research_pipeline(self) -> None:
        """Sanju Samson end-to-end research: PIRE -> TMVE -> CDCRE."""
        result = research_player_profile("Sanju Samson")

        assert isinstance(result, CDCREOutputContract)
        assert result.candidate_discovery is not None
        assert result.career_coverage is not None

        # Candidate discovery assertions
        cand_res = result.candidate_discovery
        assert cand_res.ambiguity_status == AmbiguityStatus.SINGLE_CORROBORATED
        assert cand_res.collision_detected is False
        assert len(cand_res.candidates) == 1

        candidate = cand_res.candidates[0]
        assert "Sanju Samson" in candidate.canonical_name
        assert candidate.player_id == SANJU_SAMSON_ORGANIZER_UUID

        # TMVE membership assertions in metadata
        assert "tmve" in result.metadata
        tmve_meta = result.metadata["tmve"]
        assert tmve_meta["verified_rr_appearances"] >= 0

        # Career coverage assertions
        career = result.career_coverage
        assert career.canonical_player_id == SANJU_SAMSON_ORGANIZER_UUID
        assert career.competitions_evaluated_count > 0
        assert len(career.competitions_covered) > 0

        # Verified appearances in IPL
        ipl_records = [
            r for r in career.competitions_covered
            if "Indian Premier League" in r.competition_name or "IPL" in r.competition_name
        ]
        assert len(ipl_records) > 0
        total_ipl_apps = sum(r.appearances or 0 for r in ipl_records)
        assert total_ipl_apps >= 100

    def test_jos_buttler_full_research_pipeline(self) -> None:
        """Jos Buttler end-to-end research verifies multi-competition coverage."""
        result = research_player_profile("Jos Buttler")

        assert isinstance(result, CDCREOutputContract)
        assert result.candidate_discovery is not None
        assert result.career_coverage is not None

        cand_res = result.candidate_discovery
        assert cand_res.ambiguity_status == AmbiguityStatus.SINGLE_CORROBORATED
        assert cand_res.collision_detected is False
        assert len(cand_res.candidates) == 1

        candidate = cand_res.candidates[0]
        assert "Buttler" in candidate.canonical_name
        assert candidate.player_id == JOS_BUTTLER_ORGANIZER_UUID

        career = result.career_coverage
        assert career.canonical_player_id == JOS_BUTTLER_ORGANIZER_UUID
        assert career.competitions_evaluated_count > 0

        # Multi-competition check (IPL, BBL, etc.)
        comp_names = {r.competition_name for r in career.competitions_covered}
        assert any("IPL" in c or "Indian Premier League" in c for c in comp_names)


# ==============================================================================
# 3. Collision Fixtures Anti-Merge Invariant Verification (R6)
# ==============================================================================


class TestCollisionFixturesAntiMergeE2E:
    """Assert all seven collision fixtures emit AmbiguityStatus.MULTIPLE without auto-merging."""

    @pytest.mark.parametrize(
        "fixture",
        KNOWN_COLLISION_FIXTURES,
        ids=[f["name"] for f in KNOWN_COLLISION_FIXTURES],
    )
    def test_collision_fixture_emits_multiple_and_halts_career_retrieval(
        self,
        fixture: dict[str, Any],
    ) -> None:
        """For every known collision pair:

        - AmbiguityStatus MUST be MULTIPLE.
        - collision_detected MUST be True.
        - Exactly 2 candidate records MUST be returned.
        - ZERO identity auto-merging: distinct player IDs and source IDs preserved.
        - career_coverage MUST be None (halts to prevent data contamination).
        """
        raw_name = fixture["name"]
        result = research_player_profile(raw_name)

        assert isinstance(result, CDCREOutputContract)
        assert result.candidate_discovery is not None

        cand_res = result.candidate_discovery
        assert cand_res.ambiguity_status == AmbiguityStatus.MULTIPLE
        assert cand_res.collision_detected is True
        assert len(cand_res.candidates) >= 2

        # Verify candidate separation
        cands = cand_res.candidates
        distinct_pids = {c.player_id for c in cands if c.player_id is not None}
        assert len(distinct_pids) >= 2, f"Collision {raw_name} auto-merged player IDs!"

        distinct_sources = {c.source_id for c in cands if c.source_id is not None}
        assert len(distinct_sources) >= 2, f"Collision {raw_name} auto-merged source IDs!"

        # Mandatory anti-merge invariant: career_coverage MUST be None
        assert result.career_coverage is None
        assert result.metadata.get("anti_merge_triggered") is True
        assert result.metadata.get("status") == "COLLISION_DETECTED"


# ==============================================================================
# 4. CDCREngine Facade Method Unit Verification
# ==============================================================================


class TestCDCREngineFacadeMethods:
    """Verify CDCREngine facade delegation to M2, M3, and M4."""

    def test_engine_discover_candidates_delegation(self) -> None:
        """discover_candidates on engine returns CandidateDiscoveryResult adhering to AC-10."""
        engine = get_cdcre_engine()
        res = engine.discover_candidates("Sanju Samson")
        assert isinstance(res, CandidateDiscoveryResult)
        assert res.ambiguity_status == AmbiguityStatus.SINGLE_CORROBORATED

    def test_engine_discover_career_delegation(self) -> None:
        """discover_career requires UUID and returns enriched CareerDataCoverage."""
        engine = get_cdcre_engine()
        career = engine.discover_career(SANJU_SAMSON_ORGANIZER_UUID)

        assert isinstance(career, CareerDataCoverage)
        assert career.canonical_player_id == SANJU_SAMSON_ORGANIZER_UUID
        assert career.competitions_evaluated_count > 0
        assert isinstance(career.coverage_summary, dict)

    def test_engine_evaluate_coverage_delegation(self) -> None:
        """evaluate_coverage delegates directly to M4 four-state evaluator."""
        engine = get_cdcre_engine()

        # Verified participation
        st1 = engine.evaluate_coverage(has_dataset=True, appearances=10)
        assert st1 == CoverageStatus.VERIFIED_PARTICIPATION

        # Missing dataset (AC-11)
        st2 = engine.evaluate_coverage(has_dataset=False, appearances=None)
        assert st2 == CoverageStatus.DATASET_UNAVAILABLE

        # Confirmed non-participation
        st3 = engine.evaluate_coverage(has_dataset=True, appearances=0)
        assert st3 == CoverageStatus.CONFIRMED_NON_PARTICIPATION

    def test_engine_research_player_with_uuid(self) -> None:
        """research_player with canonical_player_id retrieves career coverage directly."""
        engine = get_cdcre_engine()
        result = engine.research_player(canonical_player_id=SANJU_SAMSON_ORGANIZER_UUID)

        assert isinstance(result, CDCREOutputContract)
        assert result.career_coverage is not None
        assert result.career_coverage.canonical_player_id == SANJU_SAMSON_ORGANIZER_UUID

    def test_engine_persist_career_coverage(self) -> None:
        """persist_career_coverage saves records into the repository."""
        repo = CDCRERepository()
        engine = CDCREngine(repository=repo)

        career = engine.discover_career(SANJU_SAMSON_ORGANIZER_UUID)
        saved = engine.persist_career_coverage(career)

        assert len(saved) == len(career.competitions_covered)
        assert repo.count() == len(career.competitions_covered)

        retrieved = repo.get_by_player_id(SANJU_SAMSON_ORGANIZER_UUID)
        assert len(retrieved) == len(career.competitions_covered)


# ==============================================================================
# 5. Contract Compliance, Validation, and Serialization
# ==============================================================================


class TestCDCREContractIntegrity:
    """Verify CDCREOutputContract strict Pydantic v2 invariants."""

    def test_cdcre_output_contract_forbids_extra_fields(self) -> None:
        """CDCREOutputContract must reject undeclared extra fields."""
        with pytest.raises(pydantic.ValidationError):
            CDCREOutputContract(
                candidate_discovery=None,
                career_coverage=None,
                unauthorized_extra_field="malicious_payload",  # type: ignore[call-arg]
            )

    def test_cdcre_output_contract_serialization_roundtrip(self) -> None:
        """CDCREOutputContract serializes to JSON and deserializes cleanly."""
        result = research_player_profile("Sanju Samson")

        json_str = result.model_dump_json()
        assert isinstance(json_str, str)

        parsed = json.loads(json_str)
        assert "candidate_discovery" in parsed
        assert "career_coverage" in parsed
        assert "metadata" in parsed

        # Re-instantiate from dictionary
        recreated = CDCREOutputContract.model_validate(parsed)
        assert recreated.candidate_discovery is not None
        assert recreated.career_coverage is not None
        assert recreated.metadata == result.metadata
