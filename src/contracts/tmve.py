"""Team Membership Verification Engine (TMVE) inter-engine runtime contracts.

Authoritative contracts reflecting TRD §4.3, §4.4, §4.5, and §11 inter-engine
specifications for Rajasthan Royals squad intelligence platform.
"""

from datetime import date
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field

from src.contracts.base import BaseContract


class RRRelationshipState(StrEnum):
    """Authoritative relationship states between a player and Rajasthan Royals (TRD §4.3)."""

    HISTORICAL_RR_APPEARANCE = "HISTORICAL_RR_APPEARANCE"
    HISTORICAL_RR_SQUAD_ONLY = "HISTORICAL_RR_SQUAD_ONLY"
    PREVIOUSLY_ASSOCIATED = "PREVIOUSLY_ASSOCIATED"
    NO_VERIFIED_RR_RELATIONSHIP = "NO_VERIFIED_RR_RELATIONSHIP"
    RR_RELATIONSHIP_UNKNOWN = "RR_RELATIONSHIP_UNKNOWN"


class RRCurrentState(StrEnum):
    """Current membership states for a player relative to Rajasthan Royals (TRD §4.3)."""

    CURRENT = "CURRENT"
    NOT_CURRENT = "NOT_CURRENT"
    UNKNOWN = "UNKNOWN"


class EligibilityStatus(StrEnum):
    """Authoritative player competition eligibility status (TRD §4.3)."""

    VERIFIED_ELIGIBLE = "VERIFIED_ELIGIBLE"
    VERIFIED_NOT_ELIGIBLE = "VERIFIED_NOT_ELIGIBLE"
    ELIGIBILITY_UNVERIFIED = "ELIGIBILITY_UNVERIFIED"
    NOT_ASSESSED = "NOT_ASSESSED"


class TMVERequestContract(BaseContract):
    """Input request contract for Team Membership Verification Engine resolution."""

    player_id: UUID
    as_of_date: date


class TMVEOutputContract(BaseContract):
    """Output contract reflecting resolved membership state and verified participation."""

    contract_version: str = "TMVE-1.0.0"
    player_id: UUID
    as_of_date: date
    rr_relationship_state: RRRelationshipState
    rr_current_state: RRCurrentState
    rr_seasons: list[str] = Field(default_factory=list)
    other_ipl_teams: list[str] = Field(default_factory=list)
    verified_rr_appearances: int = Field(default=0, ge=0)
    evidence_verification_ids: list[UUID] = Field(default_factory=list)
    verification_date: date
    membership_confidence: float | None = None
    negative_verification_met: bool = False
    review_status: str = "CLEAR"
    review_reason_codes: list[str] = Field(default_factory=list)


class EligibilityOutputContract(BaseContract):
    """Output contract reflecting evaluated season-bound player eligibility."""

    contract_version: str = "ELIG-1.0.0"
    player_id: UUID
    target_season_id: UUID
    eligibility_status: EligibilityStatus = EligibilityStatus.NOT_ASSESSED
    policy_id: UUID | None = None
    policy_version: int | None = None
    verified: bool = False
    verification_id: UUID | None = None
    rule_source: str | None = None
    evidence_verification_ids: list[UUID] = Field(default_factory=list)


class ReviewDossierContract(BaseContract):
    """Safety dossier generated when membership or eligibility claims require human review."""

    contract_version: str = "DOSSIER-1.0.0"
    dossier_id: UUID
    subject_type: str
    subject_id: UUID
    review_status: str = "REVIEW_REQUIRED"
    review_reason_codes: list[str] = Field(default_factory=list)
    unresolved_claims: list[dict[str, Any]] = Field(default_factory=list)
    conflicting_source_ids: list[UUID | int] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    recommended_manual_checks: list[str] = Field(default_factory=list)


__all__ = [
    "RRRelationshipState",
    "RRCurrentState",
    "EligibilityStatus",
    "TMVERequestContract",
    "TMVEOutputContract",
    "EligibilityOutputContract",
    "ReviewDossierContract",
]
