"""Dual-Mode Repository for CDCRE Competition History.

Part of Phase 04A — Career Discovery & Competition Research Engine (Milestone 5).
Provides dual-mode persistence (In-Memory for offline testing/development, and
Database Adapter for PostgreSQL 16), parameterized SQL query safety, transactional
rollback guarantees, thread synchronization, and schema mapping for TRD Entity 25
(player_competition_history).

PostgreSQL Environment Guard:
- Default mode is IN_MEMORY.
- Never connects to native PostgreSQL 18 on port 5432.
- Never starts Docker or executes live schema migrations.
- Live database operations verify environment authorization before connection.
"""

from __future__ import annotations

import copy
import logging
import os
import re
import threading
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from src.contracts.cdcre import (
    CareerDataCoverage,
    CareerGapRecord,
    CompetitionHistoryRecord,
    CoverageStatus,
)

logger = logging.getLogger(__name__)

# Canonical PostgreSQL 16 DDL valid coverage status values
VALID_COVERAGE_STATUSES = {
    CoverageStatus.VERIFIED_PARTICIPATION.value,
    CoverageStatus.DATASET_UNAVAILABLE.value,
    CoverageStatus.NOT_ESTABLISHED.value,
    CoverageStatus.CONFIRMED_NON_PARTICIPATION.value,
}

# Environment variable controlling live PostgreSQL 16 database authorization
PG16_AUTH_ENV_VAR = "CDCRE_AUTHORIZED_PG16_DB"


class RepositoryMode(StrEnum):
    """Execution mode for CDCRERepository."""

    IN_MEMORY = "IN_MEMORY"
    DATABASE = "DATABASE"


class DatabaseEnvironmentGuardError(RuntimeError):
    """Raised when an unauthorized attempt to access live database is detected."""


class _ThreadTransactionState:
    """Thread-local transaction staging state for in-memory concurrency isolation."""

    def __init__(self) -> None:
        self.in_transaction: bool = False
        self.staged_inserts: dict[UUID, dict[str, Any]] = {}
        self.staged_deletes: set[UUID] = set()
        self.savepoints: dict[str, tuple[dict[UUID, dict[str, Any]], set[UUID]]] = {}
        self.transaction_snapshot: dict[UUID, dict[str, Any]] | None = None


