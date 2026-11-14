"""Competition Registry and Tournament Ingestion for CDCRE.

Part of Phase 04A — Career Discovery & Competition Research Engine (Milestone 3).
Ingests and indexes 13 CricSheet tournament directories (5,083 matches) and 141
organizer competitions, mapping player identities to canonical UUIDs and normalizing
competition names, season years, and format tags (including The Hundred 5-ball semantics).
"""

from __future__ import annotations

import csv
import json
import pickle
import tempfile
from pathlib import Path
from typing import Any
from uuid import UUID, uuid5

from src.cdcre.candidate_discovery import CRIC_NAMESPACE, derive_player_uuid
from src.contracts.cdcre import CompetitionHistoryRecord, CoverageStatus
from src.pire.alias_registry import clean_name

# Authoritative deterministic competition UUID constants matching contract fixtures
IPL_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000001")
SMAT_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000002")
HUNDRED_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000003")
BBL_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000004")
BPL_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000005")

KNOWN_COMPETITION_UUIDS: dict[str, UUID] = {
    "Indian Premier League": IPL_COMPETITION_UUID,
    "Syed Mushtaq Ali Trophy": SMAT_COMPETITION_UUID,
    "The Hundred Men's Competition": HUNDRED_COMPETITION_UUID,
    "Big Bash League": BBL_COMPETITION_UUID,
    "Bangladesh Premier League": BPL_COMPETITION_UUID,
}

# The 13 CricSheet tournament directories
CRICSHEET_TOURNAMENT_SPECS: dict[str, dict[str, Any]] = {
    "bbl_male_json": {
        "canonical_name": "Big Bash League",
        "format_tag": "T20",
        "balls_per_over": 6,
    },
    "bpl_male_json": {
        "canonical_name": "Bangladesh Premier League",
        "format_tag": "T20",
        "balls_per_over": 6,
    },
    "cpl_male_json": {
        "canonical_name": "Caribbean Premier League",
        "format_tag": "T20",
        "balls_per_over": 6,
    },
    "hnd_male_json": {
        "canonical_name": "The Hundred Men's Competition",
        "format_tag": "100-ball",
        "balls_per_over": 5,
    },
    "icc_mens_cricket_world_cup_male_json": {
        "canonical_name": "ICC Cricket World Cup",
        "format_tag": "ODI",
        "balls_per_over": 6,
    },
    "icc_mens_t20_world_cup_male_json": {
        "canonical_name": "ICC Men's T20 World Cup",
        "format_tag": "T20I",
        "balls_per_over": 6,
    },
    "ilt_male_json": {
        "canonical_name": "International League T20",
        "format_tag": "T20",
        "balls_per_over": 6,
    },
    "ipl_male_json": {
        "canonical_name": "Indian Premier League",
        "format_tag": "T20",
        "balls_per_over": 6,
    },
    "lpl_male_json": {
        "canonical_name": "Lanka Premier League",
        "format_tag": "T20",
        "balls_per_over": 6,
    },
    "mlc_male_json": {
        "canonical_name": "Major League Cricket",
        "format_tag": "T20",
        "balls_per_over": 6,
    },
    "psl_male_json": {
        "canonical_name": "Pakistan Super League",
        "format_tag": "T20",
        "balls_per_over": 6,
    },
    "sat_male_json": {
        "canonical_name": "SA20",
        "format_tag": "T20",
        "balls_per_over": 6,
    },
    "sma_json": {
        "canonical_name": "Syed Mushtaq Ali Trophy",
        "format_tag": "T20",
        "balls_per_over": 6,
    },
}


def derive_competition_uuid(name: str) -> UUID:
    """Generate deterministic UUIDv5 for a competition by canonical name."""
    clean = name.strip()
    if clean in KNOWN_COMPETITION_UUIDS:
        return KNOWN_COMPETITION_UUIDS[clean]
    key = f"competition:{clean.lower()}"
    return uuid5(CRIC_NAMESPACE, key)


def derive_provenance_uuid(source_tag: str) -> UUID:
    """Generate deterministic UUIDv5 for provenance tracking."""
    key = f"provenance:{source_tag.strip().lower()}"
    return uuid5(CRIC_NAMESPACE, key)


