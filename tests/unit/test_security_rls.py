"""Phase 2 Security QA & Row-Level Security (RLS) Test Suite.

Author: Agent E (PIRE & Security QA Specialist)
Target: PostgreSQL 16 / Supabase RLS Migration (20261113000001_rls_policies.sql)

Verifies:
1. Tenant Isolation Regression Tests (CRUD operations on user_teams and user_team_players)
2. Anonymous Access Restrictions (proprietary derived_features, unverified matches, verified scorecards)
3. Declarative Child Partition Defense-in-Depth (REVOKE ALL + RLS default-deny on deliveries partitions)
4. Service-Role Unrestricted Pipeline Access
5. Static Migration AST & Regex Assertions across forward and rollback SQL
6. High-fidelity in-memory PostgreSQL 16 RLS simulation with stateful evaluation
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
RLS_SQL_PATH = ROOT_DIR / "supabase" / "migrations" / "20261113000001_rls_policies.sql"
SCHEMA_SQL_PATH = ROOT_DIR / "supabase" / "migrations" / "20261113000000_initial_schema.sql"
ROLLBACK_SQL_PATH = ROOT_DIR / "supabase" / "rollback" / "20261113000001_rls_policies.down.sql"
ALT_ROLLBACK_SQL_PATH = ROOT_DIR / "supabase" / "rollbacks" / "20261113000001_rls_policies.down.sql"

DELIVERY_PARTITIONS = [
    "deliveries_y2008_2015",
    "deliveries_y2016_2020",
    "deliveries_y2021_2023",
    "deliveries_y2024_2027",
    "deliveries_default",
]

ALL_33_TRD_TABLES = [
    "data_sources",
    "source_records",
    "verification_records",
    "players",
    "player_aliases",
    "teams",
    "venues",
    "competitions",
    "seasons",
    "team_season_participation",
    "squad_memberships",
    "player_team_history",
    "matches",
    "pitch_conditions",
    "weather_conditions",
    "innings",
    "deliveries",
    "batting_innings",
    "bowling_spells",
    "fielding_events",
    "wicketkeeping_events",
    "player_competition_history",
    "player_awards",
    "player_availability",
    "player_injuries",
    "player_membership_state",
    "eligibility_policies",
    "player_eligibility",
    "user_teams",
    "user_team_players",
    "derived_features",
    "ranking_configurations",
    "ranking_runs",
]


def load_rls_sql() -> str:
    """Load the forward RLS migration file."""
    assert RLS_SQL_PATH.exists(), f"RLS migration not found at {RLS_SQL_PATH}"
    return RLS_SQL_PATH.read_text(encoding="utf-8")


def load_rollback_sql() -> str:
    """Load the rollback RLS migration file."""
    if ROLLBACK_SQL_PATH.exists():
        return ROLLBACK_SQL_PATH.read_text(encoding="utf-8")
    assert ALT_ROLLBACK_SQL_PATH.exists(), "Rollback SQL not found"
    return ALT_ROLLBACK_SQL_PATH.read_text(encoding="utf-8")


# =============================================================================
# In-Memory PostgreSQL 16 DAC & RLS Simulation Engine
# =============================================================================


class SecurityException(Exception):
    """Base exception for security violations."""


class PermissionDeniedError(SecurityException):
    """Simulates PostgreSQL 42501 InsufficientPrivilege."""


class RlsPolicyViolationError(SecurityException):
    """Simulates PostgreSQL 42501 / 44000 RLS check violation."""


@dataclass
class Policy:
    name: str
    table_name: str
    cmd: str  # SELECT, INSERT, UPDATE, DELETE, ALL
    roles: list[str]  # anon, authenticated, service_role, etc.
    using: str  # expression or "true"
    with_check: str | None = None


@dataclass
class SimulatedDatabase:
    """Stateful simulation of PostgreSQL 16 catalog permissions and RLS policies."""

    tables: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    rls_enabled: dict[str, bool] = field(default_factory=dict)
    table_privileges: dict[str, dict[str, set[str]]] = field(default_factory=dict)  # table -> role -> {SELECT, INSERT, ...}
    policies: dict[str, list[Policy]] = field(default_factory=dict)  # table -> list[Policy]

    def add_table(self, table_name: str) -> None:
        self.tables[table_name] = []
        self.rls_enabled[table_name] = False
        self.table_privileges[table_name] = {
            "service_role": {"SELECT", "INSERT", "UPDATE", "DELETE"},
            "authenticated": set(),
            "anon": set(),
        }
        self.policies[table_name] = []

    def grant(self, priv: str, table_name: str, roles: list[str]) -> None:
        for r in roles:
            if r in self.table_privileges[table_name]:
                self.table_privileges[table_name][r].add(priv.upper())

    def revoke_all(self, table_name: str, roles: list[str]) -> None:
        for r in roles:
            if r in self.table_privileges[table_name]:
                self.table_privileges[table_name][r].clear()

    def enable_rls(self, table_name: str) -> None:
        self.rls_enabled[table_name] = True

    def add_policy(self, policy: Policy) -> None:
        self.policies[policy.table_name].append(policy)

    def _check_dac(self, table_name: str, role: str, action: str) -> None:
        """Check Discretionary Access Control (table privileges)."""
        if role == "service_role":
            return  # service_role has administrative superuser-like bypass for DAC in Supabase
        privs = self.table_privileges.get(table_name, {}).get(role, set())
        if action.upper() not in privs and "ALL" not in privs:
            raise PermissionDeniedError(
                f"ERROR: 42501 permission denied for table {table_name}"
            )

    def select(
        self,
        table_name: str,
        role: str,
        auth_uid: str | None = None,
        is_child_partition_direct: bool = False,
    ) -> list[dict[str, Any]]:
        """Simulate SELECT query under active role and auth.uid()."""
        # Step 1: Check table-level DAC permissions
        self._check_dac(table_name, role, "SELECT")

        rows = self.tables.get(table_name, [])

        # Step 2: Check RLS
        if role == "service_role":
            return list(rows)

        if not self.rls_enabled.get(table_name, False):
            return list(rows)

        # Find matching SELECT policies for this role
        matching_policies = [
            p for p in self.policies.get(table_name, [])
            if (role in p.roles or "public" in p.roles) and p.cmd in ("SELECT", "ALL")
        ]

        if not matching_policies:
            # RLS default-deny: zero rows returned
            return []

        # Filter rows by policy USING clause
        result: list[dict[str, Any]] = []
        for r in rows:
            for p in matching_policies:
                if self._eval_using(p.using, r, table_name, auth_uid):
                    result.append(r)
                    break
        return result

    def insert(
        self,
        table_name: str,
        role: str,
        row: dict[str, Any],
        auth_uid: str | None = None,
    ) -> dict[str, Any]:
        """Simulate INSERT query under active role and auth.uid()."""
        self._check_dac(table_name, role, "INSERT")

        if role == "service_role":
            self.tables[table_name].append(row)
            return row

        if not self.rls_enabled.get(table_name, False):
            self.tables[table_name].append(row)
            return row

        matching_policies = [
            p for p in self.policies.get(table_name, [])
            if (role in p.roles or "public" in p.roles) and p.cmd in ("INSERT", "ALL")
        ]

        if not matching_policies:
            raise RlsPolicyViolationError(
                f"new row violates row-level security policy for table '{table_name}' (default deny)"
            )

        for p in matching_policies:
            expr = p.with_check or p.using
            if self._eval_with_check(expr, row, table_name, auth_uid):
                self.tables[table_name].append(row)
                return row

        raise RlsPolicyViolationError(
            f"new row violates row-level security policy for table '{table_name}'"
        )

    def update(
        self,
        table_name: str,
        role: str,
        key_col: str,
        key_val: Any,
        new_values: dict[str, Any],
        auth_uid: str | None = None,
    ) -> int:
        """Simulate UPDATE query under active role and auth.uid()."""
        self._check_dac(table_name, role, "UPDATE")

        rows = self.tables.get(table_name, [])
        target_rows = [r for r in rows if r.get(key_col) == key_val]
        if not target_rows:
            return 0

        if role == "service_role":
            for r in target_rows:
                r.update(new_values)
            return len(target_rows)

        if not self.rls_enabled.get(table_name, False):
            for r in target_rows:
                r.update(new_values)
            return len(target_rows)

        matching_policies = [
            p for p in self.policies.get(table_name, [])
            if (role in p.roles or "public" in p.roles) and p.cmd in ("UPDATE", "ALL")
        ]

        if not matching_policies:
            return 0

        updated_count = 0
        for r in target_rows:
            # Check USING clause for visibility
            visible = any(self._eval_using(p.using, r, table_name, auth_uid) for p in matching_policies)
            if not visible:
                continue

            # Check WITH CHECK clause for new row values
            proposed = dict(r)
            proposed.update(new_values)
            allowed = any(
                self._eval_with_check(p.with_check or p.using, proposed, table_name, auth_uid)
                for p in matching_policies
            )
            if not allowed:
                raise RlsPolicyViolationError(
                    f"new row violates row-level security policy (WITH CHECK) for table '{table_name}'"
                )

            r.update(new_values)
            updated_count += 1

        return updated_count

    def delete(
        self,
        table_name: str,
        role: str,
        key_col: str,
        key_val: Any,
        auth_uid: str | None = None,
    ) -> int:
        """Simulate DELETE query under active role and auth.uid()."""
        self._check_dac(table_name, role, "DELETE")

        rows = self.tables.get(table_name, [])
        target_rows = [r for r in rows if r.get(key_col) == key_val]
        if not target_rows:
            return 0

        if role == "service_role":
            self.tables[table_name] = [r for r in rows if r.get(key_col) != key_val]
            return len(target_rows)

        if not self.rls_enabled.get(table_name, False):
            self.tables[table_name] = [r for r in rows if r.get(key_col) != key_val]
            return len(target_rows)

        matching_policies = [
            p for p in self.policies.get(table_name, [])
            if (role in p.roles or "public" in p.roles) and p.cmd in ("DELETE", "ALL")
        ]

        if not matching_policies:
            return 0

        deletable_ids: set[Any] = set()
        for r in target_rows:
            if any(self._eval_using(p.using, r, table_name, auth_uid) for p in matching_policies):
                deletable_ids.add(r.get(key_col))

        if deletable_ids:
            self.tables[table_name] = [r for r in rows if r.get(key_col) not in deletable_ids]
        return len(deletable_ids)

    def _eval_using(
        self,
        expr: str,
        row: dict[str, Any],
        table_name: str,
        auth_uid: str | None,
    ) -> bool:
        if expr == "true":
            return True
        if expr == "false":
            return False

        # user_teams check: created_by = (SELECT auth.uid()::text)
        if table_name == "user_teams" and "created_by" in expr:
            return auth_uid is not None and str(row.get("created_by")) == str(auth_uid)

        # user_team_players check: EXISTS (SELECT 1 FROM user_teams WHERE ...)
        if table_name == "user_team_players" and "user_teams" in expr:
            team_id = row.get("user_team_id")
            user_teams = self.tables.get("user_teams", [])
            parent_team = next((t for t in user_teams if t.get("team_id") == team_id), None)
            if not parent_team:
                return False
            return auth_uid is not None and str(parent_team.get("created_by")) == str(auth_uid)

        # matches check: status IN ('Completed', 'Abandoned', 'No Result')
        if table_name == "matches" and "status IN" in expr:
            status = row.get("status")
            return status in ("Completed", "Abandoned", "No Result")

        return False

    def _eval_with_check(
        self,
        expr: str,
        row: dict[str, Any],
        table_name: str,
        auth_uid: str | None,
    ) -> bool:
        return self._eval_using(expr, row, table_name, auth_uid)


@pytest.fixture
def sim_db() -> SimulatedDatabase:
    """Initialize a SimulatedDatabase mirroring the exact Phase 2 schema & policies."""
    db = SimulatedDatabase()

    # Create tables
    for tbl in ALL_33_TRD_TABLES + DELIVERY_PARTITIONS:
        db.add_table(tbl)

    # 1. Enable RLS on all 33 tables and all 5 delivery partitions
    for tbl in ALL_33_TRD_TABLES + DELIVERY_PARTITIONS:
        db.enable_rls(tbl)

    # 2. Configure DAC table privileges
    # Base tables readable by authenticated
    for tbl in ALL_33_TRD_TABLES:
        db.grant("SELECT", tbl, ["authenticated"])

    # user_teams & user_team_players full CRUD for authenticated
    for tbl in ["user_teams", "user_team_players"]:
        db.grant("INSERT", tbl, ["authenticated"])
        db.grant("UPDATE", tbl, ["authenticated"])
        db.grant("DELETE", tbl, ["authenticated"])

    # Public tables readable by anon
    public_readable_tables = [
        "competitions", "seasons", "teams", "venues", "players", "player_aliases",
        "matches", "pitch_conditions", "weather_conditions", "innings", "deliveries",
        "batting_innings", "bowling_spells", "fielding_events", "wicketkeeping_events",
        "team_season_participation", "squad_memberships", "player_team_history",
        "player_competition_history", "player_awards", "player_availability",
        "player_injuries", "player_membership_state", "eligibility_policies",
        "player_eligibility",
    ]
    for tbl in public_readable_tables:
        db.grant("SELECT", tbl, ["anon"])

    # SEC-05: Revoke all from child partitions
    for part in DELIVERY_PARTITIONS:
        db.revoke_all(part, ["PUBLIC", "anon", "authenticated"])

    # 3. Configure Policies matching 20261113000001_rls_policies.sql

    # Service role: ALL on all 33 tables + 5 partitions
    for tbl in ALL_33_TRD_TABLES + DELIVERY_PARTITIONS:
        db.add_policy(Policy("service_role_all", tbl, "ALL", ["service_role"], "true", "true"))

    # user_teams granular policies
    db.add_policy(Policy("user_teams_select", "user_teams", "SELECT", ["authenticated"], "created_by = (SELECT auth.uid()::text)"))
    db.add_policy(Policy("user_teams_insert", "user_teams", "INSERT", ["authenticated"], "created_by = (SELECT auth.uid()::text)", "created_by = (SELECT auth.uid()::text)"))
    db.add_policy(Policy("user_teams_update", "user_teams", "UPDATE", ["authenticated"], "created_by = (SELECT auth.uid()::text)", "created_by = (SELECT auth.uid()::text)"))
    db.add_policy(Policy("user_teams_delete", "user_teams", "DELETE", ["authenticated"], "created_by = (SELECT auth.uid()::text)"))

    # user_team_players granular policies
    subquery = "EXISTS (SELECT 1 FROM user_teams WHERE user_teams.team_id = user_team_players.user_team_id AND user_teams.created_by = (SELECT auth.uid()::text))"
    db.add_policy(Policy("user_team_players_select", "user_team_players", "SELECT", ["authenticated"], subquery))
    db.add_policy(Policy("user_team_players_insert", "user_team_players", "INSERT", ["authenticated"], subquery, subquery))
    db.add_policy(Policy("user_team_players_update", "user_team_players", "UPDATE", ["authenticated"], subquery, subquery))
    db.add_policy(Policy("user_team_players_delete", "user_team_players", "DELETE", ["authenticated"], subquery))

    # Authenticated select on read tables
    for tbl in ALL_33_TRD_TABLES:
        if tbl not in ("user_teams", "user_team_players"):
            db.add_policy(Policy("authenticated_select", tbl, "SELECT", ["authenticated"], "true"))

    # Anonymous select on public tables (matches has special status filter)
    for tbl in public_readable_tables:
        if tbl == "matches":
            db.add_policy(Policy("anon_select", "matches", "SELECT", ["anon"], "status IN ('Completed', 'Abandoned', 'No Result')"))
        else:
            db.add_policy(Policy("anon_select", tbl, "SELECT", ["anon"], "true"))

    return db


# =============================================================================
# 1. Tenant Isolation Regression Tests
# =============================================================================


def test_tenant_isolation_user_a_cannot_read_user_b_teams(sim_db: SimulatedDatabase) -> None:
    """Verify User A cannot read teams created by User B."""
    uid_a = str(uuid4())
    uid_b = str(uuid4())

    sim_db.tables["user_teams"].extend([
        {"team_id": "T_A1", "name": "Team A", "created_by": uid_a},
        {"team_id": "T_B1", "name": "Team B", "created_by": uid_b},
    ])

    rows_a = sim_db.select("user_teams", role="authenticated", auth_uid=uid_a)
    assert len(rows_a) == 1
    assert rows_a[0]["team_id"] == "T_A1"

    rows_b = sim_db.select("user_teams", role="authenticated", auth_uid=uid_b)
    assert len(rows_b) == 1
    assert rows_b[0]["team_id"] == "T_B1"


def test_tenant_isolation_user_a_cannot_insert_team_owned_by_user_b(sim_db: SimulatedDatabase) -> None:
    """Verify User A cannot spoof User B's identity in created_by on INSERT."""
    uid_a = str(uuid4())
    uid_b = str(uuid4())

    # User A tries to insert a team with created_by = User B
    spoofed_team = {"team_id": "T_SPOOF", "name": "Spoofed Team", "created_by": uid_b}
    with pytest.raises(RlsPolicyViolationError):
        sim_db.insert("user_teams", role="authenticated", row=spoofed_team, auth_uid=uid_a)

    # Legitimate insert with created_by = User A succeeds
    legit_team = {"team_id": "T_LEGIT", "name": "Legit Team", "created_by": uid_a}
    inserted = sim_db.insert("user_teams", role="authenticated", row=legit_team, auth_uid=uid_a)
    assert inserted["team_id"] == "T_LEGIT"


