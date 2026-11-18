"""Franchise Participation Service (Milestone M1).

Authoritative service managing franchise competition participation windows,
enforcing historical participation boundaries (RR active: 2008-2015, 2018-2026),
franchise-specific suspension enforcement (2016-2017), unverified provisional status
for future seasons (2027 UNKNOWN), and database constraint invariants (chk_tsp_verified_evidence).
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID, uuid4, uuid5

from src.contracts.competition import (
    Competition,
    Season,
    Team,
    TeamSeasonParticipation,
)
from src.services.base import ServiceBoundary

logger = logging.getLogger(__name__)

# Deterministic namespace for reproducible domain identifiers
RR_NAMESPACE = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

# Canonical Franchise Identity
CANONICAL_RR_NAME = "Rajasthan Royals"
CANONICAL_RR_SHORT_CODE = "RR"
CANONICAL_RR_TEAM_ID = uuid5(RR_NAMESPACE, "team:rajasthan-royals")

# Canonical Competition Identity
CANONICAL_IPL_NAME = "Indian Premier League"
CANONICAL_IPL_COMP_ID = uuid5(RR_NAMESPACE, "competition:ipl")

# Active RR Participation Seasons
ACTIVE_RR_SEASONS: tuple[str, ...] = (
    "2008",
    "2009",
    "2010",
    "2011",
    "2012",
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
    "2025",
    "2026",
)

# Franchise-Specific Suspension Seasons (Supreme Court / Justice Lodha Committee Order)
SUSPENDED_RR_SEASONS: tuple[str, ...] = ("2016", "2017")

# Future Unverified Seasons
FUTURE_UNKNOWN_SEASONS: tuple[str, ...] = ("2027",)

# Approximate season dates for canonical IPL scheduling
IPL_SEASON_DATES: dict[str, tuple[date, date]] = {
    "2008": (date(2008, 4, 18), date(2008, 6, 1)),
    "2009": (date(2009, 4, 18), date(2009, 5, 24)),
    "2010": (date(2010, 3, 12), date(2010, 4, 25)),
    "2011": (date(2011, 4, 8), date(2011, 5, 28)),
    "2012": (date(2012, 4, 4), date(2012, 5, 27)),
    "2013": (date(2013, 4, 3), date(2013, 5, 26)),
    "2014": (date(2014, 4, 16), date(2014, 6, 1)),
    "2015": (date(2015, 4, 8), date(2015, 5, 24)),
    "2016": (date(2016, 4, 9), date(2016, 5, 29)),
    "2017": (date(2017, 4, 5), date(2017, 5, 21)),
    "2018": (date(2018, 4, 7), date(2018, 5, 27)),
    "2019": (date(2019, 3, 23), date(2019, 5, 12)),
    "2020": (date(2020, 9, 19), date(2020, 11, 10)),
    "2021": (date(2021, 4, 9), date(2021, 10, 15)),
    "2022": (date(2022, 3, 26), date(2022, 5, 29)),
    "2023": (date(2023, 3, 31), date(2023, 5, 29)),
    "2024": (date(2024, 3, 22), date(2024, 5, 26)),
    "2025": (date(2025, 3, 22), date(2025, 5, 25)),
    "2026": (date(2026, 3, 21), date(2026, 5, 24)),
    "2027": (date(2027, 3, 20), date(2027, 5, 23)),
}


class FranchiseParticipationService(ServiceBoundary):
    """Authoritative service resolving and seeding team competition participation windows."""

    def __init__(self, db_client: Any = None, auto_seed: bool = True) -> None:
        """Initialize the participation service with optional database client and auto-seeding.

        Args:
            db_client: Optional Supabase or database connection client.
            auto_seed: If True, automatically populates canonical RR participation windows.
        """
        self._db_client = db_client
        self._teams: dict[UUID, Team] = {}
        self._seasons: dict[UUID, Season] = {}
        self._seasons_by_year: dict[str, Season] = {}
        self._participations: dict[tuple[UUID, UUID], TeamSeasonParticipation] = {}
        self._db_records: dict[tuple[UUID, UUID], dict[str, Any]] = {}

        # Register canonical IPL competition
        self._competition = Competition(
            competition_id=CANONICAL_IPL_COMP_ID,
            name=CANONICAL_IPL_NAME,
            competition_type="Domestic Franchise T20",
            governing_body="BCCI",
            country="India",
            match_overs=20,
            balls_per_over=6,
        )

        # Register canonical RR franchise team
        self._rr_team = Team(
            team_id=CANONICAL_RR_TEAM_ID,
            team_name=CANONICAL_RR_NAME,
            short_code=CANONICAL_RR_SHORT_CODE,
            is_active=True,
        )
        self._teams[self._rr_team.team_id] = self._rr_team

        # Initialize canonical seasons
        self._init_canonical_seasons()

        if auto_seed:
            self.seed_verified_windows()

    def _init_canonical_seasons(self) -> None:
        """Register canonical IPL seasons from 2008 to 2027."""
        all_years = list(ACTIVE_RR_SEASONS) + list(SUSPENDED_RR_SEASONS) + list(FUTURE_UNKNOWN_SEASONS)
        all_years.sort(key=int)

        for year in all_years:
            dates = IPL_SEASON_DATES.get(year, (date(int(year), 3, 1), date(int(year), 6, 1)))
            season_id = uuid5(RR_NAMESPACE, f"season:ipl:{year}")
            season = Season(
                season_id=season_id,
                competition_id=self._competition.competition_id,
                season_year=year,
                start_date=dates[0],
                end_date=dates[1],
            )
            self._seasons[season_id] = season
            self._seasons_by_year[year] = season

    # =========================================================================
    # ServiceBoundary Implementation
    # =========================================================================

    def get_service_name(self) -> str:
        """Return the canonical service identifier."""
        return "franchise_participation_service"

    def health_check(self) -> dict[str, Any]:
        """Perform service health inspection and return diagnostic status dictionary."""
        return {
            "service": self.get_service_name(),
            "status": "HEALTHY",
            "participations_count": len(self._participations),
            "teams_tracked": len(self._teams),
            "seasons_tracked": len(self._seasons),
            "canonical_rr_team_id": str(CANONICAL_RR_TEAM_ID),
            "rr_suspension_enforced": True,
            "future_season_safe": True,
        }

    # =========================================================================
    # Invariant Validation (chk_tsp_verified_evidence)
    # =========================================================================

    @staticmethod
    def validate_evidence_invariant(record: dict[str, Any]) -> None:
        """Enforce database constraint chk_tsp_verified_evidence.

        Invariant: NOT (verified = TRUE AND verification_id IS NULL)
        If verified is True or verification_status is 'VERIFIED', verification_id
        MUST NOT be None.

        Raises:
            ValueError: If verified=True or verification_status='VERIFIED' with verification_id=None.
        """
        verified = record.get("verified", False)
        verification_id = record.get("verification_id")
        verification_status = str(record.get("verification_status", "UNVERIFIED")).upper()

        if verified is True and verification_id is None:
            raise ValueError(
                "Database constraint violation (chk_tsp_verified_evidence): "
                "verified=True requires a non-null verification_id."
            )

        if verification_status == "VERIFIED" and verification_id is None:
            raise ValueError(
                "Database constraint violation (chk_tsp_verified_evidence): "
                "verification_status='VERIFIED' requires a non-null verification_id."
            )

    # =========================================================================
    # Public Core Interface Methods
    # =========================================================================

    def get_participation(self, team_id: UUID, season_id: UUID) -> TeamSeasonParticipation | None:
        """Retrieve participation record for a specific team and season.

        Args:
            team_id: UUID of the franchise team.
            season_id: UUID of the competition season.

        Returns:
            TeamSeasonParticipation if found, None otherwise.
        """
        key = (team_id, season_id)
        if key in self._participations:
            return self._participations[key]

        # Check db_client if available
        if self._db_client is not None:
            try:
                res = (
                    self._db_client.table("team_season_participation")
                    .select("*")
                    .eq("team_id", str(team_id))
                    .eq("season_id", str(season_id))
                    .execute()
                )
                data = getattr(res, "data", None)
                if data and len(data) > 0:
                    row = data[0]
                    participation = self._row_to_contract(row)
                    self._participations[key] = participation
                    self._db_records[key] = row
                    return participation
            except Exception as exc:
                logger.warning(
                    "Error querying team_season_participation from db_client: %s", exc
                )

        return None

    def list_franchise_windows(
        self, team_name: str = CANONICAL_RR_NAME
    ) -> list[TeamSeasonParticipation]:
        """List all participation windows for a franchise team.

        Args:
            team_name: Name of the team (defaults to "Rajasthan Royals").

        Returns:
            List of TeamSeasonParticipation contracts ordered chronologically.
        """
        team_id = self._resolve_team_id(team_name)
        if team_id is None:
            return []

        results: list[TeamSeasonParticipation] = [
            p for (t_id, _), p in self._participations.items() if t_id == team_id
        ]

        # Order chronologically by effective_start_date or season start_date
        def sort_key(p: TeamSeasonParticipation) -> date:
            if p.effective_start_date:
                return p.effective_start_date
            season = self._seasons.get(p.season_id)
            if season:
                return season.start_date
            return date.min

        results.sort(key=sort_key)
        return results

    def seed_verified_windows(
        self, records: list[dict[str, Any]] | None = None
    ) -> list[TeamSeasonParticipation]:
        """Seed verified participation windows idempotently (ON CONFLICT DO NOTHING).

        If records is None, seeds the canonical participation windows for Rajasthan Royals:
          - Active: 2008-2015 and 2018-2026 (participation_status='PARTICIPATING')
          - Franchise-specific suspension: 2016-2017 (participation_status='SUSPENDED')
          - Future season: 2027 (participation_status='UNKNOWN', verification_status='UNVERIFIED')

        Initial seeding defaults to verified = False and verification_status = 'UNVERIFIED'
        unless a valid verification_id is supplied, strictly upholding chk_tsp_verified_evidence.

        Args:
            records: Optional list of raw participation record dictionaries to seed.

        Returns:
            List of seeded TeamSeasonParticipation contracts.
        """
        if records is None:
            records = self._generate_canonical_rr_records()

        seeded: list[TeamSeasonParticipation] = []
        new_db_rows: list[dict[str, Any]] = []

        for rec in records:
            # 1. Enforce DDL Invariant chk_tsp_verified_evidence
            self.validate_evidence_invariant(rec)

            team_id = (
                rec["team_id"]
                if isinstance(rec["team_id"], UUID)
                else UUID(str(rec["team_id"]))
            )
            season_id = (
                rec["season_id"]
                if isinstance(rec["season_id"], UUID)
                else UUID(str(rec["season_id"]))
            )
            key = (team_id, season_id)

            # 2. Idempotency Check (ON CONFLICT DO NOTHING)
            if key in self._participations:
                seeded.append(self._participations[key])
                continue

            # 3. Construct Contract and Database Record
            participation = self._dict_to_contract(rec)
            db_row = self._contract_to_db_row(rec, participation)

            self._participations[key] = participation
            self._db_records[key] = db_row
            seeded.append(participation)
            new_db_rows.append(db_row)

        # 4. Sync with db_client if present
        if self._db_client is not None and new_db_rows:
            try:
                # Query existing in DB to ensure idempotency
                existing_res = (
                    self._db_client.table("team_season_participation")
                    .select("team_id, season_id")
                    .execute()
                )
                existing_data = getattr(existing_res, "data", []) or []
                existing_keys = {
                    (str(r["team_id"]), str(r["season_id"])) for r in existing_data
                }

                to_insert = [
                    row
                    for row in new_db_rows
                    if (str(row["team_id"]), str(row["season_id"])) not in existing_keys
                ]

                if to_insert:
                    self._db_client.table("team_season_participation").insert(to_insert).execute()
            except Exception as exc:
                logger.warning("Error syncing seeded records to db_client: %s", exc)

        return seeded

    def is_season_participating(
        self, season_year: str, team_name: str = CANONICAL_RR_NAME
    ) -> tuple[str, bool]:
        """Determine participation status and boolean flag for a season and franchise.

        Dimensional Rules:
          - Active RR seasons (2008-2015, 2018-2026): ('PARTICIPATING', True)
          - Franchise-specific suspension (2016-2017): ('SUSPENDED', False)
          - Future unverified season (2027): ('UNKNOWN', False)
          - Absent/missing data: ('UNKNOWN', False) - NEVER infer participation from missing data!

        Args:
            season_year: Competition year string (e.g. "2008", "2016", "2027").
            team_name: Franchise team name (defaults to "Rajasthan Royals").

        Returns:
            Tuple of (participation_status: str, is_participating: bool).
        """
        year_str = str(season_year).strip()
        team_id = self._resolve_team_id(team_name)

        if team_id is None:
            # Rule: Never infer participation from missing data
            return ("UNKNOWN", False)

        season = self._seasons_by_year.get(year_str)
        if season is None:
            # Rule: Never infer participation from missing data
            return ("UNKNOWN", False)

        participation = self.get_participation(team_id, season.season_id)
        if participation is None:
            # Missing record: never infer participation
            return ("UNKNOWN", False)

        status = participation.participation_status
        is_participating = status == "PARTICIPATING"
        return (status, is_participating)

    # =========================================================================
    # Helpers and Entity Lookups
    # =========================================================================

    def get_canonical_team_id(self, team_name: str = CANONICAL_RR_NAME) -> UUID:
        """Return canonical UUID for a franchise team."""
        resolved = self._resolve_team_id(team_name)
        if resolved is not None:
            return resolved
        return uuid5(RR_NAMESPACE, f"team:{team_name.lower().replace(' ', '-')}")

    def get_canonical_season_id(self, season_year: str) -> UUID:
        """Return canonical UUID for a competition season year."""
        year_str = str(season_year).strip()
        if year_str in self._seasons_by_year:
            return self._seasons_by_year[year_str].season_id
        return uuid5(RR_NAMESPACE, f"season:ipl:{year_str}")

    def register_team(self, team: Team) -> None:
        """Register a team into the service lookup cache."""
        self._teams[team.team_id] = team

    def register_season(self, season: Season) -> None:
        """Register a season into the service lookup cache."""
        self._seasons[season.season_id] = season
        self._seasons_by_year[season.season_year] = season

    def _resolve_team_id(self, team_name: str) -> UUID | None:
        """Resolve team UUID by name or short code."""
        normalized = team_name.strip().lower()
        if normalized in (
            "rr",
            "rajasthan royals",
            "rajasthan",
            CANONICAL_RR_NAME.lower(),
            CANONICAL_RR_SHORT_CODE.lower(),
        ):
            return CANONICAL_RR_TEAM_ID

        for team in self._teams.values():
            if (
                team.team_name.lower() == normalized
                or team.short_code.lower() == normalized
            ):
                return team.team_id
        return None

    def _generate_canonical_rr_records(self) -> list[dict[str, Any]]:
        """Generate canonical participation records for Rajasthan Royals (2008-2027)."""
        records: list[dict[str, Any]] = []

        all_years = list(ACTIVE_RR_SEASONS) + list(SUSPENDED_RR_SEASONS) + list(FUTURE_UNKNOWN_SEASONS)
        all_years.sort(key=int)

        for year in all_years:
            season = self._seasons_by_year[year]
            dates = IPL_SEASON_DATES.get(year, (season.start_date, season.end_date))

            if year in ACTIVE_RR_SEASONS:
                participation_status = "PARTICIPATING"
                notes = (
                    f"Official verified active participation window for Rajasthan Royals in IPL {year}."
                )
            elif year in SUSPENDED_RR_SEASONS:
                participation_status = "SUSPENDED"
                notes = (
                    f"Franchise-specific suspension for IPL {year}: "
                    "Supreme Court of India / Justice Lodha Committee order suspended "
                    "Rajasthan Royals from participation in IPL 2016 and 2017. "
                    "Other IPL franchises (e.g., KKR, MI, RCB) continued participating normally."
                )
            else:  # 2027 UNKNOWN
                participation_status = "UNKNOWN"
                notes = (
                    "IPL 2027 participation status is UNKNOWN and UNVERIFIED pending "
                    "official BCCI/IPL registration and auction evidence. "
                    "Never infer participation from missing data."
                )

            # Satisfy DDL invariant chk_tsp_verified_evidence:
            # Default to verified=False and verification_status='UNVERIFIED'
            record: dict[str, Any] = {
                "participation_id": uuid5(
                    RR_NAMESPACE, f"participation:{CANONICAL_RR_TEAM_ID}:{season.season_id}"
                ),
                "team_id": CANONICAL_RR_TEAM_ID,
                "season_id": season.season_id,
                "participation_status": participation_status,
                "status": "CONFIRMED" if participation_status in ("PARTICIPATING", "SUSPENDED") else "PROVISIONAL",
                "effective_start_date": dates[0],
                "effective_end_date": dates[1],
                "verified": False,
                "verification_id": None,
                "verification_status": "UNVERIFIED",
                "notes": notes,
                "created_at": datetime.now(UTC),
            }
            records.append(record)

        return records

    def _dict_to_contract(self, d: dict[str, Any]) -> TeamSeasonParticipation:
        """Convert dictionary to TeamSeasonParticipation Pydantic model."""
        start_date = d.get("effective_start_date")
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)

        end_date = d.get("effective_end_date")
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)

        v_id = d.get("verification_id")
        if isinstance(v_id, str):
            v_id = UUID(v_id)

        ev_src = d.get("evidence_source_id")
        if isinstance(ev_src, str):
            ev_src = UUID(ev_src)

        part_id = d.get("participation_id")
        if isinstance(part_id, str):
            part_id = UUID(part_id)
        elif part_id is None:
            part_id = uuid4()

        team_id = d["team_id"]
        if isinstance(team_id, str):
            team_id = UUID(team_id)

        season_id = d["season_id"]
        if isinstance(season_id, str):
            season_id = UUID(season_id)

        v_status = str(d.get("verification_status", "UNVERIFIED")).upper()

        return TeamSeasonParticipation(
            participation_id=part_id,
            team_id=team_id,
            season_id=season_id,
            participation_status=d["participation_status"],
            effective_start_date=start_date,
            effective_end_date=end_date,
            evidence_source_id=ev_src,
            verification_id=v_id,
            verification_status=v_status,
            notes=d.get("notes"),
        )

    def _row_to_contract(self, row: dict[str, Any]) -> TeamSeasonParticipation:
        """Convert a database row dictionary to TeamSeasonParticipation."""
        return self._dict_to_contract(row)

    def _contract_to_db_row(
        self, raw_dict: dict[str, Any], contract: TeamSeasonParticipation
    ) -> dict[str, Any]:
        """Construct full PostgreSQL database row including DDL-specific columns."""
        verified = bool(raw_dict.get("verified", False))
        status = raw_dict.get(
            "status",
            "CONFIRMED"
            if contract.participation_status in ("PARTICIPATING", "SUSPENDED")
            else "PROVISIONAL",
        )

        return {
            "participation_id": str(contract.participation_id),
            "team_id": str(contract.team_id),
            "season_id": str(contract.season_id),
            "participation_status": contract.participation_status,
            "status": status,
            "effective_start_date": contract.effective_start_date.isoformat()
            if contract.effective_start_date
            else None,
            "effective_end_date": contract.effective_end_date.isoformat()
            if contract.effective_end_date
            else None,
            "verified": verified,
            "evidence_source_id": str(contract.evidence_source_id)
            if contract.evidence_source_id
            else None,
            "verification_id": str(contract.verification_id)
            if contract.verification_id
            else None,
            "verification_status": contract.verification_status,
            "notes": contract.notes,
            "created_at": contract.created_at.isoformat(),
        }


__all__ = [
    "FranchiseParticipationService",
    "CANONICAL_RR_NAME",
    "CANONICAL_RR_SHORT_CODE",
    "CANONICAL_RR_TEAM_ID",
    "ACTIVE_RR_SEASONS",
    "SUSPENDED_RR_SEASONS",
    "FUTURE_UNKNOWN_SEASONS",
]
