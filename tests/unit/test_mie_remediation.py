"""Regression tests for the critical MIE remediation defects."""

from __future__ import annotations

import csv
import io
import json
from uuid import UUID, uuid4

import pytest
from src.contracts.cdcre import CandidatePlayerRecord
from src.contracts.cmie import CMIEVerificationStatus
from src.contracts.pvre import CareerCoverageState, PlayerCappedStatus, VerificationStatus
from src.contracts.tmve import EligibilityStatus, RRCurrentState, RRRelationshipState
from src.mie.adapters.cmie_adapter import CMIEAdapter
from src.mie.adapters.pire_adapter import PIREAdapter
from src.mie.confidence import ConfidenceReconciler
from src.mie.contracts import (
    CappedStatusEvidence,
    EngineExecutionRecord,
    EngineName,
    ExecutionState,
)
from src.mie.orchestrator import MotherIntelligenceEngine
from src.pire.models import IdentityStatus, ResolutionTier


def _records(state: ExecutionState = ExecutionState.SUCCESS) -> dict[str, EngineExecutionRecord]:
    return {
        name: EngineExecutionRecord(
            engine=EngineName.CDCRE if name == "CDCRE_CANDIDATE_DISCOVERY" else EngineName(name),
            state=state,
            execution_time_ms=1,
        )
        for name in (
            "PIRE",
            "CDCRE_CANDIDATE_DISCOVERY",
            "TMVE",
            "CDCRE",
            "CPPAE",
            "CMIE",
            "PVRE",
        )
    }


def test_verification_requires_all_sources_cap_and_complete_career() -> None:
    args = {
        "identity_status": "RESOLVED",
        "resolution_tier": 1,
        "rr_relationship_state": RRRelationshipState.NO_VERIFIED_RR_RELATIONSHIP,
        "rr_current_state": RRCurrentState.NOT_CURRENT,
        "ipl_uncapped_eligibility": EligibilityStatus.VERIFIED_ELIGIBLE,
        "player_capped_status": PlayerCappedStatus.UNCAPPED,
        "career_coverage_state": CareerCoverageState.COMPLETE_WITHIN_VERIFIED_SOURCES,
        "execution_records": _records(),
        "required_source_ids": ["src-1"],
        "cmie_verification_status": CMIEVerificationStatus.VERIFIED,
    }
    assert (
        ConfidenceReconciler.aggregate_verification_status(
            **args, cap_evidence_verified=True, candidate_evidence_present=True
        ).overall_status.value
        == "VERIFIED"
    )
    capped_case = {
        **args,
        "player_capped_status": PlayerCappedStatus.CAPPED,
    }
    assert (
        ConfidenceReconciler.aggregate_verification_status(
            **capped_case, cap_evidence_verified=True, candidate_evidence_present=True
        ).overall_status.value
        == "VERIFIED"
    )
    ineligible_case = {
        **capped_case,
        "ipl_uncapped_eligibility": EligibilityStatus.VERIFIED_NOT_ELIGIBLE,
    }
    assert (
        ConfidenceReconciler.aggregate_verification_status(
            **ineligible_case, cap_evidence_verified=True, candidate_evidence_present=True
        ).overall_status.value
        == "VERIFIED"
    )
    for altered in (
        {"cap_evidence_verified": False},
        {"required_source_ids": []},
        {"career_coverage_state": CareerCoverageState.PARTIAL_COVERAGE},
        {"identity_status": "UNRESOLVED"},
        {"execution_records": _records(ExecutionState.FAILED)},
    ):
        case = {**args, **altered}
        case.setdefault("cap_evidence_verified", True)
        case.setdefault("candidate_evidence_present", True)
        result = ConfidenceReconciler.aggregate_verification_status(**case)
        assert result.overall_status.value != "VERIFIED"


@pytest.mark.parametrize(
    ("status", "verification", "sources", "conflicts", "valid"),
    [
        (PlayerCappedStatus.CAPPED, VerificationStatus.VERIFIED, ["icc-1"], [], True),
        (PlayerCappedStatus.UNCAPPED, VerificationStatus.VERIFIED, ["icc-2"], [], True),
        (PlayerCappedStatus.UNVERIFIED, VerificationStatus.UNKNOWN, [], [], True),
        (PlayerCappedStatus.UNVERIFIED, VerificationStatus.VERIFIED, [], [], False),
        (PlayerCappedStatus.UNCAPPED, VerificationStatus.VERIFIED, [], [], False),
        (PlayerCappedStatus.UNVERIFIED, VerificationStatus.CONFLICT, ["a", "b"], ["a", "b"], True),
    ],
)
def test_cap_evidence_contract_adversarial(status, verification, sources, conflicts, valid) -> None:
    values = {
        "status": status,
        "verification_status": verification,
        "source_record_ids": sources,
        "conflicting_source_ids": conflicts,
    }
    if valid:
        CappedStatusEvidence(**values)
    else:
        with pytest.raises(ValueError):
            CappedStatusEvidence(**values)


def test_missing_cap_boolean_never_routes_as_uncapped() -> None:
    report = MotherIntelligenceEngine().request_player_intelligence("Unknown cap status")
    assert report.verification.player_capped_status == PlayerCappedStatus.UNVERIFIED
    assert report.pvre.player_capped_status == PlayerCappedStatus.UNVERIFIED
    assert report.verification.overall_status.value != "VERIFIED"


