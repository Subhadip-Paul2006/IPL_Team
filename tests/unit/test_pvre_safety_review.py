"""Unit tests for PVRE Safety Review Interceptor and Multi-Source Conflict Preservation.

Validates TRD §9.5, PRD FR-PV7, and AI_INSTRUCTIONS R17, R18:
- All 8 trigger conditions routing to REVIEW_REQUIRED.
- Invariant: unknown player absent from DB routing to REVIEW_REQUIRED.
- Multi-source conflict preservation: dual claims preserved, never averaged or overwritten.
- Dual VerificationRecord generation with status CONFLICT.
- ReviewDossierContract structure, reason codes, unresolved claims, and manual checks.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from src.contracts.pvre import (
    EvidenceTier,
    PVREReviewStatus,
    PVREVerificationStatus,
    ReviewDossierContract,
)
from src.pvre.safety_review import (
    SafetyReviewInterceptor,
    SafetyReviewReasonCode,
    build_safety_review_dossier,
    normalize_source_id,
)

from tests.fixtures.pvre_contract_fixtures import (
    build_mode_a_incumbent_request,
    build_pvre_request,
)

# =============================================================================
# 1. Source ID Normalization Tests
# =============================================================================


def test_normalize_source_id_uuid_and_int() -> None:
    """Verify UUID and int source IDs are preserved intact."""
    test_uuid = uuid4()
    assert normalize_source_id(test_uuid) == test_uuid
    assert normalize_source_id(101) == 101


def test_normalize_source_id_string() -> None:
    """Verify string source IDs are normalized to deterministic UUIDs or ints."""
    # Integer string
    assert normalize_source_id("105") == 105

    # UUID string
    test_uuid = uuid4()
    assert normalize_source_id(str(test_uuid)) == test_uuid

    # Arbitrary alphanumeric code (e.g. "S18A") produces deterministic UUID
    norm_a = normalize_source_id("S18A")
    norm_b = normalize_source_id("S18A")
    assert isinstance(norm_a, UUID)
    assert norm_a == norm_b


# =============================================================================
# 2. Trigger Condition 1: Identity Ambiguity / Collision
# =============================================================================


def test_trigger_1_identity_collision() -> None:
    """Test Trigger 1: Multiple candidate matches route to REVIEW_REQUIRED."""
    interceptor = SafetyReviewInterceptor()
    hit, code, det = interceptor.inspect_identity_collision(
        candidate_count=2,
        identity_status="UNRESOLVED",
        query="Amit Sharma",
    )
    assert hit is True
    assert code == SafetyReviewReasonCode.COLLISION_MULTIPLE_IDENTITIES.value
    assert det is not None
    assert det["candidate_count"] == 2


def test_trigger_1_single_resolved_identity_passes() -> None:
    """Test Trigger 1: Single resolved identity passes without review trigger."""
    interceptor = SafetyReviewInterceptor()
    hit, code, det = interceptor.inspect_identity_collision(
        candidate_count=1,
        identity_status="RESOLVED",
        query="Sanju Samson",
    )
    assert hit is False
    assert code is None
    assert det is None


# =============================================================================
# 3. Trigger Condition 2: DOB / Biographical Conflicts
# =============================================================================


def test_trigger_2_dob_conflict() -> None:
    """Test Trigger 2: Conflicting DOB records route to REVIEW_REQUIRED and preserve dual claims."""
    interceptor = SafetyReviewInterceptor()
    pid = uuid4()
    hit, code, det = interceptor.inspect_dob_conflict(
        primary_dob="2004-05-10",
        conflicting_dob="2003-11-22",
        primary_source="S18A",
        conflicting_source="S20A",
        player_name="Young Prospect",
        player_id=pid,
    )
    assert hit is True
    assert code == SafetyReviewReasonCode.CONFLICT_DOB_RECORD.value
    assert det is not None
    assert det["source_a"]["value"] == "2004-05-10"
    assert det["source_b"]["value"] == "2003-11-22"

    # Verify conflict record was registered
    assert len(interceptor.conflicts) == 1
    conflict = interceptor.conflicts[0]
    assert conflict.claim_type == "DATE_OF_BIRTH"
    assert conflict.primary_value == "2004-05-10"
    assert conflict.conflicting_value == "2003-11-22"
    assert conflict.resolution_status == "UNRESOLVED"


def test_trigger_2_identical_dob_passes() -> None:
    """Test Trigger 2: Identical DOB across sources passes without conflict."""
    interceptor = SafetyReviewInterceptor()
    hit, code, det = interceptor.inspect_dob_conflict(
        primary_dob="2002-04-10",
        conflicting_dob="2002-04-10",
    )
    assert hit is False
    assert code is None
    assert len(interceptor.conflicts) == 0


# =============================================================================
# 4. Trigger Condition 3: RR Membership Contradictions
# =============================================================================


def test_trigger_3_rr_membership_contradiction() -> None:
    """Test Trigger 3: Contradictory RR relationship records route to REVIEW_REQUIRED."""
    interceptor = SafetyReviewInterceptor()
    # Claimed NO_VERIFIED_RR_RELATIONSHIP but squad inclusion exists
    hit, code, det = interceptor.inspect_rr_membership_contradiction(
        rr_relationship_state="NO_VERIFIED_RR_RELATIONSHIP",
        rr_current_state="NOT_CURRENT",
        has_squad_inclusion=True,
    )
    assert hit is True
    assert code == SafetyReviewReasonCode.CONFLICT_RR_MEMBERSHIP.value
    assert det is not None
    assert det["has_squad_inclusion"] is True


def test_trigger_3_valid_incumbent_membership_passes() -> None:
    """Test Trigger 3: Consistent RR incumbent relationship passes."""
    interceptor = SafetyReviewInterceptor()
    hit, code, det = interceptor.inspect_rr_membership_contradiction(
        rr_relationship_state="CURRENT_RR",
        rr_current_state="CURRENT",
        has_squad_inclusion=True,
    )
    assert hit is False
    assert code is None


# =============================================================================
# 5. Trigger Condition 4: Unverified Eligibility Policy
# =============================================================================


def test_trigger_4_unverified_eligibility_policy() -> None:
    """Test Trigger 4: Unassessed or unverified eligibility routes to REVIEW_REQUIRED."""
    interceptor = SafetyReviewInterceptor()
    hit, code, det = interceptor.inspect_eligibility_policy(
        ipl_uncapped_eligibility="NOT_ASSESSED",
        policy_id=None,
        policy_verified=False,
    )
    assert hit is True
    assert code == SafetyReviewReasonCode.UNVERIFIED_ELIGIBILITY_POLICY.value
    assert det is not None
    assert det["ipl_uncapped_eligibility"] == "NOT_ASSESSED"


def test_trigger_4_verified_eligibility_passes() -> None:
    """Test Trigger 4: Verified eligible policy passes."""
    interceptor = SafetyReviewInterceptor()
    hit, code, det = interceptor.inspect_eligibility_policy(
        ipl_uncapped_eligibility="VERIFIED_ELIGIBLE",
        policy_id=uuid4(),
        policy_verified=True,
    )
    assert hit is False
    assert code is None


# =============================================================================
# 6. Trigger Condition 5: Statistical Discrepancy Across Sources
# =============================================================================


def test_trigger_5_statistical_discrepancy() -> None:
    """Test Trigger 5: Discrepant statistics between external sources route to REVIEW_REQUIRED."""
    interceptor = SafetyReviewInterceptor()
    hit, code, det = interceptor.inspect_statistical_discrepancy(
        metric_name="matches",
        value_a=35,
        value_b=32,
        source_a="bcci_official",
        source_b="cricinfo_archive",
        player_name="Disputed Stats Batter",
    )
    assert hit is True
    assert code == SafetyReviewReasonCode.CONFLICTING_CAREER_STATISTICS.value
    assert det is not None
    assert det["source_a"]["value"] == 35
    assert det["source_b"]["value"] == 32

    # Verify conflict was preserved
    assert len(interceptor.conflicts) == 1
    conflict = interceptor.conflicts[0]
    assert conflict.primary_value == 35
    assert conflict.conflicting_value == 32


# =============================================================================
# 7. Trigger Condition 6: Low Corroboration
# =============================================================================


def test_trigger_6_low_corroboration() -> None:
    """Test Trigger 6: Unverified claims with insufficient source corroboration trigger review."""
    interceptor = SafetyReviewInterceptor()
    hit, code, det = interceptor.inspect_low_corroboration(
        corroborating_source_count=1,
        minimum_required=2,
        claim_description="Single media tweet claiming 150 km/h delivery speed",
    )
    assert hit is True
    assert code == SafetyReviewReasonCode.LOW_CORROBORATION.value
    assert det is not None
    assert det["sources_found"] == 1
    assert det["minimum_required"] == 2


# =============================================================================
# 8. Trigger Condition 7: Career Coverage Gap / Unindexed Tournaments
# =============================================================================


def test_trigger_7_career_coverage_gap() -> None:
    """Test Trigger 7: Missing tournaments or truncated coverage triggers review."""
    interceptor = SafetyReviewInterceptor()
    hit, code, det = interceptor.inspect_career_coverage_gap(
        coverage_state="PARTIAL_COVERAGE",
        missing_competitions=["Ranji Trophy 2023-24", "SMAT 2021"],
    )
    assert hit is True
    assert code == SafetyReviewReasonCode.CAREER_COVERAGE_GAP.value
    assert det is not None
    assert len(det["missing_competitions"]) == 2


# =============================================================================
# 9. Trigger Condition 8: Restricted or Unavailable Primary Source
# =============================================================================


def test_trigger_8_restricted_source_without_secondary() -> None:
    """Test Trigger 8: Restricted primary source without verified secondary triggers review."""
    interceptor = SafetyReviewInterceptor()
    hit, code, det = interceptor.inspect_restricted_or_unverified_source(
        source_is_restricted=True,
        has_verified_secondary=False,
        source_name="bcci.tv_paywalled_scorecard",
    )
    assert hit is True
    assert code == SafetyReviewReasonCode.RESTRICTED_OR_UNVERIFIED_SOURCE.value
    assert det is not None
    assert det["source_is_restricted"] is True


# =============================================================================
# 10. Multi-Source Conflict Preservation Invariant Tests
# =============================================================================


def test_multi_source_conflict_preservation_no_averaging() -> None:
    """Test invariant: conflicting numerical values are NEVER averaged or synthesized.

    Example: Source A says 35 matches, Source B says 32 matches. Neither 33.5 nor
    any other synthetic average may be written.
    """
    interceptor = SafetyReviewInterceptor()
    conflict = interceptor.preserve_conflicts(
        claim_type="MATCH_APPEARANCES",
        subject_name="Riyan Parag",
        primary_source_id=101,
        primary_value=35,
        primary_tier=EvidenceTier.TIER_1_OFFICIAL,
        conflicting_source_id=102,
        conflicting_value=32,
        conflicting_tier=EvidenceTier.TIER_2_COMMERCIAL,
    )

    # Invariant checks
    assert conflict.primary_value == 35
    assert conflict.conflicting_value == 32
    assert conflict.resolution_status == "UNRESOLVED"
    assert conflict.primary_value != 33.5
    assert conflict.conflicting_value != 33.5


def test_multi_source_conflict_dual_verification_records() -> None:
    """Test multi-source conflict preservation generates dual VerificationRecords with status CONFLICT."""
    interceptor = SafetyReviewInterceptor()
    subject_id = uuid4()
    interceptor.preserve_conflicts(
        claim_type="DATE_OF_BIRTH",
        subject_name="Amit Sharma",
        primary_source_id="S18A",
        primary_value="2003-05-15",
        primary_tier=EvidenceTier.TIER_1_OFFICIAL,
        conflicting_source_id="S20A",
        conflicting_value="2002-11-20",
        conflicting_tier=EvidenceTier.TIER_3_MEDIA,
        subject_id=subject_id,
    )

    records = interceptor.verification_records
    assert len(records) == 2
    for rec in records:
        assert rec.verification_status == PVREVerificationStatus.CONFLICT.value
        assert rec.subject_id == subject_id
        assert rec.confidence == 0.5


# =============================================================================
# 11. ReviewDossierContract Assembly & Validation Tests
# =============================================================================


def test_build_safety_review_dossier_contract() -> None:
    """Test build_safety_review_dossier compiles valid ReviewDossierContract with correct fields."""
    subject_id = uuid4()
    reason_codes = [
        SafetyReviewReasonCode.COLLISION_MULTIPLE_IDENTITIES.value,
        SafetyReviewReasonCode.CONFLICT_DOB_RECORD.value,
    ]
    unresolved_claims = [
        {"claim_type": "DATE_OF_BIRTH", "source_a": "2004-05-10", "source_b": "2003-11-22"}
    ]
    conflicting_source_ids = ["S18A", "S20A", 105]

    dossier = build_safety_review_dossier(
        subject_id=subject_id,
        review_reason_codes=reason_codes,
        unresolved_claims=unresolved_claims,
        conflicting_source_ids=conflicting_source_ids,
    )

    assert isinstance(dossier, ReviewDossierContract)
    assert dossier.contract_version == "DOSSIER-1.0.0"
    assert dossier.subject_id == subject_id
    assert dossier.review_status == PVREReviewStatus.REVIEW_REQUIRED.value
    assert len(dossier.review_reason_codes) == 2
    assert len(dossier.unresolved_claims) == 1
    assert len(dossier.conflicting_source_ids) == 3

    # Recommended manual checks must be populated automatically
    assert len(dossier.recommended_manual_checks) > 0
    checks_str = " ".join(dossier.recommended_manual_checks)
    assert "birth" in checks_str.lower() or "identity" in checks_str.lower()

    # Missing evidence must be populated automatically
    assert len(dossier.missing_evidence) > 0


# =============================================================================
# 12. SafetyReviewInterceptor.evaluate_request E2E Scenarios
# =============================================================================


def test_evaluate_request_all_clear() -> None:
    """Test evaluate_request returns False and None when no review triggers are present."""
    interceptor = SafetyReviewInterceptor()
    request = build_mode_a_incumbent_request()
    context = {
        "candidate_count": 1,
        "policy_id": uuid4(),
        "policy_verified": True,
        "career_coverage_state": "COMPLETE_WITHIN_VERIFIED_SOURCES",
        "in_database": True,
    }

    is_review, dossier = interceptor.evaluate_request(request, context)
    assert is_review is False
    assert dossier is None


def test_evaluate_request_collision_trigger() -> None:
    """Test evaluate_request intercepts collision and emits ReviewDossierContract."""
    interceptor = SafetyReviewInterceptor()
    request = build_pvre_request(
        canonical_name="Amit Sharma",
        identity_status="UNRESOLVED",
    )
    context = {"candidate_count": 2}

    is_review, dossier = interceptor.evaluate_request(request, context)
    assert is_review is True
    assert dossier is not None
    assert SafetyReviewReasonCode.COLLISION_MULTIPLE_IDENTITIES.value in dossier.review_reason_codes
    assert dossier.review_status == "REVIEW_REQUIRED"


def test_evaluate_request_unknown_player_database_absence() -> None:
    """Test evaluate_request intercepts player absent from database."""
    interceptor = SafetyReviewInterceptor()
    request = build_pvre_request(
        player_id=None,
        canonical_name="Domestic Prospect Absent From DB",
    )
    context = {"in_database": False}

    is_review, dossier = interceptor.evaluate_request(request, context)
    assert is_review is True
    assert dossier is not None
    assert SafetyReviewReasonCode.UNKNOWN_PLAYER_NOT_IN_DATABASE.value in dossier.review_reason_codes
