"""Organizer Data Loader & Schema Validator (Phase 1B - Workstream A).

Ingests all six organizer CSV files, computes SHA-256 dataset fingerprints,
validates column schemas and data types, checks foreign key referential integrity,
and generates data quality summaries and quarantine records without mutating raw sources.
"""

import csv
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

EXPECTED_SCHEMAS: dict[str, list[str]] = {
    "ball_by_ball.csv": [
        "match_id", "innings", "overid", "over_ball_num", "innings_ball_num",
        "batting_team_id", "bowling_team_id", "striker_id", "striker_name",
        "non_striker_id", "non_striker_name", "bowler_id", "bowler_name",
        "batting_type", "bowling_type", "batting_order", "runs", "is_four",
        "is_six", "is_wicket", "dismissal_type_id", "dismissal_type",
        "dismissed_player_id", "extras_type", "extras1_runs", "extras_2_runs",
        "pace_or_spin", "bowl_speed", "stroke", "delivery_style",
        "over_or_around", "on_or_off", "delivery_ist_time",
    ],
    "competition_team_player_mapping.csv": [
        "comp_id", "comp_name", "team_id", "team_name", "player_id", "player_name",
    ],
    "competitions.csv": [
        "comp_id", "comp_name", "match_format", "season",
    ],
    "matches.csv": [
        "match_id", "comp_id", "match_number", "match_date", "stage",
        "venue_id", "venue_country", "home_team_id", "home_team",
        "away_team_id", "away_team", "home_team_captain_id",
        "away_team_captain_id", "toss_win_team_id", "toss_opted",
        "man_of_the_match", "first_inn_revised_overs",
        "second_inn_revised_overs", "revised_target", "knock_out",
        "win_team_id", "result",
    ],
    "playing_eleven.csv": [
        "match_id", "team_id", "player_id", "batting_order", "is_played",
        "is_captain", "is_wk", "is_impact", "is_impact_off",
    ],
    "teams.csv": [
        "comp_id", "team_id", "team_name",
    ],
}


@dataclass
class DatasetFingerprint:
    """Fingerprint and integrity record for an organizer source file."""

    filename: str
    row_count: int
    column_count: int
    sha256: str
    columns: list[str]
    missing_columns: list[str] = field(default_factory=list)
    unexpected_columns: list[str] = field(default_factory=list)


