"""Feature store and analytical feature contracts (TRD §11 Domain 8)."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from src.contracts.base import BaseContract


class DerivedFeature(BaseContract):
    """TRD Entity 31: derived_features."""

    feature_id: UUID = Field(default_factory=uuid4)
    player_id: UUID
    feature_group: str = Field(..., max_length=50)
    feature_name: str = Field(..., max_length=100)
    feature_value_numeric: float | None = None
    feature_value_text: str | None = None
    feature_value_json: dict[str, Any] | None = None
    calculation_window: str = Field(..., max_length=50)
    format_tag: str | None = Field(default=None, max_length=20)
    status: str = Field(default="DERIVED", max_length=20)
    model_version: str = Field(default="v2.1", max_length=20)
    source_provenance: UUID | None = None
    computed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("feature_group")
    @classmethod
    def validate_feature_group(cls, v: str) -> str:
        allowed = {
            "Batting",
            "Bowling",
            "Fielding",
            "Wicketkeeping",
            "Matchup Matrix",
            "Clutch & Pressure",
            "Venue Baselines",
            "Squad Intelligence",
            "Career Coverage",
        }
        if v not in allowed:
            raise ValueError(f"feature_group must be one of {allowed}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"OBSERVED", "DERIVED", "MODEL_INFERRED", "NOT_COMPUTABLE", "DEFERRED"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v
