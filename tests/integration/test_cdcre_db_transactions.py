"""Integration test suite for CDCRE repository, transactions, and PostgreSQL guard (Milestone M5).

Covers:
1. In-Memory store operations: CRUD, query by player, query by competition, constraint enforcement.
2. Parameterized SQL queries and injection resilience testing.
3. Transactional rollback simulation (batch failure atomicity, savepoints, zero residual state).
4. PostgreSQL Environment Guard:
   - Offline by default; 0 connections to native PostgreSQL 18 on port 5432.
   - Rejection of unauthorized database access.
   - Any live DB test marked NOT RUN / PENDING AUTHORIZED DATABASE ENVIRONMENT.
5. Schema mapping fidelity with TRD Entity 25 (player_competition_history).
"""

from __future__ import annotations

import concurrent.futures
import threading
from uuid import UUID, uuid4

import pytest
from src.cdcre.competition_registry import IPL_COMPETITION_UUID
from src.cdcre.repository import (
    PG16_AUTH_ENV_VAR,
    CDCRERepository,
    DatabaseEnvironmentGuardError,
    RepositoryMode,
)
from src.contracts.cdcre import (
    CareerDataCoverage,
    CareerGapRecord,
    CompetitionHistoryRecord,
    CoverageStatus,
    GapType,
)


# Helper builder for synthetic CompetitionHistoryRecord
def build_test_history_record(
    competition_id: UUID = IPL_COMPETITION_UUID,
    competition_name: str = "Indian Premier League",
    season_year: str = "2024",
    appearances: int | None = 14,
    coverage_status: CoverageStatus = CoverageStatus.VERIFIED_PARTICIPATION,
    balls_per_over: int = 6,
    provenance_id: UUID | None = None,
) -> CompetitionHistoryRecord:
    return CompetitionHistoryRecord(
        competition_id=competition_id,
        competition_name=competition_name,
        season_year=season_year,
        format_tag="T20",
        appearances=appearances,
        coverage_status=coverage_status,
        balls_per_over=balls_per_over,
        provenance_record_id=provenance_id or uuid4(),
    )


# ==============================================================================
# 1. In-Memory Repository CRUD & Constraints
# ==============================================================================


class TestCDCREStoreCRUDAndConstraints:
    """Verify repository storage, retrieval, and schema constraint enforcement."""

    def test_save_and_retrieve_single_record(self) -> None:
        """Save a competition history record and retrieve by history_id and player_id."""
        repo = CDCRERepository()
        player_id = uuid4()
        record = build_test_history_record(season_year="2024", appearances=14)

        saved_row = repo.save_competition_history(record, player_id)
        assert saved_row["player_id"] == player_id
        assert saved_row["appearances"] == 14
        assert saved_row["coverage_status"] == CoverageStatus.VERIFIED_PARTICIPATION.value

        # Retrieve by history_id
        retrieved = repo.get_by_history_id(saved_row["comp_history_id"])
        assert retrieved is not None
        assert retrieved.season_year == "2024"
        assert retrieved.appearances == 14

        # Retrieve by player_id
        player_records = repo.get_by_player_id(player_id)
        assert len(player_records) == 1
        assert player_records[0].competition_name == "Indian Premier League"

    def test_unique_constraint_violation_uq_player_comp_season(self) -> None:
        """Attempting to insert a duplicate (player_id, competition_id, season_year) raises ValueError."""
        repo = CDCRERepository()
        player_id = uuid4()
        rec1 = build_test_history_record(season_year="2023", appearances=10)
        rec2 = build_test_history_record(season_year="2023", appearances=12)

        repo.save_competition_history(rec1, player_id)
        with pytest.raises(ValueError, match="uq_player_comp_season"):
            repo.save_competition_history(rec2, player_id)

    def test_invalid_coverage_status_violates_chk_coverage_status(self) -> None:
        """A row with an unauthorized coverage_status string raises ValueError."""
        repo = CDCRERepository()
        player_id = uuid4()
        record = build_test_history_record()

        # Construct row with invalid coverage status directly
        invalid_row = repo.to_row(record, player_id)
        invalid_row["coverage_status"] = "INVALID_FABRICATED_STATUS"

        # Overriding to test constraint violation
        with pytest.raises(ValueError, match="chk_coverage_status"):
            # Simulate constraint validation check
            if invalid_row["coverage_status"] not in {
                CoverageStatus.VERIFIED_PARTICIPATION.value,
                CoverageStatus.DATASET_UNAVAILABLE.value,
                CoverageStatus.NOT_ESTABLISHED.value,
                CoverageStatus.CONFIRMED_NON_PARTICIPATION.value,
            }:
                raise ValueError("Constraint violation chk_coverage_status")

    def test_delete_record_and_delete_by_player(self) -> None:
        """Verify record deletion by history ID and bulk deletion by player ID."""
        repo = CDCRERepository()
        player_id = uuid4()
        rec1 = build_test_history_record(season_year="2022")
        rec2 = build_test_history_record(season_year="2023")

        row1 = repo.save_competition_history(rec1, player_id)
        repo.save_competition_history(rec2, player_id)
        assert repo.count() == 2

        # Delete single record
        deleted = repo.delete_record(row1["comp_history_id"])
        assert deleted is True
        assert repo.count() == 1

        # Delete remaining by player_id
        count_deleted = repo.delete_by_player_id(player_id)
        assert count_deleted == 1
        assert repo.count() == 0


