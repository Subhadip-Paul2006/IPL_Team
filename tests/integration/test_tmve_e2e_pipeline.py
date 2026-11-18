"""End-to-End multi-agent integration pipeline test suite for TMVE (Milestone M5).

Author: Agent E (Tests, Security and Integration Specialist)
Target: TRD §2.3, §4.3, §4.4, §4.5, §11 (Tier 4 Real-World Application Scenarios)

Executes all 7 authoritative application scenarios:
- Scenario 1: Historical RR match player (Sanju Samson proxy) -> appearances >= 1, HISTORICAL_RR_APPEARANCE.
- Scenario 2: Squad-only reserve player -> 0 appearances, HISTORICAL_RR_SQUAD_ONLY, no invented stats.
- Scenario 3: Player absent from incomplete record base -> RR_RELATIONSHIP_UNKNOWN (never negative).
- Scenario 4: Non-RR player satisfying all 7 TRD §4.5 conditions -> NO_VERIFIED_RR_RELATIONSHIP.
- Scenario 5: Ambiguous / conflicting squad claims -> routes to ReviewDossierContract (REVIEW_REQUIRED).
- Scenario 6: Unassessed player for 2027 season -> NOT_ASSESSED, policy version bound.
- Scenario 7: Full multi-agent pipeline PIRE -> TMVE -> Eligibility -> Provenance/Review -> MIE composition.
"""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID, uuid4

from src.contracts.competition import SquadMembership
from src.contracts.tmve import (
    EligibilityOutputContract,
    EligibilityStatus,
    ReviewDossierContract,
    RRCurrentState,
    RRRelationshipState,
    TMVEOutputContract,
    TMVERequestContract,
)
from src.membership.eligibility_service import EligibilityPolicyService
from src.membership.participation import (
    CANONICAL_RR_TEAM_ID,
    FranchiseParticipationService,
)
from src.membership.provenance_review import (
    ProvenanceReviewService,
    ReviewReasonCode,
)
from src.membership.tmve import (
    RR_ACTIVE_SEASONS,
    TeamMembershipVerificationEngine,
)
from src.pire.models import IdentityStatus
from src.pire.resolver import UnifiedPIRE

from tests.fixtures.tmve_fixtures import (
    RR_TEAM_ID,
    build_synthetic_verification_record,
    create_contradictory_evidence_player,
    create_incomplete_base_player,
    create_squad_only_reserve_player,
    create_unassessed_player_for_2027,
    create_verified_non_rr_player,
    create_verified_rr_match_player,
)

# ==============================================================================
# Scenario 1: Historical RR Match Player (Sanju Samson Proxy)
# ==============================================================================


class TestScenario1HistoricalRRMatchPlayer:
    """Scenario 1: Verified Historical RR match player with verified appearances >= 1."""

    def test_sanju_samson_resolves_to_historical_rr_appearance(self) -> None:
        """A player with confirmed match appearances must resolve to HISTORICAL_RR_APPEARANCE."""
        fixture_data = create_verified_rr_match_player(
            canonical_name="Sanju Samson",
            appearances=138,
            seasons=["2013", "2014", "2015", "2018", "2019", "2020", "2021", "2022", "2023", "2024"],
        )
        p_id = fixture_data["player_id"]

        tmve = TeamMembershipVerificationEngine()
        tmve.register_rr_team_id(RR_TEAM_ID)
        tmve.register_rr_team_id(CANONICAL_RR_TEAM_ID)

        for squad_rec in fixture_data["squad_records"]:
            tmve.register_squad_record(p_id, squad_rec)
        for hist_rec in fixture_data["history_records"]:
            tmve.register_history_record(p_id, hist_rec)
        tmve.register_appearances(p_id, fixture_data["total_appearances"])

        # Execute membership verification
        req = TMVERequestContract(player_id=p_id, as_of_date=date(2024, 4, 1))
        output: TMVEOutputContract = tmve.verify_player_membership(
            player_id=req.player_id,
            as_of_date=req.as_of_date,
        )

        assert output.rr_relationship_state == RRRelationshipState.HISTORICAL_RR_APPEARANCE
        assert output.verified_rr_appearances == 138
        assert output.verified_rr_appearances >= 1
        assert output.rr_current_state == RRCurrentState.CURRENT
        assert output.negative_verification_met is False
        assert output.review_status == "CLEAR"
        assert len(output.rr_seasons) == 10


# ==============================================================================
# Scenario 2: Historical Squad-Only Reserve Player (Zero Appearances)
# ==============================================================================


