"""Unit tests for Eligibility Policy Service (Milestone M3 - Workstream Agent C).

Validates:
1. Versioned and season-bound policy registration and date range retrieval.
2. Invariant chk_policy_dates: expiry_date IS NULL OR expiry_date >= effective_date.
3. Invariant chk_policy_verified_evidence: NOT (verified = TRUE AND verification_id IS NULL).
4. Invariant chk_eligibility_status_flag:
   - VERIFIED_ELIGIBLE and VERIFIED_NOT_ELIGIBLE require verified=True and verification_id is not None.
   - NOT_ASSESSED and ELIGIBILITY_UNVERIFIED require verified=False.
5. Defaulting Rule: unassessed player strictly defaults to NOT_ASSESSED without inference.
6. Official BCCI/IPL source attribution and provenance persistence.
7. Foreign key enforcement on player eligibility records.
8. Optional database client synchronization using MockSupabaseClient.
"""

from datetime import date
from uuid import UUID, uuid4

import pytest
from src.contracts.eligibility import EligibilityPolicy, PlayerEligibility
from src.contracts.tmve import EligibilityOutputContract, EligibilityStatus
from src.membership.eligibility_service import EligibilityPolicyService

from tests.fixtures.mock_supabase import MockSupabaseClient


@pytest.fixture
def service() -> EligibilityPolicyService:
    """Fixture providing a fresh in-memory EligibilityPolicyService."""
    return EligibilityPolicyService()


@pytest.fixture
def season_id() -> UUID:
    """Fixture providing a canonical season UUID."""
    return uuid4()


@pytest.fixture
def player_id() -> UUID:
    """Fixture providing a canonical player UUID."""
    return uuid4()


# =============================================================================
# 1. Service Lifecycle and Health Inspection
# =============================================================================


def test_service_identity_and_health_check(service: EligibilityPolicyService) -> None:
    """Verify service boundary identity and initial operational health status."""
    assert service.get_service_name() == "eligibility_policy_service"

    health = service.health_check()
    assert health["service"] == "eligibility_policy_service"
    assert health["status"] == "operational"
    assert health["registered_policies_count"] == 0
    assert health["recorded_eligibility_count"] == 0
    assert health["db_connected"] is False


def test_service_reset(service: EligibilityPolicyService, season_id: UUID, player_id: UUID) -> None:
    """Verify reset() empties in-memory policy and player eligibility registries."""
    policy = service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 1, 1),
        rule_source="BCCI IPL 2026 Rule 4.1",
    )
    vid = uuid4()
    service.record_player_eligibility(
        player_id=player_id,
        policy_id=policy.policy_id,
        status=EligibilityStatus.VERIFIED_ELIGIBLE,
        verified=True,
        verification_id=vid,
    )

    assert service.health_check()["registered_policies_count"] == 1
    assert service.health_check()["recorded_eligibility_count"] == 1

    service.reset()
    assert service.health_check()["registered_policies_count"] == 0
    assert service.health_check()["recorded_eligibility_count"] == 0
    assert service.get_policy_by_id(policy.policy_id) is None


# =============================================================================
# 2. Policy Registration and Invariants
# =============================================================================


def test_register_policy_minimal_and_contract_type(
    service: EligibilityPolicyService, season_id: UUID
) -> None:
    """Verify policy registration with minimal required fields producing typed EligibilityPolicy."""
    policy = service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 1, 1),
        rule_source="BCCI IPL 2026 Player Regulations §3.2",
    )

    assert isinstance(policy, EligibilityPolicy)
    assert isinstance(policy.policy_id, UUID)
    assert policy.season_id == season_id
    assert policy.policy_version == 1
    assert policy.effective_date == date(2026, 1, 1)
    assert policy.expiry_date is None
    assert policy.rule_source == "BCCI IPL 2026 Player Regulations §3.2"
    assert policy.verified is False
    assert policy.verification_id is None
    assert policy.policy_json == {}