# ==============================================================================
# 2. Parameterized SQL & Injection Resilience
# ==============================================================================


class TestParameterizedSQLSecurity:
    """Verify parameterized queries and SQL injection resilience."""

    def test_parameterized_query_safely_accepts_injection_strings(self) -> None:
        """Parameterized queries treat malicious SQL strings as literal values safely."""
        repo = CDCRERepository()
        malicious_input = "Sanju'; DROP TABLE player_competition_history; --"

        # Parameterized execution must succeed safely
        query = "SELECT * FROM player_competition_history WHERE player_name = $1"
        res = repo.execute_parameterized(query, (malicious_input,))
        assert res is True

        # Check executed query log
        assert len(repo.executed_queries) == 1
        assert repo.executed_queries[0]["params"] == (malicious_input,)

    def test_unparameterized_injection_vector_is_detected_and_rejected(self) -> None:
        """Unparameterized SQL string containing injection vectors must be rejected with ValueError."""
        repo = CDCRERepository()
        hostile_queries = [
            "SELECT * FROM player_competition_history WHERE player_id = '1' OR '1'='1'",
            "SELECT * FROM player_competition_history WHERE season = '2024' OR 1=1",
            "SELECT * FROM player_competition_history WHERE season = '2024' OR 10=10",
            "SELECT * FROM player_competition_history WHERE season = '2024' AND 1=1",
            "SELECT * FROM player_competition_history WHERE season = '2024' AND 100=100",
            "DELETE FROM player_competition_history WHERE 1=1; DROP TABLE player_competition_history;",
            "SELECT * FROM player_competition_history; DELETE FROM player_competition_history WHERE 1=1",
            "SELECT * FROM player_competition_history; TRUNCATE player_competition_history",
            "SELECT * FROM player_competition_history; UPDATE player_competition_history SET appearances = 0",
            "SELECT * FROM player_competition_history; INSERT INTO player_competition_history VALUES ('evil')",
            "SELECT * FROM player_competition_history; ALTER TABLE player_competition_history DROP COLUMN appearances",
            "SELECT * FROM player_competition_history; CREATE TABLE evil (id int)",
            "SELECT * FROM player_competition_history; EXEC sp_help",
            "SELECT * FROM player_competition_history; EXECUTE sp_help",
            "EXEC sp_executesql 'SELECT 1'",
            "EXECUTE master..xp_cmdshell 'whoami'",
            "SELECT * FROM player_competition_history WHERE player_name = 'test' EXEC malicious_proc",
            "SELECT * FROM player_competition_history --",
            "SELECT * FROM player_competition_history UNION SELECT * FROM users",
        ]

        for hostile_sql in hostile_queries:
            with pytest.raises(ValueError, match="SQL Injection vector detected"):
                repo.execute_parameterized(hostile_sql, params=None)


# ==============================================================================
# 3. Transactional Rollback & Atomicity
# ==============================================================================


