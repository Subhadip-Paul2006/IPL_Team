"""Adapter for the canonical CMIE contract and offline-safe engine boundary."""

from __future__ import annotations

import inspect
import logging
from datetime import UTC, date, datetime
from typing import Any, Protocol, cast
from uuid import UUID

from src.contracts.cmie import (
    CMIEExecutionStatus,
    CMIEFixtureInput,
    CMIEInputAvailability,
    CMIEOutputContract,
    CMIEResultState,
    CMIEVerificationStatus,
    FixtureEvidenceInput,
    InformationKind,
    ProvenanceTier,
    SourceTrace,
    VenueContext,
)
from src.mie.adapters.base import EngineAdapter
from src.mie.contracts import (
    EngineExecutionRecord,
    EngineName,
    ExecutionState,
)

logger = logging.getLogger(__name__)

__all__ = [
    "CMIEAdapter",
    "CMIEExecutionStatus",
    "CMIEInputAvailability",
    "FixtureEvidenceInput",
]


class CMIEEngineProtocol(Protocol):
    """Narrow runtime contract consumed by the MIE adapter."""

    def contextualise(
        self,
        player_id: UUID | str,
        matches: list[dict[str, Any]] | None = None,
        deliveries: list[dict[str, Any]] | None = None,
        states: list[Any] | None = None,
        bowling_styles: dict[str, str] | None = None,
        fetch_weather: bool = False,
        fixtures: list[CMIEFixtureInput] | None = None,
        input_state: CMIEResultState | None = None,
        **kwargs: Any,
    ) -> CMIEOutputContract: ...


