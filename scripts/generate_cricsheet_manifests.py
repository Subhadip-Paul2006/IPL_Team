"""Generate cryptographic SHA-256 manifests for historical CricSheet JSONs and Organizer CSVs.

Part of Phase 1 Historical Data Pipeline Closure (Track A).
Computes bitwise SHA-256 digests for all 5,083 CricSheet JSON files across 13 leagues
and 6 organizer CSVs in datasets/6af3166e7b922_data_pack.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CRICSHEET_LEAGUES = [
    "ipl_male_json",
    "bbl_male_json",
    "sma_json",
    "bpl_male_json",
    "cpl_male_json",
    "psl_male_json",
    "icc_mens_cricket_world_cup_male_json",
    "icc_mens_t20_world_cup_male_json",
    "hnd_male_json",
    "lpl_male_json",
    "ilt_male_json",
    "sat_male_json",
    "mlc_male_json",
]

ORGANIZER_CSVS = [
    "ball_by_ball.csv",
    "competitions.csv",
    "competition_team_player_mapping.csv",
    "matches.csv",
    "playing_eleven.csv",
    "teams.csv",
]


def compute_file_sha256(file_path: Path | str, chunk_size: int = 65536) -> tuple[str, int]:
    """Compute bitwise SHA-256 hex digest and file size in bytes."""
    path = Path(file_path)
    sha256 = hashlib.sha256()
    size = 0
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
            size += len(chunk)
    return sha256.hexdigest(), size


def get_datasets_root() -> Path:
    """Resolve datasets root directory dynamically."""
    env_dir = os.environ.get("DATASETS_ROOT_DIR")
    if env_dir and Path(env_dir).exists():
        return Path(env_dir)

    workspace_dir = Path(__file__).resolve().parent.parent / "datasets"
    if workspace_dir.exists():
        return workspace_dir

    fallback = Path("D:/New folder (2)/datasets")
    if fallback.exists():
        return fallback

    raise FileNotFoundError(f"Datasets root directory not found. Checked: {workspace_dir}, {fallback}")


def generate_cricsheet_manifest(
    datasets_root: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Generate SHA-256 manifest for all CricSheet JSON files."""
    manifest_entries: list[dict[str, Any]] = []
    league_summaries: dict[str, dict[str, Any]] = {}
    total_files = 0
    total_bytes = 0

    for league in CRICSHEET_LEAGUES:
        league_dir = datasets_root / league
        if not league_dir.exists():
            continue

        json_files = sorted(league_dir.glob("*.json"))
        league_files_count = len(json_files)
        league_bytes = 0

        for jf in json_files:
            digest, size = compute_file_sha256(jf)
            league_bytes += size
            manifest_entries.append({
                "league": league,
                "relative_path": f"{league}/{jf.name}",
                "file_name": jf.name,
                "sha256": digest,
                "size_bytes": size,
            })

        total_files += league_files_count
        total_bytes += league_bytes
        league_summaries[league] = {
            "file_count": league_files_count,
            "total_bytes": league_bytes,
        }

    manifest = {
        "manifest_version": "1.0.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "datasets_root": str(datasets_root),
        "total_files_count": total_files,
        "total_size_bytes": total_bytes,
        "expected_cricsheet_count": 5083,
        "is_count_verified": total_files == 5083,
        "leagues_count": len(league_summaries),
        "league_summaries": league_summaries,
        "files": manifest_entries,
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    return manifest


def generate_organizer_manifest(
    datasets_root: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Generate SHA-256 manifest for organizer CSVs and reference data."""
    pack_dir = datasets_root / "6af3166e7b922_data_pack"
    files_entries: list[dict[str, Any]] = []
    total_bytes = 0

    if pack_dir.exists():
        for csv_name in ORGANIZER_CSVS:
            csv_path = pack_dir / csv_name
            if csv_path.exists():
                digest, size = compute_file_sha256(csv_path)
                total_bytes += size
                # Quick line count
                with csv_path.open("r", encoding="utf-8", errors="replace") as f:
                    row_count = sum(1 for _ in f) - 1
                files_entries.append({
                    "dataset_group": "organizer_pack",
                    "relative_path": f"6af3166e7b922_data_pack/{csv_name}",
                    "file_name": csv_name,
                    "sha256": digest,
                    "size_bytes": size,
                    "row_count": max(row_count, 0),
                })

    # Reference CSVs in datasets root
    reference_csvs = ["names.csv", "people.csv", "venues.csv", "venue_names.csv"]
    for ref_name in reference_csvs:
        ref_path = datasets_root / ref_name
        if ref_path.exists():
            digest, size = compute_file_sha256(ref_path)
            total_bytes += size
            with ref_path.open("r", encoding="utf-8", errors="replace") as f:
                row_count = sum(1 for _ in f) - 1
            files_entries.append({
                "dataset_group": "cricsheet_reference",
                "relative_path": ref_name,
                "file_name": ref_name,
                "sha256": digest,
                "size_bytes": size,
                "row_count": max(row_count, 0),
            })

    manifest = {
        "manifest_version": "1.0.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "datasets_root": str(datasets_root),
        "total_files_count": len(files_entries),
        "total_size_bytes": total_bytes,
        "files": files_entries,
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    return manifest


def main() -> None:
    root = get_datasets_root()
    print(f"Datasets root: {root}")

    manifest_dir = Path(__file__).resolve().parent.parent / "data" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)

    print("Generating CricSheet SHA-256 manifest (5,083 files)...")
    cricsheet_path = manifest_dir / "cricsheet_sha256_manifest.json"
    cs_manifest = generate_cricsheet_manifest(root, cricsheet_path)
    print(
        f"CricSheet manifest generated: {cs_manifest['total_files_count']} files, "
        f"{cs_manifest['total_size_bytes']} bytes. Verified={cs_manifest['is_count_verified']}"
    )

    print("Generating Organizer and Reference CSV manifest...")
    org_path = manifest_dir / "organizer_sha256_manifest.json"
    org_manifest = generate_organizer_manifest(root, org_path)
    print(
        f"Organizer manifest generated: {org_manifest['total_files_count']} files, "
        f"{org_manifest['total_size_bytes']} bytes."
    )


if __name__ == "__main__":
    main()
