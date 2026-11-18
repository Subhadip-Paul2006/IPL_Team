"""MIE integration regressions against Agent 01's canonical CMIE contracts."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from src.contracts.cmie import (
    CMIEOutputContract,
    CMIEResultState,
    CMIEVerificationStatus,
    InformationKind,
    MatchContextRecord,
    ProvenanceTier,
    SourceTrace,
    VenueContext,
    WeatherContext,
    WeatherObservation,
)
from src.mie.adapters.cmie_adapter import (
    CMIEAdapter,
    FixtureEvidenceInput,
)
from src.mie.adapters.sice_adapter import SICEAdapter
from src.mie.contracts import UnifiedProvenanceGraph
from src.mie.orchestrator import MotherIntelligenceEngine
from src.mie.provenance import ProvenanceGraphBuilder


def _trace(provider: str = "Fixture Authority") -> SourceTrace:
    return SourceTrace(
        provider=provider,
        source_url="https://example.test/data",
        license_name="CC BY 4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        retrieved_at=datetime(2026, 11, 17, tzinfo=UTC),
        payload_sha256="a" * 64,
        tier=ProvenanceTier.OFFICIALLY_REPORTED,
        information_kind=InformationKind.OFFICIAL_PUBLICATION,
    )


def _populated_output(player_id: UUID) -> CMIEOutputContract:
    venue = VenueContext(name="Example Ground", source=_trace("Venue Register"))
    weather_trace = _trace("Weather Archive")
    observation = WeatherObservation(
        timestamp=datetime(2026, 11, 17, 19, tzinfo=UTC),
        temperature_celsius=27.0,
        relative_humidity_pct=81.0,
        dew_point_celsius=23.0,
        source=weather_trace,
        dew_source=weather_trace,
        measurement_availability={"temperature_celsius": True, "relative_humidity_pct": True},
    )
    match = MatchContextRecord(
        match_id=uuid4(),
        match_date=date(2026, 11, 17),
        venue=venue,
        weather=WeatherContext(
            observations=[observation],
            selected_observation=observation,
            matching_method="fixture timestamp",
        ),
    )
    return CMIEOutputContract(
        player_id=player_id,
        verification_status=CMIEVerificationStatus.VERIFIED,
        result_state=CMIEResultState.POPULATED,
        source_record_ids=[uuid4()],  # Test-only persisted-record stub for validator coverage.
        match_contexts=[match],
    )


def test_actual_canonical_contract_import_and_fallback_are_unverified() -> None:
    player_id = uuid4()
    adapter = CMIEAdapter(None)
    result = adapter.get_fallback_result(player_id=player_id)

    assert isinstance(result, CMIEOutputContract)
    assert result.player_id == player_id
    assert result.timestamp.utcoffset() is not None
    assert result.matches == []
    assert result.source_record_ids == []
    assert result.verification_status == CMIEVerificationStatus.UNVERIFIED
    assert result.limitations


def test_default_mie_cmie_adapter_uses_offline_canonical_engine() -> None:
    adapter = CMIEAdapter()

    assert adapter.is_available()
    assert adapter.cmie is not None
    assert adapter.cmie.weather_service.enable_network is False


def test_explicit_weather_opt_in_reaches_cmie_service_policy() -> None:
    class CapturingEngine:
        fetch_weather: bool | None = None

        def contextualise(self, **kwargs: object) -> CMIEOutputContract:
            self.fetch_weather = bool(kwargs.get("fetch_weather"))
            return CMIEOutputContract(
                player_id=kwargs.get("player_id"),
                match_contexts=[],
                result_state=CMIEResultState.EMPTY,
            )

    engine = CapturingEngine()
    CMIEAdapter(engine).execute(
        player_id=uuid4(),
        matches=[],
        fetch_weather=True,
    )

    assert engine.fetch_weather is True


def test_valid_empty_cmie_result_is_successful_but_unverified_evidence() -> None:
    class EmptyEngine:
        def contextualise(self, **kwargs: object) -> CMIEOutputContract:
            return CMIEOutputContract(
                player_id=kwargs.get("player_id"),
                match_contexts=[],
                verification_status=CMIEVerificationStatus.UNVERIFIED,
                result_state=CMIEResultState.EMPTY,
            )

    output, execution = CMIEAdapter(EmptyEngine()).execute_monitored(player_id=uuid4(), matches=[])

    assert execution.state.value == "SUCCESS"
    assert execution.records_processed_count == 0
    assert output.matches == []
    assert output.verification_status == CMIEVerificationStatus.UNVERIFIED
    assert output.result_state == CMIEResultState.EMPTY


def test_source_aware_fixture_mapping_preserves_input_and_leaves_unknowns_null() -> None:
    external_id = "cricsheet-fixture-123"
    raw = {
        "external_fixture_id": external_id,
        "match_date": "2024-04-01",
        "format_tag": "T20",
        "venue": None,
        "city": None,
        "payload_sha256": None,
        "source_provider": "Cricsheet",
        "source_record_key": "ipl_male_json/123.json",
    }

    fixture = CMIEAdapter.build_fixture_inputs([raw])[0]

    assert isinstance(fixture, FixtureEvidenceInput)
    assert fixture.external_fixture_id == external_id
    assert fixture.match_date == date(2024, 4, 1)
    assert fixture.match_format == "T20"
    assert fixture.fixture_source.relative_source_record_key == "ipl_male_json/123.json"
    assert fixture.fixture_source.payload_sha256 is None
    assert fixture.fixture_source.provider == "Cricsheet"
    assert fixture.venue.name is None
    assert fixture.venue.city is None
    assert fixture.venue.latitude is None and fixture.venue.longitude is None
    assert fixture.venue.elevation_meters is None
    assert fixture.venue.boundary_size_meters == {}
    assert fixture.venue.field_sources == {}


def test_fixture_source_trace_is_carried_to_explicit_venue_fields() -> None:
    raw = {
        "external_fixture_id": "fixture-2024-04-01",
        "match_date": "2024-04-01",
        "format_tag": "T20",
        "venue_name": "Source Ground",
        "venue_city": "Source City",
        "source_provider": "Cricsheet",
        "source_url": "https://example.test/archive.zip",
        "source_record_key": "ipl_male_json/123.json",
        "payload_sha256": "b" * 64,
        "license": "ODC Attribution License (ODC-By)",
        "attribution": "Attribution from the dataset notice.",
    }

    fixture = CMIEAdapter.build_fixture_inputs([raw])[0]

    assert fixture.fixture_source.provider == "Cricsheet"
    assert fixture.fixture_source.relative_source_record_key == "ipl_male_json/123.json"
    assert fixture.fixture_source.payload_sha256 == "b" * 64
    assert fixture.fixture_source.license_name == "ODC Attribution License (ODC-By)"
    assert fixture.venue.field_sources["name"] == fixture.fixture_source
    assert fixture.venue.field_sources["city"] == fixture.fixture_source
    assert fixture.venue.latitude is None and fixture.venue.longitude is None
    assert fixture.venue.boundary_size_meters == {}


def test_venue_coordinates_are_carried_only_with_venue_provenance() -> None:
    raw = {
        "external_fixture_id": "fixture-without-venue-source",
        "match_date": "2024-04-01",
        "venue_latitude": 26.9,
        "venue_longitude": 75.8,
    }
    without_source = CMIEAdapter.build_fixture_inputs([raw])[0]
    assert without_source.venue.latitude is None
    assert without_source.venue.longitude is None

    raw["venue_source"] = {
        "provider": "Venue Register",
        "source_url": "https://example.test/venues",
        "tier": ProvenanceTier.OFFICIALLY_REPORTED.value,
        "information_kind": InformationKind.OFFICIAL_PUBLICATION.value,
    }
    with_source = CMIEAdapter.build_fixture_inputs([raw])[0]
    assert with_source.venue.latitude == 26.9
    assert with_source.venue.longitude == 75.8
    assert with_source.venue.field_sources["latitude"].provider == "Venue Register"
    assert with_source.venue.field_sources["longitude"].source_url == (
        "https://example.test/venues"
    )


def test_missing_input_unavailable_dataset_and_provider_failure_are_distinct() -> None:
    adapter = CMIEAdapter()
    player_id = uuid4()

    missing, missing_execution = adapter.execute_monitored(
        player_id=player_id,
        matches=None,
        input_state=CMIEResultState.MISSING_INPUT,
    )
    unavailable, unavailable_execution = adapter.execute_monitored(
        player_id=player_id,
        matches=[],
        input_state=CMIEResultState.DATASET_UNAVAILABLE,
    )
    failed, failed_execution = adapter.execute_monitored(
        player_id=player_id,
        matches=[],
        input_state=CMIEResultState.PROVIDER_FAILURE,
    )

    assert missing.result_state == CMIEResultState.MISSING_INPUT
    assert missing_execution.state.value == "SKIPPED"
    assert unavailable.result_state == CMIEResultState.DATASET_UNAVAILABLE
    assert unavailable_execution.state.value == "DEGRADED"
    assert failed.result_state == CMIEResultState.PROVIDER_FAILURE
    assert failed.verification_status == CMIEVerificationStatus.UNVERIFIED
    assert failed_execution.state.value == "FAILED"


def test_internal_cmie_provider_exception_is_failed_not_verified_empty() -> None:
    class BrokenEngine:
        def contextualise(self, **kwargs: object) -> CMIEOutputContract:
            del kwargs
            raise RuntimeError("provider unavailable")

    output, execution = CMIEAdapter(BrokenEngine()).execute_monitored(player_id=uuid4(), matches=[])

    assert execution.state.value == "FAILED"
    assert output.result_state == CMIEResultState.MISSING_INPUT
    assert output.verification_status == CMIEVerificationStatus.UNVERIFIED
    assert not output.matches


def test_adapter_rejects_unsupported_cmie_contract_version() -> None:
    class WrongVersionEngine:
        def contextualise(self, **kwargs: object) -> CMIEOutputContract:
            return CMIEOutputContract(
                player_id=kwargs["player_id"],
                contract_version="CMIE-99.0.0",
            )

    import pytest

    with pytest.raises(ValueError, match="Unsupported CMIE contract version"):
        CMIEAdapter(WrongVersionEngine()).execute(player_id=uuid4(), matches=[])


def test_canonical_context_traces_survive_provenance_graph_and_exports() -> None:
    player_id = UUID("11111111-2222-3333-4444-555555555555")
    context = _populated_output(player_id)
    graph = ProvenanceGraphBuilder.build_provenance_graph(cmie_output=context)

    assert [trace.provider for trace in graph.cmie_source_traces if trace.provider is not None] == [
        "Venue Register",
        "Weather Archive",
    ]
    assert graph.primary_sources == ["Venue Register", "Weather Archive"]
    assert "CC BY 4.0" in graph.licenses_observed
    assert graph.source_record_ids == [str(context.source_record_ids[0])]

    report = MotherIntelligenceEngine().request_player_intelligence("Unregistered Export Player")
    report = report.model_copy(
        update={
            "context": context,
            "provenance": UnifiedProvenanceGraph(
                **{
                    **report.provenance.model_dump(),
                    "cmie_source_traces": graph.cmie_source_traces,
                    "primary_sources": graph.primary_sources,
                    "licenses_observed": graph.licenses_observed,
                    "attribution_notices": graph.attribution_notices,
                }
            ),
        }
    )

    json_export = json.loads(MotherIntelligenceEngine.export_profile(report, "json"))
    csv_export = MotherIntelligenceEngine.export_profile(report, "csv")
    assert json_export["player_intelligence"]["context"]["matches"][0]["weather"]
    assert json_export["player_intelligence"]["provenance"]["cmie_source_traces"]
    assert "Weather Archive" in csv_export
    assert "dew_point_celsius" in csv_export
    assert "CC BY 4.0" in csv_export


def test_cmie_conflict_or_unverified_status_prevents_overall_verification() -> None:
    # The required-evidence gate stays evidence-aware: CMIE status is a distinct
    # contract signal, not inferred from successful execution or a nonempty payload.
    from src.mie.confidence import ConfidenceReconciler

    values = {
        "identity_status": "RESOLVED",
        "resolution_tier": 1,
        "rr_relationship_state": "NO_VERIFIED_RR_RELATIONSHIP",
        "rr_current_state": "NOT_CURRENT",
        "ipl_uncapped_eligibility": "VERIFIED_ELIGIBLE",
        "player_capped_status": "UNCAPPED",
        "career_coverage_state": "COMPLETE_WITHIN_VERIFIED_SOURCES",
        "candidate_evidence_present": True,
        "cap_evidence_verified": True,
        "required_source_ids": ["source-1"],
    }
    for status in (CMIEVerificationStatus.UNVERIFIED, CMIEVerificationStatus.CONFLICT):
        result = ConfidenceReconciler.aggregate_verification_status(
            **values, cmie_verification_status=status
        )
        assert result.overall_status.value != "VERIFIED"


def test_mie_does_not_pass_uncontracted_cmie_match_state_to_sice() -> None:
    class CapturingSICE(SICEAdapter):
        received: dict[str, object] | None = None

        def execute(self, *args: object, **kwargs: object) -> object:
            self.received = kwargs
            return {"status": "captured"}

    sice = CapturingSICE()
    MotherIntelligenceEngine(sice_adapter=sice).request_player_intelligence(
        "SICE Context Boundary",
        user_team_id=uuid4(),
    )

    assert sice.received is not None
    assert set(sice.received) == {"user_team_id"}


def test_mie_health_reports_degraded_cmie_fallback_mode() -> None:
    adapter = CMIEAdapter()
    adapter.cmie = None
    engine = MotherIntelligenceEngine(cmie_adapter=adapter)
    health = engine.health_check()

    assert health["status"] == "DEGRADED"
    assert "CMIE" in health["degraded_adapters"]
