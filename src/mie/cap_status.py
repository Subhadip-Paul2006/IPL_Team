"""Fail-closed verification of cap evidence against persisted provenance records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from src.contracts.provenance import SourceRecord, VerificationRecord
from src.contracts.pvre import PlayerCappedStatus, VerificationStatus
from src.mie.contracts import CappedStatusEvidence
from src.mie.evidence_repository import EvidenceRepository


@dataclass(frozen=True)
class CapSourceAuthority:
    """Code-registered cap authority; never populated from a provider response."""

    authority_id: str
    source_ids: frozenset[UUID]
    senior_competitions: frozenset[str]
    complete_coverage: bool = False
    max_evidence_age_days: int = 365


class CapStatusEvidenceVerifier:
    """Validate provider assertions using repository rows and a trusted authority map.

    The production default has no registered cap authorities. Test and future
    deployment configurations may construct a verifier with a reviewed registry.
    """

    def __init__(
        self,
        repository: EvidenceRepository | None,
        authorities: Mapping[str, CapSourceAuthority] | None = None,
    ) -> None:
        self._repository = repository
        self._authorities = dict(authorities or {})

    def verify(self, player_id: UUID, evidence: CappedStatusEvidence) -> CappedStatusEvidence:
        """Return evidence only when authority, source, record, identity and scope validate."""
        unknown = self._unknown()
        # A conflict is a review signal, not a positive cap-status claim. Preserve
        # it even when no verification authority is configured so that fail-closed
        # verification does not erase contradictory evidence from the report.
        if evidence.verification_status == VerificationStatus.CONFLICT:
            return CappedStatusEvidence(
                status=PlayerCappedStatus.UNVERIFIED,
                verification_status=VerificationStatus.CONFLICT,
                conflicting_source_ids=list(evidence.conflicting_source_ids),
            )
        authority_id = evidence.provider_authority_id
        authority = self._authorities.get(authority_id or "")
        if authority is None or self._repository is None:
            return unknown
        if evidence.verification_status != VerificationStatus.VERIFIED:
            return unknown
        if not evidence.source_record_ids or not evidence.verification_record_ids:
            return unknown

        try:
            source_ids = [UUID(value) for value in evidence.source_record_ids]
            verification_ids = [UUID(value) for value in evidence.verification_record_ids]
        except (ValueError, TypeError):
            return unknown
        if len(set(source_ids)) != len(source_ids) or len(set(verification_ids)) != len(
            verification_ids
        ):
            return unknown

        sources = [self._repository.get_source_record(value) for value in source_ids]
        verifications = [
            self._repository.get_verification_record(value) for value in verification_ids
        ]
        if any(record is None for record in sources + verifications):
            return unknown
        source_rows = [record for record in sources if record is not None]
        verification_rows = [record for record in verifications if record is not None]

        if self._has_conflict(player_id):
            conflict_ids = [
                str(record.verification_id)
                for record in self._repository.list_verification_records(
                    "career_participation", player_id
                )
                if record.verification_status == "CONFLICT"
            ]
            return CappedStatusEvidence(
                status=PlayerCappedStatus.UNVERIFIED,
                verification_status=VerificationStatus.CONFLICT,
                conflicting_source_ids=conflict_ids,
            )

        now = datetime.now(UTC)
        linked_record_ids: set[UUID] = set()
        for verification in verification_rows:
            if (
                verification.verification_status != "VERIFIED"
                or verification.subject_id != player_id
                or verification.subject_type not in {"career_participation", "match_performance"}
                or verification.source_record_id is None
                or verification.data_source_id is None
                or verification.data_source_id not in authority.source_ids
                or verification.retrieval_ts > now
                or verification.retrieval_ts < now - timedelta(days=authority.max_evidence_age_days)
            ):
                return unknown
            linked_record_ids.add(verification.source_record_id)

        if linked_record_ids != {record.record_id for record in source_rows}:
            return unknown

        verification_by_source = {v.source_record_id: v for v in verification_rows}
        for source_record in source_rows:
            if source_record.source_id not in authority.source_ids:
                return unknown
            data_source = self._repository.get_data_source(source_record.source_id)
            if (
                data_source is None
                or not data_source.is_active
                or data_source.license_status != "VERIFIED"
                or data_source.license_type.casefold() in {"restricted", "unverified"}
                or verification_by_source.get(source_record.record_id) is None
                or verification_by_source[source_record.record_id].data_source_id
                != source_record.source_id
                or verification_by_source[source_record.record_id].license
                != data_source.license_type
                or source_record.processing_status not in {"Parsed", "Normalized"}
                or not source_record.payload_sha256.strip("0")
            ):
                return unknown

        if evidence.status == PlayerCappedStatus.CAPPED:
            if not self._has_positive_appearance(
                player_id, authority, source_rows, verification_by_source
            ):
                return unknown
            return evidence

        if evidence.status == PlayerCappedStatus.UNCAPPED:
            if not authority.complete_coverage or not self._has_complete_coverage(
                player_id, authority, source_rows, verification_by_source, date.today()
            ):
                return unknown
            return evidence
        return unknown

    def _has_conflict(self, player_id: UUID) -> bool:
        if self._repository is None:
            return False
        return any(
            record.verification_status == "CONFLICT"
            for subject_type in ("career_participation", "match_performance")
            for record in self._repository.list_verification_records(subject_type, player_id)
        )

    @staticmethod
    def _payload_claim(record_payload: dict[str, object]) -> dict[str, object]:
        value = record_payload.get("cap_evidence")
        return value if isinstance(value, dict) else {}

    @classmethod
    def _has_positive_appearance(
        cls,
        player_id: UUID,
        authority: CapSourceAuthority,
        source_rows: list[SourceRecord],
        verification_by_source: dict[UUID | None, VerificationRecord],
    ) -> bool:
        for source_record in source_rows:
            payload = source_record.raw_payload
            claim = cls._payload_claim(payload)
            verification = verification_by_source.get(source_record.record_id)
            competition = str(claim.get("competition", ""))
            if (
                claim.get("claim_type") == "senior_international_appearance"
                and str(claim.get("player_id", "")) == str(player_id)
                and claim.get("appearance_confirmed") is True
                and competition in authority.senior_competitions
                and verification is not None
                and verification.subject_type == "career_participation"
            ):
                return True
        return False

    @classmethod
    def _has_complete_coverage(
        cls,
        player_id: UUID,
        authority: CapSourceAuthority,
        source_rows: list[SourceRecord],
        verification_by_source: dict[UUID | None, VerificationRecord],
        as_of: date,
    ) -> bool:
        for source_record in source_rows:
            claim = cls._payload_claim(source_record.raw_payload)
            verification = verification_by_source.get(source_record.record_id)
            try:
                coverage_end = date.fromisoformat(str(claim.get("coverage_end", "")))
                coverage_start = date.fromisoformat(str(claim.get("coverage_start", "")))
            except ValueError:
                continue
            competitions = claim.get("competitions")
            if (
                claim.get("claim_type") == "senior_international_coverage"
                and str(claim.get("player_id", "")) == str(player_id)
                and claim.get("complete") is True
                and isinstance(competitions, list)
                and {str(item) for item in competitions} >= set(authority.senior_competitions)
                and coverage_start <= date(1900, 1, 1)
                and coverage_end >= as_of
                and verification is not None
                and verification.subject_type == "career_participation"
            ):
                return True
        return False

    @staticmethod
    def _unknown() -> CappedStatusEvidence:
        return CappedStatusEvidence(
            status=PlayerCappedStatus.UNVERIFIED,
            verification_status=VerificationStatus.UNKNOWN,
        )


__all__ = ["CapSourceAuthority", "CapStatusEvidenceVerifier"]
