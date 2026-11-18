"""User Custom Squad Composition and Roster Lifecycle Management (Service E).

Part of Phase 06 — SICE (Milestone 2: Service E & Persistence Engine).
Governs:
- User team lifecycle: create, get, update, delete, list.
- Squad player roster: add player, update player, remove player, role assignment, batting order.
- IPL tournament and squad balance governance (HD-05, HD-08, HD-09):
    * Squad capacity: 18–25 players
    * Overseas quota: max 8 overseas, min 10 domestic
    * Designated wicketkeepers: target 2–3 (shortage < 2, waste > 3)
    * Captain assignment: single designated captain
    * Batting order validity: positions 1–11 with no slot collision
    * Draft tolerance: progressive evaluation for N in [1, 25]
    * Official certification: strict validation requiring resolved identities.
- Thread-safe concurrency synchronization via RLock.
- ServiceBoundary lifecycle and health check compliance.
"""

from __future__ import annotations

import logging
import re
import threading
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from src.contracts.sice import RosterStatus
from src.contracts.team_builder import UserTeam, UserTeamPlayer
from src.services.base import ServiceBoundary
from src.sice.exceptions import (
    IncompleteRosterError,
    SquadConstraintViolationError,
)
from src.sice.repository import RepositoryMode, SICERepository

logger = logging.getLogger(__name__)


def _is_overseas_player(
    player: UserTeamPlayer,
    metadata: dict[UUID, dict[str, Any]] | None = None,
) -> bool:
    """Determine whether a player is classified as overseas based on metadata."""
    if metadata and player.player_id in metadata:
        meta = metadata[player.player_id]
        if "is_overseas" in meta:
            return bool(meta["is_overseas"])
        nationality = meta.get("nationality") or meta.get("country")
        if nationality is not None:
            return str(nationality).strip().lower() not in {"india", "ind", "indian"}
    return False


def _is_wicketkeeper_player(
    player: UserTeamPlayer,
    metadata: dict[UUID, dict[str, Any]] | None = None,
) -> bool:
    """Determine whether a player is a designated wicketkeeper."""
    if player.is_designated_wk:
        return True
    if player.assigned_role:
        role_cleaned = re.sub(r"[\s\-_]+", "", player.assigned_role.lower())
        if (
            "wicketkeeper" in role_cleaned
            or role_cleaned in {"wk", "keeper"}
            or "wk" in role_cleaned
        ):
            return True
    if metadata and player.player_id in metadata:
        meta = metadata[player.player_id]
        if meta.get("is_designated_wk") or meta.get("is_wicketkeeper"):
            return True
        role_str = str(meta.get("role") or meta.get("primary_role") or "").strip().lower()
        role_cleaned = re.sub(r"[\s\-_]+", "", role_str)
        if (
            "wicketkeeper" in role_cleaned
            or role_cleaned in {"wk", "keeper"}
            or "wk" in role_cleaned
        ):
            return True
    return False


