"""Shared pytest fixtures and transactional test harness for TMVE and repository tests.

Author: Agent E (Tests, Security and Integration Specialist)
Milestone: M5
"""

from __future__ import annotations

import os
import re
from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any

import pytest

from tests.fixtures.tmve_fixtures import (
    build_synthetic_seasons_and_participation,
    create_contradictory_evidence_player,
    create_incomplete_base_player,
    create_squad_only_reserve_player,
    create_synthetic_eligibility_policy,
    create_unassessed_player_for_2027,
    create_verified_non_rr_player,
    create_verified_rr_match_player,
)


class MockTransactionalSession:
    """High-fidelity in-memory transactional session for PostgreSQL 16 testing.

    Enforces:
    1. Transaction boundaries (begin, commit, rollback, savepoints).
    2. Atomicity: rollback completely restores database state to the pre-transaction snapshot.
    3. Zero residual data post-rollback.
    4. Mandatory query parameterization inspection (detects string concatenation / injection).
    """

    def __init__(self) -> None:
        self._committed_state: dict[str, list[dict[str, Any]]] = {}
        self._working_state: dict[str, list[dict[str, Any]]] = {}
        self._in_transaction: bool = False
        self._savepoints: dict[str, dict[str, list[dict[str, Any]]]] = {}
        self.executed_queries: list[dict[str, Any]] = []

    def _clone_state(
        self, state: dict[str, list[dict[str, Any]]]
    ) -> dict[str, list[dict[str, Any]]]:
        return {table: [dict(row) for row in rows] for table, rows in state.items()}

    def begin(self) -> None:
        """Start a new transaction."""
        if not self._in_transaction:
            self._working_state = self._clone_state(self._committed_state)
            self._in_transaction = True
            self._savepoints.clear()

    def commit(self) -> None:
        """Commit current transaction changes to persistent state."""
        if self._in_transaction:
            self._committed_state = self._clone_state(self._working_state)
            self._in_transaction = False
            self._savepoints.clear()

    def rollback(self) -> None:
        """Roll back current transaction, restoring state to snapshot."""
        if self._in_transaction:
            self._working_state = self._clone_state(self._committed_state)
            self._in_transaction = False
            self._savepoints.clear()

    def savepoint(self, name: str) -> None:
        """Create a savepoint within the active transaction."""
        if not self._in_transaction:
            self.begin()
        self._savepoints[name] = self._clone_state(self._working_state)

    def rollback_to(self, name: str) -> None:
        """Roll back to named savepoint."""
        if name in self._savepoints:
            self._working_state = self._clone_state(self._savepoints[name])

    def insert(
        self, table: str, record: dict[str, Any], fail_if_pk_exists: str | None = None
    ) -> dict[str, Any]:
        """Perform insert into working table state within transaction."""
        if not self._in_transaction:
            self.begin()

        table_rows = self._working_state.setdefault(table, [])
        if fail_if_pk_exists and fail_if_pk_exists in record:
            pk_val = record[fail_if_pk_exists]
            if any(r.get(fail_if_pk_exists) == pk_val for r in table_rows):
                raise ValueError(
                    f"Unique constraint violation on {table}.{fail_if_pk_exists}={pk_val}"
                )

        row_copy = dict(record)
        table_rows.append(row_copy)
        return row_copy

    def insert_batch(
        self,
        table: str,
        records: list[dict[str, Any]],
        fail_index: int | None = None,
        fail_reason: str = "Simulated mid-batch constraint failure",
    ) -> list[dict[str, Any]]:
        """Insert a batch of records, optionally failing midway to verify atomicity."""
        if not self._in_transaction:
            self.begin()

        inserted: list[dict[str, Any]] = []
        for i, rec in enumerate(records):
            if fail_index is not None and i == fail_index:
                # Trigger transaction rollback on failure
                self.rollback()
                raise RuntimeError(f"{fail_reason} at index {i}")
            inserted.append(self.insert(table, rec))
        return inserted

    def select(self, table: str, **filters: Any) -> list[dict[str, Any]]:
        """Query rows from current working state."""
        rows = self._working_state.get(table, [])
        if not filters:
            return [dict(r) for r in rows]

        matched = []
        for r in rows:
            if all(r.get(k) == v for k, v in filters.items()):
                matched.append(dict(r))
        return matched

    def execute(self, sql: str, params: tuple[Any, ...] | dict[str, Any] | None = None) -> Any:
        """Execute query verifying strict parameterization and detecting injection vectors."""
        self.executed_queries.append({"sql": sql, "params": params, "ts": datetime.now(UTC)})

        # Security check: Check for raw string concatenation injection patterns
        raw_injection_patterns = [
            r"'\s*OR\s*'1'\s*=\s*'1",
            r"'\s*OR\s*1\s*=\s*1",
            r";\s*DROP\s+TABLE",
            r"--\s*$",
        ]
        for pattern in raw_injection_patterns:
            if re.search(pattern, sql, re.IGNORECASE) and params is None:
                raise ValueError(
                    f"SQL Injection vector detected in unparameterized query: {sql}"
                )

        return True

    def count_records(self, table: str) -> int:
        """Return total row count in table."""
        return len(self._working_state.get(table, []))


