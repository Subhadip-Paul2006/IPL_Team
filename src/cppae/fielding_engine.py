"""CPPAE Fielding and Wicketkeeping Analytics Engine (TRD §6, DATA_DICTIONARY §3 F01–F09 & WK-01..03).

Computes fielding and wicketkeeping profiles respecting source evidence boundaries,
never inferring missing events or fabricating player attributes, and assigning
accurate coverage classes (FULLY_RECORDED, PARTIALLY_RECORDED, COVERAGE_LIMITED).
"""

from typing import Any
from uuid import UUID

from src.contracts.cppae import FieldingProfile, WicketkeepingProfile
from src.contracts.scorecard import FieldingEvent, WicketkeepingEvent


class FieldingEngine:
    """Core analytics engine for Fielding (F01–F07) and Wicketkeeping (F08–F09, WK-01–03)."""

    def __init__(self) -> None:
        pass

    def calculate_fielding_profile(
        self,
        player_id: UUID | str,
        fielding_events: list[FieldingEvent | dict[str, Any]] | None = None,
        playing_xi_rosters: list[list[str]] | None = None,
        source_records_available: bool = True,
    ) -> FieldingProfile:
        """Calculate FieldingProfile from verified fielding events and playing-XI rosters."""
        pid_str = str(player_id)
        events = fielding_events or []

        # Count events for this player
        catches = 0
        run_outs_direct = 0
        run_outs_assisted = 0
        stumpings = 0
        dropped_catches: int | None = None
        boundary_saves: int | None = None
        missed_opportunities: int | None = None

        has_explicit_drop_records = False
        has_explicit_save_records = False

        for ev in events:
            ev_pid = str(getattr(ev, "player_id", None) or (ev.get("player_id") if isinstance(ev, dict) else ""))
            ev_asst = str(getattr(ev, "assisted_by_player_id", None) or (ev.get("assisted_by_player_id") if isinstance(ev, dict) else "") or "")
            ev_type = str(getattr(ev, "event_type", "") or (ev.get("event_type", "") if isinstance(ev, dict) else ""))

            if ev_type == "Dropped Catch":
                has_explicit_drop_records = True
            elif ev_type == "Boundary Save":
                has_explicit_save_records = True

            if ev_pid == pid_str:
                if ev_type == "Catch":
                    catches += 1
                elif ev_type == "Run Out Thrower":
                    run_outs_direct += 1
                elif ev_type == "Run Out Catcher":
                    run_outs_assisted += 1
                elif ev_type == "Stumping":
                    stumpings += 1
                elif ev_type == "Dropped Catch":
                    dropped_catches = (dropped_catches or 0) + 1
                elif ev_type == "Boundary Save":
                    boundary_saves = (boundary_saves or 0) + 1
            elif ev_asst == pid_str and ev_type in ("Run Out Thrower", "Run Out Catcher"):
                run_outs_assisted += 1

        run_outs_total = run_outs_direct + run_outs_assisted

        # Dropped catches: if dataset tracks drops explicitly, count is an integer; else None (NULL)
        if not has_explicit_drop_records:
            dropped_catches = None
        if not has_explicit_save_records:
            boundary_saves = None

        # Missed opportunities: prohibited from inference per domain rule (DATA_DICTIONARY §3 F06)
        missed_opportunities = None

        # Fielding appearances: from playing XI rosters where recorded
        appearances: int | None = None
        if playing_xi_rosters is not None:
            appearances = sum(1 for roster in playing_xi_rosters if pid_str in roster)

        # Coverage class determination
        coverage_class = "COVERAGE_LIMITED"
        if not source_records_available:
            coverage_class = "COVERAGE_LIMITED"
        elif appearances is not None and has_explicit_drop_records and has_explicit_save_records:
            coverage_class = "FULLY_RECORDED"
        elif appearances is not None or len(events) > 0:
            coverage_class = "PARTIALLY_RECORDED"

        return FieldingProfile(
            appearances=appearances,
            catches=catches,
            run_outs_direct=run_outs_direct,
            run_outs_assisted=run_outs_assisted,
            run_outs_total=run_outs_total,
            stumpings=stumpings,
            recorded_dropped_catches=dropped_catches,
            boundary_saves=boundary_saves,
            missed_opportunities=missed_opportunities,
            coverage_class=coverage_class,
        )

    def calculate_wicketkeeping_profile(
        self,
        player_id: UUID | str,
        wk_events: list[WicketkeepingEvent | dict[str, Any]] | None = None,
        fielding_events: list[FieldingEvent | dict[str, Any]] | None = None,
    ) -> WicketkeepingProfile:
        """Calculate WicketkeepingProfile from recorded wicketkeeping events."""
        pid_str = str(player_id)
        events = wk_events or []
        f_events = fielding_events or []

        appearances = 0
        stumpings = 0
        catches = 0
        missed_stumpings: int | None = None
        missed_catches: int | None = None

        has_explicit_miss_records = False

        for ev in events:
            ev_pid = str(getattr(ev, "player_id", None) or (ev.get("player_id") if isinstance(ev, dict) else ""))
            if ev_pid != pid_str:
                continue

            app = int(getattr(ev, "appearances", 0) or (ev.get("appearances", 0) if isinstance(ev, dict) else 0))
            st = int(getattr(ev, "stumpings", 0) or (ev.get("stumpings", 0) if isinstance(ev, dict) else 0))
            ct = int(getattr(ev, "catches", 0) or (ev.get("catches", 0) if isinstance(ev, dict) else 0))
            ms = getattr(ev, "missed_stumpings", None) or (ev.get("missed_stumpings") if isinstance(ev, dict) else None)
            mc = getattr(ev, "missed_catches", None) or (ev.get("missed_catches") if isinstance(ev, dict) else None)

            appearances += app
            stumpings += st
            catches += ct

            if ms is not None:
                has_explicit_miss_records = True
                missed_stumpings = (missed_stumpings or 0) + int(ms)
            if mc is not None:
                has_explicit_miss_records = True
                missed_catches = (missed_catches or 0) + int(mc)

        # Fallback to fielding events if no dedicated wk_events table entries
        if appearances == 0 and stumpings == 0 and catches == 0 and f_events:
            for fe in f_events:
                fe_pid = str(getattr(fe, "player_id", None) or (fe.get("player_id") if isinstance(fe, dict) else ""))
                if fe_pid != pid_str:
                    continue
                pos = str(getattr(fe, "fielding_position", "") or (fe.get("fielding_position", "") if isinstance(fe, dict) else ""))
                ev_type = str(getattr(fe, "event_type", "") or (fe.get("event_type", "") if isinstance(fe, dict) else ""))
                if "keeper" in pos.lower() or ev_type == "Stumping":
                    if ev_type == "Stumping":
                        stumpings += 1
                    elif ev_type == "Catch":
                        catches += 1

        total_dismissals = stumpings + catches
        dpa = round(total_dismissals / appearances, 2) if appearances > 0 else None

        if not has_explicit_miss_records:
            missed_stumpings = None
            missed_catches = None

        coverage_class = "COVERAGE_LIMITED"
        if appearances > 0 and has_explicit_miss_records:
            coverage_class = "FULLY_RECORDED"
        elif appearances > 0 or total_dismissals > 0:
            coverage_class = "PARTIALLY_RECORDED"

        return WicketkeepingProfile(
            appearances=appearances,
            dismissals_total=total_dismissals,
            stumpings=stumpings,
            catches=catches,
            dismissals_per_appearance=dpa,
            recorded_missed_stumpings=missed_stumpings,
            recorded_missed_catches=missed_catches,
            coverage_class=coverage_class,
        )
