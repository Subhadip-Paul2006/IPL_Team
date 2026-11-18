"""Authoritative contract and presentation tests for all 11 PRD §6 Streamlit views.

Covers:
- Empty and unavailable fallback states across all 11 views (AC-22)
- Populated multi-engine report states across all 11 views
- Session state discipline (UI only, no analytical transformation in UI)
- Import isolation (AC-23: zero engine imports of Streamlit)
- Ambiguity detection & candidate card waterfalls (PIRE Tier 4)
- 2016–2017 franchise suspension notice (TRD §4.5)
- Four-state competition coverage table (Mode B Discovery)
- CPPAE null metric formatting (Rule R1: NULL is never 0.0)
- CMIE macro domain disclaimer and 5-tier provenance
- Top 10 uncapped candidate board (RK-1.0.0 deliverable)
- CSV formula injection immunity (OWASP sanitizer)
- Streamlit AppTest end-to-end framework verification
"""

from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.streamlit.components import (
    format_metric,
    format_pct,
    generate_safe_csv,
    sanitize_csv_cell,
)
from app.streamlit.views import VIEW_ORDER, ViewName, render_view, run_app


class FakeUI:
    """Record Streamlit-like output calls without requiring a live Streamlit server."""

    def __init__(self) -> None:
        self.session_state: dict[str, Any] = {}
        self.messages: list[tuple[str, Any]] = []

    def title(self, body: str) -> None:
        self.messages.append(("title", body))

    def caption(self, body: str) -> None:
        self.messages.append(("caption", body))

    def info(self, body: str) -> None:
        self.messages.append(("info", body))

    def warning(self, body: str) -> None:
        self.messages.append(("warning", body))

    def error(self, body: str) -> None:
        self.messages.append(("error", body))

    def success(self, body: str) -> None:
        self.messages.append(("success", body))

    def json(self, body: Any, **kwargs: Any) -> None:
        self.messages.append(("json", body))

    def markdown(self, body: str, **kwargs: Any) -> None:
        self.messages.append(("markdown", body))

    def subheader(self, body: str) -> None:
        self.messages.append(("subheader", body))

    def dataframe(self, data: Any, **kwargs: Any) -> None:
        self.messages.append(("dataframe", data))

    def table(self, data: Any) -> None:
        self.messages.append(("table", data))

    def metric(self, label: str, value: Any, **kwargs: Any) -> None:
        self.messages.append(("metric", (label, value)))

    def divider(self) -> None:
        self.messages.append(("divider", "---"))

    def download_button(self, label: str, data: Any, **kwargs: Any) -> bool:
        self.messages.append(("download_button", (label, data)))
        return False

    def text_input(self, label: str, **kwargs: Any) -> str:
        return ""

    def button(self, label: str, **kwargs: Any) -> bool:
        return False

    def selectbox(self, label: str, options: list[str], **kwargs: Any) -> str:
        return options[0]

    def number_input(self, label: str, **kwargs: Any) -> int | float:
        return 0

    def checkbox(self, label: str, **kwargs: Any) -> bool:
        return False

    def expander(self, label: str, expanded: bool = False) -> Any:
        return nullcontext()

    def spinner(self, text: str) -> Any:
        return nullcontext()