def test_register_policy_full_specification(
    service: EligibilityPolicyService, season_id: UUID
) -> None:
    """Verify policy registration with complete specification including verified evidence."""
    vid = uuid4()
    policy_spec = {
        "max_overseas_slots": 8,
        "uncapped_retention_limit": 2,
        "salary_cap_inr_crores": 120.0,
    }
    policy = service.register_policy(
        season_id=season_id,
        policy_version=2,
        effective_date=date(2026, 1, 1),
        expiry_date=date(2026, 12, 31),
        rule_source="IPL Governing Council Minutes 2025-11-20",
        policy_json=policy_spec,
        verified=True,
        verification_id=vid,
        notes="Official governance policy for IPL 2026 auction",
    )

    assert policy.policy_version == 2
    assert policy.expiry_date == date(2026, 12, 31)
    assert policy.verified is True
    assert policy.verification_id == vid
    assert policy.policy_json == policy_spec
    assert policy.notes == "Official governance policy for IPL 2026 auction"


def test_register_policy_unique_constraint_uq_policy(
    service: EligibilityPolicyService, season_id: UUID
) -> None:
    """Verify registering duplicate policy version for same season violates uq_policy."""
    service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 1, 1),
        rule_source="BCCI Rule v1",
    )

    with pytest.raises(ValueError, match="uq_policy violation"):
        service.register_policy(
            season_id=season_id,
            policy_version=1,
            effective_date=date(2026, 2, 1),
            rule_source="Conflicting BCCI Rule v1",
        )

    # Different version on same season succeeds
    p2 = service.register_policy(
        season_id=season_id,
        policy_version=2,
        effective_date=date(2026, 3, 1),
        rule_source="BCCI Rule v2",
    )
    assert p2.policy_version == 2


def test_register_policy_version_less_than_one_rejected(
    service: EligibilityPolicyService, season_id: UUID
) -> None:
    """Verify policy_version must be >= 1."""
    with pytest.raises(ValueError, match="policy_version must be >= 1"):
        service.register_policy(
            season_id=season_id,
            policy_version=0,
            effective_date=date(2026, 1, 1),
            rule_source="BCCI Rule v0",
        )


def test_register_policy_chk_policy_dates_violation(
    service: EligibilityPolicyService, season_id: UUID
) -> None:
    """Verify DDL constraint chk_policy_dates: expiry_date < effective_date is rejected."""
    with pytest.raises(ValueError, match="chk_policy_dates violation"):
        service.register_policy(
            season_id=season_id,
            policy_version=1,
            effective_date=date(2026, 6, 1),
            expiry_date=date(2026, 5, 31),
            rule_source="Invalid Date Range Policy",
        )


def test_register_policy_chk_policy_verified_evidence_violation(
    service: EligibilityPolicyService, season_id: UUID
) -> None:
    """Verify DDL constraint chk_policy_verified_evidence: verified=True without verification_id is rejected."""
    with pytest.raises(ValueError, match="chk_policy_verified_evidence violation"):
        service.register_policy(
            season_id=season_id,
            policy_version=1,
            effective_date=date(2026, 1, 1),
            rule_source="Unattributed Verified Policy",
            verified=True,
            verification_id=None,
        )


def test_register_policy_empty_rule_source_rejected(
    service: EligibilityPolicyService, season_id: UUID
) -> None:
    """Verify rule_source cannot be empty or whitespace."""
    with pytest.raises(ValueError, match="rule_source must be a non-empty string"):
        service.register_policy(
            season_id=season_id,
            policy_version=1,
            effective_date=date(2026, 1, 1),
            rule_source="   ",
        )


def test_register_policy_rule_source_max_length_rejected(
    service: EligibilityPolicyService, season_id: UUID
) -> None:
    """Verify rule_source cannot exceed 200 characters."""
    with pytest.raises(ValueError, match="rule_source cannot exceed 200 characters"):
        service.register_policy(
            season_id=season_id,
            policy_version=1,
            effective_date=date(2026, 1, 1),
            rule_source="X" * 201,
        )


# =============================================================================
# 3. Effective Policy Resolution (get_effective_policy)
# =============================================================================


