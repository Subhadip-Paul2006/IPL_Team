"""Unit tests for CPPAE Feature Store Persistence and Entity 29/31 Compatibility."""

from uuid import uuid4

from src.contracts.cppae import (
    BattingProfile,
    BowlingProfile,
    CPPAEOutput,
    FieldingProfile,
    MatchContributionProfile,
    SampleSizes,
    WicketkeepingProfile,
)
from src.contracts.features import DerivedFeature
from src.contracts.team_builder import UserTeam, UserTeamPlayer
from src.cppae.persistence import FeatureStorePublisher, OfflineFeatureStoreAdapter


def test_feature_store_publisher_build_features_t20():
    """Verify FeatureStorePublisher correctly transforms CPPAEOutput into TRD Entity 31 records."""
    publisher = FeatureStorePublisher(model_version="v2.1")
    pid = uuid4()

    output = CPPAEOutput(
        player_id=pid,
        canonical_name="Elite All-Rounder",
        format_tag="T20",
        window="career",
        batting=BattingProfile(
            matches=15,
            innings=15,
            runs=450,
            balls_faced=300,
            dismissals=10,
            batting_average=45.0,
            strike_rate=150.0,
            fours=35,
            sixes=20,
            boundaries=55,
            boundary_pct=57.78,
            dot_balls=90,
            dot_pct=30.0,
            bpps=84.2,
        ),
        bowling=BowlingProfile(
            matches=15,
            innings=15,
            legal_balls_bowled=240,
            overs_display="40.0",
            runs_conceded=300,
            wickets_taken=18,
            economy_rate=7.5,
            bowling_average=16.67,
            bwps=82.1,
            hles=0.65,
        ),
        fielding=FieldingProfile(
            appearances=15,
            catches=10,
            run_outs_total=3,
        ),
        wicketkeeping=WicketkeepingProfile(
            appearances=0,
            dismissals_total=0,
        ),
        match_contribution=MatchContributionProfile(
            player_of_match_awards=3,
            batting_contribution_pct=28.5,
            bowling_wicket_share_pct=22.0,
            additive_composite=50.5,
        ),
        samples=SampleSizes(
            matches=15,
            innings=30,
            balls_faced=300,
            legal_balls_bowled=240,
        ),
    )

    features = publisher.build_derived_features(output)
    assert len(features) > 20

    # Verify all are valid DerivedFeature instances
    for f in features:
        assert isinstance(f, DerivedFeature)
        assert f.player_id == pid
        assert f.format_tag == "T20"
        assert f.model_version == "v2.1"
        assert f.feature_group in {
            "Batting",
            "Bowling",
            "Fielding",
            "Wicketkeeping",
            "Matchup Matrix",
            "Clutch & Pressure",
            "Venue Baselines",
            "Squad Intelligence",
            "Career Coverage",
        }
        assert f.status in {"OBSERVED", "DERIVED", "MODEL_INFERRED", "NOT_COMPUTABLE", "DEFERRED"}


def test_feature_store_publisher_hundred_deferred_status():
    """Verify that derived rate metrics for The Hundred carry status = 'DEFERRED'."""
    publisher = FeatureStorePublisher(model_version="v2.1")
    pid = uuid4()

    output = CPPAEOutput(
        player_id=pid,
        canonical_name="Hundred Player",
        format_tag="HUNDRED",
        window="career",
        batting=BattingProfile(
            matches=10,
            innings=10,
            runs=220,
            balls_faced=150,
            dismissals=8,
            batting_average=27.5,
            strike_rate=146.67,
            bpps=75.0,
        ),
        bowling=BowlingProfile(
            matches=10,
            innings=10,
            legal_balls_bowled=100,
            overs_display="20.0",
            balls_per_over=5,
            runs_conceded=130,
            wickets_taken=7,
            economy_rate=6.5,
            bowling_average=18.57,
            bwps=76.0,
        ),
        samples=SampleSizes(matches=10, innings=20, balls_faced=150, legal_balls_bowled=100),
    )

    features = publisher.build_derived_features(output)

    # Check that rate metrics for The Hundred carry status = 'DEFERRED' per Decision 2
    econ_feat = next(f for f in features if f.feature_name == "economy_rate")
    sr_feat = next(f for f in features if f.feature_name == "strike_rate")
    avg_feat = next(f for f in features if f.feature_name == "batting_average")

    assert econ_feat.status == "DEFERRED"
    assert sr_feat.status == "DEFERRED"
    assert avg_feat.status == "DEFERRED"

    # Raw counts remain OBSERVED
    runs_feat = next(f for f in features if f.feature_name == "runs")
    assert runs_feat.status == "OBSERVED"

    # Even if batting_average or economy_rate is None (e.g. undefeated / 0 dismissals), status is DEFERRED
    output_none = CPPAEOutput(
        player_id=pid,
        canonical_name="Hundred Undefeated",
        format_tag="HUNDRED",
        window="career",
        batting=BattingProfile(matches=1, innings=1, runs=30, balls_faced=15, dismissals=0, batting_average=None),
        bowling=BowlingProfile(matches=1, innings=1, legal_balls_bowled=0, economy_rate=None),
        samples=SampleSizes(matches=1, innings=1, balls_faced=15, legal_balls_bowled=0),
    )
    features_none = publisher.build_derived_features(output_none)
    avg_feat_none = next(f for f in features_none if f.feature_name == "batting_average")
    econ_feat_none = next(f for f in features_none if f.feature_name == "economy_rate")
    assert avg_feat_none.status == "DEFERRED"
    assert econ_feat_none.status == "DEFERRED"


def test_offline_feature_store_adapter_operations():
    """Verify offline mock adapter operations without live PostgreSQL connection."""
    adapter = OfflineFeatureStoreAdapter()
    pid = uuid4()

    f1 = DerivedFeature(
        player_id=pid,
        feature_group="Batting",
        feature_name="runs",
        feature_value_numeric=500.0,
        calculation_window="career",
        format_tag="T20",
        status="OBSERVED",
    )
    f2 = DerivedFeature(
        player_id=pid,
        feature_group="Bowling",
        feature_name="wickets",
        feature_value_numeric=25.0,
        calculation_window="career",
        format_tag="T20",
        status="OBSERVED",
    )

    adapter.insert_features_batch([f1, f2])
    assert adapter.count() == 2

    # Query by player
    retrieved = adapter.get_features_by_player(pid)
    assert len(retrieved) == 2

    # Query with group filter
    bat_only = adapter.get_features_by_player(pid, feature_group="Batting")
    assert len(bat_only) == 1
    assert bat_only[0].feature_name == "runs"


def test_entity_29_schema_compatibility():
    """Verify TRD Entity 29 (user_teams) compatibility is preserved alongside Entity 31."""
    team_id = uuid4()
    p1 = uuid4()

    user_team = UserTeam(
        team_id=team_id,
        team_name="Rajasthan Royals Optimal XI",
        created_by="Chief Analyst",
        target_season="2027",
    )
    assert user_team.team_name == "Rajasthan Royals Optimal XI"

    player_rel = UserTeamPlayer(
        user_team_id=team_id,
        player_id=p1,
        assigned_role="Opening Batter",
        batting_order=1,
        is_captain=False,
    )
    assert player_rel.assigned_role == "Opening Batter"
    assert player_rel.batting_order == 1