class TestScenario2SquadOnlyReservePlayer:
    """Scenario 2: Squad-only player (0 appearances, zero invented match statistics)."""

    def test_squad_only_reserve_retains_zero_appearances(self) -> None:
        """A roster member with 0 match appearances MUST be HISTORICAL_RR_SQUAD_ONLY with 0 caps."""
        fixture_data = create_squad_only_reserve_player(
            canonical_name="Synthetic Reserve Player",
            squad_seasons=["2021", "2022"],
        )
        p_id = fixture_data["player_id"]

        tmve = TeamMembershipVerificationEngine()
        tmve.register_rr_team_id(RR_TEAM_ID)
        tmve.register_rr_team_id(CANONICAL_RR_TEAM_ID)

        for squad_rec in fixture_data["squad_records"]:
            tmve.register_squad_record(p_id, squad_rec)
        for hist_rec in fixture_data["history_records"]:
            tmve.register_history_record(p_id, hist_rec)
        tmve.register_appearances(p_id, 0)

        req = TMVERequestContract(player_id=p_id, as_of_date=date(2024, 1, 1))
        output: TMVEOutputContract = tmve.verify_player_membership(
            player_id=req.player_id,
            as_of_date=req.as_of_date,
        )

        assert output.rr_relationship_state == RRRelationshipState.HISTORICAL_RR_SQUAD_ONLY
        # MANDATORY INTEGRITY GUARDRAIL: verified appearances must be strictly 0, NEVER None or fabricated
        assert output.verified_rr_appearances == 0
        assert output.rr_current_state == RRCurrentState.NOT_CURRENT
        assert output.negative_verification_met is False
        assert output.review_status == "CLEAR"


# ==============================================================================
# Scenario 3: Player Absent from Incomplete Record Base
# ==============================================================================


class TestScenario3IncompleteRecordBasePlayer:
    """Scenario 3: Player absent from incomplete record base (yields RR_RELATIONSHIP_UNKNOWN)."""

    def test_incomplete_base_player_defaults_strictly_to_unknown(self) -> None:
        """Absence from an incomplete record base MUST NEVER be inferred as negative membership."""
        fixture_data = create_incomplete_base_player(
            canonical_name="Synthetic Absent Prospect",
        )
        p_id = fixture_data["player_id"]

        tmve = TeamMembershipVerificationEngine()
        # Empty registrations (unassessed / absent from database)

        output: TMVEOutputContract = tmve.verify_player_membership(
            player_id=p_id,
            as_of_date=date(2024, 5, 1),
        )

        assert output.rr_relationship_state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
        assert output.rr_current_state == RRCurrentState.UNKNOWN
        assert output.negative_verification_met is False


# ==============================================================================
# Scenario 4: Non-RR Player Satisfying All 7 TRD §4.5 Conditions
# ==============================================================================


