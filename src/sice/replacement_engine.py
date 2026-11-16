"""Squad Intelligence & Composition Engine (SICE) — Replacement Engine (RE-1.0.0).

Executes role-aware 1-to-1 incumbent-vs-candidate replacement evaluation across
16 micro comparison dimensions (D01–D16), incorporating:
- HD-11: Multi-Objective Pareto-Dominance Screening across role criteria
- HD-12: Scorecard-Only Evidence Capping (>4 uncomputable dims -> ANALYTICAL_MONITOR)
- HD-13: Overseas Replacement Slot Liberation (Overseas Incumbent + Indian Candidate)
- Rule R18: Safety Interception Gate (halting on REVIEW_REQUIRED status)
- Strict Separation of Analytical Intelligence from Selection Authority (Rules R20, R21)

Governing Specifications:
- reports/phase6-execution/PHASE6_SICE_READINESS_REPORT.md §7 & §16
- docs/DATA_DICTIONARY.md §10.3 & §11
- docs/RANKING_SPEC.md §9
- docs/TRD.md §8.3 & §8.4
"""

from __future__ import annotations

import hashlib
import logging
import math
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from src.contracts.sice import (
    CandidateReplacementEvaluation,
    DimensionAdvantage,
    DimensionComparisonResult,
    DimensionStatus,
    RecommendationState,
    ReplacementComparisonOutputContract,
    ReplacementComparisonRequest,
    RunType,
)
from src.sice.exceptions import (
    RoleCompatibilityError,
    SafetyReviewInterceptionError,
    SICEError,
)
from src.sice.role_compatibility import (
    CanonicalRole,
    RoleCompatibilityEvaluator,
    normalize_role,
)
from src.sice.similarity import SimilarityCalculator

logger = logging.getLogger(__name__)


class ReplacementCandidateCategory(StrEnum):
    """Candidate-level classification state across developmental and systemic dimensions."""

    DIRECT_UPGRADE = "DIRECT_UPGRADE"
    SYSTEMIC_FIT = "SYSTEMIC_FIT"
    LATERAL_ROTATION = "LATERAL_ROTATION"
    LONG_TERM_PROJECT = "LONG_TERM_PROJECT"
    ANALYTICAL_MONITOR = "ANALYTICAL_MONITOR"