def normalize_competition_name(raw_name: str) -> str:
    """Normalize raw competition strings into canonical names."""
    if not raw_name:
        return "Unknown Competition"
    trimmed = raw_name.strip()

    # Normalize IPL organizer iterations
    if trimmed.startswith("IPL ") and len(trimmed) >= 8 and trimmed[4:8].isdigit():
        return "Indian Premier League"
    if trimmed == "Indian Premier League":
        return "Indian Premier League"

    # Normalize ICC World Cups
    if trimmed in ("World T20", "ICC Men's T20 World Cup"):
        return "ICC Men's T20 World Cup"
    if trimmed in ("World Cup", "ICC World Cup", "ICC Cricket World Cup"):
        return "ICC Cricket World Cup"

    # Normalize The Hundred
    if "The Hundred" in trimmed or trimmed == "The Hundred Men's Competition":
        return "The Hundred Men's Competition"

    # Normalize CricSheet leagues
    if "Syed Mushtaq Ali" in trimmed:
        return "Syed Mushtaq Ali Trophy"
    if "Big Bash" in trimmed:
        return "Big Bash League"
    if "Bangladesh Premier League" in trimmed:
        return "Bangladesh Premier League"
    if "Caribbean Premier League" in trimmed:
        return "Caribbean Premier League"
    if "Pakistan Super League" in trimmed:
        return "Pakistan Super League"
    if trimmed in ("SA20", "SA20 League"):
        return "SA20"
    if "International League T20" in trimmed:
        return "International League T20"
    if "Lanka Premier League" in trimmed:
        return "Lanka Premier League"
    if "Major League Cricket" in trimmed:
        return "Major League Cricket"

    return trimmed


def normalize_season_year(raw_season: Any) -> str:
    """Normalize season representation (e.g., '2024', '2023/24')."""
    if raw_season is None:
        return "Unknown"
    season_str = str(raw_season).strip()
    # Normalize four-digit slash four-digit (e.g. 2023/2024 -> 2023/24)
    if "/" in season_str:
        parts = season_str.split("/")
        if len(parts) == 2 and len(parts[0]) == 4 and len(parts[1]) == 4:
            return f"{parts[0]}/{parts[1][2:]}"
    return season_str


def normalize_format_tag(comp_name: str, raw_format: str | None = None, balls_per_over: int = 6) -> str:
    """Normalize format tag (T20, T20I, ODI, 100-ball)."""
    if balls_per_over == 5 or "The Hundred" in comp_name or "Hundred" in comp_name:
        return "100-ball"

    fmt = (raw_format or "").strip().upper()
    if fmt == "ODI" or ("World Cup" in comp_name and "T20" not in comp_name):
        return "ODI"
    if fmt == "T20I" or "T20I" in comp_name or "ICC Men's T20 World Cup" in comp_name:
        return "T20I"
    return "T20"


