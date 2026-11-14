"""Unit tests for Team Membership Verification Engine (TMVE) inter-engine runtime contracts.

Validates model serialization, deserialization, field validation, default values,
and enum constraints for TRD §4.3, §4.4, §4.5, and §11 inter-engine contracts.
"""

from datetime import date
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from src.contracts import (
    EligibilityOutputContract,
    EligibilityStatus,
    ReviewDossierContract,
    RRCurrentState,
    RRRelationshipState,
    TMVEOutputContract,
    TMVERequestContract,
    tmve,
)

# =============================================================================
# 1. Enum Tests
# =============================================================================


def test_rr_relationship_state_enum_values() -> None:
    """Verify RRRelationshipState contains exact required states with matching str values."""
    expected_members = {
        "HISTORICAL_RR_APPEARANCE": "HISTORICAL_RR_APPEARANCE",
        "HISTORICAL_RR_SQUAD_ONLY": "HISTORICAL_RR_SQUAD_ONLY",
        "PREVIOUSLY_ASSOCIATED": "PREVIOUSLY_ASSOCIATED",
        "NO_VERIFIED_RR_RELATIONSHIP": "NO_VERIFIED_RR_RELATIONSHIP",
        "RR_RELATIONSHIP_UNKNOWN": "RR_RELATIONSHIP_UNKNOWN",
    }
    assert len(RRRelationshipState) == len(expected_members)
    for name, value in expected_members.items():
        member = RRRelationshipState[name]
        assert member.value == value
        assert member == value
        assert isinstance(member, str)


def test_rr_current_state_enum_values() -> None:
    """Verify RRCurrentState contains exact required states with matching str values."""
    expected_members = {
        "CURRENT": "CURRENT",
        "NOT_CURRENT": "NOT_CURRENT",
        "UNKNOWN": "UNKNOWN",
    }
    assert len(RRCurrentState) == len(expected_members)
    for name, value in expected_members.items():
        member = RRCurrentState[name]
        assert member.value == value
        assert member == value
        assert isinstance(member, str)


def test_eligibility_status_enum_values() -> None:
    """Verify EligibilityStatus contains exact required states with matching str values."""
    expected_members = {
        "VERIFIED_ELIGIBLE": "VERIFIED_ELIGIBLE",
        "VERIFIED_NOT_ELIGIBLE": "VERIFIED_NOT_ELIGIBLE",
        "ELIGIBILITY_UNVERIFIED": "ELIGIBILITY_UNVERIFIED",
        "NOT_ASSESSED": "NOT_ASSESSED",
    }
    assert len(EligibilityStatus) == len(expected_members)
    for name, value in expected_members.items():
        member = EligibilityStatus[name]
        assert member.value == value
        assert member == value
        assert isinstance(member, str)


# =============================================================================
# 2. TMVERequestContract Tests
# =============================================================================


def test_tmve_request_contract_valid_instantiation() -> None:
    """Verify TMVERequestContract instantiation with typed UUID and date."""
    player_id = uuid4()
    as_of = date(2026, 3, 1)
    req = TMVERequestContract(player_id=player_id, as_of_date=as_of)

    assert req.player_id == player_id
    assert req.as_of_date == as_of


def test_tmve_request_contract_coercion() -> None:
    """Verify TMVERequestContract coerces valid string UUID and date representation."""
    raw_uuid = "e7b0a880-9c2e-4e78-9e12-32b5d4f6c801"
    raw_date = "2026-03-01"
    req = TMVERequestContract(player_id=raw_uuid, as_of_date=raw_date)  # type: ignore[arg-type]

    assert req.player_id == UUID(raw_uuid)
    assert req.as_of_date == date(2026, 3, 1)


def test_tmve_request_contract_missing_required_fields() -> None:
    """Verify TMVERequestContract fails validation when required fields are missing."""
    with pytest.raises(ValidationError) as exc_info:
        TMVERequestContract(player_id=uuid4())  # type: ignore[call-arg]
    errors = exc_info.value.errors()
    assert any(err["loc"] == ("as_of_date",) for err in errors)

    with pytest.raises(ValidationError) as exc_info:
        TMVERequestContract(as_of_date=date(2026, 3, 1))  # type: ignore[call-arg]
    errors = exc_info.value.errors()
    assert any(err["loc"] == ("player_id",) for err in errors)


