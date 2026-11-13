"""Player eligibility and competition policy contracts (TRD §11 Domain 6b)."""

from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

from src.contracts.base import BaseContract


class EligibilityPolicy(BaseContract):
    """TRD Entity 27: eligibility_policies."""

    policy_id: UUID = Field(default_factory=uuid4)
    season_id: UUID
    policy_version: int = Field(default=1, ge=1)
    effective_date: date
    expiry_date: date | None = None
    rule_source: str = Field(..., max_length=200)
    verified: bool = False
    verification_id: UUID | None = None
    policy_json: dict[str, Any] | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_policy_invariants(self) -> "EligibilityPolicy":
        if self.expiry_date is not None and self.expiry_date < self.effective_date:
            raise ValueError("expiry_date must be greater than or equal to effective_date")
        if self.verified and self.verification_id is None:
            raise ValueError("verification_id cannot be None when verified is True")
        return self


class PlayerEligibility(BaseContract):
    """TRD Entity 28: player_eligibility."""

    eligibility_id: UUID = Field(default_factory=uuid4)
    player_id: UUID
    policy_id: UUID
    eligibility_status: str = Field(..., max_length=25)
    verified: bool = False
    verification_id: UUID | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("eligibility_status")
    @classmethod
    def validate_eligibility_status(cls, v: str) -> str:
        allowed = {
            "VERIFIED_ELIGIBLE",
            "VERIFIED_NOT_ELIGIBLE",
            "ELIGIBILITY_UNVERIFIED",
            "NOT_ASSESSED",
        }
        if v not in allowed:
            raise ValueError(f"eligibility_status must be one of {allowed}")
        return v

    @model_validator(mode="after")
    def validate_eligibility_invariants(self) -> "PlayerEligibility":
        if self.eligibility_status in {"VERIFIED_ELIGIBLE", "VERIFIED_NOT_ELIGIBLE"}:
            if not self.verified or self.verification_id is None:
                raise ValueError(
                    "Verified status requires verified=True and verification_id is not None"
                )
        elif (
            self.eligibility_status in {"ELIGIBILITY_UNVERIFIED", "NOT_ASSESSED"} and self.verified
        ):
            raise ValueError("Unverified status requires verified=False")
        return self
