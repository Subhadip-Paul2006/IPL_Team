"""End-to-end integration tests for CPPAEEngine master facade (TRD §6.3)."""

from uuid import uuid4

from src.cmie.match_context import PreDeliveryState
from src.contracts.cppae import CPPAEOutput
from src.contracts.scorecard import FieldingEvent
from src.cppae.engine import CPPAEEngine
from src.cppae.persistence import OfflineFeatureStoreAdapter


def test_cppae_engine_analyse_all_rounder_full_pipeline():
    """Verify CPPAEEngine.analyse() end-to-end execution for an all-rounder."""
    adapter = OfflineFeatureStoreAdapter()
    engine = CPPAEEngine(feature_adapter=adapter)

    pid = uuid4()
    pid_str = str(pid)

    # Deliveries: 2 matches
    deliveries = []
    states = []

    # Match 1: Player bats (20 balls, 36 runs, 1 four, 2 sixes, not out)
    # Player bowls (24 balls, 28 runs, 2 wickets, 12 dots)
    for i in range(20):
        runs = 4 if i == 0 else (6 if i in (5, 10) else (1 if i % 2 == 0 else 0))
        deliveries.append({
            "match_id": "M1", "innings": 1, "over_number": i // 6, "striker_id": pid_str, "bowler_id": "OPP_B1",
            "runs": runs, "extras_type": "None", "batting_team_id": "TEAM_RR", "is_wicket": "false",
        })
        states.append(PreDeliveryState(
            match_id="M1", innings=1, overid=(i // 6) + 1, over_ball_num=(i % 6) + 1, innings_ball_num=i + 1,
            striker_id=pid_str, bowler_id="OPP_B1", legal_balls_bowled=i, legal_balls_remaining=120 - i,
            current_runs=float(i * 1.5), current_wickets=1, wickets_in_hand=9, crr=9.0, cdpi=0.75, mpt="HIGH", is_pressure=True,
        ))

    for i in range(24):
        is_w = "true" if i in (11, 23) else "false"
        d_type = "bowled" if is_w == "true" else ""
        runs = 0 if i % 2 == 0 else 2
        deliveries.append({
            "match_id": "M1", "innings": 2, "over_number": i // 6, "striker_id": "OPP_BAT", "bowler_id": pid_str,
            "runs": runs, "extras_type": "None", "bowling_team_id": "TEAM_RR", "is_wicket": is_w, "dismissal_type": d_type, "dismissed_player_id": "OPP_BAT",
        })
        states.append(PreDeliveryState(
            match_id="M1", innings=2, overid=(i // 6) + 1, over_ball_num=(i % 6) + 1, innings_ball_num=i + 1,
            striker_id="OPP_BAT", bowler_id=pid_str, legal_balls_bowled=i, legal_balls_remaining=120 - i,
            current_runs=float(i * 1.2), current_wickets=1, wickets_in_hand=9, crr=7.2, cdpi=0.80, mpt="HIGH", is_pressure=True,
        ))

    matches = [
        {"match_id": "M1", "winner_id": "TEAM_RR", "outcome_type": "runs", "player_of_match": pid_str}
    ]

    f_events = [
        FieldingEvent(player_id=pid, event_type="Catch", is_recorded_opportunity=True, provenance_tier="DIRECTLY_MEASURED")
    ]

    output = engine.analyse(
        player_id=pid,
        deliveries=deliveries,
        states=states,
        matches=matches,
        fielding_events=f_events,
        player_names={pid_str: "Rajasthan Royals Hero"},
        format_tag="T20",
        persist_features=True,
    )

    assert isinstance(output, CPPAEOutput)
    assert output.player_id == pid
    assert output.canonical_name == "Rajasthan Royals Hero"
    assert output.format_tag == "T20"

    # Batting assertions
    assert output.batting is not None
    assert output.batting.balls_faced == 20
    assert output.batting.runs > 0
    # Undefeated batter in this window -> average must be None and Option B tag set
    assert output.batting.batting_average is None
    assert output.batting.profile_tag == "UNDEFEATED_IN_WINDOW"

    # Bowling assertions
    assert output.bowling is not None
    assert output.bowling.legal_balls_bowled == 24
    assert output.bowling.overs_display == "4.0"
    assert output.bowling.wickets_taken == 2
    assert output.bowling.bowling_average is not None
    assert output.bowling.economy_rate is not None

    # Fielding assertions
    assert output.fielding is not None
    assert output.fielding.catches == 1

    # Match contribution assertions
    assert output.match_contribution is not None
    assert output.match_contribution.player_of_match_awards == 1
    assert output.match_contribution.batting_contribution_pct is not None
    assert output.match_contribution.additive_composite is not None

    # Sample sizes
    assert output.samples.balls_faced == 20
    assert output.samples.legal_balls_bowled == 24

    # Per stat dictionary completeness
    assert "B01" in output.per_stat
    assert "B03" in output.per_stat
    assert "B05" in output.per_stat
    assert "B06" in output.per_stat
    assert "W01" in output.per_stat
    assert "W02" in output.per_stat
    assert "W06" in output.per_stat
    assert "M01" in output.per_stat
    assert "M07" in output.per_stat

    # Persistence verification
    assert adapter.count() > 15
    stored_feats = adapter.get_features_by_player(pid)
    assert len(stored_feats) > 15


def test_cppae_engine_the_hundred_rate_metrics_retention_as_deferred():
    """Verify that in The Hundred format, derived rate metrics are strictly marked DEFERRED."""
    engine = CPPAEEngine()
    pid = uuid4()
    pid_str = str(pid)

    deliveries = [
        {"match_id": "M_HND", "innings": 1, "over_number": 0, "striker_id": pid_str, "bowler_id": "B1", "runs": 4, "extras_type": "None", "is_wicket": "false"},
        {"match_id": "M_HND", "innings": 1, "over_number": 0, "striker_id": pid_str, "bowler_id": "B1", "runs": 1, "extras_type": "None", "is_wicket": "false"},
        {"match_id": "M_HND", "innings": 2, "over_number": 0, "striker_id": "S1", "bowler_id": pid_str, "runs": 2, "extras_type": "None", "is_wicket": "false"},
        {"match_id": "M_HND", "innings": 2, "over_number": 0, "striker_id": "S1", "bowler_id": pid_str, "runs": 0, "extras_type": "None", "is_wicket": "false"},
    ]

    output = engine.analyse(
        player_id=pid,
        deliveries=deliveries,
        format_tag="HUNDRED",
        persist_features=False,
    )

    assert output.format_tag == "HUNDRED"
    # Batting strike rate and average must be DEFERRED in The Hundred per Decision 2
    assert output.per_stat["B06"].status == "DEFERRED"
    assert output.per_stat["B05"].status == "DEFERRED"
    assert output.per_stat["W06"].status == "DEFERRED"

    # Bowling economy must use 5-ball semantics even while status is DEFERRED
    assert output.bowling is not None
    assert output.bowling.balls_per_over == 5
    # 2 runs in 2 legal balls -> (2 / 2) * 5 = 5.0 (NOT 6.0)
    assert output.bowling.economy_rate == 5.0
    assert output.bowling.overs_display == "0.2"


def test_cppae_engine_empty_deliveries_null_propagation():
    """Verify that analyzing a player with 0 deliveries returns safe NULL metrics without crash."""
    engine = CPPAEEngine()
    pid = uuid4()

    output = engine.analyse(
        player_id=pid,
        deliveries=[],
        format_tag="T20",
        persist_features=False,
    )

    assert output.samples.balls_faced == 0
    assert output.samples.legal_balls_bowled == 0
    assert output.batting is not None
    assert output.batting.batting_average is None
    assert output.batting.strike_rate is None
    assert output.bowling is not None
    assert output.bowling.economy_rate is None
    assert output.bowling.bowling_average is None
    assert output.per_stat["B05"].null_reason is not None
    assert output.per_stat["W06"].null_reason is not None


def test_cppae_engine_specialist_keeper_samples_matches():
    """Verify that a specialist wicketkeeper/fielder with 0 balls faced/bowled retains accurate match sample count."""
    engine = CPPAEEngine()
    pid = uuid4()
    pid_str = str(pid)

    # 4 playing XI rosters with this player
    playing_xi = [[pid_str] for _ in range(4)]

    output = engine.analyse(
        player_id=pid,
        deliveries=[],
        playing_xi_rosters=playing_xi,
        persist_features=False,
    )

    assert output.fielding is not None
    assert output.fielding.appearances == 4
    # Must reflect playing appearances, NOT 0
    assert output.samples.matches == 4
    assert output.per_stat["M01"].sample_size == 4
