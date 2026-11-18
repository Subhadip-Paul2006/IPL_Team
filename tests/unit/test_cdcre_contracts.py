"""Unit tests for CDCRE (Career Discovery & Competition Research Engine) contracts.

Validates model serialization, deserialization, field validation, default values,
extra-field rejection, assignment validation, and enum constraints for TRD §5.1-§5.5
and PRD FR-C1-FR-C5 inter-engine runtime contracts.
"""

import warnings
from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from src.contracts.base import BaseContract
from src.contracts.cdcre import (
    AmbiguityStatus,
    CandidateDiscoveryResult,
    CandidatePlayerRecord,
    CareerDataCoverage,
    CareerGapRecord,
    CDCREOutputContract,
    CompetitionHistoryRecord,
    CoverageStatus,
    GapType,
)

from tests.fixtures.cdcre_contract_fixtures import (
    BPL_COMPETITION_UUID,
    HUNDRED_COMPETITION_UUID,
    PROVENANCE_SOURCE_UUID_1,
    PROVENANCE_SOURCE_UUID_2,
    SMAT_COMPETITION_UUID,
    SYNTHETIC_PLAYER_UUID_COLLISION_A,
    SYNTHETIC_PLAYER_UUID_COLLISION_B,
    SYNTHETIC_PLAYER_UUID_PRIMARY,
    build_synthetic_candidate_discovery,
    build_synthetic_candidate_record,
    build_synthetic_career_data_coverage,
    build_synthetic_career_gap,
    build_synthetic_cdcre_output,
    build_synthetic_collision_discovery,
    build_synthetic_competition_history,
    build_synthetic_hundred_history,
    build_synthetic_rr_suspension_gap,
    build_synthetic_unavailable_dataset_history,
)

warnings.filterwarnings("ignore", category=pytest.PytestAssertRewriteWarning)
pytest_plugins = ["tests.fixtures.cdcre_contract_fixtures"]

# =============================================================================
# 1. Enum Tests
# =============================================================================


def test_ambiguity_status_enum_values() -> None:
    """Verify AmbiguityStatus contains exact required states with matching str values."""
    expected_members = {
        "NONE": "NONE",
        "SINGLE_CORROBORATED": "SINGLE_CORROBORATED",
        "MULTIPLE": "MULTIPLE",
    }
    assert len(AmbiguityStatus) == len(expected_members)
    for name, value in expected_members.items():
        member = AmbiguityStatus[name]
        assert member.value == value
        assert member == value
        assert isinstance(member, str)


def test_coverage_status_enum_values() -> None:
    """Verify CoverageStatus contains exact 4-state taxonomy matching DDL chk_coverage_status."""
    expected_members = {
        "VERIFIED_PARTICIPATION": "VERIFIED_PARTICIPATION",
        "DATASET_UNAVAILABLE": "DATASET_UNAVAILABLE",
        "NOT_ESTABLISHED": "NOT_ESTABLISHED",
        "CONFIRMED_NON_PARTICIPATION": "CONFIRMED_NON_PARTICIPATION",
    }
    assert len(CoverageStatus) == len(expected_members)
    for name, value in expected_members.items():
        member = CoverageStatus[name]
        assert member.value == value
        assert member == value
        assert isinstance(member, str)


def test_gap_type_enum_values() -> None:
    """Verify GapType contains exact required career gap classification values."""
    expected_members = {
        "FRANCHISE_SUSPENSION": "FRANCHISE_SUSPENSION",
        "INJURY": "INJURY",
        "NOC_DENIED": "NOC_DENIED",
        "UNAVAILABLE": "UNAVAILABLE",
        "UNEXPLAINED_GAP": "UNEXPLAINED_GAP",
    }
    assert len(GapType) == len(expected_members)
    for name, value in expected_members.items():
        member = GapType[name]
        assert member.value == value
        assert member == value
        assert isinstance(member, str)


# =============================================================================
# 2. CandidatePlayerRecord Tests
# =============================================================================


def test_candidate_player_record_valid_instantiation() -> None:
    """Verify CandidatePlayerRecord instantiation with full explicit fields."""
    pid = uuid4()
    rec = CandidatePlayerRecord(
        player_id=pid,
        canonical_name="Sanju Samson",
        source_id="cricsheet_ss01",
        teams=["Rajasthan Royals", "Delhi Daredevils"],
        competitions=["Indian Premier League", "Syed Mushtaq Ali Trophy"],
        confidence=0.98,
    )
    assert rec.player_id == pid
    assert rec.canonical_name == "Sanju Samson"
    assert rec.source_id == "cricsheet_ss01"
    assert rec.teams == ["Rajasthan Royals", "Delhi Daredevils"]
    assert rec.competitions == ["Indian Premier League", "Syed Mushtaq Ali Trophy"]
    assert rec.confidence == 0.98


