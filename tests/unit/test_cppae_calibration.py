"""Unit tests for CPPAE Statistical Calibration Engine (TRD §6, §10)."""

from src.cmie.match_context import PreDeliveryState
from src.cppae.calibration import StatisticalCalibrationEngine


def test_hierarchical_prior_fallback_levels():
    """Verify hierarchical fallback across levels 1 through 4."""
    engine = StatisticalCalibrationEngine()

    # Level 1: Empirical dataset prior when sample is sufficient (>= 500 balls, >= 20 dismissals)
    prior_l1 = engine.resolve_prior(
        role="BATTER",
        format_tag="T20",
        observed_p_runs=800,
        observed_p_balls=550,
        observed_p_dismissals=25,
        observed_p_bowl_runs=700,
        observed_p_bowl_lb=520,
        balls_per_over=6,
    )
    assert prior_l1.batting_sr_prior == round((800 / 550) * 100.0, 2)
    assert prior_l1.batting_avg_prior == round(800 / 25, 2)
    assert prior_l1.bowling_econ_prior == round((700 / 520) * 6.0, 2)

    # Level 2: Tabulated default for known role and format
    prior_l2 = engine.resolve_prior(role="TOP_ORDER", format_tag="T20")
    assert prior_l2.batting_sr_prior == 135.0
    assert prior_l2.batting_avg_prior == 32.0

    # Level 3: Known role with novel format (scales T20 bowling economy by balls_per_over)
    prior_l3 = engine.resolve_prior(role="BOWLER", format_tag="T10", balls_per_over=6)
    assert prior_l3.bowling_econ_prior == 8.0

    # Level 4: Unknown role and novel format (universal default)
    prior_l4 = engine.resolve_prior(role="MYSTERY_ROLE", format_tag="T10", balls_per_over=6)
    assert prior_l4.batting_sr_prior == 135.0
    assert prior_l4.batting_avg_prior == 25.0


def test_shrinkage_undefeated_batter_null_average():
    """Verify Empirical Bayes shrinkage preserves NULL average for undefeated batter."""
    engine = StatisticalCalibrationEngine(k_bat=30.0, k_bat_avg=5.0)
    prior = engine.resolve_prior("BATTER", "T20")

    # Undefeated batter: 0 dismissals, 40 balls, 70 runs (SR 175.0)
    shrunk_sr, shrunk_avg = engine.shrink_batting_metrics(
        raw_sr=175.0,
        raw_avg=None,
        balls_faced=40,
        dismissals=0,
        prior=prior,
    )

    assert shrunk_sr is not None
    assert 138.0 < shrunk_sr < 175.0
    # Must remain strictly None (Option B preservation)
    assert shrunk_avg is None


def test_shrinkage_sensitivity_analysis():
    """Verify shrinkage sensitivity analysis across K_bat and K_bowl grids."""
    engine = StatisticalCalibrationEngine()

    deliveries = []
    states = []
    # Generate 15 matches with 3 batters and 3 bowlers
    for m in range(15):
        mid = f"M{m}"
        for b_idx in range(1, 4):
            pid = f"BAT_{b_idx}"
            # 10 balls per match
            for i in range(10):
                runs = 4 if b_idx == 1 else (2 if b_idx == 2 else 1)
                is_w = "true" if (i == 9 and b_idx != 1) else "false"
                deliveries.append({"match_id": mid, "striker_id": pid, "bowler_id": f"BOWL_{b_idx}", "runs": str(runs), "extras_type": "None", "is_wicket": is_w, "dismissal_type": "bowled" if is_w == "true" else "", "dismissed_player_id": pid if is_w == "true" else ""})
                states.append(PreDeliveryState(
                    match_id=mid, innings=1, overid=i + 1, over_ball_num=1, innings_ball_num=i + 1,
                    striker_id=pid, bowler_id=f"BOWL_{b_idx}", legal_balls_bowled=i, legal_balls_remaining=120 - i,
                    current_runs=float(i * runs), current_wickets=0, wickets_in_hand=10, crr=8.0, cdpi=0.75, mpt="HIGH", is_pressure=True,
                ))

    names = {f"BAT_{i}": f"Batter {i}" for i in range(1, 4)}
    names.update({f"BOWL_{i}": f"Bowler {i}" for i in range(1, 4)})
    appearances = {f"BAT_{i}": 15 for i in range(1, 4)}
    appearances.update({f"BOWL_{i}": 15 for i in range(1, 4)})

    sens = engine.run_shrinkage_sensitivity(
        deliveries=deliveries,
        states=states,
        player_names=names,
        match_appearances=appearances,
        top_n=3,
    )

    assert "batting_overlap_k20_k30" in sens
    assert "bowling_overlap_k30_k40" in sens
    assert sens["batting_overlap_k20_k30"] >= 0.0


def test_clustered_block_bootstrap_execution():
    """Verify clustered match-level block bootstrap generates valid 95% CIs and stability."""
    engine = StatisticalCalibrationEngine(seed=42)

    deliv_by_m = {}
    states_by_m = {}

    for m in range(12):
        mid = f"M{m}"
        d_list = []
        s_list = []
        for i in range(10):
            d_list.append({"runs": "4", "extras_type": "None", "is_wicket": "false", "dismissal_type": "", "dismissed_player_id": ""})
            s_list.append(PreDeliveryState(
                match_id=mid, innings=1, overid=i + 1, over_ball_num=1, innings_ball_num=i + 1,
                striker_id="B1", bowler_id="W1", legal_balls_bowled=i, legal_balls_remaining=120 - i,
                current_runs=float(i * 4), current_wickets=0, wickets_in_hand=10, crr=10.0, cdpi=0.8, mpt="HIGH", is_pressure=True,
            ))
        deliv_by_m[mid] = d_list
        states_by_m[mid] = s_list

    res = engine.run_clustered_bootstrap(
        deliveries_by_match=deliv_by_m,
        states_by_match=states_by_m,
        target_player_ids=["B1"],
        role="BATTER",
        n_iterations=25,
    )

    assert "B1" in res
    b1_res = res["B1"]
    assert b1_res.replicates == 25
    assert b1_res.score_ci_lower_95 <= b1_res.score_median <= b1_res.score_ci_upper_95
    assert 0.0 <= b1_res.rank_stability_pct <= 100.0