def test_get_effective_policy_within_date_range(
    service: EligibilityPolicyService, season_id: UUID
) -> None:
    """Verify effective policy retrieval within active date boundaries."""
    policy = service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 2, 1),
        expiry_date=date(2026, 11, 30),
        rule_source="BCCI IPL 2026 Standard Policy",
    )

    resolved = service.get_effective_policy(season_id=season_id, as_of_date=date(2026, 5, 15))
    assert resolved is not None
    assert resolved.policy_id == policy.policy_id


def test_get_effective_policy_boundary_dates(
    service: EligibilityPolicyService, season_id: UUID
) -> None:
    """Verify effective policy on exact effective_date and exact expiry_date boundaries."""
    policy = service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 2, 1),
        expiry_date=date(2026, 11, 30),
        rule_source="BCCI IPL 2026 Standard Policy",
    )

    # Exact start boundary
    on_start = service.get_effective_policy(season_id=season_id, as_of_date=date(2026, 2, 1))
    assert on_start is not None
    assert on_start.policy_id == policy.policy_id

    # Exact end boundary
    on_end = service.get_effective_policy(season_id=season_id, as_of_date=date(2026, 11, 30))
    assert on_end is not None
    assert on_end.policy_id == policy.policy_id


def test_get_effective_policy_before_effective_date_returns_none(
    service: EligibilityPolicyService, season_id: UUID
) -> None:
    """Verify date prior to policy effective_date resolves to None."""
    service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 2, 1),
        expiry_date=date(2026, 11, 30),
        rule_source="BCCI IPL 2026 Standard Policy",
    )

    resolved = service.get_effective_policy(season_id=season_id, as_of_date=date(2026, 1, 31))
    assert resolved is None


def test_get_effective_policy_after_expiry_date_returns_none(
    service: EligibilityPolicyService, season_id: UUID
) -> None:
    """Verify date after policy expiry_date resolves to None."""
    service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 2, 1),
        expiry_date=date(2026, 11, 30),
        rule_source="BCCI IPL 2026 Standard Policy",
    )

    resolved = service.get_effective_policy(season_id=season_id, as_of_date=date(2026, 12, 1))
    assert resolved is None


def test_get_effective_policy_open_ended_without_expiry(
    service: EligibilityPolicyService, season_id: UUID
) -> None:
    """Verify open-ended policy (expiry_date=None) remains effective into future dates."""
    policy = service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 1, 1),
        expiry_date=None,
        rule_source="BCCI Perpetual Guidelines",
    )

    resolved = service.get_effective_policy(season_id=season_id, as_of_date=date(2030, 7, 1))
    assert resolved is not None
    assert resolved.policy_id == policy.policy_id


def test_get_effective_policy_multi_version_precedence(
    service: EligibilityPolicyService, season_id: UUID
) -> None:
    """Verify higher version takes precedence when multiple policies are concurrently active."""
    service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 1, 1),
        expiry_date=None,
        rule_source="BCCI Initial Guidelines v1",
    )
    p2 = service.register_policy(
        season_id=season_id,
        policy_version=2,
        effective_date=date(2026, 3, 1),
        expiry_date=None,
        rule_source="BCCI Amended Guidelines v2",
    )

    # Before v2 is effective, v1 is active
    before_v2 = service.get_effective_policy(season_id=season_id, as_of_date=date(2026, 2, 15))
    assert before_v2 is not None
    assert before_v2.policy_version == 1

    # After v2 is effective, v2 takes precedence
    after_v2 = service.get_effective_policy(season_id=season_id, as_of_date=date(2026, 4, 1))
    assert after_v2 is not None
    assert after_v2.policy_id == p2.policy_id
    assert after_v2.policy_version == 2


def test_get_effective_policy_no_registered_policy_returns_none(
    service: EligibilityPolicyService,
) -> None:
    """Verify query for unseeded season returns None."""
    random_season = uuid4()
    assert service.get_effective_policy(random_season, date(2026, 5, 1)) is None


# =============================================================================
# 4. Player Eligibility Recording and DDL Invariants
# =============================================================================


