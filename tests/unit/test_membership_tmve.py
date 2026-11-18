"""Unit tests for Team Membership Verification Engine (TMVE) - Phase 3 Milestone M2.

Validates:
1. Verified appearance player resolution -> HISTORICAL_RR_APPEARANCE
2. Squad-only player resolution -> HISTORICAL_RR_SQUAD_ONLY (0 appearances, zero invented stats)
3. Prior association resolution -> PREVIOUSLY_ASSOCIATED
4. Player absent from incomplete records -> RR_RELATIONSHIP_UNKNOWN (no inference from absence)
5. Negative verification 7-gate satisfaction -> NO_VERIFIED_RR_RELATIONSHIP
6. Negative verification individual gate failures (Gates 1-7) -> RR_RELATIONSHIP_UNKNOWN
7. Current vs Not-Current vs Unknown membership resolution
8. Conflict detection triggering RR_RELATIONSHIP_UNKNOWN and REVIEW_REQUIRED
9. TMVERequestContract input handling and TMVEOutputContract structure
10. ServiceBoundary contract (get_service_name, health_check)
11. MockSupabaseClient database integration
"""

from datetime import date
from uuid import uuid4

import pytest
from src.contracts.tmve import (
    RRCurrentState,
    RRRelationshipState,
    TMVEOutputContract,
    TMVERequestContract,
)
from src.membership import (
    RR_CANONICAL_NAME,
    RR_SHORT_CODE,
    TeamMembershipVerificationEngine,
)

from tests.fixtures.mock_supabase import MockSupabaseClient

# =============================================================================
# 1. ServiceBoundary and Lifecycle Tests
# =============================================================================


def test_service_boundary_identity_and_health() -> None:
    """Verify ServiceBoundary methods get_service_name and health_check."""
    engine = TeamMembershipVerificationEngine()
    assert engine.get_service_name() == "team_membership_verification_engine"

    health = engine.health_check()
    assert health["service"] == "team_membership_verification_engine"
    assert health["status"] == "healthy"
    assert health["engine_version"] == "TMVE-1.0.0"
    assert health["db_connected"] is False

    mock_db = MockSupabaseClient()
    engine_with_db = TeamMembershipVerificationEngine(db_client=mock_db)
    health_with_db = engine_with_db.health_check()
    assert health_with_db["db_connected"] is True


# =============================================================================
# 2. Verified Appearance Player Tests
# =============================================================================


def test_resolve_relationship_state_verified_appearance() -> None:
    """Verify player with >= 1 appearances resolves to HISTORICAL_RR_APPEARANCE."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()

    state = engine.resolve_relationship_state(
        player_id=player_id,
        verified_appearances=14,
        squad_records=[{"contract_type": "Retained"}],
    )
    assert state == RRRelationshipState.HISTORICAL_RR_APPEARANCE


def test_verify_player_membership_appearance() -> None:
    """Verify full contract output for a player with verified RR appearances."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()
    as_of = date(2026, 3, 1)

    engine.register_squad_record(
        player_id,
        {
            "season_year": "2024",
            "contract_type": "Retained",
            "is_active_squad": False,
        },
    )
    engine.register_appearances(player_id, 16)

    output = engine.verify_player_membership(player_id=player_id, as_of_date=as_of)

    assert isinstance(output, TMVEOutputContract)
    assert output.player_id == player_id
    assert output.rr_relationship_state == RRRelationshipState.HISTORICAL_RR_APPEARANCE
    assert output.verified_rr_appearances == 16
    assert output.rr_seasons == ["2024"]
    assert output.membership_confidence == 1.0
    assert output.negative_verification_met is False
    assert output.review_status == "CLEAR"


# =============================================================================
# 3. Squad-Only Player Tests (Zero Invented Stats Guardrail)
# =============================================================================