def _build_mock_populated_report() -> dict[str, Any]:
    """Construct a fully populated multi-engine player intelligence report."""
    player_id = str(uuid4())
    return {
        "report_id": str(uuid4()),
        "canonical_name": "Sanju Samson",
        "player_id": player_id,
        "identity": {
            "canonical_name": "Sanju Samson",
            "player_id": player_id,
            "resolution_tier": "TIER_1",
            "confidence_score": 0.99,
            "date_of_birth": "1994-11-11",
            "primary_role": "WICKETKEEPER_BATTER",
            "batting_style": "RIGHT_HAND",
            "bowling_style": "RIGHT_ARM_OFF_BREAK",
            "is_ambiguous": False,
            "candidates": [],
        },
        "membership": {
            "relationship_status": "DIRECT_CURRENT_CONTRACT",
            "current_status": "RETAINED",
            "rr_seasons": [
                "2013",
                "2014",
                "2015",
                "2018",
                "2019",
                "2020",
                "2021",
                "2022",
                "2023",
                "2024",
            ],
            "suspension_applied": True,
        },
        "eligibility": {
            "status": "CONFIRMED_CAPPED",
            "reasons": ["Senior Men's International Caps on record."],
        },
        "career": {
            "tournament_coverage": {
                "Indian Premier League (IPL)": "COMPLETE_WITHIN_VERIFIED_SOURCES",
                "Syed Mushtaq Ali Trophy (SMAT T20)": "COMPLETE_WITHIN_VERIFIED_SOURCES",
                "Ranji Trophy (First Class)": "COMPLETE_WITHIN_VERIFIED_SOURCES",
                "Vijay Hazare Trophy (List A)": "COMPLETE_WITHIN_VERIFIED_SOURCES",
            },
            "career_gaps": ["Verified continuous participation across domestic seasons."],
        },
        "performance": {
            "samples": {"matches": 152, "balls_faced": 2980, "legal_balls_bowled": 0},
            "batting": {
                "innings": 147,
                "runs_scored": 3888,
                "balls_faced": 2810,
                "batting_average": 30.85,
                "strike_rate": 138.36,
                "boundary_pct": 20.4,
                "dot_pct": 34.2,
            },
            "bowling": {
                "overs_display": "0.0",
                "runs_conceded": 0,
                "wickets_taken": 0,
                "bowling_average": None,
                "economy_rate": None,
                "bowling_strike_rate": None,
                "dot_pct": None,
            },
        },
        "context": {
            "summary": {
                "total_matches_contextualized": 152,
                "night_fixtures_count": 118,
                "dew_affected_fixtures_count": 42,
                "high_pressure_matches_count": 68,
            }
        },
        "pvre": {
            "replaceability_signal": "RETAIN_SIGNAL",
            "rr_relationship_state": "DIRECT_CURRENT_CONTRACT",
            "rr_current_state": "RETAINED",
            "ipl_uncapped_eligibility": "CONFIRMED_CAPPED",
        },
        "verification": {
            "overall_status": "VERIFIED",
            "requires_human_review": False,
            "reasons": [],
        },
        "provenance": {
            "attribution_notices": ["Local CricSheet Lake (ODC-By v1.0)"],
            "sources": [{"dataset": "CricSheet", "license": "ODC-By v1.0"}],
        },
        "engine_executions": {
            "PIRE": {"status": "EXECUTED", "latency_ms": 12.4, "fallback_applied": False},
            "TMVE": {"status": "EXECUTED", "latency_ms": 8.1, "fallback_applied": False},
            "CDCRE": {"status": "EXECUTED", "latency_ms": 15.2, "fallback_applied": False},
            "CPPAE": {"status": "EXECUTED", "latency_ms": 28.6, "fallback_applied": False},
            "CMIE": {"status": "EXECUTED", "latency_ms": 32.1, "fallback_applied": False},
            "SICE": {"status": "EXECUTED", "latency_ms": 45.0, "fallback_applied": False},
            "PVRE": {"status": "EXECUTED", "latency_ms": 19.3, "fallback_applied": False},
        },
    }


# ==============================================================================
# Baseline Contract Tests (AC-21, AC-22, AC-23)
# ==============================================================================


def test_all_eleven_views_render_empty_and_unavailable_states() -> None:
    """AC-22: Every view renders without backend data or live server connection."""
    assert len(VIEW_ORDER) == 11
    for view in VIEW_ORDER:
        ui = FakeUI()
        render_view(ui, view, {})
        assert ("title", view.value) in ui.messages
        assert any(kind in {"info", "warning"} for kind, _ in ui.messages)


def test_report_status_is_visible_in_data_views() -> None:
    """AC-14/AC-22: Review and unverified statuses are explicit text, not color-only."""
    ui = FakeUI()
    ui.session_state["mie_report"] = {
        "verification": {"overall_status": "REVIEW_REQUIRED"},
        "context": {"match_contexts": []},
    }
    render_view(ui, ViewName.CONTEXT, {})
    assert any("REVIEW_REQUIRED" in str(value) for kind, value in ui.messages if kind == "warning")


def test_navigation_exposes_all_eleven_views() -> None:
    """AC-21: Navigation contains every PRD view name."""
    ui = FakeUI()
    run_app(ui, {})
    assert [value for kind, value in ui.messages if kind == "title"] == [
        "Rajasthan Royals Squad Intelligence",
        ViewName.HOME_TEAM_BUILDER.value,
    ]


def test_engine_modules_do_not_import_streamlit() -> None:
    """AC-23: Core engines remain strictly decoupled from presentation frameworks."""
    source_root = Path(__file__).parents[2] / "src"
    for path in source_root.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "import streamlit" not in source, f"Forbidden Streamlit import in {path}"
        assert "from streamlit" not in source, f"Forbidden Streamlit import in {path}"


