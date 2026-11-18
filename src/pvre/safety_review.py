"""Safety Review Interceptor and Multi-Source Conflict Preservation Engine for PVRE.

Implements TRD §9.5, PRD FR-PV7, and AI_INSTRUCTIONS R17, R18:
- Traps 8 explicit trigger conditions routing to REVIEW_REQUIRED.
- Preserves multi-source conflicting assertions without silent overwrite or averaging.
- Assembles standardized ReviewDossierContract payloads with evidence provenance,
  reason codes, and recommended manual checks.
"""

from __future__ import annotations

import copy
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import NAMESPACE_DNS, UUID, uuid4, uuid5

from src.contracts.provenance import VerificationRecord
from src.contracts.pvre import (
    EvidenceTier,
    PVRERequestContract,
    PVREReviewStatus,
    PVREVerificationStatus,
    ResearchConflict,
    ReviewDossierContract,
)

# Deterministic namespace for source identifiers
PVRE_SOURCE_NAMESPACE = uuid5(NAMESPACE_DNS, "pvre.rajasthanroyals.com/sources")


def map_claim_type_to_subject_type(claim_type: str) -> str:
    """Map claim type string to TRD canonical VerificationRecord subject_type."""
    ct = claim_type.upper()
    if any(k in ct for k in ("DOB", "BIRTH", "IDENTITY", "NAME", "ALIAS")):
        return "player_identity"
    if any(k in ct for k in ("MEMBERSHIP", "SQUAD", "RR")):
        return "player_membership"
    if "ELIGIBILITY" in ct:
        return "player_eligibility"
    if any(k in ct for k in ("STAT", "MATCH", "CAREER", "RUNS", "WICKETS")):
        return "career_participation"
    return "player_identity"


def normalize_source_id(raw_id: Any) -> UUID | int:
    """Normalize arbitrary source identifiers to UUID or int required by ReviewDossierContract.

    Preserves existing UUID or int instances directly; derives a deterministic UUIDv5
    for string identifiers to prevent silent contract validation failures.
    """
    if isinstance(raw_id, (UUID, int)):
        return raw_id
    if isinstance(raw_id, str):
        raw_str = raw_id.strip()
        try:
            return UUID(raw_str)
        except ValueError:
            pass
        try:
            return int(raw_str)
        except ValueError:
            pass
        return uuid5(PVRE_SOURCE_NAMESPACE, raw_str)
    return int(raw_id)


class SafetyReviewReasonCode(StrEnum):
    """Authoritative review reason codes for PVRE safety triggers (TRD §9.5, PRD FR-PV7).

    Captures all 8 mandatory trigger conditions and unindexed/unknown player scenarios.
    """

    # Trigger 1: Multiple candidate identities
    COLLISION_MULTIPLE_IDENTITIES = "COLLISION_MULTIPLE_IDENTITIES"
    IDENTITY_AMBIGUITY = "IDENTITY_AMBIGUITY"

    # Trigger 2: Date of birth / attribute conflicts across sources
    CONFLICT_DOB_RECORD = "CONFLICT_DOB_RECORD"
    DOB_CONFLICT = "DOB_CONFLICT"

    # Trigger 3: Contradictory RR relationship records
    CONFLICT_RR_MEMBERSHIP = "CONFLICT_RR_MEMBERSHIP"
    CONFLICTING_SQUAD_LISTS = "CONFLICTING_SQUAD_LISTS"

    # Trigger 4: Unverified or missing eligibility policy
    UNVERIFIED_ELIGIBILITY_POLICY = "UNVERIFIED_ELIGIBILITY_POLICY"
    ELIGIBILITY_UNVERIFIED = "ELIGIBILITY_UNVERIFIED"

    # Trigger 5: Statistical discrepancy across external sources
    CONFLICTING_CAREER_STATISTICS = "CONFLICTING_CAREER_STATISTICS"
    SOURCE_DISCREPANCY = "SOURCE_DISCREPANCY"
    CONFLICT_SCORECARD_VS_BBB = "CONFLICT_SCORECARD_VS_BBB"

    # Trigger 6: Low corroboration / unverified claims
    LOW_CORROBORATION = "LOW_CORROBORATION"
    UNVERIFIED_CLAIMS = "UNVERIFIED_CLAIMS"

    # Trigger 7: Career coverage gap / unindexed tournaments
    CAREER_COVERAGE_GAP = "CAREER_COVERAGE_GAP"
    DATA_GAP_UNINDEXED_TOURNAMENT = "DATA_GAP_UNINDEXED_TOURNAMENT"

    # Trigger 8: Restricted or unverified source data
    RESTRICTED_OR_UNVERIFIED_SOURCE = "RESTRICTED_OR_UNVERIFIED_SOURCE"
    RESTRICTED_SOURCE_UNAVAILABLE = "RESTRICTED_SOURCE_UNAVAILABLE"

    # Invariant: Unknown player absent from database
    UNKNOWN_PLAYER_NOT_IN_DATABASE = "UNKNOWN_PLAYER_NOT_IN_DATABASE"


