"""Unit and static security regression tests for Phase 2 Row Level Security (RLS) policies.

Verifies tenant isolation, ownership enforcement (auth.uid()), derived child ownership,
proprietary feature protection, and partition boundary security in supabase/migrations/20261113000001_rls_policies.sql.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
RLS_SQL_PATH = ROOT_DIR / "supabase" / "migrations" / "20261113000001_rls_policies.sql"
SCHEMA_SQL_PATH = ROOT_DIR / "supabase" / "migrations" / "20261113000000_initial_schema.sql"


def load_rls_sql() -> str:
    assert RLS_SQL_PATH.exists(), f"Missing RLS migration file at {RLS_SQL_PATH}"
    return RLS_SQL_PATH.read_text(encoding="utf-8")


def test_user_teams_tenant_isolation_policies() -> None:
    """Verify user_teams enforces strict auth.uid() on all CRUD operations."""
    content = load_rls_sql()

    # Verify separate CRUD policies exist
    assert "CREATE POLICY user_teams_select ON user_teams" in content
    assert "CREATE POLICY user_teams_insert ON user_teams" in content
    assert "CREATE POLICY user_teams_update ON user_teams" in content
    assert "CREATE POLICY user_teams_delete ON user_teams" in content

    # Verify no blanket permissive true policies for authenticated users on user_teams
    assert "CREATE POLICY authenticated_user_teams_crud ON user_teams\n    FOR ALL\n    TO authenticated\n    USING (true)" not in content

    # Verify auth.uid() predicate enforcement
    uid_checks = re.findall(
        r"created_by\s*=\s*\(\s*SELECT\s+auth\.uid\(\)::text\s*\)", content, re.IGNORECASE
    )
    # user_teams has SELECT, INSERT, UPDATE (using+check), DELETE -> at least 5 checks
    assert len(uid_checks) >= 5, f"Expected at least 5 auth.uid() checks, found {len(uid_checks)}"


def test_user_team_players_derived_ownership() -> None:
    """Verify user_team_players derives ownership through parent user_teams.created_by."""
    content = load_rls_sql()

    assert "CREATE POLICY user_team_players_select ON user_team_players" in content
    assert "CREATE POLICY user_team_players_insert ON user_team_players" in content
    assert "CREATE POLICY user_team_players_update ON user_team_players" in content
    assert "CREATE POLICY user_team_players_delete ON user_team_players" in content

    # Verify parent relationship derivation via EXISTS subquery
    derived_pattern = re.compile(
        r"EXISTS\s*\(\s*SELECT\s+1\s+FROM\s+user_teams\s+"
        r"WHERE\s+user_teams\.team_id\s*=\s*user_team_players\.user_team_id\s+"
        r"AND\s+user_teams\.created_by\s*=\s*\(\s*SELECT\s+auth\.uid\(\)::text\s*\)",
        re.IGNORECASE,
    )
    matches = derived_pattern.findall(content)
    assert len(matches) >= 4, f"Expected at least 4 derived ownership subqueries, found {len(matches)}"


def test_proprietary_features_excluded_from_anonymous_access() -> None:
    """Verify proprietary derived_features and internal configs are never exposed to anon."""
    content = load_rls_sql()

    # Extract public_tables array
    match = re.search(r"public_tables\s+text\[\]\s*:=\s*ARRAY\[(.*?)\];", content, re.DOTALL)
    assert match is not None, "public_tables array not found in RLS migration"
    array_content = match.group(1)

    # derived_features must NOT be in public_tables
    assert "'derived_features'" not in array_content
    # internal verification, source_records, configs, ranking runs must NOT be in public_tables
    assert "'source_records'" not in array_content
    assert "'verification_records'" not in array_content
    assert "'ranking_configurations'" not in array_content
    assert "'ranking_runs'" not in array_content


def test_public_scorecard_visibility_includes_fielding_and_wicketkeeping() -> None:
    """Verify public scorecard tables include fielding and wicketkeeping events."""
    content = load_rls_sql()

    match = re.search(r"public_tables\s+text\[\]\s*:=\s*ARRAY\[(.*?)\];", content, re.DOTALL)
    assert match is not None
    array_content = match.group(1)

    assert "'fielding_events'" in array_content
    assert "'wicketkeeping_events'" in array_content
    assert "'batting_innings'" in array_content
    assert "'bowling_spells'" in array_content
    assert "'deliveries'" in array_content


def test_delivery_partitions_explicit_rls_enablement() -> None:
    """Verify all 5 physical delivery partitions have explicit RLS enabled."""
    content = load_rls_sql()

    expected_partitions = [
        "deliveries_y2008_2015",
        "deliveries_y2016_2020",
        "deliveries_y2021_2023",
        "deliveries_y2024_2027",
        "deliveries_default",
    ]

    for part in expected_partitions:
        assert f"ALTER TABLE {part} ENABLE ROW LEVEL SECURITY;" in content


def test_service_role_retains_unrestricted_pipeline_permissions() -> None:
    """Verify service_role retains full unrestricted access on all tables."""
    content = load_rls_sql()

    assert "CREATE POLICY service_role_all ON %I" in content
    assert "FOR ALL" in content
    assert "TO service_role" in content
    assert "USING (true)" in content
    assert "WITH CHECK (true)" in content


def test_cross_user_isolation_logic_simulation() -> None:
    """Simulate policy evaluation logic in Python for cross-user operations."""
    current_auth_uid = "00000000-0000-0000-0000-000000000001"
    other_user_uid = "00000000-0000-0000-0000-000000000002"

    teams = [
        {"team_id": "T1", "created_by": current_auth_uid, "name": "User 1 Team"},
        {"team_id": "T2", "created_by": other_user_uid, "name": "User 2 Team"},
    ]

    team_players = [
        {"id": "TP1", "user_team_id": "T1", "player_id": "P1"},
        {"id": "TP2", "user_team_id": "T2", "player_id": "P2"},
    ]

    # Policy simulator for user_teams: created_by == auth.uid()
    def can_select_team(team: dict[str, str], uid: str) -> bool:
        return team["created_by"] == uid

    # Policy simulator for user_team_players: parent team created_by == auth.uid()
    def can_select_player(player: dict[str, str], uid: str) -> bool:
        parent = next((t for t in teams if t["team_id"] == player["user_team_id"]), None)
        return parent is not None and parent["created_by"] == uid

    # User 1 can only see Team 1 and Team Player 1
    u1_teams = [t for t in teams if can_select_team(t, current_auth_uid)]
    u1_players = [p for p in team_players if can_select_player(p, current_auth_uid)]
    assert len(u1_teams) == 1 and u1_teams[0]["team_id"] == "T1"
    assert len(u1_players) == 1 and u1_players[0]["id"] == "TP1"

    # Cross-user access is denied
    assert not can_select_team(teams[1], current_auth_uid)
    assert not can_select_player(team_players[1], current_auth_uid)
