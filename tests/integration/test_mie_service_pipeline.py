"""Offline MIE service integration tests with explicit unavailable-source behavior."""

from __future__ import annotations

from src.mie import EngineName, ExecutionState, MotherIntelligenceEngine


def test_request_player_intelligence_runs_seven_adapter_pipeline_offline() -> None:
    """Unknown identity returns an auditable report without fabricated engine success."""
    engine = MotherIntelligenceEngine()
    report = engine.request_player_intelligence("Unregistered Test Player")

    assert report.is_review_required
    assert report.player_id is None
    assert set(report.engine_executions) >= {
        EngineName.PIRE.value,
        EngineName.TMVE.value,
        EngineName.CDCRE.value,
        EngineName.CPPAE.value,
        EngineName.CMIE.value,
        EngineName.PVRE.value,
    }
    # Without a resolved player, CMIE is skipped and represented as unverified empty evidence.
    assert report.engine_executions[EngineName.CMIE.value].state == ExecutionState.SKIPPED
    context = report.context
    assert not context.matches
    assert context.verification_status.value == "UNVERIFIED"
    assert report.verification.ipl_uncapped_eligibility.value == "NOT_ASSESSED"
    assert report.verification.player_capped_status.value == "UNVERIFIED"


def test_actual_canonical_cmie_runs_through_mie_for_resolved_player() -> None:
    """A resolved identity and fixture reach the copied canonical CMIE engine."""
    from uuid import uuid4

    from src.mie.adapters.pire_adapter import PIREAdapter

    player_id = uuid4()
    pire = PIREAdapter()
    pire.resolver.register_player(
        canonical_player_id=str(player_id), canonical_name="Canonical Fixture Player"
    )
    mie = MotherIntelligenceEngine(pire_adapter=pire)
    report = mie.request_player_intelligence(
        "Canonical Fixture Player",
        mock_data={
            "matches": [
                {
                    "match_id": str(uuid4()),
                    "match_date": "2026-11-17",
                    "venue": "Unknown Test Ground",
                }
            ]
        },
    )

    assert report.player_id == player_id
    # The mock fixture is explicit but has partial coverage, so CMIE execution
    # is degraded while its evidence remains unverified.
    assert report.engine_executions[EngineName.CMIE.value].state == ExecutionState.DEGRADED
    assert len(report.context.matches) == 1
    assert report.context.matches[0].weather.unavailable_reason
    assert report.context.verification_status.value == "UNVERIFIED"
    assert report.context.input_availability.value == "PARTIAL"


def test_mie_registry_maps_each_engine_to_its_adapter() -> None:
    """Every engine in the MIE registry resolves to the same typed adapter instance."""
    engine = MotherIntelligenceEngine()
    assert len(engine.registry.adapters) == 7
    for name in EngineName:
        assert engine.registry.get(name) is engine.registry.adapters[name]