@dataclass
class DataQualityReport:
    """Comprehensive data quality and quarantine summary."""

    fingerprints: dict[str, DatasetFingerprint] = field(default_factory=dict)
    total_deliveries: int = 0
    total_matches: int = 0
    total_competitions: int = 0
    total_teams: int = 0
    total_mappings: int = 0
    total_playing_eleven_rows: int = 0
    quarantined_records: list[dict[str, Any]] = field(default_factory=list)
    fk_violations: list[dict[str, Any]] = field(default_factory=list)
    ghost_dismissals_detected: int = 0
    corrupt_speed_deliveries: int = 0
    super_over_deliveries: int = 0
    abandoned_matches_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary format for reporting and serialization."""
        return {
            "fingerprints": {
                name: {
                    "filename": fp.filename,
                    "row_count": fp.row_count,
                    "column_count": fp.column_count,
                    "sha256": fp.sha256,
                    "missing_columns": fp.missing_columns,
                    "unexpected_columns": fp.unexpected_columns,
                }
                for name, fp in self.fingerprints.items()
            },
            "summary_counts": {
                "total_deliveries": self.total_deliveries,
                "total_matches": self.total_matches,
                "total_competitions": self.total_competitions,
                "total_teams": self.total_teams,
                "total_mappings": self.total_mappings,
                "total_playing_eleven_rows": self.total_playing_eleven_rows,
                "ghost_dismissals_detected": self.ghost_dismissals_detected,
                "corrupt_speed_deliveries": self.corrupt_speed_deliveries,
                "super_over_deliveries": self.super_over_deliveries,
                "abandoned_matches_count": self.abandoned_matches_count,
            },
            "quarantined_count": len(self.quarantined_records),
            "fk_violations_count": len(self.fk_violations),
        }


def compute_file_sha256(filepath: Path) -> str:
    """Compute the SHA-256 hexadecimal hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class OrganizerDataLoader:
    """Production loader and validator for the 6 organizer CSVs."""

    def __init__(self, data_pack_dir: Path) -> None:
        self.data_pack_dir = Path(data_pack_dir)
        if not self.data_pack_dir.is_dir():
            raise FileNotFoundError(f"Data pack directory not found: {self.data_pack_dir}")

    def inspect_and_fingerprint(self) -> dict[str, DatasetFingerprint]:
        """Inspect all 6 CSV files, validating schemas and calculating checksums."""
        fingerprints: dict[str, DatasetFingerprint] = {}
        for filename, expected_cols in EXPECTED_SCHEMAS.items():
            filepath = self.data_pack_dir / filename
            if not filepath.is_file():
                raise FileNotFoundError(f"Missing required organizer file: {filepath}")

            sha256 = compute_file_sha256(filepath)
            with open(filepath, encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                header = next(reader, [])
                row_count = sum(1 for _ in reader)

            missing = [c for c in expected_cols if c not in header]
            unexpected = [c for c in header if c not in expected_cols]

            fingerprints[filename] = DatasetFingerprint(
                filename=filename,
                row_count=row_count,
                column_count=len(header),
                sha256=sha256,
                columns=header,
                missing_columns=missing,
                unexpected_columns=unexpected,
            )
        return fingerprints

    def load_competitions(self) -> list[dict[str, str]]:
        """Load and return competitions.csv records."""
        path = self.data_pack_dir / "competitions.csv"
        with open(path, encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))

    def load_teams(self) -> list[dict[str, str]]:
        """Load and return teams.csv records."""
        path = self.data_pack_dir / "teams.csv"
        with open(path, encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))

    def load_matches(self) -> list[dict[str, str]]:
        """Load and return matches.csv records."""
        path = self.data_pack_dir / "matches.csv"
        with open(path, encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))

    def load_mappings(self) -> list[dict[str, str]]:
        """Load and return competition_team_player_mapping.csv records."""
        path = self.data_pack_dir / "competition_team_player_mapping.csv"
        with open(path, encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))

    def load_playing_eleven(self) -> list[dict[str, str]]:
        """Load and return playing_eleven.csv records."""
        path = self.data_pack_dir / "playing_eleven.csv"
        with open(path, encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))

    def load_deliveries(self) -> list[dict[str, str]]:
        """Load and return ball_by_ball.csv records."""
        path = self.data_pack_dir / "ball_by_ball.csv"
        with open(path, encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))

    def run_comprehensive_audit(self) -> DataQualityReport:
        """Execute full data quality, foreign key integrity, and anomaly audit."""
        report = DataQualityReport()
        report.fingerprints = self.inspect_and_fingerprint()

        comps = self.load_competitions()
        teams = self.load_teams()
        matches = self.load_matches()
        mappings = self.load_mappings()
        p11 = self.load_playing_eleven()
        deliveries = self.load_deliveries()

        report.total_competitions = len(comps)
        report.total_teams = len(teams)
        report.total_matches = len(matches)
        report.total_mappings = len(mappings)
        report.total_playing_eleven_rows = len(p11)
        report.total_deliveries = len(deliveries)

        comp_ids = {c["comp_id"].strip() for c in comps if c.get("comp_id")}
        match_ids = {m["match_id"].strip() for m in matches if m.get("match_id")}

        # Check FK integrity for matches -> competitions
        for m in matches:
            cid = m.get("comp_id", "").strip()
            if cid and cid not in comp_ids:
                report.fk_violations.append({
                    "entity": "matches",
                    "id": m.get("match_id"),
                    "foreign_key": "comp_id",
                    "invalid_value": cid,
                })

        # Check deliveries integrity & anomalies
        bbb_match_ids: set[str] = set()
        for d in deliveries:
            mid = d.get("match_id", "").strip()
            bbb_match_ids.add(mid)
            if mid and mid not in match_ids:
                report.fk_violations.append({
                    "entity": "ball_by_ball",
                    "id": f"{mid}_{d.get('innings')}_{d.get('innings_ball_num')}",
                    "foreign_key": "match_id",
                    "invalid_value": mid,
                })

            # Ghost dismissal: dismissed_player_id set but is_wicket false
            is_w = d.get("is_wicket", "").strip().lower() == "true"
            d_pid = d.get("dismissed_player_id", "").strip()
            if d_pid and not is_w:
                report.ghost_dismissals_detected += 1
                report.quarantined_records.append({
                    "category": "GHOST_DISMISSAL",
                    "match_id": mid,
                    "innings": d.get("innings"),
                    "ball": d.get("innings_ball_num"),
                    "dismissed_player_id": d_pid,
                    "reason": "dismissed_player_id populated but is_wicket is false",
                })

            # Bowl speed sanitization audit
            bs = d.get("bowl_speed", "").strip()
            if bs:
                try:
                    speed = float(bs)
                    if speed <= 0 or speed > 165.0:
                        report.corrupt_speed_deliveries += 1
                except ValueError:
                    report.corrupt_speed_deliveries += 1

            # Super overs
            try:
                if int(d.get("innings", "1")) > 2:
                    report.super_over_deliveries += 1
            except ValueError:
                pass

        # Abandoned matches: matches with 0 deliveries in ball_by_ball
        report.abandoned_matches_count = len(match_ids - bbb_match_ids)
        return report
