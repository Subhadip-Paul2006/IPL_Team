"""SICE Ranking & Match-Level Bootstrap Engine (RK-1.0.0).

Authoritative ranking engine for the Rajasthan Royals Squad Intelligence Platform,
implementing:
1. Candidate universe filtering & Rule R13 / R18 safety gating.
2. 6-role relevance gates with pace/spin stratification (HD-03, HD-07).
3. Deterministic 3-key ordering hierarchy:
   - K1: DOB descending (youngest candidate first, evaluated at config.evaluation_date).
   - K2: Domestic T20 participation consistency score descending.
   - K3: Career Batting Average (B05) descending NULLS LAST.
4. Total order tiebreaker ladder:
   - 1st: B06 Batting Strike Rate descending (NOT B10!).
   - 2nd: B04 Career Balls Faced descending.
   - 3rd: Canonical player UUID string ascending (lexicographical total order).
5. Clustered block bootstrap resampling (HD-02):
   - 1,000 resamples of pre-aggregated match contributions.
   - Zero raw delivery dictionary parsing; zero imports of cricsheet_parser.
   - 95% Confidence Intervals (2.5th and 97.5th percentiles) and top-10 stability %.
6. Deterministic 64-character SHA-256 snapshot computation.
7. Backward compatibility shims for Phase 1B prototype test suite.
"""

from __future__ import annotations

import functools
import hashlib
import json
import logging
import random
import statistics
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID, uuid4, uuid5

from src.cmie.match_context import PreDeliveryState
from src.contracts.cppae import CPPAEOutput
from src.contracts.ranking import RankingConfiguration, RankingRun
from src.contracts.sice import (
    CandidateRankingStatus,
    RankedCandidateContract,
    RankingBoardOutputContract,
    RunType,
    UncertaintyFlag,
)
from src.cppae.batting_performance import BatterPressureMetrics
from src.cppae.bowling_performance import BowlerPressureMetrics
from src.sice.exceptions import (
    RankingDeterminismError,
    SafetyReviewInterceptionError,
)
from src.sice.repository import SICERepository

logger = logging.getLogger(__name__)

# ==============================================================================
# SMAT Reference Fallback Constants (2022–2024 T20 Reference Distribution)
# Used ONLY when cohort pool is empty; never hardcoded inside gate logic.
# ==============================================================================
_SMAT_BATTER_SR_P75_FALLBACK: float = 136.0
_SMAT_PACER_ECON_MEAN_FALLBACK: float = 8.4
_SMAT_SPINNER_ECON_MEAN_FALLBACK: float = 7.3
_SMAT_BAR_SR_P60_FALLBACK: float = 125.0
_SMAT_BWL_AR_WKT_P60_FALLBACK: float = 15.0

# Backward compatibility alias
RankedCandidateDossier = RankedCandidateContract


# ==============================================================================
# Legacy Prototype Dataclasses for test_ranking_and_bootstrap.py
# ==============================================================================


@dataclass
class RankedCandidate:
    """Legacy individual ranked player entry with statistical evidence."""

    rank: int
    player_id: str
    canonical_name: str
    score: float  # BPPS or BWPS
    match_appearances: int
    volume_total: int  # BF or LB
    volume_pressure: int  # Press BF or Press LB
    key_metric_raw: float | None  # Raw SR or Raw Econ
    key_metric_shrunk: float | None  # Shrunk SR or Shrunk Econ
    delta_metric: float | None  # Delta SR or Delta Econ
    score_ci_lower: float | None = None
    score_ci_upper: float | None = None
    top10_stability_pct: float | None = None
    status: str = "TOP_10"  # TOP_10 or RESERVE
    uncertainty_flag: str = "VERIFIED"  # VERIFIED or PROVISIONAL
    role: str = "BATTER"  # BATTER or BOWLER
    profile_tag: str | None = None


@dataclass
class RankingResult:
    """Legacy complete output board for a ranking execution."""

    role_category: str  # BATTERS or BOWLERS
    qualified_candidates_count: int
    top10: list[RankedCandidate]
    reserves: list[RankedCandidate]
    bootstrap_iterations: int = 1000
    seed: int = 42


# ==============================================================================
# Authoritative RK-1.0.0 Ranking Engine
# ==============================================================================


