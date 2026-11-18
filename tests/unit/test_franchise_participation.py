"""Unit tests for Franchise Participation Service (Milestone M1).

Validates:
1. Active RR participation window retrieval (2008-2015, 2018-2026) -> PARTICIPATING.
2. Franchise-specific suspension (2016-2017) -> SUSPENDED (RR-specific, others continued).
3. 2027 season UNKNOWN & UNVERIFIED status, and strict rule against inferring participation.
4. Database constraint invariant chk_tsp_verified_evidence (verified=True requires verification_id).
5. Idempotent seeding (ON CONFLICT DO NOTHING).
6. Service boundary and database client integration.
"""

from datetime import date
from uuid import UUID, uuid4

import pytest
from src.contracts.competition import Season, Team, TeamSeasonParticipation
from src.membership.participation import (
    ACTIVE_RR_SEASONS,
    CANONICAL_RR_NAME,
    CANONICAL_RR_SHORT_CODE,
    CANONICAL_RR_TEAM_ID,
    FUTURE_UNKNOWN_SEASONS,
    SUSPENDED_RR_SEASONS,
    FranchiseParticipationService,
)

from tests.fixtures.mock_supabase import MockSupabaseClient

# =============================================================================
# 1. Service Boundary & Health Check
# =============================================================================


def test_service_boundary_identity() -> None:
    """Verify FranchiseParticipationService implements canonical service name."""
    service = FranchiseParticipationService(auto_seed=False)
    assert service.get_service_name() == "franchise_participation_service"


def test_service_boundary_health_check() -> None:
    """Verify FranchiseParticipationService returns healthy diagnostic status."""
    service = FranchiseParticipationService(auto_seed=True)
    health = service.health_check()
    assert health["status"] == "HEALTHY"
    assert health["service"] == "franchise_participation_service"
    assert health["participations_count"] == 20
    assert health["rr_suspension_enforced"] is True
    assert health["future_season_safe"] is True
    assert health["canonical_rr_team_id"] == str(CANONICAL_RR_TEAM_ID)


# =============================================================================
# 2. Active RR Participation Windows (2008-2015 and 2018-2026)
# =============================================================================


@pytest.mark.parametrize("year", ACTIVE_RR_SEASONS)
def test_active_rr_seasons_participating(year: str) -> None:
    """Verify all 17 active RR seasons evaluate to PARTICIPATING and True."""
    service = FranchiseParticipationService(auto_seed=True)
    status, is_participating = service.is_season_participating(year, CANONICAL_RR_NAME)
    assert status == "PARTICIPATING"
    assert is_participating is True


@pytest.mark.parametrize("year", ["2008", "2010", "2015", "2018", "2024", "2026"])
def test_active_rr_seasons_short_code(year: str) -> None:
    """Verify team short code 'RR' resolves to canonical active participation."""
    service = FranchiseParticipationService(auto_seed=True)
    status, is_participating = service.is_season_participating(year, CANONICAL_RR_SHORT_CODE)
    assert status == "PARTICIPATING"
    assert is_participating is True


def test_list_franchise_windows_active_count() -> None:
    """Verify list_franchise_windows returns exact active, suspended, and unknown counts."""
    service = FranchiseParticipationService(auto_seed=True)
    windows = service.list_franchise_windows(CANONICAL_RR_NAME)

    assert len(windows) == 20  # 17 active + 2 suspended + 1 future
    active_windows = [w for w in windows if w.participation_status == "PARTICIPATING"]
    assert len(active_windows) == 17

    # Check all active windows belong to canonical RR team
    for w in active_windows:
        assert w.team_id == CANONICAL_RR_TEAM_ID
        assert isinstance(w, TeamSeasonParticipation)
        assert w.effective_start_date is not None
        assert w.effective_end_date is not None
        assert w.effective_end_date > w.effective_start_date


# =============================================================================
# 3. Franchise-Specific Suspension (2016-2017)
# =============================================================================


@pytest.mark.parametrize("year", SUSPENDED_RR_SEASONS)
def test_rr_suspended_seasons(year: str) -> None:
    """Verify 2016 and 2017 evaluate strictly to SUSPENDED and False for RR."""
    service = FranchiseParticipationService(auto_seed=True)
    status, is_participating = service.is_season_participating(year, CANONICAL_RR_NAME)
    assert status == "SUSPENDED"
    assert is_participating is False


