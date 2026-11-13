"""PIRE Player Identity Resolution Engine (Phase 1B & Phase 2 Unified).

Resolves player identities using stable player_id values, audits name collisions
(1,217 mapped IDs, 1,210 unique names, 7 collisions), prevents identity merging
solely on name similarity (Rule R15 / P6), and provides an auditable resolution table.
Integrates with the UnifiedPIRE 4-tier waterfall engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.pire.models import IdentityStatus
from src.pire.resolver import UnifiedPIRE


@dataclass
class PlayerIdentity:
    """Resolved player identity model with collision and provenance attributes."""

    player_id: str
    canonical_name: str
    teams: set[str] = field(default_factory=set)
    competitions: set[str] = field(default_factory=set)
    match_appearances: int = 0
    is_name_collision: bool = False
    collision_sibling_ids: list[str] = field(default_factory=list)
    resolution_status: str = "RESOLVED"  # RESOLVED, PROVISIONAL, REVIEW_REQUIRED
    external_hashes: dict[str, str] = field(default_factory=dict)


@dataclass
class IdentityResolutionReport:
    """Audit report for the player identity universe."""

    total_mappings_count: int = 0
    total_mapped_player_ids: int = 0
    total_unique_names: int = 0
    collision_names_count: int = 0
    collision_details: dict[str, list[str]] = field(default_factory=dict)
    unmapped_player_ids: list[str] = field(default_factory=list)
    active_player_ids_count: int = 0


class PlayerIdentityResolver:
    """Resolves and validates player identities against organizer mapping and matches."""

    def __init__(self) -> None:
        self.players: dict[str, PlayerIdentity] = {}
        self.name_to_ids: dict[str, list[str]] = {}
        self.collision_names: set[str] = set()
        self.unified_engine = UnifiedPIRE()

    def build_registry(
        self,
        mappings: list[dict[str, str]],
        playing_eleven: list[dict[str, str]] | None = None,
        deliveries: list[dict[str, str]] | None = None,
    ) -> IdentityResolutionReport:
        """Build player identity registry from mapping rows and match appearances."""
        self.players.clear()
        self.name_to_ids.clear()
        self.collision_names.clear()

        # Ingest into unified engine
        self.unified_engine.ingest_organizer_mappings(mappings, playing_eleven)

        # Phase 1: Ingest authoritative mappings
        for m in mappings:
            pid = str(m.get("player_id", "")).strip()
            pname = str(m.get("player_name", "")).strip()
            team = str(m.get("team_name", "")).strip()
            comp = str(m.get("comp_name", "")).strip()

            if not pid:
                continue

            if pid not in self.players:
                self.players[pid] = PlayerIdentity(
                    player_id=pid,
                    canonical_name=pname or f"Player_{pid}",
                )

            if team:
                self.players[pid].teams.add(team)
            if comp:
                self.players[pid].competitions.add(comp)

            if pname:
                if pname not in self.name_to_ids:
                    self.name_to_ids[pname] = []
                if pid not in self.name_to_ids[pname]:
                    self.name_to_ids[pname].append(pid)

        # Phase 2: Identify collisions (same name, multiple distinct player_ids)
        for name, pids in self.name_to_ids.items():
            if len(pids) > 1:
                self.collision_names.add(name)
                for pid in pids:
                    self.players[pid].is_name_collision = True
                    self.players[pid].collision_sibling_ids = [sib for sib in pids if sib != pid]

        # Phase 3: Corroborate match appearances from playing_eleven
        unmapped_ids: set[str] = set()
        p11_matches_by_player: dict[str, set[str]] = {}
        if playing_eleven:
            for row in playing_eleven:
                pid = str(row.get("player_id", "")).strip()
                mid = str(row.get("match_id", "")).strip()
                is_p = str(row.get("is_played", "")).strip().lower() in ("true", "1")
                if not pid or not is_p:
                    continue

                if pid not in self.players:
                    unmapped_ids.add(pid)
                    # Create provisional identity if delivery/match evidence exists
                    self.players[pid] = PlayerIdentity(
                        player_id=pid,
                        canonical_name=f"Unmapped_Player_{pid}",
                        resolution_status="PROVISIONAL",
                    )
                    self.unified_engine.register_player(
                        canonical_player_id=pid,
                        canonical_name=f"Unmapped_Player_{pid}",
                        source_id="organizer_match_evidence",
                    )
                    self.unified_engine.players[pid].identity_status = IdentityStatus.PROVISIONAL

                if pid not in p11_matches_by_player:
                    p11_matches_by_player[pid] = set()
                if mid:
                    p11_matches_by_player[pid].add(mid)

        for pid, matches in p11_matches_by_player.items():
            if pid in self.players:
                self.players[pid].match_appearances = len(matches)

        mapped_unique_pids = {m.get("player_id", "").strip() for m in mappings if m.get("player_id")}

        report = IdentityResolutionReport(
            total_mappings_count=len(mappings),
            total_mapped_player_ids=len(mapped_unique_pids),
            total_unique_names=len(self.name_to_ids),
            collision_names_count=len(self.collision_names),
            collision_details={
                name: self.name_to_ids[name]
                for name in sorted(self.collision_names)
            },
            unmapped_player_ids=sorted(unmapped_ids),
            active_player_ids_count=len([p for p in self.players.values() if p.match_appearances > 0]),
        )
        return report

    def get_canonical_name(self, player_id: str) -> str:
        """Retrieve the canonical player name, with collision disambiguation tag if needed."""
        player = self.players.get(str(player_id).strip())
        if not player:
            return f"Player_{player_id}"
        if player.is_name_collision:
            teams_str = "/".join(sorted(player.teams)[:2]) if player.teams else f"ID_{player_id}"
            return f"{player.canonical_name} ({teams_str})"
        return player.canonical_name

    def get_player(self, player_id: str) -> PlayerIdentity | None:
        """Retrieve full player identity object."""
        return self.players.get(str(player_id).strip())