def test_record_player_eligibility_verified_eligible(
    service: EligibilityPolicyService, season_id: UUID, player_id: UUID
) -> None:
    """Verify recording VERIFIED_ELIGIBLE status with mandatory verification ID."""
    policy = service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 1, 1),
        rule_source="Official IPL 2026 Eligibility Guidelines",
    )
    vid = uuid4()
    record = service.record_player_eligibility(
        player_id=player_id,
        policy_id=policy.policy_id,
        status=EligibilityStatus.VERIFIED_ELIGIBLE,
        verified=True,
        verification_id=vid,
        notes="BCCI registration verified",
    )

    assert isinstance(record, PlayerEligibility)
    assert record.player_id == player_id
    assert record.policy_id == policy.policy_id
    assert record.eligibility_status == "VERIFIED_ELIGIBLE"
    assert record.verified is True
    assert record.verification_id == vid
    assert record.notes == "BCCI registration verified"


def test_record_player_eligibility_verified_not_eligible(
    service: EligibilityPolicyService, season_id: UUID, player_id: UUID
) -> None:
    """Verify recording VERIFIED_NOT_ELIGIBLE status with mandatory verification ID."""
    policy = service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 1, 1),
        rule_source="Official IPL 2026 Eligibility Guidelines",
    )
    vid = uuid4()
    record = service.record_player_eligibility(
        player_id=player_id,
        policy_id=policy.policy_id,
        status=EligibilityStatus.VERIFIED_NOT_ELIGIBLE,
        verified=True,
        verification_id=vid,
        notes="Medical unfitness documented by BCCI panel",
    )

    assert record.eligibility_status == "VERIFIED_NOT_ELIGIBLE"
    assert record.verified is True
    assert record.verification_id == vid


def test_record_player_eligibility_unverified_and_not_assessed(
    service: EligibilityPolicyService, season_id: UUID, player_id: UUID
) -> None:
    """Verify ELIGIBILITY_UNVERIFIED and NOT_ASSESSED statuses require verified=False."""
    policy = service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 1, 1),
        rule_source="Official IPL 2026 Eligibility Guidelines",
    )

    unverified = service.record_player_eligibility(
        player_id=player_id,
        policy_id=policy.policy_id,
        status=EligibilityStatus.ELIGIBILITY_UNVERIFIED,
        verified=False,
    )
    assert unverified.eligibility_status == "ELIGIBILITY_UNVERIFIED"
    assert unverified.verified is False

    # Update to NOT_ASSESSED
    not_assessed = service.record_player_eligibility(
        player_id=player_id,
        policy_id=policy.policy_id,
        status=EligibilityStatus.NOT_ASSESSED,
        verified=False,
    )
    assert not_assessed.eligibility_status == "NOT_ASSESSED"
    assert not_assessed.verified is False


def test_chk_eligibility_status_flag_verified_eligible_without_verified_flag(
    service: EligibilityPolicyService, season_id: UUID, player_id: UUID
) -> None:
    """Verify chk_eligibility_status_flag rejects VERIFIED_ELIGIBLE when verified=False."""
    policy = service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 1, 1),
        rule_source="IPL Policy",
    )
    with pytest.raises(ValueError, match="chk_eligibility_status_flag violation"):
        service.record_player_eligibility(
            player_id=player_id,
            policy_id=policy.policy_id,
            status=EligibilityStatus.VERIFIED_ELIGIBLE,
            verified=False,
            verification_id=uuid4(),
        )


def test_chk_eligibility_status_flag_verified_eligible_without_verification_id(
    service: EligibilityPolicyService, season_id: UUID, player_id: UUID
) -> None:
    """Verify chk_eligibility_status_flag rejects VERIFIED_ELIGIBLE when verification_id is None."""
    policy = service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 1, 1),
        rule_source="IPL Policy",
    )
    with pytest.raises(ValueError, match="chk_eligibility_status_flag violation"):
        service.record_player_eligibility(
            player_id=player_id,
            policy_id=policy.policy_id,
            status=EligibilityStatus.VERIFIED_ELIGIBLE,
            verified=True,
            verification_id=None,
        )


def test_chk_eligibility_status_flag_verified_not_eligible_without_verification_id(
    service: EligibilityPolicyService, season_id: UUID, player_id: UUID
) -> None:
    """Verify chk_eligibility_status_flag rejects VERIFIED_NOT_ELIGIBLE when verification_id is None."""
    policy = service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 1, 1),
        rule_source="IPL Policy",
    )
    with pytest.raises(ValueError, match="chk_eligibility_status_flag violation"):
        service.record_player_eligibility(
            player_id=player_id,
            policy_id=policy.policy_id,
            status=EligibilityStatus.VERIFIED_NOT_ELIGIBLE,
            verified=True,
            verification_id=None,
        )