def test_pire_candidate_mismatch_is_reviewed_and_candidate_provenance_survives() -> None:
    adapter = PIREAdapter()
    adapter.resolver.register_player(
        canonical_player_id=str(uuid4()), canonical_name="Asha Candidate"
    )
    unrelated = CandidatePlayerRecord(
        player_id=uuid4(), canonical_name="Different Person", source_id="cdcre-roster"
    )
    result = adapter.execute("Asha Candidate", candidates=[unrelated])
    assert result.status == IdentityStatus.UNRESOLVED
    assert result.tier == ResolutionTier.UNRESOLVED_DISPATCH
    assert result.needs_review is True
    assert result.candidate_matches[0]["source_id"] == "cdcre-roster"


def test_pire_multiple_candidates_are_not_arbitrarily_selected() -> None:
    adapter = PIREAdapter()
    candidates = [
        CandidatePlayerRecord(canonical_name="Same Name", source_id="one"),
        CandidatePlayerRecord(canonical_name="Same Name", source_id="two"),
    ]
    result = adapter.execute("Same Name", candidates=candidates)
    assert result.status == IdentityStatus.UNRESOLVED
    assert result.needs_review is True
    assert {row["source_id"] for row in result.candidate_matches} == {"one", "two"}


def test_candidate_discovery_exception_gates_pire_instead_of_passing_none() -> None:
    class FailedDiscovery:
        def search_players(self, query: str) -> object:
            raise TimeoutError("private candidate backend detail")

        def player_matches(self, player_id: UUID) -> tuple[()]:
            return ()

        def availability(self) -> dict[str, str]:
            return {}

    class MustNotResolve:
        class AliasRegistry:
            def lookup_name_candidates(self, query: str) -> list[str]:
                return []

        alias_registry = AliasRegistry()
        players: dict[str, object] = {}

        def resolve(self, **kwargs: object) -> object:
            raise AssertionError("PIRE must not run after candidate discovery failure")

    engine = MotherIntelligenceEngine(
        pire_adapter=PIREAdapter(MustNotResolve()),
        data_provider=FailedDiscovery(),
    )
    report = engine.request_player_intelligence("Candidate discovery failure")

    assert report.engine_executions["CDCRE_CANDIDATE_DISCOVERY"].state == ExecutionState.FAILED
    assert report.engine_executions[EngineName.PIRE.value].state == ExecutionState.SKIPPED
    assert report.identity["status"] == "UNRESOLVED"
    assert "CANDIDATE_DISCOVERY_EXECUTION_FAILED" in report.verification.review_reason_codes


def test_pire_exception_uses_valid_review_fallback_and_records_failure() -> None:
    class TimeoutResolver:
        def resolve(self, **kwargs: object) -> object:
            raise TimeoutError("private backend detail")

    result, record = PIREAdapter(TimeoutResolver()).execute_monitored(raw_name="Timeout player")
    assert result.status == IdentityStatus.UNRESOLVED
    assert result.tier == ResolutionTier.UNRESOLVED_DISPATCH
    assert result.needs_review is True
    assert record.state == ExecutionState.FAILED
    assert "TimeoutError" in (record.error_message or "")
    assert "private backend detail" not in (record.error_message or "")


def test_cmie_adapter_preserves_explicit_provider_status() -> None:
    class EmptyVerifiedCMIE:
        def contextualise(self, **kwargs: object) -> object:
            return (
                CMIEAdapter(None)
                .get_fallback_result(player_id=UUID("11111111-2222-3333-4444-555555555555"))
                .model_copy(update={"verification_status": CMIEVerificationStatus.VERIFIED})
            )

    adapter = CMIEAdapter(EmptyVerifiedCMIE())
    empty = adapter.execute(player_id=UUID("11111111-2222-3333-4444-555555555555"), matches=[])
    assert empty.verification_status == CMIEVerificationStatus.VERIFIED


def test_cmie_object_without_contract_method_is_a_failure() -> None:
    class WrongCMIE:
        pass

    output, record = CMIEAdapter(WrongCMIE()).execute_monitored(
        player_id=UUID("11111111-2222-3333-4444-555555555555"), matches=[]
    )
    assert output.verification_status == "UNVERIFIED"
    assert record.state == ExecutionState.FAILED


@pytest.mark.parametrize(
    "payload", ["=1+1", "+SUM(A1:A2)", "-2+3", "@SUM(A1:A2)", " \t\r=1+1", "\x00@cmd"]
)
def test_csv_escapes_formula_like_player_names(payload: str) -> None:
    report = MotherIntelligenceEngine().request_player_intelligence("Normal Player")
    report = report.model_copy(update={"canonical_name": payload})
    csv_text = MotherIntelligenceEngine.export_profile(report, format="csv")
    rows = list(csv.reader(io.StringIO(csv_text)))
    canonical = next(
        row[2] for row in rows if len(row) > 2 and row[:2] == ["IDENTIFICATION", "Canonical Name"]
    )
    assert canonical == "'" + payload
    # Export escaping does not mutate the source report or change JSON content.
    assert report.canonical_name == payload
    exported_json = json.loads(MotherIntelligenceEngine.export_profile(report, format="json"))
    assert exported_json["metadata"]["canonical_name"] == payload
