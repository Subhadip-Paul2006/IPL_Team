"""Source-scoped alias registry and string normalization for PIRE.

Part of Phase 2 Unified Database & PIRE (Track B).
Manages multi-source name aliases, deterministic case-folding, whitespace normalization,
and reverse lookup indexes while strictly preventing name collision merges.
"""

from __future__ import annotations

import re
from collections import defaultdict


def clean_name(name_str: str) -> str:
    """Normalize raw name: lowercase, strip punctuation noise, collapse spaces."""
    if not name_str:
        return ""
    # Replace dots, commas, hyphens, quotes, and parentheses with spaces
    s = re.sub(r"[.,\-()']", " ", name_str)
    # Collapse multiple whitespaces and trim
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


class AliasRegistry:
    """Multi-source player alias registry with provenance tracking."""

    def __init__(self) -> None:
        # (clean_name, source_id) -> canonical_player_id
        self._source_aliases: dict[tuple[str, str], str] = {}
        # clean_name -> set of candidate player_ids
        self._name_to_player_ids: dict[str, set[str]] = defaultdict(set)
        # player_id -> set of registered alias strings
        self._player_to_aliases: dict[str, set[str]] = defaultdict(set)
        # player_id -> canonical name
        self._player_canonical_names: dict[str, str] = {}
        # Known name collisions (names pointing to > 1 distinct player_id)
        self._collision_names: set[str] = set()

    def register_player(self, player_id: str, canonical_name: str, source_id: str = "organizer_pack") -> None:
        """Register canonical player profile."""
        pid = str(player_id).strip()
        cname = str(canonical_name).strip()
        self._player_canonical_names[pid] = cname
        self.register_alias(pid, cname, source_id=source_id)

    def register_alias(self, player_id: str, alias: str, source_id: str = "organizer_pack") -> None:
        """Register an alias for a player under a given source."""
        pid = str(player_id).strip()
        raw_alias = str(alias).strip()
        cleaned = clean_name(raw_alias)
        if not pid or not cleaned:
            return

        self._source_aliases[(cleaned, source_id)] = pid
        self._player_to_aliases[pid].add(raw_alias)
        self._name_to_player_ids[cleaned].add(pid)

        if len(self._name_to_player_ids[cleaned]) > 1:
            self._collision_names.add(cleaned)

    def lookup_exact_scoped(self, name: str, source_id: str) -> str | None:
        """Lookup by exact name and source_id."""
        cleaned = clean_name(name)
        return self._source_aliases.get((cleaned, source_id))

    def lookup_name_candidates(self, name: str) -> list[str]:
        """Lookup all player IDs sharing this name across all sources."""
        cleaned = clean_name(name)
        return sorted(self._name_to_player_ids.get(cleaned, set()))

    def is_collision(self, name: str) -> bool:
        """Check if name is an ambiguous collision shared by multiple players."""
        cleaned = clean_name(name)
        return cleaned in self._collision_names

    def get_canonical_name(self, player_id: str) -> str | None:
        """Retrieve registered canonical name."""
        return self._player_canonical_names.get(str(player_id).strip())

    def get_aliases_for_player(self, player_id: str) -> set[str]:
        """Retrieve all aliases registered for a player."""
        return self._player_to_aliases.get(str(player_id).strip(), set())

    def get_collision_names(self) -> set[str]:
        """Retrieve all detected collision name strings."""
        return set(self._collision_names)