def test_chk_eligibility_status_flag_not_assessed_with_verified_true(
    service: EligibilityPolicyService, season_id: UUID, player_id: UUID
) -> None:
    """Verify chk_eligibility_status_flag rejects NOT_ASSESSED when verified=True."""
    policy = service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 1, 1),
        rule_source="IPL Policy",
    )
    with pytest.raises(ValueError, match="chk_eligibility_status_flag violation"):
        service.record_player_eligibility(
            player_id=player_id,
            policy_id=policy.policy_id,
            status=EligibilityStatus.NOT_ASSESSED,
            verified=True,
        )


def test_chk_eligibility_status_flag_unverified_with_verified_true(
    service: EligibilityPolicyService, season_id: UUID, player_id: UUID
) -> None:
    """Verify chk_eligibility_status_flag rejects ELIGIBILITY_UNVERIFIED when verified=True."""
    policy = service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 1, 1),
        rule_source="IPL Policy",
    )
    with pytest.raises(ValueError, match="chk_eligibility_status_flag violation"):
        service.record_player_eligibility(
            player_id=player_id,
            policy_id=policy.policy_id,
            status=EligibilityStatus.ELIGIBILITY_UNVERIFIED,
            verified=True,
        )


def test_invalid_eligibility_status_string_rejected(
    service: EligibilityPolicyService, season_id: UUID, player_id: UUID
) -> None:
    """Verify invalid eligibility status string is rejected."""
    policy = service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 1, 1),
        rule_source="IPL Policy",
    )
    with pytest.raises(ValueError, match="chk_eligibility_status violation"):
        service.record_player_eligibility(
            player_id=player_id,
            policy_id=policy.policy_id,
            status="PRESUMED_ELIGIBLE",
        )


def test_record_eligibility_foreign_key_missing_policy(
    service: EligibilityPolicyService, player_id: UUID
) -> None:
    """Verify recording eligibility against a non-existent policy_id raises Foreign Key violation."""
    with pytest.raises(ValueError, match="Foreign key violation"):
        service.record_player_eligibility(
            player_id=player_id,
            policy_id=uuid4(),
            status=EligibilityStatus.NOT_ASSESSED,
            verified=False,
        )


# =============================================================================
# 5. Defaulting Rule & Player Eligibility Evaluation (evaluate_player_eligibility)
# =============================================================================


def test_evaluate_player_no_policy_defaults_to_not_assessed(
    service: EligibilityPolicyService, player_id: UUID
) -> None:
    """Verify evaluation strictly returns NOT_ASSESSED when no policy exists for season."""
    unseeded_season = uuid4()
    eval_result = service.evaluate_player_eligibility(
        player_id=player_id,
        season_id=unseeded_season,
        as_of_date=date(2026, 5, 1),
    )

    assert isinstance(eval_result, EligibilityOutputContract)
    assert eval_result.contract_version == "ELIG-1.0.0"
    assert eval_result.player_id == player_id
    assert eval_result.target_season_id == unseeded_season
    assert eval_result.eligibility_status == EligibilityStatus.NOT_ASSESSED
    assert eval_result.policy_id is None
    assert eval_result.policy_version is None
    assert eval_result.verified is False
    assert eval_result.verification_id is None
    assert eval_result.rule_source is None
    assert eval_result.evidence_verification_ids == []


