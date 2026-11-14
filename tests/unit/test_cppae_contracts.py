"""Unit tests for CPPAE contracts (TRD §6.3, Entity 31, Pydantic v2 BaseContract)."""

from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.contracts.cppae import (
    BattingPhaseSplit,
    BattingProfile,
    BowlingProfile,
    CPPAEOutput,
    FieldingProfile,
    PerStatMetric,
    SampleSizes,
    WicketkeepingProfile,
)


def test_per_stat_metric_validation():
    """Verify PerStatMetric contract validation and allowed status values."""
    stat = PerStatMetric(
        metric_id="B01",
        name="Matches (batting)",
        value=15,
        definition_ref="DATA_DICTIONARY §1 B01",
        formula="COUNT(DISTINCT match_id)",
        source_fields=["batting_innings", "matches"],
        format_tag="T20",
        sample_size=15,
        status="OBSERVED",
    )
    assert stat.metric_id == "B01"
    assert stat.value == 15
    assert stat.status == "OBSERVED"

    # Invalid status should raise ValidationError
    with pytest.raises(ValidationError):
        PerStatMetric(
            metric_id="B01",
            name="Matches (batting)",
            value=15,
            definition_ref="DATA_DICTIONARY §1 B01",
            formula="COUNT(DISTINCT match_id)",
            format_tag="T20",
            status="INVALID_STATUS",
        )


def test_batting_profile_null_safety_and_defaults():
    """Verify BattingProfile defaults and zero-denominator null safety."""
    profile = BattingProfile(
        matches=0,
        innings=0,
        runs=0,
        balls_faced=0,
        dismissals=0,
        not_outs=0,
        batting_average=None,
        strike_rate=None,
        bpps=0.0,
    )
    assert profile.batting_average is None
    assert profile.strike_rate is None
    assert profile.dot_pct is None
    assert profile.boundary_pct is None
    assert profile.dnb_count == 0
    assert profile.zero_ball_batted_count == 0


def test_bowling_profile_five_ball_overs():
    """Verify BowlingProfile format-aware overs display and economy."""
    profile = BowlingProfile(
        matches=10,
        innings=10,
        legal_balls_bowled=97,
        overs_display="19.2",
        balls_per_over=5,
        runs_conceded=120,
        wickets_taken=8,
        economy_rate=6.19,
        bowling_average=15.0,
        bwps=78.5,
    )
    assert profile.balls_per_over == 5
    assert profile.overs_display == "19.2"
    assert profile.economy_rate == 6.19


def test_fielding_and_wk_profile_coverage_classes():
    """Verify fielding and wicketkeeping profile coverage classes and no-fabrication rule."""
    f_prof = FieldingProfile(
        appearances=14,
        catches=8,
        run_outs_direct=2,
        run_outs_assisted=1,
        run_outs_total=3,
        stumpings=0,
        recorded_dropped_catches=None,
        boundary_saves=None,
        missed_opportunities=None,
        coverage_class="COVERAGE_LIMITED",
    )
    assert f_prof.recorded_dropped_catches is None
    assert f_prof.coverage_class == "COVERAGE_LIMITED"

    wk_prof = WicketkeepingProfile(
        appearances=12,
        dismissals_total=15,
        stumpings=4,
        catches=11,
        dismissals_per_appearance=1.25,
        recorded_missed_stumpings=None,
        recorded_missed_catches=None,
        coverage_class="PARTIALLY_RECORDED",
    )
    assert wk_prof.dismissals_total == 15
    assert wk_prof.recorded_missed_stumpings is None


def test_cppae_output_contract_roundtrip():
    """Verify serialization and deserialization roundtrip for CPPAEOutput."""
    pid = uuid4()
    output = CPPAEOutput(
        player_id=pid,
        canonical_name="Test Batter",
        format_tag="T20",
        window="career",
        batting=BattingProfile(
            matches=5,
            innings=5,
            runs=150,
            balls_faced=100,
            dismissals=3,
            not_outs=2,
            batting_average=50.0,
            strike_rate=150.0,
            fours=12,
            sixes=6,
            boundaries=18,
            boundary_pct=56.0,
            dot_balls=30,
            dot_pct=30.0,
            bpps=82.5,
        ),
        samples=SampleSizes(
            matches=5,
            innings=5,
            balls_faced=100,
            legal_balls_bowled=0,
        ),
        per_stat={
            "B03": PerStatMetric(
                metric_id="B03",
                name="Runs",
                value=150,
                definition_ref="DATA_DICTIONARY §1 B03",
                formula="SUM(runs_scored)",
                status="OBSERVED",
            )
        },
    )

    dumped = output.model_dump(mode="json")
    reloaded = CPPAEOutput.model_validate(dumped)

    assert reloaded.player_id == pid
    assert reloaded.canonical_name == "Test Batter"
    assert reloaded.batting is not None
    assert reloaded.batting.batting_average == 50.0
    assert "B03" in reloaded.per_stat
    assert reloaded.per_stat["B03"].value == 150


def test_contract_extra_fields_forbidden():
    """Verify that extra unknown fields raise ValidationError per BaseContract config."""
    with pytest.raises(ValidationError):
        BattingPhaseSplit(
            phase="Powerplay",
            balls_faced=20,
            runs_scored=30,
            dismissals=1,
            unknown_hallucinated_field=999,  # Extra field
        )
