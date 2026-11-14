"""Environmental, pitch, and weather condition contracts (TRD §11 Domain 4b)."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

from src.contracts.base import BaseContract


class PitchCondition(BaseContract):
    """TRD Entity 20: pitch_conditions."""

    pitch_condition_id: UUID = Field(default_factory=uuid4)
    match_id: UUID
    venue_id: UUID
    reported_description: str | None = None
    soil_type: str | None = Field(default=None, max_length=50)
    grass_coverage: str | None = Field(default=None, max_length=30)
    reported_moisture: str | None = Field(default=None, max_length=30)
    reported_surface_state: str | None = Field(default=None, max_length=40)
    pitch_pace_rating: float | None = Field(default=None, ge=1.0, le=10.0)
    pitch_bounce_rating: float | None = Field(default=None, ge=1.0, le=10.0)
    pitch_turn_rating: float | None = Field(default=None, ge=1.0, le=10.0)
    ratings_methodology_version: str | None = Field(default=None, max_length=20)
    provenance_tier: str = Field(default="UNKNOWN", max_length=30)
    source_record_id: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("provenance_tier")
    @classmethod
    def validate_provenance_tier(cls, v: str) -> str:
        allowed = {
            "DIRECTLY_MEASURED",
            "OFFICIALLY_REPORTED",
            "THIRD_PARTY_ESTIMATE",
            "MODEL_INFERRED",
            "UNKNOWN",
        }
        if v not in allowed:
            raise ValueError(f"provenance_tier must be one of {allowed}")
        return v

    @model_validator(mode="after")
    def validate_ratings_methodology(self) -> "PitchCondition":
        has_any_rating = any(
            r is not None
            for r in (
                self.pitch_pace_rating,
                self.pitch_bounce_rating,
                self.pitch_turn_rating,
            )
        )
        if has_any_rating and not self.ratings_methodology_version:
            raise ValueError(
                "ratings_methodology_version must be provided when numeric ratings are present"
            )
        return self


class WeatherCondition(BaseContract):
    """TRD Entity 21: weather_conditions."""

    weather_condition_id: UUID = Field(default_factory=uuid4)
    match_id: UUID
    observation_timestamp: datetime
    venue_timezone: str | None = Field(default=None, max_length=40)
    local_observation_time: datetime | None = None
    temperature_celsius: float | None = None
    relative_humidity_pct: float | None = Field(default=None, ge=0.0, le=100.0)
    dew_point_celsius: float | None = None
    dew_impact_index: str | None = Field(default=None, max_length=20)
    wind_speed_kmh: float | None = Field(default=None, ge=0)
    wind_direction_degrees: int | None = Field(default=None, ge=0, le=360)
    precipitation_mm: float | None = Field(default=None, ge=0)
    atmospheric_pressure_hpa: float | None = None
    cloud_cover_pct: float | None = Field(default=None, ge=0.0, le=100.0)
    spatial_temporal_match_method: str | None = Field(default=None, max_length=80)
    data_provider: str | None = Field(default=None, max_length=60)
    source_record_id: UUID | None = None
    data_provenance_flag: str = Field(
        default="Macro Environmental Context (Not Direct Pitch Moisture)",
        max_length=100,
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