def test_suspension_notes_document_franchise_specificity() -> None:
    """Verify suspension records cite franchise-specific order and non-impact on others."""
    service = FranchiseParticipationService(auto_seed=True)
    windows = service.list_franchise_windows(CANONICAL_RR_NAME)
    suspended_windows = [w for w in windows if w.participation_status == "SUSPENDED"]

    assert len(suspended_windows) == 2
    for w in suspended_windows:
        assert w.notes is not None
        assert "Franchise-specific suspension" in w.notes
        assert "Lodha" in w.notes or "Supreme Court" in w.notes
        assert "Other IPL franchises" in w.notes


def test_suspension_is_franchise_specific_other_teams_participated() -> None:
    """Verify suspension was franchise-specific: another team participating in 2016/2017 is valid."""
    service = FranchiseParticipationService(auto_seed=True)

    mi_team_id = uuid4()
    mi_team = Team(
        team_id=mi_team_id,
        team_name="Mumbai Indians",
        short_code="MI",
        is_active=True,
    )
    service.register_team(mi_team)

    season_2016_id = service.get_canonical_season_id("2016")

    # Seed Mumbai Indians as participating in 2016
    custom_records = [
        {
            "participation_id": uuid4(),
            "team_id": mi_team_id,
            "season_id": season_2016_id,
            "participation_status": "PARTICIPATING",
            "effective_start_date": date(2016, 4, 9),
            "effective_end_date": date(2016, 5, 29),
            "verified": False,
            "verification_status": "UNVERIFIED",
            "notes": "Mumbai Indians participated in IPL 2016 normally.",
        }
    ]
    service.seed_verified_windows(custom_records)

    # RR is SUSPENDED in 2016
    rr_status, rr_part = service.is_season_participating("2016", "Rajasthan Royals")
    assert rr_status == "SUSPENDED"
    assert rr_part is False

    # MI is PARTICIPATING in 2016
    mi_status, mi_part = service.is_season_participating("2016", "Mumbai Indians")
    assert mi_status == "PARTICIPATING"
    assert mi_part is True


# =============================================================================
# 4. 2027 UNKNOWN Status & Rule Against Inferring Participation
# =============================================================================


@pytest.mark.parametrize("year", FUTURE_UNKNOWN_SEASONS)
def test_2027_season_unknown_status(year: str) -> None:
    """Verify 2027 evaluates to UNKNOWN and False until official evidence is presented."""
    service = FranchiseParticipationService(auto_seed=True)
    status, is_participating = service.is_season_participating(year, CANONICAL_RR_NAME)
    assert status == "UNKNOWN"
    assert is_participating is False


def test_2027_season_contract_attributes() -> None:
    """Verify 2027 participation record has UNKNOWN status and UNVERIFIED verification."""
    service = FranchiseParticipationService(auto_seed=True)
    season_2027_id = service.get_canonical_season_id("2027")
    part = service.get_participation(CANONICAL_RR_TEAM_ID, season_2027_id)

    assert part is not None
    assert part.participation_status == "UNKNOWN"
    assert part.verification_status == "UNVERIFIED"
    assert part.verification_id is None
    assert part.notes is not None
    assert "Never infer participation from missing data" in part.notes


@pytest.mark.parametrize("missing_year", ["1999", "2007", "2028", "2030"])
def test_never_infer_participation_from_missing_seasons(missing_year: str) -> None:
    """Verify unrecorded seasons strictly return UNKNOWN and False without inventing participation."""
    service = FranchiseParticipationService(auto_seed=True)
    status, is_participating = service.is_season_participating(missing_year, CANONICAL_RR_NAME)
    assert status == "UNKNOWN"
    assert is_participating is False


def test_never_infer_participation_from_missing_team() -> None:
    """Verify unrecorded team strictly returns UNKNOWN and False."""
    service = FranchiseParticipationService(auto_seed=True)
    status, is_participating = service.is_season_participating("2024", "Nonexistent Franchise FC")
    assert status == "UNKNOWN"
    assert is_participating is False


def test_unseeded_service_returns_unknown() -> None:
    """Verify service without auto-seeding returns UNKNOWN and does not infer participation."""
    service = FranchiseParticipationService(auto_seed=False)
    status, is_participating = service.is_season_participating("2008", CANONICAL_RR_NAME)
    assert status == "UNKNOWN"
    assert is_participating is False