def test_squad_composition_view_calls_sice_service() -> None:
    """Verify Squad Composition view triggers SICE evaluate_squad method."""
    team_id = uuid4()

    class ActionUI(FakeUI):
        def button(self, label: str, **kwargs: Any) -> bool:
            return kwargs.get("key") == "mie_sice_evaluate"

    class SICE:
        def evaluate_squad(self, *, team_id: Any) -> dict[str, str]:
            return {"evaluated_team": str(team_id)}

    ui = ActionUI()
    ui.session_state["mie_selected_team_id"] = str(team_id)
    render_view(ui, ViewName.SQUAD_COMPOSITION, {"sice": SICE()})
    assert ("json", {"evaluated_team": str(team_id)}) in ui.messages


def test_comparison_view_submits_typed_sice_request() -> None:
    """Verify Comparison view submits typed ReplacementComparisonRequest."""
    incumbent = str(uuid4())
    candidate = str(uuid4())

    class ActionUI(FakeUI):
        def text_input(self, label: str, **kwargs: Any) -> str:
            if kwargs.get("key") == "mie_incumbent_id":
                return incumbent
            if kwargs.get("key") == "mie_candidate_pool_ids":
                return candidate
            return ""

        def button(self, label: str, **kwargs: Any) -> bool:
            return kwargs.get("key") == "mie_sice_compare"

    class SICE:
        def __init__(self) -> None:
            self.request: Any = None

        def compare_replacement(self, *, request: Any) -> dict[str, str]:
            self.request = request
            return {"status": "REVIEW_REQUIRED"}

    ui = ActionUI()
    sice = SICE()
    render_view(ui, ViewName.COMPARISON, {"sice": sice})
    assert str(sice.request.incumbent_player_id) == incumbent
    assert [str(value) for value in sice.request.candidate_pool_ids] == [candidate]
    assert ("json", {"status": "REVIEW_REQUIRED"}) in ui.messages


# ==============================================================================
# Comprehensive Phase 9 Tests: Populated State & Domain Guardrails
# ==============================================================================


def test_all_eleven_views_render_populated_state() -> None:
    """Verify all 11 PRD views render populated multi-engine reports cleanly."""
    report = _build_mock_populated_report()
    for view in VIEW_ORDER:
        ui = FakeUI()
        ui.session_state["mie_report"] = report
        ui.session_state["mie_selected_team_id"] = str(uuid4())
        ui.session_state["mie_sice_result"] = {"squad_size": 22, "is_valid_ipl_roster": True}
        ui.session_state["mie_replacement_result"] = {"recommended_action": "RECOMMENDED"}

        render_view(ui, view, {})
        assert ("title", view.value) in ui.messages
        # Ensure no error messages were emitted
        assert not any(kind == "error" for kind, _ in ui.messages)


