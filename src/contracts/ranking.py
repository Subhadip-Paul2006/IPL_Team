"""Ranking configuration and execution run contracts (TRD §11 Domain 9)."""

from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, model_validator

from src.contracts.base import BaseContract


class RankingConfiguration(BaseContract):
    """TRD Entity 32: ranking_configurations."""

    config_id: UUID = Field(default_factory=uuid4)
    config_version: str = Field(..., max_length=20)
    target_season_id: UUID
    policy_id: UUID
    evaluation_date: date
    role_grouping_json: dict[str, Any] | None = None
    gate_thresholds_json: dict[str, Any] | None = None
    ordering_json: dict[str, Any]
    tiebreakers_json: dict[str, Any] | None = None
    seed: int = 0
    created_by: str | None = Field(default=None, max_length=50)
    verified: bool = False
    verification_id: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_ranking_evidence(self) -> "RankingConfiguration":
        if self.verified and self.verification_id is None:
            raise ValueError("verification_id cannot be None when verified is True")
        return self


class RankingRun(BaseContract):
    """TRD Entity 33: ranking_runs."""

    run_id: UUID = Field(default_factory=uuid4)
    config_id: UUID
    data_snapshot_sha256: str = Field(..., min_length=64, max_length=64)
    candidate_pool: Any
    top10: Any
    reserve_list: Any | None = None
    computed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    determinism_note: str | None = None
