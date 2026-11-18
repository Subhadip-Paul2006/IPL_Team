"""Integration tests for PVRE Transactional Repository and Database Safety.

Validates TRD §11, ORIGINAL_REQUEST R5, and AI_INSTRUCTIONS P12:
- Parameterized SQL enforcement: detects and rejects SQL injection vectors.
- Multi-record batch failure rollback: atomicity with zero persistent residue.
- Savepoint isolation and partial rollback (savepoint / rollback_to).
- Multi-threaded transaction staging concurrency isolation.
- PostgreSQL Environment Guard safety: prevents unauthorized native database connections.
"""

from __future__ import annotations

import os
import threading
from typing import Any
from uuid import uuid4

import pytest
from src.pvre.repository import (
    PG16_AUTH_ENV_VAR,
    DatabaseEnvironmentGuardError,
    PVRERepository,
    RepositoryMode,
)

from tests.fixtures.pvre_contract_fixtures import (
    build_mode_a_output,
    build_mode_b_output,
    build_review_dossier,
)


@pytest.fixture
def repo() -> PVRERepository:
    """Fixture providing a clean in-memory PVRERepository."""
    r = PVRERepository(mode=RepositoryMode.IN_MEMORY)
    r.clear()
    return r


# =============================================================================
# 1. Parameterized SQL Enforcement & Injection Resilience Tests
# =============================================================================


def test_parameterized_query_audit_and_success(repo: PVRERepository) -> None:
    """Verify parameterized queries execute cleanly and log to audit trail."""
    sql = "SELECT * FROM pvre_research_outputs WHERE player_id = $1 AND route_status = $2"
    params = (str(uuid4()), "ROUTED_RR_INCUMBENT")

    result = repo.execute_parameterized(sql, params)
    assert result is True
    assert len(repo.executed_queries) == 1
    assert repo.executed_queries[0]["sql"] == sql
    assert repo.executed_queries[0]["params"] == params


def test_sql_injection_rejection_tautology(repo: PVRERepository) -> None:
    """Verify unparameterized SQL injection tautology (' OR '1'='1) is rejected."""
    malicious_sql = "SELECT * FROM players WHERE name = '' OR '1'='1'"
    with pytest.raises(ValueError, match="SQL Injection vector detected"):
        repo.execute_parameterized(malicious_sql)


def test_sql_injection_rejection_numeric_tautology(repo: PVRERepository) -> None:
    """Verify unparameterized numeric tautology (OR 1=1) is rejected."""
    malicious_sql = "SELECT * FROM players WHERE id = 5 OR 1=1"
    with pytest.raises(ValueError, match="SQL Injection vector detected"):
        repo.execute_parameterized(malicious_sql)


def test_sql_injection_rejection_stacked_drop_table(repo: PVRERepository) -> None:
    """Verify stacked DROP TABLE command injection is detected and rejected."""
    malicious_sql = "SELECT * FROM pvre_outputs; DROP TABLE pvre_outputs"
    with pytest.raises(ValueError, match="SQL Injection vector detected"):
        repo.execute_parameterized(malicious_sql)


def test_sql_injection_rejection_comment_termination(repo: PVRERepository) -> None:
    """Verify comment termination injection (-- comment) is rejected."""
    malicious_sql = "SELECT * FROM players WHERE player_id = 'test-id' -- "
    with pytest.raises(ValueError, match="SQL Injection vector detected"):
        repo.execute_parameterized(malicious_sql)


def test_sql_injection_rejection_union_select(repo: PVRERepository) -> None:
    """Verify UNION SELECT unparameterized injection is rejected."""
    malicious_sql = "SELECT id, name FROM players UNION SELECT id, password FROM users"
    with pytest.raises(ValueError, match="SQL Injection vector detected"):
        repo.execute_parameterized(malicious_sql)


def test_parameterized_query_with_injection_strings_in_parameters_is_safe(
    repo: PVRERepository,
) -> None:
    """Verify parameterized query safely handles string values that look like SQL syntax."""
    sql = "INSERT INTO test_table (comment) VALUES ($1)"
    malicious_payload_as_param = "Robert'; DROP TABLE Students; --"

    # Safely passes because the query IS parameterized with params tuple
    result = repo.execute_parameterized(sql, (malicious_payload_as_param,))
    assert result is True
    assert len(repo.executed_queries) == 1
    assert repo.executed_queries[0]["params"] == (malicious_payload_as_param,)