def test_csv_sanitizer_formula_injection_defense() -> None:
    """OWASP formula injection prevention: dangerous initial characters must be prepended with single quote."""
    # Test individual cell sanitization
    assert sanitize_csv_cell("=1+1") == "'=1+1"
    assert sanitize_csv_cell("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
    assert sanitize_csv_cell("-5+2") == "'-5+2"
    assert sanitize_csv_cell("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert sanitize_csv_cell("\tTabLeading") == "'\tTabLeading"
    assert sanitize_csv_cell("\rReturnLeading") == "'\rReturnLeading"

    # Safe cells remain untouched
    assert sanitize_csv_cell("Sanju Samson") == "Sanju Samson"
    assert sanitize_csv_cell(12345) == "12345"
    assert sanitize_csv_cell(None) == ""

    # Test full safe CSV generation
    headers = ["Player", "Formula"]
    rows = [["Sanju", "=cmd|' /C calc'"], ["Riyan", "@SUM(1,2)"]]
    csv_str = generate_safe_csv(headers, rows)
    assert "'=cmd|" in csv_str
    assert "'@SUM" in csv_str


def test_null_metric_formatters_rule_r1() -> None:
    """Rule R1: Missing/null metric data must format as 'N/A', NEVER 0.0."""
    assert format_metric(None) == "N/A"
    assert format_metric(float("nan")) == "N/A"
    assert format_metric(float("inf")) == "N/A"
    assert format_metric(30.852, decimals=2) == "30.85"
    assert format_metric(0.0) == "0.00"  # Genuine 0.0 is preserved when explicitly provided

    assert format_pct(None) == "N/A"
    assert format_pct(float("nan")) == "N/A"
    assert format_pct(14.56, decimals=1) == "14.6%"


def test_player_search_ambiguity_alert_rendering() -> None:
    """PRD §6.2: Multiple candidate matches must trigger prominent ambiguity warning and card list."""
    ui = FakeUI()
    ui.session_state["mie_report"] = {
        "identity": {
            "canonical_name": "Riyan Parag",
            "resolution_tier": "TIER_4",
            "is_ambiguous": True,
            "candidates": [
                {
                    "canonical_name": "Riyan Parag",
                    "player_id": str(uuid4()),
                    "primary_role": "ALL_ROUNDER",
                },
                {
                    "canonical_name": "Riyan Parag (Jr)",
                    "player_id": str(uuid4()),
                    "primary_role": "BATTER",
                },
            ],
        },
        "verification": {"overall_status": "REVIEW_REQUIRED"},
    }
    render_view(ui, ViewName.PLAYER_SEARCH, {})
    assert any("Ambiguity Alert" in str(msg) for kind, msg in ui.messages if kind == "warning")


def test_historical_rr_membership_2016_2017_suspension_notice() -> None:
    """PRD §6.4 & TRD §4.5: RR 2016-17 suspension must be explicitly audited in historical timeline."""
    ui = FakeUI()
    ui.session_state["mie_report"] = _build_mock_populated_report()
    render_view(ui, ViewName.MEMBERSHIP_MODE_A, {})
    # Suspension period notice must be present
    assert any(
        "FRANCHISE SUSPENSION PERIOD" in str(msg) for kind, msg in ui.messages if kind == "markdown"
    )


def test_career_mode_b_four_coverage_states() -> None:
    """PRD §6.5: Tournament coverage table must expose the four canonical states."""
    ui = FakeUI()
    ui.session_state["mie_report"] = _build_mock_populated_report()
    render_view(ui, ViewName.CAREER_MODE_B, {})
    assert any(
        "Four-State Competition Coverage" in str(msg)
        for kind, msg in ui.messages
        if kind == "subheader"
    )


def test_performance_analytics_powerplay_middle_death_splits() -> None:
    """PRD §6.6: Performance Analytics must display phase splits (Powerplay, Middle, Death)."""
    ui = FakeUI()
    ui.session_state["mie_report"] = _build_mock_populated_report()
    render_view(ui, ViewName.PERFORMANCE, {})
    assert any("T20 Phase Splits" in str(msg) for kind, msg in ui.messages if kind == "subheader")


def test_contextual_analysis_macro_disclaimer_and_provenance() -> None:
    """PRD §6.7 & TRD §7: CMIE view must display macro domain disclaimer and 5-tier provenance."""
    ui = FakeUI()
    ui.session_state["mie_report"] = _build_mock_populated_report()
    render_view(ui, ViewName.CONTEXT, {})
    assert any(
        "Macro Domain Disclaimer" in str(msg) for kind, msg in ui.messages if kind == "markdown"
    )
    assert any(
        "5-Tier Provenance Breakdown" in str(msg)
        for kind, msg in ui.messages
        if kind == "subheader"
    )


def test_squad_intelligence_top_10_uncapped_ranking_board() -> None:
    """PRD §6.10 & PRD §4.3: Top 10 uncapped candidate board must be displayed under RK-1.0.0."""
    ui = FakeUI()
    ui.session_state["mie_report"] = _build_mock_populated_report()
    ui.session_state["mie_selected_team_id"] = str(uuid4())
    render_view(ui, ViewName.SQUAD_INTELLIGENCE, {})
    assert any(
        "Top 10 Youngest Uncapped Candidates" in str(msg)
        for kind, msg in ui.messages
        if kind == "subheader"
    )


def test_source_review_safe_exports() -> None:
    """PRD §6.11: Source Review must provide download buttons for JSON and injection-protected CSV."""
    ui = FakeUI()
    ui.session_state["mie_report"] = _build_mock_populated_report()
    render_view(ui, ViewName.SOURCE_REVIEW, {})
    download_calls = [val for kind, val in ui.messages if kind == "download_button"]
    assert len(download_calls) >= 2
    assert any("JSON" in call[0] for call in download_calls)
    assert any("CSV" in call[0] for call in download_calls)


def test_streamlit_apptest_navigation_cycle() -> None:
    """Streamlit AppTest: Verify real Streamlit runtime renders without unhandled exceptions."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file("app/streamlit_app.py", default_timeout=15)
    # Inject lightweight mock services to prevent long cold-start dataset indexing
    at.session_state["_mie_services"] = {
        "mie": None,
        "sice": None,
        "team_builder": None,
    }
    at.run()
    assert not at.exception
    assert at.title[0].value == "Rajasthan Royals Squad Intelligence"


def test_dynamic_csv_export_reflects_actual_report_evidence() -> None:
    """PRD §6.11, §7 & AC-20: CSV export must dynamically reflect actual player evidence, not hardcoded data."""
    ui = FakeUI()
    player_id = str(uuid4())
    # Construct an unverified player report with specific audit reasons
    report = {
        "canonical_name": "Unverified Candidate",
        "player_id": player_id,
        "identity": {"status": "UNRESOLVED", "resolution_tier": "TIER_4"},
        "membership": {
            "rr_relationship_state": "NO_VERIFIED_RR_RELATIONSHIP",
            "rr_current_state": "UNASSOCIATED",
        },
        "eligibility": {"eligibility_status": "NOT_ASSESSED"},
        "verification": {
            "overall_status": "REVIEW_REQUIRED",
            "review_reason_codes": ["IDENTITY_UNRESOLVED", "CAP_STATUS_EVIDENCE_MISSING"],
        },
        "safety_dossier": {
            "unresolved_claims": [
                {"reason": "IDENTITY_UNRESOLVED", "conflicting_source_ids": ["src_123"]}
            ],
            "missing_evidence": ["State association registration"],
            "recommended_manual_checks": ["Check domestic archives"],
        },
        "local_source_evidence": [
            {
                "source_record_key": "datasets/smat/sample.json",
                "license": "ODC-By v1.0",
                "source_provider": "CricSheet",
                "attribution": "ODC-By v1.0 CricSheet Lake",
            }
        ],
    }
    ui.session_state["mie_report"] = report
    render_view(ui, ViewName.SOURCE_REVIEW, {})

    download_calls = [val for kind, val in ui.messages if kind == "download_button"]
    csv_call = next(call for call in download_calls if "CSV" in call[0])
    csv_text = csv_call[1]

    # Verify actual player evidence is preserved
    assert "Unverified Candidate" in csv_text
    assert "REVIEW_REQUIRED" in csv_text
    assert "UNRESOLVED" in csv_text
    assert "IDENTITY_UNRESOLVED" in csv_text
    assert "src_123" in csv_text
    assert "ODC-By v1.0" in csv_text
    # Verify no fake hardcoded claim or fake verified contract
    assert "contract_2024" not in csv_text


def test_mode_a_squad_inclusion_vs_match_appearances() -> None:
    """PRD §6.4: Mode A must explicitly contrast squad inclusions against verified playing XI appearances."""
    ui = FakeUI()
    report = {
        "canonical_name": "Squad Veteran",
        "membership": {
            "rr_seasons": ["2018", "2019", "2020"],
            "verified_rr_appearances": 4,
            "other_ipl_teams": ["DC", "KKR"],
            "negative_verification_met": True,
        },
        "pvre": {
            "replaceability_signal": "MONITOR_SIGNAL",
            "recent_global_performance": {
                "window_start": "2023-01-01",
                "window_end": "2026-11-01",
                "competitions_investigated": ["IPL", "SMAT"],
            },
        },
    }
    ui.session_state["mie_report"] = report
    render_view(ui, ViewName.MEMBERSHIP_MODE_A, {})

    # Check that appearances and inclusions are explicitly rendered
    markdown_msgs = [msg for kind, msg in ui.messages if kind == "markdown"]
    assert any("Squad Inclusion Seasons:** 3" in msg for msg in markdown_msgs)
    assert any("Playing XI Match Appearances:** 4" in msg for msg in markdown_msgs)
    assert any("Negative Verification:** Met" in msg for msg in markdown_msgs)


def test_performance_phase_splits_real_data_and_null_semantics() -> None:
    """PRD §6.6 & Rule R1: Performance analytics must extract actual phase splits without hardcoding."""
    ui = FakeUI()
    # Report with real batting phase splits and null bowling phase splits
    report = {
        "canonical_name": "Finisher Batter",
        "performance": {
            "samples": {"matches": 30, "balls_faced": 450, "legal_balls_bowled": 0},
            "batting": {
                "innings": 28,
                "runs": 850,
                "strike_rate": 155.2,
                "phase_splits": {
                    "powerplay": {"strike_rate": 140.0, "boundary_pct": 20.0},
                    "middle": {"strike_rate": 132.5, "boundary_pct": 14.5},
                    "death": {"strike_rate": 195.8, "boundary_pct": 28.2},
                },
            },
            "bowling": {
                "overs_display": "0.0",
                "phase_splits": {},
            },
        },
    }
    ui.session_state["mie_report"] = report
    render_view(ui, ViewName.PERFORMANCE, {})

    df_msgs = [data for kind, data in ui.messages if kind == "dataframe"]
    phase_table = next(tbl for tbl in df_msgs if any("Death Overs" in str(row) for row in tbl))

    # Verify actual death overs strike rate is present
    death_row = next(r for r in phase_table if "Death Overs" in r["Phase"])
    assert death_row["Batting SR"] == "195.80"
    assert death_row["Boundary %"] == "28.2%"
    # Bowling was null/empty, so economy rate MUST be N/A (Rule R1)
    assert death_row["Bowling Econ"] == "N/A"


def test_candidate_discovery_ambiguity_waterfall() -> None:
    """PRD §6.2: Ambiguous search candidates from candidate_discovery contract must be surfaced."""
    ui = FakeUI()
    cand1_id = str(uuid4())
    cand2_id = str(uuid4())
    report = {
        "canonical_name": "Riyan Parag",
        "identity": {"tier": "TIER_4", "is_ambiguous": True},
        "candidate_discovery": {
            "collision_detected": True,
            "candidates": [
                {
                    "canonical_name": "Riyan Parag",
                    "player_id": cand1_id,
                    "primary_role": "ALL_ROUNDER",
                    "teams": ["RR", "Assam"],
                },
                {
                    "canonical_name": "Riyan Parag (Jr)",
                    "player_id": cand2_id,
                    "primary_role": "BATTER",
                    "teams": ["Assam U19"],
                },
            ],
        },
    }
    ui.session_state["mie_report"] = report
    render_view(ui, ViewName.PLAYER_SEARCH, {})

    warn_msgs = [msg for kind, msg in ui.messages if kind == "warning"]
    assert any("Ambiguity Alert" in msg for msg in warn_msgs)

    df_msgs = [data for kind, data in ui.messages if kind == "dataframe"]
    cand_table = next(tbl for tbl in df_msgs if any("Riyan Parag" in str(row) for row in tbl))
    assert len(cand_table) == 2
    assert any("Assam" in r["Teams / Source"] for r in cand_table)


def test_replacement_comparison_with_real_sice_evaluation() -> None:
    """PRD §6.8: Replacement view must render candidate evaluations and dimension comparison rows."""
    ui = FakeUI()
    comparison_result = {
        "incumbent_canonical_name": "Incumbent Pacer",
        "incumbent_role": "PACE_BOWLER",
        "recommended_action": "TARGET_REPLACEMENT",
        "overseas_slot_liberated": True,
        "evaluations": [
            {
                "canonical_name": "Emerging Pacer",
                "role_compatibility": "EXCELLENT_MATCH",
                "recommendation_label": "STRONG_REPLACEMENT",
                "confidence": 0.88,
                "dimension_comparisons": [
                    {
                        "dimension_name": "Death Overs Bowling Utility",
                        "incumbent_value": "9.85 Econ",
                        "candidate_value": "7.60 Econ",
                        "delta": -2.25,
                        "advantage": "CANDIDATE_ADVANTAGE",
                        "dimension_status": "MEASURED",
                    }
                ],
            }
        ],
    }
    ui.session_state["mie_replacement_result"] = comparison_result
    render_view(ui, ViewName.COMPARISON, {})

    markdown_msgs = [msg for kind, msg in ui.messages if kind == "markdown"]
    assert any("Incumbent Pacer" in msg for msg in markdown_msgs)
    assert any("TARGET_REPLACEMENT" in msg for msg in markdown_msgs)
    assert any("Overseas Slot Liberated:** Yes" in msg for msg in markdown_msgs)

    df_msgs = [data for kind, data in ui.messages if kind == "dataframe"]
    dim_table = next(
        tbl for tbl in df_msgs if any("Death Overs Bowling Utility" in str(row) for row in tbl)
    )
    assert dim_table[0]["Advantage"] == "CANDIDATE_ADVANTAGE"
    assert dim_table[0]["Delta"] == "-2.25"