class CompetitionRegistry:
    """Registry indexing 13 CricSheet tournament directories and 141 organizer competitions.

    Maintains inverted index mapping canonical player UUIDs to verified match appearances
    across competition seasons while enforcing R6 anti-merging and The Hundred 5-ball semantics.
    """

    def __init__(
        self,
        datasets_dir: Path | str | None = None,
        enable_cache: bool = True,
    ) -> None:
        if datasets_dir is None:
            cwd_datasets = Path("datasets")
            if cwd_datasets.exists():
                self.datasets_dir = cwd_datasets
            else:
                self.datasets_dir = Path(__file__).resolve().parent.parent.parent / "datasets"
        else:
            self.datasets_dir = Path(datasets_dir)

        self.enable_cache = enable_cache
        # Maps canonical player UUID -> list of CompetitionHistoryRecord
        self._player_careers: dict[UUID, list[CompetitionHistoryRecord]] = {}
        # In-memory index of loaded competitions
        self._registered_competitions: set[str] = set()
        self._indexed: bool = False
        self._build_or_load_index()

    def _locate_file(self, rel_paths: list[str]) -> Path | None:
        """Find the first matching relative path within datasets_dir."""
        for rel in rel_paths:
            candidate = self.datasets_dir / rel
            if candidate.exists():
                return candidate
        return None

    def _get_cache_path(self) -> Path:
        """Get the path for the persistent index cache file."""
        cache_dir = Path(tempfile.gettempdir())
        return cache_dir / "cdcre_career_registry_index_v1.pkl"

    def _build_or_load_index(self) -> None:
        """Load from cache or build fresh inverted index."""
        if self._indexed:
            return

        cache_path = self._get_cache_path()
        # Only use disk cache if datasets_dir is the standard datasets directory
        is_standard_dir = (
            self.datasets_dir.name == "datasets"
            and (self.datasets_dir / "people.csv").exists()
            and (self.datasets_dir / "ipl_male_json").exists()
        )

        if self.enable_cache and is_standard_dir and cache_path.exists():
            try:
                with open(cache_path, "rb") as f:
                    cached_data = pickle.load(f)
                    self._player_careers = cached_data["player_careers"]
                    self._registered_competitions = cached_data["registered_competitions"]
                    self._indexed = True
                    return
            except Exception:
                # If cache corrupted or incompatible, fall through to re-indexing
                pass

        self._build_index()

        # Cache on disk if standard dataset
        if self.enable_cache and is_standard_dir:
            try:
                with open(cache_path, "wb") as f:
                    pickle.dump(
                        {
                            "player_careers": self._player_careers,
                            "registered_competitions": self._registered_competitions,
                        },
                        f,
                    )
            except Exception:
                pass

    def _build_index(self) -> None:
        """Build genuine in-memory inverted index across all canonical datasets."""
        # 1. Ingest identity mappings (people.csv, names.csv, organizer mappings)
        people_path = self._locate_file(["people.csv"])
        names_path = self._locate_file(["names.csv"])
        mapping_path = self._locate_file([
            "6af3166e7b922_data_pack/competition_team_player_mapping.csv",
            "competition_team_player_mapping.csv",
        ])
        competitions_path = self._locate_file([
            "6af3166e7b922_data_pack/competitions.csv",
            "competitions.csv",
        ])
        matches_path = self._locate_file([
            "6af3166e7b922_data_pack/matches.csv",
            "matches.csv",
        ])
        playing_eleven_path = self._locate_file([
            "6af3166e7b922_data_pack/playing_eleven.csv",
            "playing_eleven.csv",
        ])

        # Map clean_name -> set of CricSheet identifiers
        cric_name_to_idents: dict[str, set[str]] = {}
        if people_path and people_path.exists():
            with open(people_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ident = row.get("identifier", "").strip()
                    name = row.get("name", "").strip()
                    uname = row.get("unique_name", "").strip()
                    if not ident or not name:
                        continue
                    cn = clean_name(name)
                    cric_name_to_idents.setdefault(cn, set()).add(ident)
                    if uname and uname != name:
                        cric_name_to_idents.setdefault(clean_name(uname), set()).add(ident)

        if names_path and names_path.exists():
            with open(names_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ident = row.get("identifier", "").strip()
                    alias = row.get("name", "").strip()
                    if not ident or not alias:
                        continue
                    cric_name_to_idents.setdefault(clean_name(alias), set()).add(ident)

        # Map clean_name -> set of organizer player_ids
        org_name_to_pids: dict[str, set[str]] = {}
        if mapping_path and mapping_path.exists():
            with open(mapping_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pid = row.get("player_id", "").strip()
                    pname = row.get("player_name", "").strip()
                    if not pid or not pname:
                        continue
                    cn = clean_name(pname)
                    org_name_to_pids.setdefault(cn, set()).add(pid)

        # Safe 1-to-1 linkage (anti-merging guardrail for collisions)
        org_to_cric: dict[str, str] = {}
        cric_to_org: dict[str, str] = {}
        for cn, pids in org_name_to_pids.items():
            if len(pids) == 1:
                pid = next(iter(pids))
                idents = cric_name_to_idents.get(cn, set())
                if len(idents) == 1:
                    ident = next(iter(idents))
                    org_to_cric[pid] = ident
                    cric_to_org[ident] = pid

        # 2. Ingest 13 CricSheet tournament directories (5,083 matches)
        # cric_player_appearances: ident -> dict[(comp_name, season_year), dict]
        cric_appearances: dict[str, dict[tuple[str, str], dict[str, Any]]] = {}

        for dir_name, spec in CRICSHEET_TOURNAMENT_SPECS.items():
            tourney_dir = self.datasets_dir / dir_name
            if not tourney_dir.exists():
                continue

            self._registered_competitions.add(spec["canonical_name"])

            for json_path in tourney_dir.glob("*.json"):
                try:
                    with open(json_path, encoding="utf-8") as jf:
                        match_data = json.load(jf)
                except Exception:
                    continue

                info = match_data.get("info", {})
                raw_event_name = info.get("event", {}).get("name", "")
                comp_name = normalize_competition_name(raw_event_name) or spec["canonical_name"]
                self._registered_competitions.add(comp_name)

                season = normalize_season_year(info.get("season"))
                balls_per_over = info.get("balls_per_over", spec["balls_per_over"])
                raw_type = info.get("match_type", spec["format_tag"])
                format_tag = normalize_format_tag(comp_name, raw_type, balls_per_over)

                registry_people = info.get("registry", {}).get("people", {})
                players_dict = info.get("players", {})

                # Exact match players (excluding match officials and referees)
                match_idents: set[str] = set()
                for team_players in players_dict.values():
                    for pname in team_players:
                        ident = registry_people.get(pname)
                        if ident:
                            match_idents.add(ident)

                key = (comp_name, season)
                for ident in match_idents:
                    player_seasons = cric_appearances.setdefault(ident, {})
                    if key not in player_seasons:
                        player_seasons[key] = {
                            "competition_name": comp_name,
                            "season_year": season,
                            "format_tag": format_tag,
                            "balls_per_over": balls_per_over,
                            "appearances": 0,
                        }
                    player_seasons[key]["appearances"] += 1

        # 3. Ingest Organizer competitions & appearances
        # org_appearances: pid -> dict[(comp_name, season_year), dict]
        org_appearances: dict[str, dict[tuple[str, str], dict[str, Any]]] = {}

        org_comps: dict[str, dict[str, str]] = {}
        if competitions_path and competitions_path.exists():
            with open(competitions_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cid = row.get("comp_id", "").strip()
                    cname = row.get("comp_name", "").strip()
                    mformat = row.get("match_format", "").strip()
                    season = normalize_season_year(row.get("season", "").strip())
                    if cid and cname:
                        org_comps[cid] = {
                            "comp_name": cname,
                            "match_format": mformat,
                            "season": season,
                        }
                        norm_cname = normalize_competition_name(cname)
                        self._registered_competitions.add(norm_cname)

        match_to_comp: dict[str, str] = {}
        if matches_path and matches_path.exists():
            with open(matches_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    mid = row.get("match_id", "").strip()
                    cid = row.get("comp_id", "").strip()
                    if mid and cid:
                        match_to_comp[mid] = cid

        if playing_eleven_path and playing_eleven_path.exists():
            with open(playing_eleven_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    is_played = row.get("is_played", "").strip().lower()
                    if is_played != "true":
                        continue

                    pid = row.get("player_id", "").strip()
                    mid = row.get("match_id", "").strip()
                    if not pid or not mid:
                        continue

                    cid = match_to_comp.get(mid)
                    if not cid or cid not in org_comps:
                        continue

                    cinfo = org_comps[cid]
                    raw_cname = cinfo["comp_name"]
                    comp_name = normalize_competition_name(raw_cname)
                    season = cinfo["season"]
                    balls_per_over = 5 if ("The Hundred" in comp_name or "Hundred" in comp_name) else 6
                    format_tag = normalize_format_tag(comp_name, cinfo["match_format"], balls_per_over)

                    key = (comp_name, season)
                    p_seasons = org_appearances.setdefault(pid, {})
                    if key not in p_seasons:
                        p_seasons[key] = {
                            "competition_name": comp_name,
                            "season_year": season,
                            "format_tag": format_tag,
                            "balls_per_over": balls_per_over,
                            "appearances": 0,
                        }
                    p_seasons[key]["appearances"] += 1

        # 4. Synthesize unified career records per player identity
        # Gather all distinct player entities (both linked and unlinked)
        all_pids = set(org_appearances.keys()) | set(org_to_cric.keys())
        all_idents = set(cric_appearances.keys()) | set(cric_to_org.keys())

        # Build records for organizer players
        for pid in all_pids:
            linked_ident = org_to_cric.get(pid)
            combined_seasons: dict[tuple[str, str], dict[str, Any]] = {}

            # Add organizer seasons
            for key, data in org_appearances.get(pid, {}).items():
                combined_seasons[key] = dict(data)

            # Integrate CricSheet seasons if linked
            if linked_ident and linked_ident in cric_appearances:
                for key, data in cric_appearances[linked_ident].items():
                    if key in combined_seasons:
                        # Deduplicate overlapping seasons taking max verified match appearances
                        combined_seasons[key]["appearances"] = max(
                            combined_seasons[key]["appearances"], data["appearances"]
                        )
                    else:
                        combined_seasons[key] = dict(data)

            history_records = self._create_history_records(combined_seasons)

            # Map all canonical UUID variations for this organizer player
            uuid_variants = [
                derive_player_uuid(f"organizer_{pid}"),
                derive_player_uuid(pid),
            ]
            if linked_ident:
                uuid_variants.append(derive_player_uuid(linked_ident))
                uuid_variants.append(derive_player_uuid(f"cricsheet_{linked_ident}"))

            for u in uuid_variants:
                self._player_careers[u] = history_records

        # Build records for CricSheet-only players (not linked to an organizer player)
        for ident in all_idents:
            if ident in cric_to_org:
                continue

            seasons = cric_appearances.get(ident, {})
            history_records = self._create_history_records(seasons)

            uuid_variants = [
                derive_player_uuid(ident),
                derive_player_uuid(f"cricsheet_{ident}"),
            ]
            for u in uuid_variants:
                self._player_careers[u] = history_records

        self._indexed = True

    def _create_history_records(
        self,
        seasons_dict: dict[tuple[str, str], dict[str, Any]],
    ) -> list[CompetitionHistoryRecord]:
        """Convert aggregated season stats into CompetitionHistoryRecord models."""
        records: list[CompetitionHistoryRecord] = []
        for (comp_name, season_year), data in seasons_dict.items():
            appearances = data.get("appearances", 0)
            if appearances <= 0:
                continue

            comp_id = derive_competition_uuid(comp_name)
            format_tag = data.get("format_tag", "T20")
            balls_per_over = data.get("balls_per_over", 6)
            prov_id = derive_provenance_uuid(f"{comp_name}:{season_year}")

            records.append(
                CompetitionHistoryRecord(
                    competition_id=comp_id,
                    competition_name=comp_name,
                    season_year=season_year,
                    format_tag=format_tag,
                    appearances=appearances,
                    coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
                    balls_per_over=balls_per_over,
                    provenance_record_id=prov_id,
                )
            )

        # Sort deterministically
        records.sort(key=lambda r: (r.competition_name, r.season_year))
        return records

    def get_career_history(self, player_id: UUID) -> list[CompetitionHistoryRecord]:
        """Retrieve verified competition history records for a canonical player UUID."""
        if not isinstance(player_id, UUID):
            raise TypeError(
                f"get_career_history expects player_id as a UUID instance, got {type(player_id).__name__}"
            )
        return list(self._player_careers.get(player_id, []))

    def register_competition_history(
        self,
        player_id: UUID,
        records: list[CompetitionHistoryRecord],
    ) -> None:
        """Register custom or synthetic competition history records (for fixtures/tests)."""
        if not isinstance(player_id, UUID):
            raise TypeError(f"player_id must be a UUID, got {type(player_id).__name__}")
        self._player_careers[player_id] = list(records)

    def get_competition_count(self) -> int:
        """Return the count of registered competitions indexed."""
        return len(self._registered_competitions)

    def get_indexed_tournaments(self) -> list[str]:
        """Return sorted list of canonical competition names."""
        return sorted(self._registered_competitions)

    def has_player(self, player_id: UUID) -> bool:
        """Check if registry has records for the given canonical UUID."""
        return player_id in self._player_careers


# Global singleton registry instance
_default_registry: CompetitionRegistry | None = None


def get_competition_registry(
    datasets_dir: Path | str | None = None,
    enable_cache: bool = True,
) -> CompetitionRegistry:
    """Retrieve or initialize the default competition registry singleton."""
    global _default_registry
    if datasets_dir is not None:
        return CompetitionRegistry(datasets_dir=datasets_dir, enable_cache=enable_cache)
    if _default_registry is None:
        _default_registry = CompetitionRegistry(enable_cache=enable_cache)
    return _default_registry


__all__ = [
    "BBL_COMPETITION_UUID",
    "BPL_COMPETITION_UUID",
    "CRICSHEET_TOURNAMENT_SPECS",
    "CompetitionRegistry",
    "HUNDRED_COMPETITION_UUID",
    "IPL_COMPETITION_UUID",
    "KNOWN_COMPETITION_UUIDS",
    "SMAT_COMPETITION_UUID",
    "derive_competition_uuid",
    "derive_provenance_uuid",
    "get_competition_registry",
    "normalize_competition_name",
    "normalize_format_tag",
    "normalize_season_year",
]