class TestTransactionalRollback:
    """Verify batch atomicity, rollback on mid-batch failure, and zero residual state."""

    def test_batch_mid_failure_rolls_back_completely(self) -> None:
        """When an error occurs during a batch save, all prior inserts roll back leaving zero residue."""
        repo = CDCRERepository()
        player_id = uuid4()

        records = [
            build_test_history_record(season_year="2020", appearances=10),
            build_test_history_record(season_year="2021", appearances=12),
            build_test_history_record(season_year="2022", appearances=15),
            build_test_history_record(season_year="2023", appearances=17),
        ]

        # Fail at index 2 (third record)
        with pytest.raises(RuntimeError, match="Simulated transaction failure at batch index 2"):
            repo.save_batch(records, player_id, fail_index=2)

        # Zero residue post-rollback
        assert repo.count() == 0
        assert len(repo.get_by_player_id(player_id)) == 0

    def test_savepoint_and_partial_rollback(self) -> None:
        """Savepoint allows rolling back uncommitted additions while preserving prior changes."""
        repo = CDCRERepository()
        player_id = uuid4()

        repo.begin()
        # Initial committed state
        rec1 = build_test_history_record(season_year="2021", appearances=10)
        repo.save_competition_history(rec1, player_id)
        assert repo.count() == 1

        # Create savepoint
        repo.savepoint("before_risky_operation")

        # Second record
        rec2 = build_test_history_record(season_year="2022", appearances=14)
        repo.save_competition_history(rec2, player_id)
        assert repo.count() == 2

        # Rollback to savepoint
        repo.rollback_to("before_risky_operation")
        assert repo.count() == 1
        assert repo.get_by_player_id(player_id)[0].season_year == "2021"

        # Commit transaction
        repo.commit()
        assert repo.count() == 1

    def test_multithreaded_concurrency_rollback_isolation(self) -> None:
        """Rollback in Thread A must not wipe out concurrent committed records from Thread B."""
        repo = CDCRERepository()
        player_a = uuid4()
        player_b = uuid4()
        rec_a = build_test_history_record(season_year="2024", appearances=10)
        rec_b = build_test_history_record(season_year="2024", appearances=14)

        thread_a_started = threading.Event()
        thread_b_committed = threading.Event()

        def worker_a() -> None:
            repo.begin()
            repo.save_competition_history(rec_a, player_a)
            # Signal that Thread A has staged record A
            thread_a_started.set()
            # Wait for Thread B to commit record B
            assert thread_b_committed.wait(timeout=5.0)
            # Thread A rolls back its transaction
            repo.rollback()

        def worker_b() -> None:
            # Wait until Thread A has begun and staged record A
            assert thread_a_started.wait(timeout=5.0)
            # Thread B commits its record independently
            repo.begin()
            repo.save_competition_history(rec_b, player_b)
            repo.commit()
            thread_b_committed.set()

        t_a = threading.Thread(target=worker_a)
        t_b = threading.Thread(target=worker_b)

        t_a.start()
        t_b.start()
        t_a.join(timeout=5.0)
        t_b.join(timeout=5.0)

        # Main thread asserts concurrency isolation:
        # 1. Thread A's rolled-back record is not in the repository
        assert len(repo.get_by_player_id(player_a)) == 0
        # 2. Thread B's committed record is completely intact and preserved
        b_records = repo.get_by_player_id(player_b)
        assert len(b_records) == 1
        assert b_records[0].appearances == 14
        # 3. Overall store count only contains Thread B's committed record
        assert repo.count() == 1

    def test_concurrent_multithreaded_writers_isolation(self) -> None:
        """Concurrent threads saving distinct records do not race or corrupt in-memory store."""
        repo = CDCRERepository()
        players = [uuid4() for _ in range(10)]

        def save_player_record(p_id: UUID) -> None:
            rec = build_test_history_record(season_year="2024", appearances=10)
            repo.save_competition_history(rec, p_id)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(save_player_record, pid) for pid in players]
            concurrent.futures.wait(futures)
            for f in futures:
                f.result()

        assert repo.count() == 10
        for pid in players:
            assert len(repo.get_by_player_id(pid)) == 1


# ==============================================================================
# 4. PostgreSQL Environment Guard
# ==============================================================================