def test_tmve_request_contract_forbids_extra_fields() -> None:
    """Verify BaseContract extra='forbid' prevents unmodeled parameters."""
    with pytest.raises(ValidationError) as exc_info:
        TMVERequestContract(
            player_id=uuid4(),
            as_of_date=date(2026, 3, 1),
            unauthorized_field="malicious_payload",  # type: ignore[call-arg]
        )
    assert any(err["loc"] == ("unauthorized_field",) for err in exc_info.value.errors())


def test_tmve_request_contract_roundtrip() -> None:
    """Verify serialization and deserialization roundtrip for TMVERequestContract."""
    player_id = uuid4()
    as_of = date(2026, 3, 1)
    req = TMVERequestContract(player_id=player_id, as_of_date=as_of)

    dumped = req.model_dump()
    assert dumped == {"player_id": player_id, "as_of_date": as_of}

    json_str = req.model_dump_json()
    reconstructed = TMVERequestContract.model_validate_json(json_str)
    assert reconstructed == req


# =============================================================================
# 3. TMVEOutputContract Tests
# =============================================================================


def test_tmve_output_contract_defaults() -> None:
    """Verify default field values on TMVEOutputContract."""
    player_id = uuid4()
    as_of = date(2026, 3, 1)
    v_date = date(2026, 3, 1)

    contract = TMVEOutputContract(
        player_id=player_id,
        as_of_date=as_of,
        rr_relationship_state=RRRelationshipState.RR_RELATIONSHIP_UNKNOWN,
        rr_current_state=RRCurrentState.UNKNOWN,
        verification_date=v_date,
    )

    assert contract.contract_version == "TMVE-1.0.0"
    assert contract.rr_seasons == []
    assert contract.other_ipl_teams == []
    assert contract.verified_rr_appearances == 0
    assert contract.evidence_verification_ids == []
    assert contract.membership_confidence is None
    assert contract.negative_verification_met is False
    assert contract.review_status == "CLEAR"
    assert contract.review_reason_codes == []


def test_tmve_output_contract_full_instantiation() -> None:
    """Verify fully populated TMVEOutputContract instantiation."""
    player_id = uuid4()
    as_of = date(2026, 3, 1)
    v_date = date(2026, 3, 1)
    ev_id_1 = uuid4()
    ev_id_2 = uuid4()

    contract = TMVEOutputContract(
        contract_version="TMVE-1.0.0",
        player_id=player_id,
        as_of_date=as_of,
        rr_relationship_state=RRRelationshipState.HISTORICAL_RR_APPEARANCE,
        rr_current_state=RRCurrentState.NOT_CURRENT,
        rr_seasons=["2008", "2009", "2010"],
        other_ipl_teams=["Mumbai Indians", "Delhi Capitals"],
        verified_rr_appearances=35,
        evidence_verification_ids=[ev_id_1, ev_id_2],
        verification_date=v_date,
        membership_confidence=0.98,
        negative_verification_met=False,
        review_status="CLEAR",
        review_reason_codes=[],
    )

    assert contract.player_id == player_id
    assert contract.rr_relationship_state == RRRelationshipState.HISTORICAL_RR_APPEARANCE
    assert contract.rr_current_state == RRCurrentState.NOT_CURRENT
    assert contract.rr_seasons == ["2008", "2009", "2010"]
    assert contract.other_ipl_teams == ["Mumbai Indians", "Delhi Capitals"]
    assert contract.verified_rr_appearances == 35
    assert contract.evidence_verification_ids == [ev_id_1, ev_id_2]
    assert contract.membership_confidence == 0.98
    assert contract.negative_verification_met is False


def test_tmve_output_contract_negative_appearances_forbidden() -> None:
    """Verify verified_rr_appearances >= 0 constraint fails on negative values."""
    with pytest.raises(ValidationError) as exc_info:
        TMVEOutputContract(
            player_id=uuid4(),
            as_of_date=date(2026, 3, 1),
            rr_relationship_state=RRRelationshipState.HISTORICAL_RR_APPEARANCE,
            rr_current_state=RRCurrentState.NOT_CURRENT,
            verification_date=date(2026, 3, 1),
            verified_rr_appearances=-1,
        )
    assert any(err["loc"] == ("verified_rr_appearances",) for err in exc_info.value.errors())