def test_resolve_relationship_state_squad_only() -> None:
    """Verify squad member with 0 appearances resolves to HISTORICAL_RR_SQUAD_ONLY."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()

    squad_records = [
        {"contract_type": "Squad Inclusion", "role": "Player"},
    ]
    state = engine.resolve_relationship_state(
        player_id=player_id,
        verified_appearances=0,
        squad_records=squad_records,
    )
    assert state == RRRelationshipState.HISTORICAL_RR_SQUAD_ONLY


@pytest.mark.parametrize(
    "contract_type",
    ["Retained", "Auction Buy", "Replacement", "Draft", "Squad Inclusion"],
)
def test_squad_only_contract_types(contract_type: str) -> None:
    """Verify all valid squad contract types resolve to HISTORICAL_RR_SQUAD_ONLY with 0 appearances."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()

    state = engine.resolve_relationship_state(
        player_id=player_id,
        verified_appearances=0,
        squad_records=[{"contract_type": contract_type}],
    )
    assert state == RRRelationshipState.HISTORICAL_RR_SQUAD_ONLY


def test_verify_player_membership_squad_only_preserves_zero_stats() -> None:
    """MANDATORY GUARDRAIL: Squad member with 0 appearances retains 0 appearances and zero invented stats."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()
    as_of = date(2026, 3, 1)

    squad_rec = {
        "season_year": "2023",
        "contract_type": "Auction Buy",
        "role": "Player",
        "is_active_squad": False,
    }
    engine.register_squad_record(player_id, squad_rec)
    engine.register_appearances(player_id, 0)

    output = engine.verify_player_membership(player_id, as_of)

    assert output.rr_relationship_state == RRRelationshipState.HISTORICAL_RR_SQUAD_ONLY
    assert output.verified_rr_appearances == 0
    assert output.membership_confidence == 1.0
    assert output.rr_seasons == ["2023"]
    assert output.negative_verification_met is False
    assert output.review_status == "CLEAR"


# =============================================================================
# 4. Previously Associated Player Tests
# =============================================================================


def test_resolve_relationship_state_previously_associated() -> None:
    """Verify player with prior loan/trade/release association and 0 appearances resolves to PREVIOUSLY_ASSOCIATED."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()

    # Case A: history record with association_type = 'Loan'
    state_loan = engine.resolve_relationship_state(
        player_id=player_id,
        verified_appearances=0,
        squad_records=[],
        history_records=[{"association_type": "Loan", "season_year": "2021"}],
    )
    assert state_loan == RRRelationshipState.PREVIOUSLY_ASSOCIATED

    # Case B: squad record with contract_type = 'Trade'
    state_trade = engine.resolve_relationship_state(
        player_id=player_id,
        verified_appearances=0,
        squad_records=[{"contract_type": "Trade"}],
        history_records=[],
    )
    assert state_trade == RRRelationshipState.PREVIOUSLY_ASSOCIATED

    # Case C: squad record with contract_type = 'Released'
    state_released = engine.resolve_relationship_state(
        player_id=player_id,
        verified_appearances=0,
        squad_records=[{"contract_type": "Released"}],
        history_records=[],
    )
    assert state_released == RRRelationshipState.PREVIOUSLY_ASSOCIATED


# =============================================================================
# 5. Incomplete Records Base & Non-Inference Tests
# =============================================================================


def test_absent_player_resolves_to_unknown() -> None:
    """MANDATORY INVARIANT: Absent from incomplete records MUST yield RR_RELATIONSHIP_UNKNOWN.

    NEVER infer non-membership (NO_VERIFIED_RR_RELATIONSHIP) from dataset absence!
    """
    engine = TeamMembershipVerificationEngine()
    unknown_player_id = uuid4()
    as_of = date(2026, 3, 1)

    # Empty records
    state = engine.resolve_relationship_state(
        player_id=unknown_player_id,
        verified_appearances=0,
        squad_records=[],
        history_records=[],
    )
    assert state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN

    output = engine.verify_player_membership(unknown_player_id, as_of)
    assert output.rr_relationship_state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
    assert output.rr_current_state == RRCurrentState.UNKNOWN
    assert output.negative_verification_met is False
    assert output.membership_confidence is None
    assert output.verified_rr_appearances == 0
    assert output.review_status == "CLEAR"


# =============================================================================
# 6. Negative Verification Protocol 7-Gate Satisfaction Tests
# =============================================================================