class TestScenario4VerifiedNonRRPlayer:
    """Scenario 4: Fully verified non-RR player meeting all 7 negative-verification requirements."""

    def test_verified_non_rr_player_satisfies_all_seven_gates(self) -> None:
        """When all 7 conditions are satisfied, return NO_VERIFIED_RR_RELATIONSHIP."""
        fixture_data = create_verified_non_rr_player(
            canonical_name="Synthetic Domestic Non-RR Prospect",
            career_years=[2021, 2022, 2023, 2024, 2025],
        )
        p_id = fixture_data["player_id"]

        squad_cov = dict.fromkeys(RR_ACTIVE_SEASONS, True)
        scorecard_cov = dict.fromkeys(RR_ACTIVE_SEASONS, True)

        tmve = TeamMembershipVerificationEngine()
        tmve.register_negative_evaluation(
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

        output: TMVEOutputContract = tmve.verify_player_membership(
            player_id=p_id,
            as_of_date=date(2024, 5, 1),
        )

        assert output.rr_relationship_state == RRRelationshipState.NO_VERIFIED_RR_RELATIONSHIP
        assert output.negative_verification_met is True
        assert output.verified_rr_appearances == 0
        assert output.review_status == "CLEAR"


# ==============================================================================
# Scenario 5: Ambiguous / Conflicting Squad Claim (Routes to Review Dossier)
# ==============================================================================


class TestScenario5ConflictingSquadClaim:
    """Scenario 5: Contradictory squad claims route to ReviewDossierContract (REVIEW_REQUIRED)."""

    def test_conflicting_squad_claims_generate_review_dossier(self) -> None:
        """Discrepant claims must be preserved without silent overwrite and route to human review."""
        fixture_data = create_contradictory_evidence_player(
            canonical_name="Synthetic Contradictory Player",
        )
        p_id = fixture_data["player_id"]
        claims = fixture_data["conflicting_claims"]

        prov_service = ProvenanceReviewService()
        tmve = TeamMembershipVerificationEngine()
        tmve.register_rr_team_id(RR_TEAM_ID)

        # Step 1: Preserve conflict in ProvenanceReviewService
        conflict_entry = prov_service.preserve_conflicts(
            existing_claim=claims[0],
            conflicting_claim=claims[1],
        )
        assert conflict_entry["conflict_detected"] is True
        assert conflict_entry["resolution_decision"] == "PRESERVED_FOR_HUMAN_REVIEW"

        # Step 2: Build ReviewDossierContract
        dossier: ReviewDossierContract = prov_service.build_review_dossier(
            subject_type="player_membership",
            subject_id=p_id,
            reason_codes=[ReviewReasonCode.CONFLICTING_SQUAD_LISTS],
            conflicts=[conflict_entry],
            recommended_checks=[
                "Cross-reference official franchise squad registration filings with IPL governing council",
            ],
        )

        assert dossier.review_status == "REVIEW_REQUIRED"
        assert ReviewReasonCode.CONFLICTING_SQUAD_LISTS in dossier.review_reason_codes
        assert len(dossier.unresolved_claims) == 1

        # Step 3: Register contradictory records in TMVE with conflict flag
        tmve.register_squad_record(
            p_id,
            {
                "membership_id": uuid4(),
                "team_id": RR_TEAM_ID,
                "season_id": uuid4(),
                "contract_type": "Auction Buy",
                "conflict": True,
                "verification_status": "CONFLICT",
            },
        )

        output: TMVEOutputContract = tmve.verify_player_membership(
            player_id=p_id,
            as_of_date=date(2024, 1, 1),
        )

        assert output.rr_relationship_state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
        assert output.review_status == "REVIEW_REQUIRED"
        assert "CONFLICTING_MEMBERSHIP_RECORD" in output.review_reason_codes


# ==============================================================================
# Scenario 6: Unassessed Player for 2027 Season
# ==============================================================================


class TestScenario6UnassessedPlayerFor2027:
    """Scenario 6: Unassessed player for 2027 season defaults to NOT_ASSESSED."""

    def test_unassessed_player_defaults_to_not_assessed(self) -> None:
        """A player without an independent eligibility assessment must evaluate to NOT_ASSESSED."""
        fixture_data = create_unassessed_player_for_2027()
        p_id = fixture_data["player_id"]
        season_2027_id = fixture_data["target_season_id"]

        elig_service = EligibilityPolicyService()

        # Register official 2027 policy
        policy = elig_service.register_policy(
            season_id=season_2027_id,
            policy_version=1,
            effective_date=date(2026, 11, 1),
            expiry_date=date(2027, 6, 30),
            rule_source="BCCI IPL 2027 Player Regulations §4",
            verified=True,
            verification_id=uuid4(),
        )

        # Evaluate player without prior assessment record
        eval_output: EligibilityOutputContract = elig_service.evaluate_player_eligibility(
            player_id=p_id,
            season_id=season_2027_id,
            as_of_date=date(2026, 12, 1),
        )

        assert eval_output.eligibility_status == EligibilityStatus.NOT_ASSESSED
        assert eval_output.verified is False
        assert eval_output.verification_id is None
        assert eval_output.policy_id == policy.policy_id
        assert eval_output.policy_version == 1
        assert eval_output.rule_source == "BCCI IPL 2027 Player Regulations §4"


# ==============================================================================
# Scenario 7: Full Multi-Agent Pipeline (PIRE -> TMVE -> Eligibility -> MIE)
# ==============================================================================


class TestScenario7FullPipelineE2E:
    """Scenario 7: Full multi-agent orchestration sequence (TRD §2.3) into unified MIE contract."""

    def test_full_pipeline_orchestration_flow(self) -> None:
        """Execute complete flow: PIRE -> TMVE -> Eligibility -> Review -> MIE composition."""
        # 1. PIRE: Identity Resolution
        sanju_id = uuid4()
        pire = UnifiedPIRE()
        pire.register_player(
            canonical_player_id=str(sanju_id),
            canonical_name="Sanju Samson",
            teams={"Rajasthan Royals"},
        )

        pire_res = pire.resolve("Sanju Samson", context_teams=["Rajasthan Royals"])
        assert pire_res.status == IdentityStatus.RESOLVED
        assert pire_res.player_id == str(sanju_id)
        assert pire_res.canonical_name == "Sanju Samson"
        resolved_pid: UUID = sanju_id

        # 2. Franchise Participation: Verify RR active windows & 2016-17 suspension
        part_service = FranchiseParticipationService()
        status_2015, active_2015 = part_service.is_season_participating("2015")
        status_2016, active_2016 = part_service.is_season_participating("2016")
        status_2027, active_2027 = part_service.is_season_participating("2027")

        assert status_2015 == "PARTICIPATING" and active_2015 is True
        assert status_2016 == "SUSPENDED" and active_2016 is False
        assert status_2027 == "UNKNOWN" and active_2027 is False

        # 3. TMVE: Verify RR Membership Dimensions 1 & 2
        tmve = TeamMembershipVerificationEngine()
        tmve.register_rr_team_id(CANONICAL_RR_TEAM_ID)
        s_id_2024 = uuid4()
        v_rec_tmve = build_synthetic_verification_record("player_membership", resolved_pid)

        tmve.register_squad_record(
            resolved_pid,
            SquadMembership(
                membership_id=uuid4(),
                player_id=resolved_pid,
                team_id=CANONICAL_RR_TEAM_ID,
                season_id=s_id_2024,
                contract_type="Retained",
                is_active_squad=True,
                evidence_source_id=v_rec_tmve.verification_id,
            ),
        )
        tmve.register_appearances(resolved_pid, 138)
        tmve.register_verification_record(resolved_pid, v_rec_tmve)

        as_of = date(2024, 5, 1)
        tmve_output: TMVEOutputContract = tmve.verify_player_membership(
            player_id=resolved_pid,
            as_of_date=as_of,
        )

        assert tmve_output.rr_relationship_state == RRRelationshipState.HISTORICAL_RR_APPEARANCE
        assert tmve_output.rr_current_state == RRCurrentState.CURRENT
        assert tmve_output.verified_rr_appearances == 138

        # 4. Eligibility Policy Service: Dimension 3
        elig_service = EligibilityPolicyService()
        season_2027_id = uuid4()
        policy = elig_service.register_policy(
            season_id=season_2027_id,
            policy_version=1,
            effective_date=date(2026, 11, 1),
            rule_source="BCCI IPL 2027 Regulations §4",
            verified=True,
            verification_id=uuid4(),
        )

        # Record verified capped status
        v_rec_elig = build_synthetic_verification_record("player_eligibility", resolved_pid)
        elig_service.record_player_eligibility(
            player_id=resolved_pid,
            policy_id=policy.policy_id,
            status=EligibilityStatus.VERIFIED_NOT_ELIGIBLE,  # Capped player ineligible for uncapped pool
            verified=True,
            verification_id=v_rec_elig.verification_id,
        )

        elig_output: EligibilityOutputContract = elig_service.evaluate_player_eligibility(
            player_id=resolved_pid,
            season_id=season_2027_id,
            as_of_date=date(2026, 11, 15),
        )

        assert elig_output.eligibility_status == EligibilityStatus.VERIFIED_NOT_ELIGIBLE
        assert elig_output.verified is True
        assert elig_output.verification_id == v_rec_elig.verification_id

        # 5. Provenance & Review Integration
        prov_service = ProvenanceReviewService()
        v_rec_attached = prov_service.attach_verification(
            subject_type="player_membership",
            subject_id=resolved_pid,
            evidence_tier=1,
            source_provider="BCCI Official Registry",
        )
        assert v_rec_attached.evidence_tier == 1

        # 6. MIE Composition (TRD §4.4 Option B): Verify typed composition without dimension conflation
        mie_unified_report: dict[str, Any] = {
            "canonical_player_id": str(resolved_pid),
            "canonical_name": pire_res.canonical_name,
            "membership": tmve_output,  # Dimensions 1 & 2
            "eligibility": elig_output,  # Dimension 3
            "review_dossier": None,
        }

        # Validate typed contracts within MIE payload
        assert isinstance(mie_unified_report["membership"], TMVEOutputContract)
        assert isinstance(mie_unified_report["eligibility"], EligibilityOutputContract)

        # Dimension independence assertions:
        assert mie_unified_report["membership"].rr_relationship_state == RRRelationshipState.HISTORICAL_RR_APPEARANCE
        assert mie_unified_report["membership"].rr_current_state == RRCurrentState.CURRENT
        assert mie_unified_report["eligibility"].eligibility_status == EligibilityStatus.VERIFIED_NOT_ELIGIBLE
        assert mie_unified_report["membership"].verified_rr_appearances == 138