def test_tmve_output_contract_invalid_enum_rejected() -> None:
    """Verify invalid string cannot be used where RRRelationshipState or RRCurrentState is required."""
    with pytest.raises(ValidationError) as exc_info:
        TMVEOutputContract(
            player_id=uuid4(),
            as_of_date=date(2026, 3, 1),
            rr_relationship_state="NON_EXISTENT_STATE",  # type: ignore[arg-type]
            rr_current_state=RRCurrentState.UNKNOWN,
            verification_date=date(2026, 3, 1),
        )
    assert any(err["loc"] == ("rr_relationship_state",) for err in exc_info.value.errors())

    with pytest.raises(ValidationError) as exc_info:
        TMVEOutputContract(
            player_id=uuid4(),
            as_of_date=date(2026, 3, 1),
            rr_relationship_state=RRRelationshipState.RR_RELATIONSHIP_UNKNOWN,
            rr_current_state="INVALID_CURRENT_STATE",  # type: ignore[arg-type]
            verification_date=date(2026, 3, 1),
        )
    assert any(err["loc"] == ("rr_current_state",) for err in exc_info.value.errors())


def test_tmve_output_contract_validate_assignment() -> None:
    """Verify BaseContract validate_assignment=True catches runtime invalid mutations."""
    contract = TMVEOutputContract(
        player_id=uuid4(),
        as_of_date=date(2026, 3, 1),
        rr_relationship_state=RRRelationshipState.HISTORICAL_RR_APPEARANCE,
        rr_current_state=RRCurrentState.CURRENT,
        verification_date=date(2026, 3, 1),
        verified_rr_appearances=10,
    )
    with pytest.raises(ValidationError):
        contract.verified_rr_appearances = -5


def test_tmve_output_contract_forbids_extra_fields() -> None:
    """Verify TMVEOutputContract rejects unknown attributes."""
    with pytest.raises(ValidationError) as exc_info:
        TMVEOutputContract(
            player_id=uuid4(),
            as_of_date=date(2026, 3, 1),
            rr_relationship_state=RRRelationshipState.RR_RELATIONSHIP_UNKNOWN,
            rr_current_state=RRCurrentState.UNKNOWN,
            verification_date=date(2026, 3, 1),
            extra_field="rejected",  # type: ignore[call-arg]
        )
    assert any(err["loc"] == ("extra_field",) for err in exc_info.value.errors())


def test_tmve_output_contract_roundtrip() -> None:
    """Verify serialization and deserialization roundtrip for TMVEOutputContract."""
    player_id = uuid4()
    ev_id = uuid4()
    contract = TMVEOutputContract(
        player_id=player_id,
        as_of_date=date(2026, 3, 1),
        rr_relationship_state=RRRelationshipState.NO_VERIFIED_RR_RELATIONSHIP,
        rr_current_state=RRCurrentState.NOT_CURRENT,
        rr_seasons=[],
        other_ipl_teams=["Chennai Super Kings"],
        verified_rr_appearances=0,
        evidence_verification_ids=[ev_id],
        verification_date=date(2026, 3, 1),
        membership_confidence=1.0,
        negative_verification_met=True,
        review_status="CLEAR",
        review_reason_codes=["NEGATIVE_PROTOCOL_PASSED"],
    )

    json_str = contract.model_dump_json()
    reconstructed = TMVEOutputContract.model_validate_json(json_str)
    assert reconstructed == contract
    assert reconstructed.negative_verification_met is True
    assert reconstructed.rr_relationship_state == RRRelationshipState.NO_VERIFIED_RR_RELATIONSHIP


# =============================================================================
# 4. EligibilityOutputContract Tests
# =============================================================================


def test_eligibility_output_contract_defaults() -> None:
    """Verify default values on EligibilityOutputContract."""
    player_id = uuid4()
    season_id = uuid4()

    contract = EligibilityOutputContract(
        player_id=player_id,
        target_season_id=season_id,
    )

    assert contract.contract_version == "ELIG-1.0.0"
    assert contract.player_id == player_id
    assert contract.target_season_id == season_id
    assert contract.eligibility_status == EligibilityStatus.NOT_ASSESSED
    assert contract.policy_id is None
    assert contract.policy_version is None
    assert contract.verified is False
    assert contract.verification_id is None
    assert contract.rule_source is None
    assert contract.evidence_verification_ids == []


