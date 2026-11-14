"""Unit tests for CDCRE Pre-Identity Candidate Discovery (Milestone 2).

Verifies AC-10 compliance (accepts raw names only, forbids player_id), resolution
of all 7 name-collision fixtures into MULTIPLE without auto-merging (R6 invariant),
single-match resolution, non-existent name handling, and clean_name normalization invariance.
"""

from __future__ import annotations

import csv
import inspect
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from src.cdcre import (
    CandidateDiscoveryEngine,
    PreIdentityCandidateDiscovery,
    derive_player_uuid,
    discover_candidates,
    get_candidate_discovery_engine,
)
from src.contracts.cdcre import (
    AmbiguityStatus,
    CandidateDiscoveryResult,
    CandidatePlayerRecord,
)

from tests.fixtures.cdcre_candidate_fixtures import (
    KNOWN_COLLISION_FIXTURES,
    NON_EXISTENT_QUERIES,
    PUNCTUATION_CASING_FIXTURES,
    SINGLE_MATCH_FIXTURES,
)

# =============================================================================
# 1. AC-10 Interface Contract Verification Tests
# =============================================================================


class TestAC10InterfaceContract:
    """Tests verifying strict adherence to Acceptance Criterion AC-10.

    AC-10: discover_candidates accepts raw name strings only, never requires,
    accepts, or inspects player_id.
    """

    def test_signature_has_only_raw_name_parameter(self) -> None:
        """AC-10: discover_candidates function signature must expose only raw_name."""
        sig = inspect.signature(discover_candidates)
        param_names = list(sig.parameters.keys())
        assert param_names == ["raw_name"], (
            f"Expected only ['raw_name'] in discover_candidates signature, got {param_names}"
        )
        assert "player_id" not in param_names, "AC-10 violation: player_id must not be a parameter"

    def test_accepts_raw_name_string(self) -> None:
        """AC-10: Valid raw name string query executes successfully."""
        result = discover_candidates("Sanju Samson")
        assert isinstance(result, CandidateDiscoveryResult)
        assert result.raw_name_query == "Sanju Samson"

    def test_rejects_player_id_keyword_argument(self) -> None:
        """AC-10: Attempting to pass player_id as keyword argument must raise TypeError."""
        dummy_uuid = uuid4()
        with pytest.raises(TypeError, match="unexpected keyword argument 'player_id'"):
            # Type ignore to test dynamic invocation robustness
            discover_candidates("Sanju Samson", player_id=dummy_uuid)  # type: ignore[call-arg]

    def test_rejects_player_id_string_keyword_argument(self) -> None:
        """AC-10: Attempting to pass player_id string keyword argument must raise TypeError."""
        with pytest.raises(TypeError, match="unexpected keyword argument 'player_id'"):
            discover_candidates("Sanju Samson", player_id="2258")  # type: ignore[call-arg]

    def test_rejects_extra_positional_arguments(self) -> None:
        """AC-10: Passing additional positional arguments raises TypeError."""
        with pytest.raises(TypeError):
            discover_candidates("Sanju Samson", "extra_argument")  # type: ignore[call-arg]

    @pytest.mark.parametrize("invalid_input", [None, 12345, 99.9, uuid4(), [], {}])
    def test_rejects_non_string_raw_name(self, invalid_input: Any) -> None:
        """AC-10: Non-string inputs must raise TypeError."""
        with pytest.raises(TypeError, match="discover_candidates expects"):
            discover_candidates(invalid_input)


# =============================================================================
# 2. Seven Known Name-Collision Fixtures Tests
# =============================================================================