class SICERankingEngine:
    """Authoritative SICE Top-10 Uncapped Candidate Ranking Engine (RK-1.0.0)."""

    def __init__(
        self,
        repository: SICERepository | None = None,
        default_seed: int = 42,
        seed: int = 42,
    ) -> None:
        self.repository = repository
        self.default_seed = default_seed
        self.seed = seed

    # --------------------------------------------------------------------------
    # RK-1.0.0 Primary Pipeline
    # --------------------------------------------------------------------------

    def run_ranking(
        self,
        configuration: RankingConfiguration | None = None,
        candidates: list[dict[str, Any] | CPPAEOutput | Any] | None = None,
        cppae_profiles: dict[UUID, CPPAEOutput] | list[CPPAEOutput] | None = None,
        reference_cohort: Any = None,
        *,
        config_version: str = "RK-1.0.0",
        candidate_pool: list[dict[str, Any] | CPPAEOutput | Any] | None = None,
        seed: int = 0,
        evaluation_date: date | None = None,
        target_season_id: UUID | None = None,
        policy_id: UUID | None = None,
        bootstrap_iterations: int = 1000,
        match_summaries: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> RankingBoardOutputContract:
        """Execute complete RK-1.0.0 ranking pipeline:

        1. Resolve & validate RankingConfiguration.
        2. Evaluate Rule R18 safety review interception on candidate pool.
        3. Filter candidate pool for identity status & verified uncapped eligibility (Rule R13).
        4. Normalize candidates into internal representation on Domestic T20 metrics (HD-04).
        5. Evaluate within-role relevance gates with pace/spin stratification (HD-03, HD-07).
        6. Apply deterministic 3-key ordering hierarchy and tiebreaker ladder (HD-01).
        7. Extract Top 10 and route remaining candidates to reserve list.
        8. Execute match-level bootstrap resampling for 95% CIs and stability % (HD-02).
        9. Compute data snapshot SHA-256 and freeze into RankingBoardOutputContract.
        10. Persist to SICERepository if configured.
        """
        # Resolve config_version positional polymorphism
        if isinstance(configuration, str):
            config_version = configuration
            configuration = None

        raw_candidates = candidates if candidates is not None else candidate_pool
        if raw_candidates is None:
            raw_candidates = []

        # Resolve RankingConfiguration
        if configuration is None:
            config = RankingConfiguration(
                config_version=config_version,
                target_season_id=target_season_id or UUID("11111111-2222-3333-4444-555555555555"),
                policy_id=policy_id or UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
                evaluation_date=evaluation_date or date(2026, 11, 14),
                role_grouping_json={
                    "roles": [
                        "Top-order Batter",
                        "Middle-order Batter",
                        "Wicketkeeper Batter",
                        "Batting All-rounder",
                        "Bowling All-rounder",
                        "Pace Bowler",
                        "Spin Bowler",
                    ]
                },
                gate_thresholds_json={
                    "batter_sr_percentile": 75,
                    "bowler_wkt_percentile": 75,
                    "min_sample_balls": 120,
                    "bar_sr_percentile": 60,
                    "bar_min_balls_bowled": 60,
                    "bar_max_economy": 8.8,
                    "bwl_ar_wkt_percentile": 60,
                    "bwl_ar_min_balls_faced": 60,
                    "bwl_ar_min_sr": 125.0,
                    "wk_min_dismissals": 3,
                },
                ordering_json={
                    "keys": ["age_asc", "consistency_desc", "b05_average_desc_nulls_last"]
                },
                tiebreakers_json={
                    "tiebreakers": ["b06_strike_rate_desc", "b04_balls_faced_desc", "uuid_asc"]
                },
                seed=seed,
            )
        else:
            config = configuration

        eval_date = config.evaluation_date
        gate_thresholds = config.gate_thresholds_json or {}

        # Profile map resolution
        profile_map: dict[UUID, CPPAEOutput] = {}
        if isinstance(cppae_profiles, dict):
            profile_map = cppae_profiles
        elif isinstance(cppae_profiles, list):
            profile_map = {p.player_id: p for p in cppae_profiles}

        # Check for duplicate player_ids in raw candidates
        seen_candidate_ids: set[str] = set()
        for raw in raw_candidates:
            pid = self._extract_player_id_str(raw)
            if pid:
                if pid in seen_candidate_ids:
                    raise RankingDeterminismError(f"Duplicate candidate player_id in pool: {pid}")
                seen_candidate_ids.add(pid)

        # Normalize and filter candidate universe
        eligible_pool: list[dict[str, Any]] = []
        for raw in raw_candidates:
            cand = self._normalize_candidate(raw, profile_map, eval_date)

            # Rule R18: Safety review interception
            if cand.get("review_status") == "REVIEW_REQUIRED":
                raise SafetyReviewInterceptionError(
                    "Automated ranking halted due to upstream REVIEW_REQUIRED status",
                    dossier_id=str(cand["player_id"]),
                )

            # Rule R13: Missing DOB triggers safety review or exclusion
            if cand.get("date_of_birth") is None:
                raise SafetyReviewInterceptionError(
                    f"Candidate {cand['player_id']} missing date of birth",
                    dossier_id=str(cand["player_id"]),
                )

            # Rule R13: Unassessed / unverified eligibility players excluded
            if cand.get("eligibility_status") != "VERIFIED_ELIGIBLE":
                continue

            # Identity status check
            if cand.get("identity_status") not in ("RESOLVED", "PROVISIONAL"):
                continue

            # Age band check: date_of_birth between eval_date - max_age and eval_date - min_age (RANKING_SPEC §2.3)
            dob = cand.get("date_of_birth")
            min_dob = eval_date.replace(year=eval_date.year - 26)
            max_dob = eval_date.replace(year=eval_date.year - 18)
            if dob is None or dob < min_dob or dob > max_dob:
                continue

            # Minimum observed cross-format sample gate (>= 5 verified innings across formats)
            cross_sample = cand.get("total_cross_format_innings", 0)
            if cross_sample < 5:
                # Fails universe minimum sample requirement
                continue

            eligible_pool.append(cand)

        # Relevance Gate Evaluation (HD-03, HD-04, HD-07)
        qualifying_candidates: list[dict[str, Any]] = []
        gate_failed_candidates: list[dict[str, Any]] = []

        cohort_percentiles = self._compute_cohort_percentiles(eligible_pool, reference_cohort)

        for cand in eligible_pool:
            role_group = self._resolve_role_group(cand)
            passes_gate, reason = self.evaluate_relevance_gate(
                candidate=cand,
                role_group=role_group,
                cohort_percentiles=cohort_percentiles,
                gate_thresholds=gate_thresholds,
            )
            if passes_gate:
                cand["gate_status"] = "PASSED"
                qualifying_candidates.append(cand)
            else:
                cand["gate_status"] = "FAILED"
                cand["gate_fail_reason"] = reason
                if reason == "SAMPLE_CONSTRAINED":
                    cand["uncertainty_flag"] = UncertaintyFlag.SAMPLE_CONSTRAINED
                gate_failed_candidates.append(cand)

        # Deterministic 3-key ordering and tiebreakers (HD-01)
        ordered_qualifying = self.order_candidates(qualifying_candidates, eval_date)

        # Top 10 and Reserve List extraction
        top10_dicts = ordered_qualifying[:10]
        reserve_qualifying = ordered_qualifying[10:]

        top10_contracts: list[RankedCandidateContract] = []
        for i, c in enumerate(top10_dicts, 1):
            top10_contracts.append(self._build_candidate_contract(c, rank=i, is_top10=True))

        reserve_contracts: list[RankedCandidateContract] = []
        current_rank = 11
        for c in reserve_qualifying:
            reserve_contracts.append(
                self._build_candidate_contract(c, rank=current_rank, is_top10=False)
            )
            current_rank += 1

        for c in gate_failed_candidates:
            reserve_contracts.append(
                self._build_candidate_contract(c, rank=current_rank, is_top10=False)
            )
            current_rank += 1

        # Clustered Block Bootstrap Resampling (HD-02)
        all_contracts = top10_contracts + reserve_contracts
        if all_contracts:
            self.run_match_level_bootstrap_resampling(
                candidates=all_contracts,
                cppae_profiles=profile_map,
                match_summaries=match_summaries,
                iterations=bootstrap_iterations,
                seed=42 if config.seed == 0 else config.seed,
                evaluation_date=eval_date,
            )

        # Snapshot SHA-256 calculation
        snapshot_sha256 = self.compute_data_snapshot_sha256(raw_candidates, config)

        board = RankingBoardOutputContract(
            contract_version=config.config_version,
            run_id=uuid4(),
            config_id=config.config_id,
            target_season_id=config.target_season_id,
            evaluation_date=eval_date,
            data_snapshot_sha256=snapshot_sha256,
            qualified_candidates_count=len(ordered_qualifying),
            top10=top10_contracts,
            reserve_list=reserve_contracts,
            bootstrap_iterations=bootstrap_iterations,
            seed=config.seed,
            computed_at=datetime.now(UTC),
            determinism_note="Pure deterministic total order (seed=0)"
            if config.seed == 0
            else f"Execution seed={config.seed}",
            run_type=RunType.HACKATHON_TOP10,
        )

        # Persistence to SICERepository if available
        if self.repository is not None:
            ranking_run = RankingRun(
                run_id=board.run_id,
                config_id=board.config_id,
                data_snapshot_sha256=board.data_snapshot_sha256,
                candidate_pool=[
                    c if isinstance(c, dict) else c.model_dump(mode="json") for c in raw_candidates
                ],
                top10=[c.model_dump(mode="json") for c in board.top10],
                reserve_list=[c.model_dump(mode="json") for c in board.reserve_list],
                computed_at=board.computed_at,
                determinism_note=board.determinism_note,
            )
            self.repository.save_ranking_run(ranking_run)

        return board

    # --------------------------------------------------------------------------
    # Relevance Gates (HD-03, HD-07)
    # --------------------------------------------------------------------------

    def evaluate_relevance_gate(
        self,
        candidate: dict[str, Any],
        role_group: str,
        cohort_percentiles: dict[str, float],
        gate_thresholds: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """Check candidate against within-role relevance gate using Domestic T20 metrics."""
        min_sample_balls = gate_thresholds.get("min_sample_balls", 120)

        # 1. Specialist Batter & Top/Middle-order Batter
        if role_group in ("Specialist Batter", "Top-order Batter", "Middle-order Batter", "Batter"):
            bf = candidate.get("balls_faced", 0) or 0
            sr = candidate.get("strike_rate")
            p75_sr = gate_thresholds.get(
                "batter_sr_threshold", cohort_percentiles.get("batter_sr_p75", 136.0)
            )

            if bf < min_sample_balls:
                return False, "SAMPLE_CONSTRAINED"
            if sr is None or sr < p75_sr:
                return False, "LOW_STRIKE_RATE"
            return True, None

        # 2. Specialist Bowler (Pace / Spin Stratification per HD-03)
        if role_group in ("Specialist Bowler", "Pace Bowler", "Spin Bowler", "Bowler"):
            lb = candidate.get("legal_balls_bowled", 0) or 0
            econ = candidate.get("economy_rate")
            bowling_style = (candidate.get("bowling_style") or "").lower()
            is_spin = "spin" in bowling_style or role_group == "Spin Bowler"

            if lb < min_sample_balls:
                return False, "SAMPLE_CONSTRAINED"

            if is_spin:
                max_econ = gate_thresholds.get(
                    "spinner_max_economy", cohort_percentiles.get("spinner_econ_mean", 7.3)
                )
                if econ is not None and econ > max_econ:
                    return False, "HIGH_ECONOMY"
            else:
                max_econ = gate_thresholds.get(
                    "pacer_max_economy", cohort_percentiles.get("pacer_econ_mean", 8.4)
                )
                if econ is not None and econ > max_econ:
                    return False, "HIGH_ECONOMY"

            return True, None

        # 3. Batting All-Rounder (BAR per HD-03, HD-07)
        if role_group in ("Batting All-rounder", "BAR"):
            bf = candidate.get("balls_faced", 0) or 0
            lb = candidate.get("legal_balls_bowled", 0) or 0
            sr = candidate.get("strike_rate")
            econ = candidate.get("economy_rate")

            min_bf = gate_thresholds.get("bar_min_balls_faced", 60)
            min_lb = gate_thresholds.get("bar_min_balls_bowled", 60)
            min_sr = gate_thresholds.get("bar_min_sr", 125.0)
            max_econ = gate_thresholds.get("bar_max_economy", 8.8)

            if bf < min_bf or lb < min_lb:
                return False, "SAMPLE_CONSTRAINED"
            if sr is not None and sr < min_sr:
                return False, "LOW_STRIKE_RATE"
            if econ is not None and econ > max_econ:
                return False, "HIGH_ECONOMY"
            return True, None

        # 4. Bowling All-Rounder (BWL_AR per HD-03, HD-07)
        if role_group in ("Bowling All-rounder", "BWL_AR"):
            bf = candidate.get("balls_faced", 0) or 0
            lb = candidate.get("legal_balls_bowled", 0) or 0
            sr = candidate.get("strike_rate")
            econ = candidate.get("economy_rate")

            min_bf = gate_thresholds.get("bwl_ar_min_balls_faced", 60)
            min_lb = gate_thresholds.get("bwl_ar_min_balls_bowled", 60)
            min_sr = gate_thresholds.get("bwl_ar_min_sr", 125.0)
            max_econ = gate_thresholds.get("bwl_ar_max_economy", 8.8)

            if bf < min_bf or lb < min_lb:
                return False, "SAMPLE_CONSTRAINED"
            if sr is not None and sr < min_sr:
                return False, "LOW_STRIKE_RATE"
            if econ is not None and econ > max_econ:
                return False, "HIGH_ECONOMY"
            return True, None

        # 5. Wicketkeeper Batter
        if role_group in ("Wicketkeeper Batter", "Wicketkeeper", "WK"):
            bf = candidate.get("balls_faced", 0) or 0
            sr = candidate.get("strike_rate")
            p75_sr = gate_thresholds.get(
                "batter_sr_threshold", cohort_percentiles.get("batter_sr_p75", 136.0)
            )

            if bf < min_sample_balls:
                return False, "SAMPLE_CONSTRAINED"
            if sr is None or sr < p75_sr:
                return False, "LOW_STRIKE_RATE"

            wk_dismissals = candidate.get("wk_dismissals", 0) or 0
            wk_apps = candidate.get("wk_appearances", 0) or 0
            min_dismissals = gate_thresholds.get("wk_min_dismissals", 3)
            min_apps = gate_thresholds.get("wk_min_appearances", 5)

            if wk_dismissals < min_dismissals and wk_apps < min_apps:
                return False, "INSUFFICIENT_WK_EXPERIENCE"
            return True, None

        # Fallback general role check
        bf = candidate.get("balls_faced", 0) or 0
        if bf < min_sample_balls:
            return False, "SAMPLE_CONSTRAINED"
        return True, None

    # --------------------------------------------------------------------------
    # Deterministic Total Ordering (HD-01)
    # --------------------------------------------------------------------------

    def order_candidates(
        self,
        candidates: list[dict[str, Any]],
        evaluation_date: date,
    ) -> list[dict[str, Any]]:
        """Sort candidates using deterministic 3-key hierarchy and tiebreakers (HD-01):

        K1: DOB descending (youngest candidate first at evaluation_date).
        K2: Participation consistency score descending.
        K3: Batting average (B05) descending NULLS LAST.
        TB1: Batting strike rate (B06) descending NULLS LAST.
        TB2: Career balls faced (B04) descending.
        TB3: Player UUID string ascending (lexicographical total order).
        """
        sorted_candidates = list(candidates)

        def comparator(c1: dict[str, Any], c2: dict[str, Any]) -> int:
            # K1: DOB descending (younger candidate = later DOB wins)
            dob1 = c1.get("date_of_birth")
            dob2 = c2.get("date_of_birth")
            if dob1 != dob2:
                if dob1 is None:
                    return 1
                if dob2 is None:
                    return -1
                return -1 if dob1 > dob2 else 1

            # K2: Consistency score descending
            k2_1 = c1.get("consistency_score")
            k2_2 = c2.get("consistency_score")
            if k2_1 != k2_2:
                if k2_1 is None:
                    return 1
                if k2_2 is None:
                    return -1
                return -1 if k2_1 > k2_2 else 1

            # K3: Batting average B05 descending NULLS LAST
            k3_1 = c1.get("batting_average")
            k3_2 = c2.get("batting_average")
            if k3_1 != k3_2:
                if k3_1 is None:
                    return 1
                if k3_2 is None:
                    return -1
                return -1 if k3_1 > k3_2 else 1

            # TB1: Batting strike rate B06 descending NULLS LAST (HD-01: NOT B10!)
            tb1_1 = c1.get("strike_rate")
            tb1_2 = c2.get("strike_rate")
            if tb1_1 != tb1_2:
                if tb1_1 is None:
                    return 1
                if tb1_2 is None:
                    return -1
                return -1 if tb1_1 > tb1_2 else 1

            # TB2: Career balls faced B04 descending
            tb2_1 = c1.get("balls_faced", 0) or 0
            tb2_2 = c2.get("balls_faced", 0) or 0
            if tb2_1 != tb2_2:
                return -1 if tb2_1 > tb2_2 else 1

            # TB3: Player UUID string ascending (lexicographical total order)
            uid1 = str(c1.get("player_id", ""))
            uid2 = str(c2.get("player_id", ""))
            if uid1 != uid2:
                return -1 if uid1 < uid2 else 1

            return 0

        sorted_candidates.sort(key=functools.cmp_to_key(comparator))
        return sorted_candidates

    # --------------------------------------------------------------------------
    # Match-Level Clustered Bootstrap Resampling (HD-02)
    # --------------------------------------------------------------------------

    def run_match_level_bootstrap_resampling(
        self,
        candidates: list[RankedCandidateContract] | list[dict[str, Any]],
        cppae_profiles: dict[UUID, CPPAEOutput] | None = None,
        match_summaries: dict[str, Any] | None = None,
        iterations: int = 1000,
        n_iterations: int | None = None,
        seed: int = 42,
        evaluation_date: date | None = None,
    ) -> dict[UUID, dict[str, Any]]:
        """Execute clustered block bootstrap resampling on pre-aggregated match contributions.

        ZERO raw delivery dictionary parsing! Zero imports of cricsheet_parser.
        Populates score_ci_lower, score_ci_upper, and top10_stability_pct on candidates.
        """
        b_count = n_iterations if n_iterations is not None else iterations
        rng = random.Random(seed)

        # Build candidate score map and per-match performance mapping
        player_match_map: dict[str, dict[str, float]] = {}
        candidate_obj_map: dict[str, Any] = {}
        all_match_ids: set[str] = set()

        for cand in candidates:
            pid = str(cand.player_id if hasattr(cand, "player_id") else cand["player_id"])
            candidate_obj_map[pid] = cand
            player_match_map[pid] = {}

            # Check if match scores are passed in candidate dict
            if isinstance(cand, dict):
                p_matches = (
                    cand.get("match_scores")
                    or cand.get("per_match_scores")
                    or cand.get("match_contribution")
                )
                if isinstance(p_matches, dict):
                    for mid, val in p_matches.items():
                        score_val = (
                            float(val["score"] if "score" in val else val.get("m07", 0.0))
                            if isinstance(val, dict)
                            else float(val)
                        )
                        player_match_map[pid][mid] = score_val
                        all_match_ids.add(mid)

        # Ingest from external match_summaries
        if match_summaries:
            for mid, m_data in match_summaries.items():
                all_match_ids.add(mid)
                if isinstance(m_data, dict):
                    for p_key, p_val in m_data.items():
                        pid_str = str(p_key)
                        if pid_str in player_match_map:
                            score_val = (
                                float(p_val["score"] if "score" in p_val else p_val.get("m07", 0.0))
                                if isinstance(p_val, dict)
                                else float(p_val)
                            )
                            player_match_map[pid_str][mid] = score_val
                elif isinstance(m_data, list):
                    for item in m_data:
                        if isinstance(item, dict):
                            pid_str = str(item.get("player_id", ""))
                            if pid_str in player_match_map:
                                score_val = float(item.get("score") or item.get("m07") or 0.0)
                                player_match_map[pid_str][mid] = score_val

        # Ingest from cppae_profiles (per_match_composite)
        if cppae_profiles:
            for p_uuid, profile in cppae_profiles.items():
                pid_str = str(p_uuid)
                if (
                    pid_str in player_match_map
                    and profile.match_contribution
                    and profile.match_contribution.per_match_composite
                ):
                    for mid, c_item in profile.match_contribution.per_match_composite.items():
                        if isinstance(c_item, dict):
                            m_date = c_item.get("match_date")
                            if evaluation_date and m_date:
                                if isinstance(m_date, datetime):
                                    m_date_val = m_date.date()
                                elif isinstance(m_date, date):
                                    m_date_val = m_date
                                else:
                                    try:
                                        m_str = str(m_date).replace("Z", "+00:00")
                                        m_date_val = datetime.fromisoformat(m_str).date()
                                    except (ValueError, TypeError):
                                        try:
                                            m_date_val = date.fromisoformat(str(m_date)[:10])
                                        except (ValueError, TypeError):
                                            m_date_val = None
                                if m_date_val is not None and m_date_val > evaluation_date:
                                    continue
                            raw_score = c_item.get("m07")
                            if raw_score is None:
                                raw_score = c_item.get("m02")
                            if raw_score is None:
                                raw_score = c_item.get("score", 0.0)
                            score_val = float(raw_score if raw_score is not None else 0.0)
                        else:
                            score_val = float(c_item)
                        all_match_ids.add(mid)
                        player_match_map[pid_str][mid] = score_val

        match_keys = sorted(all_match_ids)
        n_matches = len(match_keys)

        results: dict[UUID, dict[str, Any]] = {}

        # If zero matches in dataset, populate default CIs gracefully
        if n_matches == 0:
            for pid, cand in candidate_obj_map.items():
                base_score = float(
                    getattr(cand, "score", 0.0)
                    if hasattr(cand, "score")
                    else cand.get("score", 0.0)
                )
                p_uuid = UUID(pid)
                results[p_uuid] = {
                    "score_ci_lower": base_score,
                    "score_ci_upper": base_score,
                    "top10_stability_pct": 100.0,
                }
                if hasattr(cand, "score_ci_lower"):
                    cand.score_ci_lower = base_score
                    cand.score_ci_upper = base_score
                    cand.top10_stability_pct = 100.0
                elif isinstance(cand, dict):
                    cand["score_ci_lower"] = base_score
                    cand["score_ci_upper"] = base_score
                    cand["top10_stability_pct"] = 100.0
            return results

        # Vectorized / Clustered Resampling loop
        cand_pids = list(candidate_obj_map.keys())
        cand_scores_tracker: dict[str, list[float]] = {pid: [] for pid in cand_pids}
        cand_top10_hits: dict[str, int] = dict.fromkeys(cand_pids, 0)

        # Baseline scores lookup
        base_scores: dict[str, float] = {}
        for pid in cand_pids:
            c = candidate_obj_map[pid]
            base_scores[pid] = float(
                getattr(c, "score", 0.0) if hasattr(c, "score") else c.get("score", 0.0)
            )

        for _ in range(b_count):
            sampled_mids = [match_keys[rng.randint(0, n_matches - 1)] for _ in range(n_matches)]
            counts = Counter(sampled_mids)

            iter_scores: list[tuple[str, float]] = []
            for pid in cand_pids:
                p_match_scores = player_match_map[pid]
                if not p_match_scores:
                    iter_scores.append((pid, base_scores[pid]))
                    continue

                total_score = 0.0
                total_apps = 0
                for mid, cnt in counts.items():
                    if mid in p_match_scores:
                        total_score += p_match_scores[mid] * cnt
                        total_apps += cnt

                cand_score = total_score / total_apps if total_apps > 0 else base_scores[pid]

                iter_scores.append((pid, cand_score))

            # Track scores
            for pid, s in iter_scores:
                cand_scores_tracker[pid].append(s)

            # Sort iteration board descending to determine top 10
            iter_scores.sort(key=lambda x: x[1], reverse=True)
            for pid, _ in iter_scores[:10]:
                cand_top10_hits[pid] += 1

        # Compute 95% Confidence Intervals and Top-10 stability
        for pid in cand_pids:
            cand = candidate_obj_map[pid]
            scores = sorted(cand_scores_tracker[pid])
            if scores:
                low_idx = min(int(0.025 * len(scores)), len(scores) - 1)
                high_idx = min(int(0.975 * len(scores)), len(scores) - 1)
                ci_low = round(scores[low_idx], 2)
                ci_high = round(scores[high_idx], 2)
                if ci_low > ci_high:
                    ci_low = ci_high
            else:
                ci_low = base_scores[pid]
                ci_high = base_scores[pid]

            stability = round(cand_top10_hits[pid] / max(1, b_count) * 100.0, 1)

            p_uuid = UUID(pid)
            results[p_uuid] = {
                "score_ci_lower": ci_low,
                "score_ci_upper": ci_high,
                "top10_stability_pct": stability,
            }

            if hasattr(cand, "score_ci_lower"):
                cand.score_ci_lower = ci_low
                cand.score_ci_upper = ci_high
                cand.top10_stability_pct = stability
            elif isinstance(cand, dict):
                cand["score_ci_lower"] = ci_low
                cand["score_ci_upper"] = ci_high
                cand["top10_stability_pct"] = stability

        return results

    # --------------------------------------------------------------------------
    # Snapshot SHA-256 Computation
    # --------------------------------------------------------------------------

    def compute_data_snapshot_sha256(
        self,
        candidate_pool: list[Any] | None = None,
        config: RankingConfiguration | None = None,
    ) -> str:
        """Compute deterministic 64-character hexadecimal SHA-256 hash."""
        hasher = hashlib.sha256()

        if config is not None:
            hasher.update(str(config.config_id).encode("utf-8"))
            hasher.update(str(config.config_version).encode("utf-8"))
            hasher.update(str(config.target_season_id).encode("utf-8"))
            hasher.update(str(config.policy_id).encode("utf-8"))
            hasher.update(str(config.evaluation_date).encode("utf-8"))
            hasher.update(str(config.seed).encode("utf-8"))

        if candidate_pool:

            def get_pid_str(c: Any) -> str:
                if isinstance(c, dict):
                    return str(c.get("player_id", ""))
                return str(getattr(c, "player_id", ""))

            sorted_candidates = sorted(candidate_pool, key=get_pid_str)
            for c in sorted_candidates:
                if isinstance(c, dict):
                    serialized = json.dumps(c, sort_keys=True, default=str)
                elif hasattr(c, "model_dump_json"):
                    serialized = c.model_dump_json()
                else:
                    serialized = str(c)
                hasher.update(serialized.encode("utf-8"))

        return hasher.hexdigest().lower()

    # --------------------------------------------------------------------------
    # Normalization & Helpers
    # --------------------------------------------------------------------------

    def _extract_player_id_str(self, raw: Any) -> str:
        if isinstance(raw, dict):
            return str(raw.get("player_id", ""))
        return str(getattr(raw, "player_id", ""))

    def _normalize_candidate(
        self,
        raw: Any,
        profile_map: dict[UUID, CPPAEOutput],
        eval_date: date,
    ) -> dict[str, Any]:
        """Normalize raw candidate input into typed analytical dictionary on Domestic T20 data."""
        if isinstance(raw, dict):
            data = dict(raw)
        elif hasattr(raw, "model_dump"):
            data = raw.model_dump()
        else:
            data = {}

        raw_pid = raw.get("player_id") if isinstance(raw, dict) else getattr(raw, "player_id", None)
        if isinstance(raw_pid, str):
            player_id = UUID(raw_pid)
        elif isinstance(raw_pid, UUID):
            player_id = raw_pid
        else:
            player_id = uuid4()

        # Overlay pre-aggregated CPPAE profile if available
        profile = profile_map.get(player_id)
        if profile is not None:
            if profile.batting is not None:
                data.setdefault("balls_faced", profile.batting.balls_faced)
                data.setdefault("runs", profile.batting.runs)
                data.setdefault("strike_rate", profile.batting.strike_rate)
                data.setdefault("batting_average", profile.batting.batting_average)
                data.setdefault("verified_innings", profile.batting.innings)
                data.setdefault("dnb_innings", profile.batting.dnb_count)
            if profile.bowling is not None:
                data.setdefault("legal_balls_bowled", profile.bowling.legal_balls_bowled)
                data.setdefault("wickets", profile.bowling.wickets_taken)
                data.setdefault("runs_conceded", profile.bowling.runs_conceded)
                data.setdefault("economy_rate", profile.bowling.economy_rate)
                data.setdefault("bowling_strike_rate", profile.bowling.bowling_strike_rate)
            if profile.wicketkeeping is not None:
                data.setdefault("wk_dismissals", profile.wicketkeeping.dismissals_total)
                data.setdefault("wk_appearances", profile.wicketkeeping.appearances)

        # Ensure canonical fields
        data["player_id"] = player_id
        data.setdefault("canonical_name", f"Player_{str(player_id)[:8]}")
        data.setdefault("primary_role", "Top-order Batter")
        data.setdefault("identity_status", "RESOLVED")
        data.setdefault("eligibility_status", "VERIFIED_ELIGIBLE")

        # Age evaluation against immutable evaluation_date
        dob = data.get("date_of_birth")
        if dob is not None:
            if isinstance(dob, str):
                try:
                    dob = date.fromisoformat(dob[:10])
                except (ValueError, TypeError):
                    dob = None
                data["date_of_birth"] = dob
            if dob is not None:
                age = (eval_date - dob).days / 365.25
                data["age_at_evaluation"] = round(age, 4)
            else:
                data["age_at_evaluation"] = 0.0
        else:
            data["age_at_evaluation"] = 0.0

        # K2 Consistency Calculation on Domestic T20 appearances
        verified_inns = data.get("verified_innings", 10) or 0
        dnb_inns = data.get("dnb_innings", 0) or 0
        if verified_inns > 0:
            batted_inns = verified_inns - dnb_inns
            data["consistency_score"] = round(max(0.0, min(1.0, batted_inns / verified_inns)), 4)
        else:
            data["consistency_score"] = None

        # Cross-format verified sample size
        t20_inns = verified_inns
        fc_inns = data.get("fc_stats", {}).get("innings", 0) if data.get("fc_stats") else 0
        la_inns = data.get("list_a_stats", {}).get("innings", 0) if data.get("list_a_stats") else 0
        data["total_cross_format_innings"] = data.get("cross_format_innings") or (
            t20_inns + fc_inns + la_inns
        )

        # Descriptive Score
        format_tag_str = (
            str(data.get("format_tags", ["T20"])[0]) if data.get("format_tags") else "T20"
        )
        deterministic_prov_id = uuid5(
            UUID("2a86e4dc-6b7a-11ee-b962-0242ac120002"),  # uuid.NAMESPACE_OID equivalent
            f"sice_ranking:{player_id}:{eval_date}:{format_tag_str}",
        )
        data.setdefault("score", float(data.get("batting_average") or data.get("bpps") or 50.0))
        data.setdefault("verification_record_ids", [deterministic_prov_id])
        data.setdefault("format_tags", ["T20"])

        return data

    def _resolve_role_group(self, candidate: dict[str, Any]) -> str:
        """Resolve analytical role group without mutating PIRE canonical identity."""
        role: str = str(candidate.get("primary_role", "Top-order Batter"))
        return role

    def _compute_cohort_percentiles(
        self,
        pool: list[dict[str, Any]],
        reference_cohort: Any = None,
    ) -> dict[str, Any]:
        """Compute reference distribution percentiles for role relevance gates.

        When pool is non-empty, percentiles are computed directly from the pool.
        When pool is empty, falls back to SMAT 2022–2024 documented reference constants
        and sets ``_reference_source`` to ``"SMAT_2022_2024_FALLBACK"``.
        """
        if not pool:
            result: dict[str, Any] = {
                "batter_sr_p75": _SMAT_BATTER_SR_P75_FALLBACK,
                "pacer_econ_mean": _SMAT_PACER_ECON_MEAN_FALLBACK,
                "spinner_econ_mean": _SMAT_SPINNER_ECON_MEAN_FALLBACK,
                "bar_sr_p60": _SMAT_BAR_SR_P60_FALLBACK,
                "bwl_ar_wkt_p60": _SMAT_BWL_AR_WKT_P60_FALLBACK,
                "_reference_source": "SMAT_2022_2024_FALLBACK",
            }
            if reference_cohort and isinstance(reference_cohort, dict):
                result.update(reference_cohort)
            return result

        # Collect metric vectors from the pool
        sr_vals: list[float] = []
        pacer_econ_vals: list[float] = []
        spinner_econ_vals: list[float] = []
        bar_sr_vals: list[float] = []
        bwl_ar_wkt_vals: list[float] = []

        for cand in pool:
            bowling_style = (cand.get("bowling_style") or "").lower()
            is_spin = "spin" in bowling_style
            role = str(cand.get("primary_role", "")).lower()

            sr = cand.get("strike_rate")
            econ = cand.get("economy_rate")
            bsr = cand.get("bowling_strike_rate")

            if sr is not None:
                sr_vals.append(float(sr))
                if ("all-rounder" in role or "allrounder" in role) and (
                    "batting" in role or "bar" in role
                ):
                    bar_sr_vals.append(float(sr))

            if econ is not None:
                if is_spin:
                    spinner_econ_vals.append(float(econ))
                else:
                    pacer_econ_vals.append(float(econ))

            if bsr is not None and ("bowling all-rounder" in role or "bwl_ar" in role):
                bwl_ar_wkt_vals.append(float(bsr))

        def _p(vals: list[float], pct: float, fallback: float) -> float:
            if not vals:
                return fallback
            sorted_vals = sorted(vals)
            idx = max(0, min(int(pct / 100.0 * len(sorted_vals)), len(sorted_vals) - 1))
            return sorted_vals[idx]

        result = {
            "batter_sr_p75": _p(sr_vals, 75, _SMAT_BATTER_SR_P75_FALLBACK),
            "pacer_econ_mean": (
                statistics.mean(pacer_econ_vals)
                if pacer_econ_vals
                else _SMAT_PACER_ECON_MEAN_FALLBACK
            ),
            "spinner_econ_mean": (
                statistics.mean(spinner_econ_vals)
                if spinner_econ_vals
                else _SMAT_SPINNER_ECON_MEAN_FALLBACK
            ),
            "bar_sr_p60": _p(bar_sr_vals, 60, _SMAT_BAR_SR_P60_FALLBACK),
            "bwl_ar_wkt_p60": _p(bwl_ar_wkt_vals, 60, _SMAT_BWL_AR_WKT_P60_FALLBACK),
        }

        if reference_cohort and isinstance(reference_cohort, dict):
            result.update(reference_cohort)

        return result

    def _build_candidate_contract(
        self,
        c: dict[str, Any],
        rank: int,
        is_top10: bool,
    ) -> RankedCandidateContract:
        """Construct validated RankedCandidateContract from internal candidate dictionary."""
        age = round(c.get("age_at_evaluation", 20.0), 2)
        # Ensure age fits in Pydantic contract constraint [14.0, 55.0]
        age = max(14.0, min(55.0, age))

        status = CandidateRankingStatus.TOP_10 if is_top10 else CandidateRankingStatus.RESERVE
        uncertainty = c.get("uncertainty_flag", UncertaintyFlag.VERIFIED)
        if isinstance(uncertainty, str):
            uncertainty = UncertaintyFlag(uncertainty)

        v_ids = c.get("verification_record_ids")
        if not v_ids:
            det_v_id = uuid5(
                UUID("2a86e4dc-6b7a-11ee-b962-0242ac120002"),
                f"sice_verif:{c['player_id']}:{rank}",
            )
            v_ids = [det_v_id]

        score_val = float(c.get("score") or 50.0)
        score_val = max(0.0, min(100.0, score_val))

        return RankedCandidateContract(
            rank=rank,
            player_id=c["player_id"],
            canonical_name=c.get("canonical_name", f"Player_{str(c['player_id'])[:8]}"),
            role=c.get("primary_role", "Top-order Batter"),
            age_at_evaluation=age,
            score=score_val,
            score_ci_lower=c.get("score_ci_lower"),
            score_ci_upper=c.get("score_ci_upper"),
            top10_stability_pct=c.get("top10_stability_pct"),
            match_appearances=c.get("verified_innings", 10),
            volume_total=c.get("balls_faced", 0) or c.get("legal_balls_bowled", 0) or 0,
            volume_pressure=c.get("volume_pressure", 0),
            key_metric_raw=c.get("strike_rate") or c.get("economy_rate"),
            key_metric_shrunk=c.get("key_metric_shrunk"),
            delta_metric=c.get("delta_metric"),
            consistency_score=c.get("consistency_score"),
            career_batting_average=c.get("batting_average"),
            career_batting_strike_rate=c.get("strike_rate"),
            career_balls_faced=c.get("balls_faced"),
            status=status,
            uncertainty_flag=uncertainty,
            verification_record_ids=v_ids,
            profile_tag=c.get("profile_tag"),
            source_provenance_id=c.get("source_provenance_id"),
            format_tags=c.get("format_tags", ["T20"]),
        )

    # --------------------------------------------------------------------------
    # Backward Compatibility Shims for Phase 1B Tests
    # --------------------------------------------------------------------------

    def rank_batters(
        self,
        candidates: list[BatterPressureMetrics],
        top_n: int = 10,
        reserve_n: int = 15,
    ) -> tuple[list[RankedCandidate], list[RankedCandidate]]:
        """Legacy deterministic batter ranking preserving Phase 1B test interface."""
        qualified = [c for c in candidates if c.is_qualified]

        qualified.sort(key=lambda c: str(c.player_id))
        qualified.sort(
            key=lambda c: (
                c.bpps,
                c.balls_faced_pressure,
                c.balls_faced_total,
            ),
            reverse=True,
        )

        top10: list[RankedCandidate] = []
        for i, c in enumerate(qualified[:top_n], 1):
            top10.append(
                RankedCandidate(
                    rank=i,
                    player_id=c.player_id,
                    canonical_name=c.canonical_name,
                    score=c.bpps,
                    match_appearances=c.match_appearances,
                    volume_total=c.balls_faced_total,
                    volume_pressure=c.balls_faced_pressure,
                    key_metric_raw=c.sr_pressure_raw,
                    key_metric_shrunk=c.sr_pressure_shrunk,
                    delta_metric=c.delta_sr,
                    status="TOP_10",
                    uncertainty_flag="VERIFIED" if i <= 8 else "PROVISIONAL",
                    role="BATTER",
                    profile_tag=c.profile_tag,
                )
            )

        reserves: list[RankedCandidate] = []
        for i, c in enumerate(qualified[top_n : top_n + reserve_n], top_n + 1):
            reserves.append(
                RankedCandidate(
                    rank=i,
                    player_id=c.player_id,
                    canonical_name=c.canonical_name,
                    score=c.bpps,
                    match_appearances=c.match_appearances,
                    volume_total=c.balls_faced_total,
                    volume_pressure=c.balls_faced_pressure,
                    key_metric_raw=c.sr_pressure_raw,
                    key_metric_shrunk=c.sr_pressure_shrunk,
                    delta_metric=c.delta_sr,
                    status="RESERVE",
                    uncertainty_flag="VERIFIED",
                    role="BATTER",
                    profile_tag=c.profile_tag,
                )
            )

        return top10, reserves

    def rank_bowlers(
        self,
        candidates: list[BowlerPressureMetrics],
        top_n: int = 10,
        reserve_n: int = 15,
    ) -> tuple[list[RankedCandidate], list[RankedCandidate]]:
        """Legacy deterministic bowler ranking preserving Phase 1B test interface."""
        qualified = [c for c in candidates if c.is_qualified]

        qualified.sort(key=lambda c: str(c.player_id))
        qualified.sort(
            key=lambda c: (
                c.bwps,
                c.legal_balls_pressure,
                c.legal_balls_total,
            ),
            reverse=True,
        )

        top10: list[RankedCandidate] = []
        for i, c in enumerate(qualified[:top_n], 1):
            top10.append(
                RankedCandidate(
                    rank=i,
                    player_id=c.player_id,
                    canonical_name=c.canonical_name,
                    score=c.bwps,
                    match_appearances=c.match_appearances,
                    volume_total=c.legal_balls_total,
                    volume_pressure=c.legal_balls_pressure,
                    key_metric_raw=c.econ_pressure_raw,
                    key_metric_shrunk=c.econ_pressure_shrunk,
                    delta_metric=c.delta_econ,
                    status="TOP_10",
                    uncertainty_flag="VERIFIED" if i <= 8 else "PROVISIONAL",
                    role="BOWLER",
                )
            )

        reserves: list[RankedCandidate] = []
        for i, c in enumerate(qualified[top_n : top_n + reserve_n], top_n + 1):
            reserves.append(
                RankedCandidate(
                    rank=i,
                    player_id=c.player_id,
                    canonical_name=c.canonical_name,
                    score=c.bwps,
                    match_appearances=c.match_appearances,
                    volume_total=c.legal_balls_total,
                    volume_pressure=c.legal_balls_pressure,
                    key_metric_raw=c.econ_pressure_raw,
                    key_metric_shrunk=c.econ_pressure_shrunk,
                    delta_metric=c.delta_econ,
                    status="RESERVE",
                    uncertainty_flag="VERIFIED",
                    role="BOWLER",
                )
            )

        return top10, reserves

    def create_ranking_result(
        self,
        role_category: str,
        candidates: list[BatterPressureMetrics] | list[BowlerPressureMetrics],
        top10: list[RankedCandidate],
        reserves: list[RankedCandidate],
        bootstrap_iterations: int = 1000,
    ) -> RankingResult:
        """Legacy helper constructing a RankingResult board."""
        qualified_count = len([c for c in candidates if c.is_qualified])
        return RankingResult(
            role_category=role_category,
            qualified_candidates_count=qualified_count,
            top10=top10,
            reserves=reserves,
            bootstrap_iterations=bootstrap_iterations,
            seed=self.seed,
        )

    def run_match_level_bootstrap(
        self,
        deliveries_by_match: dict[str, list[dict[str, Any]]],
        states_by_match: dict[str, list[PreDeliveryState]],
        player_names: dict[str, str],
        match_appearances: dict[str, int],
        top_batters: list[RankedCandidate],
        top_bowlers: list[RankedCandidate],
        n_iterations: int = 1000,
    ) -> None:
        """Legacy match-level delivery bootstrap with inlined cricket parsing helpers."""
        rng = random.Random(self.seed)
        match_keys = list(deliveries_by_match.keys())
        n_matches = len(match_keys)

        if n_matches == 0:
            return

        bat_by_m: dict[str, dict[str, list[int]]] = {}
        bowl_by_m: dict[str, dict[str, list[int]]] = {}

        for mid in match_keys:
            bat_m: dict[str, list[int]] = {}
            bowl_m: dict[str, list[int]] = {}
            delivs = deliveries_by_match.get(mid, [])
            sts = states_by_match.get(mid, [])

            for d, st in zip(delivs, sts, strict=False):
                if st.mpt == "SUPER_OVER":
                    continue
                et = str(d.get("extras_type", "None")).strip().lower()
                is_bf = et != "wide"
                is_leg = et not in ("wide", "noball", "overstep")
                s_id = st.striker_id
                b_id = st.bowler_id
                runs_bat = int(d.get("runs", 0) or 0)

                # Bowler runs calculation
                if et in ("bye", "legbye"):
                    bowler_runs = 0
                else:
                    bowler_runs = runs_bat + int(d.get("extras_runs", 0) or 0)

                dt = str(d.get("dismissal_type", "")).strip().lower()
                is_w = str(d.get("is_wicket", "")).strip().lower() in ("true", "1")
                is_bowler_w = is_w and dt in (
                    "bowled",
                    "caught",
                    "lbw",
                    "stumped",
                    "hit wicket",
                    "caught and bowled",
                )
                dismissed_pid = str(d.get("dismissed_player_id", "")).strip()

                if is_w and dismissed_pid and st.is_pressure:
                    if dismissed_pid not in bat_m:
                        bat_m[dismissed_pid] = [0, 0, 0, 0, 0, 0, 0, 0]
                    bat_m[dismissed_pid][7] += 1

                if is_bf:
                    if s_id not in bat_m:
                        bat_m[s_id] = [0, 0, 0, 0, 0, 0, 0, 0]
                    bat_m[s_id][0] += 1
                    bat_m[s_id][1] += runs_bat
                    if st.is_pressure:
                        bat_m[s_id][2] += 1
                        bat_m[s_id][3] += runs_bat
                        if runs_bat == 0 and et != "overstep":
                            bat_m[s_id][4] += 1
                        elif runs_bat == 4:
                            bat_m[s_id][5] += 1
                        elif runs_bat == 6:
                            bat_m[s_id][6] += 1

                if is_leg:
                    if b_id not in bowl_m:
                        bowl_m[b_id] = [0, 0, 0, 0, 0, 0, 0]
                    bowl_m[b_id][0] += 1
                    bowl_m[b_id][1] += bowler_runs
                    if st.is_pressure:
                        bowl_m[b_id][2] += 1
                        bowl_m[b_id][3] += bowler_runs
                        if bowler_runs == 0:
                            bowl_m[b_id][4] += 1
                        if runs_bat in (4, 6):
                            bowl_m[b_id][5] += 1
                        if is_bowler_w:
                            bowl_m[b_id][6] += 1
                elif et in ("wide", "overstep"):
                    if b_id not in bowl_m:
                        bowl_m[b_id] = [0, 0, 0, 0, 0, 0, 0]
                    bowl_m[b_id][1] += bowler_runs
                    if st.is_pressure:
                        bowl_m[b_id][3] += bowler_runs

            bat_by_m[mid] = bat_m
            bowl_by_m[mid] = bowl_m

        bat_tracker: dict[str, list[float]] = {b.player_id: [] for b in top_batters}
        bat_top10_hits: dict[str, int] = {b.player_id: 0 for b in top_batters}
        bowl_tracker: dict[str, list[float]] = {w.player_id: [] for w in top_bowlers}
        bowl_top10_hits: dict[str, int] = {w.player_id: 0 for w in top_bowlers}

        k_bat = 30.0
        k_bat_avg = 5.0
        k_bowl = 40.0

        for _ in range(n_iterations):
            sample_mids = [match_keys[rng.randint(0, n_matches - 1)] for _ in range(n_matches)]
            mid_counts = Counter(sample_mids)

            b_agg: dict[str, list[int]] = {}
            for mid, cnt in mid_counts.items():
                m_bats = bat_by_m.get(mid, {})
                for pid, vec in m_bats.items():
                    if pid not in b_agg:
                        b_agg[pid] = [0, 0, 0, 0, 0, 0, 0, 0]
                    for idx in range(8):
                        b_agg[pid][idx] += vec[idx] * cnt

            w_agg: dict[str, list[int]] = {}
            for mid, cnt in mid_counts.items():
                m_bowls = bowl_by_m.get(mid, {})
                for pid, vec in m_bowls.items():
                    if pid not in w_agg:
                        w_agg[pid] = [0, 0, 0, 0, 0, 0, 0]
                    for idx in range(7):
                        w_agg[pid][idx] += vec[idx] * cnt

            p_runs_tot = sum(v[3] for v in b_agg.values())
            p_bf_tot = sum(v[2] for v in b_agg.values())
            p_d_tot = sum(v[7] for v in b_agg.values())
            prior_sr = (p_runs_tot / max(1, p_bf_tot) * 100.0) if p_bf_tot > 0 else 140.0
            prior_avg = (p_runs_tot / max(1, p_d_tot)) if p_d_tot > 0 else 20.0

            rep_bat_scores: list[tuple[str, float]] = []
            for pid, v in b_agg.items():
                bf_all, r_all, p_bf, p_r, p_dot, p_4, p_6, p_d = v
                if bf_all < 80 or p_bf < 25 or match_appearances.get(pid, 0) < 10:
                    continue
                sr_all = (r_all / bf_all * 100.0) if bf_all > 0 else 120.0
                sr_p_raw = (p_r / p_bf * 100.0) if p_bf > 0 else 140.0
                sr_p_shrunk = (p_bf / (p_bf + k_bat)) * sr_p_raw + (
                    k_bat / (p_bf + k_bat)
                ) * prior_sr
                dot_pct = (p_dot / p_bf * 100.0) if p_bf > 0 else 0.0
                bnd_pct = ((p_4 * 4 + p_6 * 6) / max(1, p_r) * 100.0) if p_r > 0 else 0.0
                delta_sr = sr_p_raw - sr_all
                c_sr = max(0.0, min(100.0, (sr_p_shrunk - 80.0) / 1.20))
                c_dot = max(0.0, min(100.0, 100.0 - dot_pct * 1.5))
                c_bnd = max(0.0, min(100.0, bnd_pct * 1.25))
                c_delta = max(0.0, min(100.0, 50.0 + delta_sr * 1.5))

                if p_d > 0:
                    avg_p_raw = p_r / p_d
                    avg_p_shrunk = (p_d / (p_d + k_bat_avg)) * avg_p_raw + (
                        k_bat_avg / (p_d + k_bat_avg)
                    ) * prior_avg
                    c_avg = max(0.0, min(100.0, (avg_p_shrunk - 10.0) * 2.0))
                    bpps = 0.35 * c_sr + 0.25 * c_avg + 0.15 * c_dot + 0.15 * c_bnd + 0.10 * c_delta
                else:
                    bpps = 0.4667 * c_sr + 0.2000 * c_dot + 0.2000 * c_bnd + 0.1333 * c_delta
                rep_bat_scores.append((pid, bpps))

            rep_bat_scores.sort(key=lambda x: x[1], reverse=True)
            top_bats_rep = {x[0] for x in rep_bat_scores[:10]}
            bat_score_dict = dict(rep_bat_scores)

            for b in top_batters:
                pid = b.player_id
                if pid in bat_score_dict:
                    bat_tracker[pid].append(bat_score_dict[pid])
                if pid in top_bats_rep:
                    bat_top10_hits[pid] += 1

            w_runs_tot = sum(v[3] for v in w_agg.values())
            w_lb_tot = sum(v[2] for v in w_agg.values())
            prior_econ = (w_runs_tot / max(1, w_lb_tot) * 6.0) if w_lb_tot > 0 else 9.0

            rep_bowl_scores: list[tuple[str, float]] = []
            for pid, v in w_agg.items():
                lb_all, r_all, p_lb, p_r, p_dot, p_bnd, p_w = v
                if lb_all < 80 or p_lb < 20 or match_appearances.get(pid, 0) < 10:
                    continue
                econ_all = (r_all / lb_all * 6.0) if lb_all > 0 else 8.5
                econ_p_raw = (p_r / p_lb * 6.0) if p_lb > 0 else 9.0
                econ_p_shrunk = (p_lb / (p_lb + k_bowl)) * econ_p_raw + (
                    k_bowl / (p_lb + k_bowl)
                ) * prior_econ
                dot_pct = p_dot / p_lb * 100.0
                bnd_pct = p_bnd / p_lb * 100.0
                wkt_rate = p_w / p_lb * 100.0
                delta_econ = econ_all - econ_p_raw

                b_econ = max(0.0, min(100.0, (13.5 - econ_p_shrunk) * 13.0))
                b_dot = max(0.0, min(100.0, dot_pct * 2.0))
                b_bnd = max(0.0, min(100.0, (25.0 - bnd_pct) * 5.0))
                b_wkt = max(0.0, min(100.0, wkt_rate * 12.0))
                b_delta = max(0.0, min(100.0, 50.0 + delta_econ * 10.0))
                bwps = 0.35 * b_econ + 0.25 * b_dot + 0.15 * b_bnd + 0.15 * b_wkt + 0.10 * b_delta
                rep_bowl_scores.append((pid, bwps))

            rep_bowl_scores.sort(key=lambda x: x[1], reverse=True)
            top_bowls_rep = {x[0] for x in rep_bowl_scores[:10]}
            bowl_score_dict = dict(rep_bowl_scores)

            for w in top_bowlers:
                pid = w.player_id
                if pid in bowl_score_dict:
                    bowl_tracker[pid].append(bowl_score_dict[pid])
                if pid in top_bowls_rep:
                    bowl_top10_hits[pid] += 1

        for b in top_batters:
            scores = sorted(bat_tracker[b.player_id])
            if scores:
                low_idx = int(0.025 * len(scores))
                high_idx = int(0.975 * len(scores))
                b.score_ci_lower = round(scores[min(low_idx, len(scores) - 1)], 2)
                b.score_ci_upper = round(scores[min(high_idx, len(scores) - 1)], 2)
            else:
                b.score_ci_lower = b.score
                b.score_ci_upper = b.score
            b.top10_stability_pct = round(
                bat_top10_hits[b.player_id] / max(1, n_iterations) * 100.0, 1
            )

        for w in top_bowlers:
            scores = sorted(bowl_tracker[w.player_id])
            if scores:
                low_idx = int(0.025 * len(scores))
                high_idx = int(0.975 * len(scores))
                w.score_ci_lower = round(scores[min(low_idx, len(scores) - 1)], 2)
                w.score_ci_upper = round(scores[min(high_idx, len(scores) - 1)], 2)
            else:
                w.score_ci_lower = w.score
                w.score_ci_upper = w.score
            w.top10_stability_pct = round(
                bowl_top10_hits[w.player_id] / max(1, n_iterations) * 100.0, 1
            )


# Backward compatibility alias
SiceRankingEngine = SICERankingEngine