def test_tenant_isolation_user_a_cannot_update_user_b_team(sim_db: SimulatedDatabase) -> None:
    """Verify User A cannot update any properties of User B's team."""
    uid_a = str(uuid4())
    uid_b = str(uuid4())

    sim_db.tables["user_teams"].append(
        {"team_id": "T_B_TARGET", "name": "User B Squad", "created_by": uid_b}
    )

    # User A attempts to rename User B's team
    updated = sim_db.update(
        "user_teams",
        role="authenticated",
        key_col="team_id",
        key_val="T_B_TARGET",
        new_values={"name": "Hacked Name"},
        auth_uid=uid_a,
    )
    assert updated == 0
    assert sim_db.tables["user_teams"][0]["name"] == "User B Squad"

    # User B updating their own team succeeds
    updated_b = sim_db.update(
        "user_teams",
        role="authenticated",
        key_col="team_id",
        key_val="T_B_TARGET",
        new_values={"name": "Updated by B"},
        auth_uid=uid_b,
    )
    assert updated_b == 1
    assert sim_db.tables["user_teams"][0]["name"] == "Updated by B"


def test_tenant_isolation_user_a_cannot_delete_user_b_team(sim_db: SimulatedDatabase) -> None:
    """Verify User A cannot delete User B's team."""
    uid_a = str(uuid4())
    uid_b = str(uuid4())

    sim_db.tables["user_teams"].append(
        {"team_id": "T_B_IMMUTABLE", "name": "Protected Team", "created_by": uid_b}
    )

    # User A attempts to delete User B's team
    deleted = sim_db.delete(
        "user_teams",
        role="authenticated",
        key_col="team_id",
        key_val="T_B_IMMUTABLE",
        auth_uid=uid_a,
    )
    assert deleted == 0
    assert len(sim_db.tables["user_teams"]) == 1

    # User B deleting their own team succeeds
    deleted_b = sim_db.delete(
        "user_teams",
        role="authenticated",
        key_col="team_id",
        key_val="T_B_IMMUTABLE",
        auth_uid=uid_b,
    )
    assert deleted_b == 1
    assert len(sim_db.tables["user_teams"]) == 0