class TestSevenCollisionFixtures:
    """Tests verifying resolution of all 7 known name collisions into MULTIPLE.

    Invariants:
    - Never auto-merge ambiguous player identities (R6 invariant).
    - Emits AmbiguityStatus.MULTIPLE with collision_detected=True.
    - Emits distinct CandidatePlayerRecord instances with unique UUIDs.
    """

    @pytest.mark.parametrize(
        "fixture",
        KNOWN_COLLISION_FIXTURES,
        ids=[f["name"] for f in KNOWN_COLLISION_FIXTURES],
    )
    def test_collision_fixture_emits_multiple(self, fixture: dict[str, Any]) -> None:
        """Verify each collision fixture resolves to MULTIPLE with 2 separate records."""
        name = fixture["name"]
        result = discover_candidates(name)

        # 1. State verification
        assert result.ambiguity_status == AmbiguityStatus.MULTIPLE, (
            f"Expected MULTIPLE for {name}, got {result.ambiguity_status}"
        )
        assert result.collision_detected is True, (
            f"collision_detected must be True for ambiguous {name}"
        )

        # 2. Candidate count verification
        assert len(result.candidates) == 2, (
            f"Expected exactly 2 distinct candidates for {name}, found {len(result.candidates)}"
        )

        c1, c2 = result.candidates[0], result.candidates[1]

        # 3. Anti-merge verification: candidate UUIDs, source IDs, and context
        assert c1.player_id is not None
        assert c2.player_id is not None
        assert c1.player_id != c2.player_id, (
            f"R6 Invariant violation: candidates for {name} share the same player_id ({c1.player_id})"
        )
        assert c1.source_id != c2.source_id, (
            f"Candidates for {name} must have distinct source_ids"
        )
        assert (c1.teams != c2.teams) or (c1.competitions != c2.competitions), (
            f"Candidates for {name} must have distinct tournament or team contexts"
        )

        # 4. Content verification matching organizer mapping
        returned_source_ids = {c.source_id for c in result.candidates}
        expected_source_ids = {fixture["cand1_id"], fixture["cand2_id"]}
        assert returned_source_ids == expected_source_ids, (
            f"Expected sources {expected_source_ids}, got {returned_source_ids}"
        )

    def test_abdul_samad_specific_disambiguation(self) -> None:
        """Verify Abdul Samad resolves to SRH/LSG and Pakistan candidates."""
        result = discover_candidates("Abdul Samad")
        assert result.ambiguity_status == AmbiguityStatus.MULTIPLE
        assert result.collision_detected is True
        cand_by_source = {c.source_id: c for c in result.candidates}

        srh_cand = cand_by_source.get("organizer_7446")
        assert srh_cand is not None
        assert any("Sunrisers Hyderabad" in t for t in srh_cand.teams)
        assert any("IPL" in comp for comp in srh_cand.competitions)

        pak_cand = cand_by_source.get("organizer_6922")
        assert pak_cand is not None
        assert "Pakistan" in pak_cand.teams

    def test_rashid_khan_specific_disambiguation(self) -> None:
        """Verify Rashid Khan resolves to Gujarat Titans (AFG) and Nepal candidates."""
        result = discover_candidates("Rashid Khan")
        assert result.ambiguity_status == AmbiguityStatus.MULTIPLE
        assert result.collision_detected is True
        cand_by_source = {c.source_id: c for c in result.candidates}

        gt_cand = cand_by_source.get("organizer_4722")
        assert gt_cand is not None
        assert "Gujarat Titans" in gt_cand.teams
        assert "Afghanistan" in gt_cand.teams

        nep_cand = cand_by_source.get("organizer_20172")
        assert nep_cand is not None
        assert "Nepal" in nep_cand.teams


# =============================================================================
# 3. Single Corroborated Match Tests
# =============================================================================


class TestSingleCorroboratedMatch:
    """Tests verifying single unique matches emit SINGLE_CORROBORATED."""

    @pytest.mark.parametrize(
        "fixture",
        SINGLE_MATCH_FIXTURES,
        ids=[f["query"] for f in SINGLE_MATCH_FIXTURES],
    )
    def test_single_match_emits_single_corroborated(self, fixture: dict[str, Any]) -> None:
        """Verify query returns SINGLE_CORROBORATED with exactly 1 candidate."""
        query = fixture["query"]
        result = discover_candidates(query)

        assert result.ambiguity_status == AmbiguityStatus.SINGLE_CORROBORATED, (
            f"Expected SINGLE_CORROBORATED for {query}, got {result.ambiguity_status}"
        )
        assert result.collision_detected is False
        assert len(result.candidates) == 1

        cand = result.candidates[0]
        assert cand.canonical_name == fixture["expected_canonical_name"]
        assert cand.source_id == fixture["expected_source_id"]
        assert cand.player_id is not None

        if fixture["expected_team"]:
            assert fixture["expected_team"] in cand.teams

    def test_alias_sv_samson_resolves_to_sanju_samson(self) -> None:
        """CricSheet alias 'SV Samson' resolves to organizer record of Sanju Samson."""
        res_alias = discover_candidates("SV Samson")
        res_canonical = discover_candidates("Sanju Samson")

        assert res_alias.ambiguity_status == AmbiguityStatus.SINGLE_CORROBORATED
        assert res_canonical.ambiguity_status == AmbiguityStatus.SINGLE_CORROBORATED

        # Both queries point to the exact same candidate
        assert res_alias.candidates[0].player_id == res_canonical.candidates[0].player_id
        assert res_alias.candidates[0].source_id == res_canonical.candidates[0].source_id
        assert "Rajasthan Royals" in res_alias.candidates[0].teams


# =============================================================================
# 4. Non-Existent Query Handling Tests
# =============================================================================