def test_candidate_player_record_defaults() -> None:
    """Verify CandidatePlayerRecord defaults for pre-identity discovery."""
    rec = CandidatePlayerRecord(canonical_name="Unresolved Candidate")
    assert rec.player_id is None
    assert rec.canonical_name == "Unresolved Candidate"
    assert rec.source_id is None
    assert rec.teams == []
    assert rec.competitions == []
    assert rec.confidence == 1.0


def test_candidate_player_record_uuid_string_coercion() -> None:
    """Verify CandidatePlayerRecord coerces string UUID to UUID object."""
    raw_uuid = "a1b2c3d4-e5f6-7890-1234-56789abcdef0"
    rec = CandidatePlayerRecord(
        player_id=raw_uuid,  # type: ignore[arg-type]
        canonical_name="Test Player",
    )
    assert rec.player_id == UUID(raw_uuid)


def test_candidate_player_record_missing_canonical_name_raises() -> None:
    """Verify missing required canonical_name raises ValidationError."""
    with pytest.raises(ValidationError):
        CandidatePlayerRecord()  # type: ignore[call-arg]


def test_candidate_player_record_extra_field_forbidden() -> None:
    """Verify extra fields are strictly forbidden."""
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CandidatePlayerRecord(
            canonical_name="Test",
            unauthorized_field="forbidden",  # type: ignore[call-arg]
        )


def test_candidate_player_record_validate_assignment() -> None:
    """Verify validate_assignment enforces bounds and types on attribute modification."""
    rec = CandidatePlayerRecord(canonical_name="Test Player", confidence=0.8)
    rec.confidence = 0.5
    assert rec.confidence == 0.5

    with pytest.raises(ValidationError):
        rec.confidence = 1.5  # Exceeds max 1.0

    with pytest.raises(ValidationError):
        rec.confidence = -0.1  # Subceeds min 0.0


def test_candidate_player_record_roundtrip_serialization() -> None:
    """Verify CandidatePlayerRecord serialization round-trip through dict and JSON."""
    rec = build_synthetic_candidate_record(
        player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
        canonical_name="Sanju Samson",
        source_id="cricsheet_ss01",
        teams=["Rajasthan Royals"],
        competitions=["Indian Premier League"],
        confidence=0.99,
    )
    dumped_dict = rec.model_dump()
    reconstituted = CandidatePlayerRecord.model_validate(dumped_dict)
    assert reconstituted == rec

    json_str = rec.model_dump_json()
    reconstituted_json = CandidatePlayerRecord.model_validate_json(json_str)
    assert reconstituted_json == rec


# =============================================================================
# 3. CandidateDiscoveryResult Tests
# =============================================================================


def test_candidate_discovery_result_single_corroborated() -> None:
    """Verify CandidateDiscoveryResult for a unique match."""
    cand = build_synthetic_candidate_record(canonical_name="Unique Player")
    result = CandidateDiscoveryResult(
        raw_name_query="Unique Player",
        ambiguity_status=AmbiguityStatus.SINGLE_CORROBORATED,
        candidates=[cand],
        collision_detected=False,
    )
    assert result.raw_name_query == "Unique Player"
    assert result.ambiguity_status == AmbiguityStatus.SINGLE_CORROBORATED
    assert len(result.candidates) == 1
    assert result.collision_detected is False


def test_candidate_discovery_result_collision_multiple() -> None:
    """Verify CandidateDiscoveryResult for a collision match (MULTIPLE)."""
    result = build_synthetic_collision_discovery("Rashid Khan")
    assert result.raw_name_query == "Rashid Khan"
    assert result.ambiguity_status == AmbiguityStatus.MULTIPLE
    assert len(result.candidates) == 2
    assert result.collision_detected is True
    assert result.candidates[0].player_id == SYNTHETIC_PLAYER_UUID_COLLISION_A
    assert result.candidates[1].player_id == SYNTHETIC_PLAYER_UUID_COLLISION_B


def test_candidate_discovery_result_none_defaults() -> None:
    """Verify CandidateDiscoveryResult for an unmatched query (NONE)."""
    result = CandidateDiscoveryResult(
        raw_name_query="Non Existent Player",
        ambiguity_status=AmbiguityStatus.NONE,
    )
    assert result.raw_name_query == "Non Existent Player"
    assert result.ambiguity_status == AmbiguityStatus.NONE
    assert result.candidates == []
    assert result.collision_detected is False