# =============================================================================
# 5. DDL Invariant (chk_tsp_verified_evidence)
# =============================================================================


def test_invariant_violation_verified_true_null_verification_id() -> None:
    """Verify seeding verified=True with null verification_id raises ValueError."""
    service = FranchiseParticipationService(auto_seed=False)
    team_id = uuid4()
    season_id = uuid4()

    invalid_record = {
        "team_id": team_id,
        "season_id": season_id,
        "participation_status": "PARTICIPATING",
        "verified": True,
        "verification_id": None,
        "verification_status": "UNVERIFIED",
    }

    with pytest.raises(ValueError) as exc_info:
        service.seed_verified_windows([invalid_record])
    assert "chk_tsp_verified_evidence" in str(exc_info.value)
    assert "verified=True requires a non-null verification_id" in str(exc_info.value)


def test_invariant_violation_status_verified_null_verification_id() -> None:
    """Verify seeding verification_status='VERIFIED' with null verification_id raises ValueError."""
    service = FranchiseParticipationService(auto_seed=False)
    team_id = uuid4()
    season_id = uuid4()

    invalid_record = {
        "team_id": team_id,
        "season_id": season_id,
        "participation_status": "PARTICIPATING",
        "verified": False,
        "verification_id": None,
        "verification_status": "VERIFIED",
    }

    with pytest.raises(ValueError) as exc_info:
        service.seed_verified_windows([invalid_record])
    assert "chk_tsp_verified_evidence" in str(exc_info.value)


def test_invariant_satisfied_verified_false_null_verification_id() -> None:
    """Verify seeding verified=False with null verification_id succeeds."""
    service = FranchiseParticipationService(auto_seed=False)
    team_id = uuid4()
    season_id = uuid4()

    valid_record = {
        "team_id": team_id,
        "season_id": season_id,
        "participation_status": "PARTICIPATING",
        "verified": False,
        "verification_id": None,
        "verification_status": "UNVERIFIED",
    }

    seeded = service.seed_verified_windows([valid_record])
    assert len(seeded) == 1
    assert seeded[0].team_id == team_id
    assert seeded[0].verification_id is None
    assert seeded[0].verification_status == "UNVERIFIED"


def test_invariant_satisfied_verified_true_with_valid_verification_id() -> None:
    """Verify seeding verified=True with valid UUID verification_id succeeds."""
    service = FranchiseParticipationService(auto_seed=False)
    team_id = uuid4()
    season_id = uuid4()
    v_id = uuid4()

    valid_record = {
        "team_id": team_id,
        "season_id": season_id,
        "participation_status": "PARTICIPATING",
        "verified": True,
        "verification_id": v_id,
        "verification_status": "VERIFIED",
    }

    seeded = service.seed_verified_windows([valid_record])
    assert len(seeded) == 1
    assert seeded[0].team_id == team_id
    assert seeded[0].verification_id == v_id
    assert seeded[0].verification_status == "VERIFIED"


def test_canonical_seeding_defaults_satisfy_invariant() -> None:
    """Verify all canonical records default to verified=False and verification_status='UNVERIFIED'."""
    service = FranchiseParticipationService(auto_seed=True)
    windows = service.list_franchise_windows(CANONICAL_RR_NAME)

    for w in windows:
        # Initial seeding defaults strictly satisfy chk_tsp_verified_evidence
        assert w.verification_status == "UNVERIFIED"
        assert w.verification_id is None


# =============================================================================
# 6. Idempotent Seeding (ON CONFLICT DO NOTHING)
# =============================================================================


def test_canonical_seeding_is_idempotent() -> None:
    """Verify multiple calls to seed_verified_windows produce identical state and no duplicates."""
    service = FranchiseParticipationService(auto_seed=False)
    first_run = service.seed_verified_windows()
    assert len(first_run) == 20

    second_run = service.seed_verified_windows()
    assert len(second_run) == 20

    third_run = service.seed_verified_windows()
    assert len(third_run) == 20

    # Ensure windows in service remained exactly 20
    windows = service.list_franchise_windows(CANONICAL_RR_NAME)
    assert len(windows) == 20


