"""Unit and integration tests for Mother Intelligence Engine (MIE) Master Orchestrator.

Validates the strict 7-engine deterministic waterfall:
PIRE -> TMVE -> CDCRE -> CPPAE -> CMIE -> SICE -> PVRE
across all PRD user workflows, safety review gating, and adapter failure isolation.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID, uuid4

from src.contracts.pvre import PlayerCappedStatus, RouteStatus
from src.contracts.tmve import (
    EligibilityStatus,
    RRCurrentState,
    RRRelationshipState,
)
from src.mie.contracts import (
    EngineName,
    ExecutionState,
    OverallVerificationStatus,
)
from src.mie.orchestrator import MotherIntelligenceEngine


def test_mie_orchestrator_initialization_and_health_check() -> None:
    """Verify all seven engine adapters are properly initialized and report healthy."""
    mie = MotherIntelligenceEngine()
    health = mie.health_check()
    assert health["service"] == "mother_intelligence_engine"
    assert health["status"] == "HEALTHY"
    assert len(health["adapters"]) == 7
    for eng in (
        EngineName.PIRE.value,
        EngineName.TMVE.value,
        EngineName.CDCRE.value,
        EngineName.CPPAE.value,
        EngineName.CMIE.value,
        EngineName.SICE.value,
        EngineName.PVRE.value,
    ):
        assert eng in health["adapters"]


def test_mie_orchestration_verified_rr_incumbent() -> None:
    """Test full orchestration workflow for a verified RR incumbent player (Sanju Samson proxy)."""
    mie = MotherIntelligenceEngine()
    player_id = UUID("33333333-3333-3333-3333-333333333333")

    # Register player in PIRE
    mie.pire.resolver.register_player(
        canonical_player_id=str(player_id),
        canonical_name="Sanju Samson",
        source_id="organizer_pack",
        teams={"Rajasthan Royals", "RR"},
        competitions={"IPL"},
    )

    # Register appearances in TMVE
    mie.tmve.tmve.register_squad_record(
        player_id,
        {
            "contract_type": "Retained",
            "role": "Captain",
            "is_active_squad": True,
            "start_date": date(2021, 1, 1),
            "end_date": date(2026, 12, 31),
        },
    )
    mie.tmve.tmve.register_appearances(player_id, 140)

    # Execute MIE request
    report = mie.request_player_intelligence(
        query="Sanju Samson",
        evaluation_date=date(2026, 11, 14),
    )

    # Assertions on pipeline
    assert report.canonical_name == "Sanju Samson"
    assert report.player_id == player_id
    assert report.verification.identity_status == "RESOLVED"
    assert report.verification.rr_relationship_state == RRRelationshipState.HISTORICAL_RR_APPEARANCE
    assert report.verification.rr_current_state == RRCurrentState.CURRENT
    assert report.is_rr_incumbent is True
    assert report.total_execution_time_ms > 0.0

    # Engine executions verified
    assert EngineName.PIRE.value in report.engine_executions
    assert EngineName.TMVE.value in report.engine_executions
    assert EngineName.CDCRE.value in report.engine_executions
    assert EngineName.CPPAE.value in report.engine_executions
    assert EngineName.CMIE.value in report.engine_executions
    assert EngineName.PVRE.value in report.engine_executions


def test_mie_orchestration_squad_only_reserve_zero_stats() -> None:
    """Test reserve squad player with 0 match appearances retains 0 appearances (Rule P1)."""
    mie = MotherIntelligenceEngine()
    player_id = UUID("44444444-4444-4444-4444-444444444444")

    mie.pire.resolver.register_player(
        canonical_player_id=str(player_id),
        canonical_name="Shubham Dubey",
        teams={"Rajasthan Royals"},
    )
    mie.tmve.tmve.register_squad_record(
        player_id,
        {
            "contract_type": "Auction Buy",
            "role": "Reserve",
            "is_active_squad": False,
        },
    )
    mie.tmve.tmve.register_appearances(player_id, 0)

    report = mie.request_player_intelligence(
        query="Shubham Dubey",
        evaluation_date=date(2026, 11, 14),
    )

    assert report.verification.rr_relationship_state == RRRelationshipState.HISTORICAL_RR_SQUAD_ONLY
    assert getattr(report.membership, "verified_rr_appearances", 0) == 0


def test_mie_orchestration_eligibility_does_not_infer_uncapped_status() -> None:
    """Verified IPL eligibility alone is not evidence that the player is uncapped."""
    mie = MotherIntelligenceEngine()
    player_id = UUID("55555555-5555-5555-5555-555555555555")

    mie.pire.resolver.register_player(
        canonical_player_id=str(player_id),
        canonical_name="Priyansh Arya",
        teams={"Delhi", "South Delhi Superstars"},
        competitions={"SMAT", "DPL"},
    )

    # Register negative verification in TMVE
    mie.tmve.tmve.register_negative_evaluation(
        player_id,
        {
            # Synthetic evidence fixture satisfying all seven TRD §4.5 gates.
            "career_years": [2019, 2020, 2021, 2022, 2023],
            "squad_coverage": dict.fromkeys(range(2019, 2024), True),
            "scorecard_coverage": dict.fromkeys(range(2019, 2024), True),
            "has_tier1_2_source": True,
            "human_reviewed": True,
            "has_conflicts": False,
        },
    )

    # Register 2027 eligibility policy and player eligibility
    policy = mie.tmve.eligibility_service.register_policy(
        season_id=UUID("11111111-2222-3333-4444-555555555555"),
        policy_version=1,
        effective_date=date(2026, 1, 1),
        rule_source="BCCI IPL 2027 Player Regulations Clause 4",
        verified=True,
        verification_id=uuid4(),
    )
    mie.tmve.eligibility_service.record_player_eligibility(
        player_id=player_id,
        policy_id=policy.policy_id,
        status=EligibilityStatus.VERIFIED_ELIGIBLE,
        verified=True,
        verification_id=uuid4(),
    )

    report = mie.request_player_intelligence(
        query="Priyansh Arya",
        target_season_id=UUID("11111111-2222-3333-4444-555555555555"),
        evaluation_date=date(2026, 11, 14),
    )

    assert (
        report.verification.rr_relationship_state == RRRelationshipState.NO_VERIFIED_RR_RELATIONSHIP
    )
    assert report.verification.ipl_uncapped_eligibility == EligibilityStatus.VERIFIED_ELIGIBLE
    assert report.verification.player_capped_status == PlayerCappedStatus.UNVERIFIED
    assert report.is_uncapped_eligible is False
    assert report.pvre.route_status in (
        RouteStatus.ROUTED_UNCAPPED_CANDIDATE.value,
        RouteStatus.ROUTED_SAFETY_REVIEW.value,
    )


def test_mie_orchestration_unknown_player_database_absence() -> None:
    """Rule R13: Database absence is never proof of uncapped status; routes to REVIEW_REQUIRED."""
    mie = MotherIntelligenceEngine()

    report = mie.request_player_intelligence(
        query="Completely Unknown Prospect 2027",
        evaluation_date=date(2026, 11, 14),
    )

    assert report.is_review_required is True
    assert report.verification.overall_status in (
        OverallVerificationStatus.REVIEW_REQUIRED,
        OverallVerificationStatus.UNVERIFIED,
    )
    assert report.safety_dossier is not None
    assert "IDENTITY_UNRESOLVED" in report.safety_dossier.review_reason_codes


def test_mie_orchestration_adapter_failure_isolation() -> None:
    """Verify that a failure in one adapter is isolated and does not abort orchestration."""
    mie = MotherIntelligenceEngine()

    # Simulate an error inside CMIE adapter
    class CrashingCMIEAdapter(mie.cmie.__class__):
        def is_available(self) -> bool:
            return True

        def execute(self, *args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("Simulated Open-Meteo Gateway Timeout 504")

    mie.cmie = CrashingCMIEAdapter(cmie_engine=None)
    player_id = uuid4()
    mie.pire.resolver.register_player(
        canonical_player_id=str(player_id), canonical_name="Virat Kohli"
    )

    report = mie.request_player_intelligence("Virat Kohli")

    # The pipeline should complete gracefully
    assert report is not None
    assert EngineName.CMIE.value in report.engine_executions
    cmie_rec = report.engine_executions[EngineName.CMIE.value]
    assert cmie_rec.state == ExecutionState.FAILED
    assert "RuntimeError" in (cmie_rec.error_message or "")
    assert "Simulated Open-Meteo Gateway Timeout 504" not in (cmie_rec.error_message or "")
    # PIRE and TMVE still succeeded
    assert report.engine_executions[EngineName.PIRE.value].state == ExecutionState.SUCCESS
