"""Squad Intelligence & Composition Engine (SICE) — Master Facade Engine.

Implements SICEEngine satisfying ServiceBoundary contracts, integrating:
- SiceRankingEngine (RK-1.0.0 Top-10 ranking & match-level bootstrap)
- SquadCompositionEngine & BalanceEvaluator (16 balance dimensions & Playing XI)
- ReplacementEngine (RE-1.0.0 16-dimension incumbent replacement)
- TeamBuilderService (UserTeam & UserTeamPlayer CRUD)
- SICERepository (Dual-mode in-memory & PG16 guarded persistence)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

if TYPE_CHECKING:
    from src.sice.repository import RepositoryMode, SICERepository

from src.contracts.sice import (
    LineupEvaluationResult,
    RankingBoardOutputContract,
    ReplacementComparisonOutputContract,
    ReplacementComparisonRequest,
    SICEOutputContract,
)
from src.contracts.team_builder import UserTeam, UserTeamPlayer
from src.services.base import ServiceBoundary

logger = logging.getLogger(__name__)


class SICEEngine(ServiceBoundary):
    """Authoritative master facade for Squad Intelligence & Composition Engine (SICE)."""

    def __init__(
        self,
        ranking_engine: Any | None = None,
        composition_engine: Any | None = None,
        replacement_engine: Any | None = None,
        team_builder: Any | None = None,
        repository: Any | None = None,
        default_seed: int = 42,
    ) -> None:
        """Initialize SICEEngine with injected or default subsystem components."""
        self._ranking_engine = ranking_engine
        self._composition_engine = composition_engine
        self._replacement_engine = replacement_engine
        self._team_builder = team_builder
        self._repository = repository
        self._default_seed = default_seed

    # -------------------------------------------------------------------------
    # Subsystem Properties
    # -------------------------------------------------------------------------
    @property
    def ranking_engine(self) -> Any | None:
        """Return injected ranking engine subsystem."""
        return self._ranking_engine

    @property
    def composition_engine(self) -> Any | None:
        """Return injected squad composition engine subsystem."""
        return self._composition_engine

    @property
    def replacement_engine(self) -> Any | None:
        """Return injected replacement comparison engine subsystem."""
        return self._replacement_engine

    @property
    def team_builder(self) -> Any | None:
        """Return injected team builder service."""
        return self._team_builder

    @property
    def repository(self) -> Any | None:
        """Return injected SICE persistence repository."""
        return self._repository

    # -------------------------------------------------------------------------
    # ServiceBoundary Interface
    # -------------------------------------------------------------------------
    def get_service_name(self) -> str:
        """Return the canonical service identifier for SICE."""
        return "squad_intelligence_comparison_engine"

    def health_check(self) -> dict[str, Any]:
        """Perform service health inspection across all SICE components."""
        return {
            "service": self.get_service_name(),
            "status": "healthy",
            "subsystems": {
                "ranking_engine": "ready" if self._ranking_engine is not None else "uninitialized",
                "composition_engine": (
                    "ready" if self._composition_engine is not None else "uninitialized"
                ),
                "replacement_engine": (
                    "ready" if self._replacement_engine is not None else "uninitialized"
                ),
                "team_builder": "ready" if self._team_builder is not None else "uninitialized",
                "repository": "ready" if self._repository is not None else "uninitialized",
            },
            "default_seed": self._default_seed,
        }

    # -------------------------------------------------------------------------
    # Core Service Methods
    # -------------------------------------------------------------------------
    def evaluate_squad(
        self,
        team_id: UUID,
        context: dict[str, Any] | None = None,
    ) -> SICEOutputContract:
        """Evaluate assembled squad across 16 macro balance dimensions."""
        if not isinstance(team_id, UUID):
            raise TypeError(f"team_id must be a UUID instance, got {type(team_id).__name__}")

        if self._composition_engine is not None:
            return cast(
                SICEOutputContract,
                self._composition_engine.evaluate_squad(team_id, context=context),
            )
        raise NotImplementedError("Squad composition engine not yet wired in Milestone 1 skeleton")

    def evaluate(
        self,
        team_id: UUID,
        context: dict[str, Any] | None = None,
    ) -> SICEOutputContract:
        """Evaluate assembled squad across 16 macro balance dimensions (TRD §8.2 notation alias)."""
        return self.evaluate_squad(team_id=team_id, context=context)

    def optimize_playing_xi(
        self,
        players: list[UserTeamPlayer] | None = None,
        team_id: UUID | None = None,
        player_metadata: dict[UUID, dict[str, Any]] | None = None,
        enable_impact_player: bool = True,
        seed: int | None = None,
        tactical_scenario: str = "BALANCED",
        **kwargs: Any,
    ) -> list[LineupEvaluationResult]:
        """Optimize Playing XI and Impact Player tactical combinations."""
        if self._composition_engine is None:
            raise NotImplementedError(
                "Squad composition engine not yet wired in Milestone 1 skeleton"
            )

        effective_seed = seed if seed is not None else self._default_seed

        if players is None:
            if team_id is None:
                raise ValueError("Either players list or team_id must be provided")
            if not isinstance(team_id, UUID):
                raise TypeError(f"team_id must be a UUID instance, got {type(team_id).__name__}")
            if self._repository is not None:
                players = self._repository.get_team_players(team_id)
            elif self._team_builder is not None:
                players = self._team_builder.get_team_players(team_id)
            else:
                players = []

        return cast(
            list[LineupEvaluationResult],
            self._composition_engine.optimize_playing_xi(
                players=players,
                player_metadata=player_metadata,
                enable_impact_player=enable_impact_player,
                seed=effective_seed,
                tactical_scenario=tactical_scenario,
                **kwargs,
            ),
        )

    def compare_replacement(
        self,
        request: ReplacementComparisonRequest,
        incumbent_dossier: Any | None = None,
        candidate_pool: list[Any] | None = None,
        strict_mode: bool = False,
        **kwargs: Any,
    ) -> ReplacementComparisonOutputContract:
        """Evaluate incumbent replacement across 16 micro comparison dimensions."""
        if not isinstance(request, ReplacementComparisonRequest):
            raise TypeError(
                f"request must be a ReplacementComparisonRequest instance, got "
                f"{type(request).__name__}"
            )

        if self._replacement_engine is not None:
            if (
                incumbent_dossier is None
                and candidate_pool is None
                and not strict_mode
                and not kwargs
            ):
                return cast(
                    ReplacementComparisonOutputContract,
                    self._replacement_engine.compare_replacement(request),
                )
            return cast(
                ReplacementComparisonOutputContract,
                self._replacement_engine.compare_replacement(
                    request=request,
                    incumbent_dossier=incumbent_dossier,
                    candidate_pool=candidate_pool,
                    strict_mode=strict_mode,
                    **kwargs,
                ),
            )
        raise NotImplementedError("Replacement engine not yet wired in Milestone 1 skeleton")

    def run_ranking(
        self,
        config_version: str = "RK-1.0.0",
        candidate_pool: list[dict[str, Any]] | None = None,
        seed: int = 0,
        **kwargs: Any,
    ) -> RankingBoardOutputContract:
        """Execute Top-10 uncapped candidate ranking under RK-1.0.0."""
        if not isinstance(config_version, str) or not config_version:
            raise ValueError("config_version must be a non-empty string")

        if self._ranking_engine is not None:
            return cast(
                RankingBoardOutputContract,
                self._ranking_engine.run_ranking(
                    config_version=config_version,
                    candidate_pool=candidate_pool,
                    seed=seed,
                    **kwargs,
                ),
            )
        raise NotImplementedError("Ranking engine refactor not yet wired in Milestone 1 skeleton")

    def rank_uncapped_candidates(
        self,
        config_version: str = "RK-1.0.0",
        candidate_pool: list[dict[str, Any]] | None = None,
        seed: int = 0,
        **kwargs: Any,
    ) -> RankingBoardOutputContract:
        """Execute Top-10 uncapped candidate ranking under RK-1.0.0 (Unified API)."""
        return self.run_ranking(
            config_version=config_version,
            candidate_pool=candidate_pool,
            seed=seed,
            **kwargs,
        )

    # -------------------------------------------------------------------------
    # Team Builder CRUD Delegations (Service E)
    # -------------------------------------------------------------------------
    def create_user_team(
        self,
        team_name: str,
        target_season: str | None = "IPL 2027",
        created_by: str | None = None,
        notes: str | None = None,
        team_id: UUID | None = None,
    ) -> UserTeam:
        """Create a new user custom squad header."""
        if self._team_builder is None:
            raise NotImplementedError("Team builder service not yet wired in Milestone 1 skeleton")
        return cast(
            UserTeam,
            self._team_builder.create_team(
                team_name=team_name,
                target_season=target_season,
                created_by=created_by,
                notes=notes,
                team_id=team_id,
            ),
        )

    def create_team(
        self,
        team_name: str,
        target_season: str | None = "IPL 2027",
        created_by: str | None = None,
        notes: str | None = None,
        team_id: UUID | None = None,
    ) -> UserTeam:
        """Alias for create_user_team."""
        return self.create_user_team(
            team_name=team_name,
            target_season=target_season,
            created_by=created_by,
            notes=notes,
            team_id=team_id,
        )

    def get_user_team(self, team_id: UUID | str) -> UserTeam | None:
        """Retrieve a user squad by identifier."""
        if self._team_builder is None:
            raise NotImplementedError("Team builder service not yet wired in Milestone 1 skeleton")
        return cast(UserTeam | None, self._team_builder.get_team(team_id))

    def get_team(self, team_id: UUID | str) -> UserTeam | None:
        """Alias for get_user_team."""
        return self.get_user_team(team_id)

    def update_user_team(
        self,
        team_id: UUID | str,
        team_name: str | None = None,
        target_season: str | None = None,
        notes: str | None = None,
    ) -> UserTeam:
        """Update mutable fields of a user squad."""
        if self._team_builder is None:
            raise NotImplementedError("Team builder service not yet wired in Milestone 1 skeleton")
        return cast(
            UserTeam,
            self._team_builder.update_team(
                team_id=team_id,
                team_name=team_name,
                target_season=target_season,
                notes=notes,
            ),
        )

    def update_team(
        self,
        team_id: UUID | str,
        team_name: str | None = None,
        target_season: str | None = None,
        notes: str | None = None,
    ) -> UserTeam:
        """Alias for update_user_team."""
        return self.update_user_team(
            team_id=team_id,
            team_name=team_name,
            target_season=target_season,
            notes=notes,
        )

    def delete_user_team(self, team_id: UUID | str) -> bool:
        """Delete a user squad and cascade delete associated player assignments."""
        if self._team_builder is None:
            raise NotImplementedError("Team builder service not yet wired in Milestone 1 skeleton")
        return bool(self._team_builder.delete_team(team_id))

    def delete_team(self, team_id: UUID | str) -> bool:
        """Alias for delete_user_team."""
        return self.delete_user_team(team_id)

    def list_user_teams(
        self,
        limit: int = 100,
        offset: int = 0,
        created_by: str | None = None,
        target_season: str | None = None,
    ) -> list[UserTeam]:
        """List user squads with pagination and optional creator/season filters."""
        if self._team_builder is None:
            raise NotImplementedError("Team builder service not yet wired in Milestone 1 skeleton")
        return cast(
            list[UserTeam],
            self._team_builder.list_teams(
                limit=limit,
                offset=offset,
                created_by=created_by,
                target_season=target_season,
            ),
        )

    def list_teams(
        self,
        limit: int = 100,
        offset: int = 0,
        created_by: str | None = None,
        target_season: str | None = None,
    ) -> list[UserTeam]:
        """Alias for list_user_teams."""
        return self.list_user_teams(
            limit=limit,
            offset=offset,
            created_by=created_by,
            target_season=target_season,
        )

    def add_player_to_team(
        self,
        team_id: UUID | str,
        player_id: UUID | str,
        assigned_role: str | None = None,
        batting_order: int | None = None,
        is_designated_wk: bool = False,
        is_captain: bool = False,
        allow_oversize: bool = False,
    ) -> UserTeamPlayer:
        """Add a player to a user team roster."""
        if self._team_builder is None:
            raise NotImplementedError("Team builder service not yet wired in Milestone 1 skeleton")
        return cast(
            UserTeamPlayer,
            self._team_builder.add_player(
                team_id=team_id,
                player_id=player_id,
                assigned_role=assigned_role,
                batting_order=batting_order,
                is_designated_wk=is_designated_wk,
                is_captain=is_captain,
                allow_oversize=allow_oversize,
            ),
        )

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
        """Alias for add_player_to_team."""
        return self.add_player_to_team(
            team_id=team_id,
            player_id=player_id,
            assigned_role=assigned_role,
            batting_order=batting_order,
            is_designated_wk=is_designated_wk,
            is_captain=is_captain,
            allow_oversize=allow_oversize,
        )

    def update_player_in_team(
        self,
        team_id: UUID | str,
        player_id: UUID | str,
        assigned_role: str | None = None,
        batting_order: int | None = None,
        is_designated_wk: bool | None = None,
        is_captain: bool | None = None,
    ) -> UserTeamPlayer:
        """Update role or batting order for a rostered player."""
        if self._team_builder is None:
            raise NotImplementedError("Team builder service not yet wired in Milestone 1 skeleton")
        return cast(
            UserTeamPlayer,
            self._team_builder.update_player(
                team_id=team_id,
                player_id=player_id,
                assigned_role=assigned_role,
                batting_order=batting_order,
                is_designated_wk=is_designated_wk,
                is_captain=is_captain,
            ),
        )

    def update_player(
        self,
        team_id: UUID | str,
        player_id: UUID | str,
        assigned_role: str | None = None,
        batting_order: int | None = None,
        is_designated_wk: bool | None = None,
        is_captain: bool | None = None,
    ) -> UserTeamPlayer:
        """Alias for update_player_in_team."""
        return self.update_player_in_team(
            team_id=team_id,
            player_id=player_id,
            assigned_role=assigned_role,
            batting_order=batting_order,
            is_designated_wk=is_designated_wk,
            is_captain=is_captain,
        )

    def remove_player_from_team(
        self,
        team_id: UUID | str,
        player_id: UUID | str,
    ) -> bool:
        """Remove a player from a user team roster."""
        if self._team_builder is None:
            raise NotImplementedError("Team builder service not yet wired in Milestone 1 skeleton")
        return bool(self._team_builder.remove_player(team_id=team_id, player_id=player_id))

    def remove_player(
        self,
        team_id: UUID | str,
        player_id: UUID | str,
    ) -> bool:
        """Alias for remove_player_from_team."""
        return self.remove_player_from_team(team_id=team_id, player_id=player_id)

    def get_team_players(self, team_id: UUID | str) -> list[UserTeamPlayer]:
        """Retrieve all rostered players for a user team."""
        if self._team_builder is None:
            raise NotImplementedError("Team builder service not yet wired in Milestone 1 skeleton")
        return cast(list[UserTeamPlayer], self._team_builder.get_team_players(team_id))

    def validate_roster(
        self,
        team_id: UUID | str,
        player_metadata: dict[UUID, dict[str, Any]] | None = None,
        metadata: dict[UUID, dict[str, Any]] | None = None,
        strict_official: bool = False,
    ) -> dict[str, Any]:
        """Validate roster against IPL tournament rules and franchise constraints."""
        if self._team_builder is None:
            raise NotImplementedError("Team builder service not yet wired in Milestone 1 skeleton")
        meta = player_metadata if player_metadata is not None else metadata
        return cast(
            dict[str, Any],
            self._team_builder.validate_roster(
                team_id=team_id,
                player_metadata=meta,
                strict_official=strict_official,
            ),
        )

    @classmethod
    def create_default(
        cls,
        default_seed: int = 42,
        repository: SICERepository | None = None,
        mode: RepositoryMode | None = None,
        db_client: Any | None = None,
    ) -> SICEEngine:
        """Create and wire fully integrated SICEEngine with authoritative subsystems."""
        from src.sice.balance_evaluator import BalanceEvaluator
        from src.sice.ranking_engine import SiceRankingEngine
        from src.sice.replacement_engine import ReplacementEngine
        from src.sice.repository import RepositoryMode, SICERepository
        from src.sice.squad_composition import SquadCompositionEngine
        from src.sice.team_builder import TeamBuilderService

        if repository is not None:
            repo = repository
        elif mode is not None or db_client is not None:
            repo = SICERepository(mode=mode or RepositoryMode.IN_MEMORY, db_client=db_client)
        else:
            repo = SICERepository(mode=RepositoryMode.IN_MEMORY)

        team_builder = TeamBuilderService(repository=repo)
        ranking_eng = SiceRankingEngine(repository=repo, default_seed=default_seed)
        balance_eval = BalanceEvaluator()
        comp_eng = SquadCompositionEngine(
            balance_evaluator=balance_eval,
            team_builder=team_builder,
            repository=repo,
        )
        repl_eng = ReplacementEngine(default_seed=default_seed)

        return cls(
            ranking_engine=ranking_eng,
            composition_engine=comp_eng,
            replacement_engine=repl_eng,
            team_builder=team_builder,
            repository=repo,
            default_seed=default_seed,
        )
