"""Unit tests for CricSheet v1.3.0 and legacy format parser.

Part of Track A — Phase 1 Historical Data Pipeline Closure.
"""

from datetime import date
from uuid import UUID

import pytest
from scripts.generate_cricsheet_manifests import get_datasets_root
from src.ingestion.cricsheet_parser import (
    CricSheetParsedMatch,
    CricSheetParser,
    derive_uuid,
)


@pytest.fixture
def parser() -> CricSheetParser:
    return CricSheetParser()


@pytest.fixture
def sample_payload() -> dict:
    return {
        "meta": {"data_version": "1.3.0", "created": "2023-04-01", "revision": 1},
        "info": {
            "balls_per_over": 6,
            "city": "Jaipur",
            "dates": ["2023-04-10"],
            "event": {"name": "Indian Premier League", "match_number": 15},
            "gender": "male",
            "match_type": "T20",
            "outcome": {"by": {"runs": 16}, "winner": "Rajasthan Royals"},
            "overs": 20,
            "player_of_match": ["SV Samson"],
            "players": {
                "Rajasthan Royals": ["YBK Jaiswal", "JC Buttler", "SV Samson", "TA Boult"],
                "Delhi Capitals": ["DA Warner", "PP Shaw", "MR Marsh", "AR Patel"],
            },
            "registry": {
                "people": {
                    "YBK Jaiswal": "a1b2c3d4",
                    "JC Buttler": "e5f6a7b8",
                    "SV Samson": "c9d0e1f2",
                    "DA Warner": "dcce6f09",
                    "TA Boult": "11223344",
                }
            },
            "season": "2023",
            "teams": ["Rajasthan Royals", "Delhi Capitals"],
            "toss": {"decision": "bat", "winner": "Rajasthan Royals"},
            "venue": "Sawai Mansingh Stadium",
        },
        "innings": [
            {
                "team": "Rajasthan Royals",
                "overs": [
                    {
                        "over": 0,
                        "deliveries": [
                            {
                                "batter": "YBK Jaiswal",
                                "bowler": "AR Patel",
                                "non_striker": "JC Buttler",
                                "runs": {"batter": 4, "extras": 0, "total": 4},
                            },
                            {
                                "batter": "YBK Jaiswal",
                                "bowler": "AR Patel",
                                "non_striker": "JC Buttler",
                                "runs": {"batter": 0, "extras": 1, "total": 1},
                                "extras": {"wides": 1},
                            },
                            {
                                "batter": "YBK Jaiswal",
                                "bowler": "AR Patel",
                                "non_striker": "JC Buttler",
                                "runs": {"batter": 0, "extras": 0, "total": 0},
                                "wickets": [{"kind": "bowled", "player_out": "YBK Jaiswal"}],
                            },
                        ],
                    }
                ],
            }
        ],
    }


def test_parse_in_memory_json(parser: CricSheetParser, sample_payload: dict):
    """Test parsing an in-memory CricSheet JSON structure."""
    result = parser.parse_json(sample_payload, external_id="IPL_2023_15")

    assert isinstance(result, CricSheetParsedMatch)
    assert not result.is_quarantined
    assert result.match.external_cricsheet_id == "IPL_2023_15"
    assert result.match.match_date == date(2023, 4, 10)
    assert result.match.match_type == "T20"
    assert result.match.toss_decision == "bat"
    assert result.match.outcome_type == "runs"
    assert result.match.win_margin_runs == 16
    assert result.venue_name == "Sawai Mansingh Stadium"

    # Registry hashes
    assert result.player_registry["YBK Jaiswal"] == "a1b2c3d4"
    assert result.player_registry["JC Buttler"] == "e5f6a7b8"

    # Innings
    assert len(result.innings) == 1
    inn = result.innings[0]
    assert inn.innings_number == 1
    assert inn.total_runs == 5
    assert inn.total_extras == 1
    assert inn.total_wickets == 1
    assert inn.total_legal_deliveries == 2  # 3 balls minus 1 wide = 2 legal balls

    # Deliveries
    assert len(result.deliveries) == 3
    d0 = result.deliveries[0]
    assert d0.over_number == 0
    assert d0.ball_in_over == 1
    assert d0.runs_batter == 4
    assert d0.match_phase == "Powerplay"
    assert not d0.is_wicket

    d1 = result.deliveries[1]
    assert d1.is_wide is True
    assert d1.runs_wides == 1

    d2 = result.deliveries[2]
    assert d2.is_wicket is True
    assert d2.wicket_kind == "bowled"
    assert d2.is_bowler_credited_wicket is True


