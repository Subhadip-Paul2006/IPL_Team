"""Synthetic test fixtures for unit and integration testing.

==============================================================================
CRITICAL DOMAIN GUARDRAIL COMPLIANCE:
- R2: NEVER fabricate or hallucinate statistics, players, or memberships.
- P1: Generating synthetic / mock / hallucinated player or match records is
      STRICTLY PROHIBITED in application data or production stores.
- NOTICE: The synthetic fixtures in this module are EXCLUSIVELY FOR OFFLINE
  UNIT TESTS. All names, entities, and values are 100% fictional test data.
  NO REAL CRICKETER STATS OR IDENTITIES ARE FABRICATED OR REPRESENTED HEREIN.
==============================================================================
"""

import uuid
from datetime import UTC, datetime
from typing import Any


def create_synthetic_player(
    player_id: str | None = None,
    canonical_name: str = "Synthetic Test Player Alpha",
    primary_role: str = "Top-order Batter",
    nationality: str = "India",
    identity_status: str = "RESOLVED",
) -> dict[str, Any]:
    """Generate a valid synthetic player dictionary adhering to TRD §11 Table 4."""
    return {
        "player_id": player_id or str(uuid.uuid4()),
        "canonical_name": canonical_name,
        "full_name": f"Full {canonical_name}",
        "date_of_birth": "2002-05-15",
        "nationality": nationality,
        "primary_role": primary_role,
        "batting_hand": "Right",
        "bowling_arm": "Right",
        "bowling_style": "Right-arm offbreak",
        "cricsheet_id": f"syn_{uuid.uuid4().hex[:8]}",
        "identity_status": identity_status,
        "is_active": True,
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }


def create_synthetic_data_source(
    source_id: str | None = None,
    source_name: str = "Synthetic Test Data Feed",
    source_type: str = "JSON Feed",
    license_type: str = "ODC-By",
) -> dict[str, Any]:
    """Generate a valid synthetic data source dictionary adhering to TRD §11 Table 1."""
    return {
        "source_id": source_id or str(uuid.uuid4()),
        "source_name": source_name,
        "source_type": source_type,
        "base_url": "https://synthetic.test.local/feed",
        "license_type": license_type,
        "license_status": "VERIFIED",
        "license_evidence": "Synthetic offline test fixture notice",
        "update_cadence": "Static",
        "data_steward": "QA Test Suite",
        "is_active": True,
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }


def create_synthetic_source_record(
    source_id: str,
    record_id: str | None = None,
    external_entity_id: str = "SYN-MATCH-001",
) -> dict[str, Any]:
    """Generate a valid synthetic source record adhering to TRD §11 Table 2."""
    return {
        "record_id": record_id or str(uuid.uuid4()),
        "source_id": source_id,
        "external_entity_id": external_entity_id,
        "raw_payload": {"synthetic_test_payload": True},
        "payload_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "ingestion_timestamp": datetime.now(UTC).isoformat(),
        "processing_status": "Pending",
    }


def create_synthetic_verification_record(
    subject_id: str,
    subject_type: str = "player_identity",
    verification_id: str | None = None,
) -> dict[str, Any]:
    """Generate a valid synthetic verification record adhering to TRD §11 Table 3."""
    return {
        "verification_id": verification_id or str(uuid.uuid4()),
        "subject_type": subject_type,
        "subject_id": subject_id,
        "source_url": "https://synthetic.test.local/verify",
        "source_provider": "Synthetic Verification Agent",
        "evidence_tier": 1,
        "retrieval_ts": datetime.now(UTC).isoformat(),
        "license": "ODC-By",
        "verification_status": "VERIFIED",
        "confidence": 1.0,
    }


def create_synthetic_venue(venue_id: str | None = None) -> dict[str, Any]:
    """Generate a valid synthetic venue dictionary adhering to TRD §11 Table 6."""
    return {
        "venue_id": venue_id or str(uuid.uuid4()),
        "stadium_name": "Synthetic Arena",
        "city": "Jaipur",
        "country": "India",
        "cricsheet_venue_id": "syn_venue_001",
        "latitude": 26.9124,
        "longitude": 75.7873,
    }


def create_synthetic_team(
    team_id: str | None = None, team_name: str = "Synthetic Royals"
) -> dict[str, Any]:
    """Generate a valid synthetic team dictionary adhering to TRD §11 Table 7."""
    return {
        "team_id": team_id or str(uuid.uuid4()),
        "team_name": team_name,
        "short_code": "SYN",
        "is_active": True,
    }


def create_synthetic_competition(competition_id: str | None = None) -> dict[str, Any]:
    """Generate a valid synthetic competition dictionary adhering to TRD §11 Table 8."""
    return {
        "competition_id": competition_id or str(uuid.uuid4()),
        "name": "Synthetic Indian Premier League",
        "competition_type": "Domestic Franchise T20",
        "governing_body": "BCCI",
        "country": "India",
        "match_overs": 20,
        "balls_per_over": 6,
    }


