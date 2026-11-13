"""CMIE Match Context & CDPI Pressure Engine (Phase 1B - Workstream D).

Calculates strictly pre-delivery chronological match-state features, prevents
outcome leakage (Rule R11), isolates Super Overs (Rule R6 / P4), applies DLS revised
targets and overs (Rule R7), and computes the Continuous Delivery Pressure Index (CDPI)
and categorical Match Pressure Tier (MPT).
"""

from dataclasses import dataclass
from typing import Any

from src.ingestion.normalizer import (
    is_legal_ball,
    is_valid_wicket,
    parse_revised_balls,
    parse_runs_breakdown,
)


@dataclass
class PreDeliveryState:
    """Snapshot of match context strictly prior to the delivery being bowled."""

    match_id: str
    innings: int
    overid: int
    over_ball_num: int
    innings_ball_num: int
    striker_id: str
    bowler_id: str
    legal_balls_bowled: int
    legal_balls_remaining: int
    current_runs: float
    current_wickets: int
    wickets_in_hand: int
    crr: float
    target_runs: int | None = None
    runs_required: int | None = None
    rrr: float | None = None
    cdpi: float = 0.0
    mpt: str = "LOW"  # LOW, MEDIUM, HIGH, EXTREME, SUPER_OVER
    is_pressure: bool = False  # True if MPT in (HIGH, EXTREME)


