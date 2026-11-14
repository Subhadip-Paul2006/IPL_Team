"""Execute all seven validation gateway criteria across all 201 local JSON files for The Hundred.

Per Decision 2:
Execute all seven validation gateway criteria across the 201 local JSON files.
Promote derived rate metrics from DEFERRED to DERIVED only if every criterion passes
with complete reconciliation. Otherwise, retain DEFERRED status and document the failed criteria.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.ingestion.cricsheet_parser import CricSheetParser  # noqa: E402
from src.quality.reconciliation import DataQualityReconciliationService  # noqa: E402


def validate_the_hundred(dataset_dir: Path) -> dict[str, Any]:
    json_files = sorted(dataset_dir.glob("*.json"))
    total_files = len(json_files)

    parser = CricSheetParser()
    dq_service = DataQualityReconciliationService()

    results = {
        "total_files": total_files,
        "criteria": {
            "C1_schema_and_metadata": {"passed": True, "failures": []},
            "C2_runs_reconciliation": {"passed": True, "failures": []},
            "C3_extras_reconciliation": {"passed": True, "failures": []},
            "C4_wickets_reconciliation": {"passed": True, "failures": []},
            "C5_legal_balls_accounting": {"passed": True, "failures": []},
            "C6_phase_model_and_economy": {"passed": True, "failures": []},
            "C7_player_registry_and_spells": {"passed": True, "failures": []},
        },
        "metrics": {
            "total_matches": 0,
            "total_innings": 0,
            "total_deliveries": 0,
            "total_legal_balls": 0,
            "total_runs": 0,
            "total_extras": 0,
            "total_wickets": 0,
            "powerplay_balls": 0,
            "middle_balls": 0,
            "death_balls": 0,
            "bowlers_exceeding_max_balls": 0,
            "unresolved_players": 0,
            "dq_reconciled_matches": 0,
        },
    }

    if total_files != 201:
        results["criteria"]["C1_schema_and_metadata"]["passed"] = False
        results["criteria"]["C1_schema_and_metadata"]["failures"].append(
            f"Expected exactly 201 files, found {total_files}"
        )

    for jf in json_files:
        match_id = jf.stem
        try:
            with jf.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            results["criteria"]["C1_schema_and_metadata"]["passed"] = False
            results["criteria"]["C1_schema_and_metadata"]["failures"].append(
                f"{match_id}: JSON parse error: {e}"
            )
            continue

        results["metrics"]["total_matches"] += 1
        info = data.get("info", {})

        # Criterion 1: Schema and Metadata
        bpo = info.get("balls_per_over")
        overs = info.get("overs")
        if bpo != 5:
            results["criteria"]["C1_schema_and_metadata"]["passed"] = False
            results["criteria"]["C1_schema_and_metadata"]["failures"].append(
                f"{match_id}: balls_per_over={bpo}, expected 5"
            )
        if overs != 20:
            results["criteria"]["C1_schema_and_metadata"]["passed"] = False
            results["criteria"]["C1_schema_and_metadata"]["failures"].append(
                f"{match_id}: overs={overs}, expected 20"
            )

        # Parse through canonical CricSheetParser and run DataQualityReconciliationService
        try:
            parsed = parser.parse_json(data, external_id=match_id)
            dq_res = dq_service.reconcile_match(parsed.match, parsed.innings, parsed.deliveries)
            if dq_res["is_reconciled"]:
                results["metrics"]["dq_reconciled_matches"] += 1
            else:
                for det in dq_res.get("innings_details", []):
                    if not det.get("runs", {}).get("match", True):
                        results["criteria"]["C2_runs_reconciliation"]["passed"] = False
                        results["criteria"]["C2_runs_reconciliation"]["failures"].append(
                            f"{match_id} inn {det['innings_id']}: scorecard runs {det['runs']['innings_total']} != deliv sum {det['runs']['deliveries_sum']}"
                        )
                    if not det.get("extras", {}).get("match", True):
                        results["criteria"]["C3_extras_reconciliation"]["passed"] = False
                        results["criteria"]["C3_extras_reconciliation"]["failures"].append(
                            f"{match_id} inn {det['innings_id']}: scorecard extras {det['extras']['innings_total']} != deliv sum {det['extras']['deliveries_sum']}"
                        )
                    if not det.get("wickets", {}).get("match", True):
                        results["criteria"]["C4_wickets_reconciliation"]["passed"] = False
                        results["criteria"]["C4_wickets_reconciliation"]["failures"].append(
                            f"{match_id} inn {det['innings_id']}: scorecard wickets {det['wickets']['innings_total']} != deliv sum {det['wickets']['deliveries_sum']}"
                        )
                    if not det.get("legal_balls", {}).get("match", True):
                        results["criteria"]["C5_legal_balls_accounting"]["passed"] = False
                        results["criteria"]["C5_legal_balls_accounting"]["failures"].append(
                            f"{match_id} inn {det['innings_id']}: scorecard legal balls {det['legal_balls']['innings_total']} != deliv sum {det['legal_balls']['deliveries_sum']}"
                        )
        except Exception as e:
            results["criteria"]["C1_schema_and_metadata"]["passed"] = False
            results["criteria"]["C1_schema_and_metadata"]["failures"].append(
                f"{match_id}: Parser/DQ error: {e}"
            )

        # Verify Criterion 6: Phase boundaries on parsed delivery objects (zero T20 inheritance)
        for deliv_obj in parsed.deliveries:
            o_num = deliv_obj.over_number
            expected_phase = "Powerplay" if o_num < 5 else ("Middle" if o_num < 18 else "Death")
            if deliv_obj.match_phase != expected_phase:
                results["criteria"]["C6_phase_model_and_economy"]["passed"] = False
                results["criteria"]["C6_phase_model_and_economy"]["failures"].append(
                    f"{match_id} over {o_num}: delivery match_phase '{deliv_obj.match_phase}' != expected '{expected_phase}'"
                )

        people_registry = info.get("registry", {}).get("people", {})

        # Innings processing
        innings_list = data.get("innings", [])
        for inn_idx, inn_data in enumerate(innings_list, 1):
            results["metrics"]["total_innings"] += 1
            raw_overs = inn_data.get("overs", [])
            target = inn_data.get("target", {})
            is_super_over = bool(inn_data.get("super_over", False))

            deliv_runs_sum = 0
            deliv_extras_sum = 0
            deliv_wickets_sum = 0
            deliv_legal_balls_sum = 0

            extras_breakdown = {"wides": 0, "noballs": 0, "byes": 0, "legbyes": 0, "penalty": 0}
            bowler_balls: dict[str, int] = {}
            innings_ball_count = 0

            for over_dict in raw_overs:
                for deliv in over_dict.get("deliveries", []):
                    results["metrics"]["total_deliveries"] += 1
                    runs_dict = deliv.get("runs", {})
                    bat_runs = runs_dict.get("batter", 0)
                    ext_runs = runs_dict.get("extras", 0)
                    tot_runs = runs_dict.get("total", bat_runs + ext_runs)

                    # Criterion 2: Runs total invariant and non-negativity
                    if tot_runs != bat_runs + ext_runs:
                        results["criteria"]["C2_runs_reconciliation"]["passed"] = False
                        results["criteria"]["C2_runs_reconciliation"]["failures"].append(
                            f"{match_id} inn {inn_idx}: runs invariant {tot_runs} != {bat_runs} + {ext_runs}"
                        )
                    if bat_runs < 0 or ext_runs < 0 or tot_runs < 0:
                        results["criteria"]["C2_runs_reconciliation"]["passed"] = False
                        results["criteria"]["C2_runs_reconciliation"]["failures"].append(
                            f"{match_id} inn {inn_idx}: negative runs detected ({tot_runs})"
                        )

                    deliv_runs_sum += tot_runs
                    deliv_extras_sum += ext_runs

                    # Criterion 3: Extras breakdown reconciliation
                    extras_info = deliv.get("extras", {})
                    is_wide = "wides" in extras_info
                    is_noball = "noballs" in extras_info
                    extras_components_sum = 0
                    for ek, ev in extras_info.items():
                        if ev < 0:
                            results["criteria"]["C3_extras_reconciliation"]["passed"] = False
                            results["criteria"]["C3_extras_reconciliation"]["failures"].append(
                                f"{match_id} inn {inn_idx}: negative extras {ek}={ev}"
                            )
                        if ek in extras_breakdown:
                            extras_breakdown[ek] += ev
                            extras_components_sum += ev

                    if extras_info and extras_components_sum != ext_runs:
                        results["criteria"]["C3_extras_reconciliation"]["passed"] = False
                        results["criteria"]["C3_extras_reconciliation"]["failures"].append(
                            f"{match_id} inn {inn_idx}: extras breakdown {extras_components_sum} != {ext_runs}"
                        )

                    is_legal = not is_wide and not is_noball
                    if is_legal:
                        deliv_legal_balls_sum += 1
                        innings_ball_count += 1
                        bowler = deliv.get("bowler")
                        if bowler:
                            bowler_balls[bowler] = bowler_balls.get(bowler, 0) + 1

                        # Criterion 6: Phase boundaries (Powerplay 1-25, Middle 26-90, Death 91-100)
                        if innings_ball_count <= 25:
                            results["metrics"]["powerplay_balls"] += 1
                        elif innings_ball_count <= 90:
                            results["metrics"]["middle_balls"] += 1
                        else:
                            results["metrics"]["death_balls"] += 1

                    # Criterion 4: Wickets reconciliation
                    wickets = deliv.get("wickets", [])
                    for w in wickets:
                        w_kind = w.get("kind", "").strip().lower()
                        p_out = w.get("player_out")
                        if not p_out:
                            results["criteria"]["C4_wickets_reconciliation"]["passed"] = False
                            results["criteria"]["C4_wickets_reconciliation"]["failures"].append(
                                f"{match_id} inn {inn_idx}: wicket missing player_out"
                            )
                        if w_kind != "retired hurt":
                            deliv_wickets_sum += 1

                    # Criterion 7: Player Registry check
                    for role_key in ("batter", "bowler", "non_striker"):
                        p_name = deliv.get(role_key)
                        if p_name and p_name not in people_registry:
                            in_players = any(
                                p_name in plist for plist in info.get("players", {}).values()
                            )
                            if not in_players:
                                results["criteria"]["C7_player_registry_and_spells"]["passed"] = False
                                results["criteria"]["C7_player_registry_and_spells"]["failures"].append(
                                    f"{match_id}: Player '{p_name}' not found in registry or team player lists"
                                )
                                results["metrics"]["unresolved_players"] += 1

            results["metrics"]["total_runs"] += deliv_runs_sum
            results["metrics"]["total_extras"] += deliv_extras_sum
            results["metrics"]["total_wickets"] += deliv_wickets_sum
            results["metrics"]["total_legal_balls"] += deliv_legal_balls_sum

            # Criterion 5: In an uninterrupted match, legal balls <= 100
            if deliv_legal_balls_sum > 100 and not is_super_over:
                results["criteria"]["C5_legal_balls_accounting"]["passed"] = False
                results["criteria"]["C5_legal_balls_accounting"]["failures"].append(
                    f"{match_id} inn {inn_idx}: {deliv_legal_balls_sum} legal balls exceeds 100"
                )

            # Check bowler max balls (in uninterrupted match, max 20 legal balls per bowler per innings)
            is_shortened = (
                info.get("outcome", {}).get("method") in ("D/L", "DLS")
                or target.get("overs") is not None and target.get("overs") < 20
            )
            if not is_shortened and not is_super_over:
                for b_name, b_balls in bowler_balls.items():
                    if b_balls > 20:
                        results["criteria"]["C7_player_registry_and_spells"]["passed"] = False
                        results["criteria"]["C7_player_registry_and_spells"]["failures"].append(
                            f"{match_id} inn {inn_idx}: Bowler '{b_name}' bowled {b_balls} legal balls (> 20)"
                        )
                        results["metrics"]["bowlers_exceeding_max_balls"] += 1

    return results

    return results


if __name__ == "__main__":
    datasets_dir = Path("datasets/hnd_male_json")
    res = validate_the_hundred(datasets_dir)
    print("--- THE HUNDRED VALIDATION GATEWAY REPORT ---")
    print(f"Total Files Audited: {res['total_files']}")
    print(f"Total Matches: {res['metrics']['total_matches']}")
    print(f"Total Innings: {res['metrics']['total_innings']}")
    print(f"Total Deliveries: {res['metrics']['total_deliveries']}")
    print(f"Total Legal Balls: {res['metrics']['total_legal_balls']}")
    print(f"Total Runs: {res['metrics']['total_runs']}")
    print(f"Total Extras: {res['metrics']['total_extras']}")
    print(f"Total Wickets: {res['metrics']['total_wickets']}")
    print(f"Powerplay Balls (1-25): {res['metrics']['powerplay_balls']}")
    print(f"Middle Balls (26-90): {res['metrics']['middle_balls']}")
    print(f"Death Balls (91-100): {res['metrics']['death_balls']}")
    print()
    all_passed = True
    for c_name, c_res in res["criteria"].items():
        status = "PASSED" if c_res["passed"] else "FAILED"
        if not c_res["passed"]:
            all_passed = False
        print(f"[{status}] {c_name} (Failures: {len(c_res['failures'])})")
        if c_res["failures"]:
            for f in c_res["failures"][:5]:
                print(f"    - {f}")
            if len(c_res["failures"]) > 5:
                print(f"    ... and {len(c_res['failures']) - 5} more")

    print()
    print(f"OVERALL GATEWAY VERDICT: {'ALL CRITERIA PASSED' if all_passed else 'GATEWAY FAILED'}")