def test_negative_verification_all_seven_gates_satisfied() -> None:
    """Verify NO_VERIFIED_RR_RELATIONSHIP returned when ALL 7 conditions of TRD §4.5 are met."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()

    met, state, reasons = engine.evaluate_negative_verification(
        player_id=player_id,
        career_years=[2022, 2023],
        squad_coverage={2022: True, 2023: True},
        scorecard_coverage={2022: True, 2023: True},
        has_tier1_2_source=True,
        human_reviewed=True,
        has_conflicts=False,
    )

    assert met is True
    assert state == RRRelationshipState.NO_VERIFIED_RR_RELATIONSHIP
    assert reasons == ["NEGATIVE_PROTOCOL_PASSED"]


def test_verify_player_membership_with_satisfied_negative_protocol() -> None:
    """Verify TMVEOutputContract when negative verification protocol is fully satisfied."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()
    as_of = date(2026, 3, 1)

    neg_data = {
        "career_years": [2021, 2022, 2023],
        "squad_coverage": {2021: True, 2022: True, 2023: True},
        "scorecard_coverage": {2021: True, 2022: True, 2023: True},
        "has_tier1_2_source": True,
        "human_reviewed": True,
        "has_conflicts": False,
    }
    engine.register_negative_evaluation(player_id, neg_data)

    output = engine.verify_player_membership(player_id, as_of)

    assert output.rr_relationship_state == RRRelationshipState.NO_VERIFIED_RR_RELATIONSHIP
    assert output.negative_verification_met is True
    assert output.membership_confidence == 1.0
    assert output.review_status == "CLEAR"
    assert output.review_reason_codes == ["NEGATIVE_PROTOCOL_PASSED"]


# =============================================================================
# 7. Negative Verification Individual Gate Failure Tests (Gates 1-7)
# =============================================================================


def test_negative_gate_1_failure_missing_historical_scope() -> None:
    """Gate 1: Incomplete or empty coverage scope fails negative verification."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()

    met, state, reasons = engine.evaluate_negative_verification(
        player_id=player_id,
        career_years=[2022],
        squad_coverage={},  # Empty coverage
        scorecard_coverage={2022: True},
        has_tier1_2_source=True,
        human_reviewed=True,
        has_conflicts=False,
    )
    assert met is False
    assert state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
    assert "MISSING_HISTORICAL_SCOPE" in reasons


def test_negative_gate_2_failure_no_career_window_overlap() -> None:
    """Gate 2: Player whose career does not overlap with active RR seasons fails."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()

    # Pre-IPL player
    met_old, state_old, reasons_old = engine.evaluate_negative_verification(
        player_id=player_id,
        career_years=[1985, 1990],
        squad_coverage={2022: True},
        scorecard_coverage={2022: True},
        has_tier1_2_source=True,
        human_reviewed=True,
        has_conflicts=False,
    )
    assert met_old is False
    assert state_old == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
    assert "NO_CAREER_WINDOW_OVERLAP" in reasons_old

    # Player only active in 2016-2017 (RR suspension seasons)
    met_susp, state_susp, reasons_susp = engine.evaluate_negative_verification(
        player_id=player_id,
        career_years=[2016, 2017],
        squad_coverage={2016: True, 2017: True},
        scorecard_coverage={2016: True, 2017: True},
        has_tier1_2_source=True,
        human_reviewed=True,
        has_conflicts=False,
    )
    assert met_susp is False
    assert state_susp == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
    assert "NO_CAREER_WINDOW_OVERLAP" in reasons_susp


def test_negative_gate_3_failure_incomplete_squad_coverage() -> None:
    """Gate 3: Missing squad coverage for an overlapping season fails."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()

    met, state, reasons = engine.evaluate_negative_verification(
        player_id=player_id,
        career_years=[2021, 2022],
        squad_coverage={2021: True, 2022: False},  # 2022 incomplete
        scorecard_coverage={2021: True, 2022: True},
        has_tier1_2_source=True,
        human_reviewed=True,
        has_conflicts=False,
    )
    assert met is False
    assert state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
    assert "INCOMPLETE_SQUAD_COVERAGE" in reasons


def test_negative_gate_4_failure_incomplete_scorecard_coverage() -> None:
    """Gate 4: Missing scorecard coverage for an overlapping season fails."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()

    met, state, reasons = engine.evaluate_negative_verification(
        player_id=player_id,
        career_years=[2021, 2022],
        squad_coverage={2021: True, 2022: True},
        scorecard_coverage={2021: True, 2022: False},  # 2022 incomplete
        has_tier1_2_source=True,
        human_reviewed=True,
        has_conflicts=False,
    )
    assert met is False
    assert state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
    assert "INCOMPLETE_SCORECARD_COVERAGE" in reasons