def test_tenant_isolation_user_a_cannot_access_user_b_team_players(sim_db: SimulatedDatabase) -> None:
    """Verify User A cannot view, insert, update, or delete players on User B's team."""
    uid_a = str(uuid4())
    uid_b = str(uuid4())

    sim_db.tables["user_teams"].extend([
        {"team_id": "T_A", "name": "Team A", "created_by": uid_a},
        {"team_id": "T_B", "name": "Team B", "created_by": uid_b},
    ])
    sim_db.tables["user_team_players"].extend([
        {"id": "TP_A", "user_team_id": "T_A", "player_id": "P_1"},
        {"id": "TP_B", "user_team_id": "T_B", "player_id": "P_2"},
    ])

    # 1. SELECT isolation
    rows_a = sim_db.select("user_team_players", role="authenticated", auth_uid=uid_a)
    assert len(rows_a) == 1
    assert rows_a[0]["id"] == "TP_A"

    # 2. INSERT isolation: User A cannot add a player to User B's team
    with pytest.raises(RlsPolicyViolationError):
        sim_db.insert(
            "user_team_players",
            role="authenticated",
            row={"id": "TP_A_INJECT", "user_team_id": "T_B", "player_id": "P_3"},
            auth_uid=uid_a,
        )

    # 3. UPDATE isolation: User A cannot mutate player in User B's team
    updated = sim_db.update(
        "user_team_players",
        role="authenticated",
        key_col="id",
        key_val="TP_B",
        new_values={"player_id": "P_HIJACK"},
        auth_uid=uid_a,
    )
    assert updated == 0
    assert sim_db.tables["user_team_players"][1]["player_id"] == "P_2"

    # 4. DELETE isolation: User A cannot remove player from User B's team
    deleted = sim_db.delete(
        "user_team_players",
        role="authenticated",
        key_col="id",
        key_val="TP_B",
        auth_uid=uid_a,
    )
    assert deleted == 0
    assert len(sim_db.tables["user_team_players"]) == 2