# Authoritative mapping of recommended manual checks and missing evidence per reason code
RECOMMENDED_CHECKS_MAP: dict[str, list[str]] = {
    SafetyReviewReasonCode.COLLISION_MULTIPLE_IDENTITIES: [
        "Verify state cricket association registration records for disambiguation",
        "Inspect official government identity document (Passport/Aadhaar)",
        "Cross-reference player roster photographs and distinct CricSheet identifiers",
    ],
    SafetyReviewReasonCode.IDENTITY_AMBIGUITY: [
        "Verify state cricket association registration records for disambiguation",
        "Inspect official government identity document (Passport/Aadhaar)",
    ],
    SafetyReviewReasonCode.CONFLICT_DOB_RECORD: [
        "Inspect official municipal birth certificate or passport copy",
        "Verify BCCI central registration portal date of birth records",
        "Consult state cricket association registration dossier",
    ],
    SafetyReviewReasonCode.DOB_CONFLICT: [
        "Inspect official municipal birth certificate or passport copy",
        "Verify BCCI central registration portal date of birth records",
    ],
    SafetyReviewReasonCode.CONFLICT_RR_MEMBERSHIP: [
        "Inspect official IPL franchise registration ledger for disputed seasons",
        "Cross-reference BCCI contract registration sheets",
        "Verify official match referee team sheets for appearance vs squad-only status",
    ],
    SafetyReviewReasonCode.CONFLICTING_SQUAD_LISTS: [
        "Inspect official IPL franchise registration ledger for disputed seasons",
        "Cross-reference BCCI contract registration sheets",
    ],
    SafetyReviewReasonCode.UNVERIFIED_ELIGIBILITY_POLICY: [
        "Verify active IPL season player regulations and uncapped rules",
        "Confirm zero senior international caps via ICC official match registry",
        "Verify active eligibility policy ID and version promulgation status",
    ],
    SafetyReviewReasonCode.ELIGIBILITY_UNVERIFIED: [
        "Verify active IPL season player regulations and uncapped rules",
        "Confirm zero senior international caps via ICC official match registry",
    ],
    SafetyReviewReasonCode.CONFLICTING_CAREER_STATISTICS: [
        "Inspect official BCCI scorecard for disputed match fixtures",
        "Reconcile ball-by-ball delivery log against official match referee report",
        "Verify boundaries, extras, and wicket events against primary match sheet",
    ],
    SafetyReviewReasonCode.SOURCE_DISCREPANCY: [
        "Inspect official BCCI scorecard for disputed match fixtures",
        "Reconcile ball-by-ball delivery log against official match referee report",
    ],
    SafetyReviewReasonCode.CONFLICT_SCORECARD_VS_BBB: [
        "Quarantine delivery sequence in Service D and inspect official match report",
        "Reconcile scorecard run totals with sum of delivery events",
    ],
    SafetyReviewReasonCode.LOW_CORROBORATION: [
        "Obtain second independent scorecard or official tournament summary",
        "Verify claim across primary tier 1/2 sources before accepting assertion",
    ],
    SafetyReviewReasonCode.UNVERIFIED_CLAIMS: [
        "Obtain second independent scorecard or official tournament summary",
    ],
    SafetyReviewReasonCode.CAREER_COVERAGE_GAP: [
        "Retrieve missing tournament archive or verify player injury status in unindexed season",
        "Confirm player domestic availability via state association fixture sheets",
    ],
    SafetyReviewReasonCode.DATA_GAP_UNINDEXED_TOURNAMENT: [
        "Retrieve missing tournament archive or verify player injury status in unindexed season",
    ],
    SafetyReviewReasonCode.RESTRICTED_OR_UNVERIFIED_SOURCE: [
        "Perform authenticated per-claim lookup via authorized BCCI/ICC research portal",
        "Attach source provenance with timestamp, URL, and verification tier",
    ],
    SafetyReviewReasonCode.RESTRICTED_SOURCE_UNAVAILABLE: [
        "Perform authenticated per-claim lookup via authorized BCCI/ICC research portal",
    ],
    SafetyReviewReasonCode.UNKNOWN_PLAYER_NOT_IN_DATABASE: [
        "Search domestic association player registers and age-group tournament lists",
        "Perform affirmative eligibility verification before admitting to candidate pool",
    ],
}