def test_candidate_discovery_result_missing_required_fields_raises() -> None:
    """Verify CandidateDiscoveryResult requires raw_name_query and ambiguity_status."""
    with pytest.raises(ValidationError):
        CandidateDiscoveryResult()  # type: ignore[call-arg]

    with pytest.raises(ValidationError):
        CandidateDiscoveryResult(raw_name_query="Query Only")  # type: ignore[call-arg]


def test_candidate_discovery_result_enum_string_coercion() -> None:
    """Verify string enum value is coerced to AmbiguityStatus."""
    result = CandidateDiscoveryResult(
        raw_name_query="Query",
        ambiguity_status="MULTIPLE",  # type: ignore[arg-type]
    )
    assert result.ambiguity_status == AmbiguityStatus.MULTIPLE


def test_candidate_discovery_result_invalid_enum_raises() -> None:
    """Verify invalid ambiguity status string raises ValidationError."""
    with pytest.raises(ValidationError):
        CandidateDiscoveryResult(
            raw_name_query="Query",
            ambiguity_status="INVALID_STATUS",  # type: ignore[arg-type]
        )


def test_candidate_discovery_result_extra_field_forbidden() -> None:
    """Verify extra fields are rejected."""
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CandidateDiscoveryResult(
            raw_name_query="Query",
            ambiguity_status=AmbiguityStatus.NONE,
            unexpected_field=123,  # type: ignore[call-arg]
        )


def test_candidate_discovery_result_roundtrip_serialization() -> None:
    """Verify CandidateDiscoveryResult round-trip serialization."""
    result = build_synthetic_collision_discovery("Abdul Samad")
    dumped = result.model_dump()
    assert CandidateDiscoveryResult.model_validate(dumped) == result

    json_str = result.model_dump_json()
    assert CandidateDiscoveryResult.model_validate_json(json_str) == result


# =============================================================================
# 4. CompetitionHistoryRecord Tests
# =============================================================================


def test_competition_history_record_valid_standard() -> None:
    """Verify standard 6-ball CompetitionHistoryRecord instantiation."""
    cid = uuid4()
    prov_id = uuid4()
    rec = CompetitionHistoryRecord(
        competition_id=cid,
        competition_name="Indian Premier League",
        season_year="2024",
        format_tag="T20",
        appearances=15,
        coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
        balls_per_over=6,
        provenance_record_id=prov_id,
    )
    assert rec.competition_id == cid
    assert rec.competition_name == "Indian Premier League"
    assert rec.season_year == "2024"
    assert rec.format_tag == "T20"
    assert rec.appearances == 15
    assert rec.coverage_status == CoverageStatus.VERIFIED_PARTICIPATION
    assert rec.balls_per_over == 6
    assert rec.provenance_record_id == prov_id


def test_competition_history_record_hundred_semantics() -> None:
    """Verify The Hundred 5-ball format semantics (balls_per_over = 5)."""
    rec = build_synthetic_hundred_history(
        competition_id=HUNDRED_COMPETITION_UUID,
        season_year="2023",
        appearances=8,
    )
    assert rec.balls_per_over == 5
    assert rec.format_tag == "THE_HUNDRED"
    assert rec.appearances == 8
    assert rec.coverage_status == CoverageStatus.VERIFIED_PARTICIPATION


def test_competition_history_record_dataset_unavailable_ac11() -> None:
    """Verify DATASET_UNAVAILABLE produces None appearances (AC-11)."""
    rec = build_synthetic_unavailable_dataset_history(
        competition_id=BPL_COMPETITION_UUID,
        competition_name="Bangladesh Premier League",
        season_year="2018",
    )
    assert rec.appearances is None
    assert rec.coverage_status == CoverageStatus.DATASET_UNAVAILABLE
    assert rec.provenance_record_id is None


def test_competition_history_record_negative_appearances_forbidden() -> None:
    """Verify negative appearances raises ValidationError."""
    with pytest.raises(ValidationError):
        CompetitionHistoryRecord(
            competition_id=uuid4(),
            competition_name="IPL",
            season_year="2024",
            format_tag="T20",
            appearances=-1,
            coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
        )


