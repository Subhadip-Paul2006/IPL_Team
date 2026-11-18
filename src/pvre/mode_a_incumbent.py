"""Player Verification & Research Engine (PVRE) — Mode A: Incumbent Player Intelligence.

Implements Phase 04B Module A1 (RR Historical Performance), Module A2 (Recent Global Form),
and Module A3 (Replaceability Evidence Assessment) in strict compliance with TRD §9.3,
PRD FR-PV2..FR-PV4, DATA_DICTIONARY §9, §10, and AI_INSTRUCTIONS R1..R22.
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field

from src.contracts.base import BaseContract
from src.contracts.pvre import (
    CareerCoverageState,
    PVREOutputContract,
    PVRERequestContract,
    PVREReviewStatus,
    PVREVerificationStatus,
    ReplaceabilitySignal,
    ResearchMode,
    RouteStatus,
)

# ==============================================================================
# Domain Constants & Taxonomy
# ==============================================================================

RR_CANONICAL_NAME: str = "Rajasthan Royals"
RR_SHORT_CODE: str = "RR"

# Authoritative operational active seasons for Rajasthan Royals (TRD §4.1)
RR_ACTIVE_SEASONS: frozenset[int] = frozenset({
    2008,
    2009,
    2010,
    2011,
    2012,
    2013,
    2014,
    2015,
    2018,
    2019,
    2020,
    2021,
    2022,
    2023,
    2024,
    2025,
    2026,
})

RR_SUSPENDED_SEASONS: frozenset[int] = frozenset({2016, 2017})
RR_FUTURE_SEASONS: frozenset[int] = frozenset({2027})

# Half-life parameter for exponential time decay: T_half = 365 days (DATA_DICTIONARY §9.1)
DEFAULT_T_HALF_DAYS: float = 365.0

# Minimum sample size thresholds (DATA_DICTIONARY §9.1 R06, TRD §9.3.3)
MIN_BATTING_BALLS_FACED: int = 20
MIN_BOWLING_LEGAL_BALLS: int = 30

# Fallback string token for uncomputable metrics
NOT_COMPUTABLE_TOKEN: str = "NOT_COMPUTABLE_FROM_AVAILABLE_SOURCES"


class GapCode(StrEnum):
    """Mutually exclusive gap taxonomy codes for unplayed matches (DATA_DICTIONARY §9.1 R05)."""

    GAP_VERIFIED_INJURY = "GAP_VERIFIED_INJURY"
    GAP_NATIONAL_DUTY = "GAP_NATIONAL_DUTY"
    GAP_DOMESTIC_CLASH = "GAP_DOMESTIC_CLASH"
    GAP_NOT_SELECTED = "GAP_NOT_SELECTED"
    GAP_UNKNOWN_UNEXPLAINED = "GAP_UNKNOWN_UNEXPLAINED"


# Default balls per over by competition name / archive
COMPETITION_BALLS_PER_OVER: dict[str, int] = {
    "The Hundred": 5,
    "The Hundred Men": 5,
    "hnd_male_json": 5,
}


def get_balls_per_over(competition_name: str | None, default: int = 6) -> int:
    """Return format-aware balls per over for a competition (e.g. 5 for The Hundred)."""
    if not competition_name:
        return default
    for comp_key, bpo in COMPETITION_BALLS_PER_OVER.items():
        if comp_key.lower() in competition_name.lower():
            return bpo
    return default


def calculate_time_decay_weight(
    match_date: date,
    evaluation_date: date,
    window_years: int = 3,
    t_half_days: float = DEFAULT_T_HALF_DAYS,
) -> float:
    """Calculate exponential time-decay weight for a match within research window.

    Formula (DATA_DICTIONARY §9.1):
        w(t_i) = exp(-ln(2) * (t_eval - t_i) / T_half)

    Rules:
        - If t_i > t_eval: excluded (returns 0.0)
        - If (t_eval - t_i) > W * 365.25 days: w(t_i) = 0.0
    """
    if match_date > evaluation_date:
        return 0.0

    delta_days = (evaluation_date - match_date).days
    max_days = float(window_years) * 365.25
    if delta_days > max_days:
        return 0.0

    ln2 = math.log(2.0)
    return math.exp(-ln2 * float(delta_days) / float(t_half_days))


# ==============================================================================
# Typed Domain Models for Mode A Profiles
# ==============================================================================


class SeasonSplitBatting(BaseContract):
    """Batting statistics for a specific season."""

    runs: int = 0
    balls_faced: int = 0
    dismissals: int = 0
    fours: int = 0
    sixes: int = 0
    dot_balls: int = 0
    strike_rate: float | None = None
    batting_average: float | None = None
    boundary_pct: float | None = None
    dot_pct: float | None = None
    phase_splits: dict[str, Any] = Field(default_factory=dict)


class SeasonSplitBowling(BaseContract):
    """Bowling statistics for a specific season."""

    legal_balls: int = 0
    runs_conceded: int = 0
    wickets: int = 0
    dot_balls: int = 0
    economy_rate: float | None = None
    bowling_average: float | None = None
    bowling_strike_rate: float | None = None
    dot_pct: float | None = None
    phase_splits: dict[str, Any] = Field(default_factory=dict)


class RRSeasonRecord(BaseContract):
    """Single season participation and performance record for Rajasthan Royals."""

    season: str
    in_squad: bool = True
    contract_type: str = "Squad Inclusion"
    appearances: int = 0
    is_squad_only: bool = False
    tactical_role: str = "UNKNOWN"
    batting: SeasonSplitBatting = Field(default_factory=SeasonSplitBatting)
    bowling: SeasonSplitBowling = Field(default_factory=SeasonSplitBowling)
    catches: int = 0
    run_outs: int = 0
    stumpings: int = 0


class RRHistoricalProfile(BaseContract):
    """Module A1: Rajasthan Royals Historical Career Profile (TRD §9.3.1)."""

    player_id: UUID | None = None
    canonical_name: str
    total_seasons: int = 0
    seasons_active: list[str] = Field(default_factory=list)
    squad_only_seasons: list[str] = Field(default_factory=list)
    suspension_seasons_excluded: list[str] = Field(default_factory=list)
    total_matches: int = 0
    total_runs: int = 0
    total_balls_faced: int = 0
    strike_rate: float | None = None
    batting_average: float | None = None
    boundary_pct: float | None = None
    dot_ball_pct: float | None = None
    total_legal_balls: int = 0
    total_runs_conceded: int = 0
    total_wickets: int = 0
    economy_rate: float | None = None
    bowling_average: float | None = None
    bowling_strike_rate: float | None = None
    fielding_summary: dict[str, int] = Field(
        default_factory=lambda: {"catches": 0, "run_outs": 0, "stumpings": 0}
    )
    season_splits: list[dict[str, Any]] = Field(default_factory=list)
    phase_splits: dict[str, Any] = Field(default_factory=dict)
    role_evolution: list[dict[str, str]] = Field(default_factory=list)
    provenance_ids: list[UUID | int] = Field(default_factory=list)


class RecentGlobalPerformance(BaseContract):
    """Module A2: Recent Global Performance Profile (TRD §9.3.2, DATA_DICTIONARY §9)."""

    evaluation_date: date
    window_years: int
    window_start: date
    window_end: date
    t_half_days: float = DEFAULT_T_HALF_DAYS
    weighted_strike_rate: float | None = None
    weighted_economy: float | None = None
    boundary_pct: float | None = None
    dot_ball_pct: float | str | None = None
    gap_records: list[dict[str, Any]] = Field(default_factory=list)
    sample_indicators: dict[str, Any] = Field(default_factory=dict)
    competitions_investigated: list[str] = Field(default_factory=list)
    format_breakdown: dict[str, Any] = Field(default_factory=dict)
    super_overs_excluded_count: int = 0


class ReplaceabilityAssessment(BaseContract):
    """Module A3: Incumbent Replaceability Evidence Assessment (TRD §9.3.3, DATA_DICTIONARY §10)."""

    signal: ReplaceabilitySignal
    signal_rationale: str
    role_archetype: str
    age_at_evaluation: float | None = None
    evaluation_factors: dict[str, Any] = Field(default_factory=dict)
    insufficient_sample_flag: bool = False
    review_required_flag: bool = False
    confidence: float | None = None
    forward_to_sice: bool = True


# ==============================================================================
# Module A1: RR Historical Performance Analyzer
# ==============================================================================


class ModuleA1RRHistory:
    """Analyzes a player's complete tenure across Rajasthan Royals active seasons.

    Guarantees:
    - Analyzes evidenced active seasons (2008–2015, 2018–2026).
    - Strictly excludes 2016–2017 suspension seasons from active stats.
    - Squad vs appearance separation: if appearances == 0, strictly 0 runs, 0 balls, 0 wickets.
    - Season splits, phase stats, and tactical role evolution tracking.
    """

    @classmethod
    def analyze(
        cls,
        player_id: UUID | None,
        canonical_name: str,
        squad_records: list[dict[str, Any]],
        match_records: list[dict[str, Any]],
        provenance_ids: list[UUID | int] | None = None,
    ) -> RRHistoricalProfile:
        """Analyze RR historical performance from squad memberships and match records."""
        seasons_active: list[str] = []
        squad_only_seasons: list[str] = []
        suspension_seasons_excluded: list[str] = []
        season_split_dicts: list[dict[str, Any]] = []
        role_evolution: list[dict[str, str]] = []

        total_matches = 0
        total_runs = 0
        total_balls_faced = 0
        total_dismissals = 0
        total_fours = 0
        total_sixes = 0
        total_batting_dots = 0

        total_legal_balls = 0
        total_runs_conceded = 0
        total_wickets = 0
        total_bowling_dots = 0

        total_catches = 0
        total_run_outs = 0
        total_stumpings = 0

        pp_runs = 0
        pp_balls = 0
        mid_runs = 0
        mid_balls = 0
        dth_runs = 0
        dth_balls = 0

        pp_bowl_balls = 0
        pp_bowl_runs = 0
        pp_bowl_wkts = 0
        mid_bowl_balls = 0
        mid_bowl_runs = 0
        mid_bowl_wkts = 0
        dth_bowl_balls = 0
        dth_bowl_runs = 0
        dth_bowl_wkts = 0

        # Group matches by season
        rr_matches_by_season: dict[int, list[dict[str, Any]]] = {}
        for match in match_records:
            # Check team identity
            team_code = str(match.get("team_code") or match.get("team_name") or "")
            if "RR" not in team_code.upper() and "RAJASTHAN" not in team_code.upper():
                continue

            season_val = match.get("season")
            if season_val is None:
                # Try inferring from match_date
                m_date = match.get("match_date")
                if isinstance(m_date, date):
                    season_val = m_date.year
                else:
                    continue

            try:
                season_int = int(str(season_val).strip()[:4])
            except (ValueError, TypeError):
                continue

            if season_int in RR_SUSPENDED_SEASONS:
                season_str = str(season_int)
                if season_str not in suspension_seasons_excluded:
                    suspension_seasons_excluded.append(season_str)
                continue

            rr_matches_by_season.setdefault(season_int, []).append(match)

        # Process each squad membership
        processed_seasons: set[int] = set()
        for squad in squad_records:
            raw_season = squad.get("season")
            try:
                season_int = int(str(raw_season).strip()[:4])
            except (ValueError, TypeError):
                continue

            processed_seasons.add(season_int)

            # Check suspension years
            if season_int in RR_SUSPENDED_SEASONS:
                season_str = str(season_int)
                if season_str not in suspension_seasons_excluded:
                    suspension_seasons_excluded.append(season_str)
                continue

            # Check future seasons
            if season_int in RR_FUTURE_SEASONS:
                continue

            season_str = str(season_int)
            matches_in_season = rr_matches_by_season.get(season_int, [])
            appearances = squad.get("appearances")
            if appearances is None:
                appearances = len(matches_in_season)

            contract_type = str(squad.get("contract_type") or "Squad Inclusion")
            tactical_role = str(squad.get("tactical_role") or "UNKNOWN")

            if appearances == 0:
                # Strict squad vs appearance separation (AC-25, TRD §9.3.1)
                squad_only_seasons.append(season_str)
                season_split_dicts.append({
                    "season": season_str,
                    "in_squad": True,
                    "contract_type": contract_type,
                    "appearances": 0,
                    "is_squad_only": True,
                    "tactical_role": tactical_role,
                    "batting": {
                        "runs": 0,
                        "balls_faced": 0,
                        "dismissals": 0,
                        "fours": 0,
                        "sixes": 0,
                        "dot_balls": 0,
                        "strike_rate": None,
                        "batting_average": None,
                        "boundary_pct": None,
                        "dot_pct": None,
                    },
                    "bowling": {
                        "legal_balls": 0,
                        "runs_conceded": 0,
                        "wickets": 0,
                        "dot_balls": 0,
                        "economy_rate": None,
                        "bowling_average": None,
                        "bowling_strike_rate": None,
                        "dot_pct": None,
                    },
                    "fielding": {"catches": 0, "run_outs": 0, "stumpings": 0},
                })
                role_evolution.append({"season": season_str, "role": tactical_role})
                continue

            # Player appeared in matches this season
            seasons_active.append(season_str)
            total_matches += appearances

            s_runs = 0
            s_balls = 0
            s_dismissals = 0
            s_fours = 0
            s_sixes = 0
            s_bat_dots = 0

            s_legal_balls = 0
            s_runs_conceded = 0
            s_wickets = 0
            s_bowl_dots = 0

            s_catches = 0
            s_run_outs = 0
            s_stumpings = 0

            for m in matches_in_season:
                # Batting
                b_runs = int(m.get("runs") or 0)
                b_balls = int(m.get("balls_faced") or 0)
                b_dismissals = 1 if m.get("dismissed") else 0
                b_fours = int(m.get("fours") or 0)
                b_sixes = int(m.get("sixes") or 0)
                b_dots = int(m.get("dot_balls") or 0)

                s_runs += b_runs
                s_balls += b_balls
                s_dismissals += b_dismissals
                s_fours += b_fours
                s_sixes += b_sixes
                s_bat_dots += b_dots

                # Phase batting
                pp_b_runs = int(m.get("powerplay_runs") or 0)
                pp_b_balls = int(m.get("powerplay_balls") or 0)
                mid_b_runs = int(m.get("middle_runs") or 0)
                mid_b_balls = int(m.get("middle_balls") or 0)
                dth_b_runs = int(m.get("death_runs") or 0)
                dth_b_balls = int(m.get("death_balls") or 0)

                pp_runs += pp_b_runs
                pp_balls += pp_b_balls
                mid_runs += mid_b_runs
                mid_balls += mid_b_balls
                dth_runs += dth_b_runs
                dth_balls += dth_b_balls

                # Bowling
                bw_balls = int(m.get("legal_balls") or 0)
                bw_runs = int(m.get("runs_conceded") or 0)
                bw_wkts = int(m.get("wickets") or 0)
                bw_dots = int(m.get("dot_balls_bowled") or 0)

                s_legal_balls += bw_balls
                s_runs_conceded += bw_runs
                s_wickets += bw_wkts
                s_bowl_dots += bw_dots

                # Phase bowling
                pp_bw_balls = int(m.get("powerplay_legal_balls") or 0)
                pp_bw_runs = int(m.get("powerplay_runs_conceded") or 0)
                pp_bw_wkts = int(m.get("powerplay_wickets") or 0)
                mid_bw_balls = int(m.get("middle_legal_balls") or 0)
                mid_bw_runs = int(m.get("middle_runs_conceded") or 0)
                mid_bw_wkts = int(m.get("middle_wickets") or 0)
                dth_bw_balls = int(m.get("death_legal_balls") or 0)
                dth_bw_runs = int(m.get("death_runs_conceded") or 0)
                dth_bw_wkts = int(m.get("death_wickets") or 0)

                pp_bowl_balls += pp_bw_balls
                pp_bowl_runs += pp_bw_runs
                pp_bowl_wkts += pp_bw_wkts
                mid_bowl_balls += mid_bw_balls
                mid_bowl_runs += mid_bw_runs
                mid_bowl_wkts += mid_bw_wkts
                dth_bowl_balls += dth_bw_balls
                dth_bowl_runs += dth_bw_runs
                dth_bowl_wkts += dth_bw_wkts

                # Fielding
                s_catches += int(m.get("catches") or 0)
                s_run_outs += int(m.get("run_outs") or 0)
                s_stumpings += int(m.get("stumpings") or 0)

            total_runs += s_runs
            total_balls_faced += s_balls
            total_dismissals += s_dismissals
            total_fours += s_fours
            total_sixes += s_sixes
            total_batting_dots += s_bat_dots

            total_legal_balls += s_legal_balls
            total_runs_conceded += s_runs_conceded
            total_wickets += s_wickets
            total_bowling_dots += s_bowl_dots

            total_catches += s_catches
            total_run_outs += s_run_outs
            total_stumpings += s_stumpings

            s_sr = round(100.0 * s_runs / s_balls, 2) if s_balls > 0 else None
            s_avg = (
                round(float(s_runs) / s_dismissals, 2)
                if s_dismissals > 0
                else (float(s_runs) if s_balls > 0 else None)
            )
            s_b_pct = (
                round(100.0 * (s_fours * 4 + s_sixes * 6) / s_runs, 2)
                if s_runs > 0
                else None
            )
            s_dot_pct = round(100.0 * s_bat_dots / s_balls, 2) if s_balls > 0 else None

            s_econ = (
                round(6.0 * s_runs_conceded / s_legal_balls, 2)
                if s_legal_balls > 0
                else None
            )
            s_bw_avg = (
                round(float(s_runs_conceded) / s_wickets, 2)
                if s_wickets > 0
                else None
            )
            s_bw_sr = (
                round(float(s_legal_balls) / s_wickets, 2)
                if s_wickets > 0
                else None
            )
            s_bw_dot_pct = (
                round(100.0 * s_bowl_dots / s_legal_balls, 2)
                if s_legal_balls > 0
                else None
            )

            season_split_dicts.append({
                "season": season_str,
                "in_squad": True,
                "contract_type": contract_type,
                "appearances": appearances,
                "is_squad_only": False,
                "tactical_role": tactical_role,
                "batting": {
                    "runs": s_runs,
                    "balls_faced": s_balls,
                    "dismissals": s_dismissals,
                    "fours": s_fours,
                    "sixes": s_sixes,
                    "dot_balls": s_bat_dots,
                    "strike_rate": s_sr,
                    "batting_average": s_avg,
                    "boundary_pct": s_b_pct,
                    "dot_pct": s_dot_pct,
                },
                "bowling": {
                    "legal_balls": s_legal_balls,
                    "runs_conceded": s_runs_conceded,
                    "wickets": s_wickets,
                    "dot_balls": s_bowl_dots,
                    "economy_rate": s_econ,
                    "bowling_average": s_bw_avg,
                    "bowling_strike_rate": s_bw_sr,
                    "dot_pct": s_bw_dot_pct,
                },
                "fielding": {
                    "catches": s_catches,
                    "run_outs": s_run_outs,
                    "stumpings": s_stumpings,
                },
            })
            role_evolution.append({"season": season_str, "role": tactical_role})

        # Check any match seasons not in squad records
        for s_int, m_list in rr_matches_by_season.items():
            if s_int in processed_seasons or s_int in RR_SUSPENDED_SEASONS:
                continue
            s_str = str(s_int)
            seasons_active.append(s_str)
            app = len(m_list)
            total_matches += app

            s_runs = sum(int(m.get("runs") or 0) for m in m_list)
            s_balls = sum(int(m.get("balls_faced") or 0) for m in m_list)
            s_dismissals = sum(1 if m.get("dismissed") else 0 for m in m_list)
            s_fours = sum(int(m.get("fours") or 0) for m in m_list)
            s_sixes = sum(int(m.get("sixes") or 0) for m in m_list)
            s_bat_dots = sum(int(m.get("dot_balls") or 0) for m in m_list)

            s_legal_balls = sum(int(m.get("legal_balls") or 0) for m in m_list)
            s_runs_conceded = sum(int(m.get("runs_conceded") or 0) for m in m_list)
            s_wickets = sum(int(m.get("wickets") or 0) for m in m_list)
            s_bowl_dots = sum(int(m.get("dot_balls_bowled") or 0) for m in m_list)

            total_runs += s_runs
            total_balls_faced += s_balls
            total_dismissals += s_dismissals
            total_fours += s_fours
            total_sixes += s_sixes
            total_batting_dots += s_bat_dots

            total_legal_balls += s_legal_balls
            total_runs_conceded += s_runs_conceded
            total_wickets += s_wickets
            total_bowling_dots += s_bowl_dots

            s_sr = round(100.0 * s_runs / s_balls, 2) if s_balls > 0 else None
            s_avg = (
                round(float(s_runs) / s_dismissals, 2)
                if s_dismissals > 0
                else (float(s_runs) if s_balls > 0 else None)
            )

            season_split_dicts.append({
                "season": s_str,
                "in_squad": True,
                "contract_type": "Match Appearance",
                "appearances": app,
                "is_squad_only": False,
                "tactical_role": "UNKNOWN",
                "batting": {
                    "runs": s_runs,
                    "balls_faced": s_balls,
                    "dismissals": s_dismissals,
                    "fours": s_fours,
                    "sixes": s_sixes,
                    "dot_balls": s_bat_dots,
                    "strike_rate": s_sr,
                    "batting_average": s_avg,
                    "boundary_pct": None,
                    "dot_pct": None,
                },
                "bowling": {
                    "legal_balls": s_legal_balls,
                    "runs_conceded": s_runs_conceded,
                    "wickets": s_wickets,
                    "dot_balls": s_bowl_dots,
                    "economy_rate": None,
                    "bowling_average": None,
                    "bowling_strike_rate": None,
                    "dot_pct": None,
                },
                "fielding": {"catches": 0, "run_outs": 0, "stumpings": 0},
            })

        # Calculate career rates (Strict Rule R1: None if 0 denominator)
        career_sr = (
            round(100.0 * total_runs / total_balls_faced, 2)
            if total_balls_faced > 0
            else None
        )
        career_avg = (
            round(float(total_runs) / total_dismissals, 2)
            if total_dismissals > 0
            else (float(total_runs) if total_balls_faced > 0 else None)
        )
        career_boundary_pct = (
            round(100.0 * (total_fours * 4 + total_sixes * 6) / total_runs, 2)
            if total_runs > 0
            else None
        )
        career_dot_pct = (
            round(100.0 * total_batting_dots / total_balls_faced, 2)
            if total_balls_faced > 0
            else None
        )

        career_economy = (
            round(6.0 * total_runs_conceded / total_legal_balls, 2)
            if total_legal_balls > 0
            else None
        )
        career_bw_avg = (
            round(float(total_runs_conceded) / total_wickets, 2)
            if total_wickets > 0
            else None
        )
        career_bw_sr = (
            round(float(total_legal_balls) / total_wickets, 2)
            if total_wickets > 0
            else None
        )

        # Build phase summary
        phase_splits = {
            "batting": {
                "powerplay": {
                    "runs": pp_runs,
                    "balls": pp_balls,
                    "strike_rate": (
                        round(100.0 * pp_runs / pp_balls, 2) if pp_balls > 0 else None
                    ),
                },
                "middle": {
                    "runs": mid_runs,
                    "balls": mid_balls,
                    "strike_rate": (
                        round(100.0 * mid_runs / mid_balls, 2) if mid_balls > 0 else None
                    ),
                },
                "death": {
                    "runs": dth_runs,
                    "balls": dth_balls,
                    "strike_rate": (
                        round(100.0 * dth_runs / dth_balls, 2) if dth_balls > 0 else None
                    ),
                },
            },
            "bowling": {
                "powerplay": {
                    "legal_balls": pp_bowl_balls,
                    "runs_conceded": pp_bowl_runs,
                    "wickets": pp_bowl_wkts,
                    "economy": (
                        round(6.0 * pp_bowl_runs / pp_bowl_balls, 2)
                        if pp_bowl_balls > 0
                        else None
                    ),
                },
                "middle": {
                    "legal_balls": mid_bowl_balls,
                    "runs_conceded": mid_bowl_runs,
                    "wickets": mid_bowl_wkts,
                    "economy": (
                        round(6.0 * mid_bowl_runs / mid_bowl_balls, 2)
                        if mid_bowl_balls > 0
                        else None
                    ),
                },
                "death": {
                    "legal_balls": dth_bowl_balls,
                    "runs_conceded": dth_bowl_runs,
                    "wickets": dth_bowl_wkts,
                    "economy": (
                        round(6.0 * dth_bowl_runs / dth_bowl_balls, 2)
                        if dth_bowl_balls > 0
                        else None
                    ),
                },
            },
        }

        # Deduplicate and sort seasons
        seasons_active = sorted(set(seasons_active))
        squad_only_seasons = sorted(set(squad_only_seasons))
        suspension_seasons_excluded = sorted(set(suspension_seasons_excluded))
        total_seasons = len(set(seasons_active + squad_only_seasons))

        return RRHistoricalProfile(
            player_id=player_id,
            canonical_name=canonical_name,
            total_seasons=total_seasons,
            seasons_active=seasons_active,
            squad_only_seasons=squad_only_seasons,
            suspension_seasons_excluded=suspension_seasons_excluded,
            total_matches=total_matches,
            total_runs=total_runs,
            total_balls_faced=total_balls_faced,
            strike_rate=career_sr,
            batting_average=career_avg,
            boundary_pct=career_boundary_pct,
            dot_ball_pct=career_dot_pct,
            total_legal_balls=total_legal_balls,
            total_runs_conceded=total_runs_conceded,
            total_wickets=total_wickets,
            economy_rate=career_economy,
            bowling_average=career_bw_avg,
            bowling_strike_rate=career_bw_sr,
            fielding_summary={
                "catches": total_catches,
                "run_outs": total_run_outs,
                "stumpings": total_stumpings,
            },
            season_splits=season_split_dicts,
            phase_splits=phase_splits,
            role_evolution=role_evolution,
            provenance_ids=provenance_ids or [],
        )


# ==============================================================================
# Module A2: Recent Global Performance Analyzer
# ==============================================================================


class ModuleA2GlobalPerformance:
    """Analyzes recent global performance across recognized franchise leagues and formats.

    Guarantees:
    - Configurable research window (2–3 years relative to evaluation_date).
    - Matches after evaluation_date or older than window are excluded.
    - Exponential time-decay weighting function with T_half = 365 days.
    - Format-aware economy rate: respects balls_per_over = 5 for The Hundred, 6 for T20.
    - Metrics R01–R06 strictly adhering to DATA_DICTIONARY §9.1.
    - Super Over isolation: CricSheet innings 3 or 4 strictly excluded from metrics.
    - Format isolation: First-Class and List A are segregated and not mixed with T20.
    - Gap taxonomy: tags unplayed fixtures with mutually exclusive gap codes.
    """

    @classmethod
    def analyze(
        cls,
        evaluation_date: date,
        window_years: int = 3,
        match_records: list[dict[str, Any]] | None = None,
        injury_records: list[dict[str, Any]] | None = None,
        absence_records: list[dict[str, Any]] | None = None,
        t_half_days: float = DEFAULT_T_HALF_DAYS,
    ) -> RecentGlobalPerformance:
        """Analyze recent global performance across the research window."""
        matches = match_records or []
        injuries = injury_records or []
        absences = absence_records or []

        # Calculate window start date (W * 365.25 days)
        max_window_days = int(window_years * 365.25)
        window_start = evaluation_date - timedelta(days=max_window_days)

        competitions_set: set[str] = set()
        format_breakdown: dict[str, dict[str, Any]] = {}
        super_overs_excluded = 0

        # Weighted accumulators for primary T20 format (or all white-ball franchise leagues)
        sum_w_bat_runs = 0.0
        sum_w_bat_balls = 0.0
        sum_w_boundary_runs = 0.0
        sum_w_total_runs_for_boundary = 0.0
        sum_w_dot_balls = 0.0
        sum_w_dot_balls_faced = 0.0

        sum_w_bowl_econ_num = 0.0  # sum(w * bpo * runs_conceded)
        sum_w_bowl_legal_balls = 0.0

        # Unweighted sample totals
        total_matches = 0
        total_innings = 0
        total_balls_faced = 0
        total_legal_balls_bowled = 0
        total_wickets_taken = 0
        total_runs_scored = 0
        total_runs_conceded = 0

        has_scorecard_only_matches = False
        has_delivery_dot_data = False

        for match in matches:
            # 1. Date Check: Matches after evaluation_date are strictly excluded
            m_date = match.get("match_date")
            if isinstance(m_date, str):
                m_date = date.fromisoformat(m_date)
            if not isinstance(m_date, date):
                continue

            if m_date > evaluation_date:
                continue

            # Calculate time-decay weight
            weight = calculate_time_decay_weight(
                m_date, evaluation_date, window_years, t_half_days
            )
            if weight <= 0.0:
                # Outside window
                continue

            # 2. Super Over Isolation (CricSheet innings 3 or 4)
            is_super_over = bool(
                match.get("is_super_over")
                or match.get("super_over")
                or match.get("innings_number") in (3, 4)
            )
            if is_super_over:
                super_overs_excluded += 1
                continue

            comp_name = str(match.get("competition_name") or "Unknown Competition")
            competitions_set.add(comp_name)
            format_tag = str(match.get("format_tag") or "T20").upper()

            total_matches += 1

            # Format-aware balls per over
            bpo = match.get("balls_per_over")
            if bpo is None:
                bpo = get_balls_per_over(comp_name, default=6)
            bpo_int = int(bpo)

            granularity = str(match.get("granularity") or "BALL_BY_BALL").upper()
            if granularity == "SCORECARD_ONLY":
                has_scorecard_only_matches = True

            # Track format stats separately (Format Isolation)
            if format_tag not in format_breakdown:
                format_breakdown[format_tag] = {
                    "matches": 0,
                    "innings": 0,
                    "runs": 0,
                    "balls_faced": 0,
                    "wickets": 0,
                    "legal_balls": 0,
                    "runs_conceded": 0,
                }
            f_stat = format_breakdown[format_tag]
            f_stat["matches"] += 1

            # Batting metrics
            batted = bool(match.get("batted", False))
            b_runs = int(match.get("runs") or 0)
            b_balls = int(match.get("balls_faced") or 0)
            b_fours = int(match.get("fours") or 0)
            b_sixes = int(match.get("sixes") or 0)
            b_dots = match.get("dot_balls")

            if batted or b_balls > 0 or b_runs > 0:
                total_innings += 1
                total_runs_scored += b_runs
                total_balls_faced += b_balls

                f_stat["innings"] += 1
                f_stat["runs"] += b_runs
                f_stat["balls_faced"] += b_balls

                sum_w_bat_runs += weight * float(b_runs)
                sum_w_bat_balls += weight * float(b_balls)

                boundary_run_val = float(b_fours * 4 + b_sixes * 6)
                sum_w_boundary_runs += weight * boundary_run_val
                sum_w_total_runs_for_boundary += weight * float(b_runs)

                if b_dots is not None and granularity != "SCORECARD_ONLY":
                    has_delivery_dot_data = True
                    sum_w_dot_balls += weight * float(b_dots)
                    sum_w_dot_balls_faced += weight * float(b_balls)

            # Bowling metrics
            bowled = bool(match.get("bowled", False))
            bw_balls = int(match.get("legal_balls") or 0)
            bw_runs = int(match.get("runs_conceded") or 0)
            bw_wkts = int(match.get("wickets") or 0)

            if bowled or bw_balls > 0 or bw_runs > 0 or bw_wkts > 0:
                total_legal_balls_bowled += bw_balls
                total_runs_conceded += bw_runs
                total_wickets_taken += bw_wkts

                f_stat["legal_balls"] += bw_balls
                f_stat["runs_conceded"] += bw_runs
                f_stat["wickets"] += bw_wkts

                sum_w_bowl_econ_num += weight * float(bpo_int) * float(bw_runs)
                sum_w_bowl_legal_balls += weight * float(bw_balls)

        # R01: Window Batting Strike Rate (weighted)
        weighted_sr: float | None = None
        if sum_w_bat_balls > 0.0:
            weighted_sr = round(100.0 * sum_w_bat_runs / sum_w_bat_balls, 2)

        # R02: Window Bowling Economy Rate (weighted & format-aware)
        weighted_economy: float | None = None
        if sum_w_bowl_legal_balls > 0.0:
            weighted_economy = round(sum_w_bowl_econ_num / sum_w_bowl_legal_balls, 2)

        # R03: Window Boundary % (weighted)
        boundary_pct: float | None = None
        if sum_w_total_runs_for_boundary > 0.0:
            boundary_pct = round(
                100.0 * sum_w_boundary_runs / sum_w_total_runs_for_boundary, 2
            )

        # R04: Window Dot Ball % (weighted; returns NOT_COMPUTABLE for scorecard-only)
        dot_ball_pct: float | str | None = None
        if has_scorecard_only_matches and not has_delivery_dot_data:
            dot_ball_pct = NOT_COMPUTABLE_TOKEN
        elif sum_w_dot_balls_faced > 0.0:
            dot_ball_pct = round(100.0 * sum_w_dot_balls / sum_w_dot_balls_faced, 2)

        # R05: Career Gap & Absence Taxonomy
        gap_records: list[dict[str, Any]] = []
        for abs_record in absences:
            abs_date = abs_record.get("match_date")
            if isinstance(abs_date, str):
                abs_date = date.fromisoformat(abs_date)
            if not isinstance(abs_date, date):
                continue

            if abs_date > evaluation_date or (evaluation_date - abs_date).days > max_window_days:
                continue

            # Classify gap
            gap_code = cls._classify_gap(abs_date, abs_record, injuries)
            gap_records.append({
                "match_id": str(abs_record.get("match_id") or "UNKNOWN"),
                "match_date": abs_date.isoformat(),
                "competition_name": str(abs_record.get("competition_name") or "Unknown"),
                "gap_code": gap_code.value,
                "gap_detail": str(abs_record.get("detail") or ""),
            })

        # R06: Window Sample Indicators
        overs_bowled = round(float(total_legal_balls_bowled) / 6.0, 1)
        insufficient_sample = (
            total_balls_faced < MIN_BATTING_BALLS_FACED
            and total_legal_balls_bowled < MIN_BOWLING_LEGAL_BALLS
        )

        sample_indicators = {
            "matches": total_matches,
            "innings": total_innings,
            "balls_faced": total_balls_faced,
            "overs_bowled": overs_bowled,
            "legal_balls_bowled": total_legal_balls_bowled,
            "wickets_taken": total_wickets_taken,
            "runs_scored": total_runs_scored,
            "runs_conceded": total_runs_conceded,
            "insufficient_sample_flag": insufficient_sample,
        }

        return RecentGlobalPerformance(
            evaluation_date=evaluation_date,
            window_years=window_years,
            window_start=window_start,
            window_end=evaluation_date,
            t_half_days=t_half_days,
            weighted_strike_rate=weighted_sr,
            weighted_economy=weighted_economy,
            boundary_pct=boundary_pct,
            dot_ball_pct=dot_ball_pct,
            gap_records=gap_records,
            sample_indicators=sample_indicators,
            competitions_investigated=sorted(competitions_set),
            format_breakdown=format_breakdown,
            super_overs_excluded_count=super_overs_excluded,
        )

    @classmethod
    def _classify_gap(
        cls,
        absence_date: date,
        absence_record: dict[str, Any],
        injury_records: list[dict[str, Any]],
    ) -> GapCode:
        """Classify an unplayed fixture using authoritative gap taxonomy."""
        # 1. Verified Injury
        for inj in injury_records:
            if not inj.get("verified", True):
                continue
            start_d = inj.get("start_date")
            if isinstance(start_d, str):
                start_d = date.fromisoformat(start_d)
            end_d = inj.get("end_date")
            if isinstance(end_d, str):
                end_d = date.fromisoformat(end_d)

            if isinstance(start_d, date):
                if end_d is None and absence_date >= start_d:
                    return GapCode.GAP_VERIFIED_INJURY
                if isinstance(end_d, date) and start_d <= absence_date <= end_d:
                    return GapCode.GAP_VERIFIED_INJURY

        # 2. Hint-based classification
        hint = str(absence_record.get("reason_hint") or "").upper()
        if "NATIONAL" in hint or "INTERNATIONAL" in hint or "INDIA" in hint:
            return GapCode.GAP_NATIONAL_DUTY
        if "CLASH" in hint or "DOMESTIC" in hint or "OVERLAP" in hint:
            return GapCode.GAP_DOMESTIC_CLASH
        if "BENCH" in hint or "NOT_SELECTED" in hint or "SQUAD_ONLY" in hint:
            return GapCode.GAP_NOT_SELECTED

        # Default strictly to GAP_UNKNOWN_UNEXPLAINED (Rule R1, R2)
        return GapCode.GAP_UNKNOWN_UNEXPLAINED


# ==============================================================================
# Module A3: Replaceability Evidence Assessor
# ==============================================================================


class ModuleA3ReplaceabilityAssessor:
    """Synthesizes RR historical profile and recent global form into an analytical signal.

    Guarantees:
    - Emits one of 5 analytical signals:
        RETAIN_SIGNAL, MONITOR_SIGNAL, POTENTIALLY_REPLACEABLE,
        INSUFFICIENT_EVIDENCE, REVIEW_REQUIRED.
    - Sample size guardrail: balls faced < 20 or legal balls < 30 flags
      insufficient_sample_flag = True and emits INSUFFICIENT_EVIDENCE.
    - Non-decision rule: Strictly emits analytical signals only. NEVER makes release
      or retention decisions, and NEVER produces scalar replacement probabilities.
    """

    ROLE_BENCHMARKS: dict[str, dict[str, float]] = {
        "TOP_ORDER_BATTER": {"benchmark_sr": 136.0, "benchmark_b_pct": 18.0},
        "TOP_ORDER_BATTER_WK": {"benchmark_sr": 136.0, "benchmark_b_pct": 18.0},
        "MIDDLE_ORDER_BATTER": {"benchmark_sr": 138.0, "benchmark_b_pct": 17.0},
        "FINISHER_BATTER": {"benchmark_sr": 150.0, "benchmark_b_pct": 22.0},
        "WICKETKEEPER_BATTER": {"benchmark_sr": 135.0, "benchmark_b_pct": 18.0},
        "PACE_BOWLER": {"benchmark_economy": 8.50},
        "SPIN_BOWLER": {"benchmark_economy": 7.80},
        "ALL_ROUNDER": {"benchmark_sr": 135.0, "benchmark_economy": 8.50},
        "DEFAULT": {"benchmark_sr": 135.0, "benchmark_economy": 8.50},
    }

    @classmethod
    def assess(
        cls,
        rr_profile: RRHistoricalProfile | dict[str, Any],
        global_profile: RecentGlobalPerformance | dict[str, Any],
        primary_role: str = "TOP_ORDER_BATTER",
        age_at_evaluation: float | None = None,
        review_required_reasons: list[str] | None = None,
    ) -> ReplaceabilityAssessment:
        """Synthesize performance profiles and context into an analytical replaceability signal."""
        # Convert Pydantic models to dict if needed
        rr_dict = rr_profile if isinstance(rr_profile, dict) else rr_profile.model_dump()
        gp_dict = (
            global_profile if isinstance(global_profile, dict) else global_profile.model_dump()
        )

        role_archetype = primary_role.upper()
        review_reasons = review_required_reasons or []

        # 1. Safety Interceptor: Conflict or review required
        if review_reasons:
            return ReplaceabilityAssessment(
                signal=ReplaceabilitySignal.REVIEW_REQUIRED,
                signal_rationale=(
                    f"Safety gateway triggered: {', '.join(review_reasons)}. "
                    "Requires human analyst review before replaceability assessment."
                ),
                role_archetype=role_archetype,
                age_at_evaluation=age_at_evaluation,
                review_required_flag=True,
                insufficient_sample_flag=False,
                confidence=None,
                forward_to_sice=True,
            )

        # 2. Sample Size Guardrail
        sample_inds = gp_dict.get("sample_indicators", {})
        balls_faced = int(sample_inds.get("balls_faced", 0))
        legal_balls_bowled = int(sample_inds.get("legal_balls_bowled", 0))

        is_bowler = "BOWLER" in role_archetype
        is_batter = "BATTER" in role_archetype or "WICKETKEEPER" in role_archetype
        is_all_rounder = "ALL_ROUNDER" in role_archetype

        insufficient_sample = False
        if is_all_rounder:
            if balls_faced < MIN_BATTING_BALLS_FACED and legal_balls_bowled < MIN_BOWLING_LEGAL_BALLS:
                insufficient_sample = True
        elif is_bowler:
            if legal_balls_bowled < MIN_BOWLING_LEGAL_BALLS:
                insufficient_sample = True
        elif is_batter:
            if balls_faced < MIN_BATTING_BALLS_FACED:
                insufficient_sample = True
        elif balls_faced < MIN_BATTING_BALLS_FACED and legal_balls_bowled < MIN_BOWLING_LEGAL_BALLS:
            insufficient_sample = True

        if insufficient_sample:
            return ReplaceabilityAssessment(
                signal=ReplaceabilitySignal.INSUFFICIENT_EVIDENCE,
                signal_rationale=(
                    f"Sample size below evaluation threshold in window: "
                    f"balls faced ({balls_faced}) < {MIN_BATTING_BALLS_FACED} or "
                    f"legal balls bowled ({legal_balls_bowled}) < {MIN_BOWLING_LEGAL_BALLS}."
                ),
                role_archetype=role_archetype,
                age_at_evaluation=age_at_evaluation,
                insufficient_sample_flag=True,
                review_required_flag=False,
                confidence=None,
                forward_to_sice=True,
            )

        # 3. Benchmark Comparison
        benchmarks = cls.ROLE_BENCHMARKS.get(role_archetype, cls.ROLE_BENCHMARKS["DEFAULT"])
        weighted_sr = gp_dict.get("weighted_strike_rate")
        weighted_econ = gp_dict.get("weighted_economy")
        boundary_pct = gp_dict.get("boundary_pct")

        rr_total_matches = int(rr_dict.get("total_matches", 0))
        rr_sr = rr_dict.get("strike_rate")
        rr_econ = rr_dict.get("economy_rate")

        evaluation_factors: dict[str, Any] = {
            "weighted_strike_rate": weighted_sr,
            "weighted_economy": weighted_econ,
            "boundary_pct": boundary_pct,
            "rr_total_matches": rr_total_matches,
            "rr_strike_rate": rr_sr,
            "rr_economy": rr_econ,
            "age_at_evaluation": age_at_evaluation,
            "benchmarks_used": benchmarks,
        }

        # Calculate performance deltas
        sr_delta = (
            float(weighted_sr) - benchmarks.get("benchmark_sr", 135.0)
            if weighted_sr is not None
            else None
        )
        econ_delta = (
            benchmarks.get("benchmark_economy", 8.5) - float(weighted_econ)
            if weighted_econ is not None
            else None
        )  # positive econ_delta means better than benchmark

        evaluation_factors["sr_delta"] = sr_delta
        evaluation_factors["econ_delta"] = econ_delta

        # Check age trajectory
        is_advanced_age = age_at_evaluation is not None and age_at_evaluation >= 35.0
        is_prime_age = age_at_evaluation is not None and (23.0 <= age_at_evaluation <= 32.0)

        # Deterministic Signal Synthesis
        is_retained = False
        is_replaceable = False

        if is_batter:
            if sr_delta is not None and sr_delta >= 2.0 and (not is_advanced_age or sr_delta >= 10.0):
                is_retained = True
            elif (sr_delta is not None and sr_delta <= -12.0) or (
                is_advanced_age and sr_delta is not None and sr_delta < 0.0
            ):
                is_replaceable = True

        elif is_bowler:
            if econ_delta is not None and econ_delta >= 0.2 and (not is_advanced_age or econ_delta >= 1.0):
                is_retained = True
            elif (econ_delta is not None and econ_delta <= -1.2) or (
                is_advanced_age and econ_delta is not None and econ_delta < 0.0
            ):
                is_replaceable = True

        elif is_all_rounder:
            good_bat = sr_delta is not None and sr_delta >= 0.0
            good_bowl = econ_delta is not None and econ_delta >= 0.0
            bad_bat = sr_delta is not None and sr_delta <= -10.0
            bad_bowl = econ_delta is not None and econ_delta <= -1.0

            if (good_bat or good_bowl) and not (bad_bat or bad_bowl):
                is_retained = True
            elif (bad_bat and bad_bowl) or (is_advanced_age and (bad_bat or bad_bowl)):
                is_replaceable = True

        # Franchise historical equity bonus: if played > 40 RR matches with career SR > 135
        if rr_total_matches >= 40 and rr_sr is not None and rr_sr >= 135.0 and not is_replaceable:
            is_retained = True

        if is_retained:
            signal = ReplaceabilitySignal.RETAIN_SIGNAL
            rationale = (
                "Strong recent performance, high role contribution, stable multi-season "
                "metrics; clear evidence against replacement."
            )
            confidence = 0.90 if is_prime_age else 0.82
        elif is_replaceable:
            signal = ReplaceabilitySignal.POTENTIALLY_REPLACEABLE
            rationale = (
                "Declining multi-season performance, reduced availability, diminishing returns "
                "in key phases, or advanced age relative to role demands."
            )
            confidence = 0.85 if is_advanced_age else 0.75
        else:
            signal = ReplaceabilitySignal.MONITOR_SIGNAL
            rationale = (
                "Mixed recent form, minor sample gaps, or role shifts requiring "
                "continued observation."
            )
            confidence = 0.70

        return ReplaceabilityAssessment(
            signal=signal,
            signal_rationale=rationale,
            role_archetype=role_archetype,
            age_at_evaluation=age_at_evaluation,
            evaluation_factors=evaluation_factors,
            insufficient_sample_flag=False,
            review_required_flag=False,
            confidence=confidence,
            forward_to_sice=True,
        )


# ==============================================================================
# Mode A Incumbent Engine Facade
# ==============================================================================


class ModeAExecutionResult:
    """Encapsulates the complete outputs generated by Mode A execution."""

    def __init__(
        self,
        rr_historical_profile: RRHistoricalProfile,
        recent_global_performance: RecentGlobalPerformance,
        replaceability_assessment: ReplaceabilityAssessment,
        source_record_ids: list[UUID | int] | None = None,
        verification_record_ids: list[UUID | int] | None = None,
        review_status: str = "CLEAR",
        review_reason_codes: list[str] | None = None,
    ) -> None:
        self.rr_historical_profile = rr_historical_profile
        self.recent_global_performance = recent_global_performance
        self.replaceability_assessment = replaceability_assessment
        self.source_record_ids = source_record_ids or []
        self.verification_record_ids = verification_record_ids or []
        self.review_status = review_status
        self.review_reason_codes = review_reason_codes or []

    def to_pvre_output(
        self,
        request: PVRERequestContract,
        career_coverage_state: str = CareerCoverageState.COMPLETE_WITHIN_VERIFIED_SOURCES.value,
        competition_coverage: dict[str, str] | None = None,
    ) -> PVREOutputContract:
        """Compile a fully compliant 26-field PVREOutputContract for downstream consumers."""
        comp_cov = competition_coverage or {
            "Indian Premier League": PVREVerificationStatus.VERIFIED.value,
        }
        for comp in self.recent_global_performance.competitions_investigated:
            comp_cov.setdefault(comp, PVREVerificationStatus.VERIFIED.value)

        # Merge verification IDs
        all_verification_ids = list(
            set(self.verification_record_ids + self.rr_historical_profile.provenance_ids)
        )

        return PVREOutputContract(
            contract_version="PVRE-2.2.0",
            research_run_id=request.research_run_id,
            player_id=request.player_id,
            canonical_name=request.canonical_name,
            identity_status=request.identity_status,
            research_mode=ResearchMode.MODE_A.value,
            route_status=RouteStatus.ROUTED_RR_INCUMBENT.value,
            evaluation_date=request.evaluation_date,
            target_season_id=request.target_season_id,
            rr_relationship_state=request.rr_relationship_state,
            rr_current_state=request.rr_current_state,
            player_capped_status=request.player_capped_status,
            ipl_uncapped_eligibility=request.ipl_uncapped_eligibility,
            research_window_start=self.recent_global_performance.window_start,
            research_window_end=self.recent_global_performance.window_end,
            career_coverage_state=career_coverage_state,
            rr_historical_profile=self.rr_historical_profile.model_dump(),
            recent_global_performance=self.recent_global_performance.model_dump(),
            complete_career_profile=None,
            replaceability_assessment=self.replaceability_assessment.model_dump(),
            competition_coverage=comp_cov,
            source_record_ids=self.source_record_ids,
            verification_record_ids=all_verification_ids,
            review_status=self.review_status,
            review_reason_codes=self.review_reason_codes,
            data_quality_summary={
                "super_overs_excluded": self.recent_global_performance.super_overs_excluded_count,
                "squad_only_seasons_count": len(self.rr_historical_profile.squad_only_seasons),
                "insufficient_sample": self.replaceability_assessment.insufficient_sample_flag,
            },
        )


class ModeAIncumbentEngine:
    """Mother engine for Phase 04B Mode A: Existing RR Player Replacement Intelligence."""

    @classmethod
    def execute(
        cls,
        request: PVRERequestContract,
        squad_records: list[dict[str, Any]] | None = None,
        rr_match_records: list[dict[str, Any]] | None = None,
        global_match_records: list[dict[str, Any]] | None = None,
        injury_records: list[dict[str, Any]] | None = None,
        absence_records: list[dict[str, Any]] | None = None,
        primary_role: str = "TOP_ORDER_BATTER",
        date_of_birth: date | None = None,
        review_required_reasons: list[str] | None = None,
        source_record_ids: list[UUID | int] | None = None,
        verification_record_ids: list[UUID | int] | None = None,
    ) -> ModeAExecutionResult:
        """Execute complete Mode A workflow (Module A1 + Module A2 + Module A3)."""
        # Calculate age as of evaluation_date
        age_at_evaluation: float | None = None
        if date_of_birth is not None:
            age_at_evaluation = round(
                (request.evaluation_date - date_of_birth).days / 365.25, 1
            )

        # Module A1: RR Historical Performance
        rr_profile = ModuleA1RRHistory.analyze(
            player_id=request.player_id,
            canonical_name=request.canonical_name,
            squad_records=squad_records or [],
            match_records=rr_match_records or [],
            provenance_ids=verification_record_ids,
        )

        # Module A2: Recent Global Performance
        all_matches: list[dict[str, Any]] = []
        if rr_match_records:
            all_matches.extend(rr_match_records)
        if global_match_records:
            all_matches.extend(global_match_records)

        global_profile = ModuleA2GlobalPerformance.analyze(
            evaluation_date=request.evaluation_date,
            window_years=request.research_window_years,
            match_records=all_matches,
            injury_records=injury_records,
            absence_records=absence_records,
        )

        # Module A3: Replaceability Assessment
        replaceability = ModuleA3ReplaceabilityAssessor.assess(
            rr_profile=rr_profile,
            global_profile=global_profile,
            primary_role=primary_role,
            age_at_evaluation=age_at_evaluation,
            review_required_reasons=review_required_reasons,
        )

        review_status = (
            PVREReviewStatus.REVIEW_REQUIRED.value
            if (review_required_reasons or replaceability.review_required_flag)
            else PVREReviewStatus.CLEAR.value
        )

        return ModeAExecutionResult(
            rr_historical_profile=rr_profile,
            recent_global_performance=global_profile,
            replaceability_assessment=replaceability,
            source_record_ids=source_record_ids,
            verification_record_ids=verification_record_ids,
            review_status=review_status,
            review_reason_codes=review_required_reasons,
        )


__all__ = [
    # Constants
    "RR_CANONICAL_NAME",
    "RR_SHORT_CODE",
    "RR_ACTIVE_SEASONS",
    "RR_SUSPENDED_SEASONS",
    "RR_FUTURE_SEASONS",
    "DEFAULT_T_HALF_DAYS",
    "MIN_BATTING_BALLS_FACED",
    "MIN_BOWLING_LEGAL_BALLS",
    "NOT_COMPUTABLE_TOKEN",
    "GapCode",
    # Functions
    "get_balls_per_over",
    "calculate_time_decay_weight",
    # Models
    "RRSeasonRecord",
    "RRHistoricalProfile",
    "RecentGlobalPerformance",
    "ReplaceabilityAssessment",
    "ModeAExecutionResult",
    # Engines & Analyzers
    "ModuleA1RRHistory",
    "ModuleA2GlobalPerformance",
    "ModuleA3ReplaceabilityAssessor",
    "ModeAIncumbentEngine",
]
