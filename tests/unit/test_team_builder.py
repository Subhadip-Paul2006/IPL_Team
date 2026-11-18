"""Unit tests for SICE Persistence Repository and Service E TeamBuilderService.

Verifies:
- Suite 1: SICERepository Dual-Mode & PostgreSQL Environment Guard
- Suite 2: SICERepository Transactions, Atomicity & Concurrency Isolation
- Suite 3: SICERepository Entity CRUD & Cascade Deletion (Entities 29-33)
- Suite 4: TeamBuilderService Team Lifecycle Operations
- Suite 5: TeamBuilderService Player Roster Assignment & Constraints
- Suite 6: TeamBuilderService Roster Validation & IPL Governance (HD-05, HD-08, HD-09)
"""

from __future__ import annotations

import threading
from datetime import date, datetime
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from src.contracts.features import DerivedFeature
from src.contracts.ranking import RankingConfiguration, RankingRun
from src.contracts.sice import RosterStatus
from src.contracts.team_builder import UserTeam, UserTeamPlayer
from src.services.base import ServiceBoundary
from src.sice.exceptions import (
    DatabaseEnvironmentGuardError,
    IncompleteRosterError,
    SquadConstraintViolationError,
)
from src.sice.repository import (
    RepositoryMode,
    SICERepository,
)
from src.sice.team_builder import TeamBuilderService

# ==============================================================================
# Suite 1: SICERepository Dual-Mode & PostgreSQL Environment Guard
# ==============================================================================


def test_repository_default_mode_is_in_memory() -> None:
    """Verify repository defaults to IN_MEMORY mode for hermetic offline testing."""
    repo = SICERepository()
    assert repo.mode == RepositoryMode.IN_MEMORY
    assert repo._db_client is None


