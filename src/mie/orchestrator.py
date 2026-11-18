"""Mother Intelligence Engine (MIE) Master Orchestrator (Phase 7, Engine 00).

Coordinates all seven specialized platform engines in deterministic sequence:
$$\\text{PIRE} \\longrightarrow \\text{TMVE} \\longrightarrow \\text{CDCRE} \\longrightarrow \\text{CPPAE} \\longrightarrow \\text{CMIE} \\longrightarrow \\text{SICE} \\longrightarrow \\text{PVRE}$$

Enforces:
- Deterministic orchestration and request validation.
- Ambiguity detection and mandatory REVIEW_REQUIRED escalation (Rule R18).
- Multi-dimensional confidence reconciliation and calibration checking (AC-15).
- Complete multi-source provenance graph assembly (Service C).
- Support Service B (JSON/CSV export with attribution and confidentiality controls).
- Fault-tolerant execution with per-engine diagnostic isolation.
"""

from __future__ import annotations

import logging
import time
from datetime import date
from typing import Any
from uuid import UUID, uuid4

from src.contracts.cdcre import CandidateDiscoveryResult
from src.contracts.cmie import CMIEResultState
from src.contracts.pvre import (
    CareerCoverageState,
    PlayerCappedStatus,
    PVRERequestContract,
    PVREReviewDossierContract,
    PVREReviewStatus,
    VerificationStatus,
)
from src.mie.adapters.cdcre_adapter import CDCREAdapter
from src.mie.adapters.cmie_adapter import CMIEAdapter
from src.mie.adapters.cppae_adapter import CPPAEAdapter
from src.mie.adapters.pire_adapter import PIREAdapter
from src.mie.adapters.pvre_adapter import PVREAdapter
from src.mie.adapters.sice_adapter import SICEAdapter
from src.mie.adapters.tmve_adapter import TMVEAdapter
from src.mie.cap_status import CapStatusEvidenceVerifier
from src.mie.confidence import ConfidenceReconciler
from src.mie.contracts import (
    CappedStatusEvidence,
    EngineExecutionRecord,
    EngineName,
    ExecutionState,
    PlayerDataCoverage,
    PlayerIntelligenceReport,
    PlayerIntelligenceRequest,
)
from src.mie.data_provider import (
    CappedStatusProvider,
    LocalCricsheetProvider,
    PlayerIntelligenceProvider,
    SourcePayloadChangedError,
    UnavailableCappedStatusProvider,
)
from src.mie.diagnostics import MIEDiagnostics
from src.mie.evidence_repository import EvidenceRepository
from src.mie.profile_gen import ProfileGeneratorService
from src.mie.provenance import ProvenanceGraphBuilder
from src.mie.registry import MIEEngineRegistry
from src.pire.models import ResolutionResult
from src.services.base import ServiceBoundary

logger = logging.getLogger("mie.orchestrator")