def _extract_attr(obj: Any, key: str, default: Any = None) -> Any:
    """Safely extract attribute or dictionary key from obj."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


_DEFAULT_INCUMBENT_METRICS: dict[str, float] = {
    "strike_rate": 130.0,
    "batting_average": 28.0,
    "boundary_pct": 14.0,
    "dot_ball_pct": 40.0,
    "pp_strike_rate": 125.0,
    "middle_strike_rate": 120.0,
    "death_strike_rate": 140.0,
    "economy_rate": 9.5,
    "bowling_strike_rate": 26.0,
    "bowling_dot_pct": 32.0,
    "death_economy": 11.5,
    "phase_economy": 11.5,
    "dismissals_per_match": 0.2,
}


class ReplacementEngine:
    """Authoritative engine for incumbent-vs-candidate replacement evaluation (RE-1.0.0)."""

    def __init__(
        self,
        similarity_calculator: SimilarityCalculator | None = None,
        role_evaluator: RoleCompatibilityEvaluator | None = None,
        cppae_service: Any | None = None,
        tmve_service: Any | None = None,
        default_seed: int = 42,
    ) -> None:
        self._similarity = similarity_calculator or SimilarityCalculator()
        self._role_evaluator = role_evaluator or RoleCompatibilityEvaluator()
        self._cppae_service = cppae_service
        self._tmve_service = tmve_service
        self._default_seed = default_seed

    # -------------------------------------------------------------------------
    # Public Evaluation Interface
    # -------------------------------------------------------------------------
    def compare_replacement(
        self,
        request: ReplacementComparisonRequest,
        incumbent_dossier: Any | None = None,
        candidate_pool: list[Any] | None = None,
        strict_mode: bool = False,
    ) -> ReplacementComparisonOutputContract:
        """Compare an RR incumbent player against a pool of verified replacement candidates.

        Args:
            request: Typed ReplacementComparisonRequest contract.
            incumbent_dossier: Incumbent PVRE profile / performance dossier.
            candidate_pool: List of candidate profiles / PVRE Mode B evidence objects.
            strict_mode: If True, raises exceptions on safety or compatibility boundaries.

        Returns:
            ReplacementComparisonOutputContract satisfying RE-1.0.0.

        Raises:
            TypeError: If request is not a ReplacementComparisonRequest.
            SafetyReviewInterceptionError: If strict_mode=True and incumbent safety status is
                REVIEW_REQUIRED or CONFLICT.
            SICEError: If incumbent ID is unknown or cannot be resolved.
        """
        if not isinstance(request, ReplacementComparisonRequest):
            raise TypeError(
                f"request must be a ReplacementComparisonRequest, got {type(request).__name__}"
            )

        # 1. Resolve Incumbent Profile
        incumbent = self._resolve_incumbent(request.incumbent_player_id, incumbent_dossier)
        if incumbent is None:
            raise SICEError(
                f"Incumbent player ID {request.incumbent_player_id} could not be resolved",
                code="UNKNOWN_INCUMBENT_ID",
            )

        inc_name = str(_extract_attr(incumbent, "canonical_name", "Unknown Incumbent"))
        inc_role_raw = str(_extract_attr(incumbent, "primary_role", "Top-order Batter"))
        inc_signal = (
            str(
                _extract_attr(incumbent, "replaceability_signal", "POTENTIALLY_REPLACEABLE")
                or "POTENTIALLY_REPLACEABLE"
            )
            .strip()
            .upper()
        )
        inc_review_status = (
            str(_extract_attr(incumbent, "review_status", "CLEAR") or "CLEAR").strip().upper()
        )
        inc_verif_status = (
            str(_extract_attr(incumbent, "verification_status", "CLEAR") or "CLEAR").strip().upper()
        )
        inc_review_dossier_id = _extract_attr(incumbent, "review_dossier_id", None)
        if isinstance(inc_review_dossier_id, str):
            inc_review_dossier_id = UUID(inc_review_dossier_id)

        # Generate reproducible data snapshot SHA256
        snapshot_str = (
            f"{request.incumbent_player_id}:{request.target_season_id}:{request.evaluation_date}:"
            f"{request.config_version}:{self._default_seed}"
        )
        snapshot_sha256 = hashlib.sha256(snapshot_str.encode("utf-8")).hexdigest()

        # 2. Rule R18 Safety Interception Gate
        safety_trigger_statuses = {"REVIEW_REQUIRED", "CONFLICT"}
        if (
            inc_review_status in safety_trigger_statuses
            or inc_verif_status in safety_trigger_statuses
            or inc_signal in safety_trigger_statuses
        ):
            logger.warning(
                "SafetyReviewInterception: Incumbent %s is flagged with safety status "
                "(review_status=%s, verification_status=%s, replaceability_signal=%s)",
                request.incumbent_player_id,
                inc_review_status,
                inc_verif_status,
                inc_signal,
            )
            if strict_mode:
                raise SafetyReviewInterceptionError(
                    f"Incumbent {request.incumbent_player_id} requires human review "
                    f"(review_status={inc_review_status}, verification_status={inc_verif_status}, "
                    f"replaceability_signal={inc_signal})",
                    dossier_id=str(inc_review_dossier_id or uuid4()),
                )
            return ReplacementComparisonOutputContract(
                comparison_id=uuid4(),
                incumbent_player_id=request.incumbent_player_id,
                incumbent_canonical_name=inc_name,
                incumbent_role=inc_role_raw,
                replaceability_signal="REVIEW_REQUIRED",
                evaluation_date=request.evaluation_date,
                target_season_id=request.target_season_id,
                evaluations=[],
                recommended_action=RecommendationState.INSUFFICIENT_EVIDENCE,
                review_status="REVIEW_REQUIRED",
                review_dossier_id=inc_review_dossier_id or uuid4(),
                data_snapshot_sha256=snapshot_sha256,
                computed_at=datetime.now(UTC),
                run_type=RunType.REPLACEMENT_EVALUATION,
                overseas_slot_liberated=False,
            )

        # 3. Resolve Candidate Pool
        raw_pool = candidate_pool if candidate_pool is not None else []
        if request.candidate_pool_ids is not None:
            target_ids = set(request.candidate_pool_ids)
            raw_pool = [
                c
                for c in raw_pool
                if UUID(str(_extract_attr(c, "candidate_player_id", uuid4()))) in target_ids
            ]

        # Filter out candidates with REVIEW_REQUIRED or CONFLICT (Safety Gate Suite 8, Rule R18)
        safe_candidates: list[Any] = []
        for cand in raw_pool:
            cand_rev = str(_extract_attr(cand, "review_status", "CLEAR") or "CLEAR").strip().upper()
            cand_verif = (
                str(_extract_attr(cand, "verification_status", "CLEAR") or "CLEAR").strip().upper()
            )
            if cand_rev in safety_trigger_statuses or cand_verif in safety_trigger_statuses:
                logger.info(
                    "Safety Gate: Excluding candidate %s due to review_status=%s, verification_status=%s",
                    _extract_attr(cand, "candidate_player_id"),
                    cand_rev,
                    cand_verif,
                )
                continue
            safe_candidates.append(cand)

        # 4. Evaluate Each Candidate across 16 Dimensions
        candidate_evaluations: list[CandidateReplacementEvaluation] = []
        candidate_categories: dict[UUID, ReplacementCandidateCategory] = {}

        for cand in safe_candidates:
            eval_res, cat = self._evaluate_single_candidate(
                incumbent=incumbent,
                candidate=cand,
                evaluation_date=request.evaluation_date,
                strict_mode=strict_mode,
            )
            if eval_res is not None:
                candidate_evaluations.append(eval_res)
                candidate_categories[eval_res.candidate_player_id] = cat

        # 5. HD-11: Multi-Objective Pareto-Dominance Screening
        pareto_front = self._screen_pareto_frontier(
            incumbent=incumbent,
            evaluations=candidate_evaluations,
            categories=candidate_categories,
        )

        # 6. Overall Recommended Action Synthesis
        overall_action, overseas_liberated = self._synthesize_incumbent_action(
            incumbent_signal=inc_signal,
            evaluations=pareto_front,
            total_candidate_count=len(safe_candidates),
        )

        return ReplacementComparisonOutputContract(
            comparison_id=uuid4(),
            incumbent_player_id=request.incumbent_player_id,
            incumbent_canonical_name=inc_name,
            incumbent_role=inc_role_raw,
            replaceability_signal=inc_signal,
            evaluation_date=request.evaluation_date,
            target_season_id=request.target_season_id,
            evaluations=pareto_front,
            recommended_action=overall_action,
            review_status="CLEAR",
            review_dossier_id=None,
            data_snapshot_sha256=snapshot_sha256,
            computed_at=datetime.now(UTC),
            run_type=RunType.REPLACEMENT_EVALUATION,
            overseas_slot_liberated=overseas_liberated,
        )

    # -------------------------------------------------------------------------
    # Single Candidate Evaluation
    # -------------------------------------------------------------------------
    def _evaluate_single_candidate(
        self,
        incumbent: Any,
        candidate: Any,
        evaluation_date: date,
        strict_mode: bool = False,
    ) -> tuple[CandidateReplacementEvaluation | None, ReplacementCandidateCategory]:
        """Evaluate a single candidate against the incumbent across 16 dimensions."""
        cand_id_raw = _extract_attr(candidate, "candidate_player_id", uuid4())
        cand_id = UUID(str(cand_id_raw)) if not isinstance(cand_id_raw, UUID) else cand_id_raw
        cand_name = str(_extract_attr(candidate, "canonical_name", "Unknown Candidate"))

        # Age calculation
        cand_age = self._resolve_age(candidate, evaluation_date)
        inc_age = self._resolve_age(incumbent, evaluation_date)

        # Role compatibility evaluation
        inc_role = str(_extract_attr(incumbent, "primary_role", "Top-order Batter"))
        cand_role = str(_extract_attr(candidate, "primary_role", "Top-order Batter"))
        inc_hand = _extract_attr(incumbent, "batting_hand")
        cand_hand = _extract_attr(candidate, "batting_hand")
        inc_style = _extract_attr(incumbent, "bowling_style")
        cand_style = _extract_attr(candidate, "bowling_style")
        inc_wk = bool(_extract_attr(incumbent, "is_wicketkeeper", False))
        cand_wk = bool(_extract_attr(candidate, "is_wicketkeeper", False))

        try:
            compat_res = self._role_evaluator.evaluate_compatibility(
                incumbent_role=inc_role,
                candidate_role=cand_role,
                incumbent_batting_hand=inc_hand,
                candidate_batting_hand=cand_hand,
                incumbent_bowling_style=inc_style,
                candidate_bowling_style=cand_style,
                incumbent_is_wk=inc_wk,
                candidate_is_wk=cand_wk,
                strict_mode=strict_mode,
            )
        except RoleCompatibilityError:
            if strict_mode:
                raise
            return None, ReplacementCandidateCategory.ANALYTICAL_MONITOR

        if compat_res.hard_boundary_violated and compat_res.compatibility_score <= 1e-9:
            return None, ReplacementCandidateCategory.ANALYTICAL_MONITOR

        # Evaluate the 16 dimensions (D01–D16)
        dimensions = self._compute_16_dimensions(
            incumbent=incumbent,
            candidate=candidate,
            inc_age=inc_age,
            cand_age=cand_age,
        )

        # HD-12: Scorecard-Only Cap Check
        uncomp_count = sum(
            1
            for d in dimensions
            if d.dimension_status
            in (DimensionStatus.NOT_COMPUTABLE, DimensionStatus.SCORECARD_ONLY)
        )
        capped_by_scorecard = uncomp_count > 4

        # HD-13: Overseas Slot Liberation Logic
        overseas_slot_liberated = self._check_overseas_slot_liberation(incumbent, candidate)

        # Similarities
        similarity_scores = self._compute_candidate_similarities(incumbent, candidate)

        # Classify candidate category
        candidate_category = self._classify_candidate_category(
            compat_score=compat_res.compatibility_score,
            dimensions=dimensions,
            age_delta=(cand_age - inc_age),
            capped_by_scorecard=capped_by_scorecard,
            similarity_scores=similarity_scores,
        )

        # Map to RecommendationState
        if candidate_category in (
            ReplacementCandidateCategory.DIRECT_UPGRADE,
            ReplacementCandidateCategory.SYSTEMIC_FIT,
        ):
            rec_state = (
                RecommendationState.ANALYTICAL_MONITOR
                if capped_by_scorecard
                else RecommendationState.ANALYTICAL_REPLACEMENT_CANDIDATE
            )
        else:
            rec_state = RecommendationState.ANALYTICAL_MONITOR

        # Verification IDs
        verif_ids = _extract_attr(candidate, "evidence_verification_ids", [])
        if not isinstance(verif_ids, list):
            verif_ids = []
        typed_verif_ids = [UUID(str(v)) if not isinstance(v, UUID) else v for v in verif_ids]

        confidence = float(_extract_attr(candidate, "confidence", 1.0))
        confidence = max(0.0, min(1.0, confidence))

        eval_result = CandidateReplacementEvaluation(
            candidate_player_id=cand_id,
            canonical_name=cand_name,
            age_at_evaluation=round(cand_age, 2),
            role_compatibility=f"{round(compat_res.compatibility_score, 2)} ({compat_res.transition_category.value})",
            recommendation_label=rec_state,
            dimension_comparisons=dimensions,
            evidence_verification_ids=typed_verif_ids,
            confidence=confidence,
            overseas_slot_liberated=overseas_slot_liberated,
            similarity_scores=similarity_scores,
        )

        return eval_result, candidate_category

    # -------------------------------------------------------------------------
    # 16 Dimensions Computation (D01–D16)
    # -------------------------------------------------------------------------
    def _compute_16_dimensions(
        self,
        incumbent: Any,
        candidate: Any,
        inc_age: float,
        cand_age: float,
    ) -> list[DimensionComparisonResult]:
        """Compute point-by-point comparison across all 16 micro dimensions."""
        dims: list[DimensionComparisonResult] = []

        is_scorecard_candidate = bool(
            _extract_attr(candidate, "is_scorecard_only", False)
            or _extract_attr(candidate, "evidence_tier") == "SCORECARD_ONLY"
        )

        # Helper to fetch metric values
        def get_m(obj: Any, key: str, fallback_key: str | None = None) -> float | None:
            metrics = (
                _extract_attr(obj, "domestic_t20_metrics") or _extract_attr(obj, "metrics") or {}
            )
            v = _extract_attr(metrics, key)
            if v is None and fallback_key:
                v = _extract_attr(metrics, fallback_key)
            if v is None:
                v = _extract_attr(obj, key)
            if v is None and fallback_key:
                v = _extract_attr(obj, fallback_key)
            if v is not None:
                try:
                    f = float(v)
                    if math.isnan(f) or math.isinf(f):
                        return None
                    return f
                except (ValueError, TypeError):
                    return None
            return None

        def get_sample(obj: Any, key: str) -> int | None:
            samples = _extract_attr(obj, "sample_indicators") or _extract_attr(obj, "samples") or {}
            s = _extract_attr(samples, key)
            if s is None:
                s = _extract_attr(obj, key)
            if s is not None:
                try:
                    return int(s)
                except (ValueError, TypeError):
                    return None
            return None

        # D01: Base Scoring Rate (Batting SR) [Forward]
        inc_sr = get_m(incumbent, "strike_rate", "batting_strike_rate")
        cand_sr = get_m(candidate, "strike_rate", "batting_strike_rate")
        cand_balls = get_sample(candidate, "balls_faced") or get_sample(candidate, "sample_balls")
        if cand_balls is None:
            cand_balls = 100 if cand_sr is not None else 0
        inc_balls = get_sample(incumbent, "balls_faced") or (100 if inc_sr is not None else 0)

        if cand_balls < 20:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D01",
                    dimension_name="Base Scoring Rate",
                    incumbent_value=inc_sr,
                    candidate_value=cand_sr,
                    delta=None,
                    incumbent_sample=inc_balls,
                    candidate_sample=cand_balls,
                    advantage=DimensionAdvantage.NOT_APPLICABLE,
                    computable=False,
                    dimension_status=DimensionStatus.INSUFFICIENT_SAMPLE,
                    notes="Balls faced < 20",
                )
            )
        elif inc_sr is not None and cand_sr is not None:
            delta = round(cand_sr - inc_sr, 2)
            adv = (
                DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE
                if delta > 5.0
                else (
                    DimensionAdvantage.SIGNIFICANT_INCUMBENT_ADVANTAGE
                    if delta < -5.0
                    else DimensionAdvantage.PARITY_WITHIN_UNCERTAINTY
                )
            )
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D01",
                    dimension_name="Base Scoring Rate",
                    incumbent_value=inc_sr,
                    candidate_value=cand_sr,
                    delta=delta,
                    incumbent_sample=inc_balls,
                    candidate_sample=cand_balls,
                    advantage=adv,
                    confidence_interval_lower=round(delta - 4.5, 2),
                    confidence_interval_upper=round(delta + 4.5, 2),
                    computable=True,
                    dimension_status=DimensionStatus.COMPUTED,
                )
            )
        else:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D01",
                    dimension_name="Base Scoring Rate",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )

        # D02: Dismissal Resistance (Batting Avg) [Forward]
        inc_avg = get_m(incumbent, "batting_average", "average")
        cand_avg = get_m(candidate, "batting_average", "average")
        cand_dismissals = get_sample(candidate, "dismissals")
        if cand_dismissals is None:
            cand_dismissals = 10 if cand_balls >= 50 else 2

        if cand_dismissals == 0 and cand_balls > 0:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D02",
                    dimension_name="Dismissal Resistance",
                    incumbent_value=inc_avg,
                    candidate_value=cand_avg,
                    delta=None,
                    incumbent_sample=inc_balls,
                    candidate_sample=cand_balls,
                    advantage=DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE,
                    computable=False,
                    dimension_status=DimensionStatus.UNDEFEATED_IN_WINDOW,
                    notes="Candidate undefeated in evaluation window",
                )
            )
        elif cand_dismissals < 5 and cand_balls < 50:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D02",
                    dimension_name="Dismissal Resistance",
                    incumbent_value=inc_avg,
                    candidate_value=cand_avg,
                    delta=None,
                    incumbent_sample=inc_balls,
                    candidate_sample=cand_balls,
                    advantage=DimensionAdvantage.NOT_APPLICABLE,
                    computable=False,
                    dimension_status=DimensionStatus.INSUFFICIENT_SAMPLE,
                    notes="Dismissals < 5 and balls < 50",
                )
            )
        elif inc_avg is not None and cand_avg is not None:
            delta = round(cand_avg - inc_avg, 2)
            adv = (
                DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE
                if delta > 3.0
                else (
                    DimensionAdvantage.SIGNIFICANT_INCUMBENT_ADVANTAGE
                    if delta < -3.0
                    else DimensionAdvantage.PARITY_WITHIN_UNCERTAINTY
                )
            )
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D02",
                    dimension_name="Dismissal Resistance",
                    incumbent_value=inc_avg,
                    candidate_value=cand_avg,
                    delta=delta,
                    incumbent_sample=inc_balls,
                    candidate_sample=cand_balls,
                    advantage=adv,
                    confidence_interval_lower=round(delta - 3.0, 2),
                    confidence_interval_upper=round(delta + 3.0, 2),
                    computable=True,
                    dimension_status=DimensionStatus.COMPUTED,
                )
            )
        else:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D02",
                    dimension_name="Dismissal Resistance",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )

        # D03: Boundary Generation (Boundary %) [Forward]
        inc_bnd = get_m(incumbent, "boundary_pct")
        cand_bnd = get_m(candidate, "boundary_pct")
        if cand_balls < 20:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D03",
                    dimension_name="Boundary Generation",
                    computable=False,
                    dimension_status=DimensionStatus.INSUFFICIENT_SAMPLE,
                )
            )
        elif inc_bnd is not None and cand_bnd is not None:
            delta = round(cand_bnd - inc_bnd, 2)
            adv = (
                DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE
                if delta > 2.0
                else (
                    DimensionAdvantage.SIGNIFICANT_INCUMBENT_ADVANTAGE
                    if delta < -2.0
                    else DimensionAdvantage.PARITY_WITHIN_UNCERTAINTY
                )
            )
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D03",
                    dimension_name="Boundary Generation",
                    incumbent_value=inc_bnd,
                    candidate_value=cand_bnd,
                    delta=delta,
                    incumbent_sample=inc_balls,
                    candidate_sample=cand_balls,
                    advantage=adv,
                    confidence_interval_lower=round(delta - 2.0, 2),
                    confidence_interval_upper=round(delta + 2.0, 2),
                    computable=True,
                    dimension_status=DimensionStatus.COMPUTED,
                )
            )
        else:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D03",
                    dimension_name="Boundary Generation",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )

        # D04: Dot Ball Suppression (Batting Dot %) [Inverted: Inc - Cand]
        inc_dot = get_m(incumbent, "dot_ball_pct")
        cand_dot = get_m(candidate, "dot_ball_pct")
        if is_scorecard_candidate:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D04",
                    dimension_name="Dot Ball Suppression",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                    notes="Scorecard granularity limits delivery tracking",
                )
            )
        elif cand_balls < 30:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D04",
                    dimension_name="Dot Ball Suppression",
                    computable=False,
                    dimension_status=DimensionStatus.INSUFFICIENT_SAMPLE,
                )
            )
        elif cand_dot is None:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D04",
                    dimension_name="Dot Ball Suppression",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                    notes="Scorecard granularity limits delivery tracking",
                )
            )
        elif inc_dot is not None:
            delta = round(inc_dot - cand_dot, 2)  # Inverted
            adv = (
                DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE
                if delta > 3.0
                else (
                    DimensionAdvantage.SIGNIFICANT_INCUMBENT_ADVANTAGE
                    if delta < -3.0
                    else DimensionAdvantage.PARITY_WITHIN_UNCERTAINTY
                )
            )
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D04",
                    dimension_name="Dot Ball Suppression",
                    incumbent_value=inc_dot,
                    candidate_value=cand_dot,
                    delta=delta,
                    incumbent_sample=inc_balls,
                    candidate_sample=cand_balls,
                    advantage=adv,
                    confidence_interval_lower=round(delta - 2.5, 2),
                    confidence_interval_upper=round(delta + 2.5, 2),
                    computable=True,
                    dimension_status=DimensionStatus.COMPUTED,
                )
            )
        else:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D04",
                    dimension_name="Dot Ball Suppression",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )

        # D05: Powerplay Batting Impact (PP Batting SR) [Forward]
        inc_pp_sr = get_m(incumbent, "pp_strike_rate")
        cand_pp_sr = get_m(candidate, "pp_strike_rate")
        cand_pp_balls = get_sample(candidate, "pp_balls")
        if cand_pp_balls is None:
            cand_pp_balls = 30 if (cand_pp_sr is not None and not is_scorecard_candidate) else 0

        if is_scorecard_candidate:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D05",
                    dimension_name="Powerplay Batting Impact",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )
        elif cand_balls < 20 or (cand_pp_balls < 15 and cand_pp_sr is None):
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D05",
                    dimension_name="Powerplay Batting Impact",
                    computable=False,
                    dimension_status=DimensionStatus.INSUFFICIENT_SAMPLE,
                )
            )
        elif cand_pp_sr is None:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D05",
                    dimension_name="Powerplay Batting Impact",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )
        elif cand_pp_balls < 15:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D05",
                    dimension_name="Powerplay Batting Impact",
                    computable=False,
                    dimension_status=DimensionStatus.INSUFFICIENT_SAMPLE,
                )
            )
        elif inc_pp_sr is not None:
            delta = round(cand_pp_sr - inc_pp_sr, 2)
            adv = (
                DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE
                if delta > 5.0
                else (
                    DimensionAdvantage.SIGNIFICANT_INCUMBENT_ADVANTAGE
                    if delta < -5.0
                    else DimensionAdvantage.PARITY_WITHIN_UNCERTAINTY
                )
            )
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D05",
                    dimension_name="Powerplay Batting Impact",
                    incumbent_value=inc_pp_sr,
                    candidate_value=cand_pp_sr,
                    delta=delta,
                    incumbent_sample=60,
                    candidate_sample=cand_pp_balls,
                    advantage=adv,
                    confidence_interval_lower=round(delta - 4.0, 2),
                    confidence_interval_upper=round(delta + 4.0, 2),
                    computable=True,
                    dimension_status=DimensionStatus.COMPUTED,
                )
            )
        else:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D05",
                    dimension_name="Powerplay Batting Impact",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )

        # D06: Middle Acceleration (Middle Batting SR) [Forward]
        inc_mid_sr = get_m(incumbent, "middle_strike_rate")
        cand_mid_sr = get_m(candidate, "middle_strike_rate")
        cand_mid_balls = get_sample(candidate, "middle_balls")
        if cand_mid_balls is None:
            cand_mid_balls = 40 if (cand_mid_sr is not None and not is_scorecard_candidate) else 0

        if is_scorecard_candidate:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D06",
                    dimension_name="Middle Acceleration",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )
        elif cand_balls < 20 or (cand_mid_balls < 20 and cand_mid_sr is None):
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D06",
                    dimension_name="Middle Acceleration",
                    computable=False,
                    dimension_status=DimensionStatus.INSUFFICIENT_SAMPLE,
                )
            )
        elif cand_mid_sr is None:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D06",
                    dimension_name="Middle Acceleration",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )
        elif cand_mid_balls < 20:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D06",
                    dimension_name="Middle Acceleration",
                    computable=False,
                    dimension_status=DimensionStatus.INSUFFICIENT_SAMPLE,
                )
            )
        elif inc_mid_sr is not None:
            delta = round(cand_mid_sr - inc_mid_sr, 2)
            adv = (
                DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE
                if delta > 5.0
                else (
                    DimensionAdvantage.SIGNIFICANT_INCUMBENT_ADVANTAGE
                    if delta < -5.0
                    else DimensionAdvantage.PARITY_WITHIN_UNCERTAINTY
                )
            )
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D06",
                    dimension_name="Middle Acceleration",
                    incumbent_value=inc_mid_sr,
                    candidate_value=cand_mid_sr,
                    delta=delta,
                    incumbent_sample=80,
                    candidate_sample=cand_mid_balls,
                    advantage=adv,
                    confidence_interval_lower=round(delta - 4.0, 2),
                    confidence_interval_upper=round(delta + 4.0, 2),
                    computable=True,
                    dimension_status=DimensionStatus.COMPUTED,
                )
            )
        else:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D06",
                    dimension_name="Middle Acceleration",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )

        # D07: Death-Overs Execution (Death Batting SR) [Forward]
        inc_death_sr = get_m(incumbent, "death_strike_rate")
        cand_death_sr = get_m(candidate, "death_strike_rate")
        cand_death_balls = get_sample(candidate, "death_balls")
        if cand_death_balls is None:
            cand_death_balls = (
                30 if (cand_death_sr is not None and not is_scorecard_candidate) else 0
            )

        if is_scorecard_candidate:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D07",
                    dimension_name="Death-Overs Execution",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )
        elif cand_balls < 20 or (cand_death_balls < 10 and cand_death_sr is None):
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D07",
                    dimension_name="Death-Overs Execution",
                    computable=False,
                    dimension_status=DimensionStatus.INSUFFICIENT_SAMPLE,
                )
            )
        elif cand_death_sr is None:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D07",
                    dimension_name="Death-Overs Execution",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )
        elif cand_death_balls < 15:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D07",
                    dimension_name="Death-Overs Execution",
                    computable=False,
                    dimension_status=DimensionStatus.INSUFFICIENT_SAMPLE,
                )
            )
        elif inc_death_sr is not None:
            delta = round(cand_death_sr - inc_death_sr, 2)
            adv = (
                DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE
                if delta > 7.0
                else (
                    DimensionAdvantage.SIGNIFICANT_INCUMBENT_ADVANTAGE
                    if delta < -7.0
                    else DimensionAdvantage.PARITY_WITHIN_UNCERTAINTY
                )
            )
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D07",
                    dimension_name="Death-Overs Execution",
                    incumbent_value=inc_death_sr,
                    candidate_value=cand_death_sr,
                    delta=delta,
                    incumbent_sample=50,
                    candidate_sample=cand_death_balls,
                    advantage=adv,
                    confidence_interval_lower=round(delta - 6.0, 2),
                    confidence_interval_upper=round(delta + 6.0, 2),
                    computable=True,
                    dimension_status=DimensionStatus.COMPUTED,
                )
            )
        else:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D07",
                    dimension_name="Death-Overs Execution",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )

        # D08: Run Suppression (Bowling Economy) [Inverted: Inc - Cand]
        inc_econ = get_m(incumbent, "economy_rate", "economy")
        cand_econ = get_m(candidate, "economy_rate", "economy")
        cand_bowling_balls = get_sample(candidate, "balls_bowled") or get_sample(
            candidate, "bowling_balls"
        )
        if cand_bowling_balls is None:
            cand_bowling_balls = 60 if cand_econ is not None else 0
        inc_bowling_balls = get_sample(incumbent, "balls_bowled") or (
            60 if inc_econ is not None else 0
        )

        if cand_bowling_balls < 30:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D08",
                    dimension_name="Run Suppression (Economy)",
                    computable=False,
                    dimension_status=DimensionStatus.INSUFFICIENT_SAMPLE,
                    notes="Balls bowled < 30",
                )
            )
        elif inc_econ is not None and cand_econ is not None:
            delta = round(inc_econ - cand_econ, 2)  # Inverted
            adv = (
                DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE
                if delta > 0.35
                else (
                    DimensionAdvantage.SIGNIFICANT_INCUMBENT_ADVANTAGE
                    if delta < -0.35
                    else DimensionAdvantage.PARITY_WITHIN_UNCERTAINTY
                )
            )
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D08",
                    dimension_name="Run Suppression (Economy)",
                    incumbent_value=inc_econ,
                    candidate_value=cand_econ,
                    delta=delta,
                    incumbent_sample=inc_bowling_balls,
                    candidate_sample=cand_bowling_balls,
                    advantage=adv,
                    confidence_interval_lower=round(delta - 0.40, 2),
                    confidence_interval_upper=round(delta + 0.40, 2),
                    computable=True,
                    dimension_status=DimensionStatus.COMPUTED,
                )
            )
        else:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D08",
                    dimension_name="Run Suppression (Economy)",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )

        # D09: Wicket Efficiency (Bowling SR) [Inverted: Inc - Cand]
        inc_bowl_sr = get_m(incumbent, "bowling_strike_rate")
        cand_bowl_sr = get_m(candidate, "bowling_strike_rate")
        cand_wkts = get_sample(candidate, "wickets")
        if cand_wkts is None:
            cand_wkts = 5 if cand_bowling_balls >= 60 else (0 if cand_bowling_balls == 0 else 1)

        if cand_wkts == 0 and cand_bowling_balls > 0:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D09",
                    dimension_name="Wicket Efficiency",
                    incumbent_value=inc_bowl_sr,
                    candidate_value=cand_bowl_sr,
                    delta=None,
                    incumbent_sample=inc_bowling_balls,
                    candidate_sample=cand_bowling_balls,
                    advantage=DimensionAdvantage.NOT_APPLICABLE,
                    computable=False,
                    dimension_status=DimensionStatus.ZERO_WICKETS,
                    notes="Candidate took 0 wickets in window",
                )
            )
        elif cand_wkts < 3 or cand_bowling_balls < 30:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D09",
                    dimension_name="Wicket Efficiency",
                    computable=False,
                    dimension_status=DimensionStatus.INSUFFICIENT_SAMPLE,
                    notes="Wickets < 3 or balls < 30",
                )
            )
        elif inc_bowl_sr is not None and cand_bowl_sr is not None:
            delta = round(inc_bowl_sr - cand_bowl_sr, 2)  # Inverted
            adv = (
                DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE
                if delta > 2.0
                else (
                    DimensionAdvantage.SIGNIFICANT_INCUMBENT_ADVANTAGE
                    if delta < -2.0
                    else DimensionAdvantage.PARITY_WITHIN_UNCERTAINTY
                )
            )
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D09",
                    dimension_name="Wicket Efficiency",
                    incumbent_value=inc_bowl_sr,
                    candidate_value=cand_bowl_sr,
                    delta=delta,
                    incumbent_sample=inc_bowling_balls,
                    candidate_sample=cand_bowling_balls,
                    advantage=adv,
                    confidence_interval_lower=round(delta - 2.0, 2),
                    confidence_interval_upper=round(delta + 2.0, 2),
                    computable=True,
                    dimension_status=DimensionStatus.COMPUTED,
                )
            )
        else:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D09",
                    dimension_name="Wicket Efficiency",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )

        # D10: Bowling Dot Pressure (Bowling Dot %) [Forward]
        inc_bowl_dot = get_m(incumbent, "bowling_dot_pct")
        cand_bowl_dot = get_m(candidate, "bowling_dot_pct")
        if is_scorecard_candidate:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D10",
                    dimension_name="Bowling Dot Pressure",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )
        elif cand_bowling_balls < 30:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D10",
                    dimension_name="Bowling Dot Pressure",
                    computable=False,
                    dimension_status=DimensionStatus.INSUFFICIENT_SAMPLE,
                )
            )
        elif cand_bowl_dot is None:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D10",
                    dimension_name="Bowling Dot Pressure",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )
        elif inc_bowl_dot is not None:
            delta = round(cand_bowl_dot - inc_bowl_dot, 2)
            adv = (
                DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE
                if delta > 3.0
                else (
                    DimensionAdvantage.SIGNIFICANT_INCUMBENT_ADVANTAGE
                    if delta < -3.0
                    else DimensionAdvantage.PARITY_WITHIN_UNCERTAINTY
                )
            )
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D10",
                    dimension_name="Bowling Dot Pressure",
                    incumbent_value=inc_bowl_dot,
                    candidate_value=cand_bowl_dot,
                    delta=delta,
                    incumbent_sample=inc_bowling_balls,
                    candidate_sample=cand_bowling_balls,
                    advantage=adv,
                    confidence_interval_lower=round(delta - 2.5, 2),
                    confidence_interval_upper=round(delta + 2.5, 2),
                    computable=True,
                    dimension_status=DimensionStatus.COMPUTED,
                )
            )
        else:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D10",
                    dimension_name="Bowling Dot Pressure",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )

        # D11: Phase Bowling Control (Phase Bowling Econ) [Inverted: Inc - Cand]
        inc_phase_econ = get_m(incumbent, "death_economy", "phase_economy")
        cand_phase_econ = get_m(candidate, "death_economy", "phase_economy")
        cand_phase_balls = get_sample(candidate, "death_balls_bowled")
        if cand_phase_balls is None:
            cand_phase_balls = (
                24 if (cand_phase_econ is not None and not is_scorecard_candidate) else 0
            )

        if is_scorecard_candidate:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D11",
                    dimension_name="Phase Bowling Control",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )
        elif cand_phase_econ is None:
            if cand_bowling_balls < 30:
                dims.append(
                    DimensionComparisonResult(
                        dimension_id="D11",
                        dimension_name="Phase Bowling Control",
                        computable=False,
                        dimension_status=DimensionStatus.INSUFFICIENT_SAMPLE,
                    )
                )
            else:
                dims.append(
                    DimensionComparisonResult(
                        dimension_id="D11",
                        dimension_name="Phase Bowling Control",
                        computable=False,
                        dimension_status=DimensionStatus.NOT_COMPUTABLE,
                    )
                )
        elif cand_phase_balls < 12:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D11",
                    dimension_name="Phase Bowling Control",
                    computable=False,
                    dimension_status=DimensionStatus.INSUFFICIENT_SAMPLE,
                )
            )
        elif inc_phase_econ is not None:
            delta = round(inc_phase_econ - cand_phase_econ, 2)  # Inverted
            adv = (
                DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE
                if delta > 0.50
                else (
                    DimensionAdvantage.SIGNIFICANT_INCUMBENT_ADVANTAGE
                    if delta < -0.50
                    else DimensionAdvantage.PARITY_WITHIN_UNCERTAINTY
                )
            )
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D11",
                    dimension_name="Phase Bowling Control",
                    incumbent_value=inc_phase_econ,
                    candidate_value=cand_phase_econ,
                    delta=delta,
                    incumbent_sample=36,
                    candidate_sample=cand_phase_balls,
                    advantage=adv,
                    confidence_interval_lower=round(delta - 0.60, 2),
                    confidence_interval_upper=round(delta + 0.60, 2),
                    computable=True,
                    dimension_status=DimensionStatus.COMPUTED,
                )
            )
        else:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D11",
                    dimension_name="Phase Bowling Control",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )

        # D12: Matchup Resilience (Pace/Spin Split Delta) [Forward]
        inc_matchup = get_m(incumbent, "matchup_index")
        cand_matchup = get_m(candidate, "matchup_index")
        if cand_matchup is None or is_scorecard_candidate:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D12",
                    dimension_name="Matchup Resilience",
                    computable=False,
                    dimension_status=DimensionStatus.STYLE_UNAVAILABLE,
                    notes="Opponent style/split tracking unavailable",
                )
            )
        elif inc_matchup is not None:
            delta = round(cand_matchup - inc_matchup, 2)
            adv = (
                DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE
                if delta > 5.0
                else (
                    DimensionAdvantage.SIGNIFICANT_INCUMBENT_ADVANTAGE
                    if delta < -5.0
                    else DimensionAdvantage.PARITY_WITHIN_UNCERTAINTY
                )
            )
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D12",
                    dimension_name="Matchup Resilience",
                    incumbent_value=inc_matchup,
                    candidate_value=cand_matchup,
                    delta=delta,
                    advantage=adv,
                    computable=True,
                    dimension_status=DimensionStatus.COMPUTED,
                )
            )
        else:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D12",
                    dimension_name="Matchup Resilience",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )

        # D13: High-Leverage Execution [Forward]
        inc_lev = get_m(incumbent, "high_leverage_metric", "pressure_index")
        cand_lev = get_m(candidate, "high_leverage_metric", "pressure_index")
        if cand_lev is None or is_scorecard_candidate:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D13",
                    dimension_name="High-Leverage Execution",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )
        elif inc_lev is not None:
            delta = round(cand_lev - inc_lev, 2)
            adv = (
                DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE
                if delta > 5.0
                else (
                    DimensionAdvantage.SIGNIFICANT_INCUMBENT_ADVANTAGE
                    if delta < -5.0
                    else DimensionAdvantage.PARITY_WITHIN_UNCERTAINTY
                )
            )
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D13",
                    dimension_name="High-Leverage Execution",
                    incumbent_value=inc_lev,
                    candidate_value=cand_lev,
                    delta=delta,
                    advantage=adv,
                    computable=True,
                    dimension_status=DimensionStatus.COMPUTED,
                )
            )
        else:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D13",
                    dimension_name="High-Leverage Execution",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )

        # D14: Fielding Contribution (Dismissals/match) [Forward]
        inc_field = get_m(incumbent, "dismissals_per_match", "fielding_dismissals_per_match")
        cand_field = get_m(candidate, "dismissals_per_match", "fielding_dismissals_per_match")
        cand_apps = get_sample(candidate, "appearances") or get_sample(candidate, "matches") or 10

        if cand_apps < 5:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D14",
                    dimension_name="Fielding Contribution",
                    computable=False,
                    dimension_status=DimensionStatus.INSUFFICIENT_SAMPLE,
                )
            )
        elif inc_field is not None and cand_field is not None:
            delta = round(cand_field - inc_field, 2)
            adv = (
                DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE
                if delta > 0.15
                else (
                    DimensionAdvantage.SIGNIFICANT_INCUMBENT_ADVANTAGE
                    if delta < -0.15
                    else DimensionAdvantage.PARITY_WITHIN_UNCERTAINTY
                )
            )
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D14",
                    dimension_name="Fielding Contribution",
                    incumbent_value=inc_field,
                    candidate_value=cand_field,
                    delta=delta,
                    incumbent_sample=20,
                    candidate_sample=cand_apps,
                    advantage=adv,
                    confidence_interval_lower=round(delta - 0.15, 2),
                    confidence_interval_upper=round(delta + 0.15, 2),
                    computable=True,
                    dimension_status=DimensionStatus.COMPUTED,
                )
            )
        else:
            dims.append(
                DimensionComparisonResult(
                    dimension_id="D14",
                    dimension_name="Fielding Contribution",
                    computable=False,
                    dimension_status=DimensionStatus.NOT_COMPUTABLE,
                )
            )

        # D15: Age & Trajectory Delta (Negative = Candidate younger)
        age_delta = round(cand_age - inc_age, 2)
        adv_age = (
            DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE
            if age_delta <= -2.0
            else (
                DimensionAdvantage.SIGNIFICANT_INCUMBENT_ADVANTAGE
                if age_delta >= 2.0
                else DimensionAdvantage.PARITY_WITHIN_UNCERTAINTY
            )
        )
        dims.append(
            DimensionComparisonResult(
                dimension_id="D15",
                dimension_name="Age & Trajectory Delta",
                incumbent_value=round(inc_age, 1),
                candidate_value=round(cand_age, 1),
                delta=age_delta,
                advantage=adv_age,
                computable=True,
                dimension_status=DimensionStatus.COMPUTED,
                notes="Negative delta indicates candidate is younger",
            )
        )

        # D16: Sample Adequacy & Tier
        cand_total_sample = cand_balls + cand_bowling_balls
        inc_total_sample = max(1, inc_balls + inc_bowling_balls)
        ratio = round(cand_total_sample / float(inc_total_sample), 2)
        tier_tag = "SCORECARD_ONLY" if is_scorecard_candidate else "TIER_1_OFFICIAL"

        dims.append(
            DimensionComparisonResult(
                dimension_id="D16",
                dimension_name="Sample Adequacy & Tier",
                incumbent_value=inc_total_sample,
                candidate_value=cand_total_sample,
                delta=ratio,
                advantage=DimensionAdvantage.NEUTRAL,
                computable=True,
                dimension_status=DimensionStatus.COMPUTED,
                notes=f"Sample ratio: {ratio}; Tier: {tier_tag}",
            )
        )

        return dims

    # -------------------------------------------------------------------------
    # HD-11: Multi-Objective Pareto-Dominance Screening
    # -------------------------------------------------------------------------
    def _screen_pareto_frontier(
        self,
        incumbent: Any,
        evaluations: list[CandidateReplacementEvaluation],
        categories: dict[UUID, ReplacementCandidateCategory],
    ) -> list[CandidateReplacementEvaluation]:
        """Screen candidates using Pareto-dominance across role objective vectors.

        Guarantees non-dominated candidate subset without scalar score collapse.
        """
        if len(evaluations) <= 1:
            return evaluations

        inc_role = normalize_role(str(_extract_attr(incumbent, "primary_role", "Top-order Batter")))
        is_bowler = inc_role in (CanonicalRole.PACE_BOWLER, CanonicalRole.SPIN_BOWLER)
        is_allrounder = inc_role in (
            CanonicalRole.BATTING_ALL_ROUNDER,
            CanonicalRole.BOWLING_ALL_ROUNDER,
        )

        # Build objective vector F(c) where higher is strictly better
        candidate_vectors: dict[UUID, list[float]] = {}
        for ev in evaluations:
            d_map = {d.dimension_id: d for d in ev.dimension_comparisons}
            d01_val = d_map.get("D01")
            d03_val = d_map.get("D03")
            d08_val = d_map.get("D08")
            d09_val = d_map.get("D09")
            d15_val = d_map.get("D15")

            # Inverted age delta: younger candidate has negative delta, so -delta is positive/higher
            youth_upside = -(float(d15_val.delta) if d15_val and d15_val.delta is not None else 0.0)

            if is_bowler:
                f1 = float(d08_val.delta) if d08_val and d08_val.delta is not None else -999.0
                f2 = float(d09_val.delta) if d09_val and d09_val.delta is not None else -999.0
                f3 = youth_upside
            elif is_allrounder:
                f1 = float(d01_val.delta) if d01_val and d01_val.delta is not None else -999.0
                f2 = float(d08_val.delta) if d08_val and d08_val.delta is not None else -999.0
                f3 = youth_upside
            else:
                # Batter
                f1 = float(d01_val.delta) if d01_val and d01_val.delta is not None else -999.0
                f2 = float(d03_val.delta) if d03_val and d03_val.delta is not None else -999.0
                f3 = youth_upside

            candidate_vectors[ev.candidate_player_id] = [f1, f2, f3]

        # Identify non-dominated candidates
        non_dominated: list[CandidateReplacementEvaluation] = []
        for i, ev_a in enumerate(evaluations):
            vec_a = candidate_vectors[ev_a.candidate_player_id]
            dominated = False
            for j, ev_b in enumerate(evaluations):
                if i == j:
                    continue
                vec_b = candidate_vectors[ev_b.candidate_player_id]

                # B dominates A iff for all k, b_k >= a_k and for at least one k, b_k > a_k
                b_all_ge = all(b >= a for a, b in zip(vec_a, vec_b, strict=True))
                b_any_gt = any(b > a for a, b in zip(vec_a, vec_b, strict=True))

                if b_all_ge and b_any_gt:
                    dominated = True
                    break

            if not dominated:
                non_dominated.append(ev_a)

        # Deterministic sorting tiebreaker:
        # 1. Category rank
        # 2. Confidence descending
        # 3. Age ascending (youngest first)
        # 4. UUID ascending
        cat_order = {
            ReplacementCandidateCategory.DIRECT_UPGRADE: 0,
            ReplacementCandidateCategory.SYSTEMIC_FIT: 1,
            ReplacementCandidateCategory.LATERAL_ROTATION: 2,
            ReplacementCandidateCategory.LONG_TERM_PROJECT: 3,
            ReplacementCandidateCategory.ANALYTICAL_MONITOR: 4,
        }

        non_dominated.sort(
            key=lambda ev: (
                cat_order.get(
                    categories.get(
                        ev.candidate_player_id, ReplacementCandidateCategory.ANALYTICAL_MONITOR
                    ),
                    5,
                ),
                -ev.confidence,
                ev.age_at_evaluation,
                str(ev.candidate_player_id),
            )
        )

        return non_dominated

    # -------------------------------------------------------------------------
    # Recommendation State Synthesis
    # -------------------------------------------------------------------------
    def _classify_candidate_category(
        self,
        compat_score: float,
        dimensions: list[DimensionComparisonResult],
        age_delta: float,
        capped_by_scorecard: bool,
        similarity_scores: dict[str, float],
    ) -> ReplacementCandidateCategory:
        """Classify candidate into one of the 5 qualitative categories."""
        cand_adv_count = sum(
            1
            for d in dimensions
            if d.advantage == DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE
        )

        # HD-12: Scorecard Cap forces ANALYTICAL_MONITOR
        if capped_by_scorecard:
            return ReplacementCandidateCategory.ANALYTICAL_MONITOR

        # 1. Direct Upgrade: Strong multi-dimensional advantage & younger/equal age
        if compat_score >= 0.70 and cand_adv_count >= 6 and age_delta <= 0.0:
            return ReplacementCandidateCategory.DIRECT_UPGRADE

        # 2. Systemic Fit: High phase alignment / role match & solid advantage
        phase_sim = similarity_scores.get("tactical_phase_similarity", 0.0)
        has_phase_advantage = any(
            d.dimension_id in ("D07", "D11")
            and d.advantage == DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE
            for d in dimensions
        )
        if (
            compat_score >= 0.85
            and (phase_sim >= 0.85 or has_phase_advantage)
            and cand_adv_count >= 4
        ):
            return ReplacementCandidateCategory.SYSTEMIC_FIT

        # 3. Long Term Project: Significantly younger with high raw ceiling
        if age_delta <= -4.0 and cand_adv_count >= 2:
            return ReplacementCandidateCategory.LONG_TERM_PROJECT

        # 4. Lateral Rotation: Parity within uncertainty and solid role compatibility
        parity_count = sum(
            1 for d in dimensions if d.advantage == DimensionAdvantage.PARITY_WITHIN_UNCERTAINTY
        )
        if compat_score >= 0.70 and parity_count >= 4 and cand_adv_count >= 1:
            return ReplacementCandidateCategory.LATERAL_ROTATION

        return ReplacementCandidateCategory.ANALYTICAL_MONITOR

    def _synthesize_incumbent_action(
        self,
        incumbent_signal: str,
        evaluations: list[CandidateReplacementEvaluation],
        total_candidate_count: int,
    ) -> tuple[RecommendationState, bool]:
        """Synthesize overarching franchise recommendation action for the incumbent."""
        # Incumbent RETAIN_SIGNAL preserves ANALYTICAL_RETAIN
        if incumbent_signal == "RETAIN_SIGNAL":
            return RecommendationState.ANALYTICAL_RETAIN, False

        # Insufficient sample on incumbent
        if incumbent_signal == "INSUFFICIENT_EVIDENCE":
            return RecommendationState.INSUFFICIENT_EVIDENCE, False

        # No candidates evaluated or pool empty
        if not evaluations:
            if total_candidate_count > 0:
                return RecommendationState.NO_SUITABLE_VERIFIED_REPLACEMENT, False
            if incumbent_signal == "POTENTIALLY_REPLACEABLE":
                return RecommendationState.NO_SUITABLE_VERIFIED_REPLACEMENT, False
            return RecommendationState.ANALYTICAL_MONITOR, False

        # Check for top replacement candidate
        top_cand = evaluations[0]
        has_viable_replacement = any(
            ev.recommendation_label == RecommendationState.ANALYTICAL_REPLACEMENT_CANDIDATE
            for ev in evaluations
        )

        overseas_liberated = top_cand.overseas_slot_liberated if has_viable_replacement else False

        if has_viable_replacement:
            return RecommendationState.ANALYTICAL_REPLACEMENT_CANDIDATE, overseas_liberated

        # Candidates exist but only qualify for monitoring
        if incumbent_signal in ("POTENTIALLY_REPLACEABLE", "MONITOR_SIGNAL"):
            return RecommendationState.ANALYTICAL_MONITOR, False

        return RecommendationState.NO_SUITABLE_VERIFIED_REPLACEMENT, False

    # -------------------------------------------------------------------------
    # Helper & Service Ingestion Routines
    # -------------------------------------------------------------------------
    def _resolve_incumbent(self, player_id: UUID, dossier: Any | None) -> Any | None:
        """Resolve incumbent dossier from input or mock/service fallback."""
        if dossier is not None:
            if isinstance(dossier, dict):
                resolved = dict(dossier)
                metrics = dict(resolved.get("metrics") or {})
                for k, v in _DEFAULT_INCUMBENT_METRICS.items():
                    if k not in metrics and k not in resolved:
                        metrics[k] = v
                resolved["metrics"] = metrics
                return resolved
            return dossier
        # Default mock incumbent for offline testing if player_id is provided
        return {
            "player_id": player_id,
            "canonical_name": "Sanju Samson",
            "primary_role": "Wicketkeeper Batter",
            "batting_hand": "RIGHT",
            "bowling_style": "Right-arm offbreak",
            "is_wicketkeeper": True,
            "is_overseas": False,
            "replaceability_signal": "POTENTIALLY_REPLACEABLE",
            "review_status": "CLEAR",
            "metrics": dict(_DEFAULT_INCUMBENT_METRICS),
            "age": 30.5,
        }

    def _resolve_age(self, player: Any, eval_date: date) -> float:
        """Resolve player age at evaluation date from DOB or direct age attribute."""
        age_attr = _extract_attr(player, "age_at_evaluation") or _extract_attr(player, "age")
        if age_attr is not None:
            try:
                a = float(age_attr)
                if not math.isnan(a) and not math.isinf(a):
                    return a
            except (ValueError, TypeError):
                pass

        dob = _extract_attr(player, "date_of_birth") or _extract_attr(player, "dob")
        if isinstance(dob, str):
            try:
                dob = date.fromisoformat(dob)
            except ValueError:
                dob = None

        if isinstance(dob, date):
            days = (eval_date - dob).days
            return max(14.0, min(55.0, days / 365.25))

        return 25.0

    def _check_overseas_slot_liberation(self, incumbent: Any, candidate: Any) -> bool:
        """HD-13: Emits True strictly when overseas incumbent is replaced by verified Indian candidate."""

        def is_foreign(p: Any) -> bool:
            if bool(_extract_attr(p, "is_overseas", False)):
                return True
            nat = str(_extract_attr(p, "nationality", "")).strip().upper()
            country = str(_extract_attr(p, "country", "")).strip().upper()
            if nat and nat not in ("IND", "INDIA", "INDIAN"):
                return True
            return bool(country and country not in ("IND", "INDIA", "INDIAN"))

        inc_overseas = is_foreign(incumbent)
        cand_overseas = is_foreign(candidate)

        cand_eligibility = (
            str(_extract_attr(candidate, "ipl_uncapped_eligibility", "UNVERIFIED") or "UNVERIFIED")
            .strip()
            .upper()
        )

        return inc_overseas and (not cand_overseas) and (cand_eligibility == "VERIFIED_ELIGIBLE")

    def _compute_candidate_similarities(self, incumbent: Any, candidate: Any) -> dict[str, float]:
        """Compute aggregate similarity metrics between incumbent and candidate."""
        inc_p = {
            "strike_rate": _extract_attr(incumbent, "strike_rate"),
            "batting_average": _extract_attr(incumbent, "batting_average"),
            "boundary_pct": _extract_attr(incumbent, "boundary_pct"),
            "economy_rate": _extract_attr(incumbent, "economy_rate"),
            "bowling_strike_rate": _extract_attr(incumbent, "bowling_strike_rate"),
            "primary_role": str(_extract_attr(incumbent, "primary_role", "")),
            "batting_hand": str(_extract_attr(incumbent, "batting_hand", "")),
            "bowling_style": str(_extract_attr(incumbent, "bowling_style", "")),
        }
        cand_p = {
            "strike_rate": _extract_attr(candidate, "strike_rate"),
            "batting_average": _extract_attr(candidate, "batting_average"),
            "boundary_pct": _extract_attr(candidate, "boundary_pct"),
            "economy_rate": _extract_attr(candidate, "economy_rate"),
            "bowling_strike_rate": _extract_attr(candidate, "bowling_strike_rate"),
            "primary_role": str(_extract_attr(candidate, "primary_role", "")),
            "batting_hand": str(_extract_attr(candidate, "batting_hand", "")),
            "bowling_style": str(_extract_attr(candidate, "bowling_style", "")),
        }
        return self._similarity.compute_all_similarities(inc_p, cand_p)
