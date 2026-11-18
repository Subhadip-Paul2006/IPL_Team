"""Unit tests for organizer data loader and integrity auditing (Workstream A)."""

import csv
import tempfile
from pathlib import Path

import pytest
from src.ingestion.organizer_loader import (
    EXPECTED_SCHEMAS,
    OrganizerDataLoader,
    compute_file_sha256,
)


@pytest.fixture
def mock_organizer_dir():
    """Create a temporary directory with synthetic organizer CSV files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Write valid dummy CSVs matching EXPECTED_SCHEMAS
        for fname, cols in EXPECTED_SCHEMAS.items():
            fpath = tmp_path / fname
            with open(fpath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(cols)
                if fname == "competitions.csv":
                    writer.writerow(["101", "IPL 2024", "T20", "2024"])
                elif fname == "matches.csv":
                    writer.writerow([
                        "M1", "101", "1", "2024-04-01", "League", "V1", "India",
                        "T1", "Team 1", "T2", "Team 2", "P1", "P2", "T1", "Batting",
                        "MOM1", "120", "120", "", "0", "T1", "Team 1 Won",
                    ])
                elif fname == "teams.csv":
                    writer.writerow(["101", "T1", "Team 1"])
                    writer.writerow(["101", "T2", "Team 2"])
                elif fname == "competition_team_player_mapping.csv":
                    writer.writerow(["101", "IPL 2024", "T1", "Team 1", "P1", "Batter One"])
                    writer.writerow(["101", "IPL 2024", "T2", "Team 2", "P2", "Bowler Two"])
                elif fname == "playing_eleven.csv":
                    writer.writerow(["M1", "T1", "P1", "1", "true", "false", "false", "0", "0"])
                    writer.writerow(["M1", "T2", "P2", "11", "true", "false", "false", "0", "0"])
                elif fname == "ball_by_ball.csv":
                    writer.writerow([
                        "M1", "1", "1", "1", "1", "T1", "T2", "P1", "Batter One",
                        "P3", "Non Striker", "P2", "Bowler Two", "RHB", "Pace",
                        "1", "4", "true", "false", "false", "", "", "", "None",
                        "6", "0", "Pace", "140.0", "Cover Drive", "Inswing", "Over", "Off-side", "2024-04-01 19:30:00",
                    ])
        yield tmp_path


def test_organizer_data_loader_inspection(mock_organizer_dir: Path):
    """Verify loader inspects schemas and generates SHA-256 fingerprints."""
    loader = OrganizerDataLoader(mock_organizer_dir)
    fingerprints = loader.inspect_and_fingerprint()

    assert len(fingerprints) == 6
    assert "ball_by_ball.csv" in fingerprints
    assert fingerprints["ball_by_ball.csv"].row_count == 1
    assert len(fingerprints["ball_by_ball.csv"].sha256) == 64
    assert fingerprints["ball_by_ball.csv"].missing_columns == []


def test_organizer_data_loader_missing_file():
    """Verify loader raises FileNotFoundError if an expected file is absent."""
    with tempfile.TemporaryDirectory() as empty_dir:
        loader = OrganizerDataLoader(Path(empty_dir))
        with pytest.raises(FileNotFoundError):
            loader.inspect_and_fingerprint()


def test_organizer_data_loader_audit_clean(mock_organizer_dir: Path):
    """Verify comprehensive audit passes with 0 FK violations on valid relational mock."""
    loader = OrganizerDataLoader(mock_organizer_dir)
    report = loader.run_comprehensive_audit()

    assert report.total_matches == 1
    assert report.total_deliveries == 1
    assert len(report.fk_violations) == 0
    assert report.ghost_dismissals_detected == 0
    assert report.corrupt_speed_deliveries == 0


def test_compute_file_sha256(mock_organizer_dir: Path):
    """Verify SHA-256 calculation is deterministic."""
    p = mock_organizer_dir / "competitions.csv"
    h1 = compute_file_sha256(p)
    h2 = compute_file_sha256(p)
    assert h1 == h2
    assert len(h1) == 64
