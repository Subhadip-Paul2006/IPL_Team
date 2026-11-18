"""Provenance and Human Review Integration Service for TMVE.

Implements TRD §4.5, §9.5, and §11 requirements:
- Attach source records and verified evidence to membership/eligibility claims.
- Preserve conflicting evidence without silent overwrite (Zero Silent Resolution).
- Build standardized ReviewDossierContract safety dossiers.
- Route ambiguous negative claims to human review queue.
- Full integration with PIRE HumanReviewQueue and ServiceBoundary contracts.
"""

from __future__ import annotations

import copy
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from src.contracts.provenance import VerificationRecord
from src.contracts.tmve import ReviewDossierContract
from src.pire.review_queue import HumanReviewQueue
from src.services.base import ServiceBoundary


class ReviewReasonCode(StrEnum):
    """Authoritative review reason codes for TMVE safety triggers (TRD §4.5, §9.5)."""

    AMBIGUOUS_NEGATIVE_CLAIM = "AMBIGUOUS_NEGATIVE_CLAIM"
    INCOMPLETE_CAREER_WINDOW = "INCOMPLETE_CAREER_WINDOW"
    CONFLICTING_SQUAD_LISTS = "CONFLICTING_SQUAD_LISTS"
    BORDER_CASE_DATA = "BORDER_CASE_DATA"
    UNVERIFIED_SQUAD_APPEARANCE = "UNVERIFIED_SQUAD_APPEARANCE"
    MISSING_EVIDENCE_PROVENANCE = "MISSING_EVIDENCE_PROVENANCE"
    DISCREPANT_EXTERNAL_RECORDS = "DISCREPANT_EXTERNAL_RECORDS"
    AMBIGUOUS_NOC_STATUS = "AMBIGUOUS_NOC_STATUS"
    PARTIAL_SEASON_GAP = "PARTIAL_SEASON_GAP"
    DISCREPANT_ACTIVE_YEARS = "DISCREPANT_ACTIVE_YEARS"


