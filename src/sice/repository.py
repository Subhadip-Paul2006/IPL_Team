"""Dual-Mode Persistence Repository for Squad Intelligence & Composition Engine (SICE).

Part of Phase 06 — SICE (Milestone 2: Service E & Persistence Engine).
Provides dual-mode persistence (In-Memory for offline testing and Database Adapter for
PostgreSQL 16), thread-isolated transaction staging with savepoints and atomic rollback,
parameterized SQL query injection resilience, and PostgreSQL Environment Guard governance.

PostgreSQL Environment Guard:
- Default mode is IN_MEMORY for hermetic offline testing.
- Never connects to native PostgreSQL on port 5432 or starts Docker containers.
- Live database operations verify environment authorization via SICE_AUTHORIZED_PG16_DB.
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

from src.contracts.features import DerivedFeature
from src.contracts.ranking import RankingConfiguration, RankingRun
from src.contracts.team_builder import UserTeam, UserTeamPlayer
from src.sice.exceptions import DatabaseEnvironmentGuardError

logger = logging.getLogger(__name__)

# Environment variable controlling live PostgreSQL 16 database authorization
PG16_AUTH_ENV_VAR = "SICE_AUTHORIZED_PG16_DB"


class RepositoryMode(StrEnum):
    """Operational persistence mode for SICERepository."""

    IN_MEMORY = "IN_MEMORY"
    DATABASE = "DATABASE"


class _ThreadTransactionState:
    """Thread-local transaction staging state for in-memory concurrency isolation."""

    def __init__(self) -> None:
        self.in_transaction: bool = False
        self.staged_teams: dict[UUID, dict[str, Any]] = {}
        self.staged_team_players: dict[UUID, dict[str, Any]] = {}
        self.staged_ranking_configs: dict[UUID, dict[str, Any]] = {}
        self.staged_ranking_runs: dict[UUID, dict[str, Any]] = {}
        self.staged_derived_features: dict[UUID, dict[str, Any]] = {}
        self.staged_deletes: set[UUID] = set()
        self.savepoints: dict[str, Any] = {}
        self.transaction_snapshot: dict[str, Any] | None = None

    def clear_staging(self) -> None:
        """Clear all thread-staged changes and reset transaction boundary."""
        self.staged_teams.clear()
        self.staged_team_players.clear()
        self.staged_ranking_configs.clear()
        self.staged_ranking_runs.clear()
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
    r"--.*$",
    r"/\*.*?\*/",
    r"\bUNION\s+(?:ALL\s+)?SELECT\b",
    r"'\s*UNION\s+(?:ALL\s+)?SELECT\b",
]


class SICERepository:
    """Dual-mode transactional repository for SICE entities and team composition.

    Persists:
    - User teams (TRD Entity 29: user_teams)
    - User team player assignments (TRD Entity 30: user_team_players)
    - Analytical derived features (TRD Entity 31: derived_features)
    - Ranking configurations (TRD Entity 32: ranking_configurations)
    - Ranking execution runs (TRD Entity 33: ranking_runs)

    Guarantees:
    - Default mode is IN_MEMORY for hermetic offline testing.
    - PostgreSQL Environment Guard rejects unauthorized live database access on port 5432.
    - Thread-isolated transaction staging using RLock and threading.local().
    - Transaction rollback atomicity (zero persistent residue on failure).
    - Savepoint support for partial transaction rollbacks.
    - Parameterized SQL enforcement detecting and rejecting injection vectors.
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

        # In-memory primary stores
        self._teams: dict[UUID, dict[str, Any]] = {}
        self._team_players: dict[UUID, dict[str, Any]] = {}
        self._ranking_configs: dict[UUID, dict[str, Any]] = {}
        self._ranking_runs: dict[UUID, dict[str, Any]] = {}
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

    @staticmethod
    def _parse_uuid(val: UUID | str | None) -> UUID | None:
        """Safely parse UUID instance or string, returning None on invalid format."""
        if val is None:
            return None
        if isinstance(val, UUID):
            return val
        try:
            return UUID(str(val))
        except (ValueError, AttributeError, TypeError):
            return None

    @property
    def in_transaction(self) -> bool:
        """Whether calling thread is within an active transaction."""
        return self._get_thread_state().in_transaction

    def _get_visible_store(
        self,
        base_store: dict[UUID, dict[str, Any]],
        staged_dict: dict[UUID, dict[str, Any]],
    ) -> dict[UUID, dict[str, Any]]:
        """Return store view visible to calling thread incorporating staged mutations."""
        with self._lock:
            state = self._get_thread_state()
            if not state.in_transaction:
                return dict(base_store)

            visible = {
                k: copy.deepcopy(v) for k, v in base_store.items() if k not in state.staged_deletes
            }
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
                "No live PostgreSQL 16 instance authorized. Set SICE_AUTHORIZED_PG16_DB=1 "
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
                    "teams": copy.deepcopy(self._teams),
                    "team_players": copy.deepcopy(self._team_players),
                    "ranking_configs": copy.deepcopy(self._ranking_configs),
                    "ranking_runs": copy.deepcopy(self._ranking_runs),
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
                for rec_id in state.staged_deletes:
                    self._teams.pop(rec_id, None)
                    self._team_players.pop(rec_id, None)
                    self._ranking_configs.pop(rec_id, None)
                    self._ranking_runs.pop(rec_id, None)
                    self._derived_features.pop(rec_id, None)

                self._teams.update(state.staged_teams)
                self._team_players.update(state.staged_team_players)
                self._ranking_configs.update(state.staged_ranking_configs)
                self._ranking_runs.update(state.staged_ranking_runs)
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
                copy.deepcopy(state.staged_teams),
                copy.deepcopy(state.staged_team_players),
                copy.deepcopy(state.staged_ranking_configs),
                copy.deepcopy(state.staged_ranking_runs),
                copy.deepcopy(state.staged_derived_features),
                copy.deepcopy(state.staged_deletes),
            )

    def rollback_to(self, name: str) -> None:
        """Roll back transaction state to a previously established savepoint."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        with self._lock:
            if self._db_client is not None and hasattr(self._db_client, "rollback_to"):
                self._db_client.rollback_to(name)

            state = self._get_thread_state()
            if name not in state.savepoints:
                raise KeyError(f"Savepoint '{name}' does not exist in active transaction")

            (
                staged_teams,
                staged_team_players,
                staged_ranking_configs,
                staged_ranking_runs,
                staged_derived_features,
                staged_deletes,
            ) = state.savepoints[name]
            state.staged_teams = copy.deepcopy(staged_teams)
            state.staged_team_players = copy.deepcopy(staged_team_players)
            state.staged_ranking_configs = copy.deepcopy(staged_ranking_configs)
            state.staged_ranking_runs = copy.deepcopy(staged_ranking_runs)
            state.staged_derived_features = copy.deepcopy(staged_derived_features)
            state.staged_deletes = copy.deepcopy(staged_deletes)

    def release_savepoint(self, name: str) -> None:
        """Release a previously established savepoint."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        with self._lock:
            if self._db_client is not None and hasattr(self._db_client, "release_savepoint"):
                self._db_client.release_savepoint(name)

            state = self._get_thread_state()
            if name not in state.savepoints:
                raise KeyError(f"Savepoint '{name}' does not exist in active transaction")
            state.savepoints.pop(name, None)

    # -------------------------------------------------------------------------
    # Parameterized SQL & Injection Resilience
    # -------------------------------------------------------------------------

    def execute_parameterized(
        self,
        sql: str,
        params: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> bool:
        """Execute parameterized SQL statement, validating against injection vectors."""
        if self.mode == RepositoryMode.DATABASE:
            self._assert_database_access_allowed()

        with self._lock:
            self.executed_queries.append(
                {
                    "sql": sql,
                    "params": params,
                    "ts": datetime.now(UTC),
                }
            )

        # Reject raw unparameterized injection patterns
        is_unparameterized = params is None or (
            isinstance(params, (tuple, list, dict)) and len(params) == 0
        )
        if is_unparameterized:
            for pattern in RAW_INJECTION_PATTERNS:
                if re.search(pattern, sql, re.IGNORECASE):
                    raise ValueError(
                        f"SQL Injection vector detected in unparameterized query: {sql}"
                    )

        if self._db_client is not None and hasattr(self._db_client, "execute"):
            return bool(self._db_client.execute(sql, params))

        return True

    # -------------------------------------------------------------------------
    # UserTeam (Entity 29) Persistence
    # -------------------------------------------------------------------------

    def save_team(self, team: UserTeam | dict[str, Any]) -> UserTeam:
        """Persist or update a user team record."""
        team_obj = team if isinstance(team, UserTeam) else UserTeam.model_validate(team)
        team_dict = team_obj.model_dump()
        team_id = team_obj.team_id

        with self._lock:
            state = self._get_thread_state()
            if state.in_transaction:
                state.staged_deletes.discard(team_id)
                state.staged_teams[team_id] = team_dict
            else:
                self._teams[team_id] = team_dict

        return team_obj

    def get_team(self, team_id: UUID | str) -> UserTeam | None:
        """Retrieve a user team by its primary identifier."""
        uid = self._parse_uuid(team_id)
        if uid is None:
            return None
        visible = self._get_visible_store(self._teams, self._get_thread_state().staged_teams)
        data = visible.get(uid)
        return UserTeam.model_validate(data) if data is not None else None

    def list_teams(
        self,
        limit: int = 100,
        offset: int = 0,
        created_by: str | None = None,
        target_season: str | None = None,
    ) -> list[UserTeam]:
        """Fetch user teams with optional filtering and pagination."""
        visible = self._get_visible_store(self._teams, self._get_thread_state().staged_teams)
        results: list[UserTeam] = []
        for team_dict in visible.values():
            if created_by is not None and team_dict.get("created_by") != created_by:
                continue
            if target_season is not None and team_dict.get("target_season") != target_season:
                continue
            results.append(UserTeam.model_validate(team_dict))

        results.sort(key=lambda t: (t.created_at, t.team_id))
        return results[offset : offset + limit]

    def delete_team(self, team_id: UUID | str) -> bool:
        """Delete a user team and cascade deletion to its assigned players."""
        uid = self._parse_uuid(team_id)
        if uid is None:
            return False
        visible_teams = self._get_visible_store(self._teams, self._get_thread_state().staged_teams)
        if uid not in visible_teams:
            return False

        # Identify all assigned player records for cascade deletion
        visible_players = self._get_visible_store(
            self._team_players, self._get_thread_state().staged_team_players
        )
        player_ids_to_delete = [
            p_id for p_id, p_data in visible_players.items() if p_data.get("user_team_id") == uid
        ]

        with self._lock:
            state = self._get_thread_state()
            if state.in_transaction:
                state.staged_deletes.add(uid)
                state.staged_teams.pop(uid, None)
                for p_id in player_ids_to_delete:
                    state.staged_deletes.add(p_id)
                    state.staged_team_players.pop(p_id, None)
            else:
                self._teams.pop(uid, None)
                for p_id in player_ids_to_delete:
                    self._team_players.pop(p_id, None)

        return True

    # -------------------------------------------------------------------------
    # UserTeamPlayer (Entity 30) Persistence
    # -------------------------------------------------------------------------

    def save_team_player(self, player: UserTeamPlayer | dict[str, Any]) -> UserTeamPlayer:
        """Persist or update a player assignment in a user team."""
        player_obj = (
            player if isinstance(player, UserTeamPlayer) else UserTeamPlayer.model_validate(player)
        )
        player_dict = player_obj.model_dump()
        entry_id = player_obj.id

        with self._lock:
            state = self._get_thread_state()
            if state.in_transaction:
                state.staged_deletes.discard(entry_id)
                state.staged_team_players[entry_id] = player_dict
            else:
                self._team_players[entry_id] = player_dict

        return player_obj

    def get_team_player(self, entry_id: UUID | str) -> UserTeamPlayer | None:
        """Retrieve a specific team player assignment entry by ID."""
        uid = self._parse_uuid(entry_id)
        if uid is None:
            return None
        visible = self._get_visible_store(
            self._team_players, self._get_thread_state().staged_team_players
        )
        data = visible.get(uid)
        return UserTeamPlayer.model_validate(data) if data is not None else None

    def get_team_players(self, team_id: UUID | str) -> list[UserTeamPlayer]:
        """Retrieve all player assignments belonging to a given user team."""
        uid = self._parse_uuid(team_id)
        if uid is None:
            return []
        visible = self._get_visible_store(
            self._team_players, self._get_thread_state().staged_team_players
        )
        players = [
            UserTeamPlayer.model_validate(p)
            for p in visible.values()
            if p.get("user_team_id") == uid
        ]
        players.sort(key=lambda p: (p.batting_order or 99, p.added_at, p.id))
        return players

    def get_team_player_by_player_id(
        self,
        team_id: UUID | str,
        player_id: UUID | str,
    ) -> UserTeamPlayer | None:
        """Retrieve a player assignment by composite key (team_id, player_id)."""
        team_uid = self._parse_uuid(team_id)
        player_uid = self._parse_uuid(player_id)
        if team_uid is None or player_uid is None:
            return None
        visible = self._get_visible_store(
            self._team_players, self._get_thread_state().staged_team_players
        )
        for data in visible.values():
            if data.get("user_team_id") == team_uid and data.get("player_id") == player_uid:
                return UserTeamPlayer.model_validate(data)
        return None

    def delete_team_player(self, entry_id: UUID | str) -> bool:
        """Remove a player assignment by entry ID."""
        uid = self._parse_uuid(entry_id)
        if uid is None:
            return False
        visible = self._get_visible_store(
            self._team_players, self._get_thread_state().staged_team_players
        )
        if uid not in visible:
            return False

        with self._lock:
            state = self._get_thread_state()
            if state.in_transaction:
                state.staged_deletes.add(uid)
                state.staged_team_players.pop(uid, None)
            else:
                self._team_players.pop(uid, None)

        return True

    def delete_team_player_by_player_id(
        self,
        team_id: UUID | str,
        player_id: UUID | str,
    ) -> bool:
        """Remove a player assignment by composite key (team_id, player_id)."""
        entry = self.get_team_player_by_player_id(team_id, player_id)
        if entry is None:
            return False
        return self.delete_team_player(entry.id)

    # -------------------------------------------------------------------------
    # RankingConfiguration (Entity 32) & RankingRun (Entity 33) Persistence
    # -------------------------------------------------------------------------

    def save_ranking_configuration(
        self,
        config: RankingConfiguration | dict[str, Any],
    ) -> RankingConfiguration:
        """Persist a ranking configuration specification."""
        cfg_obj = (
            config
            if isinstance(config, RankingConfiguration)
            else RankingConfiguration.model_validate(config)
        )
        cfg_dict = cfg_obj.model_dump()
        cfg_id = cfg_obj.config_id

        with self._lock:
            state = self._get_thread_state()
            if state.in_transaction:
                state.staged_deletes.discard(cfg_id)
                state.staged_ranking_configs[cfg_id] = cfg_dict
            else:
                self._ranking_configs[cfg_id] = cfg_dict

        return cfg_obj

    def get_ranking_configuration(self, config_id: UUID | str) -> RankingConfiguration | None:
        """Retrieve a ranking configuration by its UUID."""
        uid = self._parse_uuid(config_id)
        if uid is None:
            return None
        visible = self._get_visible_store(
            self._ranking_configs, self._get_thread_state().staged_ranking_configs
        )
        data = visible.get(uid)
        return RankingConfiguration.model_validate(data) if data is not None else None

    def get_ranking_configuration_by_version(
        self,
        config_version: str,
    ) -> RankingConfiguration | None:
        """Retrieve a ranking configuration by version code (e.g. 'RK-1.0.0')."""
        visible = self._get_visible_store(
            self._ranking_configs, self._get_thread_state().staged_ranking_configs
        )
        for data in visible.values():
            if data.get("config_version") == config_version:
                return RankingConfiguration.model_validate(data)
        return None

    def save_ranking_run(self, run: RankingRun | dict[str, Any]) -> RankingRun:
        """Persist a frozen ranking run record."""
        run_obj = run if isinstance(run, RankingRun) else RankingRun.model_validate(run)
        run_dict = run_obj.model_dump()
        run_id = run_obj.run_id

        with self._lock:
            state = self._get_thread_state()
            if state.in_transaction:
                state.staged_deletes.discard(run_id)
                state.staged_ranking_runs[run_id] = run_dict
            else:
                self._ranking_runs[run_id] = run_dict

        return run_obj

    def get_ranking_run(self, run_id: UUID | str) -> RankingRun | None:
        """Retrieve a ranking run record by UUID."""
        uid = self._parse_uuid(run_id)
        if uid is None:
            return None
        visible = self._get_visible_store(
            self._ranking_runs, self._get_thread_state().staged_ranking_runs
        )
        data = visible.get(uid)
        return RankingRun.model_validate(data) if data is not None else None

    def list_ranking_runs(
        self,
        config_id: UUID | str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RankingRun]:
        """List ranking runs, optionally filtered by config_id."""
        cfg_uuid = self._parse_uuid(config_id) if config_id is not None else None
        if config_id is not None and cfg_uuid is None:
            return []
        visible = self._get_visible_store(
            self._ranking_runs, self._get_thread_state().staged_ranking_runs
        )
        results: list[RankingRun] = []
        for run_dict in visible.values():
            if cfg_uuid is not None and run_dict.get("config_id") != cfg_uuid:
                continue
            results.append(RankingRun.model_validate(run_dict))

        results.sort(key=lambda r: (r.computed_at, r.run_id))
        return results[offset : offset + limit]

    # -------------------------------------------------------------------------
    # DerivedFeature (Entity 31) Persistence
    # -------------------------------------------------------------------------

    def save_derived_feature(
        self,
        feature: DerivedFeature | dict[str, Any],
    ) -> DerivedFeature:
        """Persist an analytical squad intelligence derived feature."""
        feat_obj = (
            feature
            if isinstance(feature, DerivedFeature)
            else DerivedFeature.model_validate(feature)
        )
        feat_dict = feat_obj.model_dump()
        feat_id = feat_obj.feature_id

        with self._lock:
            state = self._get_thread_state()
            if state.in_transaction:
                state.staged_deletes.discard(feat_id)
                state.staged_derived_features[feat_id] = feat_dict
            else:
                self._derived_features[feat_id] = feat_dict

        return feat_obj

    def get_derived_feature(self, feature_id: UUID | str) -> DerivedFeature | None:
        """Retrieve a derived feature by UUID."""
        uid = self._parse_uuid(feature_id)
        if uid is None:
            return None
        visible = self._get_visible_store(
            self._derived_features, self._get_thread_state().staged_derived_features
        )
        data = visible.get(uid)
        return DerivedFeature.model_validate(data) if data is not None else None

    def get_derived_features_by_player(
        self,
        player_id: UUID | str,
        feature_group: str | None = None,
    ) -> list[DerivedFeature]:
        """Retrieve derived features for a player, optionally filtered by feature group."""
        p_uid = self._parse_uuid(player_id)
        if p_uid is None:
            return []
        visible = self._get_visible_store(
            self._derived_features, self._get_thread_state().staged_derived_features
        )
        features: list[DerivedFeature] = []
        for data in visible.values():
            if data.get("player_id") == p_uid:
                if feature_group is not None and data.get("feature_group") != feature_group:
                    continue
                features.append(DerivedFeature.model_validate(data))
        features.sort(key=lambda f: (f.computed_at, f.feature_id))
        return features

    # -------------------------------------------------------------------------
    # Batch & General Operations
    # -------------------------------------------------------------------------

    def save_batch(self, records: list[Any], fail_index: int | None = None) -> list[Any]:
        """Atomically persist a batch of records, rolling back on any failure."""
        already_in_tx = self.in_transaction
        if not already_in_tx:
            self.begin()
        else:
            self.savepoint("_save_batch_sp")

        saved: list[Any] = []
        try:
            for idx, record in enumerate(records):
                if fail_index is not None and idx == fail_index:
                    raise RuntimeError(f"Simulated failure in save_batch at index {idx}")

                if isinstance(record, UserTeam) or (
                    isinstance(record, dict)
                    and "team_name" in record
                    and "user_team_id" not in record
                    and "feature_group" not in record
                    and "config_version" not in record
                    and "data_snapshot_sha256" not in record
                ):
                    saved.append(self.save_team(record))
                elif isinstance(record, UserTeamPlayer) or (
                    isinstance(record, dict) and "user_team_id" in record and "player_id" in record
                ):
                    saved.append(self.save_team_player(record))
                elif isinstance(record, DerivedFeature) or (
                    isinstance(record, dict) and "feature_group" in record
                ):
                    saved.append(self.save_derived_feature(record))
                elif isinstance(record, RankingConfiguration) or (
                    isinstance(record, dict) and "config_version" in record
                ):
                    saved.append(self.save_ranking_configuration(record))
                elif isinstance(record, RankingRun) or (
                    isinstance(record, dict) and "data_snapshot_sha256" in record
                ):
                    saved.append(self.save_ranking_run(record))
                else:
                    raise ValueError(f"Unknown record type in save_batch: {type(record)}")

            if not already_in_tx:
                self.commit()
            else:
                self.release_savepoint("_save_batch_sp")
            return saved
        except Exception:
            if not already_in_tx:
                self.rollback()
            else:
                self.rollback_to("_save_batch_sp")
                self.release_savepoint("_save_batch_sp")
            raise

    def delete_record(self, record_id: UUID | str) -> bool:
        """Delete any entity record across visible stores by primary key."""
        uid = self._parse_uuid(record_id)
        if uid is None:
            return False
        if self.delete_team(uid):
            return True
        if self.delete_team_player(uid):
            return True

        visible_df = self._get_visible_store(
            self._derived_features, self._get_thread_state().staged_derived_features
        )
        if uid in visible_df:
            with self._lock:
                state = self._get_thread_state()
                if state.in_transaction:
                    state.staged_deletes.add(uid)
                    state.staged_derived_features.pop(uid, None)
                else:
                    self._derived_features.pop(uid, None)
            return True

        visible_rc = self._get_visible_store(
            self._ranking_configs, self._get_thread_state().staged_ranking_configs
        )
        if uid in visible_rc:
            with self._lock:
                state = self._get_thread_state()
                if state.in_transaction:
                    state.staged_deletes.add(uid)
                    state.staged_ranking_configs.pop(uid, None)
                else:
                    self._ranking_configs.pop(uid, None)
            return True

        visible_rr = self._get_visible_store(
            self._ranking_runs, self._get_thread_state().staged_ranking_runs
        )
        if uid in visible_rr:
            with self._lock:
                state = self._get_thread_state()
                if state.in_transaction:
                    state.staged_deletes.add(uid)
                    state.staged_ranking_runs.pop(uid, None)
                else:
                    self._ranking_runs.pop(uid, None)
            return True

        return False

    def count(self, store_name: str | None = None) -> int:
        """Return record count across specified store or all stores combined."""
        state = self._get_thread_state()
        stores = {
            "teams": self._get_visible_store(self._teams, state.staged_teams),
            "user_teams": self._get_visible_store(self._teams, state.staged_teams),
            "team_players": self._get_visible_store(self._team_players, state.staged_team_players),
            "user_team_players": self._get_visible_store(
                self._team_players, state.staged_team_players
            ),
            "derived_features": self._get_visible_store(
                self._derived_features, state.staged_derived_features
            ),
            "ranking_configs": self._get_visible_store(
                self._ranking_configs, state.staged_ranking_configs
            ),
            "ranking_configurations": self._get_visible_store(
                self._ranking_configs, state.staged_ranking_configs
            ),
            "ranking_runs": self._get_visible_store(self._ranking_runs, state.staged_ranking_runs),
        }
        if store_name is not None:
            if store_name in stores:
                return len(stores[store_name])
            raise ValueError(f"Unknown store_name: {store_name}")
        canonical = ["teams", "team_players", "derived_features", "ranking_configs", "ranking_runs"]
        return sum(len(stores[s]) for s in canonical)

    def clear(self) -> None:
        """Clear all in-memory stores and thread-staging states."""
        with self._lock:
            self._teams.clear()
            self._team_players.clear()
            self._derived_features.clear()
            self._ranking_configs.clear()
            self._ranking_runs.clear()
            self.executed_queries.clear()
            self._get_thread_state().clear_staging()