class TeamBuilderService(ServiceBoundary):
    """Service E: User custom squad composition and roster lifecycle management.

    Governs team creation, member assignment, role designations, batting order,
    and IPL tournament regulation compliance (HD-05, HD-08, HD-09).
    Inherits from ServiceBoundary establishing identity and lifecycle contracts.
    """

    def __init__(self, repository: SICERepository | None = None) -> None:
        """Initialize TeamBuilderService with injected or default in-memory repository."""
        self.repository = (
            repository if repository is not None else SICERepository(mode=RepositoryMode.IN_MEMORY)
        )
        self._lock = threading.RLock()

    # -------------------------------------------------------------------------
    # ServiceBoundary Interface
    # -------------------------------------------------------------------------

    def get_service_name(self) -> str:
        """Return canonical service identifier for TeamBuilderService (Service E)."""
        return "team_builder_service"

    def health_check(self) -> dict[str, Any]:
        """Perform service health inspection and return diagnostic status dictionary."""
        with self._lock:
            return {
                "service": self.get_service_name(),
                "status": "operational",
                "repository_mode": self.repository.mode.value,
                "teams_count": self.repository.count("teams"),
                "players_count": self.repository.count("team_players"),
            }

    # -------------------------------------------------------------------------
    # Team Lifecycle Operations
    # -------------------------------------------------------------------------

    def create_team(
        self,
        team_name: str,
        target_season: str | None = "IPL 2027",
        created_by: str | None = None,
        notes: str | None = None,
        team_id: UUID | None = None,
    ) -> UserTeam:
        """Create a new user custom squad header and persist to repository."""
        if not isinstance(team_name, str) or not team_name.strip():
            raise ValueError("team_name must be a non-empty string")

        with self._lock:
            team = UserTeam(
                team_id=team_id or uuid4(),
                team_name=team_name.strip(),
                target_season=target_season,
                created_by=created_by,
                notes=notes,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            return self.repository.save_team(team)

    def get_team(self, team_id: UUID | str) -> UserTeam | None:
        """Retrieve a user team by its primary identifier."""
        return self.repository.get_team(team_id)

    def update_team(
        self,
        team_id: UUID | str,
        team_name: str | None = None,
        target_season: str | None = None,
        notes: str | None = None,
    ) -> UserTeam:
        """Update mutable fields of an existing user team."""
        with self._lock:
            team = self.repository.get_team(team_id)
            if team is None:
                raise KeyError(f"Team {team_id} does not exist")

            if team_name is not None:
                if not isinstance(team_name, str) or not team_name.strip():
                    raise ValueError("team_name must be a non-empty string")
                team.team_name = team_name.strip()

            if target_season is not None:
                team.target_season = target_season

            if notes is not None:
                team.notes = notes

            team.updated_at = datetime.now(UTC)
            return self.repository.save_team(team)

    def delete_team(self, team_id: UUID | str) -> bool:
        """Delete a user team and cascade delete all associated player assignments."""
        with self._lock:
            return self.repository.delete_team(team_id)

    def list_teams(
        self,
        limit: int = 100,
        offset: int = 0,
        created_by: str | None = None,
        target_season: str | None = None,
    ) -> list[UserTeam]:
        """List user teams with pagination and optional creator/season filters."""
        return self.repository.list_teams(
            limit=limit,
            offset=offset,
            created_by=created_by,
            target_season=target_season,
        )

    # -------------------------------------------------------------------------
    # Squad Player Management
    # -------------------------------------------------------------------------

    def add_player(
        self,
        team_id: UUID | str,
        player_id: UUID | str,
        assigned_role: str | None = None,
        batting_order: int | None = None,
        is_designated_wk: bool = False,
        is_captain: bool = False,
        allow_oversize: bool = False,
    ) -> UserTeamPlayer:
        """Assign a player to a user team with role, batting order, and captain/WK flags.

        Raises:
            KeyError: If target team does not exist.
            ValueError: If batting_order is not in 1..11 or player_id is invalid.
            SquadConstraintViolationError: For duplicate player, roster capacity breach,
                batting order collision, or multiple captain conflict.
        """
        with self._lock:
            team = self.repository.get_team(team_id)
            if team is None:
                raise KeyError(f"Team {team_id} does not exist")

            team_uuid = team.team_id
            player_uuid = player_id if isinstance(player_id, UUID) else UUID(str(player_id))

            if batting_order is not None and (batting_order < 1 or batting_order > 11):
                raise ValueError(f"batting_order must be between 1 and 11 (got {batting_order})")

            current_players = self.repository.get_team_players(team_uuid)

            # Enforce uniqueness per team
            if any(p.player_id == player_uuid for p in current_players):
                raise SquadConstraintViolationError(
                    message=f"Player {player_uuid} is already assigned to team {team_uuid}",
                    violation_type="DUPLICATE_PLAYER",
                    details={"team_id": str(team_uuid), "player_id": str(player_uuid)},
                )

            # Enforce maximum squad capacity of 25 players (HD-09)
            if len(current_players) >= 25 and not allow_oversize:
                raise SquadConstraintViolationError(
                    message=f"Team {team_uuid} has reached maximum roster capacity of 25 players",
                    violation_type="ROSTER_OVERSIZED",
                    details={"team_id": str(team_uuid), "squad_size": len(current_players)},
                )

            # Enforce unique batting order position
            if batting_order is not None and any(
                p.batting_order == batting_order for p in current_players
            ):
                raise SquadConstraintViolationError(
                    message=(
                        f"Batting order slot {batting_order} is already occupied in team {team_uuid}"
                    ),
                    violation_type="BATTING_ORDER_CONFLICT",
                    details={"team_id": str(team_uuid), "batting_order": batting_order},
                )

            # Enforce single captain assignment
            if is_captain and any(p.is_captain for p in current_players):
                raise SquadConstraintViolationError(
                    message=f"Team {team_uuid} already has a designated captain",
                    violation_type="CAPTAIN_CONFLICT",
                    details={"team_id": str(team_uuid)},
                )

            assignment = UserTeamPlayer(
                user_team_id=team_uuid,
                player_id=player_uuid,
                assigned_role=assigned_role,
                batting_order=batting_order,
                is_designated_wk=is_designated_wk,
                is_captain=is_captain,
                added_at=datetime.now(UTC),
            )
            return self.repository.save_team_player(assignment)

    def update_player(
        self,
        team_id: UUID | str,
        player_id: UUID | str,
        assigned_role: str | None = None,
        batting_order: int | None = None,
        is_designated_wk: bool | None = None,
        is_captain: bool | None = None,
    ) -> UserTeamPlayer:
        """Update role, batting order, WK, or captain flags for an assigned player."""
        with self._lock:
            team = self.repository.get_team(team_id)
            if team is None:
                raise KeyError(f"Team {team_id} does not exist")

            team_uuid = team.team_id
            player_uuid = player_id if isinstance(player_id, UUID) else UUID(str(player_id))

            current_assignment = self.repository.get_team_player_by_player_id(
                team_uuid, player_uuid
            )
            if current_assignment is None:
                raise KeyError(f"Player {player_uuid} is not assigned to team {team_uuid}")

            if batting_order is not None and (batting_order < 1 or batting_order > 11):
                raise ValueError(f"batting_order must be between 1 and 11 (got {batting_order})")

            other_players = [
                p for p in self.repository.get_team_players(team_uuid) if p.player_id != player_uuid
            ]

            # Enforce unique batting order position against other players
            if batting_order is not None and any(
                p.batting_order == batting_order for p in other_players
            ):
                raise SquadConstraintViolationError(
                    message=(
                        f"Batting order slot {batting_order} is already occupied in team {team_uuid}"
                    ),
                    violation_type="BATTING_ORDER_CONFLICT",
                    details={"team_id": str(team_uuid), "batting_order": batting_order},
                )

            # Enforce single captain assignment against other players
            if is_captain is True and any(p.is_captain for p in other_players):
                raise SquadConstraintViolationError(
                    message=f"Team {team_uuid} already has a designated captain",
                    violation_type="CAPTAIN_CONFLICT",
                    details={"team_id": str(team_uuid)},
                )

            if assigned_role is not None:
                current_assignment.assigned_role = assigned_role
            if batting_order is not None:
                current_assignment.batting_order = batting_order
            if is_designated_wk is not None:
                current_assignment.is_designated_wk = is_designated_wk
            if is_captain is not None:
                current_assignment.is_captain = is_captain

            return self.repository.save_team_player(current_assignment)

    def remove_player(self, team_id: UUID | str, player_id: UUID | str) -> bool:
        """Remove a player assignment from a team by composite key."""
        with self._lock:
            return self.repository.delete_team_player_by_player_id(team_id, player_id)

    def get_team_players(self, team_id: UUID | str) -> list[UserTeamPlayer]:
        """Retrieve all player assignments currently in a given team."""
        return self.repository.get_team_players(team_id)

    # -------------------------------------------------------------------------
    # Roster Validation & Governance (HD-05, HD-08, HD-09)
    # -------------------------------------------------------------------------

    def validate_roster(
        self,
        team_id: UUID | str,
        player_metadata: dict[UUID, dict[str, Any]] | None = None,
        strict_official: bool = False,
    ) -> dict[str, Any]:
        """Validate squad composition against IPL roster governance rules.

        Evaluates:
        - Squad capacity (HD-09):
            * N == 0: ROSTER_INCOMPLETE, is_valid_ipl_roster = False
            * N < 18: ROSTER_INCOMPLETE / ROSTER_UNDERSIZED, is_valid_ipl_roster = False
            * 18 <= N <= 25: ROSTER_VALID (subject to other constraints)
            * N > 25: ROSTER_OVERSIZED, is_valid_ipl_roster = False
        - Overseas balance (HD-05):
            * Overseas count <= 8 (overseas_count > 8 -> OVERSEAS_BREACH)
            * Domestic count >= 10 when N >= 18
        - Wicketkeeper balance (HD-08):
            * 2 <= WK <= 3 target benchmark
            * WK < 2: CRITICAL_WK_SHORTAGE flag
            * WK > 3: SLOT_WASTE flag
        - Captain designation:
            * Exactly 1 captain required for official certification
        - Certification rigor (HD-05):
            * If strict_official=True: raises IncompleteRosterError if N < 18;
              requires identity_status == 'RESOLVED' and eligibility_status == 'VERIFIED_ELIGIBLE'
              for ALL players (zero unverified assumptions).
            * If strict_official=False (draft mode): permits provisional exploration.

        Returns dictionary containing squad metrics, flags, violations, and validity.
        """
        with self._lock:
            team = self.repository.get_team(team_id)
            if team is None:
                raise KeyError(f"Team {team_id} does not exist")

            team_uuid = team.team_id
            players = self.repository.get_team_players(team_uuid)
            squad_size = len(players)

            overseas_count = sum(1 for p in players if _is_overseas_player(p, player_metadata))
            domestic_count = squad_size - overseas_count
            designated_wk_count = sum(
                1 for p in players if _is_wicketkeeper_player(p, player_metadata)
            )

            captains = [p for p in players if p.is_captain]
            captain_player_id = captains[0].player_id if captains else None

            violations: list[str] = []
            warnings: list[str] = []
            flags: list[str] = []
            roster_status = RosterStatus.ROSTER_VALID
            is_valid_ipl_roster = True

            # Capacity check (HD-09)
            if squad_size == 0:
                roster_status = RosterStatus.ROSTER_INCOMPLETE
                is_valid_ipl_roster = False
                violations.append(
                    "Squad is empty (0 players). Minimum 18 players required (HD-05, HD-09)."
                )
            elif squad_size < 18:
                roster_status = RosterStatus.ROSTER_INCOMPLETE
                is_valid_ipl_roster = False
                violations.append(
                    f"Squad size ({squad_size}) is below minimum IPL roster requirement of 18 (HD-05, HD-09)."
                )
            elif squad_size > 25:
                roster_status = RosterStatus.ROSTER_OVERSIZED
                is_valid_ipl_roster = False
                violations.append(
                    f"Squad size ({squad_size}) exceeds maximum IPL roster capacity of 25 (HD-05, HD-09)."
                )

            # Overseas quota (HD-05)
            if overseas_count > 8:
                roster_status = RosterStatus.OVERSEAS_BREACH
                is_valid_ipl_roster = False
                violations.append(
                    f"Overseas players count ({overseas_count}) exceeds maximum allowed of 8 (HD-05)."
                )

            if squad_size >= 18 and domestic_count < 10:
                is_valid_ipl_roster = False
                violations.append(
                    f"Domestic players count ({domestic_count}) is below required minimum of 10 (HD-05)."
                )

            # Wicketkeeper target (HD-08)
            if designated_wk_count < 2:
                warnings.append(
                    f"Designated wicketkeeper count ({designated_wk_count}) is below target 2-3 "
                    "(HD-08: CRITICAL_WK_SHORTAGE)."
                )
                flags.append("CRITICAL_WK_SHORTAGE")
                if 18 <= squad_size <= 25 and overseas_count <= 8:
                    roster_status = RosterStatus.CRITICAL_WK_SHORTAGE
            elif designated_wk_count > 3:
                warnings.append(
                    f"Designated wicketkeeper count ({designated_wk_count}) exceeds target 2-3 "
                    "(HD-08: SLOT_WASTE)."
                )
                flags.append("SLOT_WASTE")
                if 18 <= squad_size <= 25 and overseas_count <= 8:
                    roster_status = RosterStatus.SLOT_WASTE

            # Captain designation
            if len(captains) == 0:
                warnings.append("No designated captain assigned in squad.")
            elif len(captains) > 1:
                violations.append(
                    f"Multiple captains assigned ({len(captains)}). Exactly one captain permitted."
                )
                is_valid_ipl_roster = False

            # Strict Official Certification Mode
            if strict_official:
                if squad_size < 18:
                    raise IncompleteRosterError(
                        message=(
                            f"Cannot officially certify incomplete squad with {squad_size} players; "
                            "minimum 18 required (HD-05, HD-09)."
                        ),
                        squad_size=squad_size,
                        details={"team_id": str(team_uuid), "squad_size": squad_size},
                    )

                if len(captains) != 1:
                    is_valid_ipl_roster = False
                    violations.append(
                        "Official certification requires exactly one designated captain."
                    )

                if designated_wk_count < 2:
                    is_valid_ipl_roster = False
                    violations.append(
                        "Official certification requires at least 2 designated wicketkeepers (HD-05)."
                    )

                # Identity and eligibility verification check (HD-05, R13, R18)
                if player_metadata is None:
                    is_valid_ipl_roster = False
                    violations.append(
                        "Official certification strictly requires player metadata with resolved identities "
                        "and verified eligibility (HD-05). None provided."
                    )
                else:
                    for p in players:
                        if p.player_id not in player_metadata:
                            is_valid_ipl_roster = False
                            violations.append(
                                f"Player {p.player_id} lacks verified identity and eligibility metadata. "
                                "Official certification strictly requires verified credentials (HD-05, R18)."
                            )
                            continue

                        meta = player_metadata[p.player_id]
                        ident_status = meta.get("identity_status")
                        elig_status = meta.get("eligibility_status")

                        if ident_status != "RESOLVED":
                            is_valid_ipl_roster = False
                            violations.append(
                                f"Player {p.player_id} has identity_status='{ident_status}'. "
                                "Official certification strictly requires 'RESOLVED' identity (HD-05)."
                            )
                        if elig_status != "VERIFIED_ELIGIBLE":
                            is_valid_ipl_roster = False
                            violations.append(
                                f"Player {p.player_id} has eligibility_status='{elig_status}'. "
                                "Official certification strictly requires 'VERIFIED_ELIGIBLE' (HD-05)."
                            )

            if len(violations) > 0:
                is_valid_ipl_roster = False

            return {
                "team_id": team_uuid,
                "team_name": team.team_name,
                "squad_size": squad_size,
                "overseas_count": overseas_count,
                "domestic_count": domestic_count,
                "designated_wk_count": designated_wk_count,
                "captain_player_id": captain_player_id,
                "roster_status": roster_status,
                "is_valid_ipl_roster": is_valid_ipl_roster,
                "violations": violations,
                "warnings": warnings,
                "flags": flags,
                "players": players,
            }
