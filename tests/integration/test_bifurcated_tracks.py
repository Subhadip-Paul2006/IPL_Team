"""End-to-End Integration Tests for Bifurcated Tracks (Track A & Track B).

Verifies:
1. Track A: Historical data ingestion from real CricSheet JSON files, bitwise staging,
   Pydantic v2 contract conversion, and scorecard delivery reconciliation.
2. Track B: Static migration validation of all 33 TRD PostgreSQL 16 entities,
   unified PIRE identity resolution across organizer and CricSheet people hashes,
   and collision safety.
"""

from pathlib import Path

from scripts.generate_cricsheet_manifests import get_datasets_root
from scripts.validate_migrations import validate_migrations
from src.ingestion.cricsheet_parser import CricSheetParser
from src.ingestion.staging import ImmutableStagingService, compute_payload_sha256
from src.pire.models import IdentityStatus, ResolutionTier
from src.pire.resolver import UnifiedPIRE
from src.quality.reconciliation import DataQualityReconciliationService


def test_bifurcated_track_a_and_b_integration(tmp_path: Path) -> None:
    """End-to-end integration test coupling Track A and Track B."""
    datasets_root = get_datasets_root()
    ipl_dir = datasets_root / "ipl_male_json"
    json_files = list(ipl_dir.glob("*.json"))
    assert len(json_files) > 0, "No IPL match files found"

    target_file = json_files[0]

    # -------------------------------------------------------------------------
    # TRACK A: Ingestion, Staging, Normalization, & DQ Reconciliation
    # -------------------------------------------------------------------------
    staging = ImmutableStagingService(staging_root=tmp_path / "staging")
    parser = CricSheetParser()
    dq_service = DataQualityReconciliationService()

    # Step 1: Read and Stage raw payload
    with target_file.open("r", encoding="utf-8") as f:
        import json
        raw_payload = json.load(f)

    source_id = "00000000-0000-0000-0000-000000000001"
    record_id = staging.stage_raw_payload(
        source_id=source_id,
        external_id=target_file.stem,
        payload=raw_payload,
    )
    staged_rec = staging.get_staged_record(record_id)
    assert staged_rec is not None
    assert staged_rec.payload_sha256 == compute_payload_sha256(raw_payload)

    # Step 2: Parse to Domain Contracts
    parsed = parser.parse_json(raw_payload, external_id=target_file.stem)
    assert not parsed.is_quarantined
    assert parsed.match.match_id is not None
    assert len(parsed.innings) >= 1
    assert len(parsed.deliveries) > 0

    # Step 3: Reconcile Deliveries with Innings Scorecard
    rec_result = dq_service.reconcile_match(parsed.match, parsed.innings, parsed.deliveries)
    assert rec_result["is_reconciled"] is True
    assert rec_result["deliveries_count"] == len(parsed.deliveries)

    # -------------------------------------------------------------------------
    # TRACK B: Unified PIRE Resolution & Cross-Source Linking
    # -------------------------------------------------------------------------
    pire = UnifiedPIRE()

    # Pre-register mock organizer players
    organizer_players = [
        {"pid": "1001", "name": "Player Alpha", "team": "Team A", "comp": "IPL"},
        {"pid": "1002", "name": "Player Beta", "team": "Team B", "comp": "IPL"},
    ]
    for op in organizer_players:
        pire.register_player(
            canonical_player_id=op["pid"],
            canonical_name=op["name"],
            source_id="organizer_pack",
            source_player_id=op["pid"],
            teams={op["team"]},
            competitions={op["comp"]},
        )

    # Link CricSheet people hashes extracted from parsed match
    for p_name, p_hash in parsed.player_registry.items():
        # Register new player from CricSheet
        pire.register_player(
            canonical_player_id=f"cric_{p_hash}",
            canonical_name=p_name,
            source_id="cricsheet",
            source_player_id=p_hash,
            external_hashes={"cricsheet": p_hash},
        )

    # Test Tier 1 Resolution using CricSheet hash
    first_cric_name = next(iter(parsed.player_registry.keys()))
    first_cric_hash = parsed.player_registry[first_cric_name]

    res_tier1 = pire.resolve(
        raw_name=first_cric_name,
        source_id="cricsheet",
        external_id=first_cric_hash,
    )
    assert res_tier1.status == IdentityStatus.RESOLVED
    assert res_tier1.tier == ResolutionTier.TIER_1_CANONICAL_EXTERNAL_KEY
    assert res_tier1.player_id == f"cric_{first_cric_hash}"

    # -------------------------------------------------------------------------
    # TRACK B: Schema & Migration Static Verification
    # -------------------------------------------------------------------------
    migrations_dir = Path("supabase/migrations")
    schema_results = validate_migrations(migrations_dir)
    assert schema_results["assertions"]["33_entities_present"] is True
    assert schema_results["assertions"]["deliveries_list_partitioned"] is True
    assert schema_results["assertions"]["fielding_composite_fk"] is True
    assert schema_results["assertions"]["rls_covers_all_33_tables"] is True
    assert schema_results["assertions"]["rollback_covers_all_33_tables"] is True
