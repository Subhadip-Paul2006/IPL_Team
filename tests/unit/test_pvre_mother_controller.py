"""Unit tests for PVRE Mother Controller (7-Step Deterministic Waterfall).

Validates TRD §9.1, §9.2, PRD FR-PV1, and AI_INSTRUCTIONS R13, R15, R18:
- Step 1: Pre-identity discovery & PIRE resolution.
- Step 2: Ambiguity / collision check (COLLISION_MULTIPLE_IDENTITIES -> ROUTED_SAFETY_REVIEW).
- Step 3: TMVE relationship check (CURRENT_RR, HISTORICAL_RR_APPEARED, HISTORICAL_RR_SQUAD_ONLY -> ROUTED_RR_INCUMBENT / Mode A).
- Step 4: Senior international cap check (CAPPED & no RR relationship -> ROUTED_OUT_OF_SCOPE).
- Step 5: Eligibility Policy Service validation (UNCAPPED & verified eligible -> ROUTED_UNCAPPED_CANDIDATE / Mode B).
- Step 6: Unknown/unassessed player -> ROUTED_SAFETY_REVIEW (UNKNOWN_PLAYER_NOT_IN_DATABASE, negative proof invariant).
- Step 7: Missing / conflicting data -> ROUTED_SAFETY_REVIEW.
- Precedence ordering and zero uncapped inference guardrail.
- 26-field PVREOutputContract compilation and data quality summary.
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from src.contracts.pvre import (
    PlayerCappedStatus,
    PlayerResearchRequest,
    PVREOutputContract,
    PVRERequestContract,
    PVREReviewStatus,
    ResearchMode,
    ReviewDossierContract,
    RouteStatus,
)
from src.pvre.controller import MotherController
from src.pvre.safety_review import SafetyReviewReasonCode

from tests.fixtures.pvre_contract_fixtures import (
    SYNTHETIC_PLAYER_ID_SANJU,
    SYNTHETIC_RESEARCH_RUN_ID,
    SYNTHETIC_TARGET_SEASON_ID,
    build_mode_a_incumbent_request,
    build_mode_b_uncapped_request,
    build_out_of_scope_request,
    build_pvre_request,
)


@pytest.fixture
def controller() -> MotherController:
    """Fixture providing an initialized MotherController instance."""
    return MotherController()


# =============================================================================
# Step 1: Pre-Identity Discovery & PIRE Resolution Tests
# =============================================================================


def test_waterfall_step_1_unresolved_identity_routes_to_safety_review(
    controller: MotherController,
) -> None:
    """Step 1: Unresolved identity from PIRE routes to ROUTED_SAFETY_REVIEW."""
    req = build_pvre_request(
        identity_status="UNRESOLVED",
        player_id=None,
        canonical_name="Unknown Prospect Query",
    )
    route_status, research_mode, reasons, dossier = controller.classify_and_route(
        req, context={"candidate_count": 0}
    )

    assert route_status == RouteStatus.ROUTED_SAFETY_REVIEW
    assert research_mode == ResearchMode.REVIEW_REQUIRED
    assert SafetyReviewReasonCode.IDENTITY_AMBIGUITY.value in reasons
    assert dossier is not None
    assert dossier.review_status == PVREReviewStatus.REVIEW_REQUIRED.value
    assert len(dossier.unresolved_claims) > 0


def test_waterfall_step_1_resolved_identity_proceeds(
    controller: MotherController,
) -> None:
    """Step 1: Resolved identity proceeds through the waterfall without halting."""
    req = build_mode_a_incumbent_request()
    route_status, research_mode, _, _ = controller.classify_and_route(req)

    # Sanju Samson (CURRENT_RR) proceeds to Mode A at Step 3
    assert route_status == RouteStatus.ROUTED_RR_INCUMBENT
    assert research_mode == ResearchMode.MODE_A


# =============================================================================
# Step 2: Ambiguity / Collision Check Tests
# =============================================================================


def test_waterfall_step_2_identity_collision_routes_to_safety_review(
    controller: MotherController,
) -> None:
    """Step 2: Multiple candidate entities (candidate_count > 1) halt with COLLISION."""
    req = build_pvre_request(canonical_name="Amit Sharma")
    route_status, research_mode, reasons, dossier = controller.classify_and_route(
        req, context={"candidate_count": 2}
    )

    assert route_status == RouteStatus.ROUTED_SAFETY_REVIEW
    assert research_mode == ResearchMode.REVIEW_REQUIRED
    assert SafetyReviewReasonCode.COLLISION_MULTIPLE_IDENTITIES.value in reasons
    assert dossier is not None
    assert SafetyReviewReasonCode.COLLISION_MULTIPLE_IDENTITIES.value in dossier.review_reason_codes


def test_waterfall_step_2_provisional_identity_triggers_collision(
    controller: MotherController,
) -> None:
    """Step 2: Provisional identity status halts with COLLISION_MULTIPLE_IDENTITIES."""
    req = build_pvre_request(identity_status="PROVISIONAL")
    route_status, research_mode, reasons, dossier = controller.classify_and_route(req)

    assert route_status == RouteStatus.ROUTED_SAFETY_REVIEW
    assert research_mode == ResearchMode.REVIEW_REQUIRED
    assert SafetyReviewReasonCode.COLLISION_MULTIPLE_IDENTITIES.value in reasons
    assert dossier is not None


# =============================================================================
# Step 3: TMVE Relationship Check Tests (Mode A)
# =============================================================================


def test_waterfall_step_3_current_rr_routes_to_mode_a(
    controller: MotherController,
) -> None:
    """Step 3: CURRENT_RR relationship deterministically routes to Mode A."""
    req = build_mode_a_incumbent_request()
    route_status, research_mode, reasons, dossier = controller.classify_and_route(req)

    assert route_status == RouteStatus.ROUTED_RR_INCUMBENT
    assert research_mode == ResearchMode.MODE_A
    assert len(reasons) == 0
    assert dossier is None


def test_waterfall_step_3_historical_rr_appeared_routes_to_mode_a(
    controller: MotherController,
) -> None:
    """Step 3: HISTORICAL_RR_APPEARED alumni route to Mode A."""
    req = build_pvre_request(
        rr_relationship_state="HISTORICAL_RR_APPEARED",
        rr_current_state="NOT_CURRENT",
    )
    route_status, research_mode, reasons, _ = controller.classify_and_route(req)

    assert route_status == RouteStatus.ROUTED_RR_INCUMBENT
    assert research_mode == ResearchMode.MODE_A
    assert len(reasons) == 0


def test_waterfall_step_3_historical_rr_squad_only_routes_to_mode_a(
    controller: MotherController,
) -> None:
    """Step 3: HISTORICAL_RR_SQUAD_ONLY alumni route to Mode A."""
    req = build_pvre_request(
        rr_relationship_state="HISTORICAL_RR_SQUAD_ONLY",
        rr_current_state="NOT_CURRENT",
    )
    route_status, research_mode, reasons, _ = controller.classify_and_route(req)

    assert route_status == RouteStatus.ROUTED_RR_INCUMBENT
    assert research_mode == ResearchMode.MODE_A
    assert len(reasons) == 0


def test_waterfall_step_3_contradictory_rr_membership_routes_to_safety_review(
    controller: MotherController,
) -> None:
    """Step 3: Claimed NO_VERIFIED_RR_RELATIONSHIP but squad records exist triggers CONFLICT."""
    req = build_pvre_request(
        rr_relationship_state="NO_VERIFIED_RR_RELATIONSHIP",
        rr_current_state="NOT_CURRENT",
    )
    route_status, research_mode, reasons, dossier = controller.classify_and_route(
        req, context={"has_squad_inclusion": True}
    )

    assert route_status == RouteStatus.ROUTED_SAFETY_REVIEW
    assert research_mode == ResearchMode.REVIEW_REQUIRED
    assert SafetyReviewReasonCode.CONFLICT_RR_MEMBERSHIP.value in reasons
    assert dossier is not None


# =============================================================================
# Step 4: Senior International Cap Check Tests (Out of Scope)
# =============================================================================


def test_waterfall_step_4_capped_non_rr_routes_to_out_of_scope(
    controller: MotherController,
) -> None:
    """Step 4: Capped player with no RR relationship routes to ROUTED_OUT_OF_SCOPE."""
    req = build_out_of_scope_request()  # Virat Kohli
    route_status, research_mode, reasons, dossier = controller.classify_and_route(req)

    assert route_status == RouteStatus.ROUTED_OUT_OF_SCOPE
    assert research_mode == ResearchMode.OUT_OF_SCOPE
    assert len(reasons) == 0
    assert dossier is None


def test_waterfall_step_4_blocks_capped_player_from_entering_mode_b(
    controller: MotherController,
) -> None:
    """Step 4: Guarantees capped players are NEVER routed to Mode B."""
    req = build_pvre_request(
        player_capped_status=PlayerCappedStatus.CAPPED.value,
        ipl_uncapped_eligibility="VERIFIED_NOT_ELIGIBLE",
        rr_relationship_state="NO_VERIFIED_RR_RELATIONSHIP",
        rr_current_state="NOT_CURRENT",
    )
    route_status, research_mode, _, _ = controller.classify_and_route(req)

    assert route_status == RouteStatus.ROUTED_OUT_OF_SCOPE
    assert research_mode == ResearchMode.OUT_OF_SCOPE


# =============================================================================
# Step 5: Eligibility Policy Service Validation Tests (Mode B)
# =============================================================================


def test_waterfall_step_5_verified_uncapped_candidate_routes_to_mode_b(
    controller: MotherController,
) -> None:
    """Step 5: Verified uncapped and eligible candidate routes to Mode B."""
    req = build_mode_b_uncapped_request()
    route_status, research_mode, reasons, dossier = controller.classify_and_route(
        req, context={"in_database": True, "policy_verified": True}
    )

    assert route_status == RouteStatus.ROUTED_UNCAPPED_CANDIDATE
    assert research_mode == ResearchMode.MODE_B
    assert len(reasons) == 0
    assert dossier is None


# =============================================================================
# Step 6: Unknown / Unassessed Player Guardrail Tests (AI_INSTRUCTIONS R13)
# =============================================================================


def test_waterfall_step_6_unknown_player_database_absence_routes_to_safety_review(
    controller: MotherController,
) -> None:
    """Step 6: Unknown player absent from DB routes to ROUTED_SAFETY_REVIEW."""
    req = build_pvre_request(
        player_id=None,
        canonical_name="Newly Registered U-19 Prospect",
        player_capped_status=PlayerCappedStatus.UNVERIFIED.value,
        ipl_uncapped_eligibility="NOT_ASSESSED",
        rr_relationship_state="NO_VERIFIED_RR_RELATIONSHIP",
        rr_current_state="NOT_CURRENT",
    )
    route_status, research_mode, reasons, dossier = controller.classify_and_route(
        req, context={"in_database": False}
    )

    assert route_status == RouteStatus.ROUTED_SAFETY_REVIEW
    assert research_mode == ResearchMode.REVIEW_REQUIRED
    assert SafetyReviewReasonCode.UNKNOWN_PLAYER_NOT_IN_DATABASE.value in reasons
    assert dossier is not None


def test_waterfall_step_6_negative_proof_invariant_never_infers_uncapped(
    controller: MotherController,
) -> None:
    """Step 6 (R13): Database absence must NEVER be treated as proof of uncapped status."""
    req = build_pvre_request(
        player_id=None,
        canonical_name="Unindexed Youth Bowler",
        player_capped_status=PlayerCappedStatus.UNVERIFIED.value,
        ipl_uncapped_eligibility="NOT_ASSESSED",
        rr_relationship_state="NO_VERIFIED_RR_RELATIONSHIP",
        rr_current_state="NOT_CURRENT",
    )
    route_status, research_mode, reasons, _ = controller.classify_and_route(
        req, context={"in_database": False}
    )

    assert route_status != RouteStatus.ROUTED_UNCAPPED_CANDIDATE
    assert route_status == RouteStatus.ROUTED_SAFETY_REVIEW
    assert research_mode == ResearchMode.REVIEW_REQUIRED
    assert SafetyReviewReasonCode.UNKNOWN_PLAYER_NOT_IN_DATABASE.value in reasons


def test_waterfall_step_6_unassessed_eligibility_policy_routes_to_safety_review(
    controller: MotherController,
) -> None:
    """Step 6: Known player in DB but NOT_ASSESSED eligibility triggers UNVERIFIED_ELIGIBILITY."""
    req = build_pvre_request(
        player_id=uuid4(),
        canonical_name="Domestic Player With Unassessed Policy",
        player_capped_status=PlayerCappedStatus.UNCAPPED.value,
        ipl_uncapped_eligibility="NOT_ASSESSED",
        rr_relationship_state="NO_VERIFIED_RR_RELATIONSHIP",
        rr_current_state="NOT_CURRENT",
    )
    route_status, research_mode, reasons, dossier = controller.classify_and_route(
        req, context={"in_database": True}
    )

    assert route_status == RouteStatus.ROUTED_SAFETY_REVIEW
    assert research_mode == ResearchMode.REVIEW_REQUIRED
    assert SafetyReviewReasonCode.UNVERIFIED_ELIGIBILITY_POLICY.value in reasons
    assert dossier is not None


# =============================================================================
# Step 7: Missing / Conflicting Data & Safety Interceptor Tests
# =============================================================================


def test_waterfall_step_7_dob_conflict_routes_to_safety_review(
    controller: MotherController,
) -> None:
    """Step 7: Competing DOB assertions route to ROUTED_SAFETY_REVIEW."""
    req = build_pvre_request(
        canonical_name="Young Prospect",
        player_capped_status=PlayerCappedStatus.UNCAPPED.value,
        ipl_uncapped_eligibility="VERIFIED_ELIGIBLE",
        rr_relationship_state="NO_VERIFIED_RR_RELATIONSHIP",
        rr_current_state="NOT_CURRENT",
    )
    route_status, research_mode, reasons, dossier = controller.classify_and_route(
        req,
        context={
            "in_database": True,
            "primary_dob": "2004-05-10",
            "conflicting_dob": "2003-11-22",
            "primary_dob_source": "S18A",
            "conflicting_dob_source": "S20A",
        },
    )

    assert route_status == RouteStatus.ROUTED_SAFETY_REVIEW
    assert research_mode == ResearchMode.REVIEW_REQUIRED
    assert SafetyReviewReasonCode.CONFLICT_DOB_RECORD.value in reasons
    assert dossier is not None
    assert len(dossier.conflicting_source_ids) >= 2


def test_waterfall_step_7_statistical_discrepancy_routes_to_safety_review(
    controller: MotherController,
) -> None:
    """Step 7: External source statistical discrepancies route to ROUTED_SAFETY_REVIEW."""
    req = build_mode_b_uncapped_request()
    route_status, research_mode, reasons, dossier = controller.classify_and_route(
        req,
        context={
            "in_database": True,
            "stat_discrepancy_metric": "MATCHES",
            "stat_val_a": 35,
            "stat_val_b": 32,
            "stat_src_a": "S20A",
            "stat_src_b": "S18B",
        },
    )

    assert route_status == RouteStatus.ROUTED_SAFETY_REVIEW
    assert research_mode == ResearchMode.REVIEW_REQUIRED
    assert SafetyReviewReasonCode.CONFLICTING_CAREER_STATISTICS.value in reasons
    assert dossier is not None


# =============================================================================
# Full Execution & 26-Field Contract Compilation Tests
# =============================================================================


def test_execute_mode_a_produces_valid_26_field_output(
    controller: MotherController,
) -> None:
    """Test full execute() produces a valid 26-field contract for Mode A."""
    req = build_mode_a_incumbent_request()
    output = controller.execute(req)

    assert isinstance(output, PVREOutputContract)
    assert output.contract_version == "PVRE-2.2.0"
    assert output.research_run_id == req.research_run_id
    assert output.canonical_name == req.canonical_name
    assert output.route_status == RouteStatus.ROUTED_RR_INCUMBENT.value
    assert output.research_mode == ResearchMode.MODE_A.value
    assert output.review_status == PVREReviewStatus.CLEAR.value

    # Research Window Validation
    assert output.research_window_start <= output.research_window_end

    # Profile Integrity: Mode A has RR profile and replaceability, Mode B is None
    assert output.rr_historical_profile is not None
    assert output.recent_global_performance is not None
    assert output.replaceability_assessment is not None
    assert output.complete_career_profile is None


def test_execute_mode_b_produces_valid_26_field_output(
    controller: MotherController,
) -> None:
    """Test full execute() produces a valid 26-field contract for Mode B."""
    req = build_mode_b_uncapped_request()
    output = controller.execute(req, context={"in_database": True, "policy_verified": True})

    assert isinstance(output, PVREOutputContract)
    assert output.route_status == RouteStatus.ROUTED_UNCAPPED_CANDIDATE.value
    assert output.research_mode == ResearchMode.MODE_B.value
    assert output.review_status == PVREReviewStatus.CLEAR.value

    # Profile Integrity: Mode B has complete career profile, Mode A is None
    assert output.complete_career_profile is not None
    assert output.rr_historical_profile is None
    assert output.replaceability_assessment is None


def test_execute_out_of_scope_produces_valid_output(
    controller: MotherController,
) -> None:
    """Test full execute() produces a valid contract for Out of Scope requests."""
    req = build_out_of_scope_request()
    output = controller.execute(req)

    assert isinstance(output, PVREOutputContract)
    assert output.route_status == RouteStatus.ROUTED_OUT_OF_SCOPE.value
    assert output.research_mode == ResearchMode.OUT_OF_SCOPE.value
    assert output.review_status == PVREReviewStatus.CLEAR.value
    assert output.rr_historical_profile is None
    assert output.complete_career_profile is None
    assert output.replaceability_assessment is None
    assert "out_of_scope_reason" in output.data_quality_summary


def test_execute_safety_review_produces_valid_output_and_dossier(
    controller: MotherController,
) -> None:
    """Test full execute() produces a valid contract and dossier for safety reviews."""
    req = build_pvre_request(canonical_name="Amit Sharma")
    output = controller.execute(req, context={"candidate_count": 2})
    output = controller.execute(req, context={"candidate_count": 2})

    assert isinstance(output, PVREOutputContract)
    assert output.route_status == RouteStatus.ROUTED_SAFETY_REVIEW.value
    assert output.research_mode == ResearchMode.REVIEW_REQUIRED.value
    assert output.review_status == PVREReviewStatus.REVIEW_REQUIRED.value
    assert SafetyReviewReasonCode.COLLISION_MULTIPLE_IDENTITIES.value in output.review_reason_codes
    assert controller.last_dossier is not None
    assert isinstance(controller.last_dossier, ReviewDossierContract)


def test_normalize_request_accepts_player_research_request(
    controller: MotherController,
) -> None:
    """Test normalize_request converts PlayerResearchRequest to PVRERequestContract."""
    pr_req = PlayerResearchRequest(
        research_run_id=SYNTHETIC_RESEARCH_RUN_ID,
        player_query="Sanju Samson",
        player_id=SYNTHETIC_PLAYER_ID_SANJU,
        canonical_name="Sanju Samson",
        identity_status="RESOLVED",
        rr_relationship_state="CURRENT_RR",
        rr_current_state="CURRENT",
        player_capped_status="CAPPED",
        ipl_uncapped_eligibility="VERIFIED_NOT_ELIGIBLE",
        target_season_id=SYNTHETIC_TARGET_SEASON_ID,
        evaluation_date=date(2025, 3, 1),
        research_window_years=3,
        metadata={"requester": "franchise_lead"},
    )
    pvre_req = controller.normalize_request(pr_req)

    assert isinstance(pvre_req, PVRERequestContract)
    assert pvre_req.canonical_name == "Sanju Samson"
    assert pvre_req.research_run_id == SYNTHETIC_RESEARCH_RUN_ID


def test_normalize_request_accepts_dictionary(
    controller: MotherController,
) -> None:
    """Test normalize_request converts valid dictionary to PVRERequestContract."""
    req_dict = {
        "research_run_id": SYNTHETIC_RESEARCH_RUN_ID,
        "player_query": "Sanju Samson",
        "player_id": SYNTHETIC_PLAYER_ID_SANJU,
        "canonical_name": "Sanju Samson",
        "identity_status": "RESOLVED",
        "rr_relationship_state": "CURRENT_RR",
        "rr_current_state": "CURRENT",
        "player_capped_status": "CAPPED",
        "ipl_uncapped_eligibility": "VERIFIED_NOT_ELIGIBLE",
        "target_season_id": SYNTHETIC_TARGET_SEASON_ID,
        "evaluation_date": date(2025, 3, 1),
        "research_window_years": 3,
    }
    pvre_req = controller.normalize_request(req_dict)

    assert isinstance(pvre_req, PVRERequestContract)
    assert pvre_req.player_query == "Sanju Samson"
