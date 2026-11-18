"""Confidence Reconciliation & Verification Aggregation for MIE.

Implements Bayesian confidence score combination, conflict detection, and
strict AC-15 calibration gating (numeric confidence exposed ONLY if calibrated=True).
"""

from __future__ import annotations

from collections.abc import Mapping

from src.contracts.pvre import (
    CareerCoverageState,
    PlayerCappedStatus,
)
from src.contracts.tmve import (
    EligibilityStatus,
    RRCurrentState,
    RRRelationshipState,
)
from src.mie.contracts import (
    AggregatedVerificationStatus,
    CMIEVerificationStatus,
    EngineExecutionRecord,
    ExecutionState,
    OverallVerificationStatus,
)


class ConfidenceReconciler:
    """Reconciles multi-engine confidence signals and determines overall verification status."""

    @staticmethod
    def aggregate_verification_status(
        identity_status: str,
        resolution_tier: int | None,
        rr_relationship_state: RRRelationshipState | str,
        rr_current_state: RRCurrentState | str,
        ipl_uncapped_eligibility: EligibilityStatus | str,
        player_capped_status: PlayerCappedStatus | str,
        career_coverage_state: CareerCoverageState | str,
        review_reason_codes: list[str] | None = None,
        cap_evidence_verified: bool = False,
        candidate_evidence_present: bool = False,
        cmie_verification_status: CMIEVerificationStatus | str = CMIEVerificationStatus.UNVERIFIED,
        required_source_ids: list[str] | None = None,
        execution_records: Mapping[str, EngineExecutionRecord] | None = None,
    ) -> AggregatedVerificationStatus:
        """Synthesize multi-dimensional verification state into an AggregatedVerificationStatus.

        Confidence remains unset until an approved, versioned calibrator is configured.
        Verification is fail-closed across required evidence and execution states.
        """
        reasons = list(review_reason_codes or [])
        requires_review = False
        required_engine_names = (
            "PIRE",
            "CDCRE_CANDIDATE_DISCOVERY",
            "TMVE",
            "CDCRE",
            "CPPAE",
            "CMIE",
            "PVRE",
        )
        records = execution_records or {}
        for engine_name in required_engine_names:
            record = records.get(engine_name)
            if record is None:
                reasons.append(f"REQUIRED_EVIDENCE_MISSING_{engine_name}")
            elif record.state in (
                ExecutionState.FAILED,
                ExecutionState.SKIPPED,
                ExecutionState.DEGRADED,
            ):
                reasons.append(f"REQUIRED_EVIDENCE_{record.state.value}_{engine_name}")
        rel_state = (
            rr_relationship_state
            if isinstance(rr_relationship_state, RRRelationshipState)
            else RRRelationshipState(str(rr_relationship_state))
        )
        cur_state = (
            rr_current_state
            if isinstance(rr_current_state, RRCurrentState)
            else RRCurrentState(str(rr_current_state))
        )
        elig_status = (
            ipl_uncapped_eligibility
            if isinstance(ipl_uncapped_eligibility, EligibilityStatus)
            else EligibilityStatus(str(ipl_uncapped_eligibility))
        )
        cap_status = (
            player_capped_status
            if isinstance(player_capped_status, PlayerCappedStatus)
            else PlayerCappedStatus(str(player_capped_status))
        )
        cov_state = (
            career_coverage_state
            if isinstance(career_coverage_state, CareerCoverageState)
            else CareerCoverageState(str(career_coverage_state))
        )
        cmie_status = (
            cmie_verification_status
            if isinstance(cmie_verification_status, CMIEVerificationStatus)
            else CMIEVerificationStatus(str(cmie_verification_status))
        )
        if cmie_status == CMIEVerificationStatus.CONFLICT:
            reasons.append("CMIE_EVIDENCE_CONFLICT")
        elif cmie_status != CMIEVerificationStatus.VERIFIED:
            reasons.append(f"CMIE_EVIDENCE_{cmie_status.value}")

        # 1. Inspect for conflicts and safety review triggers
        if "CONFLICT" in reasons or any("CONFLICT" in r for r in reasons):
            overall = OverallVerificationStatus.CONFLICT
            requires_review = True
        elif (
            identity_status == "UNRESOLVED"
            or cov_state == CareerCoverageState.REVIEW_REQUIRED
            or len(reasons) > 0
        ):
            overall = OverallVerificationStatus.REVIEW_REQUIRED
            requires_review = True
        elif identity_status == "PROVISIONAL":
            overall = OverallVerificationStatus.PROVISIONAL
        elif (
            rel_state
            in (
                RRRelationshipState.HISTORICAL_RR_APPEARANCE,
                RRRelationshipState.HISTORICAL_RR_SQUAD_ONLY,
                RRRelationshipState.NO_VERIFIED_RR_RELATIONSHIP,
            )
            and elig_status
            in (EligibilityStatus.VERIFIED_ELIGIBLE, EligibilityStatus.VERIFIED_NOT_ELIGIBLE)
            and identity_status == "RESOLVED"
            and cap_status in (PlayerCappedStatus.CAPPED, PlayerCappedStatus.UNCAPPED)
            and cap_evidence_verified
            and candidate_evidence_present
            and cmie_status == CMIEVerificationStatus.VERIFIED
            and cov_state == CareerCoverageState.COMPLETE_WITHIN_VERIFIED_SOURCES
            and bool(required_source_ids)
            and all(
                record.state in (ExecutionState.SUCCESS, ExecutionState.MOCK_FIXTURE)
                for name, record in records.items()
                if name in required_engine_names
            )
            and all(name in records for name in required_engine_names)
        ):
            overall = OverallVerificationStatus.VERIFIED
        elif elig_status == EligibilityStatus.NOT_ASSESSED:
            overall = OverallVerificationStatus.NOT_ASSESSED
        else:
            overall = OverallVerificationStatus.UNVERIFIED

        return AggregatedVerificationStatus(
            overall_status=overall,
            identity_status=str(identity_status),
            resolution_tier=resolution_tier,
            rr_relationship_state=rel_state,
            rr_current_state=cur_state,
            ipl_uncapped_eligibility=elig_status,
            player_capped_status=cap_status,
            career_coverage_state=cov_state,
            calibrated_confidence=None,
            is_calibrated=False,
            requires_human_review=requires_review,
            review_reason_codes=reasons,
            contradictory_evidence_count=len(
                [r for r in reasons if "CONFLICT" in r or "DISCREPANCY" in r]
            ),
        )
