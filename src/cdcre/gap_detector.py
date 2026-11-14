"""Career Gap Detector and Classifier for CDCRE.

Part of Phase 04A — Career Discovery & Competition Research Engine (Milestone 4).
Detects multi-season career gaps across tournament history and classifies them into
authoritative GapType taxonomies:
- FRANCHISE_SUSPENSION: Rajasthan Royals 2016-2017 absence per Supreme Court Order.
  Takes precedence over individual injury/NOC for RR players in IPL 2016-2017.
- INJURY: Corroborated with player_injuries evidence.
- NOC_DENIED: Corroborated with national board NOC denial in player_availability.
- UNAVAILABLE: Corroborated with personal reasons / unavailability status.
- UNEXPLAINED_GAP: Default uncorroborated gap.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import date, timedelta
from uuid import UUID

from src.cdcre.competition_registry import (
    derive_provenance_uuid,
    normalize_competition_name,
)
from src.contracts.career import PlayerAvailability, PlayerInjury
from src.contracts.cdcre import (
    CareerGapRecord,
    CompetitionHistoryRecord,
    CoverageStatus,
    GapType,
)


def parse_season_start_year(season_str: str) -> int | None:
    """Extract integer starting year from season string (e.g. '2024', '2023/24', '2015-16')."""
    if not season_str or not isinstance(season_str, str):
        return None
    s = season_str.strip()
    if "/" in s:
        s = s.split("/")[0].strip()
    elif "-" in s:
        s = s.split("-")[0].strip()

    if s.isdigit():
        return int(s)

    match = re.search(r"\b(19\d\d|20\d\d)\b", season_str)
    if match:
        return int(match.group(1))
    return None


def format_gap_season(year: int, template_season: str) -> str:
    """Format a missing year according to the season format style of a template season."""
    template = template_season.strip()
    if "/" in template:
        parts = template.split("/")
        if len(parts) == 2 and len(parts[1]) == 2:
            return f"{year}/{str(year + 1)[2:]}"
        if len(parts) == 2 and len(parts[1]) == 4:
            return f"{year}/{year + 1}"
    elif "-" in template:
        parts = template.split("-")
        if len(parts) == 2 and len(parts[1]) == 2:
            return f"{year}-{str(year + 1)[2:]}"
        if len(parts) == 2 and len(parts[1]) == 4:
            return f"{year}-{year + 1}"
    return str(year)


def _check_injury_overlap(
    injury: PlayerInjury,
    missing_years: Sequence[int],
) -> bool:
    """Determine whether a PlayerInjury record overlaps any of the missing gap years."""
    inj_start: date | None = injury.injury_date
    inj_end: date | None = injury.return_to_play_date

    if inj_start is not None and inj_end is None and injury.recovery_time_days:
        inj_end = inj_start + timedelta(days=injury.recovery_time_days)
    elif inj_start is not None and inj_end is None:
        inj_end = inj_start

    for y in missing_years:
        season_start = date(y, 1, 1)
        season_end = date(y, 12, 31)

        if inj_start is not None and inj_end is not None:
            if inj_start <= season_end and inj_end >= season_start:
                return True
        elif (inj_start is not None and inj_start.year == y) or (
            injury.medical_notes and str(y) in injury.medical_notes
        ):
            return True

    return False


def _check_availability_overlap(
    avail: PlayerAvailability,
    missing_years: Sequence[int],
) -> bool:
    """Determine whether a PlayerAvailability record overlaps any of the missing gap years."""
    for y in missing_years:
        season_start = date(y, 1, 1)
        season_end = date(y, 12, 31)
        if avail.start_date <= season_end and avail.end_date >= season_start:
            return True
    return False


def detect_career_gaps(
    player_id: UUID,
    history: list[CompetitionHistoryRecord],
    injuries: list[PlayerInjury] | None = None,
    availability: list[PlayerAvailability] | None = None,
    team_affiliations: list[str] | None = None,
) -> list[CareerGapRecord]:
    """Detect and classify chronological career gaps across competition history.

    Rules & Invariants:
    1. Gaps are identified between active verified participation seasons (appearances > 0).
    2. Rajasthan Royals (RR) absence in seasons 2016-2017 is strictly classified as
       GapType.FRANCHISE_SUSPENSION (Supreme Court order), taking precedence over injury/NOC.
    3. Gaps overlapping player_injuries evidence are classified as GapType.INJURY.
    4. Gaps with national_board_noc_status == "DENIED" are classified as GapType.NOC_DENIED.
    5. Gaps with availability_status in ("UNAVAILABLE", "PERSONAL_REASONS") are GapType.UNAVAILABLE.
    6. Uncorroborated gaps default to GapType.UNEXPLAINED_GAP.

    Args:
        player_id: Canonical UUID identifying the player.
        history: List of CompetitionHistoryRecord participation records.
        injuries: Optional player medical/injury evidence.
        availability: Optional player NOC / availability evidence.
        team_affiliations: List of historical team affiliations (e.g. ['Rajasthan Royals']).

    Returns:
        List of validated CareerGapRecord contracts, sorted chronologically.

    Raises:
        TypeError: If player_id cannot be interpreted as a valid UUID.
    """
    if not isinstance(player_id, UUID):
        try:
            player_id = UUID(str(player_id))
        except (ValueError, AttributeError) as exc:
            raise TypeError(
                f"player_id must be a UUID instance, got {type(player_id).__name__}: {player_id!r}"
            ) from exc

    if not history:
        return []

    # Group records by competition name
    records_by_comp: dict[str, list[CompetitionHistoryRecord]] = {}
    for rec in history:
        records_by_comp.setdefault(rec.competition_name, []).append(rec)

    detected_gaps: list[CareerGapRecord] = []

    for comp_name, comp_recs in records_by_comp.items():
        norm_comp = normalize_competition_name(comp_name)

        # Active verified participation seasons
        active_seasons: dict[str, CompetitionHistoryRecord] = {}
        for r in comp_recs:
            if (
                r.coverage_status == CoverageStatus.VERIFIED_PARTICIPATION
                and r.appearances is not None
                and r.appearances > 0
            ):
                active_seasons[r.season_year] = r

        if len(active_seasons) < 2:
            continue

        # Parse and sort active seasons chronologically
        parsed_seasons: list[tuple[int, str, CompetitionHistoryRecord]] = []
        for s_year, rec in active_seasons.items():
            start_yr = parse_season_start_year(s_year)
            if start_yr is not None:
                parsed_seasons.append((start_yr, s_year, rec))

        parsed_seasons.sort(key=lambda item: item[0])

        # Evaluate consecutive season pairs for breaks
        for idx in range(len(parsed_seasons) - 1):
            curr_yr, curr_season, _ = parsed_seasons[idx]
            next_yr, next_season, _ = parsed_seasons[idx + 1]

            if next_yr - curr_yr <= 1:
                # Consecutive seasons, no gap
                continue

            missing_years = list(range(curr_yr + 1, next_yr))

            # Build gap_seasons representation preserving known dataset formats
            gap_seasons: list[str] = []
            for y in missing_years:
                # Check if an existing record in history matches year y
                matching_rec = next(
                    (r for r in comp_recs if parse_season_start_year(r.season_year) == y),
                    None,
                )
                if matching_rec is not None:
                    gap_seasons.append(matching_rec.season_year)
                else:
                    gap_seasons.append(format_gap_season(y, curr_season))

            start_season = gap_seasons[0]
            end_season = gap_seasons[-1]

            # -------------------------------------------------------------
            # Classification Precedence Engine
            # -------------------------------------------------------------
            gap_type: GapType = GapType.UNEXPLAINED_GAP
            evidence_notes: str | None = None
            provenance_record_id: UUID | None = None

            # 1. FRANCHISE_SUSPENSION (Supreme Court Order)
            is_ipl = "Indian Premier League" in norm_comp or norm_comp == "IPL"
            has_suspension_years = any(y in (2016, 2017) for y in missing_years)

            is_rr_player = False
            if team_affiliations is not None and len(team_affiliations) > 0:
                is_rr_player = any(
                    "rajasthan" in t.lower() or t.strip().upper() == "RR"
                    for t in team_affiliations
                )
            else:
                # Per dispatch requirement: When a player had RR affiliation/participation
                # in IPL prior to 2016 (or returned in 2018), this gap in IPL participation
                # must be classified as FRANCHISE_SUSPENSION
                is_rr_player = (curr_yr < 2016) or (next_yr >= 2018)

            if is_ipl and has_suspension_years and is_rr_player:
                gap_type = GapType.FRANCHISE_SUSPENSION
                evidence_notes = (
                    "Rajasthan Royals franchise suspension per Supreme Court committee order (2016-2017)"
                )
                provenance_record_id = derive_provenance_uuid(
                    f"FRANCHISE_SUSPENSION:RR:{player_id}:{start_season}_{end_season}"
                )

            # 2. INJURY Corroboration
            if gap_type == GapType.UNEXPLAINED_GAP and injuries:
                for inj in injuries:
                    if _check_injury_overlap(inj, missing_years):
                        gap_type = GapType.INJURY
                        evidence_notes = (
                            inj.medical_notes
                            or f"Injury corroborated: {inj.injury_type or 'Medical condition'} "
                            f"(severity: {inj.severity or 'Unspecified'}), injury date {inj.injury_date}"
                        )
                        provenance_record_id = inj.source_record_id or derive_provenance_uuid(
                            f"INJURY:{inj.injury_id}:{player_id}"
                        )
                        break

            # 3. NOC_DENIED Corroboration
            if gap_type == GapType.UNEXPLAINED_GAP and availability:
                for avail in availability:
                    if (
                        avail.national_board_noc_status == "DENIED"
                        and _check_availability_overlap(avail, missing_years)
                    ):
                        gap_type = GapType.NOC_DENIED
                        evidence_notes = (
                            avail.reason_for_unavailability
                            or "Corroborated by national board NOC denial"
                        )
                        provenance_record_id = avail.source_record_id or derive_provenance_uuid(
                            f"NOC:{avail.availability_id}:{player_id}"
                        )
                        break

            # 4. UNAVAILABLE Corroboration
            if gap_type == GapType.UNEXPLAINED_GAP and availability:
                for avail in availability:
                    status_upper = (avail.availability_status or "").upper()
                    reason_lower = (avail.reason_for_unavailability or "").lower()
                    is_unavail = (
                        status_upper in ("UNAVAILABLE", "PERSONAL_REASONS")
                        or any(kw in reason_lower for kw in ("personal", "unavailable", "family", "rest"))
                    )
                    if is_unavail and _check_availability_overlap(avail, missing_years):
                        gap_type = GapType.UNAVAILABLE
                        evidence_notes = (
                            avail.reason_for_unavailability
                            or f"Player unavailable: {avail.availability_status}"
                        )
                        provenance_record_id = avail.source_record_id or derive_provenance_uuid(
                            f"AVAILABILITY:{avail.availability_id}:{player_id}"
                        )
                        break

            # 5. UNEXPLAINED_GAP (Default)
            if gap_type == GapType.UNEXPLAINED_GAP:
                evidence_notes = (
                    "Unexplained career gap; no corroborating franchise, injury, or availability records found."
                )
                provenance_record_id = None

            gap_record = CareerGapRecord(
                player_id=player_id,
                start_season=start_season,
                end_season=end_season,
                gap_seasons=gap_seasons,
                gap_type=gap_type,
                competition_name=norm_comp,
                evidence_notes=evidence_notes,
                provenance_record_id=provenance_record_id,
            )
            detected_gaps.append(gap_record)

    # Sort deterministically by competition name then start season
    detected_gaps.sort(key=lambda g: (g.competition_name, g.start_season))
    return detected_gaps


class CareerGapDetector:
    """Specialized detector and classifier for multi-season career gaps.

    Detects chronological breaks between active participation seasons across competition
    history and classifies gaps into authoritative GapType categories:
    - FRANCHISE_SUSPENSION: Supreme Court Order (RR 2016-2017)
    - INJURY: Corroborated with medical / injury records
    - NOC_DENIED: Corroborated with national board NOC denial
    - UNAVAILABLE: Personal reasons or player unavailability
    - UNEXPLAINED_GAP: Default uncorroborated gap
    """

    def __init__(
        self,
        injuries: list[PlayerInjury] | None = None,
        availability: list[PlayerAvailability] | None = None,
        team_affiliations: list[str] | None = None,
    ) -> None:
        self.injuries = injuries or []
        self.availability = availability or []
        self.team_affiliations = team_affiliations or []

    def detect_career_gaps(
        self,
        player_id: UUID,
        history: list[CompetitionHistoryRecord],
        injuries: list[PlayerInjury] | None = None,
        availability: list[PlayerAvailability] | None = None,
        team_affiliations: list[str] | None = None,
    ) -> list[CareerGapRecord]:
        """Detect and classify career gaps using configured or override evidence."""
        effective_injuries = injuries if injuries is not None else self.injuries
        effective_availability = availability if availability is not None else self.availability
        effective_affiliations = team_affiliations if team_affiliations is not None else self.team_affiliations

        return detect_career_gaps(
            player_id=player_id,
            history=history,
            injuries=effective_injuries,
            availability=effective_availability,
            team_affiliations=effective_affiliations,
        )


__all__ = [
    "CareerGapDetector",
    "detect_career_gaps",
    "format_gap_season",
    "parse_season_start_year",
]
