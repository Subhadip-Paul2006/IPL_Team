"""Unified Player Identity Resolution Engine (PIRE).

Part of Phase 2 Unified Database & PIRE (Track B).
Implements the 4-tier deterministic resolution hierarchy, source-scoped player tracking,
cross-provider registry linking (organizer + CricSheet people hashes), collision handling,
and human review queue dispatching in strict compliance with ADR-005 and TRD §11.
"""

from __future__ import annotations

import difflib
from collections import defaultdict
from typing import Any
from uuid import uuid4

from src.pire.alias_registry import AliasRegistry, clean_name
from src.pire.models import (
    IdentityStatus,
    ResolutionResult,
    ResolutionTier,
    SourceScopedPlayer,
)
from src.pire.review_queue import HumanReviewQueue


class UnifiedPIRE:
    """Authoritative Player Identity Resolution Engine."""

    def __init__(self) -> None:
        self.players: dict[str, SourceScopedPlayer] = {}
        # (provider, external_id) -> canonical_player_id
        self.external_id_index: dict[tuple[str, str], str] = {}
        self.alias_registry = AliasRegistry()
        self.review_queue = HumanReviewQueue()

    def register_player(
        self,
        canonical_player_id: str,
        canonical_name: str,
        source_id: str = "organizer_pack",
        source_player_id: str = "",
        external_hashes: dict[str, str] | None = None,
        teams: set[str] | None = None,
        competitions: set[str] | None = None,
        playing_role: str | None = None,
        batting_hand: str | None = None,
        bowling_style: str | None = None,
        birth_year: int | None = None,
    ) -> SourceScopedPlayer:
        """Register or update a source-scoped player profile."""
        pid = str(canonical_player_id).strip()
        cname = str(canonical_name).strip()
        spid = str(source_player_id).strip() or pid

        if pid in self.players:
            player = self.players[pid]
            if teams:
                player.teams.update(teams)
            if competitions:
                player.competitions.update(competitions)
            if external_hashes:
                player.external_hashes.update(external_hashes)
        else:
            player = SourceScopedPlayer(
                canonical_player_id=pid,
                canonical_name=cname,
                source_id=source_id,
                source_player_id=spid,
                external_hashes=external_hashes or {},
                teams=set(teams or []),
                competitions=set(competitions or []),
                playing_role=playing_role,
                batting_hand=batting_hand,
                bowling_style=bowling_style,
                birth_year=birth_year,
            )
            self.players[pid] = player

        # Register in external index
        self.external_id_index[(source_id, spid)] = pid
        if external_hashes:
            for prov, ext_id in external_hashes.items():
                self.external_id_index[(prov, ext_id)] = pid

        # Register in alias registry
        self.alias_registry.register_player(pid, cname, source_id=source_id)

        return player

    def link_external_hash(
        self,
        player_id: str,
        provider: str,
        external_hash: str,
    ) -> bool:
        """Link an external identity hash (e.g. CricSheet hex hash) to a canonical player."""
        pid = str(player_id).strip()
        ext_h = str(external_hash).strip()
        if pid not in self.players or not ext_h:
            return False

        # Collision check on external hash
        existing = self.external_id_index.get((provider, ext_h))
        if existing and existing != pid:
            self.review_queue.record_conflict(
                subject_name=self.players[pid].canonical_name,
                conflicting_ids=[pid, existing],
                conflicting_sources=[provider],
                conflict_type="CROSS_SOURCE_KEY_COLLISION",
                evidence={"hash": ext_h, "attempted_link_player_id": pid, "existing_player_id": existing},
            )
            return False

        self.players[pid].external_hashes[provider] = ext_h
        self.external_id_index[(provider, ext_h)] = pid
        return True

    def ingest_organizer_mappings(
        self,
        mappings: list[dict[str, str]],
        playing_eleven: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Ingest the verified 1,217-player organizer universe with name collisions."""
        # Step 1: Ingest player rows
        name_to_pids: dict[str, list[str]] = defaultdict(list)
        for m in mappings:
            pid = str(m.get("player_id", "")).strip()
            pname = str(m.get("player_name", "")).strip()
            team = str(m.get("team_name", "")).strip()
            comp = str(m.get("comp_name", "")).strip()
            if not pid:
                continue

            self.register_player(
                canonical_player_id=pid,
                canonical_name=pname or f"Player_{pid}",
                source_id="organizer_pack",
                source_player_id=pid,
                teams={team} if team else None,
                competitions={comp} if comp else None,
            )
            if pname and pid not in name_to_pids[pname]:
                name_to_pids[pname].append(pid)

        # Step 2: Flag and record name collisions
        collision_count = 0
        for name, pids in name_to_pids.items():
            if len(pids) > 1:
                collision_count += 1
                for pid in pids:
                    self.players[pid].is_name_collision = True
                    self.players[pid].collision_sibling_ids = [sib for sib in pids if sib != pid]
                self.review_queue.record_conflict(
                    subject_name=name,
                    conflicting_ids=pids,
                    conflicting_sources=["organizer_pack"],
                    conflict_type="NAME_COLLISION_AMBIGUITY",
                    evidence={"candidate_ids": pids},
                )

        # Step 3: Match appearances
        if playing_eleven:
            matches_by_player: dict[str, set[str]] = defaultdict(set)
            for row in playing_eleven:
                pid = str(row.get("player_id", "")).strip()
                mid = str(row.get("match_id", "")).strip()
                is_p = str(row.get("is_played", "")).strip().lower() in ("true", "1")
                if pid and is_p and mid:
                    matches_by_player[pid].add(mid)

            for pid, matches in matches_by_player.items():
                if pid in self.players:
                    self.players[pid].match_appearances = len(matches)

        return {
            "total_players_registered": len(self.players),
            "collision_names_count": collision_count,
            "collision_details": {
                name: pids for name, pids in name_to_pids.items() if len(pids) > 1
            },
        }

    def resolve(
        self,
        raw_name: str,
        source_id: str = "organizer_pack",
        external_id: str | None = None,
        context_teams: list[str] | None = None,
        context_comp: str | None = None,
    ) -> ResolutionResult:
        """Resolve a player inquiry using the 4-tier waterfall architecture."""
        clean_input = clean_name(raw_name)
        ctx_teams = {t.strip() for t in (context_teams or []) if t.strip()}

        # TIER 1: Canonical External Registry Key Lookup
        if external_id:
            ext_clean = str(external_id).strip()
            lookup_key = (source_id, ext_clean)
            if lookup_key in self.external_id_index:
                pid = self.external_id_index[lookup_key]
                player = self.players[pid]
                return ResolutionResult(
                    player_id=pid,
                    canonical_name=player.canonical_name,
                    status=IdentityStatus.RESOLVED,
                    tier=ResolutionTier.TIER_1_CANONICAL_EXTERNAL_KEY,
                    confidence=1.00,
                    matched_source=source_id,
                )

        # TIER 2: Verified Alias Exact Match
        candidates = self.alias_registry.lookup_name_candidates(raw_name)
        if len(candidates) == 1:
            pid = candidates[0]
            player = self.players[pid]
            # Verify it is not an ambiguous collision
            if not player.is_name_collision:
                return ResolutionResult(
                    player_id=pid,
                    canonical_name=player.canonical_name,
                    status=IdentityStatus.RESOLVED,
                    tier=ResolutionTier.TIER_2_VERIFIED_ALIAS_EXACT,
                    confidence=0.95,
                    matched_alias=raw_name,
                )

        # TIER 3: Contextual Intersection & Corroboration (for collisions or multi-candidates)
        if len(candidates) > 1 or (len(candidates) == 1 and self.players[candidates[0]].is_name_collision):
            qualifying_pids: list[str] = []
            for cand_id in candidates:
                cand_player = self.players[cand_id]
                team_match = bool(cand_player.teams & ctx_teams) if ctx_teams else None
                comp_match = (context_comp in cand_player.competitions) if context_comp else None

                # When both team and comp are specified, candidate must match team AND comp
                if team_match is not None and comp_match is not None:
                    if team_match and comp_match:
                        qualifying_pids.append(cand_id)
                elif team_match or comp_match:
                    qualifying_pids.append(cand_id)

            if len(qualifying_pids) == 1:
                pid = qualifying_pids[0]
                player = self.players[pid]
                return ResolutionResult(
                    player_id=pid,
                    canonical_name=player.canonical_name,
                    status=IdentityStatus.RESOLVED,
                    tier=ResolutionTier.TIER_3_CONTEXTUAL_INTERSECTION,
                    confidence=0.85,
                    matched_alias=raw_name,
                )
            elif len(qualifying_pids) > 1:
                # Multiple candidates match context - Ambiguity!
                self.review_queue.enqueue(
                    raw_name=raw_name,
                    source_id=source_id,
                    external_id=external_id,
                    context_teams=list(ctx_teams),
                    context_comp=context_comp,
                    candidate_ids=qualifying_pids,
                    trigger_reason=f"Name collision with {len(qualifying_pids)} context-matching candidates",
                )
                return ResolutionResult(
                    player_id=f"unresolved_collision_{uuid4()}",
                    canonical_name=raw_name,
                    status=IdentityStatus.UNRESOLVED,
                    tier=ResolutionTier.UNRESOLVED_DISPATCH,
                    confidence=0.0,
                    needs_review=True,
                    review_reason=f"Multiple qualifying candidates: {qualifying_pids}",
                    candidate_matches=[{"player_id": c, "name": self.players[c].canonical_name} for c in qualifying_pids],
                )

        # TIER 4: Fuzzy String Matching with Strict Context Corroboration
        if clean_input:
            matching_cands: list[tuple[str, float]] = []
            for pid, player in self.players.items():
                if player.is_name_collision:
                    continue
                sim = difflib.SequenceMatcher(None, clean_input, clean_name(player.canonical_name)).ratio()
                if sim >= 0.88:
                    cand_player = player
                    team_match = bool(cand_player.teams & ctx_teams) if ctx_teams else None
                    comp_match = (context_comp in cand_player.competitions) if context_comp else None

                    corroborated = False
                    if team_match is not None and comp_match is not None:
                        corroborated = team_match and comp_match
                    elif team_match is not None:
                        corroborated = team_match
                    elif comp_match is not None:
                        corroborated = comp_match

                    if corroborated:
                        matching_cands.append((pid, sim))

            matching_cands.sort(key=lambda x: x[1], reverse=True)
            if len(matching_cands) == 1:
                best_cand_id, best_sim = matching_cands[0]
                cand_player = self.players[best_cand_id]
                return ResolutionResult(
                    player_id=best_cand_id,
                    canonical_name=cand_player.canonical_name,
                    status=IdentityStatus.RESOLVED,
                    tier=ResolutionTier.TIER_4_FUZZY_CORROBORATED,
                    confidence=round(best_sim * 0.9, 2),
                    matched_alias=cand_player.canonical_name,
                )
            elif len(matching_cands) > 1:
                # Multiple fuzzy candidates corroborated -> Ambiguity! Enforce Anti-Merge Invariant!
                ambig_ids = [c[0] for c in matching_cands]
                self.review_queue.enqueue(
                    raw_name=raw_name,
                    source_id=source_id,
                    external_id=external_id,
                    context_teams=list(ctx_teams),
                    context_comp=context_comp,
                    candidate_ids=ambig_ids,
                    trigger_reason=f"Multiple fuzzy matches ({len(ambig_ids)}) meeting corroboration criteria",
                )
                return ResolutionResult(
                    player_id=f"unresolved_fuzzy_{uuid4()}",
                    canonical_name=raw_name,
                    status=IdentityStatus.UNRESOLVED,
                    tier=ResolutionTier.UNRESOLVED_DISPATCH,
                    confidence=0.0,
                    needs_review=True,
                    review_reason=f"Multiple corroborated fuzzy matches: {ambig_ids}",
                    candidate_matches=[{"player_id": c, "name": self.players[c].canonical_name} for c in ambig_ids],
                )

        # Fallback: UNRESOLVED DISPATCH to Review Queue
        self.review_queue.enqueue(
            raw_name=raw_name,
            source_id=source_id,
            external_id=external_id,
            context_teams=list(ctx_teams),
            context_comp=context_comp,
            candidate_ids=candidates,
            trigger_reason="No qualifying candidate found through automated tiers",
        )
        return ResolutionResult(
            player_id=f"provisional_{uuid4()}",
            canonical_name=raw_name,
            status=IdentityStatus.UNRESOLVED,
            tier=ResolutionTier.UNRESOLVED_DISPATCH,
            confidence=0.0,
            needs_review=True,
            review_reason="No qualifying candidate resolved; staged in review queue",
        )
