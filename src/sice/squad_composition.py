"""Squad Composition Engine & Playing XI Optimization.

Part of Phase 06 — SICE (Milestone 4: Squad Composition & 16-Dimension Balance).
Implements SquadCompositionEngine, Playing XI optimization under BCCI/IPL regulations,
dual-mode Impact Player tactical packages (HD-06), deterministic tiebreaking (HD-10),
batting order sequencing, bowling quota allocation, and gap analysis.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from src.contracts.sice import (
    AnalyticalRecommendation,
    LineupEvaluationResult,
    LineupType,
    RosterStatus,
    RunType,
    SICEContractVersion,
    SICEOutputContract,
    SquadBalanceDimensions,
    UncertaintyFlag,
)
from src.contracts.team_builder import UserTeamPlayer
from src.sice.balance_evaluator import (
    SquadBalanceEvaluator,
    _calculate_player_ibc,
    _calculate_player_oc,
    _canonical_role,
    _is_overseas_player,
    _is_pace_style,
    _is_spin_style,
    _is_wicketkeeper_player,
)
from src.sice.exceptions import (
    IncompleteRosterError,
    SquadConstraintViolationError,
)
from src.sice.repository import RepositoryMode, SICERepository
from src.sice.team_builder import TeamBuilderService

# Type Aliases for compatibility with dispatch and prompt terminology
SquadCompositionResult = SICEOutputContract
PlayingXIOptimizationResult = LineupEvaluationResult
RosterPlayerContract = UserTeamPlayer

logger = logging.getLogger(__name__)


class SquadCompositionEngine:
    """Master engine for squad evaluation, gap intelligence, and Playing XI optimization."""

    def __init__(
        self,
        team_builder: TeamBuilderService | None = None,
        balance_evaluator: SquadBalanceEvaluator | None = None,
        repository: SICERepository | None = None,
        default_seed: int = 42,
    ) -> None:
        self.repository = (
            repository if repository is not None else SICERepository(mode=RepositoryMode.IN_MEMORY)
        )
        self.team_builder = (
            team_builder
            if team_builder is not None
            else TeamBuilderService(repository=self.repository)
        )
        self.balance_evaluator = (
            balance_evaluator if balance_evaluator is not None else SquadBalanceEvaluator()
        )
        self.default_seed = default_seed

    # -------------------------------------------------------------------------
    # Squad Evaluation Facade
    # -------------------------------------------------------------------------

    def evaluate_squad(
        self,
        team_id: UUID | str,
        context: dict[str, Any] | None = None,
    ) -> SICEOutputContract:
        """Execute full squad evaluation across 16 dimensions, gap analysis, and Playing XI optimization."""
        ctx = context or {}
        team_uuid = team_id if isinstance(team_id, UUID) else UUID(str(team_id))

        team = self.team_builder.get_team(team_uuid)
        target_season = (
            ctx.get("target_season") or (team.target_season if team else "IPL 2027") or "IPL 2027"
        )

        # Retrieve players: from context if injected, otherwise from repository
        if "players" in ctx and ctx["players"] is not None:
            players: list[UserTeamPlayer] = ctx["players"]
        elif team is not None:
            players = self.repository.get_team_players(team_uuid)
        else:
            raise KeyError(f"Team {team_uuid} does not exist")

        meta: dict[UUID, dict[str, Any]] = ctx.get("player_metadata") or {}
        strict_official = bool(ctx.get("strict_official", False))
        run_type = ctx.get("run_type", RunType.SQUAD_EVALUATION)
        enable_impact_player = bool(ctx.get("enable_impact_player", True))
        seed = int(ctx.get("seed", self.default_seed))
        tactical_scenario = ctx.get("tactical_scenario")

        # Evaluate 16 balance dimensions
        balance = self.balance_evaluator.evaluate_all_dimensions(
            players, player_metadata=meta, target_season=target_season
        )

        n = len(players)
        os_count = balance.overseas_count
        dom_count = balance.domestic_count

        # Check for provisional identities
        has_provisional = any(
            str(meta.get(p.player_id, {}).get("identity_status") or "").upper() == "PROVISIONAL"
            or meta.get(p.player_id, {}).get("uncertainty_flag")
            in {UncertaintyFlag.PROVISIONAL, "PROVISIONAL"}
            for p in players
        )

        # Certification & Invariants (HD-05, HD-09)
        if n < 18:
            if strict_official:
                raise IncompleteRosterError(
                    message=f"Official certification requires at least 18 players (got {n})",
                    squad_size=n,
                    details={"squad_size": n},
                )
            is_valid_ipl_roster = False
            roster_status = RosterStatus.ROSTER_INCOMPLETE
            squad_health_index = None
        elif n > 25:
            if strict_official:
                raise SquadConstraintViolationError(
                    message=f"Roster exceeds maximum capacity of 25 players (got {n})",
                    violation_type="ROSTER_OVERSIZED",
                    details={"squad_size": n},
                )
            is_valid_ipl_roster = False
            roster_status = RosterStatus.ROSTER_OVERSIZED
            squad_health_index = self.balance_evaluator.calculate_squad_health_index(
                balance.dimension_scores, squad_size=n
            )
        elif os_count > 8:
            if strict_official:
                raise SquadConstraintViolationError(
                    message=f"Roster exceeds maximum overseas limit of 8 players (got {os_count})",
                    violation_type="OVERSEAS_BREACH",
                    details={"overseas_count": os_count},
                )
            is_valid_ipl_roster = False
            roster_status = RosterStatus.OVERSEAS_BREACH
            squad_health_index = self.balance_evaluator.calculate_squad_health_index(
                balance.dimension_scores, squad_size=n
            )
        else:
            # Check official mode against provisional identities
            if run_type == RunType.SQUAD_EVALUATION and has_provisional:
                if strict_official or ctx.get("strict_mode", False):
                    raise SquadConstraintViolationError(
                        message="Official certification requires RESOLVED identities and VERIFIED_ELIGIBLE status",
                        violation_type="PROVISIONAL_IDENTITY_IN_OFFICIAL",
                    )
                is_valid_ipl_roster = False
                roster_status = balance.roster_capacity_status
            elif dom_count < 10:
                is_valid_ipl_roster = False
                roster_status = balance.roster_capacity_status
            elif balance.wicketkeeper_count < 2:
                if strict_official or ctx.get("strict_mode", False):
                    raise SquadConstraintViolationError(
                        message=(
                            f"Official certification requires >=2 designated wicketkeepers "
                            f"(HD-08). Found: {balance.wicketkeeper_count}."
                        ),
                        violation_type="INSUFFICIENT_WICKETKEEPERS",
                        details={"wicketkeeper_count": balance.wicketkeeper_count},
                    )
                is_valid_ipl_roster = False
                roster_status = balance.roster_capacity_status
            else:
                is_valid_ipl_roster = True
                roster_status = balance.roster_capacity_status

            squad_health_index = self.balance_evaluator.calculate_squad_health_index(
                balance.dimension_scores, squad_size=n
            )

        # Optimize Playing XI
        if n >= 11:
            recommended_lineups = self.optimize_playing_xi(
                players=players,
                player_metadata=meta,
                enable_impact_player=enable_impact_player,
                seed=seed,
                tactical_scenario=tactical_scenario,
            )
        else:
            recommended_lineups = [
                LineupEvaluationResult(
                    lineup_type=LineupType.TRADITIONAL_XI,
                    starting_xi_player_ids=[],
                    is_valid_ipl_lineup=False,
                    violations=["ROSTER_UNDERSIZED: Squad size < 11"],
                )
            ]

        # Detect gaps, strengths, weaknesses, critical deficits
        strengths, weaknesses, critical_deficits = self._detect_gaps_and_strengths(
            balance, n, os_count, recommended_lineups, meta, players
        )

        # Generate analytical recommendations
        recommendations = self._generate_recommendations(
            balance, strengths, weaknesses, critical_deficits
        )

        # Determine uncertainty badge
        uncertainty_badge = self._determine_uncertainty_badge(
            players, meta, balance.evidentiary_health_score
        )

        # Calculate role distribution
        _, _, role_distribution, _ = self.balance_evaluator.calculate_dim02_role_distribution(
            players, meta
        )

        return SICEOutputContract(
            contract_version=SICEContractVersion.SQUAD_EVAL_VERSION.value,
            team_id=team_uuid,
            target_season=target_season,
            squad_size=n,
            is_valid_ipl_roster=is_valid_ipl_roster,
            roster_status=roster_status,
            squad_health_index=squad_health_index,
            uncertainty_badge=uncertainty_badge,
            balance_dimensions=balance,
            role_distribution=role_distribution,
            strengths=strengths,
            weaknesses=weaknesses,
            critical_deficits=critical_deficits,
            recommended_lineups=recommended_lineups,
            recommendations=recommendations,
        )

    # -------------------------------------------------------------------------
    # Playing XI Optimization
    # -------------------------------------------------------------------------

    def optimize_playing_xi(
        self,
        players: list[UserTeamPlayer],
        player_metadata: dict[UUID, dict[str, Any]] | None = None,
        enable_impact_player: bool = True,
        seed: int = 42,
        tactical_scenario: str | None = None,
    ) -> list[LineupEvaluationResult]:
        """Generate optimal Playing XI combinations and Impact Player tactical packages (HD-06, HD-10)."""
        meta = player_metadata or {}
        n = len(players)

        if n < 11:
            return [
                LineupEvaluationResult(
                    lineup_type=LineupType.TRADITIONAL_XI,
                    starting_xi_player_ids=[],
                    batting_order=[],
                    is_valid_ipl_lineup=False,
                    violations=["ROSTER_UNDERSIZED: Squad size < 11"],
                )
            ]

        # Canonical sort by UUID string ensures bit-for-bit invariance under roster permutations
        players_canonical = sorted(players, key=lambda p: str(p.player_id))

        # Check wicketkeeper availability
        wk_players = [
            p for p in players_canonical if _is_wicketkeeper_player(p, meta.get(p.player_id, {}))
        ]
        zero_wk = len(wk_players) == 0

        # Select 11 starters via deterministic branch-and-bound optimization
        starters, base_violations = self._solve_optimal_starters(
            players_canonical, meta, seed=seed, zero_wk_allowed=zero_wk
        )

        if zero_wk and "CRITICAL_WK_SHORTAGE" not in base_violations:
            base_violations.append("CRITICAL_WK_SHORTAGE")

        # Determine designated wicketkeeper (HD-08: exactly 1 designated keeper in XI)
        designated_wk_id: UUID | None = None
        starters_wks = [
            p for p in starters if _is_wicketkeeper_player(p, meta.get(p.player_id, {}))
        ]
        if starters_wks:
            # Pick highest IBC / designated keeper
            starters_wks_sorted = sorted(
                starters_wks,
                key=lambda p: (
                    p.is_designated_wk,
                    meta.get(p.player_id, {}).get("ibc") or 50.0,
                ),
                reverse=True,
            )
            designated_wk_id = starters_wks_sorted[0].player_id

        # Determine captain
        captain_id: UUID | None = None
        for p in starters:
            if p.is_captain or meta.get(p.player_id, {}).get("is_captain"):
                captain_id = p.player_id
                break
        if captain_id is None:
            # Check if squad had a captain who wasn't selected
            for p in players_canonical:
                if p.is_captain or meta.get(p.player_id, {}).get("is_captain"):
                    captain_id = p.player_id
                    break

        # Count overseas starters
        os_starters = [
            p.player_id for p in starters if _is_overseas_player(p, meta.get(p.player_id, {}))
        ]
        os_count = len(os_starters)

        # Batting order
        batting_order = self._assign_batting_order(starters, meta)

        # Batting depth index & LORM
        bdi_xi, lorm = self._calculate_lineup_bdi_and_lorm(batting_order, meta)

        # Bowling quotas and phase deficits
        bowling_capacity, fbo_count, phase_deficits = self._allocate_bowling_quotas(starters, meta)

        lineup_violations = list(base_violations)
        if os_count > 4:
            lineup_violations.append("OVERSEAS_BREACH")
        if bowling_capacity < 20.0 or fbo_count < 5:
            lineup_violations.append("CRITICAL_BOWLING_DEFICIT")
        if zero_wk:
            lineup_violations.append("CRITICAL_WK_SHORTAGE")

        is_valid_ipl = len(lineup_violations) == 0

        # Construct Traditional XI
        traditional_lineup = LineupEvaluationResult(
            lineup_type=LineupType.TRADITIONAL_XI,
            starting_xi_player_ids=[p.player_id for p in starters],
            batting_order=batting_order,
            captain_player_id=captain_id,
            designated_wicketkeeper_player_id=designated_wk_id,
            overseas_player_ids=os_starters,
            overseas_count=os_count,
            nominated_substitute_ids=[],
            impact_player_id=None,
            impact_sub_out_id=None,
            batting_depth_index=round(bdi_xi, 2) if bdi_xi is not None else None,
            lower_order_resilience=round(lorm, 2) if lorm is not None else None,
            bowling_overs_capacity=round(bowling_capacity, 2),
            frontline_bowlers_count=fbo_count,
            phase_deficits=phase_deficits,
            is_valid_ipl_lineup=is_valid_ipl,
            violations=lineup_violations,
        )

        if not enable_impact_player:
            return [traditional_lineup]

        # Construct Impact Player Tactical Packages (HD-06)
        remaining_players = [p for p in players_canonical if p not in starters]

        # Package 1: BAT_FIRST_IMPACT (extra batting, sub in death bowler)
        subs_bat, impact_in_bat, impact_out_bat = self._select_impact_player_package(
            starters=starters,
            remaining_players=remaining_players,
            meta=meta,
            lineup_type=LineupType.BAT_FIRST_IMPACT,
            os_starter_count=os_count,
        )

        bat_first_violations = list(lineup_violations)
        if (
            impact_in_bat
            and os_count == 4
            and _is_overseas_player(
                next(p for p in remaining_players if p.player_id == impact_in_bat),
                meta.get(impact_in_bat, {}),
            )
        ):
            bat_first_violations.append("OVERSEAS_IMPACT_BREACH")

        bat_first_lineup = LineupEvaluationResult(
            lineup_type=LineupType.BAT_FIRST_IMPACT,
            starting_xi_player_ids=[p.player_id for p in starters],
            batting_order=batting_order,
            captain_player_id=captain_id,
            designated_wicketkeeper_player_id=designated_wk_id,
            overseas_player_ids=os_starters,
            overseas_count=os_count,
            nominated_substitute_ids=subs_bat,
            impact_player_id=impact_in_bat,
            impact_sub_out_id=impact_out_bat,
            batting_depth_index=round(bdi_xi, 2) if bdi_xi is not None else None,
            lower_order_resilience=round(lorm, 2) if lorm is not None else None,
            bowling_overs_capacity=round(bowling_capacity, 2),
            frontline_bowlers_count=fbo_count,
            phase_deficits=phase_deficits,
            is_valid_ipl_lineup=len(bat_first_violations) == 0,
            violations=bat_first_violations,
        )

        # Package 2: BOWL_FIRST_IMPACT (extra bowling, sub in explosive finisher)
        subs_bowl, impact_in_bowl, impact_out_bowl = self._select_impact_player_package(
            starters=starters,
            remaining_players=remaining_players,
            meta=meta,
            lineup_type=LineupType.BOWL_FIRST_IMPACT,
            os_starter_count=os_count,
        )

        bowl_first_violations = list(lineup_violations)
        if (
            impact_in_bowl
            and os_count == 4
            and _is_overseas_player(
                next(p for p in remaining_players if p.player_id == impact_in_bowl),
                meta.get(impact_in_bowl, {}),
            )
        ):
            bowl_first_violations.append("OVERSEAS_IMPACT_BREACH")

        bowl_first_lineup = LineupEvaluationResult(
            lineup_type=LineupType.BOWL_FIRST_IMPACT,
            starting_xi_player_ids=[p.player_id for p in starters],
            batting_order=batting_order,
            captain_player_id=captain_id,
            designated_wicketkeeper_player_id=designated_wk_id,
            overseas_player_ids=os_starters,
            overseas_count=os_count,
            nominated_substitute_ids=subs_bowl,
            impact_player_id=impact_in_bowl,
            impact_sub_out_id=impact_out_bowl,
            batting_depth_index=round(bdi_xi, 2) if bdi_xi is not None else None,
            lower_order_resilience=round(lorm, 2) if lorm is not None else None,
            bowling_overs_capacity=round(bowling_capacity, 2),
            frontline_bowlers_count=fbo_count,
            phase_deficits=phase_deficits,
            is_valid_ipl_lineup=len(bowl_first_violations) == 0,
            violations=bowl_first_violations,
        )

        if tactical_scenario == "BAT_FIRST":
            return [bat_first_lineup]
        if tactical_scenario == "BOWL_FIRST":
            return [bowl_first_lineup]

        return [bat_first_lineup, bowl_first_lineup, traditional_lineup]

    # -------------------------------------------------------------------------
    # Optimization & Selection Engine
    # -------------------------------------------------------------------------

    def _solve_optimal_starters(
        self,
        players: list[UserTeamPlayer],
        meta: dict[UUID, dict[str, Any]],
        seed: int = 42,
        zero_wk_allowed: bool = False,
    ) -> tuple[list[UserTeamPlayer], list[str]]:
        """Deterministic branch-and-bound combinatorial optimization with HD-10 tiebreakers."""
        violations: list[str] = []

        # Identify fixed inclusions
        captain_p = next(
            (p for p in players if p.is_captain or meta.get(p.player_id, {}).get("is_captain")),
            None,
        )

        # Precompute player metrics
        player_data: list[dict[str, Any]] = []
        for p in players:
            m = meta.get(p.player_id, {})
            is_os = _is_overseas_player(p, m)
            is_wk = _is_wicketkeeper_player(p, m)
            sr = m.get("batting_strike_rate") or m.get("strike_rate") or m.get("sr") or 110.0
            avg = m.get("batting_average") or m.get("average") or m.get("avg") or 20.0
            bf = m.get("career_balls_faced") or m.get("balls_faced") or m.get("bf") or 100
            ibc = _calculate_player_ibc(sr, avg, bf) or 30.0

            balls = m.get("career_balls_bowled") or m.get("balls_bowled") or m.get("balls") or 0
            apps = m.get("matches") or m.get("apps") or 1
            econ = m.get("bowling_economy") or m.get("economy") or m.get("econ") or 8.5
            oc = _calculate_player_oc(balls, apps)

            # Bowling utility
            # Bowling utility: scaled so specialist 4-over bowlers compete with top batters
            u_bowl = oc * max(0.0, 12.0 - econ) * 3.5 if oc >= 1.0 else 0.0
            u_bat = ibc
            u_total = u_bat + u_bowl

            player_data.append(
                {
                    "player": p,
                    "is_os": is_os,
                    "is_wk": is_wk,
                    "is_captain": p == captain_p,
                    "oc": oc,
                    "ibc": ibc,
                    "econ": econ,
                    "u_bat": u_bat,
                    "u_bowl": u_bowl,
                    "utility": u_total,
                }
            )

        # Sort candidate players by primary utility descending, then UUID ascending
        player_data.sort(key=lambda d: (-d["utility"], str(d["player"].player_id)))

        def evaluate_combination(combo: list[dict[str, Any]]) -> float:
            tot_util = sum(d["utility"] for d in combo)
            tot_oc = sum(min(4.0, d["oc"]) for d in combo)
            fbo = sum(1 for d in combo if d["oc"] >= 3.5 and d["econ"] <= 9.2)

            bonus = 0.0
            if tot_oc >= 20.0:
                bonus += 50.0
            if fbo >= 5:
                bonus += 30.0
            return float(tot_util + bonus)

        # Use Combinatorial Priority Search (evaluates candidates meeting constraints)
        import itertools

        # Build balanced candidate pool: top batters + top bowlers + all-rounders + captain/WKs
        pool_pids: set[UUID] = set()
        candidate_pool: list[dict[str, Any]] = []

        by_bat = sorted(player_data, key=lambda d: -d["u_bat"])
        by_bowl = sorted(player_data, key=lambda d: (-d["u_bowl"], -d["oc"]))

        for d in by_bat[:7]:
            if d["player"].player_id not in pool_pids:
                candidate_pool.append(d)
                pool_pids.add(d["player"].player_id)

        for d in by_bowl[:7]:
            if d["player"].player_id not in pool_pids:
                candidate_pool.append(d)
                pool_pids.add(d["player"].player_id)

        for d in player_data:
            if (d["is_captain"] or d["is_wk"] or (d["oc"] >= 1.0 and d["u_bat"] >= 40.0)) and d[
                "player"
            ].player_id not in pool_pids:
                candidate_pool.append(d)
                pool_pids.add(d["player"].player_id)

        for d in player_data:
            if len(candidate_pool) >= 18:
                break
            if d["player"].player_id not in pool_pids:
                candidate_pool.append(d)
                pool_pids.add(d["player"].player_id)

        # Check if squad has feasible bowling attack (>= 5 bowlers totaling >= 20 overs)
        squad_bowlers = [d for d in candidate_pool if d["oc"] >= 1.0]
        squad_overs = sum(min(4.0, d["oc"]) for d in squad_bowlers)
        require_full_bowling = len(squad_bowlers) >= 5 and squad_overs >= 20.0

        valid_combos: list[tuple[float, list[UserTeamPlayer]]] = []

        for combo in itertools.combinations(candidate_pool, 11):
            # Constraint 1: Captain must be included if designated
            if captain_p is not None and not any(d["player"] == captain_p for d in combo):
                continue
            # Constraint 2: Max 4 overseas
            if sum(1 for d in combo if d["is_os"]) > 4:
                continue
            # Constraint 3: At least 1 wicketkeeper (unless squad has 0 keepers)
            if not zero_wk_allowed and not any(d["is_wk"] for d in combo):
                continue
            # Constraint 4: Bowling feasibility
            if require_full_bowling:
                bowlers_count = sum(1 for d in combo if d["oc"] >= 1.0)
                overs_sum = sum(min(4.0, d["oc"]) for d in combo)
                if bowlers_count < 5 or overs_sum < 20.0:
                    continue

            score = evaluate_combination(list(combo))
            valid_combos.append((score, [d["player"] for d in combo]))

        # Fallback if no valid combo found with strict filters
        if not valid_combos:
            for combo in itertools.combinations(candidate_pool, 11):
                if sum(1 for d in combo if d["is_os"]) <= 4:
                    score = evaluate_combination(list(combo))
                    valid_combos.append((score, [d["player"] for d in combo]))

        if not valid_combos:
            # Absolute fallback: take first 11
            return [d["player"] for d in player_data[:11]], violations

        # Find best score
        max_score = max(score for score, _ in valid_combos)
        tied_candidates = [
            players_list for score, players_list in valid_combos if abs(score - max_score) < 1e-4
        ]

        # HD-10 Deterministic Tiebreakers:
        # TB1: Higher LORM
        # TB2: Lower aggregate PDS
        # TB3: Ascending lexicographical string sequence of sorted starter UUIDs
        def tiebreaker_key(lineup: list[UserTeamPlayer]) -> tuple[float, float, str]:
            order = self._assign_batting_order(lineup, meta)
            _, lorm = self._calculate_lineup_bdi_and_lorm(order, meta)
            lorm_val = lorm if lorm is not None else 0.0

            _, _, pds_dict = self._allocate_bowling_quotas(lineup, meta)
            total_pds = sum(pds_dict.values())

            lex_uuid = "".join(sorted(str(p.player_id) for p in lineup))

            # Negate LORM so higher LORM sorts first; total_pds is positive so lower PDS sorts first;
            # lex_uuid sorts ascending lexicographically
            return (-lorm_val, total_pds, lex_uuid)

        tied_candidates.sort(key=tiebreaker_key)
        return tied_candidates[0], violations

    def _assign_batting_order(
        self,
        starters: list[UserTeamPlayer],
        meta: dict[UUID, dict[str, Any]],
    ) -> list[UUID]:
        """Sequence 11 players into unique positions 1..11, honoring user explicit positions and IBC/role fit."""
        result: list[UUID | None] = [None] * 11
        unassigned: list[UserTeamPlayer] = []

        # Priority 1: Honor explicit batting order (1..11)
        for p in starters:
            if p.batting_order is not None and 1 <= p.batting_order <= 11:
                idx = p.batting_order - 1
                if result[idx] is None:
                    result[idx] = p.player_id
                else:
                    unassigned.append(p)
            else:
                unassigned.append(p)

        # Categorize unassigned players by role and IBC
        def role_bucket(p: UserTeamPlayer) -> tuple[int, float]:
            m = meta.get(p.player_id, {})
            c_role = _canonical_role(p.assigned_role or m.get("role") or m.get("primary_role"))
            ibc = (
                m.get("ibc")
                or _calculate_player_ibc(
                    m.get("batting_strike_rate"),
                    m.get("batting_average"),
                    m.get("career_balls_faced"),
                )
                or 30.0
            )

            if c_role == "Top-order Batter":
                bucket = 1
            elif c_role in {"Middle-order Batter", "Wicketkeeper Batter"}:
                bucket = 2
            elif c_role in {"Batting All-rounder", "Bowling All-rounder"}:
                bucket = 3
            else:  # Pace Bowler, Spin Bowler, Specialist
                bucket = 4

            return bucket, -ibc

        unassigned.sort(key=role_bucket)

        for p in unassigned:
            # Place in first available empty slot
            for i in range(11):
                if result[i] is None:
                    result[i] = p.player_id
                    break

        return [pid for pid in result if pid is not None]

    def _calculate_lineup_bdi_and_lorm(
        self,
        batting_order: list[UUID],
        meta: dict[UUID, dict[str, Any]],
    ) -> tuple[float | None, float | None]:
        """Compute weighted Lineup Batting Depth Index (BDI) and LORM (positions 7-9)."""
        weights = [1.2, 1.2, 1.1, 1.1, 1.0, 1.0, 0.9, 0.8, 0.6, 0.4, 0.2]
        weighted_sum = 0.0
        w_sum = 0.0
        ibcs: list[float | None] = []

        for idx, pid in enumerate(batting_order):
            m = meta.get(pid, {})
            ibc = m.get("ibc")
            if ibc is None:
                sr = m.get("batting_strike_rate") or m.get("strike_rate")
                avg = m.get("batting_average") or m.get("average")
                bf = m.get("career_balls_faced") or m.get("balls_faced")
                ibc = _calculate_player_ibc(sr, avg, bf)

            ibcs.append(ibc)
            if ibc is not None:
                w = weights[idx] if idx < len(weights) else 0.1
                weighted_sum += w * ibc
                w_sum += w

        bdi = (weighted_sum / w_sum) if w_sum > 0 else None

        # LORM: positions 7, 8, 9 (indices 6, 7, 8)
        pos7_9 = [val for val in ibcs[6:9] if val is not None]
        lorm = (sum(pos7_9) / len(pos7_9)) if pos7_9 else None

        return bdi, lorm

    def _allocate_bowling_quotas(
        self,
        starters: list[UserTeamPlayer],
        meta: dict[UUID, dict[str, Any]],
    ) -> tuple[float, int, dict[str, float]]:
        """Distribute 20 overs across phase specialists and calculate phase deficits (PDS)."""
        bowler_caps: list[dict[str, Any]] = []
        for p in starters:
            m = meta.get(p.player_id, {})
            balls = m.get("career_balls_bowled") or m.get("balls_bowled") or 0
            apps = m.get("matches") or m.get("apps") or 1
            econ = m.get("bowling_economy") or m.get("economy") or m.get("econ")
            oc = _calculate_player_oc(balls, apps)

            if oc >= 1.0 or balls >= 60:
                bowler_caps.append(
                    {
                        "player_id": p.player_id,
                        "oc": min(4.0, oc),
                        "econ": econ if econ is not None else 8.5,
                        "style": m.get("bowling_style") or "",
                        "phase_balls": m.get("phase_balls") or {},
                        "phase_economy": m.get("phase_economy") or {},
                    }
                )

        tot_capacity = sum(b["oc"] for b in bowler_caps)
        fbo = sum(1 for b in bowler_caps if b["oc"] >= 3.5 and b["econ"] <= 9.2)

        # Allocate to phases: PP 6, MID 9, DTH 5
        pp_alloc = 0.0
        mid_alloc = 0.0
        dth_alloc = 0.0

        for b in bowler_caps:
            pb = b["phase_balls"]
            pe = b["phase_economy"]
            style = b["style"]
            econ = b["econ"]

            # Death specialist check
            dth_balls = pb.get("death") or pb.get("dth") or 0
            dth_econ = pe.get("death") or pe.get("dth")
            if (dth_balls >= 24 and dth_econ is not None and dth_econ <= 10.2) or (
                _is_pace_style(style) and econ <= 8.5
            ):
                alloc = min(2.0, 5.0 - dth_alloc, b["oc"])
                dth_alloc += alloc

            # Powerplay specialist check
            pp_balls = pb.get("powerplay") or pb.get("pp") or 0
            pp_econ = pe.get("powerplay") or pe.get("pp")
            if (pp_balls >= 24 and pp_econ is not None and pp_econ <= 8.5) or (
                _is_pace_style(style) and econ <= 8.2
            ):
                alloc = min(2.0, 6.0 - pp_alloc, b["oc"])
                pp_alloc += alloc

            # Middle specialist check
            mid_balls = pb.get("middle") or pb.get("mid") or 0
            mid_econ = pe.get("middle") or pe.get("mid")
            if (mid_balls >= 24 and mid_econ is not None and mid_econ <= 8.2) or (
                _is_spin_style(style) and econ <= 8.0
            ):
                alloc = min(3.0, 9.0 - mid_alloc, b["oc"])
                mid_alloc += alloc

        pds_pp = max(0.0, round(6.0 - pp_alloc, 2))
        pds_mid = max(0.0, round(9.0 - mid_alloc, 2))
        pds_dth = max(0.0, round(5.0 - dth_alloc, 2))

        phase_deficits = {
            "powerplay": pds_pp,
            "middle": pds_mid,
            "death": pds_dth,
        }

        return tot_capacity, fbo, phase_deficits

    def _select_impact_player_package(
        self,
        starters: list[UserTeamPlayer],
        remaining_players: list[UserTeamPlayer],
        meta: dict[UUID, dict[str, Any]],
        lineup_type: LineupType,
        os_starter_count: int,
    ) -> tuple[list[UUID], UUID | None, UUID | None]:
        """Nominate 5 substitutes and select Impact Player adhering to HD-06 overseas governance."""
        if not remaining_players:
            return [], None, None

        # Sort remaining players by utility
        def sub_priority(p: UserTeamPlayer) -> float:
            m = meta.get(p.player_id, {})
            u_bowl = _calculate_player_oc(m.get("career_balls_bowled"), m.get("matches")) * 10.0
            u_bat = m.get("ibc") or 50.0
            return u_bowl + u_bat

        sorted_remaining = sorted(remaining_players, key=sub_priority, reverse=True)
        nominated_subs = [p.player_id for p in sorted_remaining[:5]]

        # HD-06 Overseas Rule:
        # If starters have 4 overseas, the Impact Player MUST be an Indian domestic player!
        eligible_for_impact = sorted_remaining[:5]
        if os_starter_count >= 4:
            eligible_for_impact = [
                p
                for p in eligible_for_impact
                if not _is_overseas_player(p, meta.get(p.player_id, {}))
            ]
            if not eligible_for_impact:
                # Find best Indian substitute from all remaining
                eligible_for_impact = [
                    p
                    for p in sorted_remaining
                    if not _is_overseas_player(p, meta.get(p.player_id, {}))
                ]

        impact_in: UUID | None = None
        impact_out: UUID | None = None

        if lineup_type == LineupType.BAT_FIRST_IMPACT:
            # Bat first: impact player in is a bowler
            bowler_subs = [
                p
                for p in eligible_for_impact
                if _calculate_player_oc(
                    meta.get(p.player_id, {}).get("career_balls_bowled"),
                    meta.get(p.player_id, {}).get("matches"),
                )
                >= 2.0
            ]
            if bowler_subs:
                impact_in = bowler_subs[0].player_id
            elif eligible_for_impact:
                impact_in = eligible_for_impact[0].player_id

            # Sub out a top/middle batter
            batters_in_starters = [
                p
                for p in starters
                if _canonical_role(p.assigned_role or meta.get(p.player_id, {}).get("role"))
                in {"Top-order Batter", "Middle-order Batter"}
                and not p.is_captain
                and not p.is_designated_wk
            ]
            if batters_in_starters:
                impact_out = batters_in_starters[0].player_id
            else:
                impact_out = starters[0].player_id

        else:  # BOWL_FIRST_IMPACT
            # Bowl first: impact player in is a batter/finisher
            batter_subs = [
                p
                for p in eligible_for_impact
                if _canonical_role(p.assigned_role or meta.get(p.player_id, {}).get("role"))
                in {"Middle-order Batter", "Top-order Batter", "Batting All-rounder"}
            ]
            if batter_subs:
                impact_in = batter_subs[0].player_id
            elif eligible_for_impact:
                impact_in = eligible_for_impact[0].player_id

            # Sub out an early bowler
            bowlers_in_starters = [
                p
                for p in starters
                if _calculate_player_oc(
                    meta.get(p.player_id, {}).get("career_balls_bowled"),
                    meta.get(p.player_id, {}).get("matches"),
                )
                >= 3.0
                and not p.is_captain
            ]
            if bowlers_in_starters:
                impact_out = bowlers_in_starters[0].player_id
            else:
                impact_out = starters[-1].player_id

        # Ensure nominated_subs contains impact_in
        if impact_in and impact_in not in nominated_subs:
            nominated_subs = [impact_in] + nominated_subs[:4]

        return nominated_subs, impact_in, impact_out

    # -------------------------------------------------------------------------
    # Gap Analysis & Recommendation Synthesis
    # -------------------------------------------------------------------------

    def _detect_gaps_and_strengths(
        self,
        b: SquadBalanceDimensions,
        squad_size: int,
        os_count: int,
        lineups: list[LineupEvaluationResult],
        meta: dict[UUID, dict[str, Any]],
        players: list[UserTeamPlayer],
    ) -> tuple[list[str], list[str], list[str]]:
        """Identify squad strengths, weaknesses, and critical deficits."""
        strengths: list[str] = []
        weaknesses: list[str] = []
        critical_deficits: list[str] = []

        scores = b.dimension_scores

        # Strengths (scores >= 80.0)
        dim01 = scores.get("DIM-01")
        if dim01 is not None and dim01 >= 90.0:
            strengths.append("ROSTER_BALANCE_OPTIMAL")
        dim02 = scores.get("DIM-02")
        if dim02 is not None and dim02 >= 80.0:
            strengths.append("ROLE_DISTRIBUTION_BALANCE")
        dim03 = scores.get("DIM-03")
        if dim03 is not None and dim03 >= 80.0:
            strengths.append("BATTING_DEPTH_EXCELLENCE")
        dim04 = scores.get("DIM-04")
        if dim04 is not None and dim04 >= 80.0:
            strengths.append("BOWLING_OVERS_CUSHION")
        dim05 = scores.get("DIM-05")
        if dim05 is not None and dim05 >= 90.0:
            strengths.append("PACE_SPIN_EQUILIBRIUM")
        dim07 = scores.get("DIM-07")
        if dim07 is not None and dim07 >= 90.0:
            strengths.append("ELITE_WICKETKEEPER_SECURITY")
        dim10 = scores.get("DIM-10")
        if dim10 is not None and dim10 >= 85.0:
            strengths.append("BOWLING_STYLE_DIVERSITY")
        dim12 = scores.get("DIM-12")
        if dim12 is not None and dim12 >= 90.0:
            strengths.append("DOMESTIC_UNCAPPED_DEPTH")

        # Weaknesses
        if b.pace_to_spin_ratio is not None:
            if b.pace_to_spin_ratio < 0.8:
                weaknesses.append("PACE_DEFICIT")
            elif b.pace_to_spin_ratio > 2.5:
                weaknesses.append("SPIN_DEFICIT")

        if b.lower_order_resilience is not None and b.lower_order_resilience < 25.0:
            weaknesses.append("LONG_TAIL_VULNERABILITY")

        if b.wicketkeeper_count == 1:
            weaknesses.append("VULNERABILITY_NO_BACKUP_WK")
        elif b.wicketkeeper_count > 3:
            weaknesses.append("SLOT_WASTE")

        if b.bowling_style_diversity_count < 3:
            weaknesses.append("PREDICTABLE_BOWLING_ATTACK")

        if b.all_rounder_count < 3:
            weaknesses.append("TACTICAL_RIGIDITY")

        if b.left_hand_batting_ratio_top7 == 0.0:
            weaknesses.append("ONE_DIMENSIONAL_RHB_LINEUP")

        if b.mean_squad_age is not None and b.mean_squad_age > 29.5:
            weaknesses.append("VETERAN_FATIGUE_EXPOSURE")

        if b.verified_uncapped_count < 5:
            weaknesses.append("REGULATORY_UNCAPPED_DEFICIT")

        if b.role_cannibalization_flags:
            weaknesses.append("ROSTER_SLOT_CANNIBALIZATION")

        if b.positional_coverage_deficit > 0:
            weaknesses.append("POSITIONAL_DEPTH_SHORTAGE")

        if b.tactical_versatility_score < 0.50:
            weaknesses.append("TACTICAL_FRAGILITY")

        has_provisional = any(
            str(meta.get(p.player_id, {}).get("identity_status") or "").upper() == "PROVISIONAL"
            or meta.get(p.player_id, {}).get("uncertainty_flag")
            in {UncertaintyFlag.PROVISIONAL, "PROVISIONAL"}
            for p in players
        )
        if b.evidentiary_health_score < 0.75 or has_provisional:
            weaknesses.append("PROVISIONAL_SQUAD_INTELLIGENCE")

        if b.bowling_overs_capacity < 30.0:
            weaknesses.append("BOWLING_CUSHION_DEFICIT")

        # Check role vacuums
        for r_name in ["Pace Bowler", "Spin Bowler"]:
            if b.pace_bowler_count == 0 and r_name == "Pace Bowler":
                weaknesses.append("ROLE_VACUUM")
            if b.spin_bowler_count == 0 and r_name == "Spin Bowler":
                weaknesses.append("ROLE_VACUUM")

        # Critical Deficits
        if squad_size < 18:
            critical_deficits.append("ROSTER_INCOMPLETE")
        elif squad_size > 25:
            critical_deficits.append("ROSTER_OVERSIZED")

        if os_count > 8:
            critical_deficits.append("OVERSEAS_BREACH")

        if b.wicketkeeper_count == 0:
            critical_deficits.append("CRITICAL_WK_SHORTAGE")

        if lineups:
            first_lineup = lineups[0]
            if first_lineup.phase_deficits.get("death", 0.0) > 0.0:
                critical_deficits.append("CRITICAL_DEATH_BOWLING_DEFICIT")
            if (
                first_lineup.bowling_overs_capacity < 20.0
                or first_lineup.frontline_bowlers_count < 5
            ):
                critical_deficits.append("CRITICAL_BOWLING_DEFICIT")

        return strengths, weaknesses, critical_deficits

    def _generate_recommendations(
        self,
        b: SquadBalanceDimensions,
        strengths: list[str],
        weaknesses: list[str],
        critical_deficits: list[str],
    ) -> list[AnalyticalRecommendation]:
        """Synthesize actionable, evidence-backed analytical recommendations."""
        recs: list[AnalyticalRecommendation] = []

        for deficit in critical_deficits:
            if deficit == "CRITICAL_WK_SHORTAGE":
                recs.append(
                    AnalyticalRecommendation(
                        statement="Squad contains zero designated wicketkeepers. Immediate procurement required to satisfy statutory playing XI regulations.",
                        evidence_metrics=["wicketkeeper_count=0", "dim07_score=0.0"],
                        confidence=1.0,
                    )
                )
            elif deficit == "CRITICAL_DEATH_BOWLING_DEFICIT":
                recs.append(
                    AnalyticalRecommendation(
                        statement="Death bowling phase deficit detected. Roster lacks specialized death overs bowling options conceding <= 9.5 economy.",
                        evidence_metrics=["phase_deficit_death>0.0"],
                        confidence=0.95,
                    )
                )
            elif deficit == "CRITICAL_BOWLING_DEFICIT":
                recs.append(
                    AnalyticalRecommendation(
                        statement="Starting XI lacks mandatory 20 bowling overs across 5 frontline bowling assets.",
                        evidence_metrics=[f"bowling_overs_capacity={b.bowling_overs_capacity}"],
                        confidence=1.0,
                    )
                )
            elif deficit == "OVERSEAS_BREACH":
                recs.append(
                    AnalyticalRecommendation(
                        statement="Overseas quota ceiling breached. Maximum 8 overseas players permitted under IPL regulations.",
                        evidence_metrics=[f"overseas_count={b.overseas_count}"],
                        confidence=1.0,
                    )
                )

        for weakness in weaknesses:
            if weakness == "PACE_DEFICIT":
                recs.append(
                    AnalyticalRecommendation(
                        statement="Pace bowling depth is underrepresented relative to spin resources.",
                        evidence_metrics=[f"pace_to_spin_ratio={b.pace_to_spin_ratio}"],
                        confidence=0.90,
                    )
                )
            elif weakness == "SPIN_DEFICIT":
                recs.append(
                    AnalyticalRecommendation(
                        statement="Spin bowling depth is severely restricted; acquire domestic finger or wrist-spin coverage.",
                        evidence_metrics=[f"pace_to_spin_ratio={b.pace_to_spin_ratio}"],
                        confidence=0.90,
                    )
                )
            elif weakness == "VULNERABILITY_NO_BACKUP_WK":
                recs.append(
                    AnalyticalRecommendation(
                        statement="Squad has only 1 wicketkeeper; acquire at least 1 reserve keeper to satisfy HD-08 tournament safety.",
                        evidence_metrics=["wicketkeeper_count=1"],
                        confidence=0.95,
                    )
                )

        if not recs:
            recs.append(
                AnalyticalRecommendation(
                    statement="Squad composition satisfies core tactical and regulatory balance parameters across evaluated dimensions.",
                    evidence_metrics=[
                        f"squad_size={b.squad_size}",
                        f"overseas_count={b.overseas_count}",
                    ],
                    confidence=0.90,
                )
            )

        return recs

    def _determine_uncertainty_badge(
        self,
        players: list[UserTeamPlayer],
        meta: dict[UUID, dict[str, Any]],
        evidentiary_health: float,
    ) -> str:
        """Determine uncertainty badge: 'VERIFIED', 'PROVISIONAL', or 'SAMPLE_CONSTRAINED' (HD-05)."""
        has_provisional = any(
            str(meta.get(p.player_id, {}).get("identity_status") or "").upper() == "PROVISIONAL"
            or meta.get(p.player_id, {}).get("uncertainty_flag")
            in {UncertaintyFlag.PROVISIONAL, "PROVISIONAL"}
            for p in players
        )
        if has_provisional or evidentiary_health < 0.75:
            return "PROVISIONAL"
        if evidentiary_health >= 0.90:
            return "VERIFIED"
        return "SAMPLE_CONSTRAINED"
