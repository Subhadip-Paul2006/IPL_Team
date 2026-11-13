"""Unit tests verifying instantiation and validation across all 33 TRD entity contracts."""

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from src.contracts import (
    BattingInnings,
    BowlingSpell,
    Competition,
    DataSource,
    Delivery,
    DerivedFeature,
    EligibilityPolicy,
    FieldingEvent,
    Innings,
    Match,
    PitchCondition,
    Player,
    PlayerAlias,
    PlayerAvailability,
    PlayerAward,
    PlayerCompetitionHistory,
    PlayerEligibility,
    PlayerInjury,
    PlayerMembershipState,
    PlayerTeamHistory,
    RankingConfiguration,
    RankingRun,
    Season,
    SourceRecord,
    SquadMembership,
    Team,
    TeamSeasonParticipation,
    UserTeam,
    UserTeamPlayer,
    Venue,
    VerificationRecord,
    WeatherCondition,
    WicketkeepingEvent,
)


def test_domain_1_provenance_contracts() -> None:
    """Verify Entity 1, 2, 3: DataSource, SourceRecord, VerificationRecord."""
    src = DataSource(
        source_name="CricSheet IPL Archive",
        source_type="JSON Feed",
        license_type="ODC-By",
        update_cadence="Static",
        data_steward="CricSheet Maintainers",
    )
    assert src.source_name == "CricSheet IPL Archive"

    rec = SourceRecord(
        source_id=src.source_id,
        external_entity_id="MATCH-101",
        raw_payload={"info": {"match_type": "T20"}},
        payload_sha256="b" * 64,
    )
    assert rec.processing_status == "Pending"

    ver = VerificationRecord(
        subject_type="player_identity",
        subject_id=uuid4(),
        evidence_tier=1,
        verification_status="VERIFIED",
        confidence=1.0,
    )
    assert ver.confidence == 1.0


def test_domain_2_player_contracts() -> None:
    """Verify Entity 4, 5: Player, PlayerAlias."""
    p = Player(
        canonical_name="Sanju Samson",
        nationality="India",
        primary_role="Wicketkeeper Batter",
        batting_hand="Right",
        identity_status="RESOLVED",
    )
    assert p.canonical_name == "Sanju Samson"

    alias = PlayerAlias(
        player_id=p.player_id,
        alias_name="SV Samson",
        source_id=uuid4(),
    )
    assert alias.alias_name == "SV Samson"


def test_domain_3_teams_and_competitions_contracts() -> None:
    """Verify Entity 6, 7, 8, 9, 10, 11, 12."""
    v = Venue(stadium_name="Sawai Mansingh Stadium", city="Jaipur", country="India")
    t = Team(team_name="Rajasthan Royals", short_code="RR", home_venue_id=v.venue_id)
    c = Competition(
        name="IPL",
        competition_type="Domestic Franchise T20",
        governing_body="BCCI",
        country="India",
    )
    s = Season(
        competition_id=c.competition_id,
        season_year="2024",
        start_date=date(2024, 3, 22),
        end_date=date(2024, 5, 26),
    )
    TeamSeasonParticipation(
        team_id=t.team_id,
        season_id=s.season_id,
        participation_status="PARTICIPATING",
    )
    SquadMembership(
        player_id=uuid4(),
        team_id=t.team_id,
        season_id=s.season_id,
        contract_type="Retained",
    )
    pth = PlayerTeamHistory(
        player_id=uuid4(),
        team_id=t.team_id,
        season_year="2024",
        association_type="Played",
        appearances=14,
    )
    assert pth.appearances == 14


def test_domain_4_match_and_delivery_contracts() -> None:
    """Verify Entity 13, 14, 15: Match, Innings, Delivery."""
    h_team = uuid4()
    a_team = uuid4()
    m = Match(
        season_id=uuid4(),
        venue_id=uuid4(),
        match_date=date(2024, 4, 1),
        home_team_id=h_team,
        away_team_id=a_team,
        outcome_type="runs",
        win_margin_runs=12,
        status="Completed",
    )
    inn = Innings(
        match_id=m.match_id,
        innings_number=1,
        batting_team_id=h_team,
        bowling_team_id=a_team,
        total_runs=190,
    )
    deliv = Delivery(
        innings_id=inn.innings_id,
        season_year="2024",
        over_number=0,
        ball_in_over=1,
        delivery_sequence=1,
        batter_id=uuid4(),
        bowler_id=uuid4(),
        non_striker_id=uuid4(),
        runs_batter=4,
        runs_extras=0,
        runs_total=4,
    )
    assert deliv.runs_total == 4


def test_domain_5_scorecard_contracts() -> None:
    """Verify Entity 16, 17, 18, 19: BattingInnings, BowlingSpell, FieldingEvent, WicketkeepingEvent."""
    bi = BattingInnings(
        innings_id=uuid4(),
        player_id=uuid4(),
        team_id=uuid4(),
        is_not_out=False,
        runs_scored=52,
        balls_faced=32,
        strike_rate=162.5,
    )
    bs = BowlingSpell(
        innings_id=uuid4(),
        player_id=uuid4(),
        team_id=uuid4(),
        legal_balls_bowled=24,
        runs_conceded=30,
        wickets_taken=3,
        bowling_average=10.0,
        economy_rate=7.5,
    )
    fe = FieldingEvent(
        player_id=uuid4(),
        event_type="Catch",
        provenance_tier="OFFICIALLY_REPORTED",
    )
    wk = WicketkeepingEvent(
        innings_id=uuid4(),
        player_id=uuid4(),
        match_id=uuid4(),
        appearances=1,
        stumpings=1,
        catches=2,
        provenance_tier="OFFICIALLY_REPORTED",
    )
    assert bi.runs_scored == 52
    assert bs.wickets_taken == 3
    assert fe.event_type == "Catch"
    assert wk.catches == 2


