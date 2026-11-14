"""Unit tests for CDCRE Four-State Coverage Evaluator (Requirement R4, AC-11).

Validates:
1. Four-State Coverage Model (VERIFIED_PARTICIPATION, DATASET_UNAVAILABLE, NOT_ESTABLISHED, CONFIRMED_NON_PARTICIPATION).
2. Mandatory AC-11 Invariant: missing datasets emit DATASET_UNAVAILABLE with appearances = None (never 0).
3. Complete datasets with appearances > 0 emit VERIFIED_PARTICIPATION.
4. Complete datasets with appearances == 0 emit CONFIRMED_NON_PARTICIPATION.
5. Ambiguous or uncorroborated cases emit NOT_ESTABLISHED.
6. enrich_career_coverage accurately integrates missing datasets and updates summary counts.
7. Contract compliance: extra='forbid', validate_assignment=True, serialization roundtrip.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.cdcre.coverage_evaluator import (
    CoverageEvaluator,
    enrich_career_coverage,
    evaluate_competition_coverage,
    evaluate_coverage,
)
from src.contracts.cdcre import (
    CareerDataCoverage,
    CompetitionHistoryRecord,
    CoverageStatus,
)

from tests.fixtures.cdcre_contract_fixtures import (
    IPL_COMPETITION_UUID,
    SYNTHETIC_PLAYER_UUID_PRIMARY,
    build_synthetic_competition_history,
)


class TestFourStateCoverageModel:
    """Test the authoritative 4-state coverage model mapping."""

    def test_verified_participation_state(self) -> None:
        """Verified appearances > 0 with complete dataset yields VERIFIED_PARTICIPATION."""
        status = evaluate_coverage(has_dataset=True, appearances=1)
        assert status == CoverageStatus.VERIFIED_PARTICIPATION

        status_multi = evaluate_coverage(has_dataset=True, appearances=14)
        assert status_multi == CoverageStatus.VERIFIED_PARTICIPATION

        # Positional arguments: (has_dataset, appearances)
        status_pos = evaluate_coverage(True, 10)
        assert status_pos == CoverageStatus.VERIFIED_PARTICIPATION

        # 4-argument positional: (competition_id, season_year, has_dataset, appearances)
        status_4arg = evaluate_coverage(IPL_COMPETITION_UUID, "2024", True, 7)
        assert status_4arg == CoverageStatus.VERIFIED_PARTICIPATION

    def test_dataset_unavailable_state(self) -> None:
        """Missing dataset produces DATASET_UNAVAILABLE adhering to AC-11."""
        status = evaluate_coverage(has_dataset=False, appearances=None)
        assert status == CoverageStatus.DATASET_UNAVAILABLE

        # Even if appearances is mistakenly passed as 0 with missing dataset, status MUST be DATASET_UNAVAILABLE
        status_with_zero = evaluate_coverage(has_dataset=False, appearances=0)
        assert status_with_zero == CoverageStatus.DATASET_UNAVAILABLE

        # Positional arguments
        status_pos = evaluate_coverage(False, None)
        assert status_pos == CoverageStatus.DATASET_UNAVAILABLE

        # 4-argument positional
        status_4arg = evaluate_coverage(IPL_COMPETITION_UUID, "2018", False, None)
        assert status_4arg == CoverageStatus.DATASET_UNAVAILABLE

    def test_not_established_state(self) -> None:
        """Dataset exists but appearances is None or ambiguous yields NOT_ESTABLISHED."""
        # Dataset exists but appearances unknown/None
        status_none = evaluate_coverage(has_dataset=True, appearances=None)
        assert status_none == CoverageStatus.NOT_ESTABLISHED

        # Ambiguous flag overrides
        status_ambig = evaluate_coverage(has_dataset=True, appearances=5, ambiguous=True)
        assert status_ambig == CoverageStatus.NOT_ESTABLISHED

        # Positional arguments
        status_pos = evaluate_coverage(True, None)
        assert status_pos == CoverageStatus.NOT_ESTABLISHED

    def test_confirmed_non_participation_state(self) -> None:
        """Dataset exists and complete with 0 verified appearances yields CONFIRMED_NON_PARTICIPATION."""
        status = evaluate_coverage(has_dataset=True, appearances=0)
        assert status == CoverageStatus.CONFIRMED_NON_PARTICIPATION

        # Bench / squad member confirmed 0 appearances
        status_squad = evaluate_coverage(has_dataset=True, appearances=0, squad_member=True)
        assert status_squad == CoverageStatus.CONFIRMED_NON_PARTICIPATION

        # Positional arguments
        status_pos = evaluate_coverage(True, 0)
        assert status_pos == CoverageStatus.CONFIRMED_NON_PARTICIPATION

        # 4-argument positional
        status_4arg = evaluate_coverage(IPL_COMPETITION_UUID, "2024", True, 0)
        assert status_4arg == CoverageStatus.CONFIRMED_NON_PARTICIPATION

    def test_negative_appearances_raises_error(self) -> None:
        """Negative appearance counts must raise ValueError."""
        with pytest.raises(ValueError, match="appearances must be non-negative"):
            evaluate_coverage(has_dataset=True, appearances=-1)


class TestAC11Compliance:
    """Rigorous verification of mandatory AC-11 invariant."""

    def test_missing_dataset_forces_appearances_none(self) -> None:
        """MANDATORY AC-11: missing dataset MUST have appearances = None, NEVER appearances = 0."""
        # Attempt to pass appearances = 0 with has_dataset = False
        record = evaluate_competition_coverage(
            competition_id=IPL_COMPETITION_UUID,
            competition_name="Indian Premier League",
            season_year="2018",
            has_dataset=False,
            appearances=0,  # Hostile input violating AC-11
        )
        assert record.coverage_status == CoverageStatus.DATASET_UNAVAILABLE
        assert record.appearances is None  # AC-11 strictly enforced
        assert record.appearances != 0  # NEVER 0

    def test_complete_dataset_zero_appearances_preserved(self) -> None:
        """When dataset exists, appearances = 0 is preserved as CONFIRMED_NON_PARTICIPATION."""
        record = evaluate_competition_coverage(
            competition_id=IPL_COMPETITION_UUID,
            competition_name="Indian Premier League",
            season_year="2024",
            has_dataset=True,
            appearances=0,
            squad_member=True,
        )
        assert record.coverage_status == CoverageStatus.CONFIRMED_NON_PARTICIPATION
        assert record.appearances == 0

    def test_complete_dataset_positive_appearances_preserved(self) -> None:
        """When dataset exists, appearances > 0 is preserved as VERIFIED_PARTICIPATION."""
        record = evaluate_competition_coverage(
            competition_id=IPL_COMPETITION_UUID,
            competition_name="Indian Premier League",
            season_year="2024",
            has_dataset=True,
            appearances=14,
        )
        assert record.coverage_status == CoverageStatus.VERIFIED_PARTICIPATION
        assert record.appearances == 14

    def test_ambiguous_participation_yields_not_established(self) -> None:
        """Ambiguous flag results in NOT_ESTABLISHED."""
        record = evaluate_competition_coverage(
            competition_id=IPL_COMPETITION_UUID,
            competition_name="Indian Premier League",
            season_year="2024",
            has_dataset=True,
            appearances=5,
            ambiguous=True,
        )
        assert record.coverage_status == CoverageStatus.NOT_ESTABLISHED

    def test_the_hundred_format_semantics(self) -> None:
        """The Hundred automatically resolves to 5 balls per over and 100-ball format."""
        hundred_id = uuid4()
        record = evaluate_competition_coverage(
            competition_id=hundred_id,
            competition_name="The Hundred Men's Competition",
            season_year="2023",
            has_dataset=True,
            appearances=8,
        )
        assert record.balls_per_over == 5
        assert record.format_tag == "100-ball"
        assert record.coverage_status == CoverageStatus.VERIFIED_PARTICIPATION

    def test_invalid_competition_id_raises_type_error(self) -> None:
        """Passing non-UUID invalid object raises TypeError."""
        with pytest.raises(TypeError, match="competition_id must be a UUID instance"):
            evaluate_competition_coverage(
                competition_id="invalid-not-a-uuid",  # type: ignore[arg-type]
                competition_name="IPL",
                season_year="2024",
                has_dataset=True,
                appearances=5,
            )


class TestEnrichCareerCoverage:
    """Test enrich_career_coverage functionality and AC-11 compliance."""

    def test_enrich_updates_summary_counts(self) -> None:
        """Enriching recalculates summary counts across all 4 states."""
        r1 = build_synthetic_competition_history(
            competition_name="Indian Premier League",
            season_year="2024",
            appearances=14,
            coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
        )
        r2 = build_synthetic_competition_history(
            competition_name="Syed Mushtaq Ali Trophy",
            season_year="2023/24",
            appearances=0,
            coverage_status=CoverageStatus.CONFIRMED_NON_PARTICIPATION,
        )

        initial_coverage = CareerDataCoverage(
            canonical_player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            competitions_evaluated_count=2,
            competitions_covered=[r1, r2],
            coverage_summary={
                CoverageStatus.VERIFIED_PARTICIPATION: 999,  # Stale count
            },
        )

        enriched = enrich_career_coverage(initial_coverage)

        assert enriched.competitions_evaluated_count == 2
        assert enriched.coverage_summary[CoverageStatus.VERIFIED_PARTICIPATION] == 1
        assert enriched.coverage_summary[CoverageStatus.CONFIRMED_NON_PARTICIPATION] == 1
        assert enriched.coverage_summary[CoverageStatus.DATASET_UNAVAILABLE] == 0
        assert enriched.coverage_summary[CoverageStatus.NOT_ESTABLISHED] == 0

    def test_enrich_integrates_missing_dataset_records_ac11(self) -> None:
        """Integrating known competitions with missing datasets strictly sets appearances = None."""
        r1 = build_synthetic_competition_history(
            competition_name="Indian Premier League",
            season_year="2024",
            appearances=14,
            coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
        )

        initial_coverage = CareerDataCoverage(
            canonical_player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            competitions_evaluated_count=1,
            competitions_covered=[r1],
            coverage_summary={CoverageStatus.VERIFIED_PARTICIPATION: 1},
        )

        bpl_spec = {
            "competition_id": uuid4(),
            "competition_name": "Bangladesh Premier League",
            "season_year": "2018",
            "has_dataset": False,
            "appearances": 0,  # Deliberately attempt 0 appearances
        }

        enriched = enrich_career_coverage(initial_coverage, known_competitions=[bpl_spec])

        assert enriched.competitions_evaluated_count == 2
        assert enriched.coverage_summary[CoverageStatus.VERIFIED_PARTICIPATION] == 1
        assert enriched.coverage_summary[CoverageStatus.DATASET_UNAVAILABLE] == 1

        bpl_record = next(r for r in enriched.competitions_covered if "Bangladesh" in r.competition_name)
        assert bpl_record.coverage_status == CoverageStatus.DATASET_UNAVAILABLE
        assert bpl_record.appearances is None  # AC-11 compliance

    def test_enrich_cleanses_existing_record_with_illegal_zero_appearances(self) -> None:
        """If an existing record had DATASET_UNAVAILABLE and appearances != None, it is cleansed."""
        # Synthesize a faulty record where appearances was 0
        faulty_rec = CompetitionHistoryRecord(
            competition_id=IPL_COMPETITION_UUID,
            competition_name="Faulty Dataset League",
            season_year="2020",
            format_tag="T20",
            appearances=0,
            coverage_status=CoverageStatus.DATASET_UNAVAILABLE,
            balls_per_over=6,
        )

        coverage = CareerDataCoverage(
            canonical_player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            competitions_evaluated_count=1,
            competitions_covered=[faulty_rec],
            coverage_summary={CoverageStatus.DATASET_UNAVAILABLE: 1},
        )

        enriched = enrich_career_coverage(coverage)
        cleansed_rec = enriched.competitions_covered[0]
        assert cleansed_rec.coverage_status == CoverageStatus.DATASET_UNAVAILABLE
        assert cleansed_rec.appearances is None  # Enforced None per AC-11

    def test_enrich_detects_the_hundred_appearances(self) -> None:
        """Enriching correctly sets the_hundred_appearances_deferred."""
        rec_hundred = CompetitionHistoryRecord(
            competition_id=uuid4(),
            competition_name="The Hundred Men's Competition",
            season_year="2023",
            format_tag="100-ball",
            appearances=8,
            coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
            balls_per_over=5,
        )

        coverage = CareerDataCoverage(
            canonical_player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            competitions_evaluated_count=1,
            competitions_covered=[rec_hundred],
            the_hundred_appearances_deferred=False,  # Incorrect initially
        )

        enriched = enrich_career_coverage(coverage)
        assert enriched.the_hundred_appearances_deferred is True


class TestCoverageEvaluatorClass:
    """Test CoverageEvaluator OOP class wrapper methods."""

    def test_evaluator_methods(self) -> None:
        """Evaluator instance provides evaluate, evaluate_competition, and enrich methods."""
        evaluator = CoverageEvaluator()

        status = evaluator.evaluate(has_dataset=True, appearances=5)
        assert status == CoverageStatus.VERIFIED_PARTICIPATION

        record = evaluator.evaluate_competition(
            competition_id=IPL_COMPETITION_UUID,
            competition_name="Indian Premier League",
            season_year="2024",
            has_dataset=False,
            appearances=None,
        )
        assert record.coverage_status == CoverageStatus.DATASET_UNAVAILABLE
        assert record.appearances is None

        cov = CareerDataCoverage(
            canonical_player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            competitions_covered=[record],
        )
        enriched = evaluator.enrich(cov)
        assert enriched.coverage_summary[CoverageStatus.DATASET_UNAVAILABLE] == 1


class TestPydanticContractInvariants:
    """Test Pydantic v2 BaseContract compliance."""

    def test_forbids_extra_fields(self) -> None:
        """CompetitionHistoryRecord strictly forbids extra fields."""
        with pytest.raises(ValidationError):
            CompetitionHistoryRecord(  # type: ignore[call-arg]
                competition_id=IPL_COMPETITION_UUID,
                competition_name="IPL",
                season_year="2024",
                format_tag="T20",
                appearances=14,
                coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
                balls_per_over=6,
                unauthorized_extra_field="rejected",
            )

    def test_validate_assignment(self) -> None:
        """Mutation triggers runtime validation."""
        record = build_synthetic_competition_history()
        with pytest.raises(ValidationError):
            record.appearances = -5  # Negative appearances rejected
