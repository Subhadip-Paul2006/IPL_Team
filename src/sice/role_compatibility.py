"""Squad Intelligence & Composition Engine (SICE) — Role Compatibility Models.

Defines canonical cricketing role groups, functional role transition matrix,
handedness and bowling style modifiers, and hard boundary gating rules:
- Rule HB-1: Specialist Pace Bowler <-> Specialist Spin Bowler = 0.00 (Hard Bar)
- Rule HB-2: Non-Wicketkeeper <-> Designated Wicketkeeper = 0.00 (Defense Gate)
- Rule HB-3: Pure Batter <-> Pure Bowler = 0.00 (Discipline Segregation)

Governing Specifications:
- reports/phase6-execution/PHASE6_SICE_READINESS_REPORT.md §7.3
- docs/PRD.md §4.3 & §4.5
- docs/TRD.md §8.4
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum

from src.sice.exceptions import RoleCompatibilityError

logger = logging.getLogger(__name__)


class CanonicalRole(StrEnum):
    """Canonical 8-role taxonomy for squad intelligence and replacement evaluation."""

    TOP_ORDER_BATTER = "Top-order Batter"
    MIDDLE_ORDER_BATTER = "Middle-order Batter"
    FINISHER = "Finisher"
    BATTING_ALL_ROUNDER = "Batting All-rounder"
    BOWLING_ALL_ROUNDER = "Bowling All-rounder"
    PACE_BOWLER = "Pace Bowler"
    SPIN_BOWLER = "Spin Bowler"
    WICKETKEEPER_BATTER = "Wicketkeeper Batter"


class RoleTransitionCategory(StrEnum):
    """Qualitative feasibility category for role substitution."""

    DIRECT_MATCH = "DIRECT_MATCH"
    ADJACENT_ROLE = "ADJACENT_ROLE"
    TACTICALLY_VIABLE = "TACTICALLY_VIABLE"
    CROSS_ROLE_TRANSITION = "CROSS_ROLE_TRANSITION"
    INCOMPATIBLE = "INCOMPATIBLE"


@dataclass(frozen=True)
class RoleCompatibilityResult:
    """Detailed evaluation result of role compatibility between incumbent and candidate."""

    compatibility_score: float  # [0.0, 1.0]
    is_compatible: bool  # score >= min_threshold
    transition_category: RoleTransitionCategory
    hard_boundary_violated: bool
    boundary_reasons: list[str]
    incumbent_canonical_role: str
    candidate_canonical_role: str
    handedness_match: bool
    style_match: bool

    def __float__(self) -> float:
        return float(self.compatibility_score)


# -----------------------------------------------------------------------------
# Base Role Compatibility Matrix C(R_inc, R_cand)
# -----------------------------------------------------------------------------
BASE_ROLE_MATRIX: dict[tuple[str, str], float] = {
    # Top-order Batter incumbent
    (CanonicalRole.TOP_ORDER_BATTER, CanonicalRole.TOP_ORDER_BATTER): 1.00,
    (CanonicalRole.TOP_ORDER_BATTER, CanonicalRole.MIDDLE_ORDER_BATTER): 0.75,
    (CanonicalRole.TOP_ORDER_BATTER, CanonicalRole.FINISHER): 0.40,
    (CanonicalRole.TOP_ORDER_BATTER, CanonicalRole.BATTING_ALL_ROUNDER): 0.60,
    (CanonicalRole.TOP_ORDER_BATTER, CanonicalRole.BOWLING_ALL_ROUNDER): 0.45,
    (CanonicalRole.TOP_ORDER_BATTER, CanonicalRole.PACE_BOWLER): 0.00,
    (CanonicalRole.TOP_ORDER_BATTER, CanonicalRole.SPIN_BOWLER): 0.00,
    (CanonicalRole.TOP_ORDER_BATTER, CanonicalRole.WICKETKEEPER_BATTER): 0.65,
    # Middle-order Batter incumbent
    (CanonicalRole.MIDDLE_ORDER_BATTER, CanonicalRole.TOP_ORDER_BATTER): 0.70,
    (CanonicalRole.MIDDLE_ORDER_BATTER, CanonicalRole.MIDDLE_ORDER_BATTER): 1.00,
    (CanonicalRole.MIDDLE_ORDER_BATTER, CanonicalRole.FINISHER): 0.80,
    (CanonicalRole.MIDDLE_ORDER_BATTER, CanonicalRole.BATTING_ALL_ROUNDER): 0.70,
    (CanonicalRole.MIDDLE_ORDER_BATTER, CanonicalRole.BOWLING_ALL_ROUNDER): 0.60,
    (CanonicalRole.MIDDLE_ORDER_BATTER, CanonicalRole.PACE_BOWLER): 0.00,
    (CanonicalRole.MIDDLE_ORDER_BATTER, CanonicalRole.SPIN_BOWLER): 0.00,
    (CanonicalRole.MIDDLE_ORDER_BATTER, CanonicalRole.WICKETKEEPER_BATTER): 0.70,
    # Finisher incumbent
    (CanonicalRole.FINISHER, CanonicalRole.TOP_ORDER_BATTER): 0.35,
    (CanonicalRole.FINISHER, CanonicalRole.MIDDLE_ORDER_BATTER): 0.75,
    (CanonicalRole.FINISHER, CanonicalRole.FINISHER): 1.00,
    (CanonicalRole.FINISHER, CanonicalRole.BATTING_ALL_ROUNDER): 0.75,
    (CanonicalRole.FINISHER, CanonicalRole.BOWLING_ALL_ROUNDER): 0.70,
    (CanonicalRole.FINISHER, CanonicalRole.PACE_BOWLER): 0.00,
    (CanonicalRole.FINISHER, CanonicalRole.SPIN_BOWLER): 0.00,
    (CanonicalRole.FINISHER, CanonicalRole.WICKETKEEPER_BATTER): 0.60,
    # Batting All-rounder incumbent
    (CanonicalRole.BATTING_ALL_ROUNDER, CanonicalRole.TOP_ORDER_BATTER): 0.50,
    (CanonicalRole.BATTING_ALL_ROUNDER, CanonicalRole.MIDDLE_ORDER_BATTER): 0.70,
    (CanonicalRole.BATTING_ALL_ROUNDER, CanonicalRole.FINISHER): 0.75,
    (CanonicalRole.BATTING_ALL_ROUNDER, CanonicalRole.BATTING_ALL_ROUNDER): 1.00,
    (CanonicalRole.BATTING_ALL_ROUNDER, CanonicalRole.BOWLING_ALL_ROUNDER): 0.80,
    (CanonicalRole.BATTING_ALL_ROUNDER, CanonicalRole.PACE_BOWLER): 0.40,
    (CanonicalRole.BATTING_ALL_ROUNDER, CanonicalRole.SPIN_BOWLER): 0.40,
    (CanonicalRole.BATTING_ALL_ROUNDER, CanonicalRole.WICKETKEEPER_BATTER): 0.45,
    # Bowling All-rounder incumbent
    (CanonicalRole.BOWLING_ALL_ROUNDER, CanonicalRole.TOP_ORDER_BATTER): 0.35,
    (CanonicalRole.BOWLING_ALL_ROUNDER, CanonicalRole.MIDDLE_ORDER_BATTER): 0.55,
    (CanonicalRole.BOWLING_ALL_ROUNDER, CanonicalRole.FINISHER): 0.65,
    (CanonicalRole.BOWLING_ALL_ROUNDER, CanonicalRole.BATTING_ALL_ROUNDER): 0.80,
    (CanonicalRole.BOWLING_ALL_ROUNDER, CanonicalRole.BOWLING_ALL_ROUNDER): 1.00,
    (CanonicalRole.BOWLING_ALL_ROUNDER, CanonicalRole.PACE_BOWLER): 0.70,
    (CanonicalRole.BOWLING_ALL_ROUNDER, CanonicalRole.SPIN_BOWLER): 0.70,
    (CanonicalRole.BOWLING_ALL_ROUNDER, CanonicalRole.WICKETKEEPER_BATTER): 0.30,
    # Pace Bowler incumbent
    (CanonicalRole.PACE_BOWLER, CanonicalRole.TOP_ORDER_BATTER): 0.00,
    (CanonicalRole.PACE_BOWLER, CanonicalRole.MIDDLE_ORDER_BATTER): 0.00,
    (CanonicalRole.PACE_BOWLER, CanonicalRole.FINISHER): 0.00,
    (CanonicalRole.PACE_BOWLER, CanonicalRole.BATTING_ALL_ROUNDER): 0.35,
    (CanonicalRole.PACE_BOWLER, CanonicalRole.BOWLING_ALL_ROUNDER): 0.65,
    (CanonicalRole.PACE_BOWLER, CanonicalRole.PACE_BOWLER): 1.00,
    (CanonicalRole.PACE_BOWLER, CanonicalRole.SPIN_BOWLER): 0.00,
    (CanonicalRole.PACE_BOWLER, CanonicalRole.WICKETKEEPER_BATTER): 0.00,
    # Spin Bowler incumbent
    (CanonicalRole.SPIN_BOWLER, CanonicalRole.TOP_ORDER_BATTER): 0.00,
    (CanonicalRole.SPIN_BOWLER, CanonicalRole.MIDDLE_ORDER_BATTER): 0.00,
    (CanonicalRole.SPIN_BOWLER, CanonicalRole.FINISHER): 0.00,
    (CanonicalRole.SPIN_BOWLER, CanonicalRole.BATTING_ALL_ROUNDER): 0.35,
    (CanonicalRole.SPIN_BOWLER, CanonicalRole.BOWLING_ALL_ROUNDER): 0.65,
    (CanonicalRole.SPIN_BOWLER, CanonicalRole.PACE_BOWLER): 0.00,
    (CanonicalRole.SPIN_BOWLER, CanonicalRole.SPIN_BOWLER): 1.00,
    (CanonicalRole.SPIN_BOWLER, CanonicalRole.WICKETKEEPER_BATTER): 0.00,
    # Wicketkeeper Batter incumbent
    (CanonicalRole.WICKETKEEPER_BATTER, CanonicalRole.TOP_ORDER_BATTER): 0.00,
    (CanonicalRole.WICKETKEEPER_BATTER, CanonicalRole.MIDDLE_ORDER_BATTER): 0.00,
    (CanonicalRole.WICKETKEEPER_BATTER, CanonicalRole.FINISHER): 0.00,
    (CanonicalRole.WICKETKEEPER_BATTER, CanonicalRole.BATTING_ALL_ROUNDER): 0.00,
    (CanonicalRole.WICKETKEEPER_BATTER, CanonicalRole.BOWLING_ALL_ROUNDER): 0.00,
    (CanonicalRole.WICKETKEEPER_BATTER, CanonicalRole.PACE_BOWLER): 0.00,
    (CanonicalRole.WICKETKEEPER_BATTER, CanonicalRole.SPIN_BOWLER): 0.00,
    (CanonicalRole.WICKETKEEPER_BATTER, CanonicalRole.WICKETKEEPER_BATTER): 1.00,
}


def normalize_role(role_raw: str) -> CanonicalRole:
    """Normalize raw role string to one of the 8 CanonicalRole enum values.

    Args:
        role_raw: String role from dataset or API.

    Returns:
        CanonicalRole enum instance.

    Raises:
        RoleCompatibilityError: If role cannot be mapped.
    """
    if not isinstance(role_raw, str) or not role_raw.strip():
        raise RoleCompatibilityError(
            f"Invalid role string: {role_raw!r}",
            incumbent_role=str(role_raw) if role_raw else None,
        )

    r = role_raw.strip().lower()

    # Exact matches first
    for canonical in CanonicalRole:
        if r == canonical.value.lower():
            return canonical

    # Wicketkeeper
    if any(k in r for k in ["wicket", "keeper", "wk"]):
        return CanonicalRole.WICKETKEEPER_BATTER

    # Pace Bowler
    if any(k in r for k in ["pace", "fast", "seam"]):
        if "all-rounder" in r or "allrounder" in r or "all rounder" in r:
            return CanonicalRole.BOWLING_ALL_ROUNDER
        return CanonicalRole.PACE_BOWLER

    # Spin Bowler
    if any(k in r for k in ["spin", "slow", "orthodox", "break"]):
        if "all-rounder" in r or "allrounder" in r or "all rounder" in r:
            return CanonicalRole.BOWLING_ALL_ROUNDER
        return CanonicalRole.SPIN_BOWLER

    # All-Rounder
    if "all-rounder" in r or "allrounder" in r or "all rounder" in r:
        if "batting" in r:
            return CanonicalRole.BATTING_ALL_ROUNDER
        return CanonicalRole.BOWLING_ALL_ROUNDER

    # Batters
    if any(k in r for k in ["top", "open", "top-order", "top order"]):
        return CanonicalRole.TOP_ORDER_BATTER
    if any(k in r for k in ["finish", "lower-order", "lower order"]):
        return CanonicalRole.FINISHER
    if any(
        k in r for k in ["middle", "middle-order", "middle order", "anchor", "batter", "batsman"]
    ):
        return CanonicalRole.MIDDLE_ORDER_BATTER

    # Specialist Bowler fallback
    if r in ("bowler", "pure bowler", "specialist bowler"):
        return CanonicalRole.PACE_BOWLER

    raise RoleCompatibilityError(
        f"Unrecognized role string: {role_raw!r}",
        incumbent_role=role_raw,
    )


class RoleCompatibilityMatrix:
    """Container and interface for base role transition compatibility lookup."""

    def __init__(self, matrix: dict[tuple[str, str], float] | None = None) -> None:
        self._matrix = matrix or BASE_ROLE_MATRIX

    def get_base_compatibility(self, inc_role: CanonicalRole, cand_role: CanonicalRole) -> float:
        """Retrieve base transition score C(R_inc, R_cand)."""
        return self._matrix.get((inc_role, cand_role), 0.0)


class RoleCompatibilityEvaluator:
    """Evaluates role compatibility between incumbent and candidate players."""

    def __init__(self, matrix: RoleCompatibilityMatrix | None = None) -> None:
        self.matrix = matrix or RoleCompatibilityMatrix()

    def evaluate_compatibility(
        self,
        incumbent_role: str,
        candidate_role: str,
        incumbent_batting_hand: str | None = None,
        candidate_batting_hand: str | None = None,
        incumbent_bowling_style: str | None = None,
        candidate_bowling_style: str | None = None,
        incumbent_is_wk: bool = False,
        candidate_is_wk: bool = False,
        allow_non_wk_keeper_replacement: bool = False,
        min_compatibility_threshold: float = 0.50,
        strict_mode: bool = False,
    ) -> RoleCompatibilityResult:
        """Evaluate full role compatibility including hard boundaries and multipliers.

        Args:
            incumbent_role: Role of the incumbent player.
            candidate_role: Role of the candidate replacement.
            incumbent_batting_hand: E.g. "RIGHT", "LEFT".
            candidate_batting_hand: E.g. "RIGHT", "LEFT".
            incumbent_bowling_style: E.g. "Right-arm fast", "Left-arm orthodox".
            candidate_bowling_style: E.g. "Right-arm legbreak".
            incumbent_is_wk: Whether incumbent is designated wicketkeeper.
            candidate_is_wk: Whether candidate has wicketkeeping capability.
            allow_non_wk_keeper_replacement: Flag to bypass hard WK defense boundary.
            min_compatibility_threshold: Threshold above which candidate is deemed compatible.
            strict_mode: If True, raises RoleCompatibilityError on hard boundary violation.

        Returns:
            RoleCompatibilityResult with compatibility score and diagnostics.

        Raises:
            RoleCompatibilityError: If unrecognized role or hard boundary violated in strict_mode.
        """
        inc_canonical = normalize_role(incumbent_role)
        cand_canonical = normalize_role(candidate_role)

        hard_boundary_violated = False
        boundary_reasons: list[str] = []

        # Effective WK detection
        is_inc_wk = incumbent_is_wk or (inc_canonical == CanonicalRole.WICKETKEEPER_BATTER)
        is_cand_wk = candidate_is_wk or (cand_canonical == CanonicalRole.WICKETKEEPER_BATTER)

        # Rule HB-1: Specialist Pace Bowler <-> Specialist Spin Bowler = 0.00
        is_inc_pace = inc_canonical == CanonicalRole.PACE_BOWLER
        is_inc_spin = inc_canonical == CanonicalRole.SPIN_BOWLER
        is_cand_pace = cand_canonical == CanonicalRole.PACE_BOWLER
        is_cand_spin = cand_canonical == CanonicalRole.SPIN_BOWLER

        if (is_inc_pace and is_cand_spin) or (is_inc_spin and is_cand_pace):
            hard_boundary_violated = True
            boundary_reasons.append(
                "HB-1: Pace vs Spin cross-discipline replacement strictly forbidden"
            )

        # Rule HB-2: Non-Wicketkeeper <-> Designated Wicketkeeper = 0.00
        if is_inc_wk and not is_cand_wk and not allow_non_wk_keeper_replacement:
            hard_boundary_violated = True
            boundary_reasons.append(
                "HB-2: Non-wicketkeeper cannot replace designated wicketkeeper without explicit bypass"
            )

        # Rule HB-3: Pure Batter <-> Pure Bowler = 0.00
        is_inc_pure_batter = inc_canonical in (
            CanonicalRole.TOP_ORDER_BATTER,
            CanonicalRole.MIDDLE_ORDER_BATTER,
            CanonicalRole.FINISHER,
        )
        is_cand_pure_batter = cand_canonical in (
            CanonicalRole.TOP_ORDER_BATTER,
            CanonicalRole.MIDDLE_ORDER_BATTER,
            CanonicalRole.FINISHER,
        )
        is_inc_pure_bowler = inc_canonical in (CanonicalRole.PACE_BOWLER, CanonicalRole.SPIN_BOWLER)
        is_cand_pure_bowler = cand_canonical in (
            CanonicalRole.PACE_BOWLER,
            CanonicalRole.SPIN_BOWLER,
        )

        if (is_inc_pure_batter and is_cand_pure_bowler) or (
            is_inc_pure_bowler and is_cand_pure_batter
        ):
            hard_boundary_violated = True
            boundary_reasons.append("HB-3: Pure batter cannot replace pure bowler or vice versa")

        if hard_boundary_violated and strict_mode:
            raise RoleCompatibilityError(
                f"Role compatibility hard boundary violated: {'; '.join(boundary_reasons)}",
                incumbent_role=inc_canonical.value,
                candidate_role=cand_canonical.value,
                details={"reasons": boundary_reasons},
            )

        if hard_boundary_violated:
            return RoleCompatibilityResult(
                compatibility_score=0.00,
                is_compatible=False,
                transition_category=RoleTransitionCategory.INCOMPATIBLE,
                hard_boundary_violated=True,
                boundary_reasons=boundary_reasons,
                incumbent_canonical_role=inc_canonical.value,
                candidate_canonical_role=cand_canonical.value,
                handedness_match=False,
                style_match=False,
            )

        # Base score from matrix
        base_score = self.matrix.get_base_compatibility(inc_canonical, cand_canonical)

        # If incumbent is WK and non-WK replacement is bypassed, cap base at 0.50
        if is_inc_wk and not is_cand_wk and allow_non_wk_keeper_replacement:
            base_score = min(base_score, 0.50)

        # Multiplier 1: Batting Hand
        hand_match = True
        m_hand = 1.00
        if incumbent_batting_hand and candidate_batting_hand:
            h_inc = incumbent_batting_hand.strip().upper()
            h_cand = candidate_batting_hand.strip().upper()
            if h_inc != h_cand:
                hand_match = False
                # Bowlers don't get penalized heavily for batting hand
                if not (is_inc_pure_bowler and is_cand_pure_bowler):
                    m_hand = 0.95

        # Multiplier 2: Bowling Style
        style_match = True
        m_style = 1.00
        if incumbent_bowling_style and candidate_bowling_style:
            s_inc = incumbent_bowling_style.strip().lower()
            s_cand = candidate_bowling_style.strip().lower()
            if s_inc != s_cand:
                style_match = False
                # Check pace vs pace
                inc_is_p = any(k in s_inc for k in ["fast", "pace", "seam"])
                cand_is_p = any(k in s_cand for k in ["fast", "pace", "seam"])
                # Check spin vs spin
                inc_is_s = any(k in s_inc for k in ["spin", "orthodox", "break", "slow"])
                cand_is_s = any(k in s_cand for k in ["spin", "orthodox", "break", "slow"])

                if inc_is_p and cand_is_p:
                    m_style = 0.95  # Arm angle difference
                elif inc_is_s and cand_is_s:
                    # Leg-break vs Off-break / orthodox
                    is_inc_off = any(k in s_inc for k in ["off", "orthodox"])
                    is_cand_off = any(k in s_cand for k in ["off", "orthodox"])
                    is_inc_leg = "leg" in s_inc
                    is_cand_leg = "leg" in s_cand
                    if (is_inc_leg and is_cand_off) or (is_inc_off and is_cand_leg):
                        m_style = 0.90
                    else:
                        m_style = 0.85
                elif (inc_is_p and cand_is_s) or (inc_is_s and cand_is_p):
                    # Cross-discipline: all-rounder only, else 0
                    m_style = 0.00 if (is_inc_pure_bowler or is_cand_pure_bowler) else 0.50

        final_score = round(max(0.0, min(1.0, base_score * m_hand * m_style)), 4)

        # Transition category
        if final_score >= 0.95:
            cat = RoleTransitionCategory.DIRECT_MATCH
        elif final_score >= 0.70:
            cat = RoleTransitionCategory.ADJACENT_ROLE
        elif final_score >= 0.50:
            cat = RoleTransitionCategory.TACTICALLY_VIABLE
        elif final_score >= 0.30:
            cat = RoleTransitionCategory.CROSS_ROLE_TRANSITION
        else:
            cat = RoleTransitionCategory.INCOMPATIBLE

        return RoleCompatibilityResult(
            compatibility_score=final_score,
            is_compatible=(final_score >= min_compatibility_threshold),
            transition_category=cat,
            hard_boundary_violated=False,
            boundary_reasons=[],
            incumbent_canonical_role=inc_canonical.value,
            candidate_canonical_role=cand_canonical.value,
            handedness_match=hand_match,
            style_match=style_match,
        )


def evaluate_role_compatibility(
    incumbent_role: str,
    candidate_role: str,
    incumbent_batting_hand: str | None = None,
    candidate_batting_hand: str | None = None,
    incumbent_bowling_style: str | None = None,
    candidate_bowling_style: str | None = None,
    inc_is_wk: bool = False,
    cand_is_wk: bool = False,
    allow_non_wk_keeper_replacement: bool = False,
    min_compatibility_threshold: float = 0.50,
    strict_mode: bool = False,
) -> float:
    """Direct functional wrapper returning role compatibility score in [0.0, 1.0]."""
    evaluator = RoleCompatibilityEvaluator()
    res = evaluator.evaluate_compatibility(
        incumbent_role=incumbent_role,
        candidate_role=candidate_role,
        incumbent_batting_hand=incumbent_batting_hand,
        candidate_batting_hand=candidate_batting_hand,
        incumbent_bowling_style=incumbent_bowling_style,
        candidate_bowling_style=candidate_bowling_style,
        incumbent_is_wk=inc_is_wk,
        candidate_is_wk=cand_is_wk,
        allow_non_wk_keeper_replacement=allow_non_wk_keeper_replacement,
        min_compatibility_threshold=min_compatibility_threshold,
        strict_mode=strict_mode,
    )
    return res.compatibility_score