def test_database_mode_rejects_unauthorized_access(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify DATABASE mode without auth flag or mock client raises DatabaseEnvironmentGuardError."""
    monkeypatch.delenv("SICE_AUTHORIZED_PG16_DB", raising=False)
    repo = SICERepository(mode=RepositoryMode.DATABASE)

    with pytest.raises(DatabaseEnvironmentGuardError) as exc_info:
        repo.begin()
    assert "rejected by PostgreSQL Environment Guard" in str(exc_info.value)
    assert exc_info.value.code == "DATABASE_ENVIRONMENT_GUARD_ERROR"

    with pytest.raises(DatabaseEnvironmentGuardError):
        repo.execute_parameterized("SELECT 1")

    with pytest.raises(DatabaseEnvironmentGuardError):
        repo.commit()

    with pytest.raises(DatabaseEnvironmentGuardError):
        repo.rollback()


def test_database_mode_authorized_via_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify DATABASE mode proceeds when authorized via SICE_AUTHORIZED_PG16_DB environment flag."""
    monkeypatch.setenv("SICE_AUTHORIZED_PG16_DB", "1")
    assert SICERepository.is_live_database_authorized() is True

    repo = SICERepository(mode=RepositoryMode.DATABASE)
    repo.begin()
    success = repo.execute_parameterized("SELECT 1")
    assert success is True
    repo.commit()


def test_database_mode_authorized_via_mock_client() -> None:
    """Verify DATABASE mode delegates lifecycle methods when injected with a database client."""
    mock_client = MagicMock()
    mock_client.execute.return_value = True

    repo = SICERepository(mode=RepositoryMode.DATABASE, db_client=mock_client)
    repo.begin()
    mock_client.begin.assert_called_once()

    test_sql = "SELECT * FROM user_teams WHERE team_id = %s"
    test_params = (str(uuid4()),)
    result = repo.execute_parameterized(test_sql, test_params)
    assert result is True
    mock_client.execute.assert_called_once_with(test_sql, test_params)

    repo.commit()
    mock_client.commit.assert_called_once()


def test_sql_injection_rejection() -> None:
    """Verify raw unparameterized injection patterns raise ValueError while parameterized succeeds."""
    repo = SICERepository()

    malicious_queries = [
        "SELECT * FROM user_teams WHERE team_name = '' OR '1'='1'",
        "SELECT * FROM user_teams WHERE team_name = '' OR 1=1",
        "SELECT * FROM user_teams WHERE 1=1; DROP TABLE user_teams--",
        "SELECT * FROM user_teams UNION SELECT * FROM users",
        "EXEC sp_msforeachtable",
    ]
    for bad_sql in malicious_queries:
        with pytest.raises(ValueError, match="SQL Injection vector detected"):
            repo.execute_parameterized(bad_sql)

    # Safe parameterized query with injection characters in parameter value
    safe_sql = "SELECT * FROM user_teams WHERE team_name = %s"
    safe_params = ("' OR '1'='1",)
    assert repo.execute_parameterized(safe_sql, safe_params) is True


def test_parameterized_query_audit_logging() -> None:
    """Verify executed parameterized queries are recorded to executed_queries audit trail."""
    repo = SICERepository()
    query = "SELECT * FROM user_teams WHERE target_season = %s"
    params = ("IPL 2027",)
    repo.execute_parameterized(query, params)

    assert len(repo.executed_queries) == 1
    log_entry = repo.executed_queries[0]
    assert log_entry["sql"] == query
    assert log_entry["params"] == params
    assert isinstance(log_entry["ts"], datetime)


# ==============================================================================
# Suite 2: SICERepository Transactions, Atomicity & Concurrency Isolation
# ==============================================================================


def test_transaction_commit_persists_staged_entities() -> None:
    """Verify staged entities become persistently visible across transactions after commit."""
    repo = SICERepository()
    assert not repo.in_transaction

    repo.begin()
    assert repo.in_transaction

    team = repo.save_team(UserTeam(team_name="Royals Squad A", target_season="IPL 2027"))
    player = repo.save_team_player(
        UserTeamPlayer(user_team_id=team.team_id, player_id=uuid4(), assigned_role="Batter")
    )

    # Visible in active transaction
    assert repo.get_team(team.team_id) is not None
    assert repo.get_team_player(player.id) is not None

    repo.commit()
    assert not repo.in_transaction

    # Persistently visible after commit
    retrieved_team = repo.get_team(team.team_id)
    assert retrieved_team is not None
    assert retrieved_team.team_name == "Royals Squad A"
    assert repo.get_team_player(player.id) is not None
    assert repo.count("teams") == 1
    assert repo.count("team_players") == 1


def test_transaction_rollback_clears_staging_with_zero_residue() -> None:
    """Verify rollback discards all staged mutations with zero residual state."""
    repo = SICERepository()
    repo.begin()

    team = repo.save_team(UserTeam(team_name="Temporary Squad", target_season="IPL 2027"))
    repo.save_team_player(
        UserTeamPlayer(user_team_id=team.team_id, player_id=uuid4(), assigned_role="Bowler")
    )

    assert repo.get_team(team.team_id) is not None
    assert repo.count("teams") == 1

    repo.rollback()
    assert not repo.in_transaction

    assert repo.get_team(team.team_id) is None
    assert repo.count("teams") == 0
    assert repo.count("team_players") == 0


def test_savepoint_and_partial_rollback() -> None:
    """Verify savepoints allow partial transaction rollbacks without discarding earlier work."""
    repo = SICERepository()
    repo.begin()

    team1 = repo.save_team(UserTeam(team_name="Core Team"))
    repo.savepoint("phase_1")

    team2 = repo.save_team(UserTeam(team_name="Experimental Team"))
    assert repo.get_team(team1.team_id) is not None
    assert repo.get_team(team2.team_id) is not None
    assert repo.count("teams") == 2

    # Roll back to phase_1: team2 should vanish, team1 must remain
    repo.rollback_to("phase_1")
    assert repo.get_team(team1.team_id) is not None
    assert repo.get_team(team2.team_id) is None
    assert repo.count("teams") == 1

    repo.commit()
    assert repo.get_team(team1.team_id) is not None
    assert repo.get_team(team2.team_id) is None
    assert repo.count("teams") == 1


def test_save_batch_atomic_rollback_on_failure() -> None:
    """Verify save_batch atomically rolls back all records when an error occurs mid-batch."""
    repo = SICERepository()
    batch: list[Any] = [
        UserTeam(team_name=f"Batch Squad {i}", target_season="IPL 2027") for i in range(5)
    ]

    with pytest.raises(RuntimeError, match="Simulated failure in save_batch at index 3"):
        repo.save_batch(batch, fail_index=3)

    assert repo.count("teams") == 0

    # Successful batch
    saved = repo.save_batch(batch)
    assert len(saved) == 5
    assert repo.count("teams") == 5


def test_thread_isolation_transaction_staging() -> None:
    """Verify thread-isolated transaction staging prevents dirty reads across threads."""
    repo = SICERepository()
    t1_staged = threading.Event()
    t2_checked = threading.Event()
    t1_team_id = uuid4()
    observations: list[Any] = []

    def thread_1_work() -> None:
        repo.begin()
        repo.save_team(UserTeam(team_id=t1_team_id, team_name="T1 Private Team"))
        t1_staged.set()
        t2_checked.wait(timeout=5.0)
        repo.commit()

    def thread_2_work() -> None:
        t1_staged.wait(timeout=5.0)
        # Thread 2 must not see Thread 1's uncommitted staged team
        observations.append(repo.count("teams"))
        observations.append(repo.get_team(t1_team_id) is None)
        t2_checked.set()

    th1 = threading.Thread(target=thread_1_work)
    th2 = threading.Thread(target=thread_2_work)
    th1.start()
    th2.start()
    th1.join(timeout=5.0)
    th2.join(timeout=5.0)

    # Thread 2 saw 0 teams and None for t1_team_id
    assert observations == [0, True]
    # After commit, main thread sees it
    assert repo.count("teams") == 1
    assert repo.get_team(t1_team_id) is not None


# ==============================================================================
# Suite 3: SICERepository Entity CRUD & Cascade Deletion
# ==============================================================================


def test_user_team_crud_and_pagination() -> None:
    """Verify UserTeam create, retrieve, update, list with pagination, and filter."""
    repo = SICERepository()
    for i in range(10):
        creator = "analyst_a" if i < 5 else "analyst_b"
        season = "IPL 2026" if i % 2 == 0 else "IPL 2027"
        repo.save_team(UserTeam(team_name=f"Team {i}", created_by=creator, target_season=season))

    all_teams = repo.list_teams(limit=50)
    assert len(all_teams) == 10

    page_1 = repo.list_teams(limit=3, offset=0)
    page_2 = repo.list_teams(limit=3, offset=3)
    assert len(page_1) == 3
    assert len(page_2) == 3
    assert page_1[0].team_id != page_2[0].team_id

    filtered_creator = repo.list_teams(created_by="analyst_a")
    assert len(filtered_creator) == 5

    filtered_season = repo.list_teams(target_season="IPL 2027")
    assert len(filtered_season) == 5


def test_user_team_player_crud() -> None:
    """Verify UserTeamPlayer persistence, retrieval by entry ID, team ID, and composite key."""
    repo = SICERepository()
    team_id = uuid4()
    p1_id = uuid4()
    p2_id = uuid4()

    tp1 = repo.save_team_player(
        UserTeamPlayer(
            user_team_id=team_id,
            player_id=p1_id,
            assigned_role="Top-Order Batter",
            batting_order=1,
            is_captain=True,
        )
    )
    tp2 = repo.save_team_player(
        UserTeamPlayer(
            user_team_id=team_id,
            player_id=p2_id,
            assigned_role="Wicketkeeper",
            batting_order=2,
            is_designated_wk=True,
        )
    )

    assert repo.get_team_player(tp1.id) is not None
    assert repo.get_team_player(tp2.id) is not None
    players = repo.get_team_players(team_id)
    assert len(players) == 2

    by_composite = repo.get_team_player_by_player_id(team_id, p1_id)
    assert by_composite is not None
    assert by_composite.is_captain is True

    deleted = repo.delete_team_player_by_player_id(team_id, p2_id)
    assert deleted is True
    assert repo.get_team_player_by_player_id(team_id, p2_id) is None
    assert len(repo.get_team_players(team_id)) == 1


def test_cascade_delete_team_removes_players() -> None:
    """Verify deleting a UserTeam cascades deletion to all associated UserTeamPlayer entries."""
    repo = SICERepository()
    team = repo.save_team(UserTeam(team_name="Royals XI"))
    p1 = repo.save_team_player(UserTeamPlayer(user_team_id=team.team_id, player_id=uuid4()))
    p2 = repo.save_team_player(UserTeamPlayer(user_team_id=team.team_id, player_id=uuid4()))

    assert repo.get_team(team.team_id) is not None
    assert len(repo.get_team_players(team.team_id)) == 2

    # Delete team
    deleted = repo.delete_team(team.team_id)
    assert deleted is True

    assert repo.get_team(team.team_id) is None
    assert repo.get_team_player(p1.id) is None
    assert repo.get_team_player(p2.id) is None
    assert len(repo.get_team_players(team.team_id)) == 0
    assert repo.count("teams") == 0
    assert repo.count("team_players") == 0


def test_ranking_configuration_and_run_persistence() -> None:
    """Verify persistence and lookup of RankingConfiguration (Entity 32) and RankingRun (Entity 33)."""
    repo = SICERepository()
    config = repo.save_ranking_configuration(
        RankingConfiguration(
            config_version="RK-1.0.0",
            target_season_id=uuid4(),
            policy_id=uuid4(),
            evaluation_date=date(2027, 3, 1),
            ordering_json={"k1": "age", "k2": "consistency", "k3": "b05"},
            created_by="RR Lead Scout",
        )
    )

    retrieved_cfg = repo.get_ranking_configuration(config.config_id)
    assert retrieved_cfg is not None
    assert retrieved_cfg.config_version == "RK-1.0.0"

    by_version = repo.get_ranking_configuration_by_version("RK-1.0.0")
    assert by_version is not None
    assert by_version.config_id == config.config_id

    run = repo.save_ranking_run(
        RankingRun(
            config_id=config.config_id,
            data_snapshot_sha256="a" * 64,
            candidate_pool=[str(uuid4())],
            top10=[{"rank": 1, "player_id": str(uuid4())}],
            determinism_note="Deterministic execution with seed 42",
        )
    )

    retrieved_run = repo.get_ranking_run(run.run_id)
    assert retrieved_run is not None
    assert retrieved_run.config_id == config.config_id

    runs = repo.list_ranking_runs(config_id=config.config_id)
    assert len(runs) == 1


def test_derived_feature_persistence() -> None:
    """Verify persistence and lookup of DerivedFeature (Entity 31)."""
    repo = SICERepository()
    player_id = uuid4()

    feat = repo.save_derived_feature(
        DerivedFeature(
            player_id=player_id,
            feature_group="Squad Intelligence",
            feature_name="batting_depth_index",
            feature_value_numeric=82.5,
            calculation_window="T20_DOMESTIC_2024_2026",
        )
    )

    retrieved = repo.get_derived_feature(feat.feature_id)
    assert retrieved is not None
    assert retrieved.feature_value_numeric == 82.5

    features = repo.get_derived_features_by_player(player_id, feature_group="Squad Intelligence")
    assert len(features) == 1
    assert features[0].feature_name == "batting_depth_index"

    empty_features = repo.get_derived_features_by_player(player_id, feature_group="Bowling")
    assert len(empty_features) == 0


def test_delete_record_and_clear() -> None:
    """Verify generic delete_record across entities and clear() reset."""
    repo = SICERepository()
    team = repo.save_team(UserTeam(team_name="Team Alpha"))
    feat = repo.save_derived_feature(
        DerivedFeature(
            player_id=uuid4(),
            feature_group="Squad Intelligence",
            feature_name="role_entropy",
            calculation_window="CAREER",
        )
    )

    assert repo.count() == 2
    deleted = repo.delete_record(team.team_id)
    assert deleted is True
    assert repo.get_team(team.team_id) is None
    assert repo.count() == 1

    repo.clear()
    assert repo.count() == 0
    assert repo.get_derived_feature(feat.feature_id) is None


# ==============================================================================
# Suite 4: TeamBuilderService Team Lifecycle
# ==============================================================================


def test_create_team_success() -> None:
    """Verify creating a team with valid parameters persists correctly."""
    service = TeamBuilderService()
    team = service.create_team(
        team_name="Rajasthan Royals Draft 2027",
        target_season="IPL 2027",
        created_by="Scouting Lead",
        notes="Testing prospective uncapped core",
    )

    assert team.team_name == "Rajasthan Royals Draft 2027"
    assert team.target_season == "IPL 2027"
    assert team.created_by == "Scouting Lead"
    assert team.notes == "Testing prospective uncapped core"
    assert service.get_team(team.team_id) is not None


def test_create_team_validation_failure() -> None:
    """Verify blank, whitespace-only, or invalid team_name raises ValueError."""
    service = TeamBuilderService()
    with pytest.raises(ValueError, match="team_name must be a non-empty string"):
        service.create_team(team_name="")

    with pytest.raises(ValueError, match="team_name must be a non-empty string"):
        service.create_team(team_name="   ")


def test_get_team_not_found() -> None:
    """Verify querying non-existent team ID returns None."""
    service = TeamBuilderService()
    assert service.get_team(uuid4()) is None


def test_update_team_success() -> None:
    """Verify updating team name, target season, and notes advances updated_at."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Original Name")
    original_updated_at = team.updated_at

    updated = service.update_team(
        team_id=team.team_id,
        team_name="Updated Name",
        target_season="IPL 2028",
        notes="Revised strategy",
    )
    assert updated.team_name == "Updated Name"
    assert updated.target_season == "IPL 2028"
    assert updated.notes == "Revised strategy"
    assert updated.updated_at >= original_updated_at


def test_update_team_nonexistent_raises_key_error() -> None:
    """Verify updating unknown team ID raises KeyError."""
    service = TeamBuilderService()
    with pytest.raises(KeyError, match="does not exist"):
        service.update_team(team_id=uuid4(), team_name="New Name")


def test_delete_team_success_and_cascade() -> None:
    """Verify deleting a team returns True, cascades player removal, and get returns None."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Team to Delete")
    service.add_player(team.team_id, uuid4())

    assert len(service.get_team_players(team.team_id)) == 1

    deleted = service.delete_team(team.team_id)
    assert deleted is True
    assert service.get_team(team.team_id) is None
    assert len(service.get_team_players(team.team_id)) == 0