def test_domain_4b_condition_contracts() -> None:
    """Verify Entity 20, 21: PitchCondition, WeatherCondition."""
    pc = PitchCondition(
        match_id=uuid4(),
        venue_id=uuid4(),
        pitch_pace_rating=7.5,
        ratings_methodology_version="v1.0",
        provenance_tier="MODEL_INFERRED",
    )
    wc = WeatherCondition(
        match_id=uuid4(),
        observation_timestamp=datetime.now(UTC),
        temperature_celsius=32.5,
        relative_humidity_pct=60.0,
    )
    assert pc.pitch_pace_rating == 7.5
    assert wc.temperature_celsius == 32.5


def test_domain_6_career_and_eligibility_contracts() -> None:
    """Verify Entity 22, 23, 24, 25, 26, 27, 28."""
    pa = PlayerAvailability(
        player_id=uuid4(),
        season_id=uuid4(),
        start_date=date(2024, 3, 20),
        end_date=date(2024, 5, 30),
    )
    pi = PlayerInjury(
        player_id=uuid4(),
        injury_type="Hamstring Strain",
        severity="Moderate",
    )
    paw = PlayerAward(
        player_id=uuid4(),
        award_type="Player of the Match",
    )
    pch = PlayerCompetitionHistory(
        player_id=uuid4(),
        competition_id=uuid4(),
        season_year="2024",
        coverage_status="VERIFIED_PARTICIPATION",
    )
    pms = PlayerMembershipState(
        player_id=uuid4(),
        as_of_date=date(2024, 1, 1),
        rr_relationship_state="HISTORICAL_RR_APPEARANCE",
        rr_current_state="CURRENT",
    )
    ep = EligibilityPolicy(
        season_id=uuid4(),
        effective_date=date(2024, 1, 1),
        rule_source="BCCI IPL 2024 Player Regulations §4",
    )
    pe = PlayerEligibility(
        player_id=uuid4(),
        policy_id=ep.policy_id,
        eligibility_status="NOT_ASSESSED",
    )
    assert pa.start_date == date(2024, 3, 20)
    assert pi.severity == "Moderate"
    assert paw.award_type == "Player of the Match"
    assert pch.coverage_status == "VERIFIED_PARTICIPATION"
    assert pms.rr_current_state == "CURRENT"
    assert pe.eligibility_status == "NOT_ASSESSED"


def test_domain_7_user_team_contracts() -> None:
    """Verify Entity 29, 30: UserTeam, UserTeamPlayer."""
    ut = UserTeam(team_name="Dream Rajasthan XI", target_season="2027")
    utp = UserTeamPlayer(
        user_team_id=ut.team_id,
        player_id=uuid4(),
        assigned_role="Captain",
        batting_order=3,
        is_captain=True,
    )
    assert ut.team_name == "Dream Rajasthan XI"
    assert utp.is_captain is True


def test_domain_8_features_contract() -> None:
    """Verify Entity 31: DerivedFeature."""
    df = DerivedFeature(
        player_id=uuid4(),
        feature_group="Batting",
        feature_name="powerplay_strike_rate",
        feature_value_numeric=155.8,
        calculation_window="IPL_2022_2024",
        format_tag="T20",
        status="DERIVED",
    )
    assert df.feature_value_numeric == 155.8
    assert df.format_tag == "T20"


def test_domain_9_ranking_contracts() -> None:
    """Verify Entity 32, 33: RankingConfiguration, RankingRun."""
    rc = RankingConfiguration(
        config_version="RK-1.0.0",
        target_season_id=uuid4(),
        policy_id=uuid4(),
        evaluation_date=date(2024, 3, 1),
        ordering_json={"metric": "overall_score", "direction": "desc"},
    )
    rr = RankingRun(
        config_id=rc.config_id,
        data_snapshot_sha256="c" * 64,
        candidate_pool={"count": 50},
        top10=[{"rank": 1, "player": "Alpha"}],
    )
    assert rc.config_version == "RK-1.0.0"
    assert rr.data_snapshot_sha256 == "c" * 64


def test_contract_validation_errors() -> None:
    """Verify that domain validation errors are raised on invariant violations."""
    # 1. Invalid primary_role
    with pytest.raises(ValueError):
        Player(canonical_name="Invalid Role Player", nationality="India", primary_role="Coach")

    # 2. Season start after end
    with pytest.raises(ValueError):
        Season(
            competition_id=uuid4(),
            season_year="2024",
            start_date=date(2024, 6, 1),
            end_date=date(2024, 5, 1),
        )

    # 3. Match identical home and away teams
    same_team = uuid4()
    with pytest.raises(ValueError):
        Match(
            season_id=uuid4(),
            venue_id=uuid4(),
            match_date=date(2024, 4, 1),
            home_team_id=same_team,
            away_team_id=same_team,
            outcome_type="runs",
            status="Scheduled",
        )

    # 4. Delivery total runs mismatch
    with pytest.raises(ValueError):
        Delivery(
            innings_id=uuid4(),
            season_year="2024",
            over_number=0,
            ball_in_over=1,
            delivery_sequence=1,
            batter_id=uuid4(),
            bowler_id=uuid4(),
            non_striker_id=uuid4(),
            runs_batter=4,
            runs_extras=1,
            runs_total=6,  # Should be 5
        )