class CDCRERepository:
    """Dual-mode repository for player_competition_history persistence and queries.

    Adheres strictly to:
    - PostgreSQL 16 DDL schema constraints (`chk_coverage_status`, `uq_player_comp_season`).
    - Transactional atomicity with rollback support.
    - Concurrency isolation & thread synchronization in in-memory mode.
    - Parameterized query enforcement preventing SQL injection attacks.
    - PostgreSQL Environment Guard (offline-safe, no unauthorized socket connections).
    """

    def __init__(
        self,
        mode: RepositoryMode = RepositoryMode.IN_MEMORY,
        db_client: Any = None,
    ) -> None:
        """Initialize the repository in In-Memory or Database mode.

        Args:
            mode: Operational mode (IN_MEMORY or DATABASE). Defaults to IN_MEMORY.
            db_client: Optional mock or live database client/session.
        """
        self.mode = mode
        self._db_client = db_client

        # Concurrency & thread synchronization
        self._lock = threading.RLock()
        self._local = threading.local()

        # In-memory primary storage structures: comp_history_id -> row dict
        self._store: dict[UUID, dict[str, Any]] = {}
        # Career gap storage: gap_id -> row dict
        self._gap_store: dict[UUID, dict[str, Any]] = {}

        # Query audit log for parameterized execution tracking
        self.executed_queries: list[dict[str, Any]] = []

    # -------------------------------------------------------------------------
    # Thread-Local Staging & Storage Properties
    # -------------------------------------------------------------------------

    @property
    def _memory_store(self) -> dict[UUID, dict[str, Any]]:
        """Direct access / alias to primary in-memory store dictionary."""
        return self._store

    @_memory_store.setter
    def _memory_store(self, val: dict[UUID, dict[str, Any]]) -> None:
        self._store = val

    def _get_thread_state(self) -> _ThreadTransactionState:
        """Retrieve or initialize thread-local transaction staging state."""
        state = getattr(self._local, "state", None)
        if state is None or not isinstance(state, _ThreadTransactionState):
            state = _ThreadTransactionState()
            self._local.state = state
        return state

    @property
    def _in_transaction(self) -> bool:
        """Whether the calling thread is within an active transactional boundary."""
        return self._get_thread_state().in_transaction

    @_in_transaction.setter
    def _in_transaction(self, value: bool) -> None:
        self._get_thread_state().in_transaction = value

    @property
    def _transaction_snapshot(self) -> dict[UUID, dict[str, Any]] | None:
        """Snapshot of current thread's transaction state."""
        return self._get_thread_state().transaction_snapshot

    @_transaction_snapshot.setter
    def _transaction_snapshot(self, value: dict[UUID, dict[str, Any]] | None) -> None:
        self._get_thread_state().transaction_snapshot = value

    @property
    def _savepoints(self) -> dict[str, tuple[dict[UUID, dict[str, Any]], set[UUID]]]:
        """Savepoints dictionary for the active thread."""
        return self._get_thread_state().savepoints

    @_savepoints.setter
    def _savepoints(self, value: dict[str, tuple[dict[UUID, dict[str, Any]], set[UUID]]]) -> None:
        self._get_thread_state().savepoints = value

    def _get_visible_records(self) -> dict[UUID, dict[str, Any]]:
        """Return the dictionary of records currently visible to the calling thread."""
        with self._lock:
            state = self._get_thread_state()
            if not state.in_transaction:
                return dict(self._store)
            records = {
                k: v for k, v in self._store.items()
                if k not in state.staged_deletes
            }
            records.update(state.staged_inserts)
            return records

    # -------------------------------------------------------------------------
    # PostgreSQL Environment Guard
    # -------------------------------------------------------------------------

    @classmethod
    def is_live_database_authorized(cls) -> bool:
        """Verify whether live PostgreSQL 16 database connectivity is authorized."""
        auth_flag = os.environ.get(PG16_AUTH_ENV_VAR, "").strip().lower()
        return auth_flag in {"1", "true", "yes", "authorized"}

    def _assert_database_access_allowed(self) -> None:
        """Assert that database access is either mock-assisted or explicitly authorized."""
        if self._db_client is not None:
            # Mock DB client or injected test harness session is allowed
            return
        if not self.is_live_database_authorized():
            raise DatabaseEnvironmentGuardError(
                "Live database connection rejected by PostgreSQL Environment Guard: "
                "No live PostgreSQL 16 instance authorized. Set CDCRE_AUTHORIZED_PG16_DB=1 "
                "only in verified staging/production environments."
            )

    # -------------------------------------------------------------------------
    # Transaction Management
    # -------------------------------------------------------------------------

    def begin(self) -> None:
        """Begin a new transactional boundary."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        if self._db_client is not None and hasattr(self._db_client, "begin"):
            self._db_client.begin()

        with self._lock:
            state = self._get_thread_state()
            if not state.in_transaction:
                state.in_transaction = True
                state.staged_inserts = {}
                state.staged_deletes = set()
                state.savepoints = {}
                state.transaction_snapshot = copy.deepcopy(self._store)

    begin_transaction = begin  # Alias for explicit transaction nomenclature

    def commit(self) -> None:
        """Commit active transaction, making staged changes persistent."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        if self._db_client is not None and hasattr(self._db_client, "commit"):
            self._db_client.commit()

        with self._lock:
            state = self._get_thread_state()
            if state.in_transaction:
                # Apply staged deletes
                for hid in state.staged_deletes:
                    self._store.pop(hid, None)
                # Apply staged inserts
                self._store.update(state.staged_inserts)

                state.staged_inserts.clear()
                state.staged_deletes.clear()
                state.savepoints.clear()
                state.transaction_snapshot = None
                state.in_transaction = False

    commit_transaction = commit  # Alias for explicit transaction nomenclature

    def rollback(self) -> None:
        """Roll back active transaction, restoring state to pre-transaction snapshot."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        if self._db_client is not None and hasattr(self._db_client, "rollback"):
            self._db_client.rollback()

        with self._lock:
            state = self._get_thread_state()
            if state.in_transaction:
                # Discard thread-local staged changes without wiping out other threads' committed records
                state.staged_inserts.clear()
                state.staged_deletes.clear()
                state.savepoints.clear()
                state.transaction_snapshot = None
                state.in_transaction = False

    rollback_transaction = rollback  # Alias for explicit transaction nomenclature

    def savepoint(self, name: str) -> None:
        """Create a named savepoint within active transaction."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        with self._lock:
            state = self._get_thread_state()
            if not state.in_transaction:
                self.begin()
                state = self._get_thread_state()
            if self._db_client is not None and hasattr(self._db_client, "savepoint"):
                self._db_client.savepoint(name)
            state.savepoints[name] = (
                copy.deepcopy(state.staged_inserts),
                copy.deepcopy(state.staged_deletes),
            )

    def rollback_to(self, name: str) -> None:
        """Roll back state to named savepoint."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        with self._lock:
            if self._db_client is not None and hasattr(self._db_client, "rollback_to"):
                self._db_client.rollback_to(name)
            state = self._get_thread_state()
            if name in state.savepoints:
                staged_ins, staged_del = state.savepoints[name]
                state.staged_inserts = copy.deepcopy(staged_ins)
                state.staged_deletes = copy.deepcopy(staged_del)

    # -------------------------------------------------------------------------
    # Schema Mapping (TRD Entity 25: player_competition_history)
    # -------------------------------------------------------------------------

    @staticmethod
    def to_row(
        record: CompetitionHistoryRecord,
        player_id: UUID,
        comp_history_id: UUID | None = None,
        season_id: UUID | None = None,
        team_id: UUID | None = None,
        balls_faced: int | None = None,
        strike_rate: float | None = None,
        economy_rate: float | None = None,
    ) -> dict[str, Any]:
        """Convert a CompetitionHistoryRecord contract to player_competition_history row dictionary.

        Maps both canonical DDL columns and extended attributes:
        - comp_history_id / history_id
        - player_id
        - competition_id
        - season_year
        - season_id
        - team_id
        - appearances / matches_played
        - balls_faced
        - strike_rate
        - economy_rate
        - coverage_status
        - provenance_id
        - created_at
        """
        history_id = comp_history_id or uuid4()
        now = datetime.now(UTC)

        return {
            "comp_history_id": history_id,
            "history_id": history_id,  # Column alias compatibility
            "player_id": player_id,
            "competition_id": record.competition_id,
            "competition_name": record.competition_name,
            "season_year": str(record.season_year),
            "season_id": season_id,
            "team_id": team_id,
            "appearances": record.appearances,
            "matches_played": record.appearances,  # Metric alias compatibility
            "balls_faced": balls_faced,
            "strike_rate": strike_rate,
            "economy_rate": economy_rate,
            "coverage_status": record.coverage_status.value,
            "provenance_id": record.provenance_record_id,
            "format_tag": record.format_tag,
            "balls_per_over": record.balls_per_over,
            "created_at": now,
        }

    @staticmethod
    def from_row(row: dict[str, Any]) -> CompetitionHistoryRecord:
        """Convert a player_competition_history database/store row to CompetitionHistoryRecord.

        Handles column aliases and schema variations robustly.
        """
        raw_status = row.get("coverage_status", CoverageStatus.NOT_ESTABLISHED.value)
        try:
            status = CoverageStatus(raw_status)
        except ValueError:
            status = CoverageStatus.NOT_ESTABLISHED

        # Resolve appearances / matches_played
        appearances = row.get("appearances")
        if appearances is None:
            appearances = row.get("matches_played")

        # Resolve provenance_id / provenance_record_id
        prov_id = row.get("provenance_id") or row.get("provenance_record_id")
        if prov_id is not None and not isinstance(prov_id, UUID):
            prov_id = UUID(str(prov_id))

        comp_id = row.get("competition_id")
        if comp_id is not None and not isinstance(comp_id, UUID):
            comp_id = UUID(str(comp_id))

        return CompetitionHistoryRecord(
            competition_id=comp_id or uuid4(),
            competition_name=row.get("competition_name", "Unknown Competition"),
            season_year=str(row.get("season_year", "")),
            format_tag=str(row.get("format_tag", "T20")),
            appearances=appearances,
            coverage_status=status,
            balls_per_over=int(row.get("balls_per_over", 6)),
            provenance_record_id=prov_id,
        )

    # -------------------------------------------------------------------------
    # Parameterized SQL & Injection Resilience
    # -------------------------------------------------------------------------

    def execute_parameterized(
        self,
        sql: str,
        params: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> Any:
        """Execute query verifying strict parameterization and detecting injection vectors.

        Args:
            sql: Parameterized SQL statement.
            params: Query parameter sequence or dictionary.

        Raises:
            DatabaseEnvironmentGuardError: If DATABASE mode is unauthorized.
            ValueError: If an unparameterized SQL injection pattern is detected.
        """
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        with self._lock:
            self.executed_queries.append({
                "sql": sql,
                "params": params,
                "ts": datetime.now(UTC),
            })

        # Security check: Check for raw string concatenation injection patterns when unparameterized
        raw_injection_patterns = [
            r"'\s*OR\s*'1'\s*=\s*'1",
            r"'\s*OR\s*1\s*=\s*1",
            r"\bOR\s+\d+\s*=\s*\d+",
            r"\bAND\s+\d+\s*=\s*\d+",
            r"\b(?:EXEC|EXECUTE)\b",
            r";\s*(?:DROP|DELETE|TRUNCATE|UPDATE|INSERT|ALTER|CREATE|EXEC|EXECUTE)\b",
            r";\s*DROP\s+TABLE",
            r"--\s*$",
            r"UNION\s+SELECT",
        ]
        is_unparameterized = params is None or (isinstance(params, (tuple, list, dict)) and len(params) == 0)
        if is_unparameterized:
            for pattern in raw_injection_patterns:
                if re.search(pattern, sql, re.IGNORECASE):
                    raise ValueError(
                        f"SQL Injection vector detected in unparameterized query: {sql}"
                    )

        if self._db_client is not None and hasattr(self._db_client, "execute"):
            return self._db_client.execute(sql, params)

        return True

    # -------------------------------------------------------------------------
    # CRUD Operations
    # -------------------------------------------------------------------------

    def save_competition_history(
        self,
        record: CompetitionHistoryRecord,
        player_id: UUID,
        comp_history_id: UUID | None = None,
        season_id: UUID | None = None,
        team_id: UUID | None = None,
        balls_faced: int | None = None,
        strike_rate: float | None = None,
        economy_rate: float | None = None,
    ) -> dict[str, Any]:
        """Save a competition history record to repository store.

        Enforces PostgreSQL 16 DDL constraints:
        - `chk_coverage_status`: valid coverage status value.
        - `uq_player_comp_season`: unique (player_id, competition_id, season_year).
        """
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        row = self.to_row(
            record=record,
            player_id=player_id,
            comp_history_id=comp_history_id,
            season_id=season_id,
            team_id=team_id,
            balls_faced=balls_faced,
            strike_rate=strike_rate,
            economy_rate=economy_rate,
        )

        # Validate chk_coverage_status
        if row["coverage_status"] not in VALID_COVERAGE_STATUSES:
            raise ValueError(
                f"Constraint violation chk_coverage_status: Invalid coverage_status '{row['coverage_status']}'"
            )

        history_id: UUID = row["comp_history_id"]

        with self._lock:
            visible_store = self._get_visible_records()
            # Enforce unique constraint uq_player_comp_season
            for existing_id, existing in visible_store.items():
                if (
                    existing_id != history_id
                    and existing.get("player_id") == player_id
                    and existing.get("competition_id") == record.competition_id
                    and str(existing.get("season_year")) == str(record.season_year)
                ):
                    raise ValueError(
                        f"Unique constraint violation uq_player_comp_season: "
                        f"Player {player_id} already has a record for competition "
                        f"{record.competition_id} season {record.season_year}"
                    )

            # Parameterized query logging for database compliance
            param_sql = (
                "INSERT INTO player_competition_history "
                "(comp_history_id, player_id, competition_id, season_year, appearances, coverage_status, provenance_id) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7) "
                "ON CONFLICT (player_id, competition_id, season_year) DO UPDATE SET "
                "appearances = EXCLUDED.appearances, coverage_status = EXCLUDED.coverage_status"
            )
            self.execute_parameterized(
                param_sql,
                (
                    str(history_id),
                    str(player_id),
                    str(record.competition_id),
                    str(record.season_year),
                    record.appearances,
                    record.coverage_status.value,
                    str(record.provenance_record_id) if record.provenance_record_id else None,
                ),
            )

            # Propagate to database client if attached
            if self._db_client is not None:
                if hasattr(self._db_client, "table"):
                    self._db_client.table("player_competition_history").insert(row).execute()
                elif hasattr(self._db_client, "insert"):
                    self._db_client.insert("player_competition_history", row)

            # Store in thread-local staging if in transaction, else directly in store
            state = self._get_thread_state()
            if state.in_transaction:
                state.staged_inserts[history_id] = row
                state.staged_deletes.discard(history_id)
            else:
                self._store[history_id] = row

            return row

    save_history_record = save_competition_history  # Alias for explicit history record naming

    def save_gap_record(
        self,
        record: CareerGapRecord | dict[str, Any],
        player_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Save a career gap record to the repository.

        Enforces PostgreSQL Environment Guard in DATABASE mode.
        """
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        with self._lock:
            if isinstance(record, CareerGapRecord):
                gap_id = uuid4()
                row = {
                    "gap_id": gap_id,
                    "player_id": record.player_id,
                    "start_season": record.start_season,
                    "end_season": record.end_season,
                    "gap_seasons": list(record.gap_seasons),
                    "gap_type": record.gap_type.value,
                    "competition_name": record.competition_name,
                    "evidence_notes": record.evidence_notes,
                    "provenance_record_id": record.provenance_record_id,
                    "created_at": datetime.now(UTC),
                }
            else:
                gap_id = record.get("gap_id") or uuid4()
                row = dict(record)
                row["gap_id"] = gap_id
                if player_id is not None:
                    row["player_id"] = player_id

            param_sql = (
                "INSERT INTO player_career_gaps "
                "(gap_id, player_id, start_season, end_season, gap_type, competition_name) "
                "VALUES ($1, $2, $3, $4, $5, $6)"
            )
            self.execute_parameterized(
                param_sql,
                (
                    str(row["gap_id"]),
                    str(row["player_id"]),
                    str(row["start_season"]),
                    str(row["end_season"]),
                    str(row["gap_type"]),
                    str(row["competition_name"]),
                ),
            )

            if self._db_client is not None and hasattr(self._db_client, "insert"):
                self._db_client.insert("player_career_gaps", row)

            self._gap_store[gap_id] = row
            return row

    def save_career_coverage(
        self,
        career_coverage: CareerDataCoverage,
    ) -> list[dict[str, Any]]:
        """Persist career coverage records (competitions and gaps) to repository.

        Enforces PostgreSQL Environment Guard in DATABASE mode.
        """
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        with self._lock:
            saved = self.save_batch(
                records=career_coverage.competitions_covered,
                player_id=career_coverage.canonical_player_id,
            )
            for gap in career_coverage.career_gaps:
                self.save_gap_record(gap, player_id=career_coverage.canonical_player_id)
            return saved

    def save_batch(
        self,
        records: list[CompetitionHistoryRecord],
        player_id: UUID,
        fail_index: int | None = None,
    ) -> list[dict[str, Any]]:
        """Save a batch of records atomically within an explicit transaction.

        Args:
            records: List of CompetitionHistoryRecord contracts to persist.
            player_id: Canonical player UUID.
            fail_index: Optional index to simulate mid-batch error and verify rollback.

        Returns:
            List of persisted row dictionaries.

        Raises:
            RuntimeError: If mid-batch failure is triggered at fail_index.
        """
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        self.begin()
        saved: list[dict[str, Any]] = []

        try:
            for idx, rec in enumerate(records):
                if fail_index is not None and idx == fail_index:
                    raise RuntimeError(f"Simulated transaction failure at batch index {idx}")
                row = self.save_competition_history(rec, player_id)
                saved.append(row)
            self.commit()
            return saved
        except Exception:
            self.rollback()
            raise

    def get_by_history_id(self, comp_history_id: UUID) -> CompetitionHistoryRecord | None:
        """Retrieve a single CompetitionHistoryRecord by comp_history_id."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        with self._lock:
            visible = self._get_visible_records()
            if comp_history_id in visible:
                return self.from_row(visible[comp_history_id])

            if self._db_client is not None and hasattr(self._db_client, "select"):
                rows = self._db_client.select("player_competition_history", comp_history_id=comp_history_id)
                if rows:
                    return self.from_row(rows[0])

            return None

    def get_by_player_id(self, player_id: UUID) -> list[CompetitionHistoryRecord]:
        """Retrieve all competition history records for a canonical player UUID."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        param_sql = "SELECT * FROM player_competition_history WHERE player_id = $1 ORDER BY season_year ASC"
        self.execute_parameterized(param_sql, (str(player_id),))

        with self._lock:
            visible = self._get_visible_records()
            matched = [
                self.from_row(row)
                for row in visible.values()
                if row.get("player_id") == player_id
            ]

            if not matched and self._db_client is not None and hasattr(self._db_client, "select"):
                db_rows = self._db_client.select("player_competition_history", player_id=player_id)
                matched = [self.from_row(r) for r in db_rows]

            return sorted(matched, key=lambda r: (r.competition_name, r.season_year))

    def get_by_competition_id(self, competition_id: UUID) -> list[CompetitionHistoryRecord]:
        """Retrieve all competition history records for a specific competition UUID."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        param_sql = "SELECT * FROM player_competition_history WHERE competition_id = $1"
        self.execute_parameterized(param_sql, (str(competition_id),))

        with self._lock:
            visible = self._get_visible_records()
            matched = [
                self.from_row(row)
                for row in visible.values()
                if row.get("competition_id") == competition_id
            ]
            return sorted(matched, key=lambda r: (r.competition_name, r.season_year))

    def delete_record(self, comp_history_id: UUID) -> bool:
        """Delete a record by comp_history_id."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        param_sql = "DELETE FROM player_competition_history WHERE comp_history_id = $1"
        self.execute_parameterized(param_sql, (str(comp_history_id),))

        with self._lock:
            state = self._get_thread_state()
            if state.in_transaction:
                found = False
                if comp_history_id in state.staged_inserts:
                    del state.staged_inserts[comp_history_id]
                    found = True
                if comp_history_id in self._store:
                    state.staged_deletes.add(comp_history_id)
                    found = True
                return found

            if comp_history_id in self._store:
                del self._store[comp_history_id]
                return True

            if self._db_client is not None and hasattr(self._db_client, "delete"):
                self._db_client.delete("player_competition_history", comp_history_id=comp_history_id)
                return True

            return False

    def delete_by_player_id(self, player_id: UUID) -> int:
        """Delete all competition history records for a player."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        param_sql = "DELETE FROM player_competition_history WHERE player_id = $1"
        self.execute_parameterized(param_sql, (str(player_id),))

        with self._lock:
            state = self._get_thread_state()
            if state.in_transaction:
                deleted_ids: set[UUID] = set()
                for hid, row in list(state.staged_inserts.items()):
                    if row.get("player_id") == player_id:
                        del state.staged_inserts[hid]
                        deleted_ids.add(hid)
                for hid, row in self._store.items():
                    if row.get("player_id") == player_id and hid not in state.staged_deletes:
                        state.staged_deletes.add(hid)
                        deleted_ids.add(hid)
                return len(deleted_ids)

            to_delete = [
                hid for hid, row in self._store.items()
                if row.get("player_id") == player_id
            ]
            for hid in to_delete:
                del self._store[hid]
            return len(to_delete)

    def count(self) -> int:
        """Return total number of records currently stored / visible to this thread."""
        with self._lock:
            return len(self._get_visible_records())

    def clear(self) -> None:
        """Clear all stored records (useful for test isolation)."""
        with self._lock:
            self._store.clear()
            self._gap_store.clear()
            state = self._get_thread_state()
            state.staged_inserts.clear()
            state.staged_deletes.clear()
            state.savepoints.clear()
            state.transaction_snapshot = None
            state.in_transaction = False
            self.executed_queries.clear()


__all__ = [
    "CDCRERepository",
    "DatabaseEnvironmentGuardError",
    "PG16_AUTH_ENV_VAR",
    "RepositoryMode",
]
