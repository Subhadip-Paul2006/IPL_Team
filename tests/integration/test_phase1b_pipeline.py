"""Integration tests for the complete Phase 1B analytical pipeline."""

import csv
import json
import tempfile
from pathlib import Path

import pytest
from src.ingestion.organizer_loader import EXPECTED_SCHEMAS
from src.pipeline.run_phase1b import run_phase1b_pipeline


@pytest.fixture
def synthetic_phase1b_env():
    """Create a temporary sandbox environment with synthetic data files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        data_pack = root / "data_pack"
        out_dir = root / "output"
        rep_dir = root / "reports"
        data_pack.mkdir()
        out_dir.mkdir()
        rep_dir.mkdir()

        # Create 6 synthetic organizer CSVs
        for fname, cols in EXPECTED_SCHEMAS.items():
            fpath = data_pack / fname
            with open(fpath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(cols)

                if fname == "competitions.csv":
                    writer.writerow(["1358", "IPL 2022", "T20", "2022"])
                    writer.writerow(["1001", "T20I Series", "T20I", "2022"])
                elif fname == "teams.csv":
                    writer.writerow(["1358", "T1", "Team 1"])
                    writer.writerow(["1358", "T2", "Team 2"])
                elif fname == "matches.csv":
                    for i in range(1, 15):
                        writer.writerow([
                            f"M{i}", "1358", str(i), "2022-04-01", "League", "V1", "India",
                            "T1", "Team 1", "T2", "Team 2", "P1", "B1", "T1", "Batting",
                            "MOM1", "120", "120", "", "0", "T1", "Team 1 Won",
                        ])
                elif fname == "competition_team_player_mapping.csv":
                    writer.writerow(["1358", "IPL 2022", "T1", "Team 1", "P1", "Star Batter"])
                    writer.writerow(["1358", "IPL 2022", "T2", "Team 2", "B1", "Star Bowler"])
                elif fname == "playing_eleven.csv":
                    for i in range(1, 15):
                        writer.writerow([f"M{i}", "T1", "P1", "1", "true", "false", "false", "0", "0"])
                        writer.writerow([f"M{i}", "T2", "B1", "11", "true", "false", "false", "0", "0"])
                elif fname == "ball_by_ball.csv":
                    ball_id = 1
                    for i in range(1, 15):
                        # Add 15 balls per match for P1 batting vs B1 bowling
                        for b in range(1, 16):
                            writer.writerow([
                                f"M{i}", "2", "18", str(b), str(ball_id), "T1", "T2", "P1", "Star Batter",
                                "P2", "Non Striker", "B1", "Star Bowler", "RHB", "Pace",
                                "1", "4" if b % 3 == 0 else "1", "true" if b % 3 == 0 else "false",
                                "false", "false", "", "", "", "None", "6", "0", "Pace", "140.0",
                                "Drive", "Inswing", "Over", "Off-side", "2022-04-01 20:00:00",
                            ])
                            ball_id += 1

        yield data_pack, out_dir, rep_dir


def test_phase1b_pipeline_e2e_execution(synthetic_phase1b_env):
    """Verify end-to-end Phase 1B analytical pipeline execution."""
    data_pack, out_dir, rep_dir = synthetic_phase1b_env

    summary = run_phase1b_pipeline(
        data_pack_dir=data_pack,
        output_dir=out_dir,
        reports_dir=rep_dir,
        bootstrap_iterations=5,  # Fast bootstrap for unit test
        seed=42,
    )

    assert "elapsed_time" in summary
    assert "top10_batters" in summary
    assert "top10_bowlers" in summary
    assert "mpt_distribution" in summary

    # Verify generated files exist
    assert (out_dir / "top10_batters.csv").is_file()
    assert (out_dir / "top10_bowlers.csv").is_file()
    assert (out_dir / "top10_batters.json").is_file()
    assert (out_dir / "top10_bowlers.json").is_file()
    assert (out_dir / "reserve_candidates.csv").is_file()
    assert (out_dir / "reserve_candidates.json").is_file()
    assert (out_dir / "reproducibility_manifest.json").is_file()
    assert (out_dir / "data_quality_report.json").is_file()
    assert (rep_dir / "PHASE_1B_METHODOLOGY_AND_EVIDENCE_REPORT.md").is_file()

    # Check reproducibility manifest contents
    with open(out_dir / "reproducibility_manifest.json", encoding="utf-8") as f:
        manifest = json.load(f)
        assert manifest["pipeline_version"] == "v1.0.0-phase1b-canonical"
        assert "dataset_fingerprints" in manifest