def test_evaluate_unassessed_player_with_effective_policy_defaults_to_not_assessed(
    service: EligibilityPolicyService, season_id: UUID, player_id: UUID
) -> None:
    """Verify player with zero recorded evidence strictly defaults to NOT_ASSESSED.

    MANDATORY GUARDRAIL:
    Unknown or unassessed player eligibility MUST evaluate to NOT_ASSESSED.
    NEVER infer eligibility from missing records or dataset absence.
    """
    policy = service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 1, 1),
        rule_source="Official IPL 2026 Player Registration Rules",
    )

    eval_result = service.evaluate_player_eligibility(
        player_id=player_id,
        season_id=season_id,
        as_of_date=date(2026, 6, 1),
    )

    assert isinstance(eval_result, EligibilityOutputContract)
    assert eval_result.player_id == player_id
    assert eval_result.target_season_id == season_id
    assert eval_result.eligibility_status == EligibilityStatus.NOT_ASSESSED
    assert eval_result.policy_id == policy.policy_id
    assert eval_result.policy_version == policy.policy_version
    assert eval_result.verified is False
    assert eval_result.verification_id is None
    assert eval_result.rule_source == "Official IPL 2026 Player Registration Rules"
    assert eval_result.evidence_verification_ids == []


def test_evaluate_player_verified_eligible_contract_fidelity(
    service: EligibilityPolicyService, season_id: UUID, player_id: UUID
) -> None:
    """Verify evaluation returns verified eligible contract with provenance IDs."""
    policy = service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 1, 1),
        rule_source="BCCI IPL 2026 Eligibility Guidelines §5",
    )
    vid = uuid4()
    service.record_player_eligibility(
        player_id=player_id,
        policy_id=policy.policy_id,
        status=EligibilityStatus.VERIFIED_ELIGIBLE,
        verified=True,
        verification_id=vid,
    )

    eval_result = service.evaluate_player_eligibility(
        player_id=player_id,
        season_id=season_id,
        as_of_date=date(2026, 5, 10),
    )

    assert eval_result.eligibility_status == EligibilityStatus.VERIFIED_ELIGIBLE
    assert eval_result.verified is True
    assert eval_result.verification_id == vid
    assert eval_result.evidence_verification_ids == [vid]
    assert eval_result.rule_source == "BCCI IPL 2026 Eligibility Guidelines §5"
    assert eval_result.policy_id == policy.policy_id


def test_evaluate_player_verified_not_eligible_contract_fidelity(
    service: EligibilityPolicyService, season_id: UUID, player_id: UUID
) -> None:
    """Verify evaluation returns verified not eligible contract with provenance IDs."""
    policy = service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 1, 1),
        rule_source="BCCI IPL 2026 Disqualification Notice",
    )
    vid = uuid4()
    service.record_player_eligibility(
        player_id=player_id,
        policy_id=policy.policy_id,
        status=EligibilityStatus.VERIFIED_NOT_ELIGIBLE,
        verified=True,
        verification_id=vid,
    )

    eval_result = service.evaluate_player_eligibility(
        player_id=player_id,
        season_id=season_id,
        as_of_date=date(2026, 5, 10),
    )

    assert eval_result.eligibility_status == EligibilityStatus.VERIFIED_NOT_ELIGIBLE
    assert eval_result.verified is True
    assert eval_result.verification_id == vid
    assert eval_result.evidence_verification_ids == [vid]


def test_evaluate_player_eligibility_unverified_fidelity(
    service: EligibilityPolicyService, season_id: UUID, player_id: UUID
) -> None:
    """Verify evaluation returns unverified eligibility contract."""
    policy = service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 1, 1),
        rule_source="Provisional Registration List",
    )
    service.record_player_eligibility(
        player_id=player_id,
        policy_id=policy.policy_id,
        status=EligibilityStatus.ELIGIBILITY_UNVERIFIED,
        verified=False,
    )

    eval_result = service.evaluate_player_eligibility(
        player_id=player_id,
        season_id=season_id,
        as_of_date=date(2026, 5, 10),
    )

    assert eval_result.eligibility_status == EligibilityStatus.ELIGIBILITY_UNVERIFIED
    assert eval_result.verified is False
    assert eval_result.verification_id is None
    assert eval_result.evidence_verification_ids == []


# =============================================================================
# 6. Coercion and Utility Queries
# =============================================================================