def test_custom_record_seeding_is_idempotent() -> None:
    """Verify custom record re-seeding preserves existing record without duplicates."""
    service = FranchiseParticipationService(auto_seed=False)
    team_id = uuid4()
    season_id = uuid4()

    record = {
        "participation_id": uuid4(),
        "team_id": team_id,
        "season_id": season_id,
        "participation_status": "PARTICIPATING",
        "verified": False,
        "verification_status": "UNVERIFIED",
    }

    seeded_1 = service.seed_verified_windows([record])
    assert len(seeded_1) == 1

    # Second seed of same (team_id, season_id)
    seeded_2 = service.seed_verified_windows([record])
    assert len(seeded_2) == 1
    assert seeded_2[0].participation_id == seeded_1[0].participation_id


# =============================================================================
# 7. get_participation Retrieval & Lookups
# =============================================================================


def test_get_participation_retrieval() -> None:
    """Verify get_participation retrieves exact contract by team_id and season_id."""
    service = FranchiseParticipationService(auto_seed=True)
    season_2008_id = service.get_canonical_season_id("2008")

    part = service.get_participation(CANONICAL_RR_TEAM_ID, season_2008_id)
    assert part is not None
    assert part.team_id == CANONICAL_RR_TEAM_ID
    assert part.season_id == season_2008_id
    assert part.participation_status == "PARTICIPATING"


def test_get_participation_non_existent() -> None:
    """Verify get_participation returns None for unknown team or season."""
    service = FranchiseParticipationService(auto_seed=True)
    assert service.get_participation(uuid4(), uuid4()) is None


def test_canonical_id_helpers() -> None:
    """Verify get_canonical_team_id and get_canonical_season_id are deterministic."""
    service = FranchiseParticipationService(auto_seed=False)
    team_id_1 = service.get_canonical_team_id("Rajasthan Royals")
    team_id_2 = service.get_canonical_team_id("RR")
    assert team_id_1 == CANONICAL_RR_TEAM_ID
    assert team_id_2 == CANONICAL_RR_TEAM_ID

    season_id_1 = service.get_canonical_season_id("2024")
    season_id_2 = service.get_canonical_season_id("2024")
    assert season_id_1 == season_id_2
    assert isinstance(season_id_1, UUID)


def test_register_team_and_season() -> None:
    """Verify dynamically registering external team and season."""
    service = FranchiseParticipationService(auto_seed=False)
    new_team = Team(team_name="Gujarat Titans", short_code="GT", is_active=True)
    service.register_team(new_team)

    new_season = Season(
        competition_id=service._competition.competition_id,
        season_year="2022",
        start_date=date(2022, 3, 26),
        end_date=date(2022, 5, 29),
    )
    service.register_season(new_season)

    assert service._resolve_team_id("Gujarat Titans") == new_team.team_id
    assert service.get_canonical_season_id("2022") == new_season.season_id


# =============================================================================
# 8. Database Client Integration (MockSupabaseClient)
# =============================================================================


def test_database_client_seeding_and_retrieval() -> None:
    """Verify integration with database client populates table with DDL compliant rows."""
    mock_client = MockSupabaseClient()
    service = FranchiseParticipationService(db_client=mock_client, auto_seed=True)

    # Check mock database storage
    db_rows = mock_client.tables.get("team_season_participation", [])
    assert len(db_rows) == 20

    # Verify DDL columns in database rows
    for row in db_rows:
        assert "verified" in row
        assert "verification_status" in row
        assert "status" in row
        assert "participation_status" in row
        assert row["verified"] is False
        assert row["verification_status"] == "UNVERIFIED"

    # Query participation from db_client
    season_2019_id = service.get_canonical_season_id("2019")
    part = service.get_participation(CANONICAL_RR_TEAM_ID, season_2019_id)
    assert part is not None
    assert part.participation_status == "PARTICIPATING"


def test_database_client_idempotent_seeding() -> None:
    """Verify db_client insertion is idempotent without row duplication."""
    mock_client = MockSupabaseClient()
    service = FranchiseParticipationService(db_client=mock_client, auto_seed=True)

    initial_count = len(mock_client.tables.get("team_season_participation", []))
    assert initial_count == 20

    # Call seed_verified_windows again
    service.seed_verified_windows()
    re_seeded_count = len(mock_client.tables.get("team_season_participation", []))
    assert re_seeded_count == 20