# =============================================================================
# 2. Multi-Record Batch Failure Rollback Tests
# =============================================================================


def test_save_batch_successful_commit(repo: PVRERepository) -> None:
    """Verify successful batch save persists all records atomically."""
    output_a = build_mode_a_output(research_run_id=uuid4())
    output_b = build_mode_b_output(research_run_id=uuid4())
    dossier_c = build_review_dossier(dossier_id=uuid4())

    saved = repo.save_batch([output_a, output_b, dossier_c])
    assert len(saved) == 3
    assert repo.count() == 3

    # Records are retrievable
    retrieved_a = repo.get_research_output(output_a.research_run_id)
    assert retrieved_a is not None
    assert retrieved_a.canonical_name == output_a.canonical_name

    retrieved_c = repo.get_review_dossier(dossier_c.dossier_id)
    assert retrieved_c is not None


def test_save_batch_mid_batch_failure_rolls_back_atomically(repo: PVRERepository) -> None:
    """Verify failure at fail_index triggers atomic rollback with zero persistent residue."""
    output_a = build_mode_a_output(research_run_id=uuid4())
    output_b = build_mode_b_output(research_run_id=uuid4())
    dossier_c = build_review_dossier(dossier_id=uuid4())

    initial_count = repo.count()
    assert initial_count == 0

    # Simulate failure on index 2 (third item)
    with pytest.raises(RuntimeError, match="Simulated transaction failure at batch index 2"):
        repo.save_batch([output_a, output_b, dossier_c], fail_index=2)

    # Repository MUST be completely empty: all-or-nothing atomicity
    assert repo.count() == 0
    assert repo.get_research_output(output_a.research_run_id) is None
    assert repo.get_research_output(output_b.research_run_id) is None
    assert repo.get_review_dossier(dossier_c.dossier_id) is None


# =============================================================================
# 3. Savepoint Isolation & Partial Rollback Tests
# =============================================================================


def test_savepoint_and_partial_rollback(repo: PVRERepository) -> None:
    """Verify savepoint creation, subsequent mutation, and rollback_to savepoint."""
    repo.begin()

    # Insert Record 1 before savepoint
    out_1 = build_mode_a_output(research_run_id=uuid4())
    repo.save_research_output(out_1)

    # Create Savepoint
    repo.savepoint("sp1")

    # Insert Record 2 after savepoint
    out_2 = build_mode_b_output(research_run_id=uuid4())
    repo.save_research_output(out_2)

    # Both records visible in active transaction
    assert repo.get_research_output(out_1.research_run_id) is not None
    assert repo.get_research_output(out_2.research_run_id) is not None

    # Rollback to Savepoint sp1
    repo.rollback_to("sp1")

    # Record 1 still visible; Record 2 discarded
    assert repo.get_research_output(out_1.research_run_id) is not None
    assert repo.get_research_output(out_2.research_run_id) is None

    # Commit remaining changes
    repo.commit()

    # Record 1 persisted permanently; Record 2 absent
    assert repo.count() == 1
    assert repo.get_research_output(out_1.research_run_id) is not None
    assert repo.get_research_output(out_2.research_run_id) is None


# =============================================================================
# 4. Multi-Threaded Concurrency Isolation Tests
# =============================================================================