def test_negative_gate_5_failure_lacks_tier1_2_source() -> None:
    """Gate 5: Lacking tier-1 or tier-2 source fails negative verification."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()

    met, state, reasons = engine.evaluate_negative_verification(
        player_id=player_id,
        career_years=[2022],
        squad_coverage={2022: True},
        scorecard_coverage={2022: True},
        has_tier1_2_source=False,  # Fails gate 5
        human_reviewed=True,
        has_conflicts=False,
    )
    assert met is False
    assert state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
    assert "LACKS_TIER1_OR_TIER2_SOURCE" in reasons


def test_negative_gate_6_failure_conflicting_records() -> None:
    """Gate 6: Presence of conflicting records fails negative verification."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()

    met, state, reasons = engine.evaluate_negative_verification(
        player_id=player_id,
        career_years=[2022],
        squad_coverage={2022: True},
        scorecard_coverage={2022: True},
        has_tier1_2_source=True,
        human_reviewed=True,
        has_conflicts=True,  # Fails gate 6
    )
    assert met is False
    assert state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
    assert "CONFLICTING_RECORDS_DETECTED" in reasons


def test_negative_gate_7_failure_human_review_not_completed() -> None:
    """Gate 7: Unfinished human review fails negative verification."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()

    met, state, reasons = engine.evaluate_negative_verification(
        player_id=player_id,
        career_years=[2022],
        squad_coverage={2022: True},
        scorecard_coverage={2022: True},
        has_tier1_2_source=True,
        human_reviewed=False,  # Fails gate 7
        has_conflicts=False,
    )
    assert met is False
    assert state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
    assert "HUMAN_REVIEW_NOT_COMPLETED" in reasons


def test_negative_multiple_gate_failures_accumulated() -> None:
    """Verify multiple failing gates are all accumulated in reason_codes."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()

    met, state, reasons = engine.evaluate_negative_verification(
        player_id=player_id,
        career_years=[2022],
        squad_coverage={2022: False},  # Gate 3 fails
        scorecard_coverage={2022: False},  # Gate 4 fails
        has_tier1_2_source=False,  # Gate 5 fails
        human_reviewed=False,  # Gate 7 fails
        has_conflicts=True,  # Gate 6 fails
    )
    assert met is False
    assert state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
    assert "INCOMPLETE_SQUAD_COVERAGE" in reasons
    assert "INCOMPLETE_SCORECARD_COVERAGE" in reasons
    assert "LACKS_TIER1_OR_TIER2_SOURCE" in reasons
    assert "CONFLICTING_RECORDS_DETECTED" in reasons
    assert "HUMAN_REVIEW_NOT_COMPLETED" in reasons


# =============================================================================
# 8. Current vs Not-Current vs Unknown Resolution Tests
# =============================================================================


