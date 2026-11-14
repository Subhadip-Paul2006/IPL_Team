"""Unit tests for CDCRE Post-Identity Career Retrieval (Milestone 3).

Part of Phase 04A — Career Discovery & Competition Research Engine.
Tests AC-10 enforcement, CareerDataCoverage contract compliance, The Hundred
5-ball format semantics, deferred rate metrics, multi-competition career aggregation,
and R6 identity anti-merging across 13 tournament datasets and 141 organizer competitions.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from src.cdcre import (
    CareerRetrievalEngine,
    CompetitionRegistry,
    derive_competition_uuid,
    derive_provenance_uuid,
    discover_career,
)
from src.contracts.cdcre import (
    CareerDataCoverage,
    CompetitionHistoryRecord,
    CoverageStatus,
)

from tests.fixtures.cdcre_career_fixtures import (
    AAA_AMSTERDAM_UUID,
    ABDUL_SAMAD_PAK_UUID,
    ABDUL_SAMAD_SRH_UUID,
    DP_HUGHES_CRICSHEET_UUID,
    IPL_COMPETITION_UUID,
    JOS_BUTTLER_CRICSHEET_UUID,
    JOS_BUTTLER_ORGANIZER_UUID,
    SANJU_SAMSON_CRICSHEET_UUID,
    SANJU_SAMSON_ORGANIZER_UUID,
    SYNTHETIC_HUNDRED_PLAYER_UUID,
    SYNTHETIC_NONEXISTENT_PLAYER_UUID,
    SYNTHETIC_STANDARD_PLAYER_UUID,
)

pytest_plugins = ["tests.fixtures.cdcre_career_fixtures"]

# =============================================================================
# 1. AC-10 Interface Contract Enforcement Tests
# =============================================================================


class TestAC10InterfaceContract:
    """Verify discover_career strictly requires canonical UUID and rejects non-UUID inputs."""

    def test_signature_has_only_canonical_player_id(self) -> None:
        """discover_career signature must declare canonical_player_id as first parameter."""
        sig = inspect.signature(discover_career)
        param_names = list(sig.parameters.keys())
        assert param_names == ["canonical_player_id"]
        assert sig.parameters["canonical_player_id"].annotation in (UUID, "UUID")

    def test_accepts_valid_uuid_instance(self) -> None:
        """discover_career succeeds when given a genuine UUID instance."""
        valid_uuid = uuid4()
        cov = discover_career(valid_uuid)
        assert isinstance(cov, CareerDataCoverage)
        assert cov.canonical_player_id == valid_uuid

    def test_rejects_none_with_type_error(self) -> None:
        """discover_career must raise TypeError when canonical_player_id is None."""
        with pytest.raises(TypeError, match="canonical_player_id cannot be None"):
            discover_career(None)  # type: ignore[arg-type]

    def test_rejects_raw_name_string_with_type_error(self) -> None:
        """discover_career must reject raw player name strings (AC-10 circular dependency guard)."""
        with pytest.raises(TypeError, match="strictly requires a valid UUID instance"):
            discover_career("Sanju Samson")  # type: ignore[arg-type]

    def test_rejects_string_uuid_with_type_error(self) -> None:
        """discover_career must reject string representations of UUIDs."""
        str_uuid = str(uuid4())
        with pytest.raises(TypeError, match="strictly requires a valid UUID instance"):
            discover_career(str_uuid)  # type: ignore[arg-type]

    @pytest.mark.parametrize("invalid_input", [12345, 99.9, True, [uuid4()], {"id": uuid4()}])
    def test_rejects_other_non_uuid_types_with_type_error(self, invalid_input: Any) -> None:
        """discover_career must reject non-UUID primitive and composite types."""
        with pytest.raises(TypeError, match="strictly requires a valid UUID instance"):
            discover_career(invalid_input)

    def test_rejects_unexpected_keyword_arguments(self) -> None:
        """discover_career must reject unexpected extra arguments like raw_name."""
        with pytest.raises(TypeError):
            discover_career(uuid4(), raw_name="Sanju Samson")  # type: ignore[call-arg]


# =============================================================================
# 2. CareerDataCoverage Contract Compliance Tests
# =============================================================================


class TestCareerDataCoverageContractCompliance:
    """Verify returned CareerDataCoverage respects all domain invariants and schema constraints."""

    def test_returned_type_is_career_data_coverage(self) -> None:
        """discover_career must return an instance of CareerDataCoverage."""
        cov = discover_career(SANJU_SAMSON_ORGANIZER_UUID)
        assert isinstance(cov, CareerDataCoverage)
        assert cov.canonical_player_id == SANJU_SAMSON_ORGANIZER_UUID

    def test_evaluated_count_matches_covered_records(self) -> None:
        """competitions_evaluated_count must match len(competitions_covered)."""
        cov = discover_career(SANJU_SAMSON_ORGANIZER_UUID)
        assert cov.competitions_evaluated_count == len(cov.competitions_covered)
        assert cov.competitions_evaluated_count > 0

    def test_coverage_summary_counts_match_status(self) -> None:
        """coverage_summary dictionary counts must match competition coverage statuses."""
        cov = discover_career(SANJU_SAMSON_ORGANIZER_UUID)
        verified_count = sum(
            1 for r in cov.competitions_covered if r.coverage_status == CoverageStatus.VERIFIED_PARTICIPATION
        )
        assert cov.coverage_summary.get(CoverageStatus.VERIFIED_PARTICIPATION) == verified_count

    def test_career_gaps_is_empty_in_m3(self) -> None:
        """career_gaps must remain an empty list in Milestone 3 (M4 will populate)."""
        cov = discover_career(SANJU_SAMSON_ORGANIZER_UUID)
        assert isinstance(cov.career_gaps, list)
        assert len(cov.career_gaps) == 0

    def test_contract_extra_field_forbidden(self) -> None:
        """CareerDataCoverage forbids extra inputs (Pydantic v2 extra='forbid')."""
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            CareerDataCoverage(
                canonical_player_id=uuid4(),
                rogue_extra_field="unauthorized",  # type: ignore[call-arg]
            )

    def test_contract_validate_assignment(self) -> None:
        """CareerDataCoverage validates assignments."""
        cov = discover_career(SANJU_SAMSON_ORGANIZER_UUID)
        with pytest.raises(ValidationError):
            cov.competitions_evaluated_count = -5  # Negative count forbidden

    def test_serialization_roundtrip(self) -> None:
        """CareerDataCoverage serializes to JSON and deserializes identically."""
        cov = discover_career(SANJU_SAMSON_ORGANIZER_UUID)
        json_data = cov.model_dump_json()
        restored = CareerDataCoverage.model_validate_json(json_data)
        assert restored == cov


# =============================================================================
# 3. Non-Existent Player Career Retrieval Tests
# =============================================================================


class TestNonExistentPlayerCareerRetrieval:
    """Verify querying non-existent or zero-match players returns clean zero-appearance coverage."""

    def test_random_uuid_returns_zero_appearances(self) -> None:
        """Querying an unknown player UUID returns 0 covered competitions and 0 appearances."""
        query_uuid = uuid4()
        cov = discover_career(query_uuid)
        assert cov.canonical_player_id == query_uuid
        assert cov.competitions_evaluated_count == 0
        assert len(cov.competitions_covered) == 0
        assert cov.the_hundred_appearances_deferred is False
        assert cov.coverage_summary == {CoverageStatus.VERIFIED_PARTICIPATION: 0}
        assert cov.career_gaps == []

    def test_synthetic_nonexistent_uuid(self) -> None:
        """Synthetic nonexistent fixture UUID returns empty covered competitions."""
        cov = discover_career(SYNTHETIC_NONEXISTENT_PLAYER_UUID)
        assert cov.canonical_player_id == SYNTHETIC_NONEXISTENT_PLAYER_UUID
        assert len(cov.competitions_covered) == 0
        assert cov.the_hundred_appearances_deferred is False


# =============================================================================
# 4. The Hundred 5-Ball Semantics & Deferred Rate Metrics Tests
# =============================================================================


class TestTheHundredSemantics:
    """Verify The Hundred 5-ball format semantics across 201 matches and deferred rate metrics."""

    def test_synthetic_hundred_player_defers_rate_metrics(
        self,
        mock_career_engine: CareerRetrievalEngine,
    ) -> None:
        """A player with appearances in The Hundred has the_hundred_appearances_deferred = True."""
        cov = mock_career_engine.discover_career(SYNTHETIC_HUNDRED_PLAYER_UUID)
        assert cov.the_hundred_appearances_deferred is True
        for rec in cov.competitions_covered:
            assert rec.balls_per_over == 5
            assert rec.format_tag == "100-ball"
            assert rec.appearances is not None and rec.appearances > 0

    def test_synthetic_standard_player_does_not_defer(
        self,
        mock_career_engine: CareerRetrievalEngine,
    ) -> None:
        """A player without appearances in The Hundred has the_hundred_appearances_deferred = False."""
        cov = mock_career_engine.discover_career(SYNTHETIC_STANDARD_PLAYER_UUID)
        assert cov.the_hundred_appearances_deferred is False
        for rec in cov.competitions_covered:
            assert rec.balls_per_over == 6
            assert rec.format_tag in ("T20", "T20I", "ODI")

    def test_real_jos_buttler_hundred_appearances(self) -> None:
        """Real player Jos Buttler played in The Hundred; defers rate metrics and sets balls_per_over=5."""
        cov = discover_career(JOS_BUTTLER_ORGANIZER_UUID)
        assert cov.the_hundred_appearances_deferred is True

        hundred_records = [
            r for r in cov.competitions_covered if "Hundred" in r.competition_name
        ]
        assert len(hundred_records) >= 3
        for r in hundred_records:
            assert r.balls_per_over == 5
            assert r.format_tag == "100-ball"
            assert r.appearances is not None and r.appearances > 0

        # Non-Hundred records in Buttler's career must retain balls_per_over = 6
        non_hundred = [
            r for r in cov.competitions_covered if "Hundred" not in r.competition_name
        ]
        assert len(non_hundred) > 0
        for r in non_hundred:
            assert r.balls_per_over == 6

    def test_real_sanju_samson_has_zero_hundred_appearances(self) -> None:
        """Real player Sanju Samson never played in The Hundred; deferred flag is strictly False."""
        cov = discover_career(SANJU_SAMSON_ORGANIZER_UUID)
        assert cov.the_hundred_appearances_deferred is False
        for r in cov.competitions_covered:
            assert r.balls_per_over == 6
            assert "Hundred" not in r.competition_name

    def test_the_hundred_directory_all_matches_have_5_balls(self) -> None:
        """Direct file audit: all 201 JSON matches in hnd_male_json have balls_per_over: 5."""
        hnd_dir = Path("datasets/hnd_male_json")
        if not hnd_dir.exists():
            pytest.skip("datasets/hnd_male_json not found")

        import json

        json_files = list(hnd_dir.glob("*.json"))
        assert len(json_files) == 201
        for jf in json_files:
            with open(jf, encoding="utf-8") as f:
                data = json.load(f)
                balls = data.get("info", {}).get("balls_per_over")
                assert balls == 5, f"Match {jf.name} balls_per_over is {balls}, expected 5"


# =============================================================================
# 5. Real Dataset Multi-Competition Aggregation & Season Breakdown Tests
# =============================================================================


class TestRealDatasetCareerAggregation:
    """Verify career retrieval against real canonical CricSheet and organizer data."""

    def test_sanju_samson_ipl_and_smat_career(self) -> None:
        """Sanju Samson has verified match appearances in IPL, SMAT, and bilateral T20Is."""
        cov = discover_career(SANJU_SAMSON_ORGANIZER_UUID)
        comp_names = {r.competition_name for r in cov.competitions_covered}

        assert "Indian Premier League" in comp_names
        assert "Syed Mushtaq Ali Trophy" in comp_names

        # Verify IPL seasons are represented
        ipl_seasons = [r for r in cov.competitions_covered if r.competition_name == "Indian Premier League"]
        assert len(ipl_seasons) >= 10
        total_ipl_appearances = sum(r.appearances or 0 for r in ipl_seasons)
        assert total_ipl_appearances >= 160

        # Verify SMAT seasons are represented
        smat_seasons = [r for r in cov.competitions_covered if r.competition_name == "Syed Mushtaq Ali Trophy"]
        assert len(smat_seasons) >= 5
        total_smat_appearances = sum(r.appearances or 0 for r in smat_seasons)
        assert total_smat_appearances >= 25

    def test_sanju_samson_cricsheet_uuid_matches_organizer_uuid(self) -> None:
        """Querying by CricSheet UUID (a4cc73aa) returns the same career as organizer UUID (2258)."""
        cov_org = discover_career(SANJU_SAMSON_ORGANIZER_UUID)
        cov_cric = discover_career(SANJU_SAMSON_CRICSHEET_UUID)

        assert len(cov_org.competitions_covered) == len(cov_cric.competitions_covered)
        assert cov_org.the_hundred_appearances_deferred == cov_cric.the_hundred_appearances_deferred
        assert cov_org.competitions_evaluated_count == cov_cric.competitions_evaluated_count

    def test_jos_buttler_cricsheet_uuid_matches_organizer_uuid(self) -> None:
        """Querying by CricSheet UUID (99b75528) returns the same career as organizer UUID (813)."""
        cov_org = discover_career(JOS_BUTTLER_ORGANIZER_UUID)
        cov_cric = discover_career(JOS_BUTTLER_CRICSHEET_UUID)

        assert len(cov_org.competitions_covered) == len(cov_cric.competitions_covered)
        assert cov_org.the_hundred_appearances_deferred is True
        assert cov_cric.the_hundred_appearances_deferred is True

    def test_cricsheet_only_player_dp_hughes(self) -> None:
        """Querying pure CricSheet player DP Hughes returns verified BBL and Hundred appearances."""
        cov = discover_career(DP_HUGHES_CRICSHEET_UUID)
        assert isinstance(cov, CareerDataCoverage)
        assert cov.canonical_player_id == DP_HUGHES_CRICSHEET_UUID
        assert cov.competitions_evaluated_count >= 1
        comp_names = {r.competition_name for r in cov.competitions_covered}
        assert "Big Bash League" in comp_names
        assert cov.the_hundred_appearances_deferred is True

    def test_zero_match_cricsheet_person_aaa_amsterdam(self) -> None:
        """AAA Amsterdam is an umpire in people.csv; returns 0 appearances in competitions."""
        cov = discover_career(AAA_AMSTERDAM_UUID)
        assert cov.competitions_evaluated_count == 0
        assert len(cov.competitions_covered) == 0
        assert cov.the_hundred_appearances_deferred is False

    def test_every_history_record_has_valid_fields(self) -> None:
        """All CompetitionHistoryRecord instances contain valid IDs, seasons, and provenance."""
        cov = discover_career(SANJU_SAMSON_ORGANIZER_UUID)
        for r in cov.competitions_covered:
            assert isinstance(r.competition_id, UUID)
            assert len(r.competition_name) > 0
            assert len(r.season_year) > 0
            assert r.format_tag in ("T20", "T20I", "ODI", "100-ball")
            assert r.appearances is not None and r.appearances > 0
            assert r.coverage_status == CoverageStatus.VERIFIED_PARTICIPATION
            assert r.balls_per_over in (5, 6)
            assert isinstance(r.provenance_record_id, UUID)


# =============================================================================
# 6. Anti-Merging Guardrails Tests (Rule R6)
# =============================================================================


class TestAntiMergingGuardrails:
    """Verify colliding player identities remain strictly segregated per R6 invariant."""

    def test_abdul_samad_identities_remain_segregated(self) -> None:
        """Abdul Samad (SRH/LSG 7446) and Abdul Samad (Pakistan 6922) maintain distinct careers."""
        cov_srh = discover_career(ABDUL_SAMAD_SRH_UUID)
        cov_pak = discover_career(ABDUL_SAMAD_PAK_UUID)

        assert cov_srh.canonical_player_id != cov_pak.canonical_player_id

        srh_comps = {r.competition_name for r in cov_srh.competitions_covered}
        pak_comps = {r.competition_name for r in cov_pak.competitions_covered}

        # SRH player must have IPL appearances
        assert "Indian Premier League" in srh_comps
        # Pakistan player must NOT have IPL appearances
        assert "Indian Premier League" not in pak_comps


# =============================================================================
# 7. Custom / Subsampled Datasets Support & High Performance
# =============================================================================


class TestCustomDatasetsSupport:
    """Verify CompetitionRegistry and CareerRetrievalEngine support custom/mock datasets."""

    def test_custom_empty_dataset_dir(self, tmp_path: Path) -> None:
        """Engine initialized on an empty directory gracefully produces zero records."""
        custom_registry = CompetitionRegistry(datasets_dir=tmp_path, enable_cache=False)
        custom_engine = CareerRetrievalEngine(registry=custom_registry)

        cov = custom_engine.discover_career(uuid4())
        assert cov.competitions_evaluated_count == 0
        assert len(cov.competitions_covered) == 0
        assert cov.the_hundred_appearances_deferred is False

    def test_subsampled_competition_registration(self, tmp_path: Path) -> None:
        """Synthetic competition history can be manually registered for fast targeted testing."""
        registry = CompetitionRegistry(datasets_dir=tmp_path, enable_cache=False)
        test_uuid = uuid4()
        custom_records = [
            CompetitionHistoryRecord(
                competition_id=IPL_COMPETITION_UUID,
                competition_name="Indian Premier League",
                season_year="2024",
                format_tag="T20",
                appearances=14,
                coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
                balls_per_over=6,
                provenance_record_id=derive_provenance_uuid("custom:2024"),
            )
        ]
        registry.register_competition_history(test_uuid, custom_records)
        engine = CareerRetrievalEngine(registry=registry)

        cov = engine.discover_career(test_uuid)
        assert cov.competitions_evaluated_count == 1
        assert cov.competitions_covered[0].appearances == 14
        assert cov.the_hundred_appearances_deferred is False

    def test_derive_competition_uuid_determinism(self) -> None:
        """derive_competition_uuid returns deterministic UUIDv5 instances."""
        uuid1 = derive_competition_uuid("Indian Premier League")
        uuid2 = derive_competition_uuid("  Indian Premier League  ")
        assert uuid1 == uuid2
        assert uuid1 == IPL_COMPETITION_UUID

    def test_derive_provenance_uuid_determinism(self) -> None:
        """derive_provenance_uuid produces identical UUIDs for identical source tags."""
        p1 = derive_provenance_uuid("ipl:2024")
        p2 = derive_provenance_uuid("IPL:2024  ")
        assert p1 == p2
        assert isinstance(p1, UUID)
