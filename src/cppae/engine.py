"""CPPAE Master Facade Engine (TRD §6, §6.3 `CPPAE.analyse`).

Orchestrates all specialist engines:
- BattingEngine (B01–B17, BPPS Option B)
- BowlingEngine (W01–W12, BWPS, format-aware economy, HLES)
- FieldingEngine (F01–F09, WK-01..03, coverage classes)
- MatchContributionEngine (M01–M07, situation context, win/loss, high leverage)
- StatisticalCalibrationEngine (Empirical Bayes priors, hierarchical fallback, bootstrap)
- FeatureStorePublisher (Entity 31 DerivedFeature transformation & persistence)
"""

from typing import Any
from uuid import UUID

from src.cmie.match_context import PreDeliveryState
from src.contracts.career import PlayerAward
from src.contracts.cppae import (
    CPPAEOutput,
    PerStatMetric,
    SampleSizes,
)
from src.contracts.scorecard import BattingInnings, BowlingSpell, FieldingEvent, WicketkeepingEvent
from src.cppae.batting_engine import BattingEngine
from src.cppae.bowling_engine import BowlingEngine
from src.cppae.calibration import StatisticalCalibrationEngine
from src.cppae.fielding_engine import FieldingEngine
from src.cppae.match_contribution import MatchContributionEngine
from src.cppae.persistence import FeatureStorePublisher, OfflineFeatureStoreAdapter