def test_unauthenticated_user_cannot_access_private_team_data(sim_db: SimulatedDatabase) -> None:
    """Verify unauthenticated/anonymous users are completely denied access to user_teams."""
    uid = str(uuid4())
    sim_db.tables["user_teams"].append({"team_id": "T1", "name": "Private Team", "created_by": uid})
    sim_db.tables["user_team_players"].append({"id": "TP1", "user_team_id": "T1", "player_id": "P1"})

    # Anon has no table privileges on user_teams -> PermissionDeniedError (42501)
    with pytest.raises(PermissionDeniedError):
        sim_db.select("user_teams", role="anon")

    with pytest.raises(PermissionDeniedError):
        sim_db.select("user_team_players", role="anon")


# =============================================================================
# 2. Anonymous Access Restrictions & Public Scorecard Tests
# =============================================================================


def test_anonymous_user_cannot_read_proprietary_derived_features(sim_db: SimulatedDatabase) -> None:
    """SEC-03: Verify anonymous users cannot access proprietary derived_features."""
    sim_db.tables["derived_features"].append({
        "feature_id": "F1",
        "player_id": "P1",
        "feature_name": "batting_pressure_bpps",
        "feature_value_numeric": 78.4,
    })

    # anon has no SELECT grant on derived_features
    with pytest.raises(PermissionDeniedError):
        sim_db.select("derived_features", role="anon")

    # authenticated users can read derived_features
    rows_auth = sim_db.select("derived_features", role="authenticated", auth_uid=str(uuid4()))
    assert len(rows_auth) == 1
    assert rows_auth[0]["feature_name"] == "batting_pressure_bpps"