def test_competition_history_record_zero_balls_per_over_forbidden() -> None:
    """Verify balls_per_over must be strictly positive."""
    with pytest.raises(ValidationError):
        CompetitionHistoryRecord(
            competition_id=uuid4(),
            competition_name="IPL",
            season_year="2024",
            format_tag="T20",
            appearances=5,
            coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
            balls_per_over=0,
        )


def test_competition_history_record_missing_required_fields_raises() -> None:
    """Verify omission of required fields raises ValidationError."""
    with pytest.raises(ValidationError):
        CompetitionHistoryRecord()  # type: ignore[call-arg]

    with pytest.raises(ValidationError):
        CompetitionHistoryRecord(  # type: ignore[call-arg]
            competition_id=uuid4(),
            competition_name="IPL",
        )


def test_competition_history_record_extra_field_forbidden() -> None:
    """Verify extra fields are rejected."""
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CompetitionHistoryRecord(
            competition_id=uuid4(),
            competition_name="IPL",
            season_year="2024",
            format_tag="T20",
            appearances=5,
            coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
            fabricated_metric=99.9,  # type: ignore[call-arg]
        )


def test_competition_history_record_validate_assignment() -> None:
    """Verify validate_assignment enforces schema constraints on attribute write."""
    rec = build_synthetic_competition_history()
    rec.appearances = 20
    assert rec.appearances == 20

    with pytest.raises(ValidationError):
        rec.appearances = -5

    with pytest.raises(ValidationError):
        rec.coverage_status = "NOT_A_STATUS"  # type: ignore[assignment]


def test_competition_history_record_roundtrip_serialization() -> None:
    """Verify CompetitionHistoryRecord round-trip serialization."""
    rec = build_synthetic_competition_history(
        competition_id=SMAT_COMPETITION_UUID,
        competition_name="Syed Mushtaq Ali Trophy",
        season_year="2023/24",
        format_tag="T20",
        appearances=9,
        coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
        provenance_record_id=PROVENANCE_SOURCE_UUID_1,
    )
    dumped = rec.model_dump()
    assert CompetitionHistoryRecord.model_validate(dumped) == rec

    json_str = rec.model_dump_json()
    assert CompetitionHistoryRecord.model_validate_json(json_str) == rec


# =============================================================================
# 5. CareerGapRecord Tests
# =============================================================================


def test_career_gap_record_rr_suspension() -> None:
    """Verify CareerGapRecord for Rajasthan Royals 2016-2017 franchise suspension."""
    gap = build_synthetic_rr_suspension_gap(SYNTHETIC_PLAYER_UUID_PRIMARY)
    assert gap.player_id == SYNTHETIC_PLAYER_UUID_PRIMARY
    assert gap.start_season == "2016"
    assert gap.end_season == "2017"
    assert gap.gap_seasons == ["2016", "2017"]
    assert gap.gap_type == GapType.FRANCHISE_SUSPENSION
    assert gap.competition_name == "Indian Premier League"
    assert "Supreme Court" in (gap.evidence_notes or "")
    assert gap.provenance_record_id == PROVENANCE_SOURCE_UUID_1


def test_career_gap_record_injury_and_defaults() -> None:
    """Verify CareerGapRecord for individual injury with default notes/provenance."""
    pid = uuid4()
    gap = CareerGapRecord(
        player_id=pid,
        start_season="2022",
        end_season="2022",
        gap_seasons=["2022"],
        gap_type=GapType.INJURY,
        competition_name="Indian Premier League",
    )
    assert gap.player_id == pid
    assert gap.gap_type == GapType.INJURY
    assert gap.evidence_notes is None
    assert gap.provenance_record_id is None


def test_career_gap_record_all_gap_types() -> None:
    """Verify all GapType enum values instantiate correctly."""
    pid = uuid4()
    for g_type in GapType:
        gap = CareerGapRecord(
            player_id=pid,
            start_season="2020",
            end_season="2020",
            gap_seasons=["2020"],
            gap_type=g_type,
            competition_name="Tournament",
        )
        assert gap.gap_type == g_type


def test_career_gap_record_missing_required_fields_raises() -> None:
    """Verify CareerGapRecord requires player_id, start_season, end_season, gap_type, competition_name."""
    with pytest.raises(ValidationError):
        CareerGapRecord()  # type: ignore[call-arg]


def test_career_gap_record_invalid_enum_raises() -> None:
    """Verify invalid gap type raises ValidationError."""
    with pytest.raises(ValidationError):
        CareerGapRecord(
            player_id=uuid4(),
            start_season="2020",
            end_season="2020",
            gap_type="UNKNOWN_GAP_TYPE",  # type: ignore[arg-type]
            competition_name="IPL",
        )