class ProvenanceReviewService(ServiceBoundary):
    """Authoritative service for provenance tracking, conflict preservation, and review dossiers."""

    def __init__(self, queue: HumanReviewQueue | None = None) -> None:
        self._queue: HumanReviewQueue = queue if queue is not None else HumanReviewQueue()
        self._verifications: dict[UUID, VerificationRecord] = {}
        self._dossiers: dict[UUID, ReviewDossierContract] = {}
        self._conflicts_history: list[dict[str, Any]] = []
        self._dossier_queue_mapping: dict[UUID, str] = {}

    def get_service_name(self) -> str:
        """Return the canonical service identifier."""
        return "provenance_review_service"

    def health_check(self) -> dict[str, Any]:
        """Perform service health inspection and return diagnostic status dictionary."""
        return {
            "service": self.get_service_name(),
            "status": "healthy",
            "verifications_count": len(self._verifications),
            "dossiers_count": len(self._dossiers),
            "pending_queue_items": self._queue.pending_count,
            "conflicts_count": len(self._conflicts_history),
        }

    @property
    def queue(self) -> HumanReviewQueue:
        """Return the underlying HumanReviewQueue instance."""
        return self._queue

    @staticmethod
    def _normalize_subject_type(raw: str) -> str:
        """Normalize subject type aliases to TRD Entity 3 canonical names."""
        cleaned = raw.strip().lower()
        mapping = {
            "membership": "player_membership",
            "player_membership": "player_membership",
            "eligibility": "player_eligibility",
            "player_eligibility": "player_eligibility",
            "identity": "player_identity",
            "player_identity": "player_identity",
            "career": "career_participation",
            "career_participation": "career_participation",
            "source": "source_record",
            "source_record": "source_record",
            "team": "team_participation",
            "team_participation": "team_participation",
        }
        return mapping.get(cleaned, raw)

    def attach_verification(
        self,
        subject_type: str,
        subject_id: UUID,
        evidence_tier: int,
        source_provider: str,
        source_url: str | None = None,
        confidence: float | None = 1.0,
        *,
        claim: dict[str, Any] | None = None,
        verification_status: str = "VERIFIED",
        notes: str | None = None,
        source_record_id: UUID | None = None,
        data_source_id: UUID | None = None,
    ) -> VerificationRecord:
        """Attach a verified evidence provenance record to a subject and optional claim dict.

        Enforces mandatory provenance linking: subject_type, subject_id, evidence_tier,
        source_provider, retrieval_ts, and confidence.
        """
        norm_subject_type = self._normalize_subject_type(subject_type)

        if not (1 <= evidence_tier <= 5):
            raise ValueError(f"evidence_tier must be between 1 and 5, got {evidence_tier}")

        if confidence is not None and not (0.0 <= confidence <= 1.0):
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {confidence}")

        record = VerificationRecord(
            verification_id=uuid4(),
            subject_type=norm_subject_type,
            subject_id=subject_id,
            source_record_id=source_record_id,
            data_source_id=data_source_id,
            source_url=source_url,
            source_provider=source_provider,
            evidence_tier=evidence_tier,
            retrieval_ts=datetime.now(UTC),
            verification_status=verification_status,
            confidence=confidence,
            notes=notes,
        )

        if claim is not None:
            claim.setdefault("evidence_verification_ids", [])
            if record.verification_id not in claim["evidence_verification_ids"]:
                claim["evidence_verification_ids"].append(record.verification_id)
            claim["verification_id"] = record.verification_id
            prov_entry = {
                "verification_id": str(record.verification_id),
                "subject_type": record.subject_type,
                "subject_id": str(record.subject_id),
                "evidence_tier": record.evidence_tier,
                "source_provider": record.source_provider,
                "retrieval_ts": record.retrieval_ts.isoformat(),
                "confidence": record.confidence,
                "source_url": record.source_url,
            }
            claim.setdefault("provenance", []).append(prov_entry)

        self._verifications[record.verification_id] = record
        return record

    def preserve_conflicts(
        self,
        existing_claim: dict[str, Any],
        conflicting_claim: dict[str, Any],
    ) -> dict[str, Any]:
        """Preserve conflicting evidence without silent overwrite or loss of claims.

        Guarantees TRD §9.5 and §11 Zero Silent Resolution invariant by explicitly
        capturing both claims, highlighting field-level discrepancies, and marking
        the conflict for human analyst review.
        """
        conflict_id = uuid4()

        conflicting_fields: list[dict[str, Any]] = []
        ignored_keys = {"timestamp", "created_at", "conflict_id", "retrieval_ts"}
        all_keys = set(existing_claim.keys()) | set(conflicting_claim.keys())
        for key in sorted(all_keys):
            if key in ignored_keys:
                continue
            val_exist = existing_claim.get(key)
            val_conflict = conflicting_claim.get(key)
            if val_exist != val_conflict:
                conflicting_fields.append({
                    "field": key,
                    "existing_value": copy.deepcopy(val_exist),
                    "conflicting_value": copy.deepcopy(val_conflict),
                })

        extracted_source_ids: list[UUID | int] = []
        for claim in (existing_claim, conflicting_claim):
            for sid_key in ("source_id", "source_record_id", "data_source_id", "verification_id"):
                val = claim.get(sid_key)
                if isinstance(val, (UUID, int)):
                    if val not in extracted_source_ids:
                        extracted_source_ids.append(val)
                elif isinstance(val, str):
                    try:
                        u = UUID(val)
                        if u not in extracted_source_ids:
                            extracted_source_ids.append(u)
                    except ValueError:
                        try:
                            i = int(val)
                            if i not in extracted_source_ids:
                                extracted_source_ids.append(i)
                        except ValueError:
                            pass
            for list_key in ("evidence_verification_ids", "conflicting_source_ids", "source_ids"):
                val_list = claim.get(list_key)
                if isinstance(val_list, list):
                    for item_val in val_list:
                        if isinstance(item_val, (UUID, int)) and item_val not in extracted_source_ids:
                            extracted_source_ids.append(item_val)
                        elif isinstance(item_val, str):
                            try:
                                u = UUID(item_val)
                                if u not in extracted_source_ids:
                                    extracted_source_ids.append(u)
                            except ValueError:
                                try:
                                    i = int(item_val)
                                    if i not in extracted_source_ids:
                                        extracted_source_ids.append(i)
                                except ValueError:
                                    pass

        preserved: dict[str, Any] = {
            "conflict_id": str(conflict_id),
            "conflict_status": "UNRESOLVED_CONFLICT",
            "conflict_detected": True,
            "requires_human_review": True,
            "resolution_decision": "PRESERVED_FOR_HUMAN_REVIEW",
            "existing_claim": copy.deepcopy(existing_claim),
            "conflicting_claim": copy.deepcopy(conflicting_claim),
            "conflicting_fields": conflicting_fields,
            "conflicting_source_ids": extracted_source_ids,
            "preserved_at": datetime.now(UTC).isoformat(),
        }

        self._conflicts_history.append(preserved)

        subject_label = str(
            existing_claim.get("player_name")
            or existing_claim.get("player_id")
            or existing_claim.get("subject_id")
            or "Unknown Subject"
        )
        conflicting_ids_str = [str(sid) for sid in extracted_source_ids]
        self._queue.record_conflict(
            subject_name=subject_label,
            conflicting_ids=conflicting_ids_str,
            conflicting_sources=[
                str(existing_claim.get("source_provider") or "Existing Claim"),
                str(conflicting_claim.get("source_provider") or "Conflicting Claim"),
            ],
            conflict_type="MEMBERSHIP_CLAIM_DISCREPANCY",
            evidence={
                "conflict_id": str(conflict_id),
                "conflicting_fields": conflicting_fields,
            },
        )

        return preserved

    def build_review_dossier(
        self,
        subject_type: str,
        subject_id: UUID,
        reason_codes: list[str],
        conflicts: list[dict[str, Any]] | None = None,
        missing_evidence: list[str] | None = None,
        recommended_checks: list[str] | None = None,
        *,
        conflicting_source_ids: list[UUID | int] | None = None,
        dossier_id: UUID | None = None,
        unresolved_claims: list[dict[str, Any]] | None = None,
    ) -> ReviewDossierContract:
        """Construct a standardized ReviewDossierContract for human review workflows."""
        norm_subject_type = self._normalize_subject_type(subject_type)
        assigned_dossier_id = dossier_id or uuid4()
        reasons = list(reason_codes) if reason_codes else ["REVIEW_REQUIRED_GENERIC"]

        unresolved: list[dict[str, Any]] = []
        if unresolved_claims:
            unresolved.extend(copy.deepcopy(unresolved_claims))
        if conflicts:
            unresolved.extend(copy.deepcopy(conflicts))

        extracted_source_ids: list[UUID | int] = []
        if conflicting_source_ids:
            for sid in conflicting_source_ids:
                if isinstance(sid, (UUID, int)) and sid not in extracted_source_ids:
                    extracted_source_ids.append(sid)

        for item in unresolved:
            if not isinstance(item, dict):
                continue
            item_sids = item.get("conflicting_source_ids")
            if isinstance(item_sids, list):
                for sid in item_sids:
                    if isinstance(sid, (UUID, int)) and sid not in extracted_source_ids:
                        extracted_source_ids.append(sid)
                    elif isinstance(sid, str):
                        try:
                            u = UUID(sid)
                            if u not in extracted_source_ids:
                                extracted_source_ids.append(u)
                        except ValueError:
                            try:
                                i = int(sid)
                                if i not in extracted_source_ids:
                                    extracted_source_ids.append(i)
                            except ValueError:
                                pass
            for single_key in ("source_id", "data_source_id", "verification_id"):
                val = item.get(single_key)
                if isinstance(val, (UUID, int)) and val not in extracted_source_ids:
                    extracted_source_ids.append(val)
                elif isinstance(val, str):
                    try:
                        u = UUID(val)
                        if u not in extracted_source_ids:
                            extracted_source_ids.append(u)
                    except ValueError:
                        try:
                            i = int(val)
                            if i not in extracted_source_ids:
                                extracted_source_ids.append(i)
                        except ValueError:
                            pass

        missing = list(missing_evidence) if missing_evidence else []

        checks = list(recommended_checks) if recommended_checks else []
        if not checks:
            for rc in reasons:
                rc_upper = str(rc).upper()
                if "NOC" in rc_upper or "ELIGIBILITY" in rc_upper:
                    check_desc = "Confirm NOC submission timestamp with home board and IPL operations desk"
                    if check_desc not in checks:
                        checks.append(check_desc)
                if "NEGATIVE" in rc_upper or ("AMBIGUOUS" in rc_upper and "NOC" not in rc_upper):
                    check_desc = "Verify player career timeline against official BCCI match archives"
                    if check_desc not in checks:
                        checks.append(check_desc)
                if "SQUAD" in rc_upper or "CONFLICT" in rc_upper:
                    check_desc = "Cross-reference official franchise squad registration filings with IPL governing council"
                    if check_desc not in checks:
                        checks.append(check_desc)
                if "CAREER" in rc_upper or "GAP" in rc_upper:
                    check_desc = "Inspect official domestic/international scorecards for activity during gap years"
                    if check_desc not in checks:
                        checks.append(check_desc)
            if not checks:
                checks.append("Conduct manual analyst verification against primary records")

        dossier = ReviewDossierContract(
            contract_version="DOSSIER-1.0.0",
            dossier_id=assigned_dossier_id,
            subject_type=norm_subject_type,
            subject_id=subject_id,
            review_status="REVIEW_REQUIRED",
            review_reason_codes=reasons,
            unresolved_claims=unresolved,
            conflicting_source_ids=extracted_source_ids,
            missing_evidence=missing,
            recommended_manual_checks=checks,
        )

        self._dossiers[dossier.dossier_id] = dossier
        return dossier

    def route_negative_claim(
        self,
        player_id: UUID,
        reason_codes: list[str],
        evidence_summary: dict[str, Any],
    ) -> ReviewDossierContract:
        """Route ambiguous negative relationship claims to human review dossier and queue.

        Adheres strictly to TRD §4.5: If evidence is incomplete or negative criteria
        cannot be verified decisively, the claim is NOT silently accepted or dropped;
        it is staged into a ReviewDossierContract and enqueued to HumanReviewQueue.
        """
        if not isinstance(player_id, UUID):
            player_id = UUID(str(player_id))

        reasons = list(reason_codes) if reason_codes else []
        if not reasons:
            reasons = [ReviewReasonCode.AMBIGUOUS_NEGATIVE_CLAIM]
        elif ReviewReasonCode.AMBIGUOUS_NEGATIVE_CLAIM not in reasons and not any(
            "NEGATIVE" in r for r in reasons
        ):
            reasons.insert(0, ReviewReasonCode.AMBIGUOUS_NEGATIVE_CLAIM)

        missing_raw = evidence_summary.get("missing_evidence", [])
        if isinstance(missing_raw, list):
            missing_evidence = [str(m) for m in missing_raw]
        elif isinstance(missing_raw, str):
            missing_evidence = [missing_raw]
        else:
            missing_evidence = []

        recommended_checks_raw = (
            evidence_summary.get("recommended_checks")
            or evidence_summary.get("recommended_manual_checks")
            or []
        )
        if isinstance(recommended_checks_raw, list) and recommended_checks_raw:
            recommended_checks = [str(c) for c in recommended_checks_raw]
        else:
            recommended_checks = [
                "Audit player match timeline against official BCCI match scorecards",
                "Cross-reference player registration receipt with franchise historical filings",
                "Verify whether player was registered under replacement or net-bowler category",
            ]

        conflicts_raw = evidence_summary.get("conflicts")
        if isinstance(conflicts_raw, list):
            conflicts = conflicts_raw
        else:
            conflicts = [copy.deepcopy(evidence_summary)]

        subject_type = str(evidence_summary.get("subject_type") or "player_membership")

        dossier = self.build_review_dossier(
            subject_type=subject_type,
            subject_id=player_id,
            reason_codes=reasons,
            conflicts=conflicts,
            missing_evidence=missing_evidence,
            recommended_checks=recommended_checks,
        )

        self.submit_dossier_to_queue(dossier)
        return dossier

    def submit_dossier_to_queue(
        self,
        dossier: ReviewDossierContract,
        queue: Any | None = None,
    ) -> str:
        """Submit a ReviewDossierContract to the HumanReviewQueue or custom queue.

        Returns the generated queue item ID string.
        """
        target_queue = queue if queue is not None else self._queue

        player_name = None
        for claim in dossier.unresolved_claims:
            if isinstance(claim, dict) and "player_name" in claim:
                player_name = str(claim["player_name"])
                break

        raw_name = player_name or f"{dossier.subject_type}:{dossier.subject_id}"
        source_id = f"TMVE_DOSSIER_{dossier.dossier_id}"
        external_id = str(dossier.subject_id)
        candidate_ids = [str(cid) for cid in dossier.conflicting_source_ids]
        trigger_reason = "; ".join(dossier.review_reason_codes) or "TMVE review required"

        if hasattr(target_queue, "enqueue"):
            item = target_queue.enqueue(
                raw_name=raw_name,
                source_id=source_id,
                external_id=external_id,
                context_teams=["Rajasthan Royals"],
                context_comp="IPL",
                candidate_ids=candidate_ids,
                trigger_reason=trigger_reason,
            )
            queue_id = str(getattr(item, "queue_id", uuid4()))
        elif hasattr(target_queue, "append"):
            queue_id = str(uuid4())
            target_queue.append({
                "queue_id": queue_id,
                "raw_name": raw_name,
                "source_id": source_id,
                "dossier": dossier,
            })
        elif hasattr(target_queue, "put"):
            queue_id = str(uuid4())
            target_queue.put(dossier)
        else:
            queue_id = str(uuid4())

        self._dossier_queue_mapping[dossier.dossier_id] = queue_id
        return queue_id

    def get_verification(self, verification_id: UUID) -> VerificationRecord | None:
        """Retrieve a stored VerificationRecord by verification_id."""
        return self._verifications.get(verification_id)

    def get_dossier(self, dossier_id: UUID) -> ReviewDossierContract | None:
        """Retrieve a stored ReviewDossierContract by dossier_id."""
        return self._dossiers.get(dossier_id)

    def list_verifications(self) -> list[VerificationRecord]:
        """Return all tracked VerificationRecord instances."""
        return list(self._verifications.values())

    def list_dossiers(self) -> list[ReviewDossierContract]:
        """Return all tracked ReviewDossierContract instances."""
        return list(self._dossiers.values())


__all__ = [
    "ProvenanceReviewService",
    "ReviewReasonCode",
]
