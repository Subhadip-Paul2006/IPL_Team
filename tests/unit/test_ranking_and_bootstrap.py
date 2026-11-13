"""Unit tests for SICE ranking engine and match-level bootstrap (Workstream G)."""

from src.cppae.batting_performance import BatterPressureMetrics
from src.cppae.bowling_performance import BowlerPressureMetrics
from src.sice.ranking_engine import SiceRankingEngine


def test_ranking_batters_and_tiebreaking():
    """Verify deterministic ranking, top-10 extraction, and total ordering tiebreakers."""
    sice = SiceRankingEngine(seed=42)

    candidates = [
        BatterPressureMetrics(
            player_id="P1", canonical_name="Batter 1", match_appearances=12,
            balls_faced_total=200, runs_total=300, sr_total=150.0, avg_total=30.0,
            balls_faced_pressure=80, runs_pressure=160, fours_pressure=10, sixes_pressure=8,
            dots_pressure=15, dismissals_pressure=2, sr_pressure_raw=200.0, avg_pressure_raw=80.0,
            sr_pressure_shrunk=190.0, avg_pressure_shrunk=70.0, dot_pct_pressure=18.75,
            boundary_pct_pressure=55.0, delta_sr=50.0, bpps=85.0, is_qualified=True
        ),
        BatterPressureMetrics(
            player_id="P2", canonical_name="Batter 2", match_appearances=12,
            balls_faced_total=180, runs_total=250, sr_total=138.8, avg_total=28.0,
            balls_faced_pressure=70, runs_pressure=130, fours_pressure=8, sixes_pressure=6,
            dots_pressure=18, dismissals_pressure=3, sr_pressure_raw=185.7, avg_pressure_raw=43.3,
            sr_pressure_shrunk=178.0, avg_pressure_shrunk=40.0, dot_pct_pressure=25.7,
            boundary_pct_pressure=52.3, delta_sr=46.9, bpps=80.0, is_qualified=True
        ),
        BatterPressureMetrics(
            player_id="P3_UNQUALIFIED", canonical_name="Batter 3", match_appearances=5,
            balls_faced_total=50, runs_total=80, sr_total=160.0, avg_total=20.0,
            balls_faced_pressure=20, runs_pressure=40, fours_pressure=2, sixes_pressure=2,
            dots_pressure=5, dismissals_pressure=1, sr_pressure_raw=200.0, avg_pressure_raw=40.0,
            sr_pressure_shrunk=180.0, avg_pressure_shrunk=35.0, dot_pct_pressure=25.0,
            boundary_pct_pressure=50.0, delta_sr=40.0, bpps=90.0, is_qualified=False
        ),
    ]

    top10, reserves = sice.rank_batters(candidates, top_n=10)

    # Only qualified players should enter top-10
    assert len(top10) == 2
    assert top10[0].player_id == "P1"
    assert top10[0].score == 85.0
    assert top10[1].player_id == "P2"
    assert top10[1].score == 80.0
    assert "P3_UNQUALIFIED" not in [c.player_id for c in top10]


def test_ranking_bowlers():
    """Verify deterministic bowler ranking."""
    sice = SiceRankingEngine(seed=42)

    candidates = [
        BowlerPressureMetrics(
            player_id="B1", canonical_name="Bowler 1", match_appearances=15,
            legal_balls_total=300, runs_conceded_total=350, wickets_total=20, econ_total=7.0,
            legal_balls_pressure=100, runs_conceded_pressure=100, dots_pressure=50,
            boundaries_conceded_pressure=10, wickets_pressure=12, econ_pressure_raw=6.0,
            econ_pressure_shrunk=6.5, dot_pct_pressure=50.0, boundary_pct_pressure=10.0,
            hles=0.74, delta_econ=1.0, bwps=88.5, is_qualified=True
        ),
        BowlerPressureMetrics(
            player_id="B2", canonical_name="Bowler 2", match_appearances=15,
            legal_balls_total=280, runs_conceded_total=360, wickets_total=18, econ_total=7.71,
            legal_balls_pressure=90, runs_conceded_pressure=110, dots_pressure=40,
            boundaries_conceded_pressure=12, wickets_pressure=8, econ_pressure_raw=7.33,
            econ_pressure_shrunk=7.6, dot_pct_pressure=44.4, boundary_pct_pressure=13.3,
            hles=0.62, delta_econ=0.38, bwps=82.0, is_qualified=True
        ),
    ]

    top10, reserves = sice.rank_bowlers(candidates, top_n=10)
    assert len(top10) == 2
    assert top10[0].player_id == "B1"
    assert top10[0].score == 88.5
    assert top10[0].role == "BOWLER"
    assert top10[1].player_id == "B2"
    assert top10[1].score == 82.0
    assert top10[1].role == "BOWLER"


def test_match_level_bootstrap_execution():
    """Verify match-level clustered block bootstrap executes and populates CIs and stability."""
    from src.cmie.match_context import PreDeliveryState
    from src.sice.ranking_engine import RankedCandidate

    sice = SiceRankingEngine(seed=42)

    top_batters = [
        RankedCandidate(
            rank=1, player_id="P1", canonical_name="Batter 1", score=85.0,
            match_appearances=12, volume_total=200, volume_pressure=80,
            key_metric_raw=200.0, key_metric_shrunk=190.0, delta_metric=50.0,
            role="BATTER",
        )
    ]
    top_bowlers = [
        RankedCandidate(
            rank=1, player_id="B1", canonical_name="Bowler 1", score=88.5,
            match_appearances=12, volume_total=200, volume_pressure=80,
            key_metric_raw=6.0, key_metric_shrunk=6.5, delta_metric=1.0,
            role="BOWLER",
        )
    ]

    # 12 matches with deliveries
    deliv_by_m = {}
    states_by_m = {}
    for i in range(1, 13):
        mid = f"M{i}"
        delivs = [
            {"runs": "4", "extras_type": "None", "is_wicket": "false", "dismissal_type": "", "dismissed_player_id": ""},
            {"runs": "0", "extras_type": "None", "is_wicket": "true", "dismissal_type": "bowled", "dismissed_player_id": "P2"},
        ]
        sts = [
            PreDeliveryState(
                match_id=mid, innings=1, overid=1, over_ball_num=1, innings_ball_num=1,
                striker_id="P1", bowler_id="B1", legal_balls_bowled=0, legal_balls_remaining=120,
                current_runs=0.0, current_wickets=0, wickets_in_hand=10, crr=0.0, cdpi=0.75, mpt="HIGH", is_pressure=True,
            ),
            PreDeliveryState(
                match_id=mid, innings=1, overid=1, over_ball_num=2, innings_ball_num=2,
                striker_id="P1", bowler_id="B1", legal_balls_bowled=1, legal_balls_remaining=119,
                current_runs=4.0, current_wickets=0, wickets_in_hand=10, crr=24.0, cdpi=0.75, mpt="HIGH", is_pressure=True,
            ),
        ]
        deliv_by_m[mid] = delivs
        states_by_m[mid] = sts

    sice.run_match_level_bootstrap(
        deliv_by_m, states_by_m, {"P1": "Batter 1", "B1": "Bowler 1"}, {"P1": 12, "B1": 12},
        top_batters, top_bowlers, n_iterations=20,
    )

    assert top_batters[0].score_ci_lower is not None
    assert top_batters[0].score_ci_upper is not None
    assert top_batters[0].top10_stability_pct is not None
    assert top_bowlers[0].score_ci_lower is not None
    assert top_bowlers[0].score_ci_upper is not None
    assert top_bowlers[0].top10_stability_pct is not None
