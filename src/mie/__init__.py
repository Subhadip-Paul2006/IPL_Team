"""Mother Intelligence Engine (MIE) Package (Phase 7, Engine 00).

Central orchestration engine for the Rajasthan Royals Squad Intelligence Platform:
- Orchestrator: MotherIntelligenceEngine executing strict 7-engine deterministic waterfall:
  PIRE -> TMVE -> CDCRE -> CPPAE -> CMIE -> SICE -> PVRE
- Typed Contracts: PlayerIntelligenceRequest, PlayerIntelligenceReport, AggregatedVerificationStatus
- Support Service B: ProfileGeneratorService (JSON / CSV export with source attribution)
- Support Service C: ProvenanceGraphBuilder (unified multi-source provenance graph)
- Diagnostics: MIEDiagnostics (latency tracking, telemetry, execution observability)
"""

from src.mie.contracts import (
    AggregatedVerificationStatus,
    EngineExecutionRecord,
    EngineName,
    ExecutionState,
    OverallVerificationStatus,
    PlayerDataCoverage,
    PlayerIntelligenceReport,
    PlayerIntelligenceRequest,
    UnifiedProvenanceGraph,
)
from src.mie.orchestrator import MotherIntelligenceEngine
from src.mie.profile_gen import ProfileGeneratorService
from src.mie.provenance import ProvenanceGraphBuilder
from src.mie.registry import MIEEngineRegistry

__all__ = [
    # Master Facade
    "MotherIntelligenceEngine",
    # Service B & C
    "ProfileGeneratorService",
    "ProvenanceGraphBuilder",
    "MIEEngineRegistry",
    # Contracts
    "PlayerIntelligenceRequest",
    "PlayerIntelligenceReport",
    "AggregatedVerificationStatus",
    "UnifiedProvenanceGraph",
    "PlayerDataCoverage",
    "EngineExecutionRecord",
    "EngineName",
    "ExecutionState",
    "OverallVerificationStatus",
]
