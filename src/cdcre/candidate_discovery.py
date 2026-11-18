"""Pre-Identity Candidate Discovery for CDCRE.

Part of Phase 04A — Career Discovery & Competition Research Engine (Milestone 2).
Resolves raw name query strings against canonical datasets (CricSheet people/names,
organizer competition mappings, and competitions) while strictly preventing
identity auto-merging and enforcing AC-10 (no player_id accepted or inspected).
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_DNS, UUID, uuid5

from src.contracts.cdcre import (
    AmbiguityStatus,
    CandidateDiscoveryResult,
    CandidatePlayerRecord,
)
from src.pire.alias_registry import AliasRegistry, clean_name

# Canonical namespace for deterministic UUIDv5 derivation matching ingestion parser
CRIC_NAMESPACE = uuid5(NAMESPACE_DNS, "cricsheet.org")


def derive_player_uuid(identifier: str) -> UUID:
    """Generate deterministic UUIDv5 for a player identity."""
    key = f"player:{str(identifier).strip().lower()}"
    return uuid5(CRIC_NAMESPACE, key)


class PreIdentityCandidateDiscovery:
    """Pre-identity candidate discovery engine consuming canonical and organizer datasets.

    Adheres strictly to AC-10 (accepts raw name only, never requires or accepts player_id),
    reuses PIRE AliasRegistry for normalization and alias mapping, and guarantees zero
    auto-merging of colliding player identities (R6 invariant).
    """

    def __init__(self, datasets_dir: Path | str | None = None) -> None:
        if datasets_dir is None:
            # Fall back from current working directory or relative to project root
            cwd_datasets = Path("datasets")
            if cwd_datasets.exists():
                self.datasets_dir = cwd_datasets
            else:
                self.datasets_dir = Path(__file__).resolve().parent.parent.parent / "datasets"
        else:
            self.datasets_dir = Path(datasets_dir)

        self.alias_registry = AliasRegistry()
        self._candidate_records: dict[str, CandidatePlayerRecord] = {}
        self._ingested: bool = False
        self._ingest_datasets()

    def _locate_file(self, rel_paths: list[str]) -> Path | None:
        """Find the first matching relative path within datasets_dir."""
        for rel in rel_paths:
            candidate = self.datasets_dir / rel
            if candidate.exists():
                return candidate
        return None

    def _ingest_datasets(self) -> None:
        """Ingest competition mappings, competitions, people.csv, and names.csv."""
        if self._ingested:
            return

        # 1. Locate dataset files
        mapping_path = self._locate_file([
            "6af3166e7b922_data_pack/competition_team_player_mapping.csv",
            "competition_team_player_mapping.csv",
        ])
        competitions_path = self._locate_file([
            "6af3166e7b922_data_pack/competitions.csv",
            "competitions.csv",
        ])
        people_path = self._locate_file(["people.csv"])
        names_path = self._locate_file(["names.csv"])

        # Ingest organizer competitions metadata if available
        comp_names: set[str] = set()
        if competitions_path and competitions_path.exists():
            with open(competitions_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cname = row.get("comp_name", "").strip()
                    if cname:
                        comp_names.add(cname)

        # Ingest organizer players and team mappings
        org_players: dict[str, dict[str, Any]] = {}
        org_name_to_pids: dict[str, set[str]] = defaultdict(set)
        if mapping_path and mapping_path.exists():
            with open(mapping_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pid = row.get("player_id", "").strip()
                    pname = row.get("player_name", "").strip()
                    team = row.get("team_name", "").strip()
                    comp = row.get("comp_name", "").strip()
                    if not pid or not pname:
                        continue

                    cn = clean_name(pname)
                    if pid not in org_players:
                        org_players[pid] = {
                            "player_id": pid,
                            "canonical_name": pname,
                            "teams": set(),
                            "competitions": set(),
                        }
                    if team:
                        org_players[pid]["teams"].add(team)
                    if comp:
                        org_players[pid]["competitions"].add(comp)
                    org_name_to_pids[cn].add(pid)

        # Ingest CricSheet people.csv
        cric_people: dict[str, dict[str, str]] = {}
        cric_name_to_idents: dict[str, set[str]] = defaultdict(set)
        if people_path and people_path.exists():
            with open(people_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ident = row.get("identifier", "").strip()
                    name = row.get("name", "").strip()
                    uname = row.get("unique_name", "").strip()
                    if not ident or not name:
                        continue
                    cric_people[ident] = {
                        "name": name,
                        "unique_name": uname,
                        "key_cricinfo": row.get("key_cricinfo", "").strip(),
                        "key_bcci": row.get("key_bcci", "").strip(),
                    }
                    cric_name_to_idents[clean_name(name)].add(ident)
                    if uname and uname != name:
                        cric_name_to_idents[clean_name(uname)].add(ident)

        # Ingest CricSheet names.csv (aliases)
        names_by_ident: dict[str, list[str]] = defaultdict(list)
        if names_path and names_path.exists():
            with open(names_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ident = row.get("identifier", "").strip()
                    alias = row.get("name", "").strip()
                    if not ident or not alias:
                        continue
                    names_by_ident[ident].append(alias)
                    cric_name_to_idents[clean_name(alias)].add(ident)

        # Build safe 1-to-1 links between organizer pack and CricSheet
        # (Only link when both organizer name and CricSheet name are unambiguous singles.
        # Collisions are never merged across sources.)
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

        # Register organizer players in AliasRegistry and build candidate records
        for pid, pdata in org_players.items():
            cand_key = f"organizer_{pid}"
            cname = pdata["canonical_name"]
            teams_list = sorted(pdata["teams"])
            comps_list = sorted(pdata["competitions"])
            derived_uuid = derive_player_uuid(f"organizer_{pid}")

            record = CandidatePlayerRecord(
                player_id=derived_uuid,
                canonical_name=cname,
                source_id=cand_key,
                teams=teams_list,
                competitions=comps_list,
                confidence=1.0,
            )
            self._candidate_records[cand_key] = record
            self.alias_registry.register_player(cand_key, cname, source_id="organizer_pack")

            # If safely linked to CricSheet, register aliases from CricSheet
            if pid in org_to_cric:
                cric_id = org_to_cric[pid]
                cdata = cric_people.get(cric_id)
                if cdata:
                    self.alias_registry.register_alias(
                        cand_key, cdata["name"], source_id="cricsheet_people"
                    )
                    if cdata["unique_name"]:
                        self.alias_registry.register_alias(
                            cand_key, cdata["unique_name"], source_id="cricsheet_people"
                        )
                for alias in names_by_ident.get(cric_id, []):
                    self.alias_registry.register_alias(
                        cand_key, alias, source_id="cricsheet_names"
                    )

        # Register CricSheet-only players (not linked and not colliding with organizer pack)
        for ident, cdata in cric_people.items():
            if ident in cric_to_org:
                continue

            cn = clean_name(cdata["name"])
            # Never overwrite or merge with organizer players
            if cn not in org_name_to_pids:
                cand_key = f"cricsheet_{ident}"
                derived_uuid = derive_player_uuid(ident)
                record = CandidatePlayerRecord(
                    player_id=derived_uuid,
                    canonical_name=cdata["name"],
                    source_id=cand_key,
                    teams=[],
                    competitions=[],
                    confidence=1.0,
                )
                self._candidate_records[cand_key] = record
                self.alias_registry.register_player(
                    cand_key, cdata["name"], source_id="cricsheet_people"
                )

                if cdata["unique_name"] and clean_name(cdata["unique_name"]) not in org_name_to_pids:
                    self.alias_registry.register_alias(
                        cand_key, cdata["unique_name"], source_id="cricsheet_people"
                    )

                for alias in names_by_ident.get(ident, []):
                    if clean_name(alias) not in org_name_to_pids:
                        self.alias_registry.register_alias(
                            cand_key, alias, source_id="cricsheet_names"
                        )

        self._ingested = True

    def discover(self, raw_name: str) -> CandidateDiscoveryResult:
        """Discover player candidates from raw name query."""
        if not isinstance(raw_name, str):
            raise TypeError(f"discover_candidates expects a string, got {type(raw_name).__name__}")

        if not raw_name.strip():
            return CandidateDiscoveryResult(
                raw_name_query=raw_name,
                ambiguity_status=AmbiguityStatus.NONE,
                candidates=[],
                collision_detected=False,
            )

        cleaned = clean_name(raw_name)
        if not cleaned:
            return CandidateDiscoveryResult(
                raw_name_query=raw_name,
                ambiguity_status=AmbiguityStatus.NONE,
                candidates=[],
                collision_detected=False,
            )

        cand_keys = self.alias_registry.lookup_name_candidates(raw_name)
        if not cand_keys:
            return CandidateDiscoveryResult(
                raw_name_query=raw_name,
                ambiguity_status=AmbiguityStatus.NONE,
                candidates=[],
                collision_detected=False,
            )

        # Collect CandidatePlayerRecord objects in deterministic order
        candidates = [
            self._candidate_records[k]
            for k in sorted(cand_keys)
            if k in self._candidate_records
        ]

        if not candidates:
            return CandidateDiscoveryResult(
                raw_name_query=raw_name,
                ambiguity_status=AmbiguityStatus.NONE,
                candidates=[],
                collision_detected=False,
            )

        if len(candidates) == 1:
            return CandidateDiscoveryResult(
                raw_name_query=raw_name,
                ambiguity_status=AmbiguityStatus.SINGLE_CORROBORATED,
                candidates=candidates,
                collision_detected=False,
            )

        # len(candidates) > 1 -> Name collision detected (R6 anti-merge invariant)
        return CandidateDiscoveryResult(
            raw_name_query=raw_name,
            ambiguity_status=AmbiguityStatus.MULTIPLE,
            candidates=candidates,
            collision_detected=True,
        )


# Global default engine instance for fast in-memory candidate lookups
_default_engine: PreIdentityCandidateDiscovery | None = None


def get_candidate_discovery_engine(
    datasets_dir: Path | str | None = None,
) -> PreIdentityCandidateDiscovery:
    """Retrieve or initialize the candidate discovery engine."""
    global _default_engine
    if datasets_dir is not None:
        return PreIdentityCandidateDiscovery(datasets_dir=datasets_dir)
    if _default_engine is None:
        _default_engine = PreIdentityCandidateDiscovery()
    return _default_engine


def discover_candidates(raw_name: str) -> CandidateDiscoveryResult:
    """Accepts raw name string only. Never requires or accepts player_id (AC-10).

    Resolves collisions emitting AmbiguityStatus.MULTIPLE without auto-merging (R6 invariant).

    Args:
        raw_name: Raw player name query string.

    Returns:
        CandidateDiscoveryResult containing discovered candidate records and ambiguity status.

    Raises:
        TypeError: If raw_name is not a string or if unexpected keyword arguments are passed.
    """
    if not isinstance(raw_name, str):
        raise TypeError(f"discover_candidates expects raw_name as str, got {type(raw_name).__name__}")
    engine = get_candidate_discovery_engine()
    return engine.discover(raw_name)


# Alias CandidateDiscoveryEngine to PreIdentityCandidateDiscovery
CandidateDiscoveryEngine = PreIdentityCandidateDiscovery

__all__ = [
    "CandidateDiscoveryEngine",
    "PreIdentityCandidateDiscovery",
    "derive_player_uuid",
    "discover_candidates",
    "get_candidate_discovery_engine",
]