class TestNonExistentQueryHandling:
    """Tests verifying non-existent names or blank queries emit NONE."""

    @pytest.mark.parametrize("query", NON_EXISTENT_QUERIES)
    def test_non_existent_player_emits_none(self, query: str) -> None:
        """Verify non-existent names emit AmbiguityStatus.NONE with empty candidates."""
        result = discover_candidates(query)
        assert result.ambiguity_status == AmbiguityStatus.NONE
        assert result.collision_detected is False
        assert result.candidates == []
        assert result.raw_name_query == query

    def test_empty_string_emits_none(self) -> None:
        """Empty string query returns NONE without error."""
        result = discover_candidates("")
        assert result.ambiguity_status == AmbiguityStatus.NONE
        assert result.collision_detected is False
        assert result.candidates == []

    def test_whitespace_only_query_emits_none(self) -> None:
        """Whitespace-only query returns NONE without error."""
        result = discover_candidates("   \t  \n  ")
        assert result.ambiguity_status == AmbiguityStatus.NONE
        assert result.collision_detected is False
        assert result.candidates == []


# =============================================================================
# 5. Case, Whitespace, and Punctuation Invariance Tests
# =============================================================================


class TestNormalizationInvariance:
    """Tests verifying clean_name case, whitespace, and punctuation normalization."""

    @pytest.mark.parametrize(
        "fixture",
        PUNCTUATION_CASING_FIXTURES,
        ids=[f["canonical"] for f in PUNCTUATION_CASING_FIXTURES],
    )
    def test_variants_produce_identical_status_and_candidates(
        self,
        fixture: dict[str, Any],
    ) -> None:
        """All variations of a name produce identical ambiguity status and candidates."""
        canonical_query = fixture["canonical"]
        canonical_result = discover_candidates(canonical_query)

        assert canonical_result.ambiguity_status == fixture["expected_status"]

        for variant in fixture["variants"]:
            variant_result = discover_candidates(variant)
            assert variant_result.ambiguity_status == canonical_result.ambiguity_status, (
                f"Variant '{variant}' status {variant_result.ambiguity_status} != {canonical_result.ambiguity_status}"
            )
            assert len(variant_result.candidates) == len(canonical_result.candidates), (
                f"Candidate count mismatch for variant '{variant}'"
            )
            variant_sources = [c.source_id for c in variant_result.candidates]
            canonical_sources = [c.source_id for c in canonical_result.candidates]
            assert variant_sources == canonical_sources, (
                f"Candidate source IDs differ for variant '{variant}'"
            )


# =============================================================================
# 6. Contract and Model Serialization Compliance Tests
# =============================================================================


class TestContractCompliance:
    """Tests validating Pydantic model validation and serialization."""

    def test_candidate_discovery_result_model_dump_and_validate(self) -> None:
        """CandidateDiscoveryResult round-trips cleanly through Pydantic v2."""
        result = discover_candidates("Rashid Khan")
        dumped = result.model_dump()
        reconstructed = CandidateDiscoveryResult.model_validate(dumped)

        assert reconstructed == result
        assert reconstructed.ambiguity_status == AmbiguityStatus.MULTIPLE
        assert reconstructed.collision_detected is True

    def test_forbid_extra_fields_on_candidate_records(self) -> None:
        """BaseContract enforces extra='forbid' on CandidatePlayerRecord."""
        with pytest.raises(ValidationError):
            CandidatePlayerRecord(
                canonical_name="Test",
                extra_unknown_field="Forbidden",  # type: ignore[call-arg]
            )

    def test_candidate_discovery_engine_alias_and_getter(self) -> None:
        """CandidateDiscoveryEngine alias and get_candidate_discovery_engine work correctly."""
        engine = get_candidate_discovery_engine()
        assert isinstance(engine, CandidateDiscoveryEngine)
        assert isinstance(engine, PreIdentityCandidateDiscovery)


# =============================================================================
# 7. Isolated Engine Instance Tests
# =============================================================================


class TestIsolatedEngineInstance:
    """Tests verifying PreIdentityCandidateDiscovery operates in isolated environments."""

    def test_isolated_engine_custom_dir(self, tmp_path: Path) -> None:
        """Engine can initialize from custom directory with synthetic mapping."""
        # Create synthetic CSVs in tmp_path
        mapping_file = tmp_path / "competition_team_player_mapping.csv"
        with open(mapping_file, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["comp_id", "comp_name", "team_id", "team_name", "player_id", "player_name"])
            writer.writerow(["101", "Synthetic League", "T1", "Synthetic Team A", "9001", "Synthetic Star"])
            writer.writerow(["102", "Synthetic League", "T2", "Synthetic Team B", "9002", "Synthetic Star"])

        engine = PreIdentityCandidateDiscovery(datasets_dir=tmp_path)
        res = engine.discover("Synthetic Star")

        assert res.ambiguity_status == AmbiguityStatus.MULTIPLE
        assert res.collision_detected is True
        assert len(res.candidates) == 2
        assert {c.source_id for c in res.candidates} == {"organizer_9001", "organizer_9002"}

    def test_derive_player_uuid_determinism(self) -> None:
        """derive_player_uuid generates identical deterministic UUIDv5 values."""
        uuid_a = derive_player_uuid("organizer_7446")
        uuid_b = derive_player_uuid("ORGANIZER_7446  ")
        assert isinstance(uuid_a, UUID)
        assert uuid_a == uuid_b