def test_thread_concurrency_transaction_staging_isolation(repo: PVRERepository) -> None:
    """Verify independent threads stage changes in parallel without cross-thread contamination."""
    run_id_thread1 = uuid4()
    run_id_thread2 = uuid4()

    barrier = threading.Barrier(2)
    thread1_done = threading.Event()
    thread2_verified_isolation = threading.Event()

    def worker_1() -> None:
        repo.begin()
        out1 = build_mode_a_output(research_run_id=run_id_thread1)
        repo.save_research_output(out1)
        # Record visible inside Worker 1 transaction
        assert repo.get_research_output(run_id_thread1) is not None

        barrier.wait()  # Sync with worker 2
        thread2_verified_isolation.wait(timeout=5.0)

        # Worker 1 rolls back
        repo.rollback()
        assert repo.get_research_output(run_id_thread1) is None
        thread1_done.set()

    def worker_2() -> None:
        barrier.wait()  # Wait for Worker 1 to stage out1
        # Worker 2 should NOT see Worker 1's uncommitted staged record
        assert repo.get_research_output(run_id_thread1) is None

        # Worker 2 stages and commits its own record
        repo.begin()
        out2 = build_mode_b_output(research_run_id=run_id_thread2)
        repo.save_research_output(out2)
        repo.commit()

        # Worker 2's record is committed and visible
        assert repo.get_research_output(run_id_thread2) is not None
        thread2_verified_isolation.set()

    t1 = threading.Thread(target=worker_1)
    t2 = threading.Thread(target=worker_2)
    t1.start()
    t2.start()

    t1.join(timeout=10.0)
    t2.join(timeout=10.0)

    # After completion: Worker 2's record persisted; Worker 1's record rolled back
    assert repo.get_research_output(run_id_thread2) is not None
    assert repo.get_research_output(run_id_thread1) is None
    assert repo.count() == 1


# =============================================================================
# 5. PostgreSQL Environment Guard Safety Tests
# =============================================================================


def test_database_mode_rejects_unauthorized_access() -> None:
    """Verify DATABASE mode raises DatabaseEnvironmentGuardError without authorization."""
    # Ensure authorization env var is not set
    if PG16_AUTH_ENV_VAR in os.environ:
        del os.environ[PG16_AUTH_ENV_VAR]

    db_repo = PVRERepository(mode=RepositoryMode.DATABASE)
    with pytest.raises(DatabaseEnvironmentGuardError, match="rejected by PostgreSQL Environment Guard"):
        db_repo.begin()

    with pytest.raises(DatabaseEnvironmentGuardError, match="rejected by PostgreSQL Environment Guard"):
        db_repo.execute_parameterized("SELECT 1")


def test_database_mode_authorized_via_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify DATABASE mode passes guard when PVRE_AUTHORIZED_PG16_DB=1 is set."""
    monkeypatch.setenv(PG16_AUTH_ENV_VAR, "1")
    assert PVRERepository.is_live_database_authorized() is True

    db_repo = PVRERepository(mode=RepositoryMode.DATABASE)
    # Should not raise DatabaseEnvironmentGuardError
    db_repo.begin()
    assert db_repo.execute_parameterized("SELECT 1") is True
    db_repo.commit()


def test_database_mode_authorized_via_mock_client() -> None:
    """Verify DATABASE mode permits access when a mock client is injected."""
    if PG16_AUTH_ENV_VAR in os.environ:
        del os.environ[PG16_AUTH_ENV_VAR]

    class MockDBClient:
        def __init__(self) -> None:
            self.begun = False
            self.committed = False

        def begin(self) -> None:
            self.begun = True

        def commit(self) -> None:
            self.committed = True

        def execute(self, sql: str, params: Any = None) -> bool:
            return True

    mock_client = MockDBClient()
    db_repo = PVRERepository(mode=RepositoryMode.DATABASE, db_client=mock_client)
    db_repo.begin()
    assert mock_client.begun is True
    assert db_repo.execute_parameterized("SELECT 1") is True
    db_repo.commit()
    assert mock_client.committed is True


# =============================================================================
# 6. Delete and Clear Operations
# =============================================================================


def test_delete_record_and_clear(repo: PVRERepository) -> None:
    """Verify delete_record and clear operations function properly."""
    out = build_mode_a_output(research_run_id=uuid4())
    repo.save_research_output(out)
    assert repo.count() == 1

    deleted = repo.delete_record(out.research_run_id)
    assert deleted is True
    assert repo.count() == 0
    assert repo.get_research_output(out.research_run_id) is None

    # Clear test
    repo.save_research_output(out)
    assert repo.count() == 1
    repo.clear()
    assert repo.count() == 0
    assert len(repo.executed_queries) == 0