def build_safety_review_dossier(
    subject_id: UUID | None,
    review_reason_codes: list[str],
    unresolved_claims: list[dict[str, Any]] | None = None,
    conflicting_source_ids: list[Any] | None = None,
    missing_evidence: list[str] | None = None,
    recommended_manual_checks: list[str] | None = None,
    subject_type: str = "player_research",
    dossier_id: UUID | None = None,
) -> ReviewDossierContract:
    """Compile a structured safety review dossier contract (TRD §9.5, PRD FR-PV7).

    Guarantees strict Pydantic v2 validation and populates comprehensive human-actionable
    checklists for reviewers.
    """
    clean_dossier_id = dossier_id or uuid4()
    claims = unresolved_claims or []

    # Extract source IDs from claims if not explicitly passed
    extracted_source_ids: list[UUID | int] = []
    if conflicting_source_ids:
        for sid in conflicting_source_ids:
            norm_sid = normalize_source_id(sid)
            if norm_sid not in extracted_source_ids:
                extracted_source_ids.append(norm_sid)
    else:
        for claim in claims:
            for sid_key in ("source_id", "primary_source_id", "conflicting_source_id"):
                val = claim.get(sid_key)
                if val is not None:
                    norm_val = normalize_source_id(val)
                    if norm_val not in extracted_source_ids:
                        extracted_source_ids.append(norm_val)
            for dict_key in ("source_a", "source_b"):
                val_dict = claim.get(dict_key)
                if isinstance(val_dict, dict) and "source_id" in val_dict:
                    norm_sub = normalize_source_id(val_dict["source_id"])
                    if norm_sub not in extracted_source_ids:
                        extracted_source_ids.append(norm_sub)

    # Compile recommended manual checks
    checks = list(recommended_manual_checks or [])
    for code in review_reason_codes:
        for check in RECOMMENDED_CHECKS_MAP.get(code, []):
            if check not in checks:
                checks.append(check)

    # Compile missing evidence list
    evidence_list = list(missing_evidence or [])
    if not evidence_list:
        for code in review_reason_codes:
            if "DOB" in code:
                evidence_list.append("Official government birth certificate")
            elif "IDENTITY" in code or "COLLISION" in code:
                evidence_list.append("BCCI registration photo and state player ID")
            elif "MEMBERSHIP" in code or "SQUAD" in code:
                evidence_list.append("Signed franchise contract sheet or official squad ledger")
            elif "ELIGIBILITY" in code:
                evidence_list.append("Official BCCI uncapped eligibility certificate")
            elif "STATISTICS" in code or "SCORECARD" in code:
                evidence_list.append("Official match referee scorecard report")
            elif "COVERAGE" in code or "GAP" in code:
                evidence_list.append("Archived competition fixture match sheets")
            elif "RESTRICTED" in code or "SOURCE" in code:
                evidence_list.append("Direct authenticated API response ledger")
            elif "UNKNOWN_PLAYER" in code:
                evidence_list.append("Verified domestic tournament registration form")

    return ReviewDossierContract(
        contract_version="DOSSIER-1.0.0",
        dossier_id=clean_dossier_id,
        subject_type=subject_type,
        subject_id=subject_id,
        review_status=PVREReviewStatus.REVIEW_REQUIRED.value,
        review_reason_codes=review_reason_codes,
        unresolved_claims=claims,
        conflicting_source_ids=extracted_source_ids,
        missing_evidence=evidence_list,
        recommended_manual_checks=checks,
    )


