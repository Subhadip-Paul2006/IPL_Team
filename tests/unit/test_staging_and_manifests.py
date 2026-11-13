"""Unit tests for immutable staging service and SHA-256 manifests.

Part of Track A — Phase 1 Historical Data Pipeline Closure.
"""

import json
from pathlib import Path
from uuid import uuid4

import pytest
from src.ingestion.staging import ImmutableStagingService, compute_payload_sha256


@pytest.fixture
def staging_service(tmp_path: Path) -> ImmutableStagingService:
    return ImmutableStagingService(staging_root=tmp_path / "staging")


def test_immutable_staging_valid_payload(staging_service: ImmutableStagingService):
    """Test staging a valid payload generates proper hash and staged record."""
    source_id = str(uuid4())
    payload = {"match_id": "M101", "teams": ["RR", "CSK"], "runs": 175}

    record_id = staging_service.stage_raw_payload(
        source_id=source_id,
        external_id="M101",
        payload=payload,
    )

    record = staging_service.get_staged_record(record_id)
    assert record is not None
    assert record.external_entity_id == "M101"
    assert record.processing_status == "Pending"
    assert record.payload_sha256 == compute_payload_sha256(payload)
    assert record.raw_payload == payload


def test_immutable_staging_checksum_mismatch(staging_service: ImmutableStagingService):
    """Test staging payload with wrong expected checksum triggers quarantine and exception."""
    source_id = str(uuid4())
    payload = {"match_id": "M102", "data": "corrupted"}
    tampered_hash = "0" * 64

    with pytest.raises(ValueError, match="Checksum mismatch"):
        staging_service.stage_raw_payload(
            source_id=source_id,
            external_id="M102",
            payload=payload,
            expected_sha256=tampered_hash,
        )

    quarantined = staging_service.get_all_quarantined()
    assert len(quarantined) == 1
    assert quarantined[0]["external_id"] == "M102"
    assert "Checksum mismatch" in quarantined[0]["reason"]


def test_quarantine_payload_directly(staging_service: ImmutableStagingService):
    """Test explicit quarantine of malformed payload."""
    source_id = str(uuid4())
    staging_service.quarantine_payload(
        source_id=source_id,
        external_id="CORRUPT_01",
        reason="Invalid JSON syntax",
        payload={"corrupt": True},
    )

    quarantined = staging_service.get_all_quarantined()
    assert len(quarantined) == 1
    assert quarantined[0]["external_id"] == "CORRUPT_01"


def test_cricsheet_manifest_integrity():
    """Verify generated CricSheet SHA-256 manifest exists and contains exactly 5,083 files."""
    manifest_path = Path("data/manifests/cricsheet_sha256_manifest.json")
    assert manifest_path.exists(), "cricsheet_sha256_manifest.json does not exist"

    with manifest_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["manifest_version"] == "1.0.0"
    assert data["total_files_count"] == 5083
    assert data["is_count_verified"] is True
    assert data["leagues_count"] == 13
    assert len(data["files"]) == 5083

    # Check that each entry has sha256 and size
    first_file = data["files"][0]
    assert len(first_file["sha256"]) == 64
    assert first_file["size_bytes"] > 0
    assert first_file["league"] in data["league_summaries"]


def test_organizer_manifest_integrity():
    """Verify generated Organizer SHA-256 manifest exists and covers organizer and reference CSVs."""
    manifest_path = Path("data/manifests/organizer_sha256_manifest.json")
    assert manifest_path.exists(), "organizer_sha256_manifest.json does not exist"

    with manifest_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["manifest_version"] == "1.0.0"
    assert data["total_files_count"] >= 6
    file_names = {entry["file_name"] for entry in data["files"]}
    assert "ball_by_ball.csv" in file_names
    assert "matches.csv" in file_names
    assert "playing_eleven.csv" in file_names