# ==============================================================================
# Suite 5: TeamBuilderService Player Roster Assignment
# ==============================================================================


def test_add_player_valid() -> None:
    """Verify adding player with role, batting order, WK, and captain flags."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Match Squad")
    player_id = uuid4()

    assignment = service.add_player(
        team_id=team.team_id,
        player_id=player_id,
        assigned_role="Opening Batter",
        batting_order=1,
        is_designated_wk=True,
        is_captain=True,
    )

    assert assignment.user_team_id == team.team_id
    assert assignment.player_id == player_id
    assert assignment.assigned_role == "Opening Batter"
    assert assignment.batting_order == 1
    assert assignment.is_designated_wk is True
    assert assignment.is_captain is True


def test_add_player_duplicate_rejection() -> None:
    """Verify adding duplicate player raises SquadConstraintViolationError(DUPLICATE_PLAYER)."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Match Squad")
    player_id = uuid4()

    service.add_player(team.team_id, player_id)

    with pytest.raises(SquadConstraintViolationError) as exc_info:
        service.add_player(team.team_id, player_id)
    assert exc_info.value.code == "SQUAD_CONSTRAINT_VIOLATION"
    assert exc_info.value.details.get("violation_type") == "DUPLICATE_PLAYER"


def test_add_player_to_nonexistent_team_raises_key_error() -> None:
    """Verify adding player to non-existent team raises KeyError."""
    service = TeamBuilderService()
    with pytest.raises(KeyError, match="does not exist"):
        service.add_player(uuid4(), uuid4())