def test_resolve_current_membership_states() -> None:
    """Verify resolve_current_membership correctly resolves CURRENT, NOT_CURRENT, and UNKNOWN."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()
    as_of = date(2026, 3, 1)

    # 1. CURRENT: is_active_squad = True
    curr_state = engine.resolve_current_membership(
        player_id=player_id,
        as_of_date=as_of,
        squad_records=[{"is_active_squad": True}],
    )
    assert curr_state == RRCurrentState.CURRENT

    # 2. CURRENT: within active start_date and end_date
    curr_date_state = engine.resolve_current_membership(
        player_id=player_id,
        as_of_date=as_of,
        squad_records=[
            {
                "start_date": date(2026, 1, 1),
                "end_date": date(2026, 6, 1),
            }
        ],
    )
    assert curr_date_state == RRCurrentState.CURRENT

    # 3. NOT_CURRENT: is_active_squad = False
    not_curr_state = engine.resolve_current_membership(
        player_id=player_id,
        as_of_date=as_of,
        squad_records=[{"is_active_squad": False}],
    )
    assert not_curr_state == RRCurrentState.NOT_CURRENT

    # 4. NOT_CURRENT: contract_type = "Released"
    released_state = engine.resolve_current_membership(
        player_id=player_id,
        as_of_date=as_of,
        squad_records=[{"contract_type": "Released"}],
    )
    assert released_state == RRCurrentState.NOT_CURRENT

    # 5. NOT_CURRENT: expired contract end_date < as_of_date
    expired_state = engine.resolve_current_membership(
        player_id=player_id,
        as_of_date=as_of,
        squad_records=[{"end_date": date(2025, 5, 30)}],
    )
    assert expired_state == RRCurrentState.NOT_CURRENT

    # 6. UNKNOWN: empty squad records
    unknown_empty = engine.resolve_current_membership(
        player_id=player_id,
        as_of_date=as_of,
        squad_records=[],
    )
    assert unknown_empty == RRCurrentState.UNKNOWN

    # 7. UNKNOWN: is_active_squad is None without dates
    unknown_none = engine.resolve_current_membership(
        player_id=player_id,
        as_of_date=as_of,
        squad_records=[{"is_active_squad": None}],
    )
    assert unknown_none == RRCurrentState.UNKNOWN


# =============================================================================
# 9. Conflict Detection Triggering REVIEW_REQUIRED
# =============================================================================


def test_conflict_in_verification_records_triggers_review_required() -> None:
    """MANDATORY GUARDRAIL: Any conflict forces RR_RELATIONSHIP_UNKNOWN and review_status='REVIEW_REQUIRED'."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()
    as_of = date(2026, 3, 1)

    # Register an appearance and a conflicting verification record
    engine.register_squad_record(player_id, {"contract_type": "Retained"})
    engine.register_appearances(player_id, 10)
    engine.register_verification_record(
        player_id,
        {
            "verification_id": uuid4(),
            "subject_type": "player_membership",
            "subject_id": player_id,
            "verification_status": "CONFLICT",
            "notes": "Conflicting roster submission from external agency",
        },
    )

    output = engine.verify_player_membership(player_id, as_of)

    assert output.rr_relationship_state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
    assert output.review_status == "REVIEW_REQUIRED"
    assert "CONFLICTING_VERIFICATION_RECORDS" in output.review_reason_codes


def test_conflict_flag_in_negative_verification_triggers_review_required() -> None:
    """Verify conflicting evidence in negative protocol triggers REVIEW_REQUIRED."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()
    as_of = date(2026, 3, 1)

    neg_data = {
        "career_years": [2022],
        "squad_coverage": {2022: True},
        "scorecard_coverage": {2022: True},
        "has_tier1_2_source": True,
        "human_reviewed": True,
        "has_conflicts": True,  # Conflict!
    }
    engine.register_negative_evaluation(player_id, neg_data)

    output = engine.verify_player_membership(player_id, as_of)

    assert output.rr_relationship_state == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
    assert output.review_status == "REVIEW_REQUIRED"
    assert "CONFLICTING_RECORDS_DETECTED" in output.review_reason_codes


# =============================================================================
# 10. TMVERequestContract Integration and Other IPL Teams
# =============================================================================


def test_verify_player_membership_with_request_contract() -> None:
    """Verify verify_player_membership accepts TMVERequestContract as first argument."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()
    as_of = date(2026, 3, 1)

    req = TMVERequestContract(player_id=player_id, as_of_date=as_of)
    engine.register_appearances(player_id, 5)

    output = engine.verify_player_membership(req)
    assert output.player_id == player_id
    assert output.as_of_date == as_of
    assert output.verified_rr_appearances == 5
    assert output.rr_relationship_state == RRRelationshipState.HISTORICAL_RR_APPEARANCE


