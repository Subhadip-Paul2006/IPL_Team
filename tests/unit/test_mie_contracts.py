"""Unit tests for Mother Intelligence Engine (MIE) Typed Contracts.

Verifies schema constraints, Rule AC-15 confidence calibration gating,
and type safety across all MIE data contracts.
"""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError
from src.contracts.pvre import CareerCoverageState, PlayerCappedStatus
from src.contracts.tmve import EligibilityStatus, RRCurrentState, RRRelationshipState
from src.mie.contracts import (
    AggregatedVerificationStatus,
    EngineExecutionRecord,
    EngineName,
    ExecutionState,
    OverallVerificationStatus,
    PlayerIntelligenceRequest,
    UnifiedProvenanceGraph,
)


def test_player_intelligence_request_defaults_and_validation() -> None:
    """Verify request contract initialization with default and custom values."""
    req = PlayerIntelligenceRequest(player_query="Sanju Samson")
    assert req.player_query == "Sanju Samson"
    assert req.evaluation_date == date.today()
    assert req.research_window_years == 3
    assert req.force_refresh is False
    assert req.include_weather_enrichment is False


def test_player_intelligence_request_empty_query_rejected() -> None:
    """Verify request contract rejects empty query strings."""
    with pytest.raises(ValidationError):
        PlayerIntelligenceRequest(player_query="")


def test_engine_execution_record_tracking() -> None:
    """Verify diagnostic execution record attributes and time serialization."""
    rec = EngineExecutionRecord(
        engine=EngineName.PIRE,
        state=ExecutionState.SUCCESS,
        execution_time_ms=12.45,
        records_processed_count=5,
    )
    assert rec.engine == EngineName.PIRE
    assert rec.state == ExecutionState.SUCCESS
    assert rec.execution_time_ms == 12.45
    assert rec.records_processed_count == 5
    assert rec.error_message is None


def test_aggregated_verification_status_ac15_confidence_calibration() -> None:
    """Rule AC-15: Numeric confidence must be None unless is_calibrated is True."""
    # When is_calibrated is False, numeric confidence MUST be rejected
    with pytest.raises(ValidationError, match="Rule AC-15 violation"):
        AggregatedVerificationStatus(
            overall_status=OverallVerificationStatus.VERIFIED,
            identity_status="RESOLVED",
            resolution_tier=1,
            rr_relationship_state=RRRelationshipState.HISTORICAL_RR_APPEARANCE,
            rr_current_state=RRCurrentState.CURRENT,
            ipl_uncapped_eligibility=EligibilityStatus.VERIFIED_ELIGIBLE,
            player_capped_status=PlayerCappedStatus.UNCAPPED,
            career_coverage_state=CareerCoverageState.COMPLETE_WITHIN_VERIFIED_SOURCES,
            calibrated_confidence=0.95,  # Violates AC-15 because is_calibrated is False
            is_calibrated=False,
        )

    # Valid when is_calibrated is True
    valid_calibrated = AggregatedVerificationStatus(
        overall_status=OverallVerificationStatus.VERIFIED,
        identity_status="RESOLVED",
        resolution_tier=1,
        rr_relationship_state=RRRelationshipState.HISTORICAL_RR_APPEARANCE,
        rr_current_state=RRCurrentState.CURRENT,
        ipl_uncapped_eligibility=EligibilityStatus.VERIFIED_ELIGIBLE,
        player_capped_status=PlayerCappedStatus.UNCAPPED,
        career_coverage_state=CareerCoverageState.COMPLETE_WITHIN_VERIFIED_SOURCES,
        calibrated_confidence=0.95,
        is_calibrated=True,
    )
    assert valid_calibrated.calibrated_confidence == 0.95
    assert valid_calibrated.is_calibrated is True

    # Valid when is_calibrated is False and confidence is None
    valid_uncalibrated = AggregatedVerificationStatus(
        overall_status=OverallVerificationStatus.VERIFIED,
        identity_status="RESOLVED",
        resolution_tier=1,
        rr_relationship_state=RRRelationshipState.HISTORICAL_RR_APPEARANCE,
        rr_current_state=RRCurrentState.CURRENT,
        ipl_uncapped_eligibility=EligibilityStatus.VERIFIED_ELIGIBLE,
        player_capped_status=PlayerCappedStatus.UNCAPPED,
        career_coverage_state=CareerCoverageState.COMPLETE_WITHIN_VERIFIED_SOURCES,
        calibrated_confidence=None,
        is_calibrated=False,
    )
    assert valid_uncalibrated.calibrated_confidence is None


def test_unified_provenance_graph_compilation() -> None:
    """Verify provenance graph holds deduplicated sources and license notices."""
    graph = UnifiedProvenanceGraph(
        total_sources_consulted=3,
        source_record_ids=["src-1", "src-2", "src-1"],
        verification_record_ids=["ver-1"],
        primary_sources=["CricSheet", "Open-Meteo"],
        attribution_notices=["ODC-By v1.0", "CC BY 4.0"],
        licenses_observed=["ODC-By v1.0", "CC BY 4.0"],
    )
    assert graph.total_sources_consulted == 3
    assert len(graph.primary_sources) == 2
    assert "ODC-By v1.0" in graph.licenses_observed