def test_add_player_squad_capacity_25_enforcement_hd09() -> None:
    """Verify adding 26th player raises ROSTER_OVERSIZED violation unless allow_oversize=True."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Max Squad")

    for _ in range(25):
        service.add_player(team.team_id, uuid4())

    assert len(service.get_team_players(team.team_id)) == 25

    # 26th player without allow_oversize
    with pytest.raises(SquadConstraintViolationError) as exc_info:
        service.add_player(team.team_id, uuid4(), allow_oversize=False)
    assert exc_info.value.details.get("violation_type") == "ROSTER_OVERSIZED"

    # 26th player with allow_oversize=True
    service.add_player(team.team_id, uuid4(), allow_oversize=True)
    assert len(service.get_team_players(team.team_id)) == 26


def test_add_player_batting_order_validation() -> None:
    """Verify batting order 1..11 range bounds and slot conflict rejection."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Lineup Squad")

    # Invalid range: 0 or 12
    with pytest.raises(ValueError, match="batting_order must be between 1 and 11"):
        service.add_player(team.team_id, uuid4(), batting_order=0)

    with pytest.raises(ValueError, match="batting_order must be between 1 and 11"):
        service.add_player(team.team_id, uuid4(), batting_order=12)

    # Valid slot 3
    service.add_player(team.team_id, uuid4(), batting_order=3)

    # Colliding slot 3
    with pytest.raises(SquadConstraintViolationError) as exc_info:
        service.add_player(team.team_id, uuid4(), batting_order=3)
    assert exc_info.value.details.get("violation_type") == "BATTING_ORDER_CONFLICT"


