"""16 Macro Squad Balance Dimensions Evaluator & Squad Health Index (SHI).

Part of Phase 06 — SICE (Milestone 4: Squad Composition & 16-Dimension Balance).
Implements DIM-01 through DIM-16 and deterministic SHI computation adhering to
docs/TRD.md §8, reports/phase6-execution/PHASE6_SICE_READINESS_REPORT.md §6,
and ratified human decisions HD-05, HD-08, HD-09, and rules R1, R2, R13, R18.
"""

from __future__ import annotations

import logging
import math
import re
from datetime import date
from typing import Any
from uuid import UUID

from src.contracts.sice import (
    RosterStatus,
    SquadBalanceDimensions,
    UncertaintyFlag,
)
from src.contracts.team_builder import UserTeamPlayer

logger = logging.getLogger(__name__)

# Canonical Dimension weight vector wd (sum = 1.00)
DIMENSION_WEIGHTS: dict[str, float] = {
    "DIM-01": 0.10,  # Roster & Overseas Balance
    "DIM-02": 0.08,  # Role Distribution & Positional Balance
    "DIM-03": 0.09,  # Batting Depth Index (BDI)
    "DIM-04": 0.09,  # Bowling Depth & Over Cushion
    "DIM-05": 0.06,  # Pace vs Spin Balance
    "DIM-06": 0.08,  # Bowling Phase Specialisation
    "DIM-07": 0.06,  # Wicketkeeper Security (HD-08)
    "DIM-08": 0.06,  # All-Rounder Balance
    "DIM-09": 0.05,  # Batting Handedness Diversity
    "DIM-10": 0.05,  # Bowling Style Diversity
    "DIM-11": 0.05,  # Age & Squad Longevity
    "DIM-12": 0.06,  # Verified Uncapped Domestic Quota (Rule R13)
    "DIM-13": 0.05,  # Role Redundancy & Cannibalization
    "DIM-14": 0.05,  # Positional Coverage Continuity
    "DIM-15": 0.04,  # Tactical Versatility Index
    "DIM-16": 0.03,  # Evidentiary Completeness Health
}

# Bowling style canonical mapping
PACE_STYLE_PATTERNS = [
    r"fast",
    r"seam",
    r"pace",
    r"medium",
]
SPIN_STYLE_PATTERNS = [
    r"spin",
    r"break",
    r"orthodox",
    r"chinaman",
    r"googly",
    r"wrist",
]


def _is_overseas_player(
    player: UserTeamPlayer,
    meta: dict[str, Any],
) -> bool:
    """Determine whether player is classified as overseas based on metadata."""
    if "is_overseas" in meta:
        return bool(meta["is_overseas"])
    nationality = meta.get("nationality") or meta.get("country")
    if nationality is not None:
        nat_str = str(nationality).strip().lower()
        return nat_str not in {"india", "ind", "indian"}
    return False


def _is_wicketkeeper_player(
    player: UserTeamPlayer,
    meta: dict[str, Any],
) -> bool:
    """Determine whether player is a designated wicketkeeper."""
    if player.is_designated_wk:
        return True
    if meta.get("is_designated_wk") or meta.get("is_wicketkeeper"):
        return True
    role_str = (
        str(player.assigned_role or meta.get("role") or meta.get("primary_role") or "")
        .strip()
        .lower()
    )
    role_cleaned = re.sub(r"[\s\-_]+", "", role_str)
    return (
        "wicketkeeper" in role_cleaned or role_cleaned in {"wk", "keeper"} or "wk" in role_cleaned
    )


def _canonical_role(role_raw: str | None) -> str:
    """Map raw role string to one of the canonical role categories."""
    if not role_raw:
        return "Specialist"
    cleaned = role_raw.strip().lower()
    if "top" in cleaned or "opener" in cleaned or cleaned in {"bat", "batter"}:
        return "Top-order Batter"
    if "middle" in cleaned or "finisher" in cleaned:
        return "Middle-order Batter"
    if "wicket" in cleaned or "wk" in cleaned or "keeper" in cleaned:
        return "Wicketkeeper Batter"
    if "batting all" in cleaned or cleaned == "bar":
        return "Batting All-rounder"
    if (
        "bowling all" in cleaned
        or cleaned == "bwl_ar"
        or "all-rounder" in cleaned
        or cleaned == "ar"
    ):
        return "Bowling All-rounder"
    if any(p in cleaned for p in ["fast", "seam", "pace", "medium"]):
        return "Pace Bowler"
    if any(p in cleaned for p in ["spin", "break", "orthodox", "chinaman", "wrist"]):
        return "Spin Bowler"
    return "Specialist"


def _is_pace_style(style_str: str | None) -> bool:
    if not style_str:
        return False
    s = style_str.strip().lower()
    return any(re.search(p, s) for p in PACE_STYLE_PATTERNS)


def _is_spin_style(style_str: str | None) -> bool:
    if not style_str:
        return False
    s = style_str.strip().lower()
    return any(re.search(p, s) for p in SPIN_STYLE_PATTERNS)


def _calculate_player_ibc(
    sr: float | None,
    avg: float | None,
    bf: int | None,
) -> float | None:
    """Calculate Individual Batting Competency (IBC). Null if BF < 30."""
    if bf is not None and bf < 30:
        return None
    if sr is None or avg is None:
        return None
    ibc = (sr * min(avg, 45.0)) / 35.0
    return round(min(100.0, max(0.0, float(ibc))), 2)