def test_eligibility_output_contract_full_instantiation() -> None:
    """Verify fully populated EligibilityOutputContract."""
    player_id = uuid4()
    season_id = uuid4()
    policy_id = uuid4()
    verification_id = uuid4()
    ev_id = uuid4()

    contract = EligibilityOutputContract(
        contract_version="ELIG-1.0.0",
        player_id=player_id,
        target_season_id=season_id,
        eligibility_status=EligibilityStatus.VERIFIED_ELIGIBLE,
        policy_id=policy_id,
        policy_version=3,
        verified=True,
        verification_id=verification_id,
        rule_source="BCCI IPL 2027 Player Regulations §3.2.1",
        evidence_verification_ids=[ev_id],
    )

    assert contract.player_id == player_id
    assert contract.target_season_id == season_id
    assert contract.eligibility_status == EligibilityStatus.VERIFIED_ELIGIBLE
    assert contract.policy_id == policy_id
    assert contract.policy_version == 3
    assert contract.verified is True
    assert contract.verification_id == verification_id
    assert contract.rule_source == "BCCI IPL 2027 Player Regulations §3.2.1"
    assert contract.evidence_verification_ids == [ev_id]


def test_eligibility_output_contract_invalid_enum() -> None:
    """Verify invalid eligibility status string is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        EligibilityOutputContract(
            player_id=uuid4(),
            target_season_id=uuid4(),
            eligibility_status="DEFINITELY_ELIGIBLE",  # type: ignore[arg-type]
        )
    assert any(err["loc"] == ("eligibility_status",) for err in exc_info.value.errors())


def test_eligibility_output_contract_forbids_extra_fields() -> None:
    """Verify EligibilityOutputContract rejects unexpected attributes."""
    with pytest.raises(ValidationError) as exc_info:
        EligibilityOutputContract(
            player_id=uuid4(),
            target_season_id=uuid4(),
            unknown_flag=True,  # type: ignore[call-arg]
        )
    assert any(err["loc"] == ("unknown_flag",) for err in exc_info.value.errors())


def test_eligibility_output_contract_roundtrip() -> None:
    """Verify serialization and deserialization roundtrip for EligibilityOutputContract."""
    contract = EligibilityOutputContract(
        player_id=uuid4(),
        target_season_id=uuid4(),
        eligibility_status=EligibilityStatus.ELIGIBILITY_UNVERIFIED,
        rule_source="Provisional Schedule Announcement",
        evidence_verification_ids=[uuid4()],
    )

    json_str = contract.model_dump_json()
    reconstructed = EligibilityOutputContract.model_validate_json(json_str)
    assert reconstructed == contract


# =============================================================================
# 5. ReviewDossierContract Tests
# =============================================================================


def test_review_dossier_contract_defaults() -> None:
    """Verify default values on ReviewDossierContract."""
    dossier_id = uuid4()
    subject_id = uuid4()

    dossier = ReviewDossierContract(
        dossier_id=dossier_id,
        subject_type="player_membership",
        subject_id=subject_id,
    )

    assert dossier.contract_version == "DOSSIER-1.0.0"
    assert dossier.dossier_id == dossier_id
    assert dossier.subject_type == "player_membership"
    assert dossier.subject_id == subject_id
    assert dossier.review_status == "REVIEW_REQUIRED"
    assert dossier.review_reason_codes == []
    assert dossier.unresolved_claims == []
    assert dossier.conflicting_source_ids == []
    assert dossier.missing_evidence == []
    assert dossier.recommended_manual_checks == []


def test_review_dossier_contract_full_instantiation() -> None:
    """Verify fully populated ReviewDossierContract with mixed conflicting_source_ids."""
    dossier_id = uuid4()
    subject_id = uuid4()
    source_uuid = uuid4()

    dossier = ReviewDossierContract(
        contract_version="DOSSIER-1.0.0",
        dossier_id=dossier_id,
        subject_type="player_membership",
        subject_id=subject_id,
        review_status="REVIEW_REQUIRED",
        review_reason_codes=["CONFLICTING_SQUAD_RECORDS", "PARTIAL_SEASON_GAP"],
        unresolved_claims=[
            {
                "season": "2014",
                "claimed_role": "Squad Member",
                "discrepancy": "Absent from match registry",
            }
        ],
        conflicting_source_ids=[source_uuid, 1024, 2048],
        missing_evidence=["Official IPL 2014 Team Roster PDF"],
        recommended_manual_checks=[
            "Verify BCCI contract filing with legal archive",
            "Cross-reference player registration receipt",
        ],
    )

    assert dossier.dossier_id == dossier_id
    assert dossier.subject_type == "player_membership"
    assert dossier.subject_id == subject_id
    assert len(dossier.review_reason_codes) == 2
    assert len(dossier.unresolved_claims) == 1
    assert len(dossier.conflicting_source_ids) == 3
    assert dossier.conflicting_source_ids[0] == source_uuid
    assert dossier.conflicting_source_ids[1] == 1024
    assert dossier.conflicting_source_ids[2] == 2048
    assert len(dossier.missing_evidence) == 1
    assert len(dossier.recommended_manual_checks) == 2


def test_review_dossier_contract_missing_required_fields() -> None:
    """Verify missing required fields fail validation."""
    with pytest.raises(ValidationError) as exc_info:
        ReviewDossierContract(
            subject_type="player_membership",
            subject_id=uuid4(),
        )  # type: ignore[call-arg]
    assert any(err["loc"] == ("dossier_id",) for err in exc_info.value.errors())

    with pytest.raises(ValidationError) as exc_info:
        ReviewDossierContract(
            dossier_id=uuid4(),
            subject_id=uuid4(),
        )  # type: ignore[call-arg]
    assert any(err["loc"] == ("subject_type",) for err in exc_info.value.errors())

    with pytest.raises(ValidationError) as exc_info:
        ReviewDossierContract(
            dossier_id=uuid4(),
            subject_type="player_membership",
        )  # type: ignore[call-arg]
    assert any(err["loc"] == ("subject_id",) for err in exc_info.value.errors())


def test_review_dossier_contract_forbids_extra_fields() -> None:
    """Verify ReviewDossierContract rejects unmodeled parameters."""
    with pytest.raises(ValidationError) as exc_info:
        ReviewDossierContract(
            dossier_id=uuid4(),
            subject_type="player_membership",
            subject_id=uuid4(),
            extra_notes="Not in contract",  # type: ignore[call-arg]
        )
    assert any(err["loc"] == ("extra_notes",) for err in exc_info.value.errors())


def test_review_dossier_contract_roundtrip() -> None:
    """Verify serialization and deserialization roundtrip for ReviewDossierContract."""
    dossier = ReviewDossierContract(
        dossier_id=uuid4(),
        subject_type="player_eligibility",
        subject_id=uuid4(),
        review_reason_codes=["AMBIGUOUS_NOC_STATUS"],
        conflicting_source_ids=[uuid4(), 42],
        unresolved_claims=[{"issue": "NOC date mismatch"}],
    )

    json_str = dossier.model_dump_json()
    reconstructed = ReviewDossierContract.model_validate_json(json_str)
    assert reconstructed == dossier


# =============================================================================
# 6. Re-export and Contract Integration Tests
# =============================================================================


def test_tmve_contracts_re_exported_from_root() -> None:
    """Verify all TMVE contracts and enums are cleanly exposed via src.contracts."""
    from src import contracts

    exported_symbols = [
        "RRRelationshipState",
        "RRCurrentState",
        "EligibilityStatus",
        "TMVERequestContract",
        "TMVEOutputContract",
        "EligibilityOutputContract",
        "ReviewDossierContract",
    ]
    for symbol in exported_symbols:
        assert hasattr(contracts, symbol), f"src.contracts missing export: {symbol}"
        assert getattr(contracts, symbol) is getattr(
            contracts.tmve, symbol
        ), f"{symbol} in root contracts does not match tmve module"
        assert symbol in contracts.__all__, f"{symbol} missing from src.contracts.__all__"


def test_direct_tmve_module_identity() -> None:
    """Verify imported classes from src.contracts are identical to src.contracts.tmve classes."""
    assert RRRelationshipState is tmve.RRRelationshipState
    assert RRCurrentState is tmve.RRCurrentState
    assert EligibilityStatus is tmve.EligibilityStatus
    assert TMVERequestContract is tmve.TMVERequestContract
    assert TMVEOutputContract is tmve.TMVEOutputContract
    assert EligibilityOutputContract is tmve.EligibilityOutputContract
    assert ReviewDossierContract is tmve.ReviewDossierContract