def test_add_player_captain_conflict() -> None:
    """Verify designating second captain raises CAPTAIN_CONFLICT violation."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Leadership Squad")

    service.add_player(team.team_id, uuid4(), is_captain=True)

    with pytest.raises(SquadConstraintViolationError) as exc_info:
        service.add_player(team.team_id, uuid4(), is_captain=True)
    assert exc_info.value.details.get("violation_type") == "CAPTAIN_CONFLICT"


def test_remove_player_success_and_missing() -> None:
    """Verify remove_player returns True for existing player and False for absent player."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Roster")
    p1 = uuid4()
    p2 = uuid4()

    service.add_player(team.team_id, p1)
    assert service.remove_player(team.team_id, p1) is True
    assert service.remove_player(team.team_id, p1) is False
    assert service.remove_player(team.team_id, p2) is False


# ==============================================================================
# Suite 6: TeamBuilderService Roster Validation & IPL Governance (HD-05, HD-08, HD-09)
# ==============================================================================


def test_validate_roster_empty_squad() -> None:
    """Verify empty squad returns ROSTER_INCOMPLETE and is_valid_ipl_roster=False."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Empty Squad")

    res = service.validate_roster(team.team_id)
    assert res["squad_size"] == 0
    assert res["roster_status"] == RosterStatus.ROSTER_INCOMPLETE
    assert res["is_valid_ipl_roster"] is False
    assert len(res["violations"]) > 0


def test_validate_roster_incomplete_draft_hd09() -> None:
    """Verify squad size 14 returns ROSTER_INCOMPLETE and records capacity violation."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Incomplete Draft")

    for _ in range(14):
        service.add_player(team.team_id, uuid4())

    res = service.validate_roster(team.team_id)
    assert res["squad_size"] == 14
    assert res["roster_status"] == RosterStatus.ROSTER_INCOMPLETE
    assert res["is_valid_ipl_roster"] is False
    assert any("below minimum IPL roster requirement of 18" in v for v in res["violations"])


def test_validate_roster_valid_roster_hd05() -> None:
    """Verify compliant squad of 20 (6 overseas, 14 domestic, 2 WKs, 1 captain) is ROSTER_VALID."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Championship Squad")

    metadata: dict[UUID, dict[str, Any]] = {}

    # 6 overseas players
    for _ in range(6):
        pid = uuid4()
        metadata[pid] = {
            "is_overseas": True,
            "nationality": "Australia",
            "identity_status": "RESOLVED",
            "eligibility_status": "VERIFIED_ELIGIBLE",
        }
        service.add_player(team.team_id, pid)

    # 14 domestic players (1 captain, 2 designated WKs)
    for i in range(14):
        pid = uuid4()
        is_cpt = i == 0
        is_wk = i in {1, 2}
        metadata[pid] = {
            "is_overseas": False,
            "nationality": "India",
            "identity_status": "RESOLVED",
            "eligibility_status": "VERIFIED_ELIGIBLE",
        }
        service.add_player(
            team.team_id,
            pid,
            is_captain=is_cpt,
            is_designated_wk=is_wk,
        )

    res = service.validate_roster(team.team_id, player_metadata=metadata, strict_official=True)
    assert res["squad_size"] == 20
    assert res["overseas_count"] == 6
    assert res["domestic_count"] == 14
    assert res["designated_wk_count"] == 2
    assert res["captain_player_id"] is not None
    assert res["roster_status"] == RosterStatus.ROSTER_VALID
    assert res["is_valid_ipl_roster"] is True
    assert len(res["violations"]) == 0


def test_validate_roster_overseas_breach_hd05() -> None:
    """Verify squad with 9 overseas players emits OVERSEAS_BREACH and fails validation."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Overseas Heavy")

    metadata: dict[UUID, dict[str, Any]] = {}
    for i in range(20):
        pid = uuid4()
        is_os = i < 9  # 9 overseas
        metadata[pid] = {
            "is_overseas": is_os,
            "nationality": "England" if is_os else "India",
        }
        service.add_player(
            team.team_id,
            pid,
            is_captain=(i == 0),
            is_designated_wk=(i in {1, 2}),
        )

    res = service.validate_roster(team.team_id, player_metadata=metadata)
    assert res["overseas_count"] == 9
    assert res["roster_status"] == RosterStatus.OVERSEAS_BREACH
    assert res["is_valid_ipl_roster"] is False
    assert any("exceeds maximum allowed of 8" in v for v in res["violations"])


