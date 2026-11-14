"""Unit tests for PVRE (Player Verification & Research Engine) contracts and taxonomy.

Validates model serialization, deserialization, field validation, default values,
extra-field rejection, assignment validation, explicit verification states, and
enum constraints for TRD §9.5, §9.6, PRD FR-PV1..FR-PV8, and ORIGINAL_REQUEST R1..R4.
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.contracts.base import BaseContract
from src.contracts.pvre import (
    CareerCoverageState,
    CareerVerification,
    EvidenceSource,
    EvidenceTier,
    PlayerCappedStatus,
    PlayerResearchOutput,
    PlayerResearchRequest,
    PVREOutputContract,
    PVRERequestContract,
    PVREReviewDossierContract,
    PVREReviewStatus,
    PVREVerificationStatus,
    ReplaceabilitySignal,
    ReplacementCandidateEvidence,
    ReplacementResearchRequest,
    ResearchConflict,
    ResearchCoverage,
    ResearchMode,
    RouteStatus,
    SourceReliability,
    VerificationClaim,
    VerificationStatus,
)

from tests.fixtures.pvre_contract_fixtures import (
    DEFAULT_EVALUATION_DATE,
    DEFAULT_TIMESTAMP,
    DEFAULT_WINDOW_END,
    DEFAULT_WINDOW_START,
    SYNTHETIC_CLAIM_ID,
    SYNTHETIC_CONFLICT_ID,
    SYNTHETIC_DOSSIER_ID,
    SYNTHETIC_PLAYER_ID_SANJU,
    SYNTHETIC_PLAYER_ID_UNCAPPED,
    SYNTHETIC_POLICY_ID,
    SYNTHETIC_RESEARCH_RUN_ID,
    SYNTHETIC_TARGET_SEASON_ID,
    SYNTHETIC_VERIFICATION_ID,
    build_career_verification,
    build_evidence_source,
    build_mode_a_incumbent_request,
    build_mode_a_output,
    build_mode_b_output,
    build_mode_b_uncapped_request,
    build_out_of_scope_output,
    build_out_of_scope_request,
    build_player_research_output,
    build_player_research_request,
    build_pvre_output,
    build_pvre_request,
    build_replacement_candidate_evidence,
    build_replacement_research_request,
    build_research_conflict,
    build_research_coverage,
    build_review_dossier,
    build_review_required_output,
    build_review_required_request,
    build_verification_claim,
    valid_pvre_output_dict,
    valid_pvre_request_dict,
    valid_replacement_candidate_evidence_dict,
    valid_review_dossier_dict,
)

# =============================================================================
# 1. Domain Taxonomy & Lifecycle Enum Tests
# =============================================================================


def test_research_mode_enum() -> None:
    """Verify ResearchMode contains exact 4 operational modes."""
    expected = {
        "MODE_A": "MODE_A",
        "MODE_B": "MODE_B",
        "REVIEW_REQUIRED": "REVIEW_REQUIRED",
        "OUT_OF_SCOPE": "OUT_OF_SCOPE",
    }
    assert len(ResearchMode) == len(expected)
    for name, value in expected.items():
        member = ResearchMode[name]
        assert member.value == value
        assert member == value
        assert isinstance(member, str)


def test_route_status_enum() -> None:
    """Verify RouteStatus contains exact 4 waterfall destinations."""
    expected = {
        "ROUTED_RR_INCUMBENT": "ROUTED_RR_INCUMBENT",
        "ROUTED_UNCAPPED_CANDIDATE": "ROUTED_UNCAPPED_CANDIDATE",
        "ROUTED_SAFETY_REVIEW": "ROUTED_SAFETY_REVIEW",
        "ROUTED_OUT_OF_SCOPE": "ROUTED_OUT_OF_SCOPE",
    }
    assert len(RouteStatus) == len(expected)
    for name, value in expected.items():
        member = RouteStatus[name]
        assert member.value == value
        assert member == value
        assert isinstance(member, str)


def test_replaceability_signal_enum() -> None:
    """Verify ReplaceabilitySignal contains exact 5 analytical signals."""
    expected = {
        "RETAIN_SIGNAL": "RETAIN_SIGNAL",
        "MONITOR_SIGNAL": "MONITOR_SIGNAL",
        "POTENTIALLY_REPLACEABLE": "POTENTIALLY_REPLACEABLE",
        "INSUFFICIENT_EVIDENCE": "INSUFFICIENT_EVIDENCE",
        "REVIEW_REQUIRED": "REVIEW_REQUIRED",
    }
    assert len(ReplaceabilitySignal) == len(expected)
    for name, value in expected.items():
        member = ReplaceabilitySignal[name]
        assert member.value == value
        assert member == value
        assert isinstance(member, str)


def test_career_coverage_state_enum() -> None:
    """Verify CareerCoverageState contains exact 4 coverage states."""
    expected = {
        "COMPLETE_WITHIN_VERIFIED_SOURCES": "COMPLETE_WITHIN_VERIFIED_SOURCES",
        "PARTIAL_COVERAGE": "PARTIAL_COVERAGE",
        "UNKNOWN": "UNKNOWN",
        "REVIEW_REQUIRED": "REVIEW_REQUIRED",
    }
    assert len(CareerCoverageState) == len(expected)
    for name, value in expected.items():
        member = CareerCoverageState[name]
        assert member.value == value
        assert member == value
        assert isinstance(member, str)


def test_player_capped_status_enum() -> None:
    """Verify PlayerCappedStatus contains exact 3 capped states."""
    expected = {
        "CAPPED": "CAPPED",
        "UNCAPPED": "UNCAPPED",
        "UNVERIFIED": "UNVERIFIED",
    }
    assert len(PlayerCappedStatus) == len(expected)
    for name, value in expected.items():
        member = PlayerCappedStatus[name]
        assert member.value == value
        assert member == value
        assert isinstance(member, str)


def test_pvre_verification_status_enum() -> None:
    """Verify PVREVerificationStatus contains exact 6 discrete states."""
    expected = {
        "VERIFIED": "VERIFIED",
        "UNVERIFIED": "UNVERIFIED",
        "UNKNOWN": "UNKNOWN",
        "CONFLICT": "CONFLICT",
        "NOT_COMPUTABLE": "NOT_COMPUTABLE",
        "DATASET_UNAVAILABLE": "DATASET_UNAVAILABLE",
    }
    assert len(PVREVerificationStatus) == len(expected)
    for name, value in expected.items():
        member = PVREVerificationStatus[name]
        assert member.value == value
        assert member == value
        assert isinstance(member, str)
    # Check alias
    assert VerificationStatus is PVREVerificationStatus


def test_pvre_review_status_enum() -> None:
    """Verify PVREReviewStatus contains exact 3 review states."""
    expected = {
        "CLEAR": "CLEAR",
        "REVIEW_REQUIRED": "REVIEW_REQUIRED",
        "REJECTED": "REJECTED",
    }
    assert len(PVREReviewStatus) == len(expected)
    for name, value in expected.items():
        member = PVREReviewStatus[name]
        assert member.value == value
        assert member == value
        assert isinstance(member, str)


def test_source_reliability_enum() -> None:
    """Verify SourceReliability contains exact 4 reliability tiers."""
    expected = {
        "TIER_1_OFFICIAL": "TIER_1_OFFICIAL",
        "TIER_2_COMMERCIAL_ARCHIVE": "TIER_2_COMMERCIAL_ARCHIVE",
        "TIER_3_COMMUNITY_SCRAPE": "TIER_3_COMMUNITY_SCRAPE",
        "TIER_4_MANUAL_ESTIMATE": "TIER_4_MANUAL_ESTIMATE",
    }
    assert len(SourceReliability) == len(expected)
    for name, value in expected.items():
        member = SourceReliability[name]
        assert member.value == value
        assert member == value
        assert isinstance(member, str)


def test_evidence_tier_enum() -> None:
    """Verify EvidenceTier contains exact 4 tiers."""
    expected = {
        "TIER_1_OFFICIAL": "TIER_1_OFFICIAL",
        "TIER_2_COMMERCIAL": "TIER_2_COMMERCIAL",
        "TIER_3_MEDIA": "TIER_3_MEDIA",
        "TIER_4_CROWDSOURCED": "TIER_4_CROWDSOURCED",
    }
    assert len(EvidenceTier) == len(expected)
    for name, value in expected.items():
        member = EvidenceTier[name]
        assert member.value == value
        assert member == value
        assert isinstance(member, str)


# =============================================================================
# 2. PVRERequestContract Tests
# =============================================================================


def test_pvre_request_contract_valid_instantiation() -> None:
    """Verify valid PVRERequestContract instantiation and default field values."""
    req = build_pvre_request()
    assert req.contract_version == "PVRE-2.2.0"
    assert req.research_run_id == SYNTHETIC_RESEARCH_RUN_ID
    assert req.player_query == "Sanju Samson"
    assert req.player_id == SYNTHETIC_PLAYER_ID_SANJU
    assert req.canonical_name == "Sanju Samson"
    assert req.identity_status == "RESOLVED"
    assert req.rr_relationship_state == "CURRENT_RR"
    assert req.rr_current_state == "CURRENT"
    assert req.player_capped_status == "CAPPED"
    assert req.ipl_uncapped_eligibility == "VERIFIED_NOT_ELIGIBLE"
    assert req.target_season_id == SYNTHETIC_TARGET_SEASON_ID
    assert req.evaluation_date == DEFAULT_EVALUATION_DATE
    assert req.research_window_years == 3
    assert req.force_refresh is False


def test_pvre_request_scenarios() -> None:
    """Verify PVRERequestContract builders across operating modes."""
    # Mode A Incumbent
    req_a = build_mode_a_incumbent_request()
    assert req_a.rr_relationship_state == "CURRENT_RR"
    assert req_a.player_capped_status == "CAPPED"

    # Mode B Uncapped
    req_b = build_mode_b_uncapped_request()
    assert req_b.rr_relationship_state == "NO_VERIFIED_RR_RELATIONSHIP"
    assert req_b.player_capped_status == "UNCAPPED"
    assert req_b.ipl_uncapped_eligibility == "VERIFIED_ELIGIBLE"

    # Review Required
    req_rev = build_review_required_request()
    assert req_rev.player_id is None
    assert req_rev.identity_status == "UNRESOLVED"
    assert req_rev.player_capped_status == "UNVERIFIED"

    # Out of Scope
    req_oos = build_out_of_scope_request()
    assert req_oos.rr_relationship_state == "NO_VERIFIED_RR_RELATIONSHIP"
    assert req_oos.player_capped_status == "CAPPED"


def test_pvre_request_extra_fields_forbidden() -> None:
    """Verify Pydantic v2 extra='forbid' rejects arbitrary unmodeled attributes."""
    data = valid_pvre_request_dict(unauthorized_attribute="malicious_payload")
    with pytest.raises(ValidationError) as exc_info:
        PVRERequestContract(**data)
    assert "extra_forbidden" in str(exc_info.value) or "Extra inputs are not permitted" in str(exc_info.value)


def test_pvre_request_window_bounds() -> None:
    """Verify research_window_years accepts 2 and 3, but rejects < 2 or > 3."""
    assert build_pvre_request(research_window_years=2).research_window_years == 2
    assert build_pvre_request(research_window_years=3).research_window_years == 3

    with pytest.raises(ValidationError):
        build_pvre_request(research_window_years=1)

    with pytest.raises(ValidationError):
        build_pvre_request(research_window_years=4)


def test_pvre_request_missing_required_fields() -> None:
    """Verify missing required fields raise ValidationError."""
    with pytest.raises(ValidationError):
        PVRERequestContract(  # type: ignore[call-arg]
            player_query="Sanju Samson",
            canonical_name="Sanju Samson",
        )


def test_pvre_request_validate_assignment() -> None:
    """Verify validate_assignment enforces bounds on mutation."""
    req = build_pvre_request()
    with pytest.raises(ValidationError):
        req.research_window_years = 5


def test_pvre_request_roundtrip_json() -> None:
    """Verify JSON serialization and deserialization roundtrip."""
    req = build_pvre_request()
    json_str = req.model_dump_json()
    reconstructed = PVRERequestContract.model_validate_json(json_str)
    assert reconstructed == req


# =============================================================================
# 3. PVREOutputContract Tests (Authoritative 26 Fields)
# =============================================================================


def test_pvre_output_contract_has_all_26_fields() -> None:
    """Verify PVREOutputContract contains exactly the 26 authoritative fields (TRD §9.6.2, PRD FR-PV8)."""
    expected_fields = {
        # 1. Governance & Run Identification
        "contract_version",
        "research_run_id",
        "player_id",
        "canonical_name",
        "identity_status",
        # 2. Routing & Mode Selection
        "research_mode",
        "route_status",
        "evaluation_date",
        "target_season_id",
        # 3. Membership & Eligibility States
        "rr_relationship_state",
        "rr_current_state",
        "player_capped_status",
        "ipl_uncapped_eligibility",
        # 4. Research Windows
        "research_window_start",
        "research_window_end",
        # 5. Career Coverage State
        "career_coverage_state",
        # 6. Domain Profiles & Assessments
        "rr_historical_profile",
        "recent_global_performance",
        "complete_career_profile",
        "replaceability_assessment",
        # 7. Coverage, Provenance & Quality
        "competition_coverage",
        "source_record_ids",
        "verification_record_ids",
        "review_status",
        "review_reason_codes",
        "data_quality_summary",
    }
    model_fields = set(PVREOutputContract.model_fields.keys())
    assert len(expected_fields) == 26, f"Expected 26 fields but definition has {len(expected_fields)}"
    assert model_fields == expected_fields, f"Field mismatch: diff={model_fields ^ expected_fields}"


def test_pvre_output_contract_valid_instantiation() -> None:
    """Verify valid PVREOutputContract instantiation with full payload."""
    out = build_pvre_output()
    assert out.contract_version == "PVRE-2.2.0"
    assert out.research_run_id == SYNTHETIC_RESEARCH_RUN_ID
    assert out.player_id == SYNTHETIC_PLAYER_ID_SANJU
    assert out.canonical_name == "Sanju Samson"
    assert out.identity_status == "RESOLVED"
    assert out.research_mode == "MODE_A"
    assert out.route_status == "ROUTED_RR_INCUMBENT"
    assert out.evaluation_date == DEFAULT_EVALUATION_DATE
    assert out.target_season_id == SYNTHETIC_TARGET_SEASON_ID
    assert out.rr_relationship_state == "CURRENT_RR"
    assert out.rr_current_state == "CURRENT"
    assert out.player_capped_status == "CAPPED"
    assert out.ipl_uncapped_eligibility == "VERIFIED_NOT_ELIGIBLE"
    assert out.research_window_start == DEFAULT_WINDOW_START
    assert out.research_window_end == DEFAULT_WINDOW_END
    assert out.career_coverage_state == "COMPLETE_WITHIN_VERIFIED_SOURCES"
    assert out.rr_historical_profile is not None
    assert out.recent_global_performance is not None
    assert out.complete_career_profile is None
    assert out.replaceability_assessment is not None
    assert isinstance(out.competition_coverage, dict)
    assert len(out.source_record_ids) == 3
    assert len(out.verification_record_ids) == 2
    assert out.review_status == "CLEAR"
    assert out.review_reason_codes == []
    assert isinstance(out.data_quality_summary, dict)


def test_pvre_output_contract_defaults() -> None:
    """Verify default values on optional collection fields when omitted."""
    out_default = PVREOutputContract(
        research_run_id=SYNTHETIC_RESEARCH_RUN_ID,
        canonical_name="Player",
        identity_status="RESOLVED",
        research_mode="MODE_A",
        route_status="ROUTED_RR_INCUMBENT",
        evaluation_date=DEFAULT_EVALUATION_DATE,
        target_season_id=SYNTHETIC_TARGET_SEASON_ID,
        rr_relationship_state="CURRENT_RR",
        rr_current_state="CURRENT",
        player_capped_status="CAPPED",
        ipl_uncapped_eligibility="VERIFIED_NOT_ELIGIBLE",
        research_window_start=DEFAULT_WINDOW_START,
        research_window_end=DEFAULT_WINDOW_END,
        career_coverage_state="COMPLETE_WITHIN_VERIFIED_SOURCES",
    )
    assert out_default.contract_version == "PVRE-2.2.0"
    assert out_default.player_id is None
    assert out_default.rr_historical_profile is None
    assert out_default.recent_global_performance is None
    assert out_default.complete_career_profile is None
    assert out_default.replaceability_assessment is None
    assert out_default.competition_coverage == {}
    assert out_default.source_record_ids == []
    assert out_default.verification_record_ids == []
    assert out_default.review_status == "CLEAR"
    assert out_default.review_reason_codes == []
    assert out_default.data_quality_summary == {}


def test_pvre_output_contract_extra_fields_forbidden() -> None:
    """Verify PVREOutputContract rejects extra unauthorized fields."""
    data = valid_pvre_output_dict(unknown_metric=99.9)
    with pytest.raises(ValidationError):
        PVREOutputContract(**data)


def test_pvre_output_contract_window_validation() -> None:
    """Verify research_window_start cannot be after research_window_end."""
    with pytest.raises(ValidationError) as exc_info:
        build_pvre_output(
            research_window_start=date(2025, 4, 1),
            research_window_end=date(2025, 3, 1),
        )
    assert "must not be after research_window_end" in str(exc_info.value)


def test_pvre_output_contract_scenarios() -> None:
    """Verify all 4 operating mode output contracts."""
    # Mode A
    out_a = build_mode_a_output()
    assert out_a.research_mode == "MODE_A"
    assert out_a.route_status == "ROUTED_RR_INCUMBENT"
    assert out_a.rr_historical_profile is not None
    assert out_a.complete_career_profile is None

    # Mode B
    out_b = build_mode_b_output()
    assert out_b.research_mode == "MODE_B"
    assert out_b.route_status == "ROUTED_UNCAPPED_CANDIDATE"
    assert out_b.complete_career_profile is not None
    assert out_b.rr_historical_profile is None
    assert out_b.replaceability_assessment is None

    # Review Required
    out_rev = build_review_required_output()
    assert out_rev.research_mode == "REVIEW_REQUIRED"
    assert out_rev.route_status == "ROUTED_SAFETY_REVIEW"
    assert out_rev.review_status == "REVIEW_REQUIRED"
    assert "UNKNOWN_PLAYER_NOT_IN_DATABASE" in out_rev.review_reason_codes

    # Out of Scope
    out_oos = build_out_of_scope_output()
    assert out_oos.research_mode == "OUT_OF_SCOPE"
    assert out_oos.route_status == "ROUTED_OUT_OF_SCOPE"


def test_pvre_output_contract_mixed_source_id_types() -> None:
    """Verify source_record_ids and verification_record_ids accept both UUID and int."""
    uid = uuid4()
    out = build_pvre_output(
        source_record_ids=[uid, 101, 202],
        verification_record_ids=[uid, 303],
    )
    assert out.source_record_ids == [uid, 101, 202]
    assert out.verification_record_ids == [uid, 303]


def test_pvre_output_contract_explicit_taxonomy_states() -> None:
    """Verify explicit UNKNOWN, UNVERIFIED, CONFLICT, NOT_COMPUTABLE, DATASET_UNAVAILABLE states."""
    out = build_pvre_output(
        career_coverage_state=CareerCoverageState.UNKNOWN.value,
        player_capped_status=PlayerCappedStatus.UNVERIFIED.value,
        competition_coverage={
            "IPL": PVREVerificationStatus.VERIFIED.value,
            "SMAT": PVREVerificationStatus.CONFLICT.value,
            "Ranji Trophy": PVREVerificationStatus.NOT_COMPUTABLE.value,
            "VHT": PVREVerificationStatus.DATASET_UNAVAILABLE.value,
            "Duleep Trophy": PVREVerificationStatus.UNKNOWN.value,
            "U19 Cooch Behar": PVREVerificationStatus.UNVERIFIED.value,
        },
    )
    assert out.career_coverage_state == "UNKNOWN"
    assert out.player_capped_status == "UNVERIFIED"
    assert out.competition_coverage["SMAT"] == "CONFLICT"
    assert out.competition_coverage["Ranji Trophy"] == "NOT_COMPUTABLE"
    assert out.competition_coverage["VHT"] == "DATASET_UNAVAILABLE"


def test_pvre_output_contract_roundtrip() -> None:
    """Verify PVREOutputContract serialization and deserialization roundtrip."""
    out = build_pvre_output()
    json_str = out.model_dump_json()
    reconstructed = PVREOutputContract.model_validate_json(json_str)
    assert reconstructed == out


# =============================================================================
# 4. ReviewDossierContract Tests
# =============================================================================


def test_review_dossier_contract_defaults() -> None:
    """Verify ReviewDossierContract defaults and optional subject_id."""
    dossier = PVREReviewDossierContract(dossier_id=SYNTHETIC_DOSSIER_ID)
    assert dossier.contract_version == "DOSSIER-1.0.0"
    assert dossier.subject_type == "player_research"
    assert dossier.subject_id is None
    assert dossier.review_status == "REVIEW_REQUIRED"
    assert dossier.review_reason_codes == []
    assert dossier.unresolved_claims == []
    assert dossier.conflicting_source_ids == []
    assert dossier.missing_evidence == []
    assert dossier.recommended_manual_checks == []


def test_review_dossier_contract_full_instantiation() -> None:
    """Verify full ReviewDossierContract instantiation."""
    dossier = build_review_dossier()
    assert dossier.dossier_id == SYNTHETIC_DOSSIER_ID
    assert dossier.subject_id is not None
    assert len(dossier.review_reason_codes) == 1
    assert len(dossier.unresolved_claims) == 1
    assert len(dossier.conflicting_source_ids) == 2
    assert len(dossier.missing_evidence) == 1
    assert len(dossier.recommended_manual_checks) == 1


def test_review_dossier_contract_extra_fields_forbidden() -> None:
    """Verify ReviewDossierContract extra='forbid'."""
    data = valid_review_dossier_dict(unknown_field="prohibited")
    with pytest.raises(ValidationError):
        PVREReviewDossierContract(**data)


def test_review_dossier_contract_roundtrip() -> None:
    """Verify ReviewDossierContract roundtrip."""
    dossier = build_review_dossier()
    json_str = dossier.model_dump_json()
    reconstructed = PVREReviewDossierContract.model_validate_json(json_str)
    assert reconstructed == dossier


# =============================================================================
# 5. ReplacementCandidateEvidence Tests (ORIGINAL_REQUEST R4)
# =============================================================================


def test_replacement_candidate_evidence_valid_instantiation() -> None:
    """Verify valid ReplacementCandidateEvidence contract for SICE comparison."""
    ev = build_replacement_candidate_evidence()
    assert ev.candidate_player_id == SYNTHETIC_PLAYER_ID_UNCAPPED
    assert ev.canonical_name == "Ashutosh Sharma"
    assert ev.age_at_evaluation == 26.5
    assert ev.primary_role == "FINISHER_BATTER"
    assert ev.secondary_role == "RIGHT_ARM_MEDIUM"
    assert ev.batting_hand == "RIGHT"
    assert ev.bowling_style == "RIGHT_ARM_MEDIUM"
    assert ev.ipl_uncapped_eligibility == "VERIFIED_ELIGIBLE"
    assert ev.verified_policy_id == SYNTHETIC_POLICY_ID
    assert ev.domestic_t20_metrics["strike_rate"] == 182.4
    assert ev.sample_indicators["matches"] == 28
    assert ev.evidence_tier == 1
    assert ev.career_coverage_state == "COMPLETE_WITHIN_VERIFIED_SOURCES"
    assert ev.provenance_verification_ids == [SYNTHETIC_VERIFICATION_ID]


def test_replacement_candidate_evidence_age_bounds() -> None:
    """Verify age_at_evaluation bounds (14.0 to 55.0)."""
    assert build_replacement_candidate_evidence(age_at_evaluation=14.0).age_at_evaluation == 14.0
    assert build_replacement_candidate_evidence(age_at_evaluation=55.0).age_at_evaluation == 55.0

    with pytest.raises(ValidationError):
        build_replacement_candidate_evidence(age_at_evaluation=13.9)

    with pytest.raises(ValidationError):
        build_replacement_candidate_evidence(age_at_evaluation=55.1)


def test_replacement_candidate_evidence_tier_bounds() -> None:
    """Verify evidence_tier bounds (1 to 4)."""
    assert build_replacement_candidate_evidence(evidence_tier=1).evidence_tier == 1
    assert build_replacement_candidate_evidence(evidence_tier=4).evidence_tier == 4

    with pytest.raises(ValidationError):
        build_replacement_candidate_evidence(evidence_tier=0)

    with pytest.raises(ValidationError):
        build_replacement_candidate_evidence(evidence_tier=5)


def test_replacement_candidate_evidence_extra_fields_forbidden() -> None:
    """Verify extra='forbid' on ReplacementCandidateEvidence."""
    data = valid_replacement_candidate_evidence_dict(hallucinated_stat=100.0)
    with pytest.raises(ValidationError):
        ReplacementCandidateEvidence(**data)


def test_replacement_candidate_evidence_roundtrip() -> None:
    """Verify ReplacementCandidateEvidence roundtrip."""
    ev = build_replacement_candidate_evidence()
    json_str = ev.model_dump_json()
    reconstructed = ReplacementCandidateEvidence.model_validate_json(json_str)
    assert reconstructed == ev


# =============================================================================
# 6. Additional Typed Domain Contracts Tests (ORIGINAL_REQUEST R1)
# =============================================================================


def test_player_research_request() -> None:
    """Verify PlayerResearchRequest contract behavior and bounds."""
    req = build_player_research_request()
    assert req.contract_version == "PVRE-2.2.0"
    assert req.canonical_name == "Sanju Samson"
    assert req.metadata == {"requester": "head_coach"}

    # Extra fields forbidden
    with pytest.raises(ValidationError):
        PlayerResearchRequest(  # type: ignore[call-arg]
            research_run_id=SYNTHETIC_RESEARCH_RUN_ID,
            player_query="Sanju Samson",
            canonical_name="Sanju Samson",
            target_season_id=SYNTHETIC_TARGET_SEASON_ID,
            evaluation_date=DEFAULT_EVALUATION_DATE,
            unknown_arg="rejected",
        )


def test_player_research_output_subclasses_pvre_output() -> None:
    """Verify PlayerResearchOutput is a typed subclass of PVREOutputContract."""
    out = build_player_research_output()
    assert isinstance(out, PVREOutputContract)
    assert isinstance(out, PlayerResearchOutput)
    assert issubclass(PlayerResearchOutput, PVREOutputContract)
    assert issubclass(PlayerResearchOutput, BaseContract)
    assert len(PlayerResearchOutput.model_fields) == 26


def test_replacement_research_request() -> None:
    """Verify ReplacementResearchRequest bounds and validation."""
    req = build_replacement_research_request()
    assert req.contract_version == "PVRE-2.2.0"
    assert req.target_role == "MIDDLE_ORDER_BATTER"
    assert req.candidate_pool_limit == 25
    assert req.must_be_uncapped is True

    # Candidate pool bounds
    with pytest.raises(ValidationError):
        build_replacement_research_request(candidate_pool_limit=0)
    with pytest.raises(ValidationError):
        build_replacement_research_request(candidate_pool_limit=501)

    # Extra fields forbidden
    with pytest.raises(ValidationError):
        build_replacement_research_request(extra="prohibited")


def test_verification_claim() -> None:
    """Verify VerificationClaim instantiation, timestamp, and verification status."""
    claim = build_verification_claim()
    assert claim.claim_id == SYNTHETIC_CLAIM_ID
    assert claim.claim_type == "DATE_OF_BIRTH"
    assert claim.claimed_value == "1994-11-11"
    assert claim.source_tier == EvidenceTier.TIER_2_COMMERCIAL.value
    assert claim.verification_status == PVREVerificationStatus.VERIFIED.value

    # Test roundtrip
    json_str = claim.model_dump_json()
    reconstructed = VerificationClaim.model_validate_json(json_str)
    assert reconstructed == claim

    # Extra forbidden
    with pytest.raises(ValidationError):
        VerificationClaim(  # type: ignore[call-arg]
            claim_id=SYNTHETIC_CLAIM_ID,
            canonical_name="Player",
            claim_type="TEST",
            claimed_value="VAL",
            source_id="S1",
            source_tier=EvidenceTier.TIER_1_OFFICIAL,
            retrieval_timestamp=DEFAULT_TIMESTAMP,
            invalid_field=True,
        )


def test_evidence_source() -> None:
    """Verify EvidenceSource metadata contract."""
    source = build_evidence_source()
    assert source.source_id == "S1"
    assert source.granularity == "BALL_BY_BALL"
    assert source.balls_per_over_default == 6
    assert source.is_active is True

    # Test format with 5 balls per over (The Hundred)
    hundred_source = build_evidence_source(
        source_id="S2",
        source_name="The Hundred - CricSheet",
        balls_per_over_default=5,
    )
    assert hundred_source.balls_per_over_default == 5

    # Extra fields forbidden
    with pytest.raises(ValidationError):
        build_evidence_source(unknown="forbidden")


def test_research_conflict() -> None:
    """Verify ResearchConflict contract preserves competing claims."""
    conflict = build_research_conflict()
    assert conflict.conflict_id == SYNTHETIC_CONFLICT_ID
    assert conflict.claim_type == "DATE_OF_BIRTH"
    assert conflict.primary_source_id == "S18A"
    assert conflict.primary_value == "2003-05-15"
    assert conflict.conflicting_source_id == "S20A"
    assert conflict.conflicting_value == "2002-11-20"
    assert conflict.resolution_status == "UNRESOLVED"
    assert conflict.review_dossier_id == SYNTHETIC_DOSSIER_ID

    # Roundtrip
    json_str = conflict.model_dump_json()
    reconstructed = ResearchConflict.model_validate_json(json_str)
    assert reconstructed == conflict

    # Extra forbidden
    with pytest.raises(ValidationError):
        build_research_conflict(unauthorized_attribute="value")


def test_career_verification() -> None:
    """Verify CareerVerification contract tracks multi-format career tenures."""
    cv = build_career_verification()
    assert cv.verification_id == SYNTHETIC_VERIFICATION_ID
    assert cv.canonical_name == "Sanju Samson"
    assert cv.capped_status == "CAPPED"
    assert cv.senior_international_caps == 40
    assert cv.youth_international_caps == 15
    assert cv.ipl_appearances == 168
    assert cv.rr_appearances == 138
    assert cv.coverage_state == "COMPLETE_WITHIN_VERIFIED_SOURCES"
    assert cv.verification_status == "VERIFIED"

    # Negative appearance check
    with pytest.raises(ValidationError):
        build_career_verification(ipl_appearances=-1)

    # Extra forbidden
    with pytest.raises(ValidationError):
        build_career_verification(extra="rejected")


def test_research_coverage() -> None:
    """Verify ResearchCoverage contract tracks dataset availability and searches."""
    cov = build_research_coverage()
    assert cov.coverage_state == "PARTIAL_COVERAGE"
    assert "IPL" in cov.competitions_verified
    assert "Ranji Trophy" in cov.competitions_unavailable
    assert "Ranji Trophy 2023-24" in cov.missing_competitions
    assert cov.total_matches_indexed == 85

    # Extra forbidden
    with pytest.raises(ValidationError):
        build_research_coverage(unmodeled=123)


# =============================================================================
# 7. Package Exports & BaseContract Compliance Tests
# =============================================================================


def test_all_pvre_contracts_inherit_base_contract() -> None:
    """Verify all PVRE contract classes inherit from BaseContract with strict discipline."""
    contract_classes = [
        PVRERequestContract,
        PVREOutputContract,
        PVREReviewDossierContract,
        ReplacementCandidateEvidence,
        PlayerResearchRequest,
        PlayerResearchOutput,
        ReplacementResearchRequest,
        VerificationClaim,
        EvidenceSource,
        ResearchConflict,
        CareerVerification,
        ResearchCoverage,
    ]
    for cls in contract_classes:
        assert issubclass(cls, BaseContract), f"{cls.__name__} does not inherit from BaseContract"
        assert cls.model_config.get("extra") == "forbid", f"{cls.__name__} does not forbid extra attributes"
        assert cls.model_config.get("validate_assignment") is True, (
            f"{cls.__name__} does not validate assignments"
        )


def test_pvre_exports_from_root_contracts() -> None:
    """Verify all PVRE contracts and taxonomy enums are exported from src.contracts package."""
    from src import contracts

    expected_symbols = [
        "ResearchMode",
        "RouteStatus",
        "ReplaceabilitySignal",
        "CareerCoverageState",
        "PlayerCappedStatus",
        "PVREVerificationStatus",
        "VerificationStatus",
        "PVREReviewStatus",
        "SourceReliability",
        "EvidenceTier",
        "PVRERequestContract",
        "PVREOutputContract",
        "PVREReviewDossierContract",
        "ReplacementCandidateEvidence",
        "PlayerResearchRequest",
        "PlayerResearchOutput",
        "ReplacementResearchRequest",
        "VerificationClaim",
        "EvidenceSource",
        "ResearchConflict",
        "CareerVerification",
        "ResearchCoverage",
    ]
    for symbol in expected_symbols:
        assert hasattr(contracts, symbol), f"src.contracts missing export: {symbol}"
        assert symbol in contracts.__all__, f"{symbol} missing from src.contracts.__all__"
