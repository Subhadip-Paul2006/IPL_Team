"""CricSheet JSON Parser (v1.3.0 and legacy formats).

Part of Phase 1 Historical Data Pipeline Closure (Track A).
Parses CricSheet ball-by-ball JSON payloads into Pydantic v2 domain contracts:
- Match (TRD Entity 13 / src.contracts.match.Match)
- Innings (TRD Entity 14 / src.contracts.match.Innings)
- Delivery (TRD Entity 15 / src.contracts.match.Delivery)
Extracts people registries, team registries, and validates against Phase 1A contracts.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_DNS, UUID, uuid5

from src.contracts.match import Delivery, Innings, Match
from src.ingestion.normalizer import (
    is_bowler_credited_wicket,
)

# Namespace for deterministic UUID derivation from external string IDs
CRIC_NAMESPACE = uuid5(NAMESPACE_DNS, "cricsheet.org")


def derive_uuid(category: str, identifier: str) -> UUID:
    """Generate deterministic UUIDv5 for a given entity type and string identifier."""
    key = f"{category}:{str(identifier).strip().lower()}"
    return uuid5(CRIC_NAMESPACE, key)


def parse_match_date(date_str: str) -> date:
    """Parse ISO date string into date object."""
    return datetime.strptime(date_str[:10], "%Y-%m-%d").date()


def determine_match_phase(over_number: int, match_type: str = "T20", balls_per_over: int = 6) -> str:
    """Assign match phase (Powerplay, Middle, Death) based on format and over number."""
    m_type = match_type.upper()
    if balls_per_over == 5 or m_type == "HUNDRED":
        # The Hundred: 5-ball overs. Powerplay: overs 0-4 (balls 1-25), Middle: overs 5-17 (balls 26-90), Death: overs 18-19 (balls 91-100)
        if over_number < 5:
            return "Powerplay"
        if over_number < 18:
            return "Middle"
        return "Death"
    elif m_type in ("T20", "IT20"):
        if over_number < 6:
            return "Powerplay"
        if over_number < 15:
            return "Middle"
        return "Death"
    elif m_type in ("ODI", "ODM"):
        if over_number < 10:
            return "Powerplay"
        if over_number < 40:
            return "Middle"
        return "Death"
    # Default fallback for other white ball formats
    if over_number < 6:
        return "Powerplay"
    if over_number < 15:
        return "Middle"
    return "Death"


@dataclass
class CricSheetParsedMatch:
    """Comprehensive container for all parsed entities from a CricSheet JSON."""

    match: Match
    innings: list[Innings] = field(default_factory=list)
    deliveries: list[Delivery] = field(default_factory=list)
    player_registry: dict[str, str] = field(default_factory=dict)  # name -> cricsheet_id
    player_id_map: dict[str, UUID] = field(default_factory=dict)   # name/cricsheet_id -> UUID
    team_id_map: dict[str, UUID] = field(default_factory=dict)     # team_name -> UUID
    venue_id: UUID | None = None
    venue_name: str = ""
    season_name: str = ""
    data_version: str = "1.3.0"
    raw_payload: dict[str, Any] = field(default_factory=dict)
    quarantine_reasons: list[str] = field(default_factory=list)

    @property
    def is_quarantined(self) -> bool:
        return len(self.quarantine_reasons) > 0


class CricSheetParser:
    """Parser for CricSheet v1.3.0 and legacy ball-by-ball JSON formats."""

    def __init__(self, default_season_id: UUID | None = None) -> None:
        self.default_season_id = default_season_id

    def parse_file(self, file_path: Path | str) -> CricSheetParsedMatch:
        """Parse a CricSheet JSON file from disk."""
        path = Path(file_path)
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        external_id = path.stem
        return self.parse_json(data, external_id=external_id)

    def parse_json(self, data: dict[str, Any], external_id: str = "") -> CricSheetParsedMatch:
        """Parse in-memory CricSheet JSON data structure."""
        quarantine_reasons: list[str] = []

        if not isinstance(data, dict):
            return CricSheetParsedMatch(
                match=self._create_empty_match(external_id),
                quarantine_reasons=["Payload is not a valid JSON object"],
                raw_payload=data if isinstance(data, dict) else {},
            )

        meta = data.get("meta") or {}
        data_version = str(meta.get("data_version", "1.3.0"))
        info = data.get("info") or {}

        # Extract Teams
        teams = info.get("teams") or []
        if len(teams) < 2:
            quarantine_reasons.append("Match has fewer than 2 teams defined in info.teams")
            team1_name = teams[0] if len(teams) == 1 else "Unknown Team 1"
            team2_name = "Unknown Team 2"
        else:
            team1_name = str(teams[0]).strip()
            team2_name = str(teams[1]).strip()

        team_id_map: dict[str, UUID] = {
            team1_name: derive_uuid("team", team1_name),
            team2_name: derive_uuid("team", team2_name),
        }

        # Extract Venue
        venue_name = str(info.get("venue") or "Unknown Venue").strip()
        venue_id = derive_uuid("venue", venue_name)

        # Extract Season
        season_val = str(info.get("season") or "Unknown Season").strip()
        season_year = season_val[:4] if len(season_val) >= 4 and season_val[:4].isdigit() else "2024"
        season_id = self.default_season_id or derive_uuid("season", season_val)

        # Extract Match Dates
        dates = info.get("dates") or []
        if dates:
            try:
                match_date = parse_match_date(str(dates[0]))
            except Exception:
                match_date = date(2024, 1, 1)
        else:
            match_date = date(2024, 1, 1)

        # Pre-2008 IPL Quarantine Rule
        info_event = info.get("event") or {}
        is_ipl = "indian premier league" in str(info_event.get("name", "")).lower()
        if is_ipl and match_date < date(2008, 4, 18):
            quarantine_reasons.append(f"IPL match date {match_date} precedes inaugural tournament 2008-04-18")

        # Extract Registry (people hashes)
        info_registry = info.get("registry") or {}
        registry_people = info_registry.get("people") or {}
        player_registry: dict[str, str] = {}
        player_id_map: dict[str, UUID] = {}

        for p_name, p_hash in registry_people.items():
            player_registry[p_name] = str(p_hash)
            player_id_map[p_name] = derive_uuid("player", str(p_hash))

        # Register players from info.players if any were missing in registry
        info_players = info.get("players") or {}
        for t_name, p_list in info_players.items():
            if t_name not in team_id_map:
                team_id_map[t_name] = derive_uuid("team", t_name)
            for p in p_list:
                if p not in player_id_map:
                    p_id = derive_uuid("player", p)
                    player_id_map[p] = p_id

        # Toss details
        toss_info = info.get("toss") or {}
        toss_winner_name = toss_info.get("winner")
        toss_winner_id = team_id_map.get(toss_winner_name) if toss_winner_name else None
        raw_toss_decision = str(toss_info.get("decision", "")).lower()
        toss_decision: str | None = raw_toss_decision if raw_toss_decision in ("bat", "field") else None

        # Outcome details & Eliminator / Super Over resolution
        outcome = info.get("outcome") or {}
        eliminator = outcome.get("eliminator")
        winner_name = outcome.get("winner") or eliminator
        winner_id = team_id_map.get(winner_name) if winner_name else None

        by_dict = outcome.get("by") or {}
        win_margin_runs = by_dict.get("runs")
        win_margin_wickets = by_dict.get("wickets")

        result = str(outcome.get("result", "")).lower()
        method_str = str(outcome.get("method", "")).lower()

        # Outcome type discrimination
        if eliminator or result == "super_over" or "super over" in method_str or "eliminator" in method_str:
            outcome_type = "super_over"
        elif win_margin_runs is not None:
            outcome_type = "runs"
        elif win_margin_wickets is not None:
            outcome_type = "wickets"
        elif result == "tie":
            outcome_type = "tie"
        elif result in ("no result", "no_result"):
            outcome_type = "no_result"
        elif result == "abandoned":
            outcome_type = "abandoned"
        elif winner_id is not None:
            outcome_type = "runs"
        else:
            outcome_type = "no_result"

        # DLS check
        is_dls = "dls" in method_str or "d/l" in method_str
        dls_version = outcome.get("method") if is_dls else None

        # Match Status
        if outcome_type == "abandoned":
            status = "Abandoned"
        elif outcome_type == "no_result":
            status = "No Result"
        else:
            status = "Completed"

        # Scheduled balls
        balls_per_over = int(info.get("balls_per_over") or 6)
        overs_scheduled = int(info.get("overs") or 20)
        innings_balls_scheduled = overs_scheduled * balls_per_over

        match_type = str(info.get("match_type") or "T20")

        # Player of match resolution
        pom_list = info.get("player_of_match") or []
        pom_id: UUID | None = None
        if pom_list:
            pom_name = str(pom_list[0]).strip()
            if pom_name not in player_id_map:
                player_id_map[pom_name] = derive_uuid("player", pom_name)
            pom_id = player_id_map[pom_name]

        # Match number parsing
        raw_mn = info_event.get("match_number")
        match_number: int | None = None
        if raw_mn is not None:
            try:
                match_number = int(raw_mn)
            except (ValueError, TypeError):
                match_number = None

        # Build Match Contract
        match_contract = Match(
            match_id=derive_uuid("match", external_id or f"{team1_name}_vs_{team2_name}_{match_date}"),
            external_cricsheet_id=external_id or None,
            season_id=season_id,
            venue_id=venue_id,
            match_number=match_number,
            match_type=match_type,
            match_date=match_date,
            home_team_id=team_id_map[team1_name],
            away_team_id=team_id_map[team2_name],
            toss_winner_id=toss_winner_id,
            toss_decision=toss_decision,
            winner_id=winner_id,
            outcome_type=outcome_type,
            win_margin_runs=int(win_margin_runs) if win_margin_runs is not None else None,
            win_margin_wickets=int(win_margin_wickets) if win_margin_wickets is not None else None,
            is_dls_applied=is_dls,
            dls_method_version=dls_version,
            player_of_match_id=pom_id,
            innings_balls_scheduled=innings_balls_scheduled,
            status=status,
        )

        # Process Innings and Deliveries
        raw_innings = data.get("innings") or []
        parsed_innings: list[Innings] = []
        parsed_deliveries: list[Delivery] = []

        for inn_idx, inn_data in enumerate(raw_innings):
            inn_obj, delivs = self._parse_single_innings(
                inn_data=inn_data,
                innings_number=inn_idx + 1,
                match_id=match_contract.match_id,
                team1_name=team1_name,
                team2_name=team2_name,
                team_id_map=team_id_map,
                player_id_map=player_id_map,
                season_year=season_year,
                match_type=match_type,
                balls_per_over=balls_per_over,
                overs_scheduled=overs_scheduled,
            )
            if inn_obj:
                parsed_innings.append(inn_obj)
                parsed_deliveries.extend(delivs)

        return CricSheetParsedMatch(
            match=match_contract,
            innings=parsed_innings,
            deliveries=parsed_deliveries,
            player_registry=player_registry,
            player_id_map=player_id_map,
            team_id_map=team_id_map,
            venue_id=venue_id,
            venue_name=venue_name,
            season_name=season_val,
            data_version=data_version,
            raw_payload=data,
            quarantine_reasons=quarantine_reasons,
        )

    def _parse_single_innings(
        self,
        inn_data: dict[str, Any],
        innings_number: int,
        match_id: UUID,
        team1_name: str,
        team2_name: str,
        team_id_map: dict[str, UUID],
        player_id_map: dict[str, UUID],
        season_year: str,
        match_type: str,
        balls_per_over: int,
        overs_scheduled: int,
    ) -> tuple[Innings | None, list[Delivery]]:
        """Parse one innings block in either v1.3.0 or legacy format."""
        # Handle legacy wrapper: e.g. {"1st innings": {"team": ..., "deliveries": ...}}
        if not inn_data.get("team") and len(inn_data) == 1:
            key = next(iter(inn_data.keys()))
            inn_data = inn_data[key]

        batting_team_name = str(inn_data.get("team", "")).strip()
        if not batting_team_name:
            return None, []

        if batting_team_name not in team_id_map:
            team_id_map[batting_team_name] = derive_uuid("team", batting_team_name)

        batting_team_id = team_id_map[batting_team_name]
        # Opponent is the other team
        bowling_team_name = team2_name if batting_team_name == team1_name else team1_name
        bowling_team_id = team_id_map.get(bowling_team_name, derive_uuid("team", bowling_team_name))

        is_super_over = bool(inn_data.get("super_over", False))

        target = inn_data.get("target") or {}
        target_runs = target.get("runs")
        target_overs = target.get("overs")
        target_overs_balls = int(target_overs * balls_per_over) if target_overs else None

        # Build Innings UUID
        innings_id = derive_uuid(
            "innings",
            f"{match_id}:{innings_number}:{is_super_over}",
        )

        deliveries: list[Delivery] = []
        delivery_seq = 1
        total_runs = 0
        total_wickets = 0
        total_legal_deliveries = 0
        total_extras = 0

        # CricSheet v1.3.0 has "overs": [{"over": 0, "deliveries": [...]}]
        # Legacy CricSheet has "deliveries": [{0.1: {...}}]
        raw_overs = inn_data.get("overs")
        if raw_overs is not None:
            for over_dict in raw_overs:
                over_num = int(over_dict.get("over", 0))
                ball_in_over = 1
                for deliv_data in over_dict.get("deliveries", []):
                    deliv_obj = self._parse_delivery(
                        deliv_data=deliv_data,
                        innings_id=innings_id,
                        season_year=season_year,
                        over_number=over_num,
                        ball_in_over=ball_in_over,
                        delivery_sequence=delivery_seq,
                        player_id_map=player_id_map,
                        match_type=match_type,
                        balls_per_over=balls_per_over,
                    )
                    deliveries.append(deliv_obj)
                    delivery_seq += 1
                    ball_in_over += 1

                    total_runs += deliv_obj.runs_total
                    total_extras += deliv_obj.runs_extras
                    if not deliv_obj.is_wide and not deliv_obj.is_noball:
                        total_legal_deliveries += 1
                    if deliv_obj.is_wicket:
                        total_wickets += 1

        elif "deliveries" in inn_data:
            # Legacy format
            for item in inn_data.get("deliveries", []):
                for ball_key, deliv_data in item.items():
                    ball_str = str(ball_key).strip()
                    if "." in ball_str:
                        parts = ball_str.split(".")
                        try:
                            over_num = int(parts[0])
                            ball_in_over = int(parts[1])
                        except (ValueError, IndexError):
                            over_num = 0
                            ball_in_over = 1
                    else:
                        try:
                            over_num = int(ball_str)
                            ball_in_over = 1
                        except ValueError:
                            over_num = 0
                            ball_in_over = 1

                    deliv_obj = self._parse_delivery(
                        deliv_data=deliv_data,
                        innings_id=innings_id,
                        season_year=season_year,
                        over_number=over_num,
                        ball_in_over=ball_in_over,
                        delivery_sequence=delivery_seq,
                        player_id_map=player_id_map,
                        match_type=match_type,
                        balls_per_over=balls_per_over,
                    )
                    deliveries.append(deliv_obj)
                    delivery_seq += 1

                    total_runs += deliv_obj.runs_total
                    total_extras += deliv_obj.runs_extras
                    if not deliv_obj.is_wide and not deliv_obj.is_noball:
                        total_legal_deliveries += 1
                    if deliv_obj.is_wicket:
                        total_wickets += 1

        innings_contract = Innings(
            innings_id=innings_id,
            match_id=match_id,
            innings_number=innings_number,
            batting_team_id=batting_team_id,
            bowling_team_id=bowling_team_id,
            is_super_over=is_super_over,
            overs_allocated_balls=overs_scheduled * balls_per_over,
            target_runs=int(target_runs) if target_runs is not None else None,
            target_overs_balls=target_overs_balls,
            total_runs=total_runs,
            total_wickets=total_wickets,
            total_legal_deliveries=total_legal_deliveries,
            total_extras=total_extras,
            is_declared=bool(inn_data.get("declared", False)),
        )

        return innings_contract, deliveries

    def _parse_delivery(
        self,
        deliv_data: dict[str, Any],
        innings_id: UUID,
        season_year: str,
        over_number: int,
        ball_in_over: int,
        delivery_sequence: int,
        player_id_map: dict[str, UUID],
        match_type: str,
        balls_per_over: int = 6,
    ) -> Delivery:
        """Parse discrete ball delivery event."""
        batter_name = str(deliv_data.get("batter", deliv_data.get("batsman", "Unknown Batter"))).strip()
        bowler_name = str(deliv_data.get("bowler", "Unknown Bowler")).strip()
        non_striker_name = str(deliv_data.get("non_striker", "Unknown NonStriker")).strip()

        if batter_name not in player_id_map:
            player_id_map[batter_name] = derive_uuid("player", batter_name)
        if bowler_name not in player_id_map:
            player_id_map[bowler_name] = derive_uuid("player", bowler_name)
        if non_striker_name not in player_id_map:
            player_id_map[non_striker_name] = derive_uuid("player", non_striker_name)

        runs_dict = deliv_data.get("runs") or {}
        runs_batter = int(runs_dict.get("batter", runs_dict.get("batsman", 0)) or 0)
        runs_extras = int(runs_dict.get("extras", 0) or 0)
        runs_total = runs_batter + runs_extras

        # Extras breakdown
        extras_dict = deliv_data.get("extras") or {}
        runs_wides = int(extras_dict.get("wides", 0) or 0)
        runs_noballs = int(extras_dict.get("noballs", 0) or 0)
        runs_byes = int(extras_dict.get("byes", 0) or 0)
        runs_legbyes = int(extras_dict.get("legbyes", 0) or 0)
        runs_penalties = int(extras_dict.get("penalty", extras_dict.get("penalties", 0)) or 0)

        is_wide = runs_wides > 0
        is_noball = runs_noballs > 0
        is_bye = runs_byes > 0
        is_legbye = runs_legbyes > 0
        is_penalty = runs_penalties > 0

        # Dismissal / Wicket (handle both plural "wickets" list and legacy singular "wicket" dict)
        wickets = deliv_data.get("wickets")
        if wickets is None:
            single_w = deliv_data.get("wicket")
            wickets = [single_w] if isinstance(single_w, dict) else []
        elif isinstance(wickets, dict):
            wickets = [wickets]

        # Prioritize true dismissals over non-dismissal retirements (e.g. retired hurt)
        true_wickets = [
            w for w in wickets
            if isinstance(w, dict) and str(w.get("kind", "")).strip().lower() != "retired hurt"
        ]
        is_wicket = len(true_wickets) > 0
        wicket_kind: str | None = None
        player_out_id: UUID | None = None
        is_bowler_credited = False

        if is_wicket:
            w0 = true_wickets[0]
            raw_kind = str(w0.get("kind", "")).strip().lower()
            wicket_kind = raw_kind or "dismissal"
            player_out_name = str(w0.get("player_out", batter_name)).strip()
            if player_out_name not in player_id_map:
                player_id_map[player_out_name] = derive_uuid("player", player_out_name)
            player_out_id = player_id_map[player_out_name]
            is_bowler_credited = is_bowler_credited_wicket(wicket_kind)
        elif len(wickets) > 0 and isinstance(wickets[0], dict) and str(wickets[0].get("kind", "")).strip().lower() == "retired hurt":
            # Retired hurt: batsman retires not out; does NOT credit a wicket lost to the team
            wicket_kind = "retired hurt"
            is_wicket = False
            player_out_id = None
            is_bowler_credited = False

        match_phase = determine_match_phase(over_number, match_type, balls_per_over)

        delivery_id = derive_uuid(
            "delivery",
            f"{innings_id}:{over_number}:{ball_in_over}:{delivery_sequence}",
        )

        return Delivery(
            delivery_id=delivery_id,
            innings_id=innings_id,
            season_year=season_year,
            over_number=over_number,
            ball_in_over=ball_in_over,
            delivery_sequence=delivery_sequence,
            batter_id=player_id_map[batter_name],
            bowler_id=player_id_map[bowler_name],
            non_striker_id=player_id_map[non_striker_name],
            runs_batter=runs_batter,
            runs_extras=runs_extras,
            runs_total=runs_total,
            is_wide=is_wide,
            is_noball=is_noball,
            is_bye=is_bye,
            is_legbye=is_legbye,
            is_penalty=is_penalty,
            runs_wides=runs_wides,
            runs_noballs=runs_noballs,
            runs_byes=runs_byes,
            runs_legbyes=runs_legbyes,
            runs_penalties=runs_penalties,
            is_wicket=is_wicket,
            wicket_kind=wicket_kind,
            player_out_id=player_out_id,
            is_bowler_credited_wicket=is_bowler_credited,
            match_phase=match_phase,
        )

    def _create_empty_match(self, external_id: str) -> Match:
        """Create placeholder Match for quarantined/unparsable payloads."""
        dummy_id = derive_uuid("match", external_id or "corrupted_match")
        return Match(
            match_id=dummy_id,
            external_cricsheet_id=external_id or None,
            season_id=derive_uuid("season", "unknown"),
            venue_id=derive_uuid("venue", "unknown"),
            match_type="T20",
            match_date=date(2024, 1, 1),
            home_team_id=derive_uuid("team", "dummy_home"),
            away_team_id=derive_uuid("team", "dummy_away"),
            outcome_type="abandoned",
            status="Abandoned",
        )