def test_career_gap_record_extra_field_forbidden() -> None:
    """Verify extra fields are rejected."""
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CareerGapRecord(
            player_id=uuid4(),
            start_season="2020",
            end_season="2020",
            gap_type=GapType.UNEXPLAINED_GAP,
            competition_name="IPL",
            rogue_field="prohibited",  # type: ignore[call-arg]
        )


def test_career_gap_record_roundtrip_serialization() -> None:
    """Verify CareerGapRecord round-trip serialization."""
    gap = build_synthetic_career_gap(
        player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
        start_season="2021",
        end_season="2021",
        gap_seasons=["2021"],
        gap_type=GapType.NOC_DENIED,
        competition_name="Big Bash League",
        evidence_notes="Home board withheld NOC for overseas participation",
        provenance_record_id=PROVENANCE_SOURCE_UUID_2,
    )
    dumped = gap.model_dump()
    assert CareerGapRecord.model_validate(dumped) == gap

    json_str = gap.model_dump_json()
    assert CareerGapRecord.model_validate_json(json_str) == gap


# =============================================================================
# 6. CareerDataCoverage Tests
# =============================================================================


def test_career_data_coverage_valid_instantiation() -> None:
    """Verify CareerDataCoverage with full nested records and summary."""
    coverage = build_synthetic_career_data_coverage(
        canonical_player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
        the_hundred_deferred=True,
    )
    assert coverage.canonical_player_id == SYNTHETIC_PLAYER_UUID_PRIMARY
    assert coverage.competitions_evaluated_count == 4
    assert len(coverage.competitions_covered) == 4
    assert len(coverage.career_gaps) == 1
    assert coverage.the_hundred_appearances_deferred is True
    assert coverage.coverage_summary[CoverageStatus.VERIFIED_PARTICIPATION] == 3
    assert coverage.coverage_summary[CoverageStatus.DATASET_UNAVAILABLE] == 1


def test_career_data_coverage_string_key_coercion_in_summary() -> None:
    """Verify string keys in coverage_summary dict are coerced to CoverageStatus enums."""
    raw_summary: Any = {
        "VERIFIED_PARTICIPATION": 1,
        "DATASET_UNAVAILABLE": 1,
    }
    coverage = CareerDataCoverage(
        canonical_player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
        competitions_evaluated_count=2,
        coverage_summary=raw_summary,
    )
    assert CoverageStatus.VERIFIED_PARTICIPATION in coverage.coverage_summary
    assert coverage.coverage_summary[CoverageStatus.VERIFIED_PARTICIPATION] == 1


def test_career_data_coverage_negative_evaluation_count_forbidden() -> None:
    """Verify competitions_evaluated_count cannot be negative."""
    with pytest.raises(ValidationError):
        CareerDataCoverage(
            canonical_player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            competitions_evaluated_count=-1,
        )


def test_career_data_coverage_missing_canonical_player_id_raises() -> None:
    """Verify canonical_player_id is required."""
    with pytest.raises(ValidationError):
        CareerDataCoverage()  # type: ignore[call-arg]


def test_career_data_coverage_extra_field_forbidden() -> None:
    """Verify extra fields are rejected."""
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CareerDataCoverage(
            canonical_player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            unauthorized_summary={"test": 1},  # type: ignore[call-arg]
        )


def test_career_data_coverage_validate_assignment() -> None:
    """Verify assignment validation on CareerDataCoverage fields."""
    coverage = build_synthetic_career_data_coverage()
    coverage.the_hundred_appearances_deferred = False
    assert coverage.the_hundred_appearances_deferred is False

    with pytest.raises(ValidationError):
        coverage.competitions_evaluated_count = -3


def test_career_data_coverage_roundtrip_serialization() -> None:
    """Verify CareerDataCoverage round-trip serialization."""
    coverage = build_synthetic_career_data_coverage()
    dumped = coverage.model_dump()
    assert CareerDataCoverage.model_validate(dumped) == coverage

    json_str = coverage.model_dump_json()
    assert CareerDataCoverage.model_validate_json(json_str) == coverage


# =============================================================================
# 7. CDCREOutputContract Tests
# =============================================================================


def test_cdcre_output_contract_defaults() -> None:
    """Verify CDCREOutputContract instantiation with default None/empty fields."""
    output = CDCREOutputContract()
    assert output.candidate_discovery is None
    assert output.career_coverage is None
    assert output.metadata == {}