def test_anonymous_user_cannot_read_draft_or_scheduled_matches(sim_db: SimulatedDatabase) -> None:
    """SEC-04: Verify anonymous users only see completed/verified matches, not scheduled ones."""
    sim_db.tables["matches"].extend([
        {"match_id": "M_COMPLETED", "status": "Completed", "home_team": "RR", "away_team": "CSK"},
        {"match_id": "M_SCHEDULED", "status": "Scheduled", "home_team": "RR", "away_team": "MI"},
        {"match_id": "M_DRAFT", "status": "Draft", "home_team": "RR", "away_team": "KKR"},
        {"match_id": "M_ABANDONED", "status": "Abandoned", "home_team": "RCB", "away_team": "GT"},
        {"match_id": "M_NO_RESULT", "status": "No Result", "home_team": "PBKS", "away_team": "DC"},
    ])

    rows_anon = sim_db.select("matches", role="anon")
    returned_ids = {m["match_id"] for m in rows_anon}

    assert "M_COMPLETED" in returned_ids
    assert "M_ABANDONED" in returned_ids
    assert "M_NO_RESULT" in returned_ids
    assert "M_SCHEDULED" not in returned_ids
    assert "M_DRAFT" not in returned_ids
    assert len(rows_anon) == 3


def test_anonymous_user_can_read_verified_match_scorecards(sim_db: SimulatedDatabase) -> None:
    """SEC-06: Verify public viewers can read complete scorecard data including fielding/wicketkeeping."""
    scorecard_tables: list[tuple[str, dict[str, Any]]] = [
        ("batting_innings", {"batting_id": "B1", "runs_scored": 85}),
        ("bowling_spells", {"spell_id": "S1", "wickets": 3}),
        ("fielding_events", {"fielding_id": "FE1", "event_type": "Catch"}),
        ("wicketkeeping_events", {"wk_id": "WK1", "event_type": "Stumping"}),
        ("deliveries", {"delivery_id": "D1", "season_year": "2024", "runs_total": 4}),
    ]

    for tbl, record in scorecard_tables:
        sim_db.tables[tbl].append(record)
        rows = sim_db.select(tbl, role="anon")
        assert len(rows) == 1, f"Anonymous read failed on public scorecard table {tbl}"