def create_synthetic_season(competition_id: str, season_id: str | None = None) -> dict[str, Any]:
    """Generate a valid synthetic season dictionary adhering to TRD §11 Table 9."""
    return {
        "season_id": season_id or str(uuid.uuid4()),
        "competition_id": competition_id,
        "season_year": "2024",
        "start_date": "2024-03-22",
        "end_date": "2024-05-26",
    }


def create_synthetic_match(
    season_id: str,
    venue_id: str,
    home_team_id: str,
    away_team_id: str,
    match_id: str | None = None,
) -> dict[str, Any]:
    """Generate a valid synthetic match dictionary adhering to TRD §11 Table 13."""
    return {
        "match_id": match_id or str(uuid.uuid4()),
        "external_cricsheet_id": f"syn_match_{uuid.uuid4().hex[:8]}",
        "season_id": season_id,
        "venue_id": venue_id,
        "match_number": 1,
        "match_type": "T20",
        "match_date": "2024-03-23",
        "home_team_id": home_team_id,
        "away_team_id": away_team_id,
        "outcome_type": "runs",
        "win_margin_runs": 15,
        "status": "Completed",
    }


def create_synthetic_innings(
    match_id: str,
    batting_team_id: str,
    bowling_team_id: str,
    innings_id: str | None = None,
) -> dict[str, Any]:
    """Generate a valid synthetic innings dictionary adhering to TRD §11 Table 14."""
    return {
        "innings_id": innings_id or str(uuid.uuid4()),
        "match_id": match_id,
        "innings_number": 1,
        "batting_team_id": batting_team_id,
        "bowling_team_id": bowling_team_id,
        "overs_allocated_balls": 120,
        "total_runs": 185,
        "total_wickets": 5,
        "total_legal_deliveries": 120,
        "total_extras": 8,
    }


def create_synthetic_delivery(
    innings_id: str,
    batter_id: str,
    bowler_id: str,
    non_striker_id: str,
    season_year: str = "2024",
    delivery_id: str | None = None,
) -> dict[str, Any]:
    """Generate a valid synthetic delivery record adhering to TRD §11 Table 15."""
    return {
        "delivery_id": delivery_id or str(uuid.uuid4()),
        "innings_id": innings_id,
        "season_year": season_year,
        "over_number": 0,
        "ball_in_over": 1,
        "delivery_sequence": 1,
        "batter_id": batter_id,
        "bowler_id": bowler_id,
        "non_striker_id": non_striker_id,
        "runs_batter": 1,
        "runs_extras": 0,
        "runs_total": 1,
        "is_wicket": False,
    }


def create_synthetic_batting_innings(
    innings_id: str,
    player_id: str,
    team_id: str,
    batting_innings_id: str | None = None,
) -> dict[str, Any]:
    """Generate a valid synthetic batting innings record adhering to TRD §11 Table 16."""
    return {
        "batting_innings_id": batting_innings_id or str(uuid.uuid4()),
        "innings_id": innings_id,
        "player_id": player_id,
        "team_id": team_id,
        "did_not_bat": False,
        "batting_position": 1,
        "runs_scored": 45,
        "balls_faced": 30,
        "fours": 4,
        "sixes": 2,
        "dot_balls_faced": 10,
        "strike_rate": 150.0,
        "is_not_out": False,
    }


def create_synthetic_bowling_spell(
    innings_id: str,
    player_id: str,
    team_id: str,
    spell_id: str | None = None,
) -> dict[str, Any]:
    """Generate a valid synthetic bowling spell record adhering to TRD §11 Table 17."""
    return {
        "spell_id": spell_id or str(uuid.uuid4()),
        "innings_id": innings_id,
        "player_id": player_id,
        "team_id": team_id,
        "spell_order": 1,
        "legal_balls_bowled": 24,
        "maidens": 0,
        "runs_conceded": 28,
        "wickets_taken": 2,
        "dot_balls_bowled": 12,
        "economy_rate": 7.0,
        "bowling_average": 14.0,
        "bowling_strike_rate": 12.0,
    }


def create_synthetic_ranking_config(
    target_season_id: str,
    policy_id: str,
    config_id: str | None = None,
) -> dict[str, Any]:
    """Generate a valid synthetic ranking configuration adhering to TRD §11 Table 32."""
    return {
        "config_id": config_id or str(uuid.uuid4()),
        "config_version": "RK-1.0.0-SYNTHETIC",
        "target_season_id": target_season_id,
        "policy_id": policy_id,
        "evaluation_date": "2024-03-01",
        "ordering_json": {"metric": "composite_index", "direction": "desc"},
        "seed": 42,
    }


def create_synthetic_ranking_run(
    config_id: str,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Generate a valid synthetic ranking run adhering to TRD §11 Table 33."""
    return {
        "run_id": run_id or str(uuid.uuid4()),
        "config_id": config_id,
        "data_snapshot_sha256": "a" * 64,
        "candidate_pool": ["syn_p1", "syn_p2", "syn_p3"],
        "top10": [{"rank": 1, "player_id": "syn_p1", "score": 98.5}],
    }