def test_validate_roster_wicketkeeper_shortage_hd08() -> None:
    """Verify squad with 1 designated WK emits CRITICAL_WK_SHORTAGE flag and warning."""
    service = TeamBuilderService()
    team = service.create_team(team_name="WK Shortage Squad")

    for i in range(20):
        service.add_player(
            team.team_id,
            uuid4(),
            is_captain=(i == 0),
            is_designated_wk=(i == 1),  # Only 1 WK
        )

    res = service.validate_roster(team.team_id)
    assert res["designated_wk_count"] == 1
    assert "CRITICAL_WK_SHORTAGE" in res["flags"]
    assert any("CRITICAL_WK_SHORTAGE" in w for w in res["warnings"])
    assert res["roster_status"] == RosterStatus.CRITICAL_WK_SHORTAGE


def test_validate_roster_wicketkeeper_slot_waste_hd08() -> None:
    """Verify squad with 4 designated WKs emits SLOT_WASTE flag and warning."""
    service = TeamBuilderService()
    team = service.create_team(team_name="WK Surplus Squad")

    for i in range(20):
        service.add_player(
            team.team_id,
            uuid4(),
            is_captain=(i == 0),
            is_designated_wk=(i in {1, 2, 3, 4}),  # 4 WKs
        )

    res = service.validate_roster(team.team_id)
    assert res["designated_wk_count"] == 4
    assert "SLOT_WASTE" in res["flags"]
    assert any("SLOT_WASTE" in w for w in res["warnings"])
    assert res["roster_status"] == RosterStatus.SLOT_WASTE


def test_validate_roster_strict_official_mode_requires_resolved_identity() -> None:
    """Verify strict_official=True enforces minimum size 18 and RESOLVED/VERIFIED_ELIGIBLE status."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Official Certification Target")

    # Incomplete squad (15 players) raises IncompleteRosterError
    for _ in range(15):
        service.add_player(team.team_id, uuid4())

    with pytest.raises(IncompleteRosterError) as exc_info:
        service.validate_roster(team.team_id, strict_official=True)
    assert exc_info.value.code == "SQUAD_CONSTRAINT_VIOLATION"
    assert exc_info.value.details.get("squad_size") == 15

    # Expand to 18 players but with a PROVISIONAL candidate
    for _ in range(3):
        service.add_player(team.team_id, uuid4())

    players = service.get_team_players(team.team_id)
    metadata: dict[UUID, dict[str, Any]] = {}
    for idx, p in enumerate(players):
        # Set first player to PROVISIONAL
        ident = "PROVISIONAL" if idx == 0 else "RESOLVED"
        metadata[p.player_id] = {
            "identity_status": ident,
            "eligibility_status": "VERIFIED_ELIGIBLE",
        }

    res = service.validate_roster(team.team_id, player_metadata=metadata, strict_official=True)
    assert res["is_valid_ipl_roster"] is False
    assert any("strictly requires 'RESOLVED' identity" in v for v in res["violations"])


def test_validate_roster_draft_mode_tolerates_provisional_candidates() -> None:
    """Verify strict_official=False permits PROVISIONAL candidates in draft exploration."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Exploratory Draft")

    metadata: dict[UUID, dict[str, Any]] = {}
    for i in range(20):
        pid = uuid4()
        # Mix of PROVISIONAL and RESOLVED
        metadata[pid] = {
            "is_overseas": False,
            "identity_status": "PROVISIONAL" if i % 2 == 0 else "RESOLVED",
            "eligibility_status": "VERIFIED_ELIGIBLE",
        }
        service.add_player(
            team.team_id,
            pid,
            is_captain=(i == 0),
            is_designated_wk=(i in {1, 2}),
        )

    res = service.validate_roster(team.team_id, player_metadata=metadata, strict_official=False)
    # Draft mode permits provisional candidates without raising exception
    assert res["squad_size"] == 20
    assert res["roster_status"] == RosterStatus.ROSTER_VALID
    assert res["is_valid_ipl_roster"] is True


# ==============================================================================
# Suite 7: ServiceBoundary Compliance & Roster Modification (Update Player)
# ==============================================================================


def test_team_builder_service_boundary_compliance() -> None:
    """Verify TeamBuilderService inherits from ServiceBoundary and implements lifecycle methods."""
    service = TeamBuilderService()
    assert isinstance(service, ServiceBoundary)
    assert service.get_service_name() == "team_builder_service"

    health = service.health_check()
    assert health["service"] == "team_builder_service"
    assert health["status"] == "operational"
    assert health["repository_mode"] == "IN_MEMORY"
    assert health["teams_count"] == 0
    assert health["players_count"] == 0