class MatchContextEngine:
    """Orchestrates chronological state reconstruction and CDPI calculation."""

    def __init__(
        self,
        chase_weights: dict[str, float] | None = None,
        first_inn_weights: dict[str, float] | None = None,
        bye_legbye_run_value: float = 1.0,
    ) -> None:
        self.w_c = chase_weights or {"base": 0.15, "rrr": 0.45, "w": 0.25, "stage": 0.20}
        self.w_1 = first_inn_weights or {"base": 0.20, "stage": 0.45, "wicket": 0.35, "rate": 0.20}
        self.bye_legbye_run_value = bye_legbye_run_value

    def compute_innings_1_totals(
        self,
        deliveries_by_match: dict[str, dict[int, list[dict[str, Any]]]],
    ) -> dict[str, int]:
        """Compute total 1st innings runs for every match to establish default chase targets."""
        totals: dict[str, int] = {}
        for mid, inns in deliveries_by_match.items():
            if 1 in inns:
                tot = 0.0
                for d in inns[1]:
                    _, _, team_runs = parse_runs_breakdown(d, self.bye_legbye_run_value)
                    tot += team_runs
                totals[mid] = int(round(tot))
        return totals

    def process_match_deliveries(
        self,
        match_info: dict[str, Any],
        inns_deliveries: dict[int, list[dict[str, Any]]],
        inn1_total: int | None = None,
    ) -> list[PreDeliveryState]:
        """Process all deliveries for a match, producing chronological pre-delivery states."""
        mid = str(match_info.get("match_id", "")).strip()
        r1_balls = parse_revised_balls(match_info.get("first_inn_revised_overs")) or 120
        r2_balls = parse_revised_balls(match_info.get("second_inn_revised_overs")) or 120
        rev_target_str = str(match_info.get("revised_target", "")).strip()

        target_runs: int | None = None
        if rev_target_str:
            try:
                target_runs = int(rev_target_str)
            except ValueError:
                target_runs = None
        elif match_info.get("second_inn_revised_overs"):
            # Rule R4 Invariant 14: DLS match with missing revised target must exclude chase from target-dependent pressure
            target_runs = None
        elif inn1_total is not None:
            target_runs = inn1_total + 1

        all_states: list[PreDeliveryState] = []

        for inn_num in sorted(inns_deliveries.keys()):
            balls = inns_deliveries[inn_num]
            if inn_num > 2:
                # Super Over: strict isolation from ordinary baselines
                for d in balls:
                    state = PreDeliveryState(
                        match_id=mid,
                        innings=inn_num,
                        overid=int(d.get("overid", 1)),
                        over_ball_num=int(d.get("over_ball_num", 1)),
                        innings_ball_num=int(d.get("innings_ball_num", 1)),
                        striker_id=str(d.get("striker_id", "")).strip(),
                        bowler_id=str(d.get("bowler_id", "")).strip(),
                        legal_balls_bowled=0,
                        legal_balls_remaining=6,
                        current_runs=0.0,
                        current_wickets=0,
                        wickets_in_hand=2,
                        crr=0.0,
                        cdpi=1.0,
                        mpt="SUPER_OVER",
                        is_pressure=False,  # Quarantined, does not contaminate main baselines
                    )
                    all_states.append(state)
                continue

            max_balls = r1_balls if inn_num == 1 else r2_balls
            cur_runs = 0.0
            cur_wickets = 0
            cur_legal = 0

            for d in balls:
                et = str(d.get("extras_type", "None")).strip().lower()
                is_legal = is_legal_ball(et)
                s_id = str(d.get("striker_id", "")).strip()
                b_id = str(d.get("bowler_id", "")).strip()
                rem_balls = max(0, max_balls - cur_legal)
                w_in_hand = max(0, 10 - cur_wickets)
                crr = (cur_runs / max(1, cur_legal)) * 6.0 if cur_legal >= 12 else 8.0

                runs_req: int | None = None
                rrr: float | None = None

                if inn_num == 1:
                    # First Innings CDPI Model
                    stage = cur_legal / max(1, max_balls)
                    w_deficit = max(0.0, float(cur_wickets) - (stage * 5.0)) / 6.0
                    rate_press = max(0.0, (8.5 - crr) / 4.0) if crr < 8.5 else 0.0
                    cdpi = (
                        self.w_1["base"]
                        + self.w_1["stage"] * stage
                        + self.w_1["wicket"] * w_deficit
                        + self.w_1["rate"] * rate_press
                    )
                else:
                    # Chase (Innings 2) CDPI Model
                    if target_runs is None:
                        # Missing revised target under DLS: exclude chase from target pressure
                        cdpi = 0.50
                    else:
                        runs_req = max(0, target_runs - int(round(cur_runs)))
                        if runs_req == 0:
                            cdpi = 0.0
                            rrr = 0.0
                        else:
                            rrr = (runs_req / max(1, rem_balls)) * 6.0 if rem_balls > 0 else 36.0
                            stage = 1.0 - (rem_balls / max(1, max_balls))
                            rrr_factor = max(0.0, min(1.0, (rrr - 5.0) / 10.0))
                            w_factor = float(10 - w_in_hand) / 8.0
                            cdpi = (
                                self.w_c["base"]
                                + self.w_c["rrr"] * rrr_factor
                                + self.w_c["w"] * w_factor
                                + self.w_c["stage"] * stage
                            )
                            if rrr >= 12.0:
                                cdpi = max(cdpi, 0.65)
                            if rrr >= 15.0:
                                cdpi = max(cdpi, 0.82)

                cdpi = max(0.0, min(1.0, cdpi))

                # Categorical MPT classification
                if cdpi < 0.40:
                    mpt = "LOW"
                elif cdpi < 0.60:
                    mpt = "MEDIUM"
                elif cdpi < 0.80:
                    mpt = "HIGH"
                else:
                    mpt = "EXTREME"

                is_press = mpt in ("HIGH", "EXTREME")

                state = PreDeliveryState(
                    match_id=mid,
                    innings=inn_num,
                    overid=int(d.get("overid", 1)),
                    over_ball_num=int(d.get("over_ball_num", 1)),
                    innings_ball_num=int(d.get("innings_ball_num", 1)),
                    striker_id=s_id,
                    bowler_id=b_id,
                    legal_balls_bowled=cur_legal,
                    legal_balls_remaining=rem_balls,
                    current_runs=round(cur_runs, 2),
                    current_wickets=cur_wickets,
                    wickets_in_hand=w_in_hand,
                    crr=round(crr, 2),
                    target_runs=target_runs if inn_num == 2 else None,
                    runs_required=runs_req,
                    rrr=round(rrr, 2) if rrr is not None else None,
                    cdpi=round(cdpi, 4),
                    mpt=mpt,
                    is_pressure=is_press,
                )
                all_states.append(state)

                # Post-delivery state progression
                _, _, team_runs = parse_runs_breakdown(d, self.bye_legbye_run_value)
                cur_runs += team_runs

                if is_valid_wicket(d):
                    cur_wickets = min(10, cur_wickets + 1)

                if is_legal:
                    cur_legal += 1

        return all_states
