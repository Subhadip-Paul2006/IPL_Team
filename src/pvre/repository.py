"""Dual-Mode Repository for Player Verification & Research Engine (PVRE).

Part of Phase 04B — Player Verification & Research Engine (Milestone 5).
Provides dual-mode persistence (In-Memory for offline testing/development, and
Database Adapter for PostgreSQL 16), thread-isolated transaction staging with
savepoints and atomic rollback, parameterized SQL query injection resilience,
and PostgreSQL Environment Guard governance.

PostgreSQL Environment Guard:
- Default mode is IN_MEMORY.
- Never connects to native PostgreSQL on port 5432.
- Never starts Docker or executes live schema migrations.
- Live database operations verify environment authorization via PVRE_AUTHORIZED_PG16_DB.
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
from uuid import UUID

from src.contracts.pvre import (
    PVREOutputContract,
    ReplacementCandidateEvidence,
    ResearchConflict,
    ReviewDossierContract,
    VerificationClaim,
)

logger = logging.getLogger(__name__)

# Environment variable controlling live PostgreSQL 16 database authorization
PG16_AUTH_ENV_VAR = "PVRE_AUTHORIZED_PG16_DB"


class RepositoryMode(StrEnum):
    """Operational persistence mode for PVRERepository."""

    IN_MEMORY = "IN_MEMORY"
    DATABASE = "DATABASE"


class DatabaseEnvironmentGuardError(RuntimeError):
    """Raised when an unauthorized attempt to access live database is detected."""


class _ThreadTransactionState:
    """Thread-local transaction staging state for in-memory concurrency isolation."""

    def __init__(self) -> None:
        self.in_transaction: bool = False
        self.staged_outputs: dict[UUID, dict[str, Any]] = {}
        self.staged_dossiers: dict[UUID, dict[str, Any]] = {}
        self.staged_evidence: dict[UUID, dict[str, Any]] = {}
        self.staged_claims: dict[UUID, dict[str, Any]] = {}
        self.staged_conflicts: dict[UUID, dict[str, Any]] = {}
        self.staged_derived_features: dict[UUID, dict[str, Any]] = {}
        self.staged_deletes: set[UUID] = set()
        self.savepoints: dict[str, Any] = {}
        self.transaction_snapshot: dict[str, Any] | None = None

    def clear_staging(self) -> None:
        """Clear all staged changes."""
        self.staged_outputs.clear()
        self.staged_dossiers.clear()
        self.staged_evidence.clear()
        self.staged_claims.clear()
        self.staged_conflicts.clear()
        self.staged_derived_features.clear()
        self.staged_deletes.clear()
        self.savepoints.clear()
        self.transaction_snapshot = None
        self.in_transaction = False


# Authoritative SQL Injection detection regex patterns
RAW_INJECTION_PATTERNS: list[str] = [
    r"'\s*OR\s*'1'\s*=\s*'1",
    r"'\s*OR\s*1\s*=\s*1",
    r"\bOR\s+\d+\s*=\s*\d+",
    r"\bAND\s+\d+\s*=\s*\d+",
    r"\b(?:EXEC|EXECUTE)\b",
    r";\s*(?:DROP|DELETE|TRUNCATE|UPDATE|INSERT|ALTER|CREATE|EXEC|EXECUTE)\b",
    r";\s*DROP\s+TABLE",
    r"--\s*$",
    r"UNION\s+SELECT",
    r"'\s*UNION\s+SELECT",
]


class PVRERepository:
    """Dual-mode transactional repository for PVRE artifacts.

    Persists:
    - Research outputs (derived_features where feature_set_name = 'pvre_replacement_assessment')
    - Review dossiers (ReviewDossierContract)
    - Replacement candidate evidence (ReplacementCandidateEvidence)
    - Fact verification claims and conflicts (VerificationClaim, ResearchConflict)

    Guarantees:
    - Thread-isolated transaction staging using RLock and threading.local().
    - Transaction rollback atomicity (zero persistent residue on failure).
    - Savepoint support for partial transaction rollbacks.
    - Parameterized SQL enforcement detecting and rejecting injection vectors.
    - PostgreSQL Environment Guard preventing unauthorized network/socket access.
    """

    def __init__(
        self,
        mode: RepositoryMode = RepositoryMode.IN_MEMORY,
        db_client: Any = None,
    ) -> None:
        """Initialize the repository in In-Memory or Database mode."""
        self.mode = mode
        self._db_client = db_client

        # Concurrency & thread synchronization
        self._lock = threading.RLock()
        self._local = threading.local()

        # In-memory stores
        self._outputs: dict[UUID, dict[str, Any]] = {}
        self._dossiers: dict[UUID, dict[str, Any]] = {}
        self._candidate_evidence: dict[UUID, dict[str, Any]] = {}
        self._claims: dict[UUID, dict[str, Any]] = {}
        self._conflicts: dict[UUID, dict[str, Any]] = {}
        self._derived_features: dict[UUID, dict[str, Any]] = {}

        # Audit log for executed queries
        self.executed_queries: list[dict[str, Any]] = []

    # -------------------------------------------------------------------------
    # Thread-Local State Helpers
    # -------------------------------------------------------------------------

    def _get_thread_state(self) -> _ThreadTransactionState:
        """Retrieve or initialize thread-local transaction staging state."""
        state = getattr(self._local, "state", None)
        if state is None or not isinstance(state, _ThreadTransactionState):
            state = _ThreadTransactionState()
            self._local.state = state
        return state

    @property
    def in_transaction(self) -> bool:
        """Whether calling thread is in an active transaction."""
        return self._get_thread_state().in_transaction

    def _get_visible_store(
        self,
        base_store: dict[UUID, dict[str, Any]],
        staged_dict: dict[UUID, dict[str, Any]],
    ) -> dict[UUID, dict[str, Any]]:
        """Return store view visible to calling thread (incorporating staged changes)."""
        with self._lock:
            state = self._get_thread_state()
            if not state.in_transaction:
                return dict(base_store)

            visible = {k: copy.deepcopy(v) for k, v in base_store.items() if k not in state.staged_deletes}
            for k, v in staged_dict.items():
                if k not in state.staged_deletes:
                    visible[k] = copy.deepcopy(v)
            return visible

    # -------------------------------------------------------------------------
    # PostgreSQL Environment Guard
    # -------------------------------------------------------------------------

    @classmethod
    def is_live_database_authorized(cls) -> bool:
        """Verify whether live PostgreSQL 16 database connectivity is authorized."""
        auth_flag = os.environ.get(PG16_AUTH_ENV_VAR, "").strip().lower()
        return auth_flag in {"1", "true", "yes", "authorized"}

    def _assert_database_access_allowed(self) -> None:
        """Assert that database access is either mock-assisted or authorized via environment."""
        if self._db_client is not None:
            return
        if not self.is_live_database_authorized():
            raise DatabaseEnvironmentGuardError(
                "Live database connection rejected by PostgreSQL Environment Guard: "
                "No live PostgreSQL 16 instance authorized. Set PVRE_AUTHORIZED_PG16_DB=1 "
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
                state.clear_staging()
                state.in_transaction = True
                state.transaction_snapshot = {
                    "outputs": copy.deepcopy(self._outputs),
                    "dossiers": copy.deepcopy(self._dossiers),
                    "candidate_evidence": copy.deepcopy(self._candidate_evidence),
                    "claims": copy.deepcopy(self._claims),
                    "conflicts": copy.deepcopy(self._conflicts),
                    "derived_features": copy.deepcopy(self._derived_features),
                }

    begin_transaction = begin

    def commit(self) -> None:
        """Commit active transaction, making staged changes persistent."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        if self._db_client is not None and hasattr(self._db_client, "commit"):
            self._db_client.commit()

        with self._lock:
            state = self._get_thread_state()
            if state.in_transaction:
                # Apply staged deletes across stores
                for rec_id in state.staged_deletes:
                    self._outputs.pop(rec_id, None)
                    self._dossiers.pop(rec_id, None)
                    self._candidate_evidence.pop(rec_id, None)
                    self._claims.pop(rec_id, None)
                    self._conflicts.pop(rec_id, None)
                    self._derived_features.pop(rec_id, None)

                # Apply staged inserts to corresponding store
                self._outputs.update(state.staged_outputs)
                self._dossiers.update(state.staged_dossiers)
                self._candidate_evidence.update(state.staged_evidence)
                self._claims.update(state.staged_claims)
                self._conflicts.update(state.staged_conflicts)
                self._derived_features.update(state.staged_derived_features)

                state.clear_staging()

    commit_transaction = commit

    def rollback(self) -> None:
        """Roll back active transaction, discarding staged changes without residue."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        if self._db_client is not None and hasattr(self._db_client, "rollback"):
            self._db_client.rollback()

        with self._lock:
            state = self._get_thread_state()
            if state.in_transaction:
                state.clear_staging()

    rollback_transaction = rollback

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
                copy.deepcopy(state.staged_outputs),
                copy.deepcopy(state.staged_dossiers),
                copy.deepcopy(state.staged_evidence),
                copy.deepcopy(state.staged_claims),
                copy.deepcopy(state.staged_conflicts),
                copy.deepcopy(state.staged_derived_features),
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
                (
                    staged_out,
                    staged_dos,
                    staged_evi,
                    staged_clm,
                    staged_cnf,
                    staged_df,
                    staged_del,
                ) = state.savepoints[name]
                state.staged_outputs = copy.deepcopy(staged_out)
                state.staged_dossiers = copy.deepcopy(staged_dos)
                state.staged_evidence = copy.deepcopy(staged_evi)
                state.staged_claims = copy.deepcopy(staged_clm)
                state.staged_conflicts = copy.deepcopy(staged_cnf)
                state.staged_derived_features = copy.deepcopy(staged_df)
                state.staged_deletes = copy.deepcopy(staged_del)

    # -------------------------------------------------------------------------
    # Parameterized SQL & Injection Resilience
    # -------------------------------------------------------------------------

    def execute_parameterized(
        self,
        sql: str,
        params: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> Any:
        """Execute SQL verifying strict parameterization and detecting injection vectors.

        Args:
            sql: Parameterized SQL statement string.
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
        is_unparameterized = params is None or (isinstance(params, (tuple, list, dict)) and len(params) == 0)
        if is_unparameterized:
            for pattern in RAW_INJECTION_PATTERNS:
                if re.search(pattern, sql, re.IGNORECASE):
                    raise ValueError(f"SQL Injection vector detected in unparameterized query: {sql}")

        if self._db_client is not None and hasattr(self._db_client, "execute"):
            return self._db_client.execute(sql, params)

        return True

    # -------------------------------------------------------------------------
    # CRUD: PVRE Output Contract
    # -------------------------------------------------------------------------

    def save_research_output(
        self,
        output: PVREOutputContract | dict[str, Any],
    ) -> dict[str, Any]:
        """Save a PVREOutputContract record to repository store."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        row: dict[str, Any] = output.model_dump() if isinstance(output, PVREOutputContract) else dict(output)
        run_id = row["research_run_id"]
        if isinstance(run_id, str):
            run_id = UUID(run_id)
            row["research_run_id"] = run_id

        # Parameterized query execution audit
        param_sql = (
            "INSERT INTO pvre_research_outputs "
            "(research_run_id, player_id, canonical_name, research_mode, route_status, review_status) "
            "VALUES ($1, $2, $3, $4, $5, $6) "
            "ON CONFLICT (research_run_id) DO UPDATE SET "
            "route_status = EXCLUDED.route_status, review_status = EXCLUDED.review_status"
        )
        self.execute_parameterized(
            param_sql,
            (
                str(run_id),
                str(row.get("player_id")) if row.get("player_id") else None,
                row.get("canonical_name"),
                row.get("research_mode"),
                row.get("route_status"),
                row.get("review_status"),
            ),
        )

        with self._lock:
            state = self._get_thread_state()
            if state.in_transaction:
                state.staged_outputs[run_id] = copy.deepcopy(row)
                state.staged_deletes.discard(run_id)
            else:
                self._outputs[run_id] = copy.deepcopy(row)

            # Persist derived features entry (feature_set_name = 'pvre_replacement_assessment')
            if row.get("replaceability_assessment"):
                self._save_derived_feature(
                    feature_set_name="pvre_replacement_assessment",
                    entity_id=run_id,
                    feature_payload=row["replaceability_assessment"],
                )

        return row

    def get_research_output(self, research_run_id: UUID | str) -> PVREOutputContract | None:
        """Retrieve PVREOutputContract by research_run_id."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        uid = UUID(str(research_run_id))
        param_sql = "SELECT * FROM pvre_research_outputs WHERE research_run_id = $1"
        self.execute_parameterized(param_sql, (str(uid),))

        with self._lock:
            state = self._get_thread_state()
            visible = self._get_visible_store(self._outputs, state.staged_outputs)
            if uid in visible:
                return PVREOutputContract(**visible[uid])

            if self._db_client is not None and hasattr(self._db_client, "select"):
                rows = self._db_client.select("pvre_research_outputs", research_run_id=uid)
                if rows:
                    return PVREOutputContract(**rows[0])

            return None

    # -------------------------------------------------------------------------
    # CRUD: Review Dossier Contract
    # -------------------------------------------------------------------------

    def save_review_dossier(
        self,
        dossier: ReviewDossierContract | dict[str, Any],
    ) -> dict[str, Any]:
        """Save a ReviewDossierContract record to repository store."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        row: dict[str, Any] = dossier.model_dump() if isinstance(dossier, ReviewDossierContract) else dict(dossier)
        dossier_id = row["dossier_id"]
        if isinstance(dossier_id, str):
            dossier_id = UUID(dossier_id)
            row["dossier_id"] = dossier_id

        param_sql = (
            "INSERT INTO pvre_review_dossiers "
            "(dossier_id, subject_id, review_status, contract_version) "
            "VALUES ($1, $2, $3, $4)"
        )
        self.execute_parameterized(
            param_sql,
            (
                str(dossier_id),
                str(row.get("subject_id")) if row.get("subject_id") else None,
                row.get("review_status"),
                row.get("contract_version"),
            ),
        )

        with self._lock:
            state = self._get_thread_state()
            if state.in_transaction:
                state.staged_dossiers[dossier_id] = copy.deepcopy(row)
                state.staged_deletes.discard(dossier_id)
            else:
                self._dossiers[dossier_id] = copy.deepcopy(row)

        return row

    def get_review_dossier(self, dossier_id: UUID | str) -> ReviewDossierContract | None:
        """Retrieve ReviewDossierContract by dossier_id."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        uid = UUID(str(dossier_id))
        param_sql = "SELECT * FROM pvre_review_dossiers WHERE dossier_id = $1"
        self.execute_parameterized(param_sql, (str(uid),))

        with self._lock:
            state = self._get_thread_state()
            visible = self._get_visible_store(self._dossiers, state.staged_dossiers)
            if uid in visible:
                return ReviewDossierContract(**visible[uid])

            if self._db_client is not None and hasattr(self._db_client, "select"):
                rows = self._db_client.select("pvre_review_dossiers", dossier_id=uid)
                if rows:
                    return ReviewDossierContract(**rows[0])

            return None

    # -------------------------------------------------------------------------
    # CRUD: Replacement Candidate Evidence Contract
    # -------------------------------------------------------------------------

    def save_candidate_evidence(
        self,
        evidence: ReplacementCandidateEvidence | dict[str, Any],
    ) -> dict[str, Any]:
        """Save a ReplacementCandidateEvidence record to repository store."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        row: dict[str, Any] = (
            evidence.model_dump() if isinstance(evidence, ReplacementCandidateEvidence) else dict(evidence)
        )
        candidate_id = row["candidate_player_id"]
        if isinstance(candidate_id, str):
            candidate_id = UUID(candidate_id)
            row["candidate_player_id"] = candidate_id

        param_sql = (
            "INSERT INTO replacement_candidate_evidence "
            "(candidate_player_id, canonical_name, primary_role, age_at_evaluation, ipl_uncapped_eligibility) "
            "VALUES ($1, $2, $3, $4, $5)"
        )
        self.execute_parameterized(
            param_sql,
            (
                str(candidate_id),
                row.get("canonical_name"),
                row.get("primary_role"),
                float(row.get("age_at_evaluation", 0.0)),
                row.get("ipl_uncapped_eligibility"),
            ),
        )

        with self._lock:
            state = self._get_thread_state()
            if state.in_transaction:
                state.staged_evidence[candidate_id] = copy.deepcopy(row)
                state.staged_deletes.discard(candidate_id)
            else:
                self._candidate_evidence[candidate_id] = copy.deepcopy(row)

        return row

    def get_candidate_evidence(self, candidate_player_id: UUID | str) -> ReplacementCandidateEvidence | None:
        """Retrieve ReplacementCandidateEvidence by candidate_player_id."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        uid = UUID(str(candidate_player_id))
        param_sql = "SELECT * FROM replacement_candidate_evidence WHERE candidate_player_id = $1"
        self.execute_parameterized(param_sql, (str(uid),))

        with self._lock:
            state = self._get_thread_state()
            visible = self._get_visible_store(self._candidate_evidence, state.staged_evidence)
            if uid in visible:
                return ReplacementCandidateEvidence(**visible[uid])

            if self._db_client is not None and hasattr(self._db_client, "select"):
                rows = self._db_client.select("replacement_candidate_evidence", candidate_player_id=uid)
                if rows:
                    return ReplacementCandidateEvidence(**rows[0])

            return None

    # -------------------------------------------------------------------------
    # CRUD: Claims & Conflicts
    # -------------------------------------------------------------------------

    def save_claim(self, claim: VerificationClaim | dict[str, Any]) -> dict[str, Any]:
        """Save a VerificationClaim record to repository store."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        row: dict[str, Any] = claim.model_dump() if isinstance(claim, VerificationClaim) else dict(claim)
        claim_id = row["claim_id"]
        if isinstance(claim_id, str):
            claim_id = UUID(claim_id)
            row["claim_id"] = claim_id

        with self._lock:
            state = self._get_thread_state()
            if state.in_transaction:
                state.staged_claims[claim_id] = copy.deepcopy(row)
                state.staged_deletes.discard(claim_id)
            else:
                self._claims[claim_id] = copy.deepcopy(row)

        return row

    def get_claim(self, claim_id: UUID | str) -> VerificationClaim | None:
        """Retrieve VerificationClaim by claim_id."""
        uid = UUID(str(claim_id))
        with self._lock:
            state = self._get_thread_state()
            visible = self._get_visible_store(self._claims, state.staged_claims)
            if uid in visible:
                return VerificationClaim(**visible[uid])
            return None

    def save_conflict(self, conflict: ResearchConflict | dict[str, Any]) -> dict[str, Any]:
        """Save a ResearchConflict record to repository store."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        row: dict[str, Any] = conflict.model_dump() if isinstance(conflict, ResearchConflict) else dict(conflict)
        conflict_id = row["conflict_id"]
        if isinstance(conflict_id, str):
            conflict_id = UUID(conflict_id)
            row["conflict_id"] = conflict_id

        with self._lock:
            state = self._get_thread_state()
            if state.in_transaction:
                state.staged_conflicts[conflict_id] = copy.deepcopy(row)
                state.staged_deletes.discard(conflict_id)
            else:
                self._conflicts[conflict_id] = copy.deepcopy(row)

        return row

    def get_conflict(self, conflict_id: UUID | str) -> ResearchConflict | None:
        """Retrieve ResearchConflict by conflict_id."""
        uid = UUID(str(conflict_id))
        with self._lock:
            state = self._get_thread_state()
            visible = self._get_visible_store(self._conflicts, state.staged_conflicts)
            if uid in visible:
                return ResearchConflict(**visible[uid])
            return None

    # -------------------------------------------------------------------------
    # Internal: Derived Features Helper
    # -------------------------------------------------------------------------

    def _save_derived_feature(
        self,
        feature_set_name: str,
        entity_id: UUID,
        feature_payload: dict[str, Any],
    ) -> None:
        """Internal helper persisting derived feature sets."""
        row = {
            "feature_id": entity_id,
            "feature_set_name": feature_set_name,
            "entity_id": entity_id,
            "payload": feature_payload,
            "created_at": datetime.now(UTC),
        }
        state = self._get_thread_state()
        if state.in_transaction:
            state.staged_derived_features[entity_id] = copy.deepcopy(row)
        else:
            self._derived_features[entity_id] = row

    # -------------------------------------------------------------------------
    # Batch Persistence with Rollback Atomicity
    # -------------------------------------------------------------------------

    def save_batch(
        self,
        records: list[Any],
        fail_index: int | None = None,
    ) -> list[dict[str, Any]]:
        """Save a batch of records atomically within an explicit transaction boundary.

        Args:
            records: List of contract instances or row dictionaries to persist.
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

                if isinstance(rec, PVREOutputContract) or (
                    isinstance(rec, dict) and "research_run_id" in rec and "route_status" in rec
                ):
                    row = self.save_research_output(rec)
                elif isinstance(rec, ReviewDossierContract) or (
                    isinstance(rec, dict) and "dossier_id" in rec
                ):
                    row = self.save_review_dossier(rec)
                elif isinstance(rec, ReplacementCandidateEvidence) or (
                    isinstance(rec, dict) and "candidate_player_id" in rec
                ):
                    row = self.save_candidate_evidence(rec)
                elif isinstance(rec, VerificationClaim) or (
                    isinstance(rec, dict) and "claim_id" in rec
                ):
                    row = self.save_claim(rec)
                elif isinstance(rec, ResearchConflict) or (
                    isinstance(rec, dict) and "conflict_id" in rec
                ):
                    row = self.save_conflict(rec)
                else:
                    # Fallback generic insert
                    row = self.save_research_output(rec)

                saved.append(row)

            self.commit()
            return saved
        except Exception:
            self.rollback()
            raise

    # -------------------------------------------------------------------------
    # General Operations & Cleanup
    # -------------------------------------------------------------------------

    def delete_record(self, record_id: UUID | str) -> bool:
        """Delete a record by identifier across visible stores."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        uid = UUID(str(record_id))
        param_sql = "DELETE FROM pvre_records WHERE id = $1"
        self.execute_parameterized(param_sql, (str(uid),))

        with self._lock:
            state = self._get_thread_state()
            if state.in_transaction:
                found = False
                for staged_dict in (
                    state.staged_outputs,
                    state.staged_dossiers,
                    state.staged_evidence,
                    state.staged_claims,
                    state.staged_conflicts,
                    state.staged_derived_features,
                ):
                    if uid in staged_dict:
                        del staged_dict[uid]
                        found = True
                for store in (
                    self._outputs,
                    self._dossiers,
                    self._candidate_evidence,
                    self._claims,
                    self._conflicts,
                    self._derived_features,
                ):
                    if uid in store:
                        state.staged_deletes.add(uid)
                        found = True
                return found

            deleted = False
            for store in (
                self._outputs,
                self._dossiers,
                self._candidate_evidence,
                self._claims,
                self._conflicts,
                self._derived_features,
            ):
                if uid in store:
                    del store[uid]
                    deleted = True
            return deleted

    def count(self) -> int:
        """Return total number of records currently stored / visible to this thread."""
        with self._lock:
            state = self._get_thread_state()
            outputs = len(self._get_visible_store(self._outputs, state.staged_outputs))
            dossiers = len(self._get_visible_store(self._dossiers, state.staged_dossiers))
            evidence = len(self._get_visible_store(self._candidate_evidence, state.staged_evidence))
            claims = len(self._get_visible_store(self._claims, state.staged_claims))
            conflicts = len(self._get_visible_store(self._conflicts, state.staged_conflicts))
            return outputs + dossiers + evidence + claims + conflicts

    def clear(self) -> None:
        """Clear all stored records and thread staging state (useful for test isolation)."""
        with self._lock:
            self._outputs.clear()
            self._dossiers.clear()
            self._candidate_evidence.clear()
            self._claims.clear()
            self._conflicts.clear()
            self._derived_features.clear()
            self._get_thread_state().clear_staging()
            self.executed_queries.clear()


__all__ = [
    "PVRERepository",
    "RepositoryMode",
    "DatabaseEnvironmentGuardError",
    "PG16_AUTH_ENV_VAR",
    "RAW_INJECTION_PATTERNS",
]
