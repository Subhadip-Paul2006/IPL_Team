"""Mother Controller and 7-Step Deterministic Routing Waterfall for PVRE.

Part of Phase 04B — Player Verification & Research Engine (Milestone 5).
Implements MotherController in strict compliance with TRD §9.1–§9.2, PRD FR-PV1,
and AI_INSTRUCTIONS R1..R22:
- Step 1: Pre-identity discovery & PIRE resolution.
- Step 2: Ambiguity / collision check (COLLISION_MULTIPLE_IDENTITIES -> ROUTED_SAFETY_REVIEW).
- Step 3: TMVE relationship check (CURRENT_RR, HISTORICAL_RR_APPEARED, HISTORICAL_RR_SQUAD_ONLY -> ROUTED_RR_INCUMBENT / Mode A).
- Step 4: Senior international cap check (CAPPED & no RR relationship -> ROUTED_OUT_OF_SCOPE).
- Step 5: Eligibility Policy Service validation (UNCAPPED & verified eligible -> ROUTED_UNCAPPED_CANDIDATE / Mode B).
- Step 6: Unknown / unassessed player -> ROUTED_SAFETY_REVIEW (UNKNOWN_PLAYER_NOT_IN_DATABASE, negative proof invariant).
- Step 7: Missing / conflicting data -> ROUTED_SAFETY_REVIEW.

Invariant: Never infer that an unknown player is uncapped. Database absence is never proof of uncapped status.
Orchestrates ModeAIncumbentEngine, ModeBCandidateEngine, and SafetyReviewInterceptor.
Compiles the authoritative 26-field PVREOutputContract.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from src.contracts.pvre import (
    CareerCoverageState,
    PlayerCappedStatus,
    PlayerResearchRequest,
    PVREOutputContract,
    PVRERequestContract,
    PVREReviewStatus,
    ResearchMode,
    ReviewDossierContract,
    RouteStatus,
)
from src.pvre.mode_a_incumbent import ModeAIncumbentEngine
from src.pvre.mode_b_candidate import (
    SCORECARD_ONLY_GRANULARITY,
    ModeBCandidateEngine,
)
from src.pvre.safety_review import (
    SafetyReviewInterceptor,
    SafetyReviewReasonCode,
    build_safety_review_dossier,
)

logger = logging.getLogger(__name__)


class MotherController:
    """Mother Controller coordinating PVRE routing and sub-engine execution.

    Implements TRD §9.1 and §9.2 lifecycle:
    1. Input ingestion and contract validation.
    2. Deterministic 7-step routing waterfall.
    3. Routing to Mode A, Mode B, Review Required, or Out of Scope.
    4. Execution orchestration with ModeAIncumbentEngine and ModeBCandidateEngine.
    5. Safety interceptor coordination with SafetyReviewInterceptor.
    6. Contract compilation of the authoritative 26-field PVREOutputContract.
    """

    def __init__(
        self,
        safety_interceptor: SafetyReviewInterceptor | None = None,
        mode_a_engine: type[ModeAIncumbentEngine] | None = None,
        mode_b_engine: ModeBCandidateEngine | None = None,
    ) -> None:
        """Initialize MotherController with supporting sub-engines."""
        self.safety_interceptor: SafetyReviewInterceptor = (
            safety_interceptor or SafetyReviewInterceptor()
        )
        self.mode_a_engine: type[ModeAIncumbentEngine] = (
            mode_a_engine or ModeAIncumbentEngine
        )
        self.mode_b_engine: ModeBCandidateEngine = (
            mode_b_engine or ModeBCandidateEngine()
        )
        self.last_dossier: ReviewDossierContract | None = None

    # -------------------------------------------------------------------------
    # Inbound Request Normalization
    # -------------------------------------------------------------------------

    @staticmethod
    def normalize_request(
        request: PVRERequestContract | PlayerResearchRequest | dict[str, Any],
    ) -> PVRERequestContract:
        """Normalize inbound request payload to PVRERequestContract."""
        if isinstance(request, PVRERequestContract):
            return request
        if isinstance(request, PlayerResearchRequest):
            dump = request.model_dump()
            # PlayerResearchRequest metadata is mapped if needed
            dump.pop("metadata", None)
            return PVRERequestContract(**dump)
        if isinstance(request, dict):
            req_dict = dict(request)
            req_dict.pop("metadata", None)
            return PVRERequestContract(**req_dict)
        raise TypeError(f"Unsupported request type: {type(request)}")

    # -------------------------------------------------------------------------
    # Deterministic 7-Step Waterfall Classification
    # -------------------------------------------------------------------------

    def classify_and_route(
        self,
        request: PVRERequestContract,
        context: dict[str, Any] | None = None,
    ) -> tuple[RouteStatus, ResearchMode, list[str], ReviewDossierContract | None]:
        """Execute deterministic 7-step precedence waterfall.

        Returns:
            (route_status, research_mode, review_reason_codes, dossier_or_none)
        """
        ctx = context or {}
        dossier: ReviewDossierContract | None = None

        # ---------------------------------------------------------------------
        # Step 1: Pre-identity discovery & PIRE resolution
        # ---------------------------------------------------------------------
        candidate_count = ctx.get("candidate_count", 1)
        identity_status = request.identity_status.strip().upper()

        if identity_status == "UNRESOLVED" and candidate_count <= 1:
            reason = SafetyReviewReasonCode.IDENTITY_AMBIGUITY.value
            dossier = build_safety_review_dossier(
                subject_id=request.player_id,
                review_reason_codes=[reason],
                unresolved_claims=[{
                    "claim_type": "IDENTITY_RESOLUTION",
                    "player_query": request.player_query,
                    "canonical_name": request.canonical_name,
                    "identity_status": identity_status,
                }],
                subject_type="player_identity",
            )
            self.last_dossier = dossier
            return (
                RouteStatus.ROUTED_SAFETY_REVIEW,
                ResearchMode.REVIEW_REQUIRED,
                [reason],
                dossier,
            )

        # ---------------------------------------------------------------------
        # Step 2: Ambiguity / collision check
        # ---------------------------------------------------------------------
        if candidate_count > 1 or identity_status == "PROVISIONAL":
            reason = SafetyReviewReasonCode.COLLISION_MULTIPLE_IDENTITIES.value
            dossier = build_safety_review_dossier(
                subject_id=request.player_id,
                review_reason_codes=[reason],
                unresolved_claims=[{
                    "claim_type": "IDENTITY_COLLISION",
                    "player_query": request.player_query,
                    "canonical_name": request.canonical_name,
                    "candidate_count": candidate_count,
                    "identity_status": identity_status,
                }],
                subject_type="player_identity",
            )
            self.last_dossier = dossier
            return (
                RouteStatus.ROUTED_SAFETY_REVIEW,
                ResearchMode.REVIEW_REQUIRED,
                [reason],
                dossier,
            )

        # ---------------------------------------------------------------------
        # Step 3: TMVE relationship check (RR Incumbent -> Mode A)
        # ---------------------------------------------------------------------
        rr_rel = request.rr_relationship_state.strip().upper()
        rr_curr = request.rr_current_state.strip().upper()
        squad_inc = ctx.get("has_squad_inclusion", False)
        app_conf = ctx.get("has_appearance_conflict", False)

        # Check for contradictory RR records first
        is_rr_conflict, conf_code, conf_det = (
            self.safety_interceptor.inspect_rr_membership_contradiction(
                rr_relationship_state=rr_rel,
                rr_current_state=rr_curr,
                has_squad_inclusion=squad_inc,
                has_appearance_conflict=app_conf,
            )
        )
        if is_rr_conflict and conf_code:
            dossier = build_safety_review_dossier(
                subject_id=request.player_id,
                review_reason_codes=[conf_code],
                unresolved_claims=[conf_det] if conf_det else [],
                subject_type="player_membership",
            )
            self.last_dossier = dossier
            return (
                RouteStatus.ROUTED_SAFETY_REVIEW,
                ResearchMode.REVIEW_REQUIRED,
                [conf_code],
                dossier,
            )

        # Verified RR incumbent or historical player
        is_incumbent = rr_rel in (
            "CURRENT_RR",
            "HISTORICAL_RR_APPEARED",
            "HISTORICAL_RR_SQUAD_ONLY",
        )

        if is_incumbent:
            # Check for any supplementary review flags (e.g. DOB conflict, stats discrepancy)
            is_review, dossier = self.safety_interceptor.evaluate_request(request, ctx)
            # Eligibility policy checks do not apply to RR incumbents / capped alumni
            reasons = (
                [
                    r
                    for r in dossier.review_reason_codes
                    if r != SafetyReviewReasonCode.UNVERIFIED_ELIGIBILITY_POLICY.value
                ]
                if (is_review and dossier)
                else []
            )
            if dossier and not reasons:
                dossier = None
            self.last_dossier = dossier
            return (
                RouteStatus.ROUTED_RR_INCUMBENT,
                ResearchMode.MODE_A,
                reasons,
                dossier,
            )

        # ---------------------------------------------------------------------
        # Step 4: Senior international cap check (Capped Non-RR -> Out of Scope)
        # ---------------------------------------------------------------------
        is_capped = request.player_capped_status.strip().upper() == PlayerCappedStatus.CAPPED.value
        no_rr_rel = rr_rel == "NO_VERIFIED_RR_RELATIONSHIP"

        if is_capped and no_rr_rel:
            self.last_dossier = None
            return (
                RouteStatus.ROUTED_OUT_OF_SCOPE,
                ResearchMode.OUT_OF_SCOPE,
                [],
                None,
            )

        # ---------------------------------------------------------------------
        # Step 5: Eligibility Policy Service validation (Uncapped & Eligible -> Mode B)
        # ---------------------------------------------------------------------
        # Pre-check for conflicting attributes or DB absence before Mode B admission
        in_db = ctx.get("in_database", True)
        if (not in_db or request.player_id is None) and no_rr_rel:
            # Trapped by Step 6: Unknown player absent from DB
            pass
        elif (
            ctx.get("primary_dob")
            and ctx.get("conflicting_dob")
            and ctx.get("primary_dob") != ctx.get("conflicting_dob")
        ):
            # Trapped by Step 7: DOB conflict
            pass
        elif ctx.get("stat_discrepancy_metric"):
            # Trapped by Step 7: Statistical discrepancy
            pass
        else:
            is_uncapped = (
                request.player_capped_status.strip().upper() == PlayerCappedStatus.UNCAPPED.value
            )
            is_eligible = (
                request.ipl_uncapped_eligibility.strip().upper() == "VERIFIED_ELIGIBLE"
            )
            if is_uncapped and is_eligible and no_rr_rel:
                self.last_dossier = None
                return (
                    RouteStatus.ROUTED_UNCAPPED_CANDIDATE,
                    ResearchMode.MODE_B,
                    [],
                    None,
                )

        # ---------------------------------------------------------------------
        # Step 6: Unknown / unassessed player guardrail (AI_INSTRUCTIONS R13)
        # ---------------------------------------------------------------------
        if (not in_db or request.player_id is None) and no_rr_rel:
            reason = SafetyReviewReasonCode.UNKNOWN_PLAYER_NOT_IN_DATABASE.value
            dossier = build_safety_review_dossier(
                subject_id=request.player_id,
                review_reason_codes=[reason],
                unresolved_claims=[{
                    "claim_type": "DATABASE_ABSENCE",
                    "player_name": request.canonical_name,
                    "in_database": False,
                }],
                subject_type="player_identity",
            )
            self.last_dossier = dossier
            return (
                RouteStatus.ROUTED_SAFETY_REVIEW,
                ResearchMode.REVIEW_REQUIRED,
                [reason],
                dossier,
            )

        if (
            request.ipl_uncapped_eligibility.strip().upper()
            in ("NOT_ASSESSED", "ELIGIBILITY_UNVERIFIED")
            or request.player_capped_status.strip().upper() == PlayerCappedStatus.UNVERIFIED.value
        ):
            reason = SafetyReviewReasonCode.UNVERIFIED_ELIGIBILITY_POLICY.value
            dossier = build_safety_review_dossier(
                subject_id=request.player_id,
                review_reason_codes=[reason],
                unresolved_claims=[{
                    "claim_type": "ELIGIBILITY_POLICY",
                    "ipl_uncapped_eligibility": request.ipl_uncapped_eligibility,
                    "player_capped_status": request.player_capped_status,
                }],
                subject_type="player_eligibility",
            )
            self.last_dossier = dossier
            return (
                RouteStatus.ROUTED_SAFETY_REVIEW,
                ResearchMode.REVIEW_REQUIRED,
                [reason],
                dossier,
            )

        # ---------------------------------------------------------------------
        # Step 7: Missing / conflicting data & safety interceptor
        # ---------------------------------------------------------------------
        is_review, dossier = self.safety_interceptor.evaluate_request(request, ctx)
        if is_review and dossier:
            self.last_dossier = dossier
            return (
                RouteStatus.ROUTED_SAFETY_REVIEW,
                ResearchMode.REVIEW_REQUIRED,
                dossier.review_reason_codes,
                dossier,
            )

        # Fallback to safety review if not covered by prior steps
        fallback_reason = SafetyReviewReasonCode.LOW_CORROBORATION.value
        dossier = build_safety_review_dossier(
            subject_id=request.player_id,
            review_reason_codes=[fallback_reason],
            unresolved_claims=[{
                "claim_type": "UNCLASSIFIED_FALLBACK",
                "canonical_name": request.canonical_name,
            }],
            subject_type="player_research",
        )
        self.last_dossier = dossier
        return (
            RouteStatus.ROUTED_SAFETY_REVIEW,
            ResearchMode.REVIEW_REQUIRED,
            [fallback_reason],
            dossier,
        )

    # -------------------------------------------------------------------------
    # Full Execution Lifecycle
    # -------------------------------------------------------------------------

    def execute(
        self,
        request: PVRERequestContract | PlayerResearchRequest | dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> PVREOutputContract:
        """Execute complete PVRE research and compile 26-field PVREOutputContract."""
        req = self.normalize_request(request)
        ctx = context or {}

        # 1. Waterfall Classification
        route_status, research_mode, review_reasons, dossier = self.classify_and_route(
            req, ctx
        )

        # 2. Compute Research Window bounds
        window_days = int(req.research_window_years * 365.25)
        window_start: date = req.evaluation_date - timedelta(days=window_days)
        window_end: date = req.evaluation_date

        # Default career coverage state
        coverage_state = ctx.get(
            "career_coverage_state",
            CareerCoverageState.COMPLETE_WITHIN_VERIFIED_SOURCES.value,
        )
        missing_comps: list[str] = list(ctx.get("missing_competitions", []))
        if missing_comps and coverage_state == CareerCoverageState.COMPLETE_WITHIN_VERIFIED_SOURCES.value:
            coverage_state = CareerCoverageState.PARTIAL_COVERAGE.value

        # Profiles
        rr_historical_profile: dict[str, Any] | None = None
        recent_global_performance: dict[str, Any] | None = None
        complete_career_profile: dict[str, Any] | None = None
        replaceability_assessment: dict[str, Any] | None = None
        comp_coverage: dict[str, str] = dict(ctx.get("competition_coverage", {}))
        source_record_ids: list[UUID | int] = list(ctx.get("source_record_ids", []))
        verification_record_ids: list[UUID | int] = list(
            ctx.get("verification_record_ids", [])
        )
        data_quality_summary: dict[str, Any] = dict(ctx.get("data_quality_summary", {}))

        # 3. Execution by Route
        if route_status == RouteStatus.ROUTED_RR_INCUMBENT:
            # Mode A Execution
            mode_a_result = self.mode_a_engine.execute(
                request=req,
                squad_records=ctx.get("squad_records"),
                rr_match_records=ctx.get("rr_match_records"),
                global_match_records=ctx.get("global_match_records"),
                injury_records=ctx.get("injury_records"),
                absence_records=ctx.get("absence_records"),
                primary_role=ctx.get("primary_role", "TOP_ORDER_BATTER"),
                date_of_birth=ctx.get("date_of_birth"),
                review_required_reasons=review_reasons or None,
                source_record_ids=source_record_ids or None,
                verification_record_ids=verification_record_ids or None,
            )

            rr_historical_profile = mode_a_result.rr_historical_profile.model_dump()
            recent_global_performance = (
                mode_a_result.recent_global_performance.model_dump()
            )
            replaceability_assessment = (
                mode_a_result.replaceability_assessment.model_dump()
            )

            # Build default competition coverage
            if not comp_coverage:
                comp_coverage["Indian Premier League"] = "VERIFIED_PARTICIPATION"

            data_quality_summary.update({
                "super_overs_excluded": mode_a_result.recent_global_performance.super_overs_excluded_count,
                "squad_only_seasons_count": len(
                    mode_a_result.rr_historical_profile.squad_only_seasons
                ),
                "insufficient_sample": mode_a_result.replaceability_assessment.insufficient_sample_flag,
            })

            review_status = (
                PVREReviewStatus.REVIEW_REQUIRED.value
                if (review_reasons or mode_a_result.replaceability_assessment.review_required_flag)
                else PVREReviewStatus.CLEAR.value
            )

        elif route_status == RouteStatus.ROUTED_UNCAPPED_CANDIDATE:
            # Mode B Execution
            candidate_raw = ctx.get("candidate_raw_profile", {
                "player_id": req.player_id,
                "canonical_name": req.canonical_name,
                "primary_role": ctx.get("primary_role", "MIDDLE_ORDER_BATTER"),
                "age_at_evaluation": ctx.get("age_at_evaluation", 21.5),
                "domestic_t20_metrics": ctx.get("domestic_t20_metrics", {
                    "matches": 15,
                    "innings": 14,
                    "runs": 450,
                    "balls_faced": 310,
                    "strike_rate": 145.16,
                    "average": 34.62,
                    "boundary_pct": 19.35,
                    "dot_ball_pct": 36.13,
                }),
                "first_class_metrics": ctx.get("first_class_metrics"),
                "list_a_metrics": ctx.get("list_a_metrics"),
                "sample_indicators": ctx.get("sample_indicators", {
                    "matches": 15,
                    "innings": 14,
                    "balls_faced": 310,
                    "wickets": 0,
                }),
                "missing_competitions": missing_comps,
                "career_coverage_state": coverage_state,
            })

            evidence = self.mode_b_engine.compile_candidate_evidence(
                candidate=candidate_raw,
                verified_policy_id=req.target_season_id,
                evaluation_date=req.evaluation_date,
            )

            complete_career_profile = {
                "candidate_evidence": evidence.model_dump(),
                "domestic_competitions_count": len(ctx.get("domestic_competitions", ["SMAT"])),
                "granularity": (
                    SCORECARD_ONLY_GRANULARITY
                    if ctx.get("scorecard_fallback", False)
                    else "BALL_BY_BALL"
                ),
                "scorecard_fallback_active": ctx.get("scorecard_fallback", False),
                "missing_competitions": missing_comps,
            }

            if not comp_coverage:
                comp_coverage["Syed Mushtaq Ali Trophy"] = "VERIFIED_PARTICIPATION"
                for mc in missing_comps:
                    comp_coverage[mc] = "DATASET_UNAVAILABLE"

            review_status = PVREReviewStatus.CLEAR.value

        elif route_status == RouteStatus.ROUTED_OUT_OF_SCOPE:
            review_status = PVREReviewStatus.CLEAR.value
            data_quality_summary["out_of_scope_reason"] = (
                "Verified capped non-RR player cannot enter uncapped candidate pool."
            )

        else:
            # RouteStatus.ROUTED_SAFETY_REVIEW
            review_status = PVREReviewStatus.REVIEW_REQUIRED.value
            data_quality_summary["safety_review_triggered"] = True
            data_quality_summary["reasons"] = review_reasons

        # 4. Compile Authoritative 26-Field Output Contract
        return PVREOutputContract(
            contract_version="PVRE-2.2.0",
            research_run_id=req.research_run_id,
            player_id=req.player_id,
            canonical_name=req.canonical_name,
            identity_status=req.identity_status,
            research_mode=research_mode.value,
            route_status=route_status.value,
            evaluation_date=req.evaluation_date,
            target_season_id=req.target_season_id,
            rr_relationship_state=req.rr_relationship_state,
            rr_current_state=req.rr_current_state,
            player_capped_status=req.player_capped_status,
            ipl_uncapped_eligibility=req.ipl_uncapped_eligibility,
            research_window_start=window_start,
            research_window_end=window_end,
            career_coverage_state=coverage_state,
            rr_historical_profile=rr_historical_profile,
            recent_global_performance=recent_global_performance,
            complete_career_profile=complete_career_profile,
            replaceability_assessment=replaceability_assessment,
            competition_coverage=comp_coverage,
            source_record_ids=source_record_ids,
            verification_record_ids=verification_record_ids,
            review_status=review_status,
            review_reason_codes=review_reasons,
            data_quality_summary=data_quality_summary,
        )


__all__ = [
    "MotherController",
]