def test_parse_real_cricsheet_file(parser: CricSheetParser):
    """Test parsing an actual historical JSON file from the data lake."""
    datasets_root = get_datasets_root()
    ipl_dir = datasets_root / "ipl_male_json"
    files = list(ipl_dir.glob("*.json"))
    assert len(files) > 0, "No JSON files found in ipl_male_json"

    # Parse the first real match file
    parsed = parser.parse_file(files[0])
    assert parsed.match.status in ("Completed", "Abandoned", "No Result")
    assert len(parsed.innings) >= 1
    assert len(parsed.deliveries) > 0
    assert parsed.venue_name != ""
    assert len(parsed.player_registry) > 0


def test_pre_2008_ipl_quarantine_rule(parser: CricSheetParser, sample_payload: dict):
    """Test that IPL match dated prior to 2008-04-18 is flagged for quarantine."""
    sample_payload["info"]["dates"] = ["2007-05-01"]
    sample_payload["info"]["event"]["name"] = "Indian Premier League"

    parsed = parser.parse_json(sample_payload, external_id="INVALID_IPL_2007")
    assert parsed.is_quarantined
    assert any("precedes inaugural tournament" in r for r in parsed.quarantine_reasons)


def test_legacy_format_parsing(parser: CricSheetParser):
    """Test parsing legacy CricSheet format with '1st innings' wrapper and float deliveries."""
    legacy_payload = {
        "meta": {"data_version": "0.9"},
        "info": {
            "teams": ["Team A", "Team B"],
            "dates": ["2015-05-10"],
            "venue": "Old Ground",
            "outcome": {"winner": "Team A", "by": {"wickets": 5}},
            "overs": 20,
        },
        "innings": [
            {
                "1st innings": {
                    "team": "Team B",
                    "deliveries": [
                        {
                            "0.1": {
                                "batsman": "Batter One",
                                "bowler": "Bowler One",
                                "non_striker": "Batter Two",
                                "runs": {"batsman": 1, "extras": 0, "total": 1},
                            }
                        },
                        {
                            "0.2": {
                                "batsman": "Batter Two",
                                "bowler": "Bowler One",
                                "non_striker": "Batter One",
                                "runs": {"batsman": 0, "extras": 0, "total": 0},
                                "wicket": {"kind": "run out", "player_out": "Batter Two"},
                            }
                        },
                    ],
                }
            }
        ],
    }

    parsed = parser.parse_json(legacy_payload, external_id="LEGACY_001")
    assert not parsed.is_quarantined
    assert len(parsed.innings) == 1
    assert len(parsed.deliveries) == 2
    assert parsed.deliveries[0].runs_batter == 1
    assert parsed.deliveries[1].is_wicket is True
    # Run out is NOT a bowler credited wicket
    assert parsed.deliveries[1].is_bowler_credited_wicket is False


def test_deterministic_uuid_derivation():
    """Verify derive_uuid produces identical UUIDs for identical identifiers."""
    u1 = derive_uuid("player", "db584dad")
    u2 = derive_uuid("player", "db584dad")
    u3 = derive_uuid("player", "different_hash")

    assert u1 == u2
    assert u1 != u3
    assert isinstance(u1, UUID)


def test_super_over_eliminator_and_player_of_match(parser: CricSheetParser):
    """Verify Super Over matches resolve winner via eliminator and populate player_of_match_id."""
    payload = {
        "meta": {"data_version": "1.3.0"},
        "info": {
            "teams": ["Perth Scorchers", "Sydney Sixers"],
            "dates": ["2023-01-15"],
            "match_type": "T20",
            "outcome": {"result": "tie", "eliminator": "Sydney Sixers"},
            "player_of_match": ["Sydney Star"],
            "overs": 20,
        },
        "innings": [],
    }
    parsed = parser.parse_json(payload, external_id="SO_MATCH_01")
    assert not parsed.is_quarantined
    assert parsed.match.outcome_type == "super_over"
    assert parsed.match.winner_id is not None
    assert parsed.match.winner_id == parsed.team_id_map["Sydney Sixers"]
    assert parsed.match.player_of_match_id is not None
    assert parsed.match.player_of_match_id == parsed.player_id_map["Sydney Star"]


