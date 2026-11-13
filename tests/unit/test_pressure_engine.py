"""Unit tests for CMIE match context and CDPI calculation (Workstream D)."""

from src.cmie.match_context import MatchContextEngine


def test_cdpi_pre_delivery_temporal_causality():
    """Verify features reflect state strictly BEFORE delivery (0 leakage)."""
    engine = MatchContextEngine()
    match_info = {"match_id": "M1", "first_inn_revised_overs": "", "second_inn_revised_overs": ""}

    inns = {
        1: [
            {"overid": "1", "over_ball_num": "1", "innings_ball_num": "1", "runs": "4", "extras_type": "None", "striker_id": "P1", "bowler_id": "B1", "is_wicket": "false", "dismissal_type": ""},
            {"overid": "1", "over_ball_num": "2", "innings_ball_num": "2", "runs": "0", "extras_type": "None", "striker_id": "P1", "bowler_id": "B1", "is_wicket": "false", "dismissal_type": ""},
        ]
    }

    states = engine.process_match_deliveries(match_info, inns)
    assert len(states) == 2

    # Ball 1 pre-state: 0 legal balls bowled, 0 runs, 120 remaining
    s1 = states[0]
    assert s1.legal_balls_bowled == 0
    assert s1.current_runs == 0.0
    assert s1.legal_balls_remaining == 120

    # Ball 2 pre-state: 1 legal ball bowled, 4 runs, 119 remaining
    s2 = states[1]
    assert s2.legal_balls_bowled == 1
    assert s2.current_runs == 4.0
    assert s2.legal_balls_remaining == 119


def test_cdpi_mpt_tier_classification():
    """Verify deterministic MPT classification: LOW < 0.40, MED [0.4, 0.6), HIGH [0.6, 0.8), EXT >= 0.80."""
    engine = MatchContextEngine()
    match_info = {"match_id": "M_CHASE", "revised_target": "200"}

    # High pressure chase situation: 18 balls remaining, 50 runs needed, 7 wickets down
    inns = {
        2: [
            {"overid": "18", "over_ball_num": "1", "innings_ball_num": "103", "runs": "1", "extras_type": "None", "striker_id": "P1", "bowler_id": "B1", "is_wicket": "false", "dismissal_type": ""}
        ]
    }

    # Pre-populate innings 1 total for default target
    states = engine.process_match_deliveries(match_info, inns, inn1_total=199)
    assert len(states) == 1
    st = states[0]
    assert st.innings == 2
    assert 0.0 <= st.cdpi <= 1.0
    assert st.mpt in ("LOW", "MEDIUM", "HIGH", "EXTREME")


def test_super_over_quarantine():
    """Verify innings > 2 are categorized as SUPER_OVER and quarantined."""
    engine = MatchContextEngine()
    match_info = {"match_id": "M_SO"}
    inns = {
        3: [
            {"overid": "1", "over_ball_num": "1", "innings_ball_num": "1", "runs": "6", "extras_type": "None", "striker_id": "P1", "bowler_id": "B1", "is_wicket": "false", "dismissal_type": ""}
        ]
    }

    states = engine.process_match_deliveries(match_info, inns)
    assert len(states) == 1
    assert states[0].mpt == "SUPER_OVER"
    assert states[0].is_pressure is False  # Does not contaminate regular pressure pool


def test_dls_missing_revised_target_excludes_target_pressure():
    """Verify Rule R4 Invariant 14: DLS chase with missing target is excluded from target pressure."""
    engine = MatchContextEngine()
    match_info = {
        "match_id": "M_DLS_NO_TARGET",
        "first_inn_revised_overs": "54",
        "second_inn_revised_overs": "54",
        "revised_target": "",  # Missing!
    }
    inns = {
        2: [
            {"overid": "1", "over_ball_num": "1", "innings_ball_num": "1", "runs": "1", "extras_type": "None", "striker_id": "P1", "bowler_id": "B1", "is_wicket": "false", "dismissal_type": ""}
        ]
    }
    # Even if inn1_total is supplied, DLS missing target should NOT fall back to inn1_total + 1
    states = engine.process_match_deliveries(match_info, inns, inn1_total=120)
    assert len(states) == 1
    st = states[0]
    assert st.target_runs is None
    assert st.cdpi == 0.50  # Neutral fallback, excluded from target pressure
    assert st.mpt == "MEDIUM"