def test_string_coercion_for_uuids_and_dates(
    service: EligibilityPolicyService,
) -> None:
    """Verify string UUIDs and dates are smoothly parsed and coerced."""
    str_season = "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
    str_player = "e7b0a880-9c2e-4e78-9e12-32b5d4f6c801"
    str_verif = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

    policy = service.register_policy(
        season_id=str_season,  # type: ignore[arg-type]
        policy_version=1,
        effective_date="2026-03-01",  # type: ignore[arg-type]
        expiry_date="2026-10-31",  # type: ignore[arg-type]
        rule_source="Coerced String Source",
        verified=True,
        verification_id=str_verif,  # type: ignore[arg-type]
    )

    assert policy.season_id == UUID(str_season)
    assert policy.effective_date == date(2026, 3, 1)
    assert policy.expiry_date == date(2026, 10, 31)
    assert policy.verification_id == UUID(str_verif)

    rec = service.record_player_eligibility(
        player_id=str_player,  # type: ignore[arg-type]
        policy_id=str(policy.policy_id),  # type: ignore[arg-type]
        status="VERIFIED_ELIGIBLE",
        verified=True,
        verification_id=str_verif,  # type: ignore[arg-type]
    )
    assert rec.player_id == UUID(str_player)

    evaluation = service.evaluate_player_eligibility(
        player_id=str_player,  # type: ignore[arg-type]
        season_id=str_season,  # type: ignore[arg-type]
        as_of_date="2026-05-01",  # type: ignore[arg-type]
    )
    assert evaluation.player_id == UUID(str_player)
    assert evaluation.eligibility_status == EligibilityStatus.VERIFIED_ELIGIBLE


def test_list_policies_for_season(
    service: EligibilityPolicyService, season_id: UUID
) -> None:
    """Verify listing all registered policies for a target season."""
    p1 = service.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 1, 1),
        rule_source="Version 1",
    )
    p2 = service.register_policy(
        season_id=season_id,
        policy_version=2,
        effective_date=date(2026, 4, 1),
        rule_source="Version 2",
    )

    # Different season
    service.register_policy(
        season_id=uuid4(),
        policy_version=1,
        effective_date=date(2026, 1, 1),
        rule_source="Other Season Policy",
    )

    policies = service.list_policies_for_season(season_id)
    assert len(policies) == 2
    assert {p.policy_id for p in policies} == {p1.policy_id, p2.policy_id}


# =============================================================================
# 7. Database Client Integration (MockSupabaseClient)
# =============================================================================


def test_database_client_persistence_and_sync(
    season_id: UUID, player_id: UUID
) -> None:
    """Verify EligibilityPolicyService persists records to MockSupabaseClient."""
    mock_db = MockSupabaseClient()
    service_with_db = EligibilityPolicyService(db_client=mock_db)

    assert service_with_db.health_check()["db_connected"] is True

    vid = uuid4()
    policy = service_with_db.register_policy(
        season_id=season_id,
        policy_version=1,
        effective_date=date(2026, 1, 1),
        rule_source="Official IPL 2026 Rules DB",
        verified=True,
        verification_id=vid,
    )

    # Verify presence in mock DB store
    policies_in_db = mock_db.tables.get("eligibility_policies", [])
    assert len(policies_in_db) == 1
    assert policies_in_db[0]["policy_id"] == str(policy.policy_id)
    assert policies_in_db[0]["season_id"] == str(season_id)
    assert policies_in_db[0]["rule_source"] == "Official IPL 2026 Rules DB"

    # Record player eligibility
    service_with_db.record_player_eligibility(
        player_id=player_id,
        policy_id=policy.policy_id,
        status=EligibilityStatus.VERIFIED_ELIGIBLE,
        verified=True,
        verification_id=vid,
    )

    elig_in_db = mock_db.tables.get("player_eligibility", [])
    assert len(elig_in_db) == 1
    assert elig_in_db[0]["player_id"] == str(player_id)
    assert elig_in_db[0]["policy_id"] == str(policy.policy_id)
    assert elig_in_db[0]["eligibility_status"] == "VERIFIED_ELIGIBLE"

    # Evaluate using the service backed by DB
    eval_result = service_with_db.evaluate_player_eligibility(
        player_id=player_id,
        season_id=season_id,
        as_of_date=date(2026, 6, 1),
    )
    assert eval_result.eligibility_status == EligibilityStatus.VERIFIED_ELIGIBLE
    assert eval_result.verified is True