def test_multi_team_and_seasons_extraction() -> None:
    """Verify RR seasons and other IPL teams are correctly segregated and extracted."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()
    as_of = date(2026, 3, 1)

    # RR squad records
    engine.register_squad_record(
        player_id,
        {
            "team_name": RR_CANONICAL_NAME,
            "season_year": "2022",
            "contract_type": "Retained",
        },
    )
    engine.register_squad_record(
        player_id,
        {
            "team_name": RR_SHORT_CODE,
            "season_year": "2023",
            "contract_type": "Retained",
        },
    )
    # Other IPL team records
    engine.register_history_record(
        player_id,
        {
            "team_name": "Chennai Super Kings",
            "season_year": "2024",
            "association_type": "Played",
            "appearances": 14,
        },
    )
    engine.register_history_record(
        player_id,
        {
            "team_name": "Mumbai Indians",
            "season_year": "2020",
            "association_type": "Squad",
            "appearances": 0,
        },
    )
    engine.register_appearances(player_id, 24)

    output = engine.verify_player_membership(player_id, as_of)

    assert output.rr_seasons == ["2022", "2023"]
    assert output.other_ipl_teams == ["Chennai Super Kings", "Mumbai Indians"]
    assert output.verified_rr_appearances == 24


# =============================================================================
# 11. MockSupabaseClient Integration Tests
# =============================================================================


def test_mock_supabase_client_database_integration() -> None:
    """Verify TeamMembershipVerificationEngine queries tables from db_client."""
    mock_db = MockSupabaseClient()
    player_id = uuid4()
    vid = uuid4()
    as_of = date(2026, 3, 1)

    # Seed mock database tables
    mock_db.table("squad_memberships").insert(
        {
            "player_id": str(player_id),
            "team_name": "Rajasthan Royals",
            "season_year": "2025",
            "contract_type": "Retained",
            "is_active_squad": True,
        }
    ).execute()

    mock_db.table("player_team_history").insert(
        {
            "player_id": str(player_id),
            "team_name": "Rajasthan Royals",
            "season_year": "2025",
            "association_type": "Played",
            "appearances": 12,
        }
    ).execute()

    mock_db.table("verification_records").insert(
        {
            "verification_id": str(vid),
            "subject_type": "player_membership",
            "subject_id": str(player_id),
            "verification_status": "VERIFIED",
        }
    ).execute()

    engine = TeamMembershipVerificationEngine(db_client=mock_db)
    output = engine.verify_player_membership(player_id, as_of)

    assert output.player_id == player_id
    assert output.rr_relationship_state == RRRelationshipState.HISTORICAL_RR_APPEARANCE
    assert output.rr_current_state == RRCurrentState.CURRENT
    assert output.verified_rr_appearances == 12
    assert output.rr_seasons == ["2025"]
    assert output.evidence_verification_ids == [vid]


# =============================================================================
# 12. Negative Appearances Error Handling Tests
# =============================================================================


def test_negative_appearances_raises_error() -> None:
    """Verify negative appearances raises ValueError in both resolve and register methods."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()

    with pytest.raises(ValueError, match="verified_appearances"):
        engine.resolve_relationship_state(
            player_id=player_id,
            verified_appearances=-1,
            squad_records=[],
        )

    with pytest.raises(ValueError, match="verified_appearances"):
        engine.register_appearances(player_id, -5)


def test_negative_verification_alias() -> None:
    """Verify resolve_negative_verification alias works with in-memory recorded data."""
    engine = TeamMembershipVerificationEngine()
    player_id = uuid4()

    # Without registered data
    met_fail, state_fail, _ = engine.resolve_negative_verification(player_id, [2022])
    assert met_fail is False
    assert state_fail == RRRelationshipState.RR_RELATIONSHIP_UNKNOWN

    # With registered data
    engine.register_negative_evaluation(
        player_id,
        {
            "career_years": [2022],
            "squad_coverage": {2022: True},
            "scorecard_coverage": {2022: True},
            "has_tier1_2_source": True,
            "human_reviewed": True,
            "has_conflicts": False,
        },
    )
    met_pass, state_pass, reasons_pass = engine.resolve_negative_verification(player_id, [2022])
    assert met_pass is True
    assert state_pass == RRRelationshipState.NO_VERIFIED_RR_RELATIONSHIP
    assert reasons_pass == ["NEGATIVE_PROTOCOL_PASSED"]