def test_retired_hurt_non_dismissal_behavior(parser: CricSheetParser):
    """Verify retired hurt is treated as non-dismissal (not out) and does not increment team wickets."""
    payload = {
        "meta": {"data_version": "1.3.0"},
        "info": {
            "teams": ["Rajasthan Royals", "Gujarat Titans"],
            "dates": ["2023-05-01"],
            "match_type": "T20",
            "outcome": {"winner": "Gujarat Titans", "by": {"runs": 10}},
        },
        "innings": [
            {
                "team": "Rajasthan Royals",
                "overs": [
                    {
                        "over": 0,
                        "deliveries": [
                            {
                                "batter": "Injured Batter",
                                "bowler": "Fast Bowler",
                                "non_striker": "Partner Batter",
                                "runs": {"batter": 0, "extras": 0, "total": 0},
                                "wickets": [{"kind": "retired hurt", "player_out": "Injured Batter"}],
                            },
                            {
                                "batter": "New Batter",
                                "bowler": "Fast Bowler",
                                "non_striker": "Partner Batter",
                                "runs": {"batter": 0, "extras": 0, "total": 0},
                                "wickets": [{"kind": "bowled", "player_out": "New Batter"}],
                            },
                        ],
                    }
                ],
            }
        ],
    }
    parsed = parser.parse_json(payload, external_id="RH_MATCH_01")
    assert not parsed.is_quarantined
    assert len(parsed.deliveries) == 2

    # First delivery: retired hurt
    d0 = parsed.deliveries[0]
    assert d0.is_wicket is False
    assert d0.player_out_id is None
    assert d0.wicket_kind == "retired hurt"
    assert d0.is_bowler_credited_wicket is False

    # Second delivery: true wicket (bowled)
    d1 = parsed.deliveries[1]
    assert d1.is_wicket is True
    assert d1.player_out_id is not None
    assert d1.wicket_kind == "bowled"
    assert d1.is_bowler_credited_wicket is True

    # Total innings wickets must ONLY count true dismissals (1 wicket, not 2)
    assert parsed.innings[0].total_wickets == 1


def test_legacy_format_double_digit_ball_parsing(parser: CricSheetParser):
    """Verify legacy format dotted ball numbers with > 9 balls (e.g. 0.10) preserve ball_in_over = 10."""
    legacy_payload = {
        "info": {
            "teams": ["Team A", "Team B"],
            "dates": ["2015-04-10"],
            "outcome": {"winner": "Team A", "by": {"runs": 5}},
        },
        "innings": [
            {
                "1st innings": {
                    "team": "Team A",
                    "deliveries": [
                        {
                            "0.10": {
                                "batsman": "Batter A",
                                "bowler": "Bowler B",
                                "non_striker": "Batter C",
                                "runs": {"batsman": 1, "extras": 0, "total": 1},
                            }
                        }
                    ],
                }
            }
        ],
    }
    parsed = parser.parse_json(legacy_payload, external_id="LEGACY_BALL_10")
    assert len(parsed.deliveries) == 1
    d = parsed.deliveries[0]
    assert d.over_number == 0
    assert d.ball_in_over == 10


def test_null_safe_nested_dict_parsing(parser: CricSheetParser):
    """Verify parser safely handles explicit None values in JSON fields."""
    payload = {
        "meta": {"data_version": "1.3.0"},
        "info": {
            "teams": ["Team A", "Team B"],
            "dates": ["2022-01-01"],
            "registry": None,
            "event": None,
            "toss": None,
            "outcome": {"result": "no_result", "by": None},
            "players": None,
            "player_of_match": None,
            "overs": None,
            "balls_per_over": None,
        },
        "innings": None,
    }
    parsed = parser.parse_json(payload, external_id="NULL_SAFE_01")
    assert not parsed.is_quarantined
    assert parsed.match.status == "No Result"
    assert parsed.match.outcome_type == "no_result"
    assert parsed.match.innings_balls_scheduled == 120
    assert len(parsed.innings) == 0