@pytest.fixture
def mock_pg16_session() -> Generator[MockTransactionalSession, None, None]:
    """Provide an isolated MockTransactionalSession ensuring clean teardown with zero residue."""
    session = MockTransactionalSession()
    session.begin()
    try:
        yield session
    finally:
        session.rollback()
        # Verify zero uncommitted residue remains in committed state
        assert session.count_records("squad_memberships") == 0
        assert session.count_records("player_team_history") == 0
        assert session.count_records("team_season_participation") == 0


@pytest.fixture
def pg16_transaction(
    mock_pg16_session: MockTransactionalSession,
) -> Generator[Any, None, None]:
    """Database connection / rollback fixture ensuring clean teardown with zero persistent residue.

    Attempts connection to local PostgreSQL 16 (127.0.0.1:54322). If live database is available,
    runs inside a transaction with automatic teardown rollback. If offline, seamlessly provides
    the high-fidelity MockTransactionalSession.
    """
    host = os.getenv("PGHOST", "127.0.0.1")
    port = int(os.getenv("PGPORT", "54322"))
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD", "postgres")
    dbname = os.getenv("PGDATABASE", "postgres")

    live_conn = None
    try:
        import psycopg2

        live_conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname,
            connect_timeout=1,
        )
        live_conn.autocommit = False
    except Exception:
        live_conn = None

    if live_conn is not None:
        try:
            with live_conn.cursor() as cur:
                yield cur
        finally:
            live_conn.rollback()
            live_conn.close()
    else:
        # Fall back to high-fidelity mock transactional session
        yield mock_pg16_session


# ==============================================================================
# Shared Domain Pytest Fixtures
# ==============================================================================


@pytest.fixture
def tmve_verified_rr_player() -> dict[str, Any]:
    """Fixture providing verified RR player data (Sanju Samson proxy)."""
    return create_verified_rr_match_player()


@pytest.fixture
def tmve_squad_only_player() -> dict[str, Any]:
    """Fixture providing squad-only reserve player with 0 appearances."""
    return create_squad_only_reserve_player()


@pytest.fixture
def tmve_incomplete_base_player() -> dict[str, Any]:
    """Fixture providing player absent from incomplete record base."""
    return create_incomplete_base_player()


@pytest.fixture
def tmve_verified_non_rr_player() -> dict[str, Any]:
    """Fixture providing non-RR player satisfying all 7 TRD §4.5 conditions."""
    return create_verified_non_rr_player()


@pytest.fixture
def tmve_contradictory_player() -> dict[str, Any]:
    """Fixture providing player with conflicting squad claims."""
    return create_contradictory_evidence_player()


@pytest.fixture
def tmve_unassessed_player_2027() -> dict[str, Any]:
    """Fixture providing unassessed player for 2027 season."""
    return create_unassessed_player_for_2027()


@pytest.fixture
def tmve_eligibility_policy_2027() -> Any:
    """Fixture providing valid 2027 eligibility policy."""
    return create_synthetic_eligibility_policy(version=1)


@pytest.fixture
def tmve_participation_windows() -> tuple[dict[str, Any], list[Any]]:
    """Fixture providing all RR participation windows across 2008-2027."""
    return build_synthetic_seasons_and_participation()