def test_team_builder_update_player_success() -> None:
    """Verify updating player role, batting order, and captain/WK flags."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Modification Team")
    player_id = uuid4()

    assignment = service.add_player(
        team_id=team.team_id,
        player_id=player_id,
        assigned_role="Batter",
        batting_order=1,
    )
    assert assignment.assigned_role == "Batter"
    assert assignment.batting_order == 1
    assert assignment.is_captain is False

    updated = service.update_player(
        team_id=team.team_id,
        player_id=player_id,
        assigned_role="Opening Batter",
        batting_order=2,
        is_designated_wk=True,
        is_captain=True,
    )
    assert updated.assigned_role == "Opening Batter"
    assert updated.batting_order == 2
    assert updated.is_designated_wk is True
    assert updated.is_captain is True


def test_team_builder_update_player_batting_order_conflict() -> None:
    """Verify updating batting order to an occupied slot raises BATTING_ORDER_CONFLICT."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Conflict Team")
    p1 = uuid4()
    p2 = uuid4()

    service.add_player(team.team_id, p1, batting_order=3)
    service.add_player(team.team_id, p2, batting_order=4)

    with pytest.raises(SquadConstraintViolationError) as exc_info:
        service.update_player(team.team_id, p2, batting_order=3)
    assert exc_info.value.details.get("violation_type") == "BATTING_ORDER_CONFLICT"


def test_team_builder_update_player_captain_conflict() -> None:
    """Verify updating second player to captain raises CAPTAIN_CONFLICT."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Captain Team")
    p1 = uuid4()
    p2 = uuid4()

    service.add_player(team.team_id, p1, is_captain=True)
    service.add_player(team.team_id, p2, is_captain=False)

    with pytest.raises(SquadConstraintViolationError) as exc_info:
        service.update_player(team.team_id, p2, is_captain=True)
    assert exc_info.value.details.get("violation_type") == "CAPTAIN_CONFLICT"


def test_team_builder_update_player_nonexistent() -> None:
    """Verify updating player not on team or on non-existent team raises KeyError."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Ghost Team")

    with pytest.raises(KeyError, match="not assigned to team"):
        service.update_player(team.team_id, uuid4(), assigned_role="Batter")

    with pytest.raises(KeyError, match="does not exist"):
        service.update_player(uuid4(), uuid4(), assigned_role="Batter")


# ==============================================================================
# Suite 8: Concurrency Stress, Security Guardrails & Edge Cases
# ==============================================================================


def test_concurrency_100_threads_duplicate_player_rejection() -> None:
    """Verify 100 concurrent threads attempting to add the same player results in exactly 1 success."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Concurrent Duplicate Team")
    target_player_id = uuid4()

    success_count = 0
    duplicate_errors = 0
    other_errors = 0
    lock = threading.Lock()

    def worker() -> None:
        nonlocal success_count, duplicate_errors, other_errors
        try:
            service.add_player(team.team_id, target_player_id)
            with lock:
                success_count += 1
        except SquadConstraintViolationError as e:
            if e.details.get("violation_type") == "DUPLICATE_PLAYER":
                with lock:
                    duplicate_errors += 1
            else:
                with lock:
                    other_errors += 1
        except Exception:
            with lock:
                other_errors += 1

    threads = [threading.Thread(target=worker) for _ in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10.0)

    assert success_count == 1
    assert duplicate_errors == 99
    assert other_errors == 0
    assert len(service.get_team_players(team.team_id)) == 1


def test_concurrency_captain_conflict_under_load() -> None:
    """Verify 50 concurrent threads assigning captain results in exactly 1 captain."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Concurrent Captain Team")

    success_count = 0
    conflict_count = 0
    lock = threading.Lock()

    def worker() -> None:
        nonlocal success_count, conflict_count
        try:
            service.add_player(team.team_id, uuid4(), is_captain=True)
            with lock:
                success_count += 1
        except SquadConstraintViolationError as e:
            if e.details.get("violation_type") == "CAPTAIN_CONFLICT":
                with lock:
                    conflict_count += 1

    threads = [threading.Thread(target=worker) for _ in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10.0)

    assert success_count == 1
    assert conflict_count == 49
    players = service.get_team_players(team.team_id)
    assert sum(1 for p in players if p.is_captain) == 1