def test_cdcre_output_contract_full_instantiation() -> None:
    """Verify CDCREOutputContract with candidate discovery, career coverage, and metadata."""
    cand_discovery = build_synthetic_candidate_discovery()
    career_coverage = build_synthetic_career_data_coverage()
    metadata: dict[str, Any] = {
        "engine": "CDCRE",
        "pipeline_phase": "Phase 4A",
        "execution_worker": 1,
        "active_tournaments_count": 13,
    }
    output = CDCREOutputContract(
        candidate_discovery=cand_discovery,
        career_coverage=career_coverage,
        metadata=metadata,
    )
    assert output.candidate_discovery == cand_discovery
    assert output.career_coverage == career_coverage
    assert output.metadata["pipeline_phase"] == "Phase 4A"
    assert output.metadata["active_tournaments_count"] == 13


def test_cdcre_output_contract_extra_field_forbidden() -> None:
    """Verify extra fields are forbidden on CDCREOutputContract."""
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CDCREOutputContract(
            extra_payload="unsupported",  # type: ignore[call-arg]
        )


def test_cdcre_output_contract_roundtrip_serialization() -> None:
    """Verify CDCREOutputContract round-trip serialization."""
    output = build_synthetic_cdcre_output()
    dumped = output.model_dump()
    assert CDCREOutputContract.model_validate(dumped) == output

    json_str = output.model_dump_json()
    assert CDCREOutputContract.model_validate_json(json_str) == output


# =============================================================================
# 8. Structural & Architecture Compliance Tests
# =============================================================================


@pytest.mark.parametrize(
    "model_cls",
    [
        CandidatePlayerRecord,
        CandidateDiscoveryResult,
        CompetitionHistoryRecord,
        CareerGapRecord,
        CareerDataCoverage,
        CDCREOutputContract,
    ],
)
def test_all_cdcre_contracts_inherit_base_contract(model_cls: type[BaseContract]) -> None:
    """Verify every CDCRE contract model inherits from BaseContract."""
    assert issubclass(model_cls, BaseContract)
    assert model_cls.model_config.get("extra") == "forbid"
    assert model_cls.model_config.get("validate_assignment") is True
    assert model_cls.model_config.get("from_attributes") is True


def test_cdcre_module_all_exports() -> None:
    """Verify __all__ contains exactly the nine required domain types."""
    import src.contracts.cdcre as cdcre_mod

    expected_exports = {
        "AmbiguityStatus",
        "CoverageStatus",
        "GapType",
        "CandidatePlayerRecord",
        "CandidateDiscoveryResult",
        "CompetitionHistoryRecord",
        "CareerGapRecord",
        "CareerDataCoverage",
        "CDCREOutputContract",
    }
    assert set(cdcre_mod.__all__) == expected_exports
    for export_name in expected_exports:
        assert hasattr(cdcre_mod, export_name)


# =============================================================================
# 9. Pytest Fixture Smoke Tests
# =============================================================================


def test_sample_fixtures_instantiation(
    sample_candidate_record: CandidatePlayerRecord,
    sample_candidate_discovery_result: CandidateDiscoveryResult,
    sample_collision_discovery_result: CandidateDiscoveryResult,
    sample_competition_history_record: CompetitionHistoryRecord,
    sample_hundred_history_record: CompetitionHistoryRecord,
    sample_unavailable_dataset_record: CompetitionHistoryRecord,
    sample_career_gap_record: CareerGapRecord,
    sample_rr_suspension_gap_record: CareerGapRecord,
    sample_career_data_coverage: CareerDataCoverage,
    sample_cdcre_output_contract: CDCREOutputContract,
) -> None:
    """Verify all declared pytest fixtures instantiate valid domain models."""
    assert isinstance(sample_candidate_record, CandidatePlayerRecord)
    assert isinstance(sample_candidate_discovery_result, CandidateDiscoveryResult)
    assert isinstance(sample_collision_discovery_result, CandidateDiscoveryResult)
    assert isinstance(sample_competition_history_record, CompetitionHistoryRecord)
    assert isinstance(sample_hundred_history_record, CompetitionHistoryRecord)
    assert isinstance(sample_unavailable_dataset_record, CompetitionHistoryRecord)
    assert isinstance(sample_career_gap_record, CareerGapRecord)
    assert isinstance(sample_rr_suspension_gap_record, CareerGapRecord)
    assert isinstance(sample_career_data_coverage, CareerDataCoverage)
    assert isinstance(sample_cdcre_output_contract, CDCREOutputContract)
