"""Unit tests for Provenance and Human Review Integration Service (Milestone M4).

Validates:
- VerificationRecord creation and evidence provenance attachment to claims.
- Conflict preservation without silent overwrite (Zero Silent Resolution invariant).
- ReviewDossierContract generation and structured safety dossiers.
- Routing ambiguous negative claims to human review queue with reason codes.
- HumanReviewQueue submission, resolution lifecycle, and custom queue compatibility.
- ServiceBoundary contract compliance and health checks.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.contracts.provenance import VerificationRecord
from src.contracts.tmve import ReviewDossierContract
from src.membership.provenance_review import (
    ProvenanceReviewService,
    ReviewReasonCode,
)
from src.pire.review_queue import HumanReviewQueue
from src.services.base import ServiceBoundary

# =============================================================================
# 1. Service Boundary & Initialization Tests
# =============================================================================


def test_service_boundary_inheritance() -> None:
    """Verify ProvenanceReviewService inherits ServiceBoundary."""
    service = ProvenanceReviewService()
    assert isinstance(service, ServiceBoundary)
    assert service.get_service_name() == "provenance_review_service"


def test_health_check_clean_state() -> None:
    """Verify health_check reflects initial empty state."""
    service = ProvenanceReviewService()
    status = service.health_check()
    assert status["service"] == "provenance_review_service"
    assert status["status"] == "healthy"
    assert status["verifications_count"] == 0
    assert status["dossiers_count"] == 0
    assert status["pending_queue_items"] == 0
    assert status["conflicts_count"] == 0


def test_custom_queue_injection() -> None:
    """Verify custom HumanReviewQueue can be injected into ProvenanceReviewService."""
    custom_queue = HumanReviewQueue()
    service = ProvenanceReviewService(queue=custom_queue)
    assert service.queue is custom_queue


# =============================================================================
# 2. VerificationRecord & Provenance Attachment Tests
# =============================================================================


def test_attach_verification_basic() -> None:
    """Verify basic VerificationRecord generation and caching."""
    service = ProvenanceReviewService()
    subject_id = uuid4()
    record = service.attach_verification(
        subject_type="player_membership",
        subject_id=subject_id,
        evidence_tier=1,
        source_provider="BCCI Central Contract Repository",
        source_url="https://bcci.tv/contracts/2026/rr",
        confidence=1.0,
    )

    assert isinstance(record, VerificationRecord)
    assert record.subject_type == "player_membership"
    assert record.subject_id == subject_id
    assert record.evidence_tier == 1
    assert record.source_provider == "BCCI Central Contract Repository"
    assert record.source_url == "https://bcci.tv/contracts/2026/rr"
    assert record.confidence == 1.0
    assert record.verification_status == "VERIFIED"

    # Cached in service
    retrieved = service.get_verification(record.verification_id)
    assert retrieved is record
    assert len(service.list_verifications()) == 1


def test_attach_verification_subject_type_normalization() -> None:
    """Verify shorthand subject type strings normalize to canonical entity names."""
    service = ProvenanceReviewService()
    pid = uuid4()

    rec_m = service.attach_verification("membership", pid, 2, "IPL Press Release")
    assert rec_m.subject_type == "player_membership"

    rec_e = service.attach_verification("eligibility", pid, 1, "BCCI Regulations")
    assert rec_e.subject_type == "player_eligibility"

    rec_i = service.attach_verification("identity", pid, 1, "National Passport Office")
    assert rec_i.subject_type == "player_identity"


def test_attach_verification_provenance_linking_to_claim() -> None:
    """Verify attaching verification to claim dict retains complete provenance metadata."""
    service = ProvenanceReviewService()
    subject_id = uuid4()
    claim: dict[str, Any] = {
        "player_id": subject_id,
        "relationship_state": "HISTORICAL_RR_APPEARANCE",
        "verified_appearances": 42,
    }

    record = service.attach_verification(
        subject_type="player_membership",
        subject_id=subject_id,
        evidence_tier=1,
        source_provider="Official IPL Match Archives",
        source_url="https://ipl.bcci.tv/archive/stats/42",
        confidence=0.99,
        claim=claim,
    )

    assert "evidence_verification_ids" in claim
    assert record.verification_id in claim["evidence_verification_ids"]
    assert claim["verification_id"] == record.verification_id
    assert "provenance" in claim
    assert len(claim["provenance"]) == 1

    prov = claim["provenance"][0]
    assert prov["verification_id"] == str(record.verification_id)
    assert prov["subject_type"] == "player_membership"
    assert prov["subject_id"] == str(subject_id)
    assert prov["evidence_tier"] == 1
    assert prov["source_provider"] == "Official IPL Match Archives"
    assert prov["confidence"] == 0.99


def test_attach_verification_invalid_tier_rejected() -> None:
    """Verify evidence_tier outside 1..5 raises ValueError."""
    service = ProvenanceReviewService()
    pid = uuid4()

    with pytest.raises(ValueError, match="evidence_tier must be between 1 and 5"):
        service.attach_verification("player_membership", pid, 0, "Fake Source")

    with pytest.raises(ValueError, match="evidence_tier must be between 1 and 5"):
        service.attach_verification("player_membership", pid, 6, "Fake Source")


def test_attach_verification_invalid_confidence_rejected() -> None:
    """Verify confidence outside [0.0, 1.0] raises ValueError."""
    service = ProvenanceReviewService()
    pid = uuid4()

    with pytest.raises(ValueError, match="confidence must be between 0.0 and 1.0"):
        service.attach_verification("player_membership", pid, 1, "Source", confidence=-0.1)

    with pytest.raises(ValueError, match="confidence must be between 0.0 and 1.0"):
        service.attach_verification("player_membership", pid, 1, "Source", confidence=1.05)


def test_attach_verification_unsupported_subject_type_rejected() -> None:
    """Verify unsupported subject type fails VerificationRecord validation."""
    service = ProvenanceReviewService()
    pid = uuid4()

    with pytest.raises(ValidationError):
        service.attach_verification("unsupported_entity_type", pid, 1, "Source")


# =============================================================================
# 3. Conflict Preservation (Zero Silent Resolution) Tests
# =============================================================================


def test_preserve_conflicts_without_silent_overwrite() -> None:
    """Verify conflict preservation retains both claims without silent overwrite."""
    service = ProvenanceReviewService()
    src_id_1 = uuid4()
    src_id_2 = uuid4()

    existing_claim = {
        "player_id": str(uuid4()),
        "player_name": "Sanju Samson",
        "appearances": 140,
        "relationship_state": "HISTORICAL_RR_APPEARANCE",
        "source_provider": "IPL Governing Council Official Roster",
        "source_id": src_id_1,
    }
    conflicting_claim = {
        "player_id": existing_claim["player_id"],
        "player_name": "Sanju Samson",
        "appearances": 138,
        "relationship_state": "HISTORICAL_RR_APPEARANCE",
        "source_provider": "Third-Party Media Statistic Pack",
        "source_id": src_id_2,
    }

    preserved = service.preserve_conflicts(existing_claim, conflicting_claim)

    assert preserved["conflict_status"] == "UNRESOLVED_CONFLICT"
    assert preserved["conflict_detected"] is True
    assert preserved["requires_human_review"] is True
    assert preserved["resolution_decision"] == "PRESERVED_FOR_HUMAN_REVIEW"

    # Both claims preserved verbatim
    assert preserved["existing_claim"]["appearances"] == 140
    assert preserved["conflicting_claim"]["appearances"] == 138

    # Field discrepancies detected
    diff_fields = [f["field"] for f in preserved["conflicting_fields"]]
    assert "appearances" in diff_fields
    assert "source_provider" in diff_fields
    assert "source_id" in diff_fields

    # Source IDs extracted
    assert src_id_1 in preserved["conflicting_source_ids"]
    assert src_id_2 in preserved["conflicting_source_ids"]

    # Recorded in review queue as persistent conflict
    assert service.queue.conflict_count == 1
    conflicts = service.queue.get_all_conflicts()
    assert conflicts[0].subject_name == "Sanju Samson"
    assert str(src_id_1) in conflicts[0].conflicting_ids
    assert str(src_id_2) in conflicts[0].conflicting_ids


def test_preserve_conflicts_immutability_of_inputs() -> None:
    """Verify inputs are deeply copied and not mutated during preservation."""
    service = ProvenanceReviewService()
    teams_existing = ["RR", "DC"]
    teams_conflicting = ["RR"]
    existing = {"player_id": "P1", "teams": teams_existing}
    conflicting = {"player_id": "P1", "teams": teams_conflicting}

    preserved = service.preserve_conflicts(existing, conflicting)

    # Mutate external lists
    teams_existing.append("CSK")
    teams_conflicting.clear()

    # Preserved state remains unmodified
    assert preserved["existing_claim"]["teams"] == ["RR", "DC"]
    assert preserved["conflicting_claim"]["teams"] == ["RR"]


def test_preserve_conflicts_sequential_tracking() -> None:
    """Verify multiple conflicts accumulate without overwrite."""
    service = ProvenanceReviewService()
    c1_a = {"player_id": "P1", "val": 10}
    c1_b = {"player_id": "P1", "val": 20}
    c2_a = {"player_id": "P2", "role": "BAT"}
    c2_b = {"player_id": "P2", "role": "BOWL"}

    p1 = service.preserve_conflicts(c1_a, c1_b)
    p2 = service.preserve_conflicts(c2_a, c2_b)

    assert p1["conflict_id"] != p2["conflict_id"]
    assert service.health_check()["conflicts_count"] == 2
    assert service.queue.conflict_count == 2


# =============================================================================
# 4. Review Dossier Construction Tests
# =============================================================================


def test_build_review_dossier_structure() -> None:
    """Verify ReviewDossierContract structure matches TRD §9.5 and §11 requirements."""
    service = ProvenanceReviewService()
    player_id = uuid4()
    src_uuid = uuid4()

    dossier = service.build_review_dossier(
        subject_type="player_membership",
        subject_id=player_id,
        reason_codes=[
            ReviewReasonCode.CONFLICTING_SQUAD_LISTS,
            ReviewReasonCode.PARTIAL_SEASON_GAP,
        ],
        conflicts=[
            {
                "season": "2015",
                "claimed_role": "Squad Member",
                "discrepancy": "Missing in official franchise filing",
                "conflicting_source_ids": [src_uuid, 2048],
            }
        ],
        missing_evidence=["Official IPL 2015 Team Roster Sign-off"],
    )

    assert isinstance(dossier, ReviewDossierContract)
    assert dossier.contract_version == "DOSSIER-1.0.0"
    assert dossier.subject_type == "player_membership"
    assert dossier.subject_id == player_id
    assert dossier.review_status == "REVIEW_REQUIRED"
    assert len(dossier.review_reason_codes) == 2
    assert len(dossier.unresolved_claims) == 1
    assert src_uuid in dossier.conflicting_source_ids
    assert 2048 in dossier.conflicting_source_ids
    assert len(dossier.missing_evidence) == 1
    assert len(dossier.recommended_manual_checks) >= 1

    # Stored in service
    retrieved = service.get_dossier(dossier.dossier_id)
    assert retrieved is dossier
    assert len(service.list_dossiers()) == 1


def test_build_review_dossier_dynamic_recommended_checks() -> None:
    """Verify recommended checks are generated appropriately for given reason codes."""
    service = ProvenanceReviewService()
    dossier = service.build_review_dossier(
        subject_type="player_membership",
        subject_id=uuid4(),
        reason_codes=[
            ReviewReasonCode.AMBIGUOUS_NEGATIVE_CLAIM,
            ReviewReasonCode.AMBIGUOUS_NOC_STATUS,
        ],
    )

    checks = dossier.recommended_manual_checks
    assert any("timeline against official BCCI match archives" in c for c in checks)
    assert any("NOC submission timestamp" in c for c in checks)


def test_build_review_dossier_custom_recommended_checks() -> None:
    """Verify user-provided recommended checks are preserved when supplied."""
    service = ProvenanceReviewService()
    custom_checks = ["Contact state cricket association secretary", "Inspect physical registration ledger"]
    dossier = service.build_review_dossier(
        subject_type="player_membership",
        subject_id=uuid4(),
        reason_codes=[ReviewReasonCode.BORDER_CASE_DATA],
        recommended_checks=custom_checks,
    )

    assert dossier.recommended_manual_checks == custom_checks


def test_build_review_dossier_serialization_roundtrip() -> None:
    """Verify serialization and deserialization roundtrip preserves all dossier fields."""
    service = ProvenanceReviewService()
    dossier = service.build_review_dossier(
        subject_type="player_eligibility",
        subject_id=uuid4(),
        reason_codes=[ReviewReasonCode.AMBIGUOUS_NOC_STATUS],
        conflicts=[{"issue": "NOC date mismatch"}],
        conflicting_source_ids=[uuid4(), 42],
        missing_evidence=["NOC Certificate 2027"],
    )

    json_str = dossier.model_dump_json()
    reconstructed = ReviewDossierContract.model_validate_json(json_str)
    assert reconstructed == dossier


# =============================================================================
# 5. Ambiguous Negative Claim Routing Tests
# =============================================================================


def test_route_negative_claim_generates_dossier_and_queues() -> None:
    """Verify route_negative_claim builds dossier and routes directly to review queue."""
    service = ProvenanceReviewService()
    player_id = uuid4()
    src_id = uuid4()

    evidence_summary = {
        "player_name": "Unverified Prospect",
        "active_years": [2012, 2013],
        "missing_evidence": ["2012 Franchise Roster Filing", "2013 Match Scorecards"],
        "conflicting_source_ids": [src_id],
        "discrepancy": "Mentioned in fan forum; zero appearances in verified scorecards",
    }

    dossier = service.route_negative_claim(
        player_id=player_id,
        reason_codes=[ReviewReasonCode.AMBIGUOUS_NEGATIVE_CLAIM],
        evidence_summary=evidence_summary,
    )

    assert isinstance(dossier, ReviewDossierContract)
    assert dossier.subject_id == player_id
    assert dossier.subject_type == "player_membership"
    assert ReviewReasonCode.AMBIGUOUS_NEGATIVE_CLAIM in dossier.review_reason_codes
    assert len(dossier.missing_evidence) == 2
    assert src_id in dossier.conflicting_source_ids

    # Automatically queued to HumanReviewQueue
    assert service.queue.pending_count == 1
    pending_items = service.queue.get_pending()
    assert len(pending_items) == 1
    queue_item = pending_items[0]
    assert queue_item.external_id == str(player_id)
    assert queue_item.raw_name == "Unverified Prospect"
    assert queue_item.status == "PENDING"
    assert str(src_id) in queue_item.candidate_ids
    assert ReviewReasonCode.AMBIGUOUS_NEGATIVE_CLAIM in queue_item.trigger_reason


def test_route_negative_claim_default_reason_code() -> None:
    """Verify empty reason_codes defaults to AMBIGUOUS_NEGATIVE_CLAIM."""
    service = ProvenanceReviewService()
    player_id = uuid4()

    dossier = service.route_negative_claim(
        player_id=player_id,
        reason_codes=[],
        evidence_summary={"discrepancy": "Unknown timeline gap"},
    )

    assert dossier.review_reason_codes == [ReviewReasonCode.AMBIGUOUS_NEGATIVE_CLAIM]


# =============================================================================
# 6. Queue Submission & Queue Lifecycle Tests
# =============================================================================


def test_submit_dossier_to_queue_lifecycle() -> None:
    """Verify submit_dossier_to_queue stages item and supports manual resolution."""
    service = ProvenanceReviewService()
    player_id = uuid4()
    dossier = service.build_review_dossier(
        subject_type="player_membership",
        subject_id=player_id,
        reason_codes=[ReviewReasonCode.CONFLICTING_SQUAD_LISTS],
        conflicts=[{"player_name": "Test Player", "source_id": uuid4()}],
    )

    queue_id = service.submit_dossier_to_queue(dossier)
    assert isinstance(queue_id, str)
    assert len(queue_id) > 0

    # Queue reflects pending item
    assert service.queue.pending_count == 1
    pending = service.queue.get_pending()[0]
    assert pending.queue_id == queue_id
    assert pending.status == "PENDING"
    assert pending.raw_name == "Test Player"

    # Human analyst resolution
    target_canonical_id = str(uuid4())
    resolved = service.queue.resolve_item(
        queue_id=queue_id,
        target_player_id=target_canonical_id,
        reviewer_id="analyst_007",
        notes="Confirmed squad inclusion from signed BCCI contract physical archive",
    )
    assert resolved is not None
    assert resolved.status == "RESOLVED"
    assert service.queue.pending_count == 0


def test_submit_dossier_to_custom_queue() -> None:
    """Verify submit_dossier_to_queue works with custom list or queue-like object."""
    service = ProvenanceReviewService()
    dossier = service.build_review_dossier(
        subject_type="player_membership",
        subject_id=uuid4(),
        reason_codes=[ReviewReasonCode.BORDER_CASE_DATA],
    )

    custom_list: list[dict[str, Any]] = []
    queue_id = service.submit_dossier_to_queue(dossier, queue=custom_list)

    assert isinstance(queue_id, str)
    assert len(custom_list) == 1
    assert custom_list[0]["queue_id"] == queue_id
    assert custom_list[0]["dossier"] is dossier


# =============================================================================
# 7. End-to-End Service Integration & State Verification
# =============================================================================


def test_end_to_end_provenance_conflict_and_review_flow() -> None:
    """Verify comprehensive flow: verification -> conflict -> negative claim -> review queue."""
    service = ProvenanceReviewService()
    player_id = uuid4()

    # Step 1: Initial claim with evidence attachment
    claim: dict[str, Any] = {
        "player_id": player_id,
        "player_name": "Border Player",
        "rr_relationship_state": "HISTORICAL_RR_APPEARANCE",
        "appearances": 5,
        "source_provider": "Historical Scorecard Archive",
    }
    rec1 = service.attach_verification(
        subject_type="player_membership",
        subject_id=player_id,
        evidence_tier=2,
        source_provider="Historical Scorecard Archive",
        confidence=0.85,
        claim=claim,
    )
    assert rec1.verification_id in claim["evidence_verification_ids"]

    # Step 2: Conflicting claim arrives from rival data source
    conflicting_claim: dict[str, Any] = {
        "player_id": player_id,
        "player_name": "Border Player",
        "rr_relationship_state": "HISTORICAL_RR_SQUAD_ONLY",
        "appearances": 0,
        "source_provider": "Official Franchise Roster Signoff",
        "source_id": uuid4(),
    }
    conflict = service.preserve_conflicts(claim, conflicting_claim)
    assert conflict["conflict_status"] == "UNRESOLVED_CONFLICT"

    # Step 3: Ambiguous negative claim protocol triggered
    dossier = service.route_negative_claim(
        player_id=player_id,
        reason_codes=[
            ReviewReasonCode.CONFLICTING_SQUAD_LISTS,
            ReviewReasonCode.AMBIGUOUS_NEGATIVE_CLAIM,
        ],
        evidence_summary={
            "player_name": "Border Player",
            "conflicts": [conflict],
            "missing_evidence": ["2014 BCCI Match Report signed by referee"],
        },
    )

    # Step 4: Verify complete service diagnostic state
    status = service.health_check()
    assert status["status"] == "healthy"
    assert status["verifications_count"] == 1
    assert status["dossiers_count"] == 1
    assert status["conflicts_count"] == 1
    assert status["pending_queue_items"] == 1

    # Step 5: Verify dossier structure
    assert dossier.review_status == "REVIEW_REQUIRED"
    assert len(dossier.unresolved_claims) == 1
    assert len(dossier.missing_evidence) == 1
    assert len(dossier.recommended_manual_checks) >= 1