def test_concurrency_squad_capacity_25_enforcement() -> None:
    """Verify 50 concurrent threads adding players to team of 20 strictly stops at 25."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Concurrent Capacity Team")

    for _ in range(20):
        service.add_player(team.team_id, uuid4())

    assert len(service.get_team_players(team.team_id)) == 20

    success_count = 0
    oversized_count = 0
    lock = threading.Lock()

    def worker() -> None:
        nonlocal success_count, oversized_count
        try:
            service.add_player(team.team_id, uuid4())
            with lock:
                success_count += 1
        except SquadConstraintViolationError as e:
            if e.details.get("violation_type") == "ROSTER_OVERSIZED":
                with lock:
                    oversized_count += 1

    threads = [threading.Thread(target=worker) for _ in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10.0)

    assert success_count == 5
    assert oversized_count == 45
    assert len(service.get_team_players(team.team_id)) == 25


def test_sql_injection_union_all_and_comments_rejection() -> None:
    """Verify enhanced injection patterns detect UNION ALL and inline/trailing comments."""
    repo = SICERepository()

    evasive_injections = [
        "SELECT * FROM user_teams UNION ALL SELECT * FROM users",
        "SELECT * FROM user_teams WHERE 1=1; DROP TABLE user_teams; -- trailing comment",
        "SELECT * FROM user_teams WHERE 1=1 /* block comment */",
    ]
    for bad_sql in evasive_injections:
        with pytest.raises(ValueError, match="SQL Injection vector detected"):
            repo.execute_parameterized(bad_sql)


def test_savepoint_key_error_on_unknown_savepoint() -> None:
    """Verify rollback_to and release_savepoint raise KeyError on non-existent savepoints."""
    repo = SICERepository()
    repo.begin()

    with pytest.raises(KeyError, match="Savepoint 'invalid_sp' does not exist"):
        repo.rollback_to("invalid_sp")

    with pytest.raises(KeyError, match="Savepoint 'invalid_sp' does not exist"):
        repo.release_savepoint("invalid_sp")

    repo.rollback()


def test_safe_uuid_lookups_resilient_to_malformed_ids() -> None:
    """Verify repository safely returns None/empty list for malformed string UUIDs without raising."""
    repo = SICERepository()
    assert repo.get_team("not-a-valid-uuid") is None
    assert repo.delete_team("not-a-valid-uuid") is False
    assert repo.get_team_player("not-a-valid-uuid") is None
    assert repo.get_team_players("not-a-valid-uuid") == []
    assert repo.get_team_player_by_player_id("not-a-uuid", "also-bad") is None
    assert repo.delete_team_player("not-a-valid-uuid") is False
    assert repo.get_ranking_configuration("bad-uuid") is None
    assert repo.get_ranking_run("bad-uuid") is None
    assert repo.list_ranking_runs(config_id="bad-uuid") == []
    assert repo.get_derived_feature("bad-uuid") is None
    assert repo.get_derived_features_by_player("bad-uuid") == []
    assert repo.delete_record("bad-uuid") is False


def test_wicketkeeper_detection_variations() -> None:
    """Verify WK detection recognizes hyphenated, spaced, and abbreviation role designations."""
    service = TeamBuilderService()
    team = service.create_team(team_name="WK Variations Team")

    # Add players with different WK representations
    service.add_player(team.team_id, uuid4(), assigned_role="Wicket-Keeper")
    service.add_player(team.team_id, uuid4(), assigned_role="Wicket Keeper")
    service.add_player(team.team_id, uuid4(), assigned_role="WK")
    service.add_player(team.team_id, uuid4(), assigned_role="WK-Batter")
    service.add_player(team.team_id, uuid4(), assigned_role="Top-Order Batter")

    players = service.get_team_players(team.team_id)
    assert len(players) == 5

    res = service.validate_roster(team.team_id)
    assert res["designated_wk_count"] == 4


def test_strict_official_mode_requires_metadata_for_all_players() -> None:
    """Verify strict_official mode requires player_metadata and rejects unverified candidates."""
    service = TeamBuilderService()
    team = service.create_team(team_name="Strict Audit Team")

    for i in range(18):
        service.add_player(
            team.team_id,
            uuid4(),
            is_captain=(i == 0),
            is_designated_wk=(i in {1, 2}),
        )

    # 1. Calling strict_official with player_metadata=None fails
    res_none = service.validate_roster(team.team_id, player_metadata=None, strict_official=True)
    assert res_none["is_valid_ipl_roster"] is False
    assert any("strictly requires player metadata" in v for v in res_none["violations"])

    # 2. Providing metadata for 17 of 18 players fails due to missing credentials for 1 player
    players = service.get_team_players(team.team_id)
    partial_meta: dict[UUID, dict[str, Any]] = {}
    for p in players[:-1]:
        partial_meta[p.player_id] = {
            "identity_status": "RESOLVED",
            "eligibility_status": "VERIFIED_ELIGIBLE",
        }

    res_partial = service.validate_roster(
        team.team_id, player_metadata=partial_meta, strict_official=True
    )
    assert res_partial["is_valid_ipl_roster"] is False
    assert any(
        "lacks verified identity and eligibility metadata" in v for v in res_partial["violations"]
    )


def test_repository_count_entity_aliases() -> None:
    """Verify repo.count accepts canonical TRD entity names as well as short store names."""
    repo = SICERepository()
    team = repo.save_team(UserTeam(team_name="Alias Squad"))
    repo.save_team_player(UserTeamPlayer(user_team_id=team.team_id, player_id=uuid4()))

    assert repo.count("teams") == 1
    assert repo.count("user_teams") == 1
    assert repo.count("team_players") == 1
    assert repo.count("user_team_players") == 1
    assert repo.count("derived_features") == 0
    assert repo.count("ranking_configs") == 0
    assert repo.count("ranking_configurations") == 0
    assert repo.count("ranking_runs") == 0
    assert repo.count() == 2