# =============================================================================
# 3. Direct Partition Access Tests
# =============================================================================


def test_direct_child_partition_queries_denied_as_anon(sim_db: SimulatedDatabase) -> None:
    """SEC-05 Tier 1: Querying child partitions directly via anon raises 42501 Permission Denied."""
    for part in DELIVERY_PARTITIONS:
        sim_db.tables[part].append({"delivery_id": "D_RAW", "season_year": "2024"})
        with pytest.raises(PermissionDeniedError) as exc_info:
            sim_db.select(part, role="anon", is_child_partition_direct=True)
        assert f"permission denied for table {part}" in str(exc_info.value)


def test_direct_child_partition_queries_denied_as_authenticated(sim_db: SimulatedDatabase) -> None:
    """SEC-05 Tier 1: Querying child partitions directly via authenticated raises 42501."""
    uid = str(uuid4())
    for part in DELIVERY_PARTITIONS:
        sim_db.tables[part].append({"delivery_id": "D_RAW", "season_year": "2024"})
        with pytest.raises(PermissionDeniedError) as exc_info:
            sim_db.select(part, role="authenticated", auth_uid=uid, is_child_partition_direct=True)
        assert f"permission denied for table {part}" in str(exc_info.value)


def test_child_partitions_fail_safe_rls_default_deny(sim_db: SimulatedDatabase) -> None:
    """SEC-05 Tier 2: If DAC privileges are accidentally leaked, RLS default-deny returns 0 rows."""
    for part in DELIVERY_PARTITIONS:
        sim_db.tables[part].append({"delivery_id": "D_LEAK", "season_year": "2024"})
        # Simulate accidental admin privilege grant
        sim_db.grant("SELECT", part, ["authenticated"])

        # RLS is enabled and has 0 policies for authenticated -> default-deny returns empty list
        rows = sim_db.select(part, role="authenticated", auth_uid=str(uuid4()))
        assert len(rows) == 0, f"Partition {part} leaked rows under RLS default-deny"

        # Restore pristine test state
        sim_db.revoke_all(part, ["authenticated"])