class SafetyReviewInterceptor:
    """Safety Review Interceptor handling 8 trigger conditions and multi-source conflict preservation.

    Enforces TRD §9.5, PRD FR-PV7, and AI_INSTRUCTIONS Tenet 2, Rules R17, R18:
    1. Identity collision / multiple candidate matches.
    2. DOB / biographical attribute conflicts across sources.
    3. RR franchise membership contradictions.
    4. Unverified or missing active season eligibility policy.
    5. Statistical discrepancy across external sources.
    6. Low corroboration / unverified claims.
    7. Career coverage gap / unindexed tournaments.
    8. Restricted or unavailable primary source data.
    """

    def __init__(self) -> None:
        self._conflicts: list[ResearchConflict] = []
        self._verification_records: dict[UUID, VerificationRecord] = {}
        self._dossiers: dict[UUID, ReviewDossierContract] = {}

    @property
    def conflicts(self) -> list[ResearchConflict]:
        """Return all preserved multi-source research conflicts."""
        return list(self._conflicts)

    @property
    def verification_records(self) -> list[VerificationRecord]:
        """Return all registered verification records."""
        return list(self._verification_records.values())

    @property
    def dossiers(self) -> list[ReviewDossierContract]:
        """Return all compiled review dossiers."""
        return list(self._dossiers.values())

    def preserve_conflicts(
        self,
        claim_type: str,
        subject_name: str,
        primary_source_id: Any,
        primary_value: Any,
        primary_tier: EvidenceTier | str,
        conflicting_source_id: Any,
        conflicting_value: Any,
        conflicting_tier: EvidenceTier | str,
        subject_id: UUID | None = None,
        detected_at: datetime | None = None,
        review_dossier_id: UUID | None = None,
    ) -> ResearchConflict:
        """Preserve multi-source conflicting assertions without silent overwrite or averaging.

        Enforces AI_INSTRUCTIONS R17:
        - NEVER overwrites existing claim.
        - NEVER calculates an average or synthetic compromise between conflicting values.
        - Persists both competing assertions with status 'CONFLICT'.
        """
        conflict_id = uuid4()
        now = detected_at or datetime.now(UTC)

        norm_primary_tier = (
            primary_tier.value if isinstance(primary_tier, EvidenceTier) else str(primary_tier)
        )
        norm_conflicting_tier = (
            conflicting_tier.value
            if isinstance(conflicting_tier, EvidenceTier)
            else str(conflicting_tier)
        )

        conflict = ResearchConflict(
            conflict_id=conflict_id,
            claim_type=claim_type,
            subject_name=subject_name,
            subject_id=subject_id,
            primary_source_id=normalize_source_id(primary_source_id),
            primary_value=copy.deepcopy(primary_value),
            primary_tier=norm_primary_tier,
            conflicting_source_id=normalize_source_id(conflicting_source_id),
            conflicting_value=copy.deepcopy(conflicting_value),
            conflicting_tier=norm_conflicting_tier,
            detected_at=now,
            resolution_status="UNRESOLVED",
            review_dossier_id=review_dossier_id,
        )

        # Create dual VerificationRecord rows with status 'CONFLICT'
        subj_type = map_claim_type_to_subject_type(claim_type)
        rec_primary = VerificationRecord(
            verification_id=uuid4(),
            subject_type=subj_type,
            subject_id=subject_id or conflict_id,
            source_url=f"source://{primary_source_id}",
            source_provider=str(primary_source_id),
            evidence_tier=1 if "TIER_1" in norm_primary_tier else 2,
            retrieval_ts=now,
            verification_status=PVREVerificationStatus.CONFLICT.value,
            confidence=0.5,
            notes=f"Conflicting claim on {claim_type}: primary={primary_value} vs conflicting={conflicting_value}",
        )

        rec_conflicting = VerificationRecord(
            verification_id=uuid4(),
            subject_type=subj_type,
            subject_id=subject_id or conflict_id,
            source_url=f"source://{conflicting_source_id}",
            source_provider=str(conflicting_source_id),
            evidence_tier=1 if "TIER_1" in norm_conflicting_tier else 3,
            retrieval_ts=now,
            verification_status=PVREVerificationStatus.CONFLICT.value,
            confidence=0.5,
            notes=f"Conflicting claim on {claim_type}: conflicting={conflicting_value} vs primary={primary_value}",
        )

        self._conflicts.append(conflict)
        self._verification_records[rec_primary.verification_id] = rec_primary
        self._verification_records[rec_conflicting.verification_id] = rec_conflicting

        return conflict

    # =========================================================================
    # Explicit Trigger Inspection Methods (Triggers 1 to 8)
    # =========================================================================

    def inspect_identity_collision(
        self,
        candidate_count: int,
        identity_status: str,
        query: str = "",
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """Trigger 1: Detect multiple candidate identities / identity collision."""
        if candidate_count > 1 or identity_status in ("UNRESOLVED", "PROVISIONAL", "MULTIPLE"):
            code = SafetyReviewReasonCode.COLLISION_MULTIPLE_IDENTITIES.value
            detail = {
                "claim_type": "IDENTITY_RESOLUTION",
                "candidate_count": candidate_count,
                "identity_status": identity_status,
                "raw_query": query,
            }
            return True, code, detail
        return False, None, None

    def inspect_dob_conflict(
        self,
        primary_dob: Any,
        conflicting_dob: Any,
        primary_source: Any = "source_primary",
        conflicting_source: Any = "source_secondary",
        player_name: str = "",
        player_id: UUID | None = None,
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """Trigger 2: Detect conflicting dates of birth across authoritative sources."""
        str_a = str(primary_dob).strip() if primary_dob is not None else ""
        str_b = str(conflicting_dob).strip() if conflicting_dob is not None else ""

        if str_a and str_b and str_a != str_b:
            code = SafetyReviewReasonCode.CONFLICT_DOB_RECORD.value
            conflict = self.preserve_conflicts(
                claim_type="DATE_OF_BIRTH",
                subject_name=player_name,
                primary_source_id=primary_source,
                primary_value=str_a,
                primary_tier=EvidenceTier.TIER_1_OFFICIAL,
                conflicting_source_id=conflicting_source,
                conflicting_value=str_b,
                conflicting_tier=EvidenceTier.TIER_2_COMMERCIAL,
                subject_id=player_id,
            )
            detail = {
                "claim_id": str(conflict.conflict_id),
                "claim_type": "DATE_OF_BIRTH",
                "source_a": {"source_id": str(primary_source), "value": str_a},
                "source_b": {"source_id": str(conflicting_source), "value": str_b},
            }
            return True, code, detail
        return False, None, None

    def inspect_rr_membership_contradiction(
        self,
        rr_relationship_state: str,
        rr_current_state: str,
        has_squad_inclusion: bool,
        has_appearance_conflict: bool = False,
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """Trigger 3: Detect contradictory RR relationship or squad records."""
        # e.g., NO_VERIFIED_RR_RELATIONSHIP but squad inclusion found, or CURRENT with no seasons
        if (
            rr_relationship_state == "NO_VERIFIED_RR_RELATIONSHIP" and has_squad_inclusion
        ) or has_appearance_conflict or rr_relationship_state == "RR_RELATIONSHIP_UNKNOWN":
            code = SafetyReviewReasonCode.CONFLICT_RR_MEMBERSHIP.value
            detail = {
                "claim_type": "RR_MEMBERSHIP",
                "rr_relationship_state": rr_relationship_state,
                "rr_current_state": rr_current_state,
                "has_squad_inclusion": has_squad_inclusion,
                "has_appearance_conflict": has_appearance_conflict,
            }
            return True, code, detail
        return False, None, None

    def inspect_eligibility_policy(
        self,
        ipl_uncapped_eligibility: str,
        policy_id: UUID | None = None,
        policy_verified: bool = True,
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """Trigger 4: Detect unverified, missing, or contradictory target-season eligibility policy."""
        if (
            ipl_uncapped_eligibility in ("NOT_ASSESSED", "ELIGIBILITY_UNVERIFIED")
            or policy_id is None
            or not policy_verified
        ):
            code = SafetyReviewReasonCode.UNVERIFIED_ELIGIBILITY_POLICY.value
            detail = {
                "claim_type": "ELIGIBILITY_POLICY",
                "ipl_uncapped_eligibility": ipl_uncapped_eligibility,
                "policy_id": str(policy_id) if policy_id else None,
                "policy_verified": policy_verified,
            }
            return True, code, detail
        return False, None, None

    def inspect_statistical_discrepancy(
        self,
        metric_name: str,
        value_a: Any,
        value_b: Any,
        source_a: Any = "source_a",
        source_b: Any = "source_b",
        player_name: str = "",
        player_id: UUID | None = None,
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """Trigger 5: Detect material statistical discrepancies across external sources."""
        if value_a != value_b:
            code = SafetyReviewReasonCode.CONFLICTING_CAREER_STATISTICS.value
            conflict = self.preserve_conflicts(
                claim_type=f"STATISTIC_{metric_name.upper()}",
                subject_name=player_name,
                primary_source_id=source_a,
                primary_value=value_a,
                primary_tier=EvidenceTier.TIER_2_COMMERCIAL,
                conflicting_source_id=source_b,
                conflicting_value=value_b,
                conflicting_tier=EvidenceTier.TIER_3_MEDIA,
                subject_id=player_id,
            )
            detail = {
                "claim_id": str(conflict.conflict_id),
                "claim_type": f"STATISTIC_{metric_name.upper()}",
                "source_a": {"source_id": str(source_a), "value": value_a},
                "source_b": {"source_id": str(source_b), "value": value_b},
            }
            return True, code, detail
        return False, None, None

    def inspect_low_corroboration(
        self,
        corroborating_source_count: int,
        minimum_required: int = 2,
        claim_description: str = "",
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """Trigger 6: Detect uncorroborated claims below minimum corroboration threshold."""
        if corroborating_source_count < minimum_required:
            code = SafetyReviewReasonCode.LOW_CORROBORATION.value
            detail = {
                "claim_type": "CORROBORATION_THRESHOLD",
                "sources_found": corroborating_source_count,
                "minimum_required": minimum_required,
                "claim_description": claim_description,
            }
            return True, code, detail
        return False, None, None

    def inspect_career_coverage_gap(
        self,
        coverage_state: str,
        missing_competitions: list[str] | None = None,
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """Trigger 7: Detect career coverage gaps or unindexed tournaments."""
        missing = missing_competitions or []
        if coverage_state in ("UNKNOWN", "REVIEW_REQUIRED") or len(missing) > 0:
            code = SafetyReviewReasonCode.CAREER_COVERAGE_GAP.value
            detail = {
                "claim_type": "CAREER_COVERAGE",
                "coverage_state": coverage_state,
                "missing_competitions": missing,
            }
            return True, code, detail
        return False, None, None

    def inspect_restricted_or_unverified_source(
        self,
        source_is_restricted: bool,
        has_verified_secondary: bool = False,
        source_name: str = "",
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """Trigger 8: Detect restricted or unavailable primary source data lacking secondary backup."""
        if source_is_restricted and not has_verified_secondary:
            code = SafetyReviewReasonCode.RESTRICTED_OR_UNVERIFIED_SOURCE.value
            detail = {
                "claim_type": "SOURCE_AVAILABILITY",
                "source_name": source_name,
                "source_is_restricted": source_is_restricted,
                "has_verified_secondary": has_verified_secondary,
            }
            return True, code, detail
        return False, None, None

    def inspect_unknown_player_absence(
        self,
        in_database: bool,
        player_name: str = "",
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """Invariant: Detect unknown player absent from internal database (AI_INSTRUCTIONS R13)."""
        if not in_database:
            code = SafetyReviewReasonCode.UNKNOWN_PLAYER_NOT_IN_DATABASE.value
            detail = {
                "claim_type": "DATABASE_ABSENCE",
                "player_name": player_name,
                "in_database": False,
            }
            return True, code, detail
        return False, None, None

    # =========================================================================
    # Comprehensive Request Evaluation & Dossier Interception
    # =========================================================================

    def evaluate_request(
        self,
        request: PVRERequestContract | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> tuple[bool, ReviewDossierContract | None]:
        """Evaluate inbound request and external context against all 8 safety review triggers.

        Returns (is_review_required, dossier_or_none).
        """
        ctx = context or {}
        req_dict: dict[str, Any] = (
            request.model_dump() if isinstance(request, PVRERequestContract) else request
        )

        reason_codes: list[str] = []
        unresolved_claims: list[dict[str, Any]] = []
        conflicting_source_ids: list[Any] = []
        missing_evidence: list[str] = []

        # 1. Identity Ambiguity / Collision
        candidate_count = ctx.get("candidate_count", 1)
        identity_status = req_dict.get("identity_status", "RESOLVED")
        hit, code, det = self.inspect_identity_collision(
            candidate_count, identity_status, req_dict.get("canonical_name", "")
        )
        if hit and code and det:
            reason_codes.append(code)
            unresolved_claims.append(det)

        # 2. DOB Conflict
        primary_dob = ctx.get("primary_dob")
        conflicting_dob = ctx.get("conflicting_dob")
        if primary_dob and conflicting_dob:
            hit, code, det = self.inspect_dob_conflict(
                primary_dob,
                conflicting_dob,
                primary_source=ctx.get("primary_dob_source", "S18A"),
                conflicting_source=ctx.get("conflicting_dob_source", "S20A"),
                player_name=req_dict.get("canonical_name", ""),
                player_id=req_dict.get("player_id"),
            )
            if hit and code and det:
                reason_codes.append(code)
                unresolved_claims.append(det)
                conflicting_source_ids.extend([
                    ctx.get("primary_dob_source", "S18A"),
                    ctx.get("conflicting_dob_source", "S20A"),
                ])

        # 3. RR Membership Contradiction
        rr_rel = req_dict.get("rr_relationship_state", "NO_VERIFIED_RR_RELATIONSHIP")
        rr_curr = req_dict.get("rr_current_state", "NOT_CURRENT")
        squad_inc = ctx.get("has_squad_inclusion", False)
        app_conf = ctx.get("has_appearance_conflict", False)
        hit, code, det = self.inspect_rr_membership_contradiction(
            rr_rel, rr_curr, squad_inc, app_conf
        )
        if hit and code and det:
            reason_codes.append(code)
            unresolved_claims.append(det)

        # 4. Eligibility Policy Verification
        uncapped_elig = req_dict.get("ipl_uncapped_eligibility", "NOT_ASSESSED")
        pol_id = ctx.get("policy_id")
        pol_ver = ctx.get("policy_verified", True)
        hit, code, det = self.inspect_eligibility_policy(uncapped_elig, pol_id, pol_ver)
        if hit and code and det:
            reason_codes.append(code)
            unresolved_claims.append(det)

        # 5. Statistical Discrepancy
        stat_name = ctx.get("stat_discrepancy_metric")
        if stat_name:
            val_a = ctx.get("stat_val_a")
            val_b = ctx.get("stat_val_b")
            hit, code, det = self.inspect_statistical_discrepancy(
                stat_name,
                val_a,
                val_b,
                source_a=ctx.get("stat_src_a", "S5"),
                source_b=ctx.get("stat_src_b", "S18B"),
                player_name=req_dict.get("canonical_name", ""),
                player_id=req_dict.get("player_id"),
            )
            if hit and code and det:
                reason_codes.append(code)
                unresolved_claims.append(det)
                conflicting_source_ids.extend([
                    ctx.get("stat_src_a", "S5"),
                    ctx.get("stat_src_b", "S18B"),
                ])

        # 6. Low Corroboration
        corr_count = ctx.get("corroborating_source_count")
        if corr_count is not None:
            hit, code, det = self.inspect_low_corroboration(
                corr_count,
                minimum_required=ctx.get("minimum_corroboration", 2),
                claim_description=ctx.get("claim_description", ""),
            )
            if hit and code and det:
                reason_codes.append(code)
                unresolved_claims.append(det)

        # 7. Career Coverage Gap
        cov_state = ctx.get("career_coverage_state", "COMPLETE_WITHIN_VERIFIED_SOURCES")
        missing_comps = ctx.get("missing_competitions", [])
        hit, code, det = self.inspect_career_coverage_gap(cov_state, missing_comps)
        if hit and code and det:
            reason_codes.append(code)
            unresolved_claims.append(det)

        # 8. Restricted or Unavailable Primary Source
        src_restricted = ctx.get("source_is_restricted", False)
        if src_restricted:
            has_sec = ctx.get("has_verified_secondary", False)
            hit, code, det = self.inspect_restricted_or_unverified_source(
                src_restricted, has_sec, ctx.get("source_name", "bcci_restricted")
            )
            if hit and code and det:
                reason_codes.append(code)
                unresolved_claims.append(det)

        # Invariant: Unknown Player Absent from Database
        in_db = ctx.get("in_database", True)
        if (not in_db or req_dict.get("player_id") is None) and "UNKNOWN_PLAYER_NOT_IN_DATABASE" not in reason_codes:
            hit, code, det = self.inspect_unknown_player_absence(
                False, req_dict.get("canonical_name", "")
            )
            if hit and code and det:
                reason_codes.append(code)
                unresolved_claims.append(det)

        if not reason_codes:
            return False, None

        # Build comprehensive ReviewDossierContract
        dossier = build_safety_review_dossier(
            subject_id=req_dict.get("player_id"),
            review_reason_codes=reason_codes,
            unresolved_claims=unresolved_claims,
            conflicting_source_ids=conflicting_source_ids,
            missing_evidence=missing_evidence,
            subject_type="player_research",
        )
        self._dossiers[dossier.dossier_id] = dossier
        return True, dossier


__all__ = [
    "SafetyReviewReasonCode",
    "RECOMMENDED_CHECKS_MAP",
    "normalize_source_id",
    "build_safety_review_dossier",
    "SafetyReviewInterceptor",
]