def _calculate_player_oc(balls: int | None, apps: int | None) -> float:
    """Calculate Over Capacity (OC). Non-bowlers evaluate to 0.0."""
    if not balls or balls <= 0:
        return 0.0
    num_apps = max(1, apps or 1)
    return round(min(4.0, balls / (6.0 * num_apps)), 2)


class SquadBalanceEvaluator:
    """Evaluates assembled squads across all 16 Macro Squad Balance Dimensions."""

    def __init__(self, evaluation_date: date | None = None) -> None:
        self.evaluation_date = evaluation_date or date(2027, 3, 25)

    def evaluate_all_dimensions(
        self,
        players: list[UserTeamPlayer],
        player_metadata: dict[UUID, dict[str, Any]] | None = None,
        target_season: str = "IPL 2027",
    ) -> SquadBalanceDimensions:
        """Compute all 16 Squad Balance Dimensions and return SquadBalanceDimensions."""
        meta_dict = player_metadata or {}
        dim_scores: dict[str, float | None] = {}
        flags_emitted: list[str] = []

        # DIM-01: Roster & Overseas Balance
        s1, status, sq_size, os_count, os_ratio, dom_count, f1 = (
            self.calculate_dim01_roster_overseas(players, meta_dict)
        )
        dim_scores["DIM-01"] = s1
        flags_emitted.extend(f1)

        # DIM-02: Role Distribution & Role Entropy
        s2, entropy, role_counts, f2 = self.calculate_dim02_role_distribution(players, meta_dict)
        dim_scores["DIM-02"] = s2
        flags_emitted.extend(f2)

        # DIM-03: Batting Depth Index (BDI) & LORM
        s3, bdi, lorm, f3 = self.calculate_dim03_batting_depth(players, meta_dict)
        dim_scores["DIM-03"] = s3
        flags_emitted.extend(f3)

        # DIM-04: Bowling Depth & Over Cushion (SOC, FBO, SBO)
        s4, soc, fbo, sbo, f4 = self.calculate_dim04_bowling_depth(players, meta_dict)
        dim_scores["DIM-04"] = s4
        flags_emitted.extend(f4)

        # DIM-05: Pace vs Spin Balance (PSR)
        s5, pace_count, spin_count, psr, f5 = self.calculate_dim05_pace_spin(players, meta_dict)
        dim_scores["DIM-05"] = s5
        flags_emitted.extend(f5)

        # DIM-06: Bowling Phase Specialisation
        s6, phase_caps, f6 = self.calculate_dim06_bowling_phase(players, meta_dict)
        dim_scores["DIM-06"] = s6
        flags_emitted.extend(f6)

        # DIM-07: Wicketkeeper Security
        s7, wk_count, f7 = self.calculate_dim07_wicketkeeper_security(players, meta_dict)
        dim_scores["DIM-07"] = s7
        flags_emitted.extend(f7)

        # DIM-08: All-Rounder Balance
        s8, ar_count, f8 = self.calculate_dim08_all_rounder_balance(players, meta_dict)
        dim_scores["DIM-08"] = s8
        flags_emitted.extend(f8)

        # DIM-09: Batting Handedness Diversity
        s9, lhr_top7, f9 = self.calculate_dim09_handedness_diversity(players, meta_dict)
        dim_scores["DIM-09"] = s9
        flags_emitted.extend(f9)

        # DIM-10: Bowling Style Diversity
        s10, style_diversity, f10 = self.calculate_dim10_bowling_style_diversity(players, meta_dict)
        dim_scores["DIM-10"] = s10
        flags_emitted.extend(f10)

        # DIM-11: Age & Squad Longevity
        s11, mean_age, vfe, f11 = self.calculate_dim11_age_squad_longevity(players, meta_dict)
        dim_scores["DIM-11"] = s11
        flags_emitted.extend(f11)

        # DIM-12: Verified Uncapped Domestic Quota
        s12, uncapped_count, f12 = self.calculate_dim12_uncapped_quota(players, meta_dict)
        dim_scores["DIM-12"] = s12
        flags_emitted.extend(f12)

        # DIM-13: Role Redundancy & Cannibalization
        s13, cannibal_flags, f13 = self.calculate_dim13_role_redundancy(players, meta_dict)
        dim_scores["DIM-13"] = s13
        flags_emitted.extend(f13)

        # DIM-14: Positional Coverage Continuity
        s14, pos_deficit, f14 = self.calculate_dim14_positional_coverage(players, meta_dict)
        dim_scores["DIM-14"] = s14
        flags_emitted.extend(f14)

        # DIM-15: Tactical Versatility Index
        s15, versatility_score, f15 = self.calculate_dim15_tactical_versatility(players, meta_dict)
        dim_scores["DIM-15"] = s15
        flags_emitted.extend(f15)

        # DIM-16: Evidentiary Completeness Health
        s16, evidentiary_score, f16 = self.calculate_dim16_evidentiary_health(players, meta_dict)
        dim_scores["DIM-16"] = s16
        flags_emitted.extend(f16)

        return SquadBalanceDimensions(
            roster_capacity_status=status,
            squad_size=sq_size,
            overseas_count=os_count,
            overseas_ratio=os_ratio,
            domestic_count=dom_count,
            role_entropy=round(entropy, 4),
            batting_depth_index=round(bdi, 2) if bdi is not None else None,
            lower_order_resilience=round(lorm, 2) if lorm is not None else None,
            bowling_overs_capacity=round(soc, 2),
            frontline_bowlers_count=fbo,
            secondary_bowlers_count=sbo,
            pace_bowler_count=pace_count,
            spin_bowler_count=spin_count,
            pace_to_spin_ratio=round(psr, 2) if psr is not None else None,
            phase_coverage_status=phase_caps,
            wicketkeeper_count=wk_count,
            all_rounder_count=ar_count,
            left_hand_batting_ratio_top7=round(lhr_top7, 4),
            bowling_style_diversity_count=style_diversity,
            mean_squad_age=round(mean_age, 2) if mean_age is not None else None,
            verified_uncapped_count=uncapped_count,
            role_cannibalization_flags=cannibal_flags,
            positional_coverage_deficit=pos_deficit,
            tactical_versatility_score=round(versatility_score, 4),
            evidentiary_health_score=round(evidentiary_score, 4),
            dimension_scores=dim_scores,
        )

    def calculate_squad_health_index(
        self,
        dimension_scores: dict[str, float | None],
        squad_size: int,
    ) -> float | None:
        """Compute Squad Health Index (SHI) with Option B dynamic null reweighting.

        Suppresses SHI to None if squad_size < 18 (HD-09) or non-null computable dimensions < 12.
        """
        if squad_size < 18:
            return None

        # Filter computable non-null dimensions
        valid_scores = {
            dim: score
            for dim, score in dimension_scores.items()
            if score is not None and not math.isnan(score)
        }
        if len(valid_scores) < 12:
            return None

        # Option B dynamic proportional reweighting
        total_weight = sum(
            DIMENSION_WEIGHTS[dim] for dim in valid_scores if dim in DIMENSION_WEIGHTS
        )
        if total_weight <= 0.0:
            return None

        weighted_sum = sum(
            DIMENSION_WEIGHTS[dim] * valid_scores[dim]
            for dim in valid_scores
            if dim in DIMENSION_WEIGHTS
        )
        shi = weighted_sum / total_weight
        return round(max(0.0, min(100.0, float(shi))), 4)

    # -------------------------------------------------------------------------
    # Dimension Calculators
    # -------------------------------------------------------------------------

    def calculate_dim01_roster_overseas(
        self,
        players: list[UserTeamPlayer],
        meta: dict[UUID, dict[str, Any]],
    ) -> tuple[float, RosterStatus, int, int, float, int, list[str]]:
        """DIM-01: Roster & Overseas Balance."""
        flags: list[str] = []
        n = len(players)
        if n == 0:
            return 0.0, RosterStatus.ROSTER_INCOMPLETE, 0, 0, 0.0, 0, ["ROSTER_EMPTY"]

        os_count = 0
        unknown_nationality = False
        for p in players:
            m = meta.get(p.player_id, {})
            if "is_overseas" not in m and "nationality" not in m and "country" not in m:
                unknown_nationality = True
            if _is_overseas_player(p, m):
                os_count += 1

        if unknown_nationality:
            flags.append("UNKNOWN_NATIONALITY")
            flags.append("REVIEW_REQUIRED")

        dom_count = n - os_count
        os_ratio = os_count / n

        # Deductions
        penalties = 0.0
        if os_count > 8:
            penalties += 25.0 * (os_count - 8)
        if n < 18:
            penalties += 10.0 * (18 - n)
        elif n > 25:
            penalties += 20.0 * (n - 25)

        score = max(0.0, min(100.0, 100.0 - penalties))

        # Status
        if os_count > 8:
            status = RosterStatus.OVERSEAS_BREACH
            flags.append("OVERSEAS_BREACH")
        elif n < 18:
            status = RosterStatus.ROSTER_INCOMPLETE
            flags.append("ROSTER_INCOMPLETE")
        elif n > 25:
            status = RosterStatus.ROSTER_OVERSIZED
            flags.append("ROSTER_OVERSIZED")
        else:
            status = RosterStatus.ROSTER_VALID

        return score, status, n, os_count, os_ratio, dom_count, flags

    def calculate_dim02_role_distribution(
        self,
        players: list[UserTeamPlayer],
        meta: dict[UUID, dict[str, Any]],
    ) -> tuple[float, float, dict[str, int], list[str]]:
        """DIM-02: Role Distribution & Shannon Role Entropy."""
        flags: list[str] = []
        n = len(players)
        if n == 0:
            return 0.0, 0.0, {}, []

        role_counts: dict[str, int] = {
            "Top-order Batter": 0,
            "Middle-order Batter": 0,
            "Wicketkeeper Batter": 0,
            "Batting All-rounder": 0,
            "Bowling All-rounder": 0,
            "Pace Bowler": 0,
            "Spin Bowler": 0,
        }

        for p in players:
            m = meta.get(p.player_id, {})
            if _is_wicketkeeper_player(p, m):
                role_counts["Wicketkeeper Batter"] += 1
            else:
                raw_role = p.assigned_role or m.get("role") or m.get("primary_role")
                style = m.get("bowling_style")
                if not raw_role and style:
                    if _is_pace_style(style):
                        c_role = "Pace Bowler"
                    elif _is_spin_style(style):
                        c_role = "Spin Bowler"
                    else:
                        c_role = "Specialist"
                else:
                    c_role = _canonical_role(raw_role)

                if c_role in role_counts:
                    role_counts[c_role] += 1
                else:
                    role_counts["Middle-order Batter"] += 1

        k = len(role_counts)
        entropy = 0.0
        for count in role_counts.values():
            if count > 0:
                p_r = count / n
                entropy -= p_r * math.log(p_r)
        max_entropy = math.log(k)
        norm_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

        # Check for role vacuums in canonical sets
        for r_name in ["Pace Bowler", "Spin Bowler"]:
            if role_counts.get(r_name, 0) == 0:
                flags.append(f"ROLE_VACUUM_{r_name}")
                flags.append("ROLE_VACUUM")

        # Quota deviations
        dev = 0
        if role_counts["Top-order Batter"] < 3:
            dev += 3 - role_counts["Top-order Batter"]
        if role_counts["Middle-order Batter"] < 3:
            dev += 3 - role_counts["Middle-order Batter"]
        if role_counts["Wicketkeeper Batter"] < 2:
            dev += 2 - role_counts["Wicketkeeper Batter"]
        all_rounders = role_counts["Batting All-rounder"] + role_counts["Bowling All-rounder"]
        if all_rounders < 3:
            dev += 3 - all_rounders
        if role_counts["Pace Bowler"] < 4:
            dev += 4 - role_counts["Pace Bowler"]
        if role_counts["Spin Bowler"] < 2:
            dev += 2 - role_counts["Spin Bowler"]

        base_score = 100.0 * norm_entropy
        score = max(0.0, min(100.0, base_score - (5.0 * dev)))

        return score, norm_entropy, role_counts, flags

    def calculate_dim03_batting_depth(
        self,
        players: list[UserTeamPlayer],
        meta: dict[UUID, dict[str, Any]],
    ) -> tuple[float | None, float | None, float | None, list[str]]:
        """DIM-03: Batting Depth Index (BDI) and Lower-Order Resilience (LORM)."""
        flags: list[str] = []
        if not players:
            return None, None, None, []

        player_ibcs: list[tuple[UserTeamPlayer, float | None]] = []
        for p in players:
            m = meta.get(p.player_id, {})
            ibc_val: float | None
            if "ibc" in m and m["ibc"] is not None:
                ibc_val = float(m["ibc"])
            else:
                sr = m.get("batting_strike_rate") or m.get("strike_rate") or m.get("sr")
                avg = m.get("batting_average") or m.get("average") or m.get("avg")
                bf = m.get("career_balls_faced") or m.get("balls_faced") or m.get("bf")
                ibc_val = _calculate_player_ibc(sr, avg, bf)
            player_ibcs.append((p, ibc_val))

        # Check non-null count
        non_null_ibcs = [val for _, val in player_ibcs if val is not None]
        if len(non_null_ibcs) <= 4:
            flags.append("INSUFFICIENT_BATTING_DATA")
            return None, None, None, flags

        # Order players: honor explicit batting order 1..11 if present, else sort by IBC descending
        has_explicit = any(p.batting_order for p, _ in player_ibcs)
        if has_explicit:
            ordered = sorted(
                player_ibcs,
                key=lambda item: (
                    item[0].batting_order if item[0].batting_order is not None else 999,
                    -(item[1] if item[1] is not None else -1.0),
                ),
            )
        else:
            ordered = sorted(
                player_ibcs,
                key=lambda item: -(item[1] if item[1] is not None else -1.0),
            )

        top11 = ordered[:11]
        weights = [1.2, 1.2, 1.1, 1.1, 1.0, 1.0, 0.9, 0.8, 0.6, 0.4, 0.2]

        weighted_ibc_sum = 0.0
        w_sum = 0.0
        for idx, (_, val) in enumerate(top11):
            if val is not None:
                w = weights[idx] if idx < len(weights) else 0.1
                weighted_ibc_sum += w * val
                w_sum += w

        bdi_xi = (weighted_ibc_sum / w_sum) if w_sum > 0 else 0.0

        # LORM: positions 7, 8, 9 (indices 6, 7, 8)
        pos7_9 = [val for _, val in top11[6:9] if val is not None]
        lorm = (sum(pos7_9) / len(pos7_9)) if pos7_9 else None

        if lorm is not None and lorm < 25.0:
            flags.append("LONG_TAIL_VULNERABILITY")
        if bdi_xi < 50.0:
            flags.append("SHALLOW_BATTING_DEPTH")

        lorm_score = (lorm / 45.0 * 100.0) if lorm is not None else bdi_xi
        score = 0.70 * bdi_xi + 0.30 * min(100.0, lorm_score)
        score = max(0.0, min(100.0, score))

        return score, bdi_xi, lorm, flags

    def calculate_dim04_bowling_depth(
        self,
        players: list[UserTeamPlayer],
        meta: dict[UUID, dict[str, Any]],
    ) -> tuple[float, float, int, int, list[str]]:
        """DIM-04: Bowling Depth & Over Cushion (SOC, FBO, SBO)."""
        flags: list[str] = []
        if not players:
            return 0.0, 0.0, 0, 0, []

        soc = 0.0
        fbo = 0
        sbo = 0

        for p in players:
            m = meta.get(p.player_id, {})
            balls = m.get("career_balls_bowled") or m.get("balls_bowled") or m.get("balls")
            apps = m.get("matches") or m.get("apps") or m.get("appearances")
            econ = m.get("bowling_economy") or m.get("economy") or m.get("econ")
            oc = _calculate_player_oc(balls, apps)
            soc += oc

            # Frontline bowler check
            if oc >= 3.5 and (econ is not None and econ <= 9.2):
                fbo += 1
            elif oc >= 1.5 or (
                _canonical_role(p.assigned_role or m.get("role"))
                in {"Batting All-rounder", "Bowling All-rounder"}
                and oc >= 1.0
            ):
                sbo += 1

        if soc < 30.0:
            flags.append("BOWLING_CUSHION_DEFICIT")
            flags.append("INSUFFICIENT_BOWLING_COVER")

        s4 = 50.0 * min(1.0, fbo / 8.0) + 50.0 * min(1.0, soc / 42.0)
        score = max(0.0, min(100.0, s4))

        return score, soc, fbo, sbo, flags

    def calculate_dim05_pace_spin(
        self,
        players: list[UserTeamPlayer],
        meta: dict[UUID, dict[str, Any]],
    ) -> tuple[float | None, int, int, float | None, list[str]]:
        """DIM-05: Pace vs Spin Balance (PSR)."""
        flags: list[str] = []
        if not players:
            return 0.0, 0, 0, None, []

        pace_count = 0
        spin_count = 0
        unknown_style = False

        for p in players:
            m = meta.get(p.player_id, {})
            style = m.get("bowling_style")
            role = p.assigned_role or m.get("role") or m.get("primary_role") or ""
            balls = m.get("career_balls_bowled") or m.get("balls_bowled") or m.get("balls") or 0
            apps = m.get("matches") or m.get("apps") or 1
            oc = _calculate_player_oc(balls, apps)

            is_pace = _is_pace_style(style)
            is_spin = _is_spin_style(style)

            # Fallback to role only if style is not explicitly "None" and balls > 0
            if not is_pace and not is_spin and style != "None" and balls > 0:
                is_pace = _is_pace_style(role)
                is_spin = _is_spin_style(role)

            if not is_pace and not is_spin and not _is_wicketkeeper_player(p, m) and oc > 0:
                unknown_style = True

            if oc >= 1.0 or balls >= 60:
                if is_pace:
                    pace_count += 1
                elif is_spin:
                    spin_count += 1

        if unknown_style:
            flags.append("UNKNOWN_STYLE")

        if spin_count == 0:
            flags.append("ZERO_SPIN_ATTACK")
            psr = float(pace_count) if pace_count > 0 else 0.0
        else:
            psr = pace_count / spin_count

        if psr > 2.5:
            flags.append("SPIN_DEFICIT")
        elif psr < 0.8:
            flags.append("PACE_DEFICIT")

        if 1.25 <= psr <= 1.75:
            score = 100.0
        elif psr < 1.25:
            score = max(0.0, 100.0 - 50.0 * ((1.25 - psr) / 1.25))
        else:
            score = max(0.0, 100.0 - 50.0 * ((psr - 1.75) / 1.75))

        if pace_count == 0 and spin_count == 0:
            score = 0.0

        return max(0.0, min(100.0, score)), pace_count, spin_count, psr, flags

    def calculate_dim06_bowling_phase(
        self,
        players: list[UserTeamPlayer],
        meta: dict[UUID, dict[str, Any]],
    ) -> tuple[float, dict[str, float], list[str]]:
        """DIM-06: Bowling Phase Specialisation."""
        flags: list[str] = []
        if not players:
            return 0.0, {"powerplay": 0.0, "middle": 0.0, "death": 0.0}, []

        pp_cap = 0.0
        mid_cap = 0.0
        dth_cap = 0.0

        for p in players:
            m = meta.get(p.player_id, {})
            pb = m.get("phase_balls") or {}
            pe = m.get("phase_economy") or {}

            # Powerplay
            pp_balls = pb.get("powerplay") or pb.get("pp") or 0
            pp_econ = pe.get("powerplay") or pe.get("pp")
            if pp_balls >= 24 and pp_econ is not None and pp_econ <= 8.5:
                pp_cap += min(2.0, pp_balls / 60.0)

            # Middle
            mid_balls = pb.get("middle") or pb.get("mid") or 0
            mid_econ = pe.get("middle") or pe.get("mid")
            if mid_balls >= 24 and mid_econ is not None and mid_econ <= 8.2:
                mid_cap += min(3.0, mid_balls / 90.0)

            # Death
            dth_balls = pb.get("death") or pb.get("dth") or 0
            dth_econ = pe.get("death") or pe.get("dth")
            if dth_balls >= 24 and dth_econ is not None and dth_econ <= 10.2:
                dth_cap += min(2.0, dth_balls / 60.0)

        # Fallback if phase dictionaries not provided: infer from styles and overall economy
        if pp_cap == 0.0 and mid_cap == 0.0 and dth_cap == 0.0:
            for p in players:
                m = meta.get(p.player_id, {})
                style = m.get("bowling_style") or ""
                econ = m.get("bowling_economy") or m.get("economy") or m.get("econ")
                oc = _calculate_player_oc(m.get("career_balls_bowled"), m.get("matches"))
                if oc >= 2.0 and econ is not None:
                    if _is_pace_style(style):
                        pp_cap += 1.0 if econ <= 8.5 else 0.5
                        if econ <= 9.5:
                            dth_cap += 1.0
                    elif _is_spin_style(style):
                        mid_cap += 1.5 if econ <= 8.2 else 0.8

        phase_caps = {
            "powerplay": round(pp_cap, 2),
            "middle": round(mid_cap, 2),
            "death": round(dth_cap, 2),
        }

        if dth_cap < 1.0:
            flags.append("CRITICAL_DEATH_BOWLING_DEFICIT")
            flags.append("DEATH_OVERS_VULNERABILITY")
        if pp_cap < 2.0:
            flags.append("POWERPLAY_BOWLING_DEFICIT")

        s_pp = min(100.0, (pp_cap / 6.0) * 100.0)
        s_mid = min(100.0, (mid_cap / 9.0) * 100.0)
        s_dth = min(100.0, (dth_cap / 5.0) * 100.0)
        score = (s_pp + s_mid + s_dth) / 3.0

        return max(0.0, min(100.0, score)), phase_caps, flags

    def calculate_dim07_wicketkeeper_security(
        self,
        players: list[UserTeamPlayer],
        meta: dict[UUID, dict[str, Any]],
    ) -> tuple[float, int, list[str]]:
        """DIM-07: Wicketkeeper Security (HD-08: 2-3 target)."""
        flags: list[str] = []
        if not players:
            return 0.0, 0, ["CRITICAL_WK_SHORTAGE"]

        wk_players: list[UserTeamPlayer] = []
        for p in players:
            m = meta.get(p.player_id, {})
            if _is_wicketkeeper_player(p, m):
                wk_players.append(p)

        wk_count = len(wk_players)

        # Primary keeper batting standard
        pkq = 0.0
        for p in wk_players:
            m = meta.get(p.player_id, {})
            p_ibc = m.get("ibc")
            if p_ibc is not None:
                pkq = max(pkq, float(p_ibc))
            else:
                sr = m.get("batting_strike_rate") or m.get("strike_rate") or 135.0
                avg = m.get("batting_average") or m.get("average") or 30.0
                ibc_val = _calculate_player_ibc(sr, avg, 100)
                if ibc_val is not None:
                    pkq = max(pkq, ibc_val)

        if wk_count in [2, 3]:
            score = 70.0 + 30.0 * min(1.0, pkq / 60.0)
        elif wk_count == 1:
            flags.append("VULNERABILITY_NO_BACKUP_WK")
            score = 40.0 + 20.0 * min(1.0, pkq / 60.0)
        elif wk_count == 0:
            flags.append("CRITICAL_WK_SHORTAGE")
            score = 0.0
        else:  # wk_count > 3
            flags.append("SLOT_WASTE")
            score = max(20.0, 100.0 - 25.0 * (wk_count - 3))

        return max(0.0, min(100.0, score)), wk_count, flags

    def calculate_dim08_all_rounder_balance(
        self,
        players: list[UserTeamPlayer],
        meta: dict[UUID, dict[str, Any]],
    ) -> tuple[float, int, list[str]]:
        """DIM-08: All-Rounder Balance."""
        flags: list[str] = []
        if not players:
            return 0.0, 0, []

        ar_count = 0
        pace_ar = 0
        spin_ar = 0
        bar_count = 0
        bwl_ar_count = 0

        for p in players:
            m = meta.get(p.player_id, {})
            role = _canonical_role(p.assigned_role or m.get("role") or m.get("primary_role"))
            style = m.get("bowling_style") or ""
            is_ar = role in {"Batting All-rounder", "Bowling All-rounder"}
            if is_ar:
                ar_count += 1
                if role == "Batting All-rounder":
                    bar_count += 1
                else:
                    bwl_ar_count += 1

                if _is_pace_style(style):
                    pace_ar += 1
                elif _is_spin_style(style):
                    spin_ar += 1

        penalties = 0.0
        if pace_ar == 0:
            flags.append("NO_PACE_ALLROUNDER")
            penalties += 25.0
        if spin_ar == 0:
            flags.append("NO_SPIN_ALLROUNDER")
            penalties += 20.0
        if ar_count < 4:
            penalties += 15.0 * (4 - ar_count)
        elif ar_count > 6:
            penalties += 15.0 * (ar_count - 6)

        if ar_count < 3:
            flags.append("TACTICAL_RIGIDITY")

        score = max(0.0, min(100.0, 100.0 - penalties))
        return score, ar_count, flags

    def calculate_dim09_handedness_diversity(
        self,
        players: list[UserTeamPlayer],
        meta: dict[UUID, dict[str, Any]],
    ) -> tuple[float, float, list[str]]:
        """DIM-09: Batting Handedness Diversity (Top-7 LHR & Alternation)."""
        flags: list[str] = []
        if not players:
            return 0.0, 0.0, []

        # Sort top 7 by batting order if present, else order
        sorted_players = sorted(
            players,
            key=lambda p: (
                p.batting_order if p.batting_order is not None else 999,
                -(meta.get(p.player_id, {}).get("batting_strike_rate") or 0.0),
            ),
        )
        top7 = sorted_players[:7]
        hands: list[str] = []

        for p in top7:
            m = meta.get(p.player_id, {})
            h = m.get("batting_hand") or m.get("hand") or "Right-hand bat"
            if h is None:
                flags.append("UNKNOWN_HAND")
                h = "Right-hand bat"
            hands.append("Left" if "left" in str(h).lower() or str(h).upper() == "LHB" else "Right")

        lhb_count = sum(1 for h in hands if h == "Left")
        lhr_top7 = (lhb_count / len(hands)) if hands else 0.0

        if lhb_count == 0:
            flags.append("ONE_DIMENSIONAL_RHB_LINEUP")
        elif lhb_count >= 6:
            flags.append("EXCESSIVE_LHB_SKEW")

        # Pitch alternation index
        alternations = 0
        for i in range(len(hands) - 1):
            if hands[i] != hands[i + 1]:
                alternations += 1
        pai = (alternations / (len(hands) - 1)) if len(hands) > 1 else 0.0

        # Ratio score
        if 2 <= lhb_count <= 4:
            ratio_score = 1.0
        elif lhb_count in {1, 5}:
            ratio_score = 0.60
        else:
            ratio_score = 0.20

        score = 50.0 * ratio_score + 50.0 * min(1.0, pai / 0.50)
        return max(0.0, min(100.0, score)), lhr_top7, flags

    def calculate_dim10_bowling_style_diversity(
        self,
        players: list[UserTeamPlayer],
        meta: dict[UUID, dict[str, Any]],
    ) -> tuple[float, int, list[str]]:
        """DIM-10: Bowling Style Diversity (6 archetypes vector)."""
        flags: list[str] = []
        if not players:
            return 0.0, 0, []

        archetypes_present: set[str] = set()
        has_la_fast = False

        for p in players:
            m = meta.get(p.player_id, {})
            style = str(m.get("bowling_style") or "").strip().lower()
            if not style or style == "none":
                continue

            if "left" in style and ("fast" in style or "seam" in style or "medium" in style):
                archetypes_present.add("LA_FAST")
                has_la_fast = True
            elif "fast" in style or "seam" in style or "medium" in style:
                archetypes_present.add("RA_FAST")
            elif "off" in style or "off-break" in style:
                archetypes_present.add("RA_OFF")
            elif "leg" in style or "leg-break" in style:
                archetypes_present.add("RA_LEG")
            elif "slow left" in style or "orthodox" in style:
                archetypes_present.add("SLA_ORTHODOX")
            elif "chinaman" in style or "wrist" in style:
                archetypes_present.add("LA_WRIST")

        sds = len(archetypes_present)
        if sds < 3:
            flags.append("PREDICTABLE_BOWLING_ATTACK")
        if not has_la_fast:
            flags.append("NO_LEFT_ARM_SEAMER")
            flags.append("NO_LEFT_ARM_PACE")

        score = min(100.0, (sds / 5.0) * 80.0 + (20.0 if has_la_fast else 0.0))
        return max(0.0, min(100.0, score)), sds, flags

    def calculate_dim11_age_squad_longevity(
        self,
        players: list[UserTeamPlayer],
        meta: dict[UUID, dict[str, Any]],
    ) -> tuple[float | None, float | None, float, list[str]]:
        """DIM-11: Age & Squad Longevity (Mean age & Veteran Fatigue Exposure)."""
        flags: list[str] = []
        if not players:
            return 0.0, None, 0.0, []

        ages: list[float] = []
        vfe = 0.0

        for p in players:
            m = meta.get(p.player_id, {})
            age: float | None = None
            if "age" in m and m["age"] is not None:
                age = float(m["age"])
            elif "date_of_birth" in m and m["date_of_birth"] is not None:
                dob = m["date_of_birth"]
                if isinstance(dob, str):
                    try:
                        dob_date = date.fromisoformat(dob)
                        age = (self.evaluation_date - dob_date).days / 365.25
                    except ValueError:
                        age = None
                elif isinstance(dob, date):
                    age = (self.evaluation_date - dob).days / 365.25

            if age is not None:
                ages.append(age)
                if age >= 32.0:
                    balls = m.get("career_balls_bowled") or m.get("balls_bowled") or 0
                    apps = m.get("matches") or m.get("apps") or 1
                    vfe += _calculate_player_oc(balls, apps)
            else:
                flags.append("UNKNOWN_DOB")

        if not ages:
            return None, None, 0.0, flags

        mean_age = sum(ages) / len(ages)
        if mean_age > 29.5 or vfe > 16.0:
            flags.append("VETERAN_FATIGUE_EXPOSURE")

        vfe_penalty = 2.5 * max(0.0, vfe - 12.0)
        age_penalty = 15.0 * abs(mean_age - 26.5)
        score = max(0.0, 100.0 - age_penalty - vfe_penalty)

        return score, mean_age, vfe, flags

    def calculate_dim12_uncapped_quota(
        self,
        players: list[UserTeamPlayer],
        meta: dict[UUID, dict[str, Any]],
    ) -> tuple[float, int, list[str]]:
        """DIM-12: Verified Uncapped Domestic Quota (Rule R13)."""
        flags: list[str] = []
        if not players:
            return 0.0, 0, []

        uncapped_count = 0
        for p in players:
            m = meta.get(p.player_id, {})
            capped = str(m.get("capped_status") or "").strip().upper()
            elig = str(m.get("eligibility_status") or "").strip().upper()
            is_os = _is_overseas_player(p, m)

            # Rule R13: Absence from database or NOT_ASSESSED is never proof of uncapped status
            if capped == "UNCAPPED" and elig == "VERIFIED_ELIGIBLE" and not is_os:
                uncapped_count += 1

        if uncapped_count < 5:
            flags.append("REGULATORY_UNCAPPED_DEFICIT")

        score = min(100.0, (uncapped_count / 6.0) * 100.0)
        return max(0.0, min(100.0, score)), uncapped_count, flags

    def calculate_dim13_role_redundancy(
        self,
        players: list[UserTeamPlayer],
        meta: dict[UUID, dict[str, Any]],
    ) -> tuple[float, list[str], list[str]]:
        """DIM-13: Role Redundancy & Cannibalization."""
        cannibal_flags: list[str] = []
        flags: list[str] = []
        if not players:
            return 100.0, [], []

        anchors = 0
        non_batting_wk = 0
        off_spinners = 0

        for p in players:
            m = meta.get(p.player_id, {})
            sr = m.get("batting_strike_rate") or m.get("strike_rate")
            avg = m.get("batting_average") or m.get("average")
            style = str(m.get("bowling_style") or "").lower()

            if sr is not None and avg is not None and sr < 125.0 and avg >= 30.0:
                anchors += 1

            if _is_wicketkeeper_player(p, m):
                ibc = m.get("ibc")
                if ibc is not None and ibc < 40.0:
                    non_batting_wk += 1

            if "off" in style or "off-break" in style:
                off_spinners += 1

        tcp = 0
        if anchors > 2:
            tcp += anchors - 2
            cannibal_flags.append(f"EXCESS_ANCHORS_{anchors}")
        if non_batting_wk > 1:
            tcp += non_batting_wk - 1
            cannibal_flags.append(f"EXCESS_NON_BATTING_WK_{non_batting_wk}")
        if off_spinners > 2:
            tcp += off_spinners - 2
            cannibal_flags.append(f"DUPLICATE_OFF_SPINNERS_{off_spinners}")

        if tcp > 0:
            flags.append("ROSTER_SLOT_CANNIBALIZATION")

        score = max(0.0, 100.0 - (20.0 * tcp))
        return score, cannibal_flags, flags

    def calculate_dim14_positional_coverage(
        self,
        players: list[UserTeamPlayer],
        meta: dict[UUID, dict[str, Any]],
    ) -> tuple[float, int, list[str]]:
        """DIM-14: Positional Coverage Continuity (ECC & PCD)."""
        flags: list[str] = []
        if not players:
            return 0.0, 14, ["POSITIONAL_DEPTH_SHORTAGE"]

        ecc: dict[int, int] = dict.fromkeys(range(1, 8), 0)

        for p in players:
            m = meta.get(p.player_id, {})
            pos_inn = m.get("position_innings") or {}
            for pos in range(1, 8):
                if pos_inn.get(pos, 0) >= 3 or pos_inn.get(str(pos), 0) >= 3:
                    ecc[pos] += 1

        # Fallback if position_innings not provided: map canonical roles to positions
        if sum(ecc.values()) == 0:
            for p in players:
                m = meta.get(p.player_id, {})
                c_role = _canonical_role(p.assigned_role or m.get("role") or m.get("primary_role"))
                if c_role == "Top-order Batter":
                    ecc[1] += 1
                    ecc[2] += 1
                    ecc[3] += 1
                elif c_role in {"Middle-order Batter", "Wicketkeeper Batter"}:
                    ecc[4] += 1
                    ecc[5] += 1
                    ecc[6] += 1
                elif c_role in {"Batting All-rounder", "Bowling All-rounder"}:
                    ecc[6] += 1
                    ecc[7] += 1

        pcd = 0
        for pos in range(1, 8):
            if ecc[pos] == 0:
                flags.append(f"CRITICAL_POSITIONAL_VACUUM_{pos}")
                flags.append("CRITICAL_POSITIONAL_VACUUM")
            if ecc[pos] < 2:
                pcd += 2 - ecc[pos]

        if pcd > 0:
            flags.append("POSITIONAL_DEPTH_SHORTAGE")

        score = max(0.0, 100.0 - (15.0 * pcd))
        return score, pcd, flags

    def calculate_dim15_tactical_versatility(
        self,
        players: list[UserTeamPlayer],
        meta: dict[UUID, dict[str, Any]],
    ) -> tuple[float, float, list[str]]:
        """DIM-15: Tactical Versatility Index (4 match conditions)."""
        flags: list[str] = []
        if not players:
            return 0.0, 0.0, []

        # Scenario 1: Seaming Deck (>= 4 pace options with PP Econ <= 8.2 or good pace depth)
        pace_options = 0
        spin_options = 0
        high_sr_batters = 0
        tight_bowlers = 0

        for p in players:
            m = meta.get(p.player_id, {})
            style = m.get("bowling_style") or ""
            econ = m.get("bowling_economy") or m.get("economy") or 8.0
            sr = m.get("batting_strike_rate") or m.get("strike_rate") or 120.0
            balls = m.get("career_balls_bowled") or m.get("balls_bowled") or 0

            if _is_pace_style(style) and balls >= 60:
                pace_options += 1
            if _is_spin_style(style) and balls >= 60:
                spin_options += 1
            if sr >= 150.0:
                high_sr_batters += 1
            if econ <= 7.8 and balls >= 60:
                tight_bowlers += 1

        s1 = 1 if pace_options >= 4 else 0
        s2 = 1 if spin_options >= 3 else 0
        s3 = 1 if high_sr_batters >= 2 else 0
        s4 = 1 if tight_bowlers >= 2 else 0

        vi = (s1 + s2 + s3 + s4) / 4.0
        if vi < 0.50:
            flags.append("TACTICAL_FRAGILITY")

        score = vi * 100.0
        return score, vi, flags

    def calculate_dim16_evidentiary_health(
        self,
        players: list[UserTeamPlayer],
        meta: dict[UUID, dict[str, Any]],
    ) -> tuple[float, float, list[str]]:
        """DIM-16: Evidentiary Completeness Health (SEHS)."""
        flags: list[str] = []
        if not players:
            return 0.0, 0.0, []

        scores: list[float] = []
        for p in players:
            m = meta.get(p.player_id, {})
            id_status = str(m.get("identity_status") or "").upper()
            flag = m.get("uncertainty_flag")

            if id_status in {"RESOLVED", "VERIFIED"} or flag in {
                UncertaintyFlag.VERIFIED,
                "VERIFIED",
            }:
                scores.append(1.0)
            elif id_status == "PROVISIONAL" or flag in {
                UncertaintyFlag.PROVISIONAL,
                "PROVISIONAL",
            }:
                scores.append(0.5)
            else:
                scores.append(0.0)

        sehs = sum(scores) / len(scores)
        if sehs < 0.75:
            flags.append("PROVISIONAL_SQUAD_INTELLIGENCE")

        score = sehs * 100.0
        return score, sehs, flags


# Convenience Alias
BalanceEvaluator = SquadBalanceEvaluator