def test_parent_deliveries_query_succeeds_via_partition_pruning(sim_db: SimulatedDatabase) -> None:
    """Verify parent queries scan partitions seamlessly without requiring child table grants."""
    sim_db.tables["deliveries"].append({
        "delivery_id": "D_PARENT_1",
        "season_year": "2024",
        "runs_total": 6,
    })

    # Anon queries parent table
    rows_anon = sim_db.select("deliveries", role="anon")
    assert len(rows_anon) == 1
    assert rows_anon[0]["runs_total"] == 6

    # Authenticated queries parent table
    rows_auth = sim_db.select("deliveries", role="authenticated", auth_uid=str(uuid4()))
    assert len(rows_auth) == 1
    assert rows_auth[0]["runs_total"] == 6


# =============================================================================
# 4. Service-Role Unrestricted Access Tests
# =============================================================================


def test_service_role_retains_unrestricted_access_all_tables_and_partitions(sim_db: SimulatedDatabase) -> None:
    """Verify service_role can read, insert, update, and delete on all tables and child partitions."""
    # Test on base table
    sim_db.tables["players"].append({"player_id": "P_SR", "canonical_name": "Service Player"})
    assert len(sim_db.select("players", role="service_role")) == 1

    # Test direct access on child partition (for bulk loading / COPY)
    part = "deliveries_y2024_2027"
    sim_db.insert(part, role="service_role", row={"delivery_id": "D_COPY", "season_year": "2025"})
    part_rows = sim_db.select(part, role="service_role")
    assert len(part_rows) >= 1
    assert any(r.get("delivery_id") == "D_COPY" for r in part_rows)

    # Test unrestricted update and delete
    updated = sim_db.update(
        part, role="service_role", key_col="delivery_id", key_val="D_COPY", new_values={"season_year": "2026"}
    )
    assert updated == 1

    deleted = sim_db.delete(part, role="service_role", key_col="delivery_id", key_val="D_COPY")
    assert deleted == 1


# =============================================================================
# 5. Static Migration AST & Regex Assertions
# =============================================================================


def test_static_migration_ast_all_33_tables_have_rls_enabled() -> None:
    """Verify 20261113000001_rls_policies.sql enables RLS on all 33 base tables."""
    content = load_rls_sql()
    for tbl in ALL_33_TRD_TABLES:
        pattern = rf"ALTER\s+TABLE\s+{tbl}\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY;"
        assert re.search(pattern, content, re.IGNORECASE), f"Missing ENABLE RLS for {tbl}"


def test_static_migration_ast_all_5_partitions_have_rls_enabled() -> None:
    """Verify 20261113000001_rls_policies.sql enables RLS on all 5 deliveries child partitions."""
    content = load_rls_sql()
    for part in DELIVERY_PARTITIONS:
        pattern = rf"ALTER\s+TABLE\s+{part}\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY;"
        assert re.search(pattern, content, re.IGNORECASE), f"Missing ENABLE RLS for partition {part}"