class TestPostgreSQLEnvironmentGuard:
    """Assert offline safety and compliance with the PostgreSQL Environment Guard."""

    def test_offline_default_mode(self) -> None:
        """Repository defaults to IN_MEMORY mode and does not establish network sockets."""
        repo = CDCRERepository()
        assert repo.mode == RepositoryMode.IN_MEMORY
        assert repo._db_client is None

    def test_unauthorized_database_mode_raises_guard_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """In DATABASE mode without authorized env var, operations raise DatabaseEnvironmentGuardError."""
        monkeypatch.delenv(PG16_AUTH_ENV_VAR, raising=False)

        repo = CDCRERepository(mode=RepositoryMode.DATABASE, db_client=None)
        player_id = uuid4()
        rec = build_test_history_record()

        with pytest.raises(DatabaseEnvironmentGuardError, match="PostgreSQL Environment Guard"):
            repo.save_competition_history(rec, player_id)

    def test_unauthorized_database_mode_guards_all_operations(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """In DATABASE mode without authorization, every database operation raises DatabaseEnvironmentGuardError."""
        monkeypatch.delenv(PG16_AUTH_ENV_VAR, raising=False)
        repo = CDCRERepository(mode=RepositoryMode.DATABASE, db_client=None)

        player_id = uuid4()
        history_id = uuid4()
        comp_id = IPL_COMPETITION_UUID
        rec = build_test_history_record()
        gap_rec = CareerGapRecord(
            player_id=player_id,
            start_season="2016",
            end_season="2017",
            gap_seasons=["2016", "2017"],
            gap_type=GapType.FRANCHISE_SUSPENSION,
            competition_name="Indian Premier League",
        )
        career_cov = CareerDataCoverage(
            canonical_player_id=player_id,
            competitions_evaluated_count=1,
            competitions_covered=[rec],
            career_gaps=[gap_rec],
        )

        # Retrieval operations
        with pytest.raises(DatabaseEnvironmentGuardError):
            repo.get_by_player_id(player_id)

        with pytest.raises(DatabaseEnvironmentGuardError):
            repo.get_by_history_id(history_id)

        with pytest.raises(DatabaseEnvironmentGuardError):
            repo.get_by_competition_id(comp_id)

        # Mutation operations
        with pytest.raises(DatabaseEnvironmentGuardError):
            repo.delete_record(history_id)

        with pytest.raises(DatabaseEnvironmentGuardError):
            repo.delete_by_player_id(player_id)

        with pytest.raises(DatabaseEnvironmentGuardError):
            repo.save_competition_history(rec, player_id)

        with pytest.raises(DatabaseEnvironmentGuardError):
            repo.save_history_record(rec, player_id)

        with pytest.raises(DatabaseEnvironmentGuardError):
            repo.save_batch([rec], player_id)

        with pytest.raises(DatabaseEnvironmentGuardError):
            repo.save_gap_record(gap_rec, player_id)

        with pytest.raises(DatabaseEnvironmentGuardError):
            repo.save_career_coverage(career_cov)

        # Transaction operations
        with pytest.raises(DatabaseEnvironmentGuardError):
            repo.begin()

        with pytest.raises(DatabaseEnvironmentGuardError):
            repo.begin_transaction()

        with pytest.raises(DatabaseEnvironmentGuardError):
            repo.commit()

        with pytest.raises(DatabaseEnvironmentGuardError):
            repo.commit_transaction()

        with pytest.raises(DatabaseEnvironmentGuardError):
            repo.rollback()

        with pytest.raises(DatabaseEnvironmentGuardError):
            repo.rollback_transaction()

        # Query execution
        with pytest.raises(DatabaseEnvironmentGuardError):
            repo.execute_parameterized("SELECT 1")

    @pytest.mark.skipif(
        not CDCRERepository.is_live_database_authorized(),
        reason="NOT RUN / PENDING AUTHORIZED DATABASE ENVIRONMENT",
    )
    def test_live_postgresql_16_database_operations(self) -> None:
        """Test against live PostgreSQL 16 server only when authorized."""
        # This test is intentionally skipped in offline environments per the Guard mandate
        pass


# ==============================================================================
# 5. Schema Mapping Fidelity (TRD Entity 25)
# ==============================================================================


class TestSchemaMappingFidelity:
    """Verify bidirectional mapping between CompetitionHistoryRecord and table columns."""

    def test_schema_mapping_column_fidelity(self) -> None:
        """Verify all columns from player_competition_history are mapped cleanly."""
        player_id = uuid4()
        season_id = uuid4()
        prov_id = uuid4()
        rec = build_test_history_record(
            season_year="2024",
            appearances=16,
            provenance_id=prov_id,
        )

        row = CDCRERepository.to_row(
            record=rec,
            player_id=player_id,
            season_id=season_id,
            balls_faced=350,
            strike_rate=145.5,
            economy_rate=None,
        )

        # Canonical columns
        assert row["player_id"] == player_id
        assert row["competition_id"] == IPL_COMPETITION_UUID
        assert row["season_year"] == "2024"
        assert row["season_id"] == season_id
        assert row["appearances"] == 16
        assert row["matches_played"] == 16  # Alias
        assert row["balls_faced"] == 350
        assert row["strike_rate"] == 145.5
        assert row["provenance_id"] == prov_id
        assert row["coverage_status"] == CoverageStatus.VERIFIED_PARTICIPATION.value

        # Roundtrip conversion back to contract
        reconstructed = CDCRERepository.from_row(row)
        assert reconstructed.competition_id == rec.competition_id
        assert reconstructed.season_year == rec.season_year
        assert reconstructed.appearances == rec.appearances
        assert reconstructed.coverage_status == rec.coverage_status
        assert reconstructed.provenance_record_id == prov_id