class MotherIntelligenceEngine(ServiceBoundary):
    """Central orchestrator for Rajasthan Royals Squad Intelligence Platform."""

    def __init__(
        self,
        pire_adapter: PIREAdapter | None = None,
        tmve_adapter: TMVEAdapter | None = None,
        cdcre_adapter: CDCREAdapter | None = None,
        cppae_adapter: CPPAEAdapter | None = None,
        cmie_adapter: CMIEAdapter | None = None,
        sice_adapter: SICEAdapter | None = None,
        pvre_adapter: PVREAdapter | None = None,
        diagnostics: MIEDiagnostics | None = None,
        data_provider: PlayerIntelligenceProvider | None = None,
        capped_status_provider: CappedStatusProvider | None = None,
        evidence_repository: EvidenceRepository | None = None,
    ) -> None:
        """Initialize MIE with registered adapters for all seven engines."""
        self.pire = pire_adapter or PIREAdapter()
        self.tmve = tmve_adapter or TMVEAdapter()
        self.cdcre = cdcre_adapter or CDCREAdapter()
        self.cppae = cppae_adapter or CPPAEAdapter()
        self.cmie = cmie_adapter or CMIEAdapter()
        self.sice = sice_adapter or SICEAdapter()
        self.pvre = pvre_adapter or PVREAdapter()
        self.diagnostics = diagnostics or MIEDiagnostics()
        provider_repository = getattr(data_provider, "evidence_repository", None)
        self.evidence_repository = (
            evidence_repository if evidence_repository is not None else provider_repository
        )
        self.data_provider = (
            data_provider
            if data_provider is not None
            else LocalCricsheetProvider(evidence_repository=evidence_repository)
        )
        self.capped_status_provider = (
            capped_status_provider
            if capped_status_provider is not None
            else UnavailableCappedStatusProvider()
        )
        self.cap_status_verifier = CapStatusEvidenceVerifier(self.evidence_repository)
        self.registry = MIEEngineRegistry(
            pire=self.pire,
            tmve=self.tmve,
            cdcre=self.cdcre,
            cppae=self.cppae,
            cmie=self.cmie,
            sice=self.sice,
            pvre=self.pvre,
        )

    # -------------------------------------------------------------------------
    # ServiceBoundary Lifecycle
    # -------------------------------------------------------------------------

    def get_service_name(self) -> str:
        """Return canonical service identifier for MIE."""
        return "mother_intelligence_engine"

    def health_check(self) -> dict[str, Any]:
        """Perform comprehensive health check across all registered engine adapters."""
        adapter_health = {
            EngineName.PIRE.value: self.pire.health_check(),
            EngineName.TMVE.value: self.tmve.health_check(),
            EngineName.CDCRE.value: self.cdcre.health_check(),
            EngineName.CPPAE.value: self.cppae.health_check(),
            EngineName.CMIE.value: self.cmie.health_check(),
            EngineName.SICE.value: self.sice.health_check(),
            EngineName.PVRE.value: self.pvre.health_check(),
        }
        degraded = [
            name
            for name, result in adapter_health.items()
            if str(result.get("status", "UNKNOWN")).casefold() != "healthy"
        ]
        return {
            "service": self.get_service_name(),
            "status": "DEGRADED" if degraded else "HEALTHY",
            "version": "MIE-2.2.0",
            "degraded_adapters": degraded,
            "adapters": adapter_health,
            "diagnostics": self.diagnostics.get_summary_statistics(),
        }

    # -------------------------------------------------------------------------
    # Primary Orchestration Workflow: request_player_intelligence
    # -------------------------------------------------------------------------

    def request_player_intelligence(
        self,
        query: str | PlayerIntelligenceRequest,
        user_team_id: UUID | None = None,
        target_season_id: UUID | None = None,
        evaluation_date: date | None = None,
        research_window_years: int = 3,
        force_refresh: bool = False,
        include_weather_enrichment: bool = False,
        mock_data: dict[str, Any] | None = None,
    ) -> PlayerIntelligenceReport:
        """Execute end-to-end multi-engine intelligence orchestration.

        Sequence:
        1. Pre-Identity Candidate Discovery (CDCRE capability 1, AC-10)
        2. Identity Resolution & Corroboration (PIRE Engine 01)
        3. Membership Verification & Currency (TMVE Engine 02, Dimensions 1 & 2)
        4. Target-Season Eligibility Policy Assessment (Eligibility Service, Dimension 3)
        5. Career Retrieval & Coverage Evaluation (CDCRE Engine 03)
        6. Complete Performance Analytics (CPPAE Engine 04)
        7. Contextual Match Intelligence & CDPI (CMIE Engine 05)
        8. Squad Evaluation & Incumbent Comparison (SICE Engine 06)
        9. Dual-Mode Verification & Research Routing (PVRE Engine 07)
        10. Provenance Graph Assembly & Confidence Reconciliation
        """
        start_time = time.perf_counter()

        # Normalize request contract
        if isinstance(query, PlayerIntelligenceRequest):
            request = query
        else:
            if not isinstance(query, str):
                raise TypeError("query must be a string or PlayerIntelligenceRequest")
            request = PlayerIntelligenceRequest(
                player_query=query,
                user_team_id=user_team_id,
                target_season_id=target_season_id or UUID("11111111-2222-3333-4444-555555555555"),
                evaluation_date=evaluation_date or date.today(),
                research_window_years=research_window_years,
                force_refresh=force_refresh,
                include_weather_enrichment=include_weather_enrichment,
            )

        execution_records: dict[str, EngineExecutionRecord] = {}
        safety_reasons: list[str] = []
        md: dict[str, Any] = {}

        # ----------------------------------------------------------------------
        # Step 1: Pre-Identity Candidate Discovery (CDCRE Capability 1)
        # ----------------------------------------------------------------------
        cdcre_cand_start = time.perf_counter()
        candidate_discovery_res: CandidateDiscoveryResult | None = None
        try:
            existing_ids = self.pire.resolver.alias_registry.lookup_name_candidates(
                request.player_query
            )
            if existing_ids:
                from src.contracts.cdcre import AmbiguityStatus, CandidatePlayerRecord

                candidate_rows = [
                    candidate
                    for candidate in self.pire.resolver.players.values()
                    if candidate.canonical_player_id in existing_ids
                ]
                candidate_discovery_res = CandidateDiscoveryResult(
                    raw_name_query=request.player_query,
                    ambiguity_status=(
                        AmbiguityStatus.NONE
                        if not candidate_rows
                        else AmbiguityStatus.SINGLE_CORROBORATED
                        if len(candidate_rows) == 1
                        else AmbiguityStatus.MULTIPLE
                    ),
                    candidates=[
                        CandidatePlayerRecord(
                            player_id=UUID(candidate.canonical_player_id),
                            canonical_name=candidate.canonical_name,
                            source_id=candidate.source_id,
                            teams=sorted(candidate.teams),
                            competitions=sorted(candidate.competitions),
                        )
                        for candidate in candidate_rows
                    ],
                    collision_detected=len(candidate_rows) > 1,
                )
            else:
                candidate_discovery_res = self.data_provider.search_players(request.player_query)
                for candidate in candidate_discovery_res.candidates:
                    if candidate.player_id is None:
                        continue
                    identity_key = getattr(self.data_provider, "source_identity_key", None)
                    provider_player_id = (
                        identity_key(candidate.player_id) if callable(identity_key) else None
                    )
                    source_player_id = provider_player_id or str(candidate.player_id)
                    self.pire.resolver.register_player(
                        canonical_player_id=str(candidate.player_id),
                        canonical_name=candidate.canonical_name,
                        source_id=candidate.source_id or "local_provider",
                        source_player_id=source_player_id,
                        teams=set(candidate.teams),
                        competitions=set(candidate.competitions),
                    )
            if not isinstance(candidate_discovery_res, CandidateDiscoveryResult):
                raise TypeError("CDCRE returned a result outside CandidateDiscoveryResult")
            cand_dur = (time.perf_counter() - cdcre_cand_start) * 1000.0
            execution_records["CDCRE_CANDIDATE_DISCOVERY"] = EngineExecutionRecord(
                engine=EngineName.CDCRE,
                state=ExecutionState.SUCCESS,
                execution_time_ms=round(cand_dur, 3),
                records_processed_count=len(candidate_discovery_res.candidates),
            )
            if candidate_discovery_res.collision_detected:
                safety_reasons.append("COLLISION_MULTIPLE_IDENTITIES")
        except Exception as exc:
            safety_reasons.append("CANDIDATE_DISCOVERY_EXECUTION_FAILED")
            cand_dur = (time.perf_counter() - cdcre_cand_start) * 1000.0
            execution_records["CDCRE_CANDIDATE_DISCOVERY"] = EngineExecutionRecord(
                engine=EngineName.CDCRE,
                state=ExecutionState.FAILED,
                execution_time_ms=round(cand_dur, 3),
                error_message=f"{type(exc).__name__}: candidate discovery failed",
            )

        # ----------------------------------------------------------------------
        # Step 2: PIRE Identity Resolution (Engine 01)
        # ----------------------------------------------------------------------
        if candidate_discovery_res is None:
            pire_res = self.pire.get_fallback_result(raw_name=request.player_query)
            pire_rec = EngineExecutionRecord(
                engine=EngineName.PIRE,
                state=ExecutionState.SKIPPED,
                execution_time_ms=0.0,
                warnings=["Candidate discovery failed; PIRE identity resolution was gated."],
            )
        else:
            pire_res, pire_rec = self.pire.execute_monitored(
                raw_name=request.player_query,
                candidates=candidate_discovery_res.candidates,
                context_teams=request.context_teams,
                context_competition=request.context_competition,
            )
        execution_records[EngineName.PIRE.value] = pire_rec

        # Extract resolved canonical identity
        resolved_pid: UUID | None = None
        canonical_name = request.player_query
        identity_status = "UNRESOLVED"
        resolution_tier: int | None = None

        if isinstance(pire_res, ResolutionResult):
            canonical_name = pire_res.canonical_name or request.player_query
            identity_status = (
                pire_res.status.value if hasattr(pire_res.status, "value") else str(pire_res.status)
            )
            if pire_res.tier:
                tier_str = (
                    pire_res.tier.value if hasattr(pire_res.tier, "value") else str(pire_res.tier)
                )
                if "TIER_1" in tier_str:
                    resolution_tier = 1
                elif "TIER_2" in tier_str:
                    resolution_tier = 2
                elif "TIER_3" in tier_str:
                    resolution_tier = 3
                elif "TIER_4" in tier_str:
                    resolution_tier = 4
                else:
                    resolution_tier = None
            if pire_res.needs_review:
                safety_reasons.append(
                    "CONFLICT_PIRE_CDCRE_IDENTITY"
                    if "conflict" in (pire_res.review_reason or "").casefold()
                    else "IDENTITY_REVIEW_REQUIRED"
                )

            if pire_res.player_id and identity_status in ("RESOLVED", "PROVISIONAL"):
                try:
                    resolved_pid = UUID(str(pire_res.player_id))
                except ValueError:
                    safety_reasons.append("IDENTITY_INVALID_CANONICAL_ID")
                    identity_status = "UNRESOLVED"
            elif identity_status == "UNRESOLVED":
                safety_reasons.append("IDENTITY_UNRESOLVED")

        source_integrity_failed = False
        fixture_input_availability = CMIEResultState.MISSING_INPUT
        if resolved_pid is not None:
            try:
                local_evidence = self.data_provider.player_matches(resolved_pid)
            except SourcePayloadChangedError:
                logger.warning("Cricsheet source changed after indexing; evidence withheld")
                safety_reasons.append("LOCAL_SOURCE_HASH_MISMATCH")
                source_integrity_failed = True
                local_evidence = ()
                fixture_input_availability = CMIEResultState.PROVIDER_FAILURE
            except Exception as exc:
                logger.warning(
                    "Match provider failed (%s); fixture evidence withheld", type(exc).__name__
                )
                safety_reasons.append("MATCH_PROVIDER_FAILED")
                local_evidence = ()
                fixture_input_availability = CMIEResultState.PROVIDER_FAILURE
            else:
                if not local_evidence:
                    fixture_input_availability = CMIEResultState.EMPTY
                else:
                    fixture_input_availability = CMIEResultState.POPULATED
        else:
            local_evidence = ()
        coverage_method = getattr(self.data_provider, "player_coverage", None)
        raw_coverage = (
            coverage_method(resolved_pid, local_evidence)
            if callable(coverage_method)
            else {
                "records_observed": len(local_evidence),
                "source_completeness": "UNKNOWN",
                "identity_certainty": "UNKNOWN",
                "missing_periods": None,
            }
        )
        data_coverage = PlayerDataCoverage.model_validate(raw_coverage)
        t20_evidence = tuple(
            record
            for record in local_evidence
            if str(record.match.get("format_tag", "")).upper() in {"T20", "T20I", "IT20"}
            and record.match.get("balls_per_innings") == 120
        )
        md.update(
            {
                "matches": [dict(record.match) for record in local_evidence],
                "deliveries": [
                    dict(delivery) for record in local_evidence for delivery in record.deliveries
                ],
                "performance_matches": [dict(record.match) for record in t20_evidence],
                "performance_deliveries": [
                    dict(delivery) for record in t20_evidence for delivery in record.deliveries
                ],
                "states": [],
                "source_evidence": local_evidence,
                "data_availability": self.data_provider.availability(),
                "cmie_input_availability": fixture_input_availability.value,
            }
        )
        # Explicit fixture input remains available to test callers; normal UI search
        # receives its data through the provider above.
        if mock_data:
            md.update(mock_data)
            if "matches" in mock_data:
                fixture_input_availability = CMIEResultState.POPULATED
                md["cmie_input_availability"] = fixture_input_availability.value
            if "deliveries" in mock_data:
                md["performance_deliveries"] = mock_data["deliveries"]
            if "matches" in mock_data:
                md["performance_matches"] = mock_data["matches"]

        # ----------------------------------------------------------------------
        # Step 3: TMVE Membership Verification & Eligibility (Engine 02)
        # ----------------------------------------------------------------------
        effective_pid = resolved_pid or UUID("00000000-0000-0000-0000-000000000000")
        if resolved_pid is None:
            tmve_out, elig_out = self.tmve.get_fallback_result(
                player_id=effective_pid,
                as_of_date=request.evaluation_date,
                target_season_id=request.target_season_id,
            )
            tmve_rec = EngineExecutionRecord(
                engine=EngineName.TMVE,
                state=ExecutionState.SKIPPED,
                execution_time_ms=0.0,
                warnings=["Identity resolution is required before player membership lookup."],
            )
        else:
            (tmve_out, elig_out), tmve_rec = self.tmve.execute_monitored(
                player_id=effective_pid,
                as_of_date=request.evaluation_date,
                target_season_id=request.target_season_id,
                squad_records=md.get("squad_records"),
                history_records=md.get("history_records"),
                appearances=md.get("appearances"),
            )
        execution_records[EngineName.TMVE.value] = tmve_rec

        if tmve_out and tmve_out.review_reason_codes:
            safety_reasons.extend(tmve_out.review_reason_codes)

        # ----------------------------------------------------------------------
        # Step 4: CDCRE Career Retrieval (Engine 03, Capability 2)
        # ----------------------------------------------------------------------
        if resolved_pid is None:
            career_coverage = self.cdcre.get_fallback_result(player_id=effective_pid)
            cdcre_rec = EngineExecutionRecord(
                engine=EngineName.CDCRE,
                state=ExecutionState.SKIPPED,
                execution_time_ms=0.0,
                warnings=["Identity resolution is required before career retrieval."],
            )
        else:
            career_coverage, cdcre_rec = self.cdcre.execute_monitored(
                player_id=effective_pid,
                team_affiliations=getattr(tmve_out, "other_ipl_teams", None),
            )
        execution_records[EngineName.CDCRE.value] = cdcre_rec

        # ----------------------------------------------------------------------
        # Step 5: CPPAE Performance Analytics (Engine 04)
        # ----------------------------------------------------------------------
        if resolved_pid is None:
            cppae_out = self.cppae.get_fallback_result(
                player_id=effective_pid, player_names={str(effective_pid): canonical_name}
            )
            cppae_rec = EngineExecutionRecord(
                engine=EngineName.CPPAE,
                state=ExecutionState.SKIPPED,
                execution_time_ms=0.0,
                warnings=["Identity resolution is required before performance analysis."],
            )
        else:
            cppae_out, cppae_rec = self.cppae.execute_monitored(
                player_id=effective_pid,
                deliveries=md.get("performance_deliveries", []),
                states=md.get("states", []),
                batting_innings=md.get("batting_innings", []),
                bowling_spells=md.get("bowling_spells", []),
                fielding_events=md.get("fielding_events", []),
                wk_events=md.get("wk_events", []),
                matches=md.get("performance_matches", []),
                player_names={str(effective_pid): canonical_name},
            )
        execution_records[EngineName.CPPAE.value] = cppae_rec

        # ----------------------------------------------------------------------
        # Step 6: CMIE Contextual Match Intelligence (Engine 05)
        # ----------------------------------------------------------------------
        if resolved_pid is None:
            cmie_out = self.cmie.get_fallback_result(player_id=resolved_pid, matches=None)
            cmie_rec = EngineExecutionRecord(
                engine=EngineName.CMIE,
                state=ExecutionState.SKIPPED,
                execution_time_ms=0.0,
                warnings=["Identity resolution is required before match contextualisation."],
            )
        else:
            cmie_out, cmie_rec = self.cmie.execute_monitored(
                player_id=effective_pid,
                matches=md.get("matches"),
                deliveries=md.get("deliveries"),
                states=md.get("states"),
                fetch_weather=request.include_weather_enrichment,
                input_availability=md.get(
                    "cmie_input_availability", fixture_input_availability.value
                ),
            )
        execution_records[EngineName.CMIE.value] = cmie_rec

        # ----------------------------------------------------------------------
        # Step 7: SICE Squad Evaluation (Engine 06)
        # ----------------------------------------------------------------------
        sice_out = None
        if request.user_team_id:
            sice_out, sice_rec = self.sice.execute_monitored(user_team_id=request.user_team_id)
            execution_records[EngineName.SICE.value] = sice_rec
        else:
            execution_records[EngineName.SICE.value] = EngineExecutionRecord(
                engine=EngineName.SICE,
                state=ExecutionState.SKIPPED,
                execution_time_ms=0.0,
                warnings=["Squad evaluation requires a user_team_id."],
            )

        # ----------------------------------------------------------------------
        # Step 8: PVRE Dual-Mode Research & Safety Interceptor (Engine 07)
        # ----------------------------------------------------------------------
        rel_state_str = (
            tmve_out.rr_relationship_state.value if tmve_out else "RR_RELATIONSHIP_UNKNOWN"
        )
        cur_state_str = tmve_out.rr_current_state.value if tmve_out else "UNKNOWN"
        elig_status_str = elig_out.eligibility_status.value if elig_out else "NOT_ASSESSED"

        # Cap status is independent of IPL eligibility and requires explicit sourced evidence.
        raw_cap_evidence: CappedStatusEvidence | None = None
        cap_evidence: CappedStatusEvidence | None = None
        if resolved_pid is not None:
            try:
                raw_cap_evidence = self.capped_status_provider.assess(resolved_pid)
            except Exception as exc:
                logger.warning("Cap evidence provider failed closed (%s)", type(exc).__name__)
                safety_reasons.append("CAP_STATUS_PROVIDER_FAILED")
            if raw_cap_evidence is not None and not isinstance(
                raw_cap_evidence, CappedStatusEvidence
            ):
                logger.warning("Cap evidence provider returned an invalid contract")
                safety_reasons.append("CAP_STATUS_PROVIDER_INVALID")
            elif raw_cap_evidence is not None:
                cap_evidence = self.cap_status_verifier.verify(resolved_pid, raw_cap_evidence)
        capped_status = (
            cap_evidence.status
            if cap_evidence and cap_evidence.verification_status == VerificationStatus.VERIFIED
            else PlayerCappedStatus.UNVERIFIED
        )
        cap_verified = bool(
            cap_evidence
            and cap_evidence.verification_status == VerificationStatus.VERIFIED
            and cap_evidence.source_record_ids
        )
        if not cap_evidence:
            safety_reasons.append("CAP_STATUS_EVIDENCE_MISSING")
        elif cap_evidence.verification_status == VerificationStatus.CONFLICT:
            safety_reasons.append("CAP_STATUS_CONFLICT")
        elif not cap_verified:
            safety_reasons.append("CAP_STATUS_UNVERIFIED")

        pvre_req = PVRERequestContract(
            research_run_id=uuid4(),
            player_query=request.player_query,
            player_id=resolved_pid,
            canonical_name=canonical_name,
            identity_status=identity_status,
            rr_relationship_state=rel_state_str,
            rr_current_state=cur_state_str,
            player_capped_status=capped_status.value,
            ipl_uncapped_eligibility=elig_status_str,
            target_season_id=request.target_season_id,
            evaluation_date=request.evaluation_date,
            research_window_years=request.research_window_years,
            force_refresh=request.force_refresh,
        )

        pvre_context: dict[str, Any] = {
            "squad_records": md.get("squad_records", []),
            "scorecards": md.get("scorecards", []),
            "multi_league_matches": md.get("multi_league_matches", []),
            "domestic_matches": md.get("domestic_matches", []),
            "dob_evidence": md.get("dob_evidence"),
            "statistical_sources": md.get("statistical_sources"),
        }

        pvre_out, pvre_rec = self.pvre.execute_monitored(
            request=pvre_req,
            context=pvre_context,
            canonical_name=canonical_name,
            evaluation_date=request.evaluation_date,
            target_season_id=request.target_season_id,
        )
        execution_records[EngineName.PVRE.value] = pvre_rec

        if pvre_out and pvre_out.review_reason_codes:
            safety_reasons.extend(pvre_out.review_reason_codes)
        for engine_key in (
            EngineName.PIRE.value,
            "CDCRE_CANDIDATE_DISCOVERY",
            EngineName.TMVE.value,
            EngineName.CDCRE.value,
            EngineName.CPPAE.value,
            EngineName.CMIE.value,
            EngineName.PVRE.value,
        ):
            record = execution_records.get(engine_key)
            if record and record.state in (
                ExecutionState.FAILED,
                ExecutionState.SKIPPED,
                ExecutionState.DEGRADED,
            ):
                safety_reasons.append(f"ENGINE_{record.state.value}_{engine_key}")

        # ----------------------------------------------------------------------
        # Step 9: Assemble Safety Review Dossier if REVIEW_REQUIRED
        # ----------------------------------------------------------------------
        safety_dossier = None
        if safety_reasons or (
            pvre_out and pvre_out.review_status == PVREReviewStatus.REVIEW_REQUIRED
        ):
            unique_reasons = sorted(set(safety_reasons))
            cap_conflict_sources = sorted(
                set(cap_evidence.conflicting_source_ids if cap_evidence else [])
            )
            identity_conflict_sources = sorted(
                {
                    str(item.get("source_id"))
                    for item in getattr(pire_res, "candidate_matches", [])
                    if item.get("source_id")
                }
            )
            conflicting_record_ids: list[UUID | int] = []
            for item in getattr(pire_res, "candidate_matches", []):
                try:
                    if item.get("player_id"):
                        conflicting_record_ids.append(UUID(str(item["player_id"])))
                except (TypeError, ValueError):
                    continue
            safety_dossier = PVREReviewDossierContract(
                dossier_id=uuid4(),
                subject_id=resolved_pid,
                review_status=PVREReviewStatus.REVIEW_REQUIRED,
                review_reason_codes=unique_reasons,
                unresolved_claims=[
                    {
                        "reason": reason,
                        "conflicting_source_ids": (
                            cap_conflict_sources
                            if reason == "CAP_STATUS_CONFLICT"
                            else identity_conflict_sources
                            if "IDENTITY" in reason or "PIRE" in reason
                            else []
                        ),
                    }
                    for reason in unique_reasons
                ],
                conflicting_source_ids=conflicting_record_ids,
                missing_evidence=[
                    *(
                        ["Resolved player identity and canonical player ID"]
                        if resolved_pid is None
                        else []
                    ),
                    *(
                        ["Verified international cap status and source record"]
                        if not cap_verified
                        else []
                    ),
                    *(
                        ["Complete career coverage within verified sources"]
                        if getattr(pvre_out, "career_coverage_state", None)
                        != CareerCoverageState.COMPLETE_WITHIN_VERIFIED_SOURCES
                        else []
                    ),
                    *(
                        ["Required source records for each verified claim"]
                        if not (pvre_out and pvre_out.source_record_ids)
                        and not (cap_evidence and cap_evidence.source_record_ids)
                        else []
                    ),
                ]
                or ["Evidence required to resolve the review condition"],
                recommended_manual_checks=[
                    "Inspect state association registration certificate",
                    "Verify official franchise roster archives",
                ],
            )

        # ----------------------------------------------------------------------
        # Step 10: Multi-Engine Provenance & Verification Synthesis
        # ----------------------------------------------------------------------
        provenance_graph = ProvenanceGraphBuilder.build_provenance_graph(
            tmve_output=tmve_out,
            eligibility_output=elig_out,
            identity_output=pire_res if isinstance(pire_res, ResolutionResult) else None,
            candidate_discovery=candidate_discovery_res,
            career_coverage=career_coverage,
            cmie_output=cmie_out,
            pvre_output=pvre_out,
            extra_source_ids=(
                [
                    str(record.source_record_id)
                    for record in local_evidence
                    if record.source_record_id is not None
                    and self.evidence_repository is not None
                    and self.evidence_repository.durable
                ]
                + (
                    [str(source_id) for source_id in cap_evidence.source_record_ids]
                    if cap_evidence
                    else []
                )
            ),
            extra_verification_ids=(
                [str(item) for item in cap_evidence.verification_record_ids] if cap_evidence else []
            ),
            local_cricsheet_observed=bool(local_evidence),
        )
        if local_evidence and not provenance_graph.primary_sources:
            provenance_graph.primary_sources = ["Cricsheet local snapshot"]
            provenance_graph.total_sources_consulted = 1

        cov_state = getattr(pvre_out, "career_coverage_state", CareerCoverageState.PARTIAL_COVERAGE)
        verification_status = ConfidenceReconciler.aggregate_verification_status(
            identity_status=identity_status,
            resolution_tier=resolution_tier,
            rr_relationship_state=rel_state_str,
            rr_current_state=cur_state_str,
            ipl_uncapped_eligibility=elig_status_str,
            player_capped_status=capped_status,
            career_coverage_state=cov_state,
            review_reason_codes=safety_reasons,
            cap_evidence_verified=cap_verified,
            candidate_evidence_present=bool(
                candidate_discovery_res
                and candidate_discovery_res.candidates
                and all(candidate.source_id for candidate in candidate_discovery_res.candidates)
            ),
            cmie_verification_status=getattr(
                getattr(cmie_out, "verification_status", "UNVERIFIED"),
                "value",
                getattr(cmie_out, "verification_status", "UNVERIFIED"),
            ),
            required_source_ids=[
                str(source_id) for source_id in provenance_graph.source_record_ids
            ],
            execution_records=execution_records,
        )

        total_duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Log diagnostics
        self.diagnostics.record_run(
            request_id=request.request_id,
            player_query=request.player_query,
            total_time_ms=total_duration_ms,
            engine_executions=execution_records,
            overall_status=verification_status.overall_status.value,
        )

        # Assemble Final Consolidated Report
        report = PlayerIntelligenceReport(
            request=request,
            player_id=resolved_pid,
            canonical_name=canonical_name,
            identity={
                "status": identity_status,
                "tier": resolution_tier,
                "confidence": None,
                "player_id": str(resolved_pid) if resolved_pid else None,
            },
            membership=tmve_out,
            eligibility=elig_out,
            candidate_discovery=candidate_discovery_res,
            career=career_coverage,
            performance=cppae_out,
            context=cmie_out,
            squad_evaluation=sice_out,
            pvre=pvre_out,
            verification=verification_status,
            provenance=provenance_graph,
            data_availability={
                **self.data_provider.availability(),
                "cmie_input_availability": fixture_input_availability.value,
                **(
                    {"source_integrity": "A local payload changed after indexing; data withheld."}
                    if source_integrity_failed
                    else {}
                ),
            },
            local_source_evidence=[
                (
                    {
                        "source_record_key": record.source_record_key,
                        "payload_sha256": record.payload_sha256,
                        "license": record.license,
                        "license_url": record.license_url,
                        "attribution": record.attribution,
                        "source_provider": record.source_provider,
                        "source_url": record.source_url,
                        **(
                            {"retrieved_at": record.retrieved_at.isoformat()}
                            if record.retrieved_at is not None
                            else {}
                        ),
                        **(
                            {"source_record_id": str(record.source_record_id)}
                            if record.source_record_id is not None
                            and self.evidence_repository is not None
                            and self.evidence_repository.durable
                            else {}
                        ),
                        **(
                            {"ingestion_timestamp": record.ingestion_timestamp.isoformat()}
                            if record.ingestion_timestamp is not None
                            else {}
                        ),
                    }
                )
                for record in local_evidence
            ],
            data_coverage=data_coverage,
            safety_dossier=safety_dossier,
            engine_executions=execution_records,
            total_execution_time_ms=round(total_duration_ms, 3),
        )

        return report

    # -------------------------------------------------------------------------
    # Profile Export Methods (Support Service B)
    # -------------------------------------------------------------------------

    @staticmethod
    def export_profile(report: PlayerIntelligenceReport, format: str = "json") -> str:
        """Export report to JSON or CSV with embedded licensing attribution."""
        fmt = format.strip().lower()
        if fmt == "csv":
            return ProfileGeneratorService.export_to_csv(report)
        return ProfileGeneratorService.export_to_json(report)


__all__ = ["MotherIntelligenceEngine"]
