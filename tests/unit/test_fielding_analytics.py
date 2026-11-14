"""Unit tests for CPPAE Fielding and Wicketkeeping Analytics (F01–F09, WK-01..03)."""

from uuid import uuid4

from src.contracts.scorecard import FieldingEvent, WicketkeepingEvent
from src.cppae.fielding_engine import FieldingEngine


def test_fielding_profile_evidence_boundaries_and_no_inference():
    """Verify F01-F07: catches, run-outs, absence of record != 0, and inference prohibited."""
    engine = FieldingEngine()
    pid = uuid4()
    pid_str = str(pid)

    # Dataset with catches and runouts but NO dropped catches or boundary saves recorded
    events = [
        FieldingEvent(
            player_id=pid,
            event_type="Catch",
            is_recorded_opportunity=True,
            provenance_tier="DIRECTLY_MEASURED",
        ),
        FieldingEvent(
            player_id=pid,
            event_type="Catch",
            is_recorded_opportunity=True,
            provenance_tier="DIRECTLY_MEASURED",
        ),
        FieldingEvent(
            player_id=pid,
            event_type="Run Out Thrower",
            is_recorded_opportunity=True,
            provenance_tier="DIRECTLY_MEASURED",
        ),
    ]

    playing_xi = [
        [pid_str, "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10", "P11"],
        [pid_str, "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10", "P11"],
    ]

    profile = engine.calculate_fielding_profile(
        player_id=pid,
        fielding_events=events,
        playing_xi_rosters=playing_xi,
    )

    assert profile.appearances == 2
    assert profile.catches == 2
    assert profile.run_outs_direct == 1
    assert profile.run_outs_total == 1
    # Crucial domain rule: absence from scorecard is NOT evidence of zero drops!
    assert profile.recorded_dropped_catches is None
    assert profile.boundary_saves is None
    # Crucial domain rule: missed opportunities cannot be inferred!
    assert profile.missed_opportunities is None
    assert profile.coverage_class == "PARTIALLY_RECORDED"


def test_fielding_explicit_drops_and_boundary_saves():
    """Verify dropped catches and boundary saves are recorded when explicitly tracked."""
    engine = FieldingEngine()
    pid = uuid4()

    events = [
        FieldingEvent(
            player_id=pid,
            event_type="Dropped Catch",
            is_recorded_opportunity=True,
            provenance_tier="DIRECTLY_MEASURED",
        ),
        FieldingEvent(
            player_id=pid,
            event_type="Boundary Save",
            is_recorded_opportunity=True,
            runs_saved=3,
            provenance_tier="DIRECTLY_MEASURED",
        ),
    ]

    playing_xi = [[str(pid)]]

    profile = engine.calculate_fielding_profile(
        player_id=pid,
        fielding_events=events,
        playing_xi_rosters=playing_xi,
    )

    assert profile.recorded_dropped_catches == 1
    assert profile.boundary_saves == 1
    assert profile.coverage_class == "FULLY_RECORDED"


def test_wicketkeeping_profile_f08_f09_and_wk_series():
    """Verify F08-F09 and WK-01..03 wicketkeeping metrics."""
    engine = FieldingEngine()
    pid = uuid4()
    inn_id = uuid4()
    mid = uuid4()

    wk_events = [
        WicketkeepingEvent(
            innings_id=inn_id,
            match_id=mid,
            player_id=pid,
            appearances=5,
            stumpings=3,
            catches=8,
            missed_stumpings=1,
            missed_catches=2,
            provenance_tier="DIRECTLY_MEASURED",
        )
    ]

    profile = engine.calculate_wicketkeeping_profile(player_id=pid, wk_events=wk_events)

    # F08 appearances
    assert profile.appearances == 5
    # F09 total dismissals = 3 + 8 = 11
    assert profile.dismissals_total == 11
    assert profile.stumpings == 3
    # WK-01 keeper catches
    assert profile.catches == 8
    # Dismissals per appearance: 11 / 5 = 2.2
    assert profile.dismissals_per_appearance == 2.2
    # WK-02 and WK-03
    assert profile.recorded_missed_stumpings == 1
    assert profile.recorded_missed_catches == 2
    assert profile.coverage_class == "FULLY_RECORDED"
