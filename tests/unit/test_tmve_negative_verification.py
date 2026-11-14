"""Unit test suite for TRD §4.5 Negative Verification Protocol in TMVE.

Author: Agent E (Tests, Security and Integration Specialist)
Milestone: M5

Tests all 7 mandatory gates:
1. Historical coverage scope across covered seasons (2008-2015, 2018-2026)
2. Career window overlap with active RR competition years
3. Squad-list coverage consulted and complete for overlapping career years
4. Scorecard coverage consulted and complete for overlapping career years
5. Tier 1 or Tier 2 official source cited
6. Conflict-free evidence (zero contradictory records)
7. Human review completed and verified

Verifies:
- Failing ANY single condition results in RR_RELATIONSHIP_UNKNOWN (never negative).
- Passing ALL 7 conditions results in NO_VERIFIED_RR_RELATIONSHIP.
- Absent players from incomplete bases yield RR_RELATIONSHIP_UNKNOWN.
- Combinatorial failure modes and boundary conditions.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from src.contracts.tmve import (
    RRRelationshipState,
    TMVEOutputContract,
)
from src.membership.tmve import (
    RR_ACTIVE_SEASONS,
    RR_SUSPENDED_SEASONS,
    TeamMembershipVerificationEngine,
)

from tests.fixtures.tmve_fixtures import (
    create_incomplete_base_player,
    create_verified_non_rr_player,
)


@pytest.fixture
def tmve_engine() -> TeamMembershipVerificationEngine:
    """Fixture providing a fresh TeamMembershipVerificationEngine instance."""
    return TeamMembershipVerificationEngine()


@pytest.fixture
def baseline_coverage_maps() -> tuple[dict[int, bool], dict[int, bool]]:
    """Return complete squad and scorecard coverage across all RR active seasons."""
    squad_cov = dict.fromkeys(RR_ACTIVE_SEASONS, True)
    scorecard_cov = dict.fromkeys(RR_ACTIVE_SEASONS, True)
    return squad_cov, scorecard_cov


# ==============================================================================
# Tier 1 & 2: Individual Gate Audit Tests (Isolation of All 7 Conditions)
# ==============================================================================


class TestNegativeVerificationIndividualGates:
    """Systematically audit all 7 conditions of TRD §4.5 in isolation."""

    def test_gate_all_seven_pass_yields_no_verified_rr_relationship(
        self,
        tmve_engine: TeamMembershipVerificationEngine,
        baseline_coverage_maps: tuple[dict[int, bool], dict[int, bool]],
    ) -> None:
        """When all 7 conditions are satisfied, return NO_VERIFIED_RR_RELATIONSHIP."""
        p_id = uuid4()
        squad_cov, scorecard_cov = baseline_coverage_maps
        career_years = [2021, 2022, 2023, 2024, 2025]

        met, state, reasons = tmve_engine.evaluate_negative_verification(
            player_id=p_id,
            career_years=career_years,
            squad_coverage=squad_cov,
            scorecard_coverage=scorecard_cov,
            has_tier1_2_source=True,
            human_reviewed=True,
            has_conflicts=False,
        )

        assert met is True
        assert state == RRRelationshipState.NO_VERIFIED_RR_RELATIONSHIP
        assert "NEGATIVE_PROTOCOL_PASSED" in reasons
        assert len(reasons) == 1

    def test_gate_1_fails_empty_historical_scope(
        self,
        tmve_engine: TeamMembershipVerificationEngine,
    ) -> None:
        """Condition 1 Failure: empty historical scope maps yield RR_RELATIONSHIP_UNKNOWN."""
        p_id = uuid4()
        career_years = [2022, 2023]

        # Empty squad coverage
        met, state, reasons = tmve_engine.evaluate_negative_verification(
            player_id=p_id,
            career_years=career_years,
            squad_coverage={},  # Missing scope
            scorecard_coverage={2022: True, 2023: True},
            has_tier1_2_source=True,
            human_reviewed=True,
            has_conflicts=False,
        )

        assert met is False
        assert state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
        assert "MISSING_HISTORICAL_SCOPE" in reasons

    def test_gate_2_fails_no_career_window_overlap_with_active_rr_years(
        self,
        tmve_engine: TeamMembershipVerificationEngine,
        baseline_coverage_maps: tuple[dict[int, bool], dict[int, bool]],
    ) -> None:
        """Condition 2 Failure: career years outside RR active window yield UNKNOWN."""
        p_id = uuid4()
        squad_cov, scorecard_cov = baseline_coverage_maps

        # Active ONLY during 2016-2017 (suspension seasons where RR was not participating)
        suspension_career = sorted(RR_SUSPENDED_SEASONS)
        met, state, reasons = tmve_engine.evaluate_negative_verification(
            player_id=p_id,
            career_years=suspension_career,
            squad_coverage=squad_cov,
            scorecard_coverage=scorecard_cov,
            has_tier1_2_source=True,
            human_reviewed=True,
            has_conflicts=False,
        )

        assert met is False
        assert state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
        assert "NO_CAREER_WINDOW_OVERLAP" in reasons

    def test_gate_2_fails_empty_career_years(
        self,
        tmve_engine: TeamMembershipVerificationEngine,
        baseline_coverage_maps: tuple[dict[int, bool], dict[int, bool]],
    ) -> None:
        """Condition 2 Failure: empty career window yields NO_CAREER_WINDOW_OVERLAP."""
        p_id = uuid4()
        squad_cov, scorecard_cov = baseline_coverage_maps

        met, state, reasons = tmve_engine.evaluate_negative_verification(
            player_id=p_id,
            career_years=[],
            squad_coverage=squad_cov,
            scorecard_coverage=scorecard_cov,
            has_tier1_2_source=True,
            human_reviewed=True,
            has_conflicts=False,
        )

        assert met is False
        assert state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
        assert "NO_CAREER_WINDOW_OVERLAP" in reasons

    def test_gate_3_fails_incomplete_squad_coverage_for_overlapping_season(
        self,
        tmve_engine: TeamMembershipVerificationEngine,
    ) -> None:
        """Condition 3 Failure: missing squad list for an active career year yields UNKNOWN."""
        p_id = uuid4()
        career_years = [2021, 2022, 2023]
        squad_cov = {2021: True, 2022: False, 2023: True}  # 2022 missing!
        scorecard_cov = {2021: True, 2022: True, 2023: True}

        met, state, reasons = tmve_engine.evaluate_negative_verification(
            player_id=p_id,
            career_years=career_years,
            squad_coverage=squad_cov,
            scorecard_coverage=scorecard_cov,
            has_tier1_2_source=True,
            human_reviewed=True,
            has_conflicts=False,
        )

        assert met is False
        assert state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
        assert "INCOMPLETE_SQUAD_COVERAGE" in reasons

    def test_gate_4_fails_incomplete_scorecard_coverage_for_overlapping_season(
        self,
        tmve_engine: TeamMembershipVerificationEngine,
    ) -> None:
        """Condition 4 Failure: missing scorecard coverage for an active year yields UNKNOWN."""
        p_id = uuid4()
        career_years = [2023, 2024]
        squad_cov = {2023: True, 2024: True}
        scorecard_cov = {2023: True, 2024: False}  # 2024 scorecard missing!

        met, state, reasons = tmve_engine.evaluate_negative_verification(
            player_id=p_id,
            career_years=career_years,
            squad_coverage=squad_cov,
            scorecard_coverage=scorecard_cov,
            has_tier1_2_source=True,
            human_reviewed=True,
            has_conflicts=False,
        )

        assert met is False
        assert state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
        assert "INCOMPLETE_SCORECARD_COVERAGE" in reasons

    def test_gate_5_fails_lacks_tier_1_or_2_source(
        self,
        tmve_engine: TeamMembershipVerificationEngine,
        baseline_coverage_maps: tuple[dict[int, bool], dict[int, bool]],
    ) -> None:
        """Condition 5 Failure: only tier-3 or lower sources consulted yields UNKNOWN."""
        p_id = uuid4()
        squad_cov, scorecard_cov = baseline_coverage_maps
        career_years = [2022, 2023, 2024]

        met, state, reasons = tmve_engine.evaluate_negative_verification(
            player_id=p_id,
            career_years=career_years,
            squad_coverage=squad_cov,
            scorecard_coverage=scorecard_cov,
            has_tier1_2_source=False,  # No Tier 1/2 source!
            human_reviewed=True,
            has_conflicts=False,
        )

        assert met is False
        assert state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
        assert "LACKS_TIER1_OR_TIER2_SOURCE" in reasons

    def test_gate_6_fails_conflicting_evidence_detected(
        self,
        tmve_engine: TeamMembershipVerificationEngine,
        baseline_coverage_maps: tuple[dict[int, bool], dict[int, bool]],
    ) -> None:
        """Condition 6 Failure: any single contradicting claim yields UNKNOWN."""
        p_id = uuid4()
        squad_cov, scorecard_cov = baseline_coverage_maps
        career_years = [2021, 2022, 2023]

        met, state, reasons = tmve_engine.evaluate_negative_verification(
            player_id=p_id,
            career_years=career_years,
            squad_coverage=squad_cov,
            scorecard_coverage=scorecard_cov,
            has_tier1_2_source=True,
            human_reviewed=True,
            has_conflicts=True,  # Conflict flag present!
        )

        assert met is False
        assert state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
        assert "CONFLICTING_RECORDS_DETECTED" in reasons

    def test_gate_7_fails_human_review_not_completed(
        self,
        tmve_engine: TeamMembershipVerificationEngine,
        baseline_coverage_maps: tuple[dict[int, bool], dict[int, bool]],
    ) -> None:
        """Condition 7 Failure: negative claim without human signoff yields UNKNOWN."""
        p_id = uuid4()
        squad_cov, scorecard_cov = baseline_coverage_maps
        career_years = [2022, 2023]

        met, state, reasons = tmve_engine.evaluate_negative_verification(
            player_id=p_id,
            career_years=career_years,
            squad_coverage=squad_cov,
            scorecard_coverage=scorecard_cov,
            has_tier1_2_source=True,
            human_reviewed=False,  # Human review pending!
            has_conflicts=False,
        )

        assert met is False
        assert state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
        assert "HUMAN_REVIEW_NOT_COMPLETED" in reasons


# ==============================================================================
# Tier 3: Combinatorial & Multiple Gate Failure Analysis
# ==============================================================================


class TestNegativeVerificationCombinatorialFailures:
    """Verify that multiple simultaneous gate failures are properly aggregated."""

    def test_all_seven_gates_failing_simultaneously(
        self,
        tmve_engine: TeamMembershipVerificationEngine,
    ) -> None:
        """When every single condition fails, all failure reasons must be captured."""
        p_id = uuid4()

        met, state, reasons = tmve_engine.evaluate_negative_verification(
            player_id=p_id,
            career_years=[2016, 2017],  # No active overlap (Gate 2)
            squad_coverage={},  # Missing scope (Gate 1)
            scorecard_coverage={},  # Missing scope (Gate 1)
            has_tier1_2_source=False,  # Gate 5
            human_reviewed=False,  # Gate 7
            has_conflicts=True,  # Gate 6
        )

        assert met is False
        assert state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
        assert "MISSING_HISTORICAL_SCOPE" in reasons
        assert "NO_CAREER_WINDOW_OVERLAP" in reasons
        assert "LACKS_TIER1_OR_TIER2_SOURCE" in reasons
        assert "CONFLICTING_RECORDS_DETECTED" in reasons
        assert "HUMAN_REVIEW_NOT_COMPLETED" in reasons

    def test_incomplete_squad_and_unreviewed_combination(
        self,
        tmve_engine: TeamMembershipVerificationEngine,
    ) -> None:
        """Pairwise: Condition 3 (squad) + Condition 7 (human review) failing."""
        p_id = uuid4()
        career_years = [2023, 2024]
        squad_cov = {2023: False, 2024: True}
        scorecard_cov = {2023: True, 2024: True}

        met, state, reasons = tmve_engine.evaluate_negative_verification(
            player_id=p_id,
            career_years=career_years,
            squad_coverage=squad_cov,
            scorecard_coverage=scorecard_cov,
            has_tier1_2_source=True,
            human_reviewed=False,
            has_conflicts=False,
        )

        assert met is False
        assert state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
        assert "INCOMPLETE_SQUAD_COVERAGE" in reasons
        assert "HUMAN_REVIEW_NOT_COMPLETED" in reasons

    def test_conflicts_and_low_tier_source_combination(
        self,
        tmve_engine: TeamMembershipVerificationEngine,
        baseline_coverage_maps: tuple[dict[int, bool], dict[int, bool]],
    ) -> None:
        """Pairwise: Condition 5 (source tier) + Condition 6 (conflicts) failing."""
        p_id = uuid4()
        squad_cov, scorecard_cov = baseline_coverage_maps
        career_years = [2024]

        met, state, reasons = tmve_engine.evaluate_negative_verification(
            player_id=p_id,
            career_years=career_years,
            squad_coverage=squad_cov,
            scorecard_coverage=scorecard_cov,
            has_tier1_2_source=False,
            human_reviewed=True,
            has_conflicts=True,
        )

        assert met is False
        assert state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
        assert "LACKS_TIER1_OR_TIER2_SOURCE" in reasons
        assert "CONFLICTING_RECORDS_DETECTED" in reasons


# ==============================================================================
# Incomplete Base & Absence Invariants (TRD §4.3 & §4.5)
# ==============================================================================


class TestNegativeVerificationIncompleteBases:
    """Verify that absent players from incomplete bases yield RR_RELATIONSHIP_UNKNOWN."""

    def test_absent_player_from_incomplete_base_yields_unknown(
        self,
        tmve_engine: TeamMembershipVerificationEngine,
    ) -> None:
        """Mandatory Invariant: Absence from an incomplete database NEVER implies non-membership."""
        player_data = create_incomplete_base_player()
        p_id = player_data["player_id"]

        # Player has 0 squad records, 0 appearances, but record base is incomplete
        state = tmve_engine.resolve_relationship_state(
            player_id=p_id,
            verified_appearances=0,
            squad_records=[],
            history_records=[],
        )

        assert state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN

    def test_synthetic_verified_non_rr_player_fixture_integration(
        self,
        tmve_engine: TeamMembershipVerificationEngine,
        baseline_coverage_maps: tuple[dict[int, bool], dict[int, bool]],
    ) -> None:
        """Verify that synthetic non-RR player fixture satisfies all 7 conditions."""
        fixture_data = create_verified_non_rr_player()
        p_id = fixture_data["player_id"]
        squad_cov, scorecard_cov = baseline_coverage_maps

        met, state, reasons = tmve_engine.evaluate_negative_verification(
            player_id=p_id,
            career_years=fixture_data["career_years"],
            squad_coverage=squad_cov,
            scorecard_coverage=scorecard_cov,
            has_tier1_2_source=fixture_data["tier_1_or_2_source_cited"],
            human_reviewed=fixture_data["human_review_completed"],
            has_conflicts=not fixture_data["conflict_free"],
        )

        assert met == fixture_data["expected_negative_verification_met"]
        assert state == fixture_data["expected_relationship_state"]
        assert reasons == ["NEGATIVE_PROTOCOL_PASSED"]

    def test_output_contract_negative_verification_field_coherence(
        self,
        tmve_engine: TeamMembershipVerificationEngine,
        baseline_coverage_maps: tuple[dict[int, bool], dict[int, bool]],
    ) -> None:
        """Verify that TMVEOutputContract negative_verification_met aligns with relationship state."""
        fixture_data = create_verified_non_rr_player()
        p_id = fixture_data["player_id"]
        squad_cov, scorecard_cov = baseline_coverage_maps

        # Pre-register negative evaluation
        tmve_engine.register_negative_evaluation(
            player_id=p_id,
            eval_data={
                "career_years": fixture_data["career_years"],
                "squad_coverage": squad_cov,
                "scorecard_coverage": scorecard_cov,
                "has_tier1_2_source": True,
                "human_reviewed": True,
                "has_conflicts": False,
            },
        )

        contract: TMVEOutputContract = tmve_engine.verify_player_membership(
            player_id=p_id,
            as_of_date=fixture_data["player"].created_at.date(),
        )

        assert contract.rr_relationship_state == RRRelationshipState.NO_VERIFIED_RR_RELATIONSHIP
        assert contract.negative_verification_met is True
        assert contract.verified_rr_appearances == 0
        assert contract.review_status == "CLEAR"