class CMIEAdapter(EngineAdapter):
    """Run CMIE without translating or dropping canonical contract fields."""

    supported_contract_version = "CMIE-1.0.0"

    def __init__(self, cmie_engine: CMIEEngineProtocol | None = None) -> None:
        super().__init__(EngineName.CMIE)
        self.cmie = cmie_engine
        if self.cmie is None:
            try:
                from src.cmie.engine import CMIEEngine

                self.cmie = cast(CMIEEngineProtocol, CMIEEngine())
            except ImportError as err:
                logger.warning(
                    "CMIE import unavailable; using typed fallback (%s)", type(err).__name__
                )

    def is_available(self) -> bool:
        return self.cmie is not None

    def health_check(self) -> dict[str, Any]:
        if self.cmie is None:
            return {
                "engine": self.engine_name.value,
                "status": "DEGRADED_FALLBACK_MODE",
                "network_enabled": False,
                "supported_contract_version": self.supported_contract_version,
            }
        checker = getattr(self.cmie, "health_check", None)
        health = checker() if callable(checker) else {"status": "READY"}
        return {
            "engine": self.engine_name.value,
            "status": "HEALTHY",
            "supported_contract_version": self.supported_contract_version,
            "cmie_health": health,
        }

    def execute(
        self,
        player_id: UUID,
        matches: list[dict[str, Any] | FixtureEvidenceInput] | None = None,
        deliveries: list[dict[str, Any]] | None = None,
        states: list[Any] | None = None,
        bowling_styles: dict[str, str] | None = None,
        fetch_weather: bool = False,
        input_availability: CMIEInputAvailability | str | None = None,
        **kwargs: Any,
    ) -> CMIEOutputContract:
        """Return the canonical contract; provider and contract failures remain failures."""
        if self.cmie is None:
            return self.get_fallback_result(player_id=player_id, matches=matches)
        contextualise = getattr(self.cmie, "contextualise", None)
        if not callable(contextualise):
            raise TypeError("CMIE adapter object does not implement contextualise()")

        resolved_state = kwargs.get("input_state")
        if resolved_state is None and input_availability is not None:
            if isinstance(input_availability, CMIEResultState):
                resolved_state = input_availability
            elif str(input_availability) in CMIEResultState._value2member_map_:
                resolved_state = CMIEResultState(str(input_availability))

        sig = inspect.signature(contextualise)
        has_var_keyword = any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
        )
        call_kwargs: dict[str, Any] = {
            "player_id": player_id,
        }
        if "deliveries" in sig.parameters or has_var_keyword:
            call_kwargs["deliveries"] = deliveries
        if "states" in sig.parameters or has_var_keyword:
            call_kwargs["states"] = states
        if "bowling_styles" in sig.parameters or has_var_keyword:
            call_kwargs["bowling_styles"] = bowling_styles
        if "fetch_weather" in sig.parameters or has_var_keyword:
            call_kwargs["fetch_weather"] = fetch_weather
        if "fixtures" in sig.parameters or has_var_keyword:
            fixtures = kwargs.get("fixtures")
            if fixtures is None and matches and isinstance(matches[0], CMIEFixtureInput):
                fixtures = matches
            if fixtures is not None or "fixtures" in sig.parameters:
                call_kwargs["fixtures"] = fixtures
        if "matches" in sig.parameters or has_var_keyword:
            call_kwargs["matches"] = (
                [m.to_legacy_record() if isinstance(m, CMIEFixtureInput) else m for m in matches]
                if matches is not None
                else None
            )
        if "input_state" in sig.parameters or has_var_keyword:
            call_kwargs["input_state"] = resolved_state
        if "input_availability" in sig.parameters:
            call_kwargs["input_availability"] = input_availability

        output = contextualise(**call_kwargs)
        if not isinstance(output, CMIEOutputContract):
            raise TypeError("CMIE returned a result outside CMIEOutputContract")
        if output.contract_version != self.supported_contract_version:
            raise ValueError(f"Unsupported CMIE contract version: {output.contract_version}")
        if output.player_id not in (None, player_id):
            raise ValueError("CMIE output player_id does not match the request")
        return output

    @staticmethod
    def build_fixture_inputs(
        matches: list[dict[str, Any] | FixtureEvidenceInput] | None,
    ) -> list[FixtureEvidenceInput] | None:
        """Convert provider match rows to the exact source-aware CMIE input contract."""
        if matches is None:
            return None
        fixtures: list[FixtureEvidenceInput] = []
        for row in matches:
            if isinstance(row, FixtureEvidenceInput):
                fixtures.append(row)
                continue
            if not isinstance(row, dict):
                raise TypeError("CMIE match input must be a mapping or FixtureEvidenceInput")
            raw_date = row.get("match_date")
            if isinstance(raw_date, datetime):
                fixture_date = raw_date.date()
            elif isinstance(raw_date, date):
                fixture_date = raw_date
            elif isinstance(raw_date, str) and raw_date.strip():
                fixture_date = date.fromisoformat(raw_date[:10])
            else:
                raise ValueError("CMIE fixture input requires the provider's actual match_date")

            source = CMIEAdapter._source_trace(row)
            raw_time = row.get("scheduled_start_local")
            if isinstance(raw_time, str):
                raw_time = datetime.fromisoformat(raw_time)
            internal_id = row.get("internal_match_id", row.get("match_id"))
            venue_name = row.get("venue_name") or row.get("venue")
            venue_city = row.get("venue_city", row.get("city"))
            if isinstance(venue_city, str) and venue_city.strip().casefold() in {
                "unknown",
                "null",
                "none",
            }:
                venue_city = None
            venue_country = row.get("venue_country", row.get("country"))
            venue_specific_source = row.get("venue_source")
            if isinstance(venue_specific_source, dict):
                venue_specific_source = SourceTrace.model_validate(venue_specific_source)
            if not isinstance(venue_specific_source, SourceTrace):
                venue_specific_source = SourceTrace()
            supplied_venue_sources = row.get("venue_field_sources")
            if not isinstance(supplied_venue_sources, dict):
                supplied_venue_sources = {}
            venue_fields: dict[str, Any] = {}
            for target, candidate in (
                ("name", venue_name),
                ("city", venue_city),
                ("country", venue_country),
            ):
                if candidate is not None:
                    venue_fields[target] = CMIEAdapter._field_trace(
                        supplied_venue_sources.get(target), source
                    )
            dimension_traces: dict[str, SourceTrace] = {}
            has_venue_src = CMIEAdapter._trace_has_source(venue_specific_source)
            if has_venue_src:
                for target, candidate in (
                    ("latitude", row.get("venue_latitude")),
                    ("longitude", row.get("venue_longitude")),
                    ("elevation_meters", row.get("venue_elevation_meters")),
                ):
                    if candidate is not None:
                        dimension_traces[target] = CMIEAdapter._field_trace(
                            supplied_venue_sources.get(target), venue_specific_source
                        )
                        venue_fields[target] = dimension_traces[target]

            venue = VenueContext(
                stadium_name=str(venue_name).strip() if venue_name else None,
                city=str(venue_city).strip() if venue_city else None,
                country=str(venue_country).strip() if venue_country else None,
                latitude=row.get("venue_latitude") if has_venue_src else None,
                longitude=row.get("venue_longitude") if has_venue_src else None,
                elevation_meters=row.get("venue_elevation_meters") if has_venue_src else None,
                source=venue_specific_source if has_venue_src else None,
                dimension_traces=dimension_traces,
                boundary_size_meters={},
                field_sources=venue_fields,
            )
            fixture_fields = {
                field_name: source
                for field_name, value in (
                    ("match_date", fixture_date),
                    ("match_format", row.get("format_tag") or row.get("match_format")),
                )
                if value is not None
            }
            external_id = row.get("external_fixture_id") or row.get("external_match_id")
            fixtures.append(
                FixtureEvidenceInput(
                    internal_match_id=UUID(str(internal_id)) if internal_id else None,
                    external_fixture_id=str(external_id) if external_id else None,
                    match_date=fixture_date,
                    match_format=(
                        str(row.get("format_tag") or row.get("match_format") or row.get("format"))
                        if row.get("format_tag") or row.get("match_format") or row.get("format")
                        else None
                    ),
                    venue=venue,
                    scheduled_start_local=raw_time,
                    fixture_source=source,
                    field_sources=fixture_fields,
                )
            )
        return fixtures

    @staticmethod
    def _source_trace(row: dict[str, Any]) -> SourceTrace:
        """Preserve only provider metadata actually present on the provider record."""
        supplied = row.get("fixture_source", row.get("source_trace"))
        if isinstance(supplied, SourceTrace):
            return supplied
        if isinstance(supplied, dict):
            return SourceTrace.model_validate(supplied)
        provider_raw = row.get("source_provider")
        provider = str(provider_raw) if provider_raw else None
        tier = row.get(
            "source_tier",
            ProvenanceTier.THIRD_PARTY_ESTIMATE if provider else ProvenanceTier.UNKNOWN,
        )
        kind = row.get(
            "source_information_kind",
            InformationKind.THIRD_PARTY_DATASET if provider else InformationKind.UNKNOWN,
        )
        if isinstance(tier, str):
            tier = ProvenanceTier(tier)
        if isinstance(kind, str):
            kind = InformationKind(kind)
        retrieved = row.get("retrieved_at")
        ingested = row.get("ingested_at", row.get("ingestion_timestamp"))
        if isinstance(retrieved, str):
            retrieved = datetime.fromisoformat(retrieved)
        if isinstance(ingested, str):
            ingested = datetime.fromisoformat(ingested)
        key = row.get("relative_source_record_key") or row.get("source_record_key")
        return SourceTrace(
            provider=provider,
            source_url=row.get("source_url"),
            license_name=row.get("license") or row.get("license_name"),
            license_url=row.get("license_url"),
            relative_source_record_key=str(key) if key else None,
            retrieved_at=retrieved,
            ingested_at=ingested,
            payload_sha256=row.get("payload_sha256"),
            tier=tier,
            information_kind=kind,
            confidence=row.get("source_confidence"),
            attribution=row.get("attribution"),
            external_entity_id=row.get("external_entity_id"),
        )

    @staticmethod
    def _field_trace(value: Any, fallback: SourceTrace) -> SourceTrace:
        if isinstance(value, SourceTrace):
            return value
        if isinstance(value, dict):
            return SourceTrace.model_validate(value)
        return fallback

    @staticmethod
    def _trace_has_source(trace: SourceTrace) -> bool:
        return trace.information_kind != InformationKind.UNKNOWN and bool(
            trace.provider or trace.source_url or trace.relative_source_record_key
        )

    def execute_monitored(self, *args: Any, **kwargs: Any) -> tuple[Any, EngineExecutionRecord]:
        """Map canonical CMIE execution status to the MIE adapter lifecycle."""
        output, execution = super().execute_monitored(*args, **kwargs)
        if not isinstance(output, CMIEOutputContract):
            return output, execution
        state_map = {
            CMIEResultState.POPULATED: ExecutionState.SUCCESS,
            CMIEResultState.EMPTY: ExecutionState.SUCCESS,
            CMIEResultState.MISSING_INPUT: ExecutionState.SKIPPED,
            CMIEResultState.DATASET_UNAVAILABLE: ExecutionState.DEGRADED,
            CMIEResultState.PROVIDER_FAILURE: ExecutionState.FAILED,
            CMIEResultState.CONFLICTING_EVIDENCE: ExecutionState.DEGRADED,
            CMIEResultState.SUCCESS: ExecutionState.SUCCESS,
            CMIEResultState.DEGRADED: ExecutionState.DEGRADED,
            CMIEResultState.SKIPPED: ExecutionState.SKIPPED,
            CMIEResultState.FAILED: ExecutionState.FAILED,
        }
        state = (
            ExecutionState.FAILED
            if execution.state == ExecutionState.FAILED
            else state_map.get(output.result_state, ExecutionState.SUCCESS)
        )
        return output, execution.model_copy(
            update={
                "state": state,
                "error_message": execution.error_message,
                "warnings": [*execution.warnings, *output.limitations],
                "records_processed_count": len(output.matches),
            }
        )

    def get_fallback_result(self, *args: Any, **kwargs: Any) -> CMIEOutputContract:
        """Represent absent CMIE execution as explicitly unverified and data-free."""
        player_id = args[0] if args else kwargs.get("player_id")
        fallback_player_id = player_id if isinstance(player_id, UUID) else None
        return CMIEOutputContract(
            as_of_timestamp=datetime.now(UTC),
            player_id=fallback_player_id,
            verification_status=CMIEVerificationStatus.UNVERIFIED,
            result_state=CMIEResultState.MISSING_INPUT,
            source_record_ids=[],
            match_contexts=[],
            limitations=[
                "CMIE execution was unavailable; no venue, weather, pitch, timing, or leverage observations were supplied."
            ],
        )