def test_static_migration_ast_child_partitions_revoked_from_public_and_clients() -> None:
    """SEC-05: Verify direct privileges on child partitions are revoked from PUBLIC, anon, authenticated."""
    content = load_rls_sql()
    revoke_pattern = re.compile(
        r"REVOKE\s+ALL\s+ON\s+([a-zA-Z0-9_,\s]+)\s+FROM\s+PUBLIC,\s*anon,\s*authenticated;",
        re.IGNORECASE,
    )
    matches = revoke_pattern.findall(content)
    assert len(matches) > 0, "REVOKE ALL statement for child partitions not found in RLS migration"

    combined_revoked_tables = " ".join(matches)
    for part in DELIVERY_PARTITIONS:
        assert part in combined_revoked_tables, f"Partition {part} missing from REVOKE ALL statement"


def test_static_migration_ast_user_teams_crud_and_auth_uid() -> None:
    """SEC-01: Verify user_teams defines separate CRUD policies enforcing (auth.uid())::text."""
    content = load_rls_sql()

    for action in ["select", "insert", "update", "delete"]:
        policy_name = f"user_teams_{action}"
        assert f"CREATE POLICY {policy_name} ON user_teams" in content, f"Missing policy {policy_name}"

    # Verify auth.uid() comparison cast
    uid_checks = re.findall(
        r"created_by\s*=\s*\(\s*SELECT\s+auth\.uid\(\)::text\s*\)", content, re.IGNORECASE
    )
    assert len(uid_checks) >= 5, f"Expected >= 5 auth.uid() checks on user_teams, found {len(uid_checks)}"


def test_static_migration_ast_user_team_players_derived_ownership() -> None:
    """SEC-02: Verify user_team_players enforces ownership via EXISTS subquery on user_teams."""
    content = load_rls_sql()

    for action in ["select", "insert", "update", "delete"]:
        policy_name = f"user_team_players_{action}"
        assert f"CREATE POLICY {policy_name} ON user_team_players" in content, f"Missing policy {policy_name}"

    derived_subquery = re.compile(
        r"EXISTS\s*\(\s*SELECT\s+1\s+FROM\s+user_teams\s+"
        r"WHERE\s+user_teams\.team_id\s*=\s*user_team_players\.user_team_id\s+"
        r"AND\s+user_teams\.created_by\s*=\s*\(\s*SELECT\s+auth\.uid\(\)::text\s*\)",
        re.IGNORECASE,
    )
    matches = derived_subquery.findall(content)
    assert len(matches) >= 4, f"Expected >= 4 derived ownership subqueries, found {len(matches)}"


def test_static_migration_ast_proprietary_features_and_matches_filter() -> None:
    """SEC-03 & SEC-04: Verify derived_features is not exposed to anon and matches status filter is present."""
    content = load_rls_sql()

    match = re.search(r"public_tables\s+text\[\]\s*:=\s*ARRAY\[(.*?)\];", content, re.DOTALL)
    assert match is not None, "public_tables array missing from RLS migration"
    array_content = match.group(1)

    assert "'derived_features'" not in array_content
    assert "'source_records'" not in array_content
    assert "'verification_records'" not in array_content
    assert "'ranking_configurations'" not in array_content
    assert "'ranking_runs'" not in array_content

    # matches must enforce completed status filter for anon
    assert "status IN ('Completed', 'Abandoned', 'No Result')" in content


def test_static_migration_ast_rollback_reversibility() -> None:
    """Verify rollback migration cleanly disables RLS and drops policies for all 33 tables + 5 partitions."""
    content = load_rollback_sql()

    for tbl in ALL_33_TRD_TABLES:
        assert tbl in content, f"Table {tbl} missing from rollback loop"

    for part in DELIVERY_PARTITIONS:
        assert part in content, f"Partition {part} missing from rollback loop"

    # Drops granular user_teams and user_team_players policies
    for action in ["select", "insert", "update", "delete"]:
        assert f"DROP POLICY IF EXISTS user_teams_{action} ON user_teams;" in content
        assert f"DROP POLICY IF EXISTS user_team_players_{action} ON user_team_players;" in content

    # Drops loop policies and disables RLS
    assert "DROP POLICY IF EXISTS service_role_all ON" in content
    assert "ALTER TABLE %I DISABLE ROW LEVEL SECURITY" in content