class CPPAEEngine:
    """Authoritative CPPAE facade implementing TRD §6.3 `CPPAE.analyse`."""

    def __init__(
        self,
        k_bat: float = 30.0,
        k_bat_avg: float = 5.0,
        k_bowl: float = 40.0,
        balls_per_over: int = 6,
        model_version: str = "v2.1",
        feature_adapter: OfflineFeatureStoreAdapter | None = None,
    ) -> None:
        self.k_bat = k_bat
        self.k_bat_avg = k_bat_avg
        self.k_bowl = k_bowl
        self.balls_per_over = balls_per_over
        self.model_version = model_version

        # Specialist workstream engines
        self.batting_engine = BattingEngine(k_bat=k_bat, k_bat_avg=k_bat_avg, balls_per_over=balls_per_over)
        self.bowling_engine = BowlingEngine(k_bowl=k_bowl, balls_per_over=balls_per_over)
        self.fielding_engine = FieldingEngine()
        self.match_contribution_engine = MatchContributionEngine()
        self.calibration_engine = StatisticalCalibrationEngine(k_bat=k_bat, k_bat_avg=k_bat_avg, k_bowl=k_bowl)
        self.publisher = FeatureStorePublisher(model_version=model_version)
        self.feature_store = feature_adapter or OfflineFeatureStoreAdapter()

    def analyse(
        self,
        player_id: UUID | str,
        deliveries: list[dict[str, Any]],
        states: list[PreDeliveryState] | None = None,
        batting_innings: list[BattingInnings | dict[str, Any]] | None = None,
        bowling_spells: list[BowlingSpell | dict[str, Any]] | None = None,
        fielding_events: list[FieldingEvent | dict[str, Any]] | None = None,
        wk_events: list[WicketkeepingEvent | dict[str, Any]] | None = None,
        matches: list[dict[str, Any]] | None = None,
        player_awards: list[PlayerAward | dict[str, Any]] | None = None,
        playing_xi_rosters: list[list[str]] | None = None,
        player_names: dict[str, str] | None = None,
        bowling_styles: dict[str, str] | None = None,
        format_tag: str = "T20",
        window: str = "career",
        persist_features: bool = True,
    ) -> CPPAEOutput:
        """Execute complete performance analytics pipeline for player_id."""
        pid_uuid = UUID(str(player_id)) if not isinstance(player_id, UUID) else player_id
        pid_str = str(pid_uuid)
        p_names = player_names or {}
        canonical_name = p_names.get(pid_str, f"Player_{pid_str[:8]}")

        # 1. Batting Profile
        bat_profile = self.batting_engine.calculate_profile(
            player_id=pid_uuid,
            deliveries=deliveries,
            states=states,
            batting_innings=batting_innings,
            matches=matches,
            player_names=player_names,
            bowling_styles=bowling_styles,
            format_tag=format_tag,
        )

        # 2. Bowling Profile
        bowl_profile = self.bowling_engine.calculate_profile(
            player_id=pid_uuid,
            deliveries=deliveries,
            states=states,
            bowling_spells=bowling_spells,
            matches=matches,
            player_names=player_names,
            format_tag=format_tag,
        )

        # 3. Fielding & Wicketkeeping Profiles
        field_profile = self.fielding_engine.calculate_fielding_profile(
            player_id=pid_uuid,
            fielding_events=fielding_events,
            playing_xi_rosters=playing_xi_rosters,
        )
        wk_profile = self.fielding_engine.calculate_wicketkeeping_profile(
            player_id=pid_uuid,
            wk_events=wk_events,
            fielding_events=fielding_events,
        )

        # 4. Match Contribution Profile
        mc_profile = self.match_contribution_engine.calculate_profile(
            player_id=pid_uuid,
            deliveries=deliveries,
            states=states,
            matches=matches,
            player_awards=player_awards,
            format_tag=format_tag,
        )

        # 5. Visible Sample Sizes (TRD §6.2)
        delivery_events_faced = 0
        delivery_events_bowled = 0
        for d in deliveries:
            if str(d.get("striker_id", "")).strip() == pid_str:
                delivery_events_faced += 1
            if str(d.get("bowler_id", "")).strip() == pid_str:
                delivery_events_bowled += 1

        samples = SampleSizes(
            matches=max(bat_profile.matches, bowl_profile.matches, field_profile.appearances or 0, wk_profile.appearances or 0),
            innings=bat_profile.innings + bowl_profile.innings,
            balls_faced=bat_profile.balls_faced,
            legal_balls_bowled=bowl_profile.legal_balls_bowled,
            delivery_events_faced=delivery_events_faced,
            delivery_events_bowled=delivery_events_bowled,
            fielding_innings=field_profile.appearances or 0,
            wicketkeeping_innings=wk_profile.appearances,
        )

        # 6. Build atomic per_stat dictionary with exact DATA_DICTIONARY citations
        is_hundred = (format_tag == "HUNDRED")
        hundred_rate_status = "DEFERRED" if is_hundred else "DERIVED"

        per_stat: dict[str, PerStatMetric] = {}

        # Helper to register stat
        def add_stat(
            m_id: str,
            name: str,
            val: float | int | str | None,
            def_ref: str,
            formula: str,
            src: list[str],
            status: str = "DERIVED",
            null_reason: str | None = None,
            sample: int | None = None,
            insufficient: bool = False,
        ) -> None:
            per_stat[m_id] = PerStatMetric(
                metric_id=m_id,
                name=name,
                value=val,
                definition_ref=def_ref,
                formula=formula,
                source_fields=src,
                format_tag=format_tag,
                sample_size=sample,
                null_reason=null_reason if val is None else None,
                status=status,
                insufficient_sample_flag=insufficient,
            )

        # Batting B01–B17 & BPPS
        add_stat("B01", "Matches (batting)", bat_profile.matches, "DATA_DICTIONARY §1 B01", "COUNT(DISTINCT match_id)", ["batting_innings", "matches"], "OBSERVED", sample=bat_profile.matches)
        add_stat("B02", "Innings (batting)", bat_profile.innings, "DATA_DICTIONARY §1 B02", "COUNT(innings WHERE did_not_bat=FALSE)", ["batting_innings.did_not_bat"], "OBSERVED", sample=bat_profile.innings)
        add_stat("B03", "Runs", bat_profile.runs, "DATA_DICTIONARY §1 B03", "SUM(runs_scored)", ["deliveries.runs"], "OBSERVED", sample=bat_profile.balls_faced)
        add_stat("B04", "Balls faced", bat_profile.balls_faced, "DATA_DICTIONARY §1 B04", "SUM(balls_faced)", ["deliveries"], "OBSERVED", sample=bat_profile.balls_faced)
        add_stat("B05", "Batting average", bat_profile.batting_average, "DATA_DICTIONARY §1 B05", "runs / (innings - not_outs)", ["B03", "B02"], hundred_rate_status, null_reason="ZERO_DISMISSALS" if bat_profile.dismissals == 0 else None, sample=bat_profile.dismissals)
        add_stat("B06", "Strike rate", bat_profile.strike_rate, "DATA_DICTIONARY §1 B06", "100 * runs / balls", ["B03", "B04"], hundred_rate_status, null_reason="ZERO_BALLS_FACED" if bat_profile.balls_faced == 0 else None, sample=bat_profile.balls_faced)
        add_stat("B07", "Boundaries", bat_profile.boundaries, "DATA_DICTIONARY §1 B07", "fours + sixes", ["deliveries.runs"], "OBSERVED", sample=bat_profile.balls_faced)
        add_stat("B08", "Boundary %", bat_profile.boundary_pct, "DATA_DICTIONARY §1 B08", "100 * (4*fours + 6*sixes) / runs", ["B07", "B03"], hundred_rate_status, null_reason="ZERO_RUNS" if bat_profile.runs == 0 else None, sample=bat_profile.runs)
        add_stat("B09", "Dot-ball %", bat_profile.dot_pct, "DATA_DICTIONARY §1 B09", "100 * dot_balls / balls", ["deliveries.runs", "B04"], hundred_rate_status, null_reason="ZERO_BALLS_FACED" if bat_profile.balls_faced == 0 else None, sample=bat_profile.balls_faced)
        add_stat("BPPS", "Batting Pressure Performance Score", bat_profile.bpps, "TRD §6, Phase 1B/05", "Empirical Bayes shrunk weighted pressure score", ["B06", "B05", "B08", "B09"], "MODEL_INFERRED", sample=bat_profile.balls_faced)

        # Bowling W01–W12, BWPS, HLES
        add_stat("W01", "Overs (display)", bowl_profile.overs_display, "DATA_DICTIONARY §2 W01", "floor(legal_balls/BPO) + (legal_balls%BPO)/10", ["W02", "competitions.balls_per_over"], "DERIVED", sample=bowl_profile.legal_balls_bowled)
        add_stat("W02", "Legal balls", bowl_profile.legal_balls_bowled, "DATA_DICTIONARY §2 W02", "COUNT(legal deliveries)", ["deliveries.extras_type"], "OBSERVED", sample=bowl_profile.legal_balls_bowled)
        add_stat("W03", "Runs conceded", bowl_profile.runs_conceded, "DATA_DICTIONARY §2 W03", "SUM(runs excluding byes/leg-byes/penalties)", ["deliveries.runs", "deliveries.extras"], "OBSERVED", sample=bowl_profile.legal_balls_bowled)
        add_stat("W04", "Wickets", bowl_profile.wickets_taken, "DATA_DICTIONARY §2 W04", "COUNT(bowler-credited wickets)", ["deliveries.wickets"], "OBSERVED", sample=bowl_profile.legal_balls_bowled)
        add_stat("W05", "Bowling average", bowl_profile.bowling_average, "DATA_DICTIONARY §2 W05", "runs / wickets", ["W03", "W04"], hundred_rate_status, null_reason="ZERO_WICKETS" if bowl_profile.wickets_taken == 0 else None, sample=bowl_profile.wickets_taken)
        add_stat("W06", "Economy rate", bowl_profile.economy_rate, "DATA_DICTIONARY §2 W06", "(BPO * runs) / legal_balls", ["W03", "W02", "competitions.balls_per_over"], hundred_rate_status, null_reason="ZERO_LEGAL_BALLS" if bowl_profile.legal_balls_bowled == 0 else None, sample=bowl_profile.legal_balls_bowled)
        add_stat("W07", "Bowling strike rate", bowl_profile.bowling_strike_rate, "DATA_DICTIONARY §2 W07", "legal_balls / wickets", ["W02", "W04"], hundred_rate_status, null_reason="ZERO_WICKETS" if bowl_profile.wickets_taken == 0 else None, sample=bowl_profile.wickets_taken)
        add_stat("W08", "Bowling dot %", bowl_profile.dot_pct, "DATA_DICTIONARY §2 W08", "100 * dot_balls / legal_balls", ["deliveries", "W02"], hundred_rate_status, null_reason="ZERO_LEGAL_BALLS" if bowl_profile.legal_balls_bowled == 0 else None, sample=bowl_profile.legal_balls_bowled)
        add_stat("BWPS", "Bowling Pressure Performance Score", bowl_profile.bwps, "TRD §6, Phase 1B/05", "Empirical Bayes shrunk weighted bowling score", ["W06", "W08", "W04"], "MODEL_INFERRED", sample=bowl_profile.legal_balls_bowled)

        # HLES: T20 calibrated; Non-T20 DEFERRED per TRD Invariant R8
        hles_st = "DERIVED" if format_tag in ("T20", "IT20", "IPL") else "DEFERRED"
        add_stat("HLES", "High-Leverage Execution Score", bowl_profile.hles, "DATA_DICTIONARY §2, TRD §6", "(2*w + 1*dot) / balls (T20 only)", ["W04", "W08", "states.is_pressure"], hles_st, null_reason="NON_T20_DEFERRED" if hles_st == "DEFERRED" else None, sample=bowl_profile.legal_balls_bowled)

        # Fielding F01–F07
        add_stat("F01", "Catches", field_profile.catches, "DATA_DICTIONARY §3 F01", "COUNT(event_type='Catch')", ["fielding_events"], "OBSERVED", sample=field_profile.appearances)
        add_stat("F02", "Run-outs", field_profile.run_outs_total, "DATA_DICTIONARY §3 F02", "COUNT(Run Out Thrower/Catcher)", ["fielding_events"], "OBSERVED", sample=field_profile.appearances)
        add_stat("F03", "Stumpings", field_profile.stumpings, "DATA_DICTIONARY §3 F03", "COUNT(event_type='Stumping')", ["fielding_events"], "OBSERVED", sample=field_profile.appearances)
        add_stat("F04", "Recorded dropped catches", field_profile.recorded_dropped_catches, "DATA_DICTIONARY §3 F04", "COUNT(event_type='Dropped Catch') where recorded", ["fielding_events"], "OBSERVED" if field_profile.recorded_dropped_catches is not None else "NOT_COMPUTABLE", null_reason="UNRECORDED_IN_SOURCE" if field_profile.recorded_dropped_catches is None else None)
        add_stat("F05", "Boundary saves", field_profile.boundary_saves, "DATA_DICTIONARY §3 F05", "COUNT(event_type='Boundary Save') where recorded", ["fielding_events"], "OBSERVED" if field_profile.boundary_saves is not None else "NOT_COMPUTABLE", null_reason="UNRECORDED_IN_SOURCE" if field_profile.boundary_saves is None else None)
        add_stat("F06", "Missed opportunities", None, "DATA_DICTIONARY §3 F06", "Prohibited from inference", [], "NOT_COMPUTABLE", null_reason="INFERENCE_PROHIBITED")
        add_stat("F07", "Fielding appearances", field_profile.appearances, "DATA_DICTIONARY §3 F07", "Playing XI appearances", ["source playing_xi"], "OBSERVED", null_reason="ROSTER_UNAVAILABLE" if field_profile.appearances is None else None)

        # Wicketkeeping F08–F09, WK-01..03
        add_stat("F08", "Wicketkeeping appearances", wk_profile.appearances, "DATA_DICTIONARY §3 F08", "wicketkeeping_events.appearances", ["wicketkeeping_events"], "OBSERVED", sample=wk_profile.appearances)
        add_stat("F09", "Wicketkeeping dismissals", wk_profile.dismissals_total, "DATA_DICTIONARY §3 F09", "stumpings + catches", ["wicketkeeping_events"], "OBSERVED", sample=wk_profile.appearances)
        add_stat("WK-01", "Wicketkeeping catches", wk_profile.catches, "DATA_DICTIONARY §3 WK-01", "catches as designated keeper", ["wicketkeeping_events.catches"], "OBSERVED", sample=wk_profile.appearances)
        add_stat("WK-02", "Recorded missed stumpings", wk_profile.recorded_missed_stumpings, "DATA_DICTIONARY §3 WK-02", "missed stumpings where recorded", ["wicketkeeping_events"], "OBSERVED" if wk_profile.recorded_missed_stumpings is not None else "NOT_COMPUTABLE", null_reason="UNRECORDED_IN_SOURCE" if wk_profile.recorded_missed_stumpings is None else None)
        add_stat("WK-03", "Recorded missed catches", wk_profile.recorded_missed_catches, "DATA_DICTIONARY §3 WK-03", "missed keeper catches where recorded", ["wicketkeeping_events"], "OBSERVED" if wk_profile.recorded_missed_catches is not None else "NOT_COMPUTABLE", null_reason="UNRECORDED_IN_SOURCE" if wk_profile.recorded_missed_catches is None else None)

        # Match Contribution M01–M07
        add_stat("M01", "Player of the Match awards", mc_profile.player_of_match_awards, "DATA_DICTIONARY §6 M01", "COUNT(player_awards.POTM)", ["player_awards", "matches.player_of_match"], "OBSERVED", sample=samples.matches)
        add_stat("M02", "Batting contribution", mc_profile.batting_contribution_pct, "DATA_DICTIONARY §6 M02", "player runs / team innings runs", ["deliveries.runs", "innings.total_runs"], "DERIVED", null_reason="ZERO_TEAM_RUNS" if mc_profile.batting_contribution_pct is None else None, sample=bat_profile.runs)
        add_stat("M03", "Bowling contribution", mc_profile.bowling_wicket_share_pct, "DATA_DICTIONARY §6 M03", "player wickets / team innings wickets", ["deliveries.wickets"], "DERIVED", null_reason="ZERO_TEAM_WICKETS" if mc_profile.bowling_wicket_share_pct is None else None, sample=bowl_profile.wickets_taken)
        add_stat("M04", "Match situation context", None, "DATA_DICTIONARY §6 M04", "chase vs defend split", ["innings.innings_number"], "OBSERVED")
        add_stat("M05", "Performance in wins/losses", None, "DATA_DICTIONARY §6 M05", "performance split by outcome_type", ["matches.winner_id"], "DERIVED")

        # M06: High-leverage contribution (T20 calibrated; non-T20 DEFERRED per TRD Invariant R8)
        hl_st = "DERIVED" if format_tag in ("T20", "IT20", "IPL") else "DEFERRED"
        m06_val = mc_profile.high_leverage_contribution.get("high_leverage_runs") if hl_st == "DERIVED" else None
        add_stat("M06", "Measurable high-leverage contribution", m06_val, "DATA_DICTIONARY §6 M06", "runs/wickets when match state crosses threshold", ["states.is_pressure", "states.wickets_in_hand"], hl_st, null_reason="NON_T20_DEFERRED" if hl_st == "DEFERRED" else None)
        add_stat("M07", "Additive match composite", mc_profile.additive_composite, "DATA_DICTIONARY §6 M07", "M02 + M03 explicit sum", ["M02", "M03"], "DERIVED", null_reason="NO_CONTRIBUTION_RECORDED" if mc_profile.additive_composite is None else None)

        output = CPPAEOutput(
            player_id=pid_uuid,
            canonical_name=canonical_name,
            format_tag=format_tag,
            window=window,
            batting=bat_profile,
            bowling=bowl_profile,
            fielding=field_profile,
            wicketkeeping=wk_profile,
            match_contribution=mc_profile,
            samples=samples,
            per_stat=per_stat,
        )

        # 7. Persistence to Feature Store
        if persist_features:
            feats = self.publisher.build_derived_features(output)
            self.feature_store.insert_features_batch(feats)

        return output
