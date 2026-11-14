"""Team Membership Verification Engine (TMVE) Core Implementation.

Implements Phase 3 authoritative membership verification for Rajasthan Royals
Squad Intelligence Platform in strict compliance with TRD §4.3, §4.4, §4.5,
and §11 inter-engine specifications.
"""

from __future__ import annotations

from contextlib import suppress
from datetime import date
from typing import Any
from uuid import UUID

from src.contracts.competition import PlayerTeamHistory, SquadMembership
from src.contracts.provenance import VerificationRecord
from src.contracts.tmve import (
    RRCurrentState,
    RRRelationshipState,
    TMVEOutputContract,
    TMVERequestContract,
)
from src.services.base import ServiceBoundary

# Canonical franchise identifiers
RR_CANONICAL_NAME = "Rajasthan Royals"
RR_SHORT_CODE = "RR"

# Authoritative operational active seasons for Rajasthan Royals (TRD §4.1)
# Excludes franchise-specific suspension seasons (2016-2017) and future unverified seasons (2027)
RR_ACTIVE_SEASONS: frozenset[int] = frozenset({
    2008,
    2009,
    2010,
    2011,
    2012,
    2013,
    2014,
    2015,
    2018,
    2019,
    2020,
    2021,
    2022,
    2023,
    2024,
    2025,
    2026,
})

RR_SUSPENDED_SEASONS: frozenset[int] = frozenset({2016, 2017})
RR_FUTURE_SEASONS: frozenset[int] = frozenset({2027})

# Contract types establishing genuine squad roster inclusion
SQUAD_INCLUSION_CONTRACT_TYPES: frozenset[str] = frozenset({
    "Retained",
    "Auction Buy",
    "Replacement",
    "Draft",
    "Squad Inclusion",
})

# Association types establishing prior association without regular squad appearances
ASSOCIATION_TYPES_PRIOR: frozenset[str] = frozenset({
    "Loan",
    "Trade",
    "Released",
    "Acquired",
})


def _get_val(record: Any, field_name: str, default: Any = None) -> Any:
    """Helper to extract field value safely from dictionary or object attribute."""
    if isinstance(record, dict):
        return record.get(field_name, default)
    return getattr(record, field_name, default)


class TeamMembershipVerificationEngine(ServiceBoundary):
    """Authoritative Team Membership Verification Engine (TMVE).

    Inherits ServiceBoundary establishing lifecycle and identification contracts.
    Resolves Dimension 1 (RR relationship state), Dimension 2 (RR current state),
    enforces the TRD §4.5 negative verification 7-gate protocol, and guarantees
    zero invented match statistics for squad-only players.
    """

    def __init__(self, db_client: Any = None) -> None:
        """Initialize TMVE with optional PostgreSQL / Supabase client and in-memory store."""
        self.db_client = db_client
        self._in_memory_squads: dict[str, list[dict[str, Any]]] = {}
        self._in_memory_history: dict[str, list[dict[str, Any]]] = {}
        self._in_memory_appearances: dict[str, int] = {}
        self._in_memory_verifications: dict[str, list[dict[str, Any]]] = {}
        self._in_memory_negative_evaluations: dict[str, dict[str, Any]] = {}
        self._rr_team_ids: set[str] = set()

    def get_service_name(self) -> str:
        """Return the canonical service identifier."""
        return "team_membership_verification_engine"

    def health_check(self) -> dict[str, Any]:
        """Perform service health inspection and return diagnostic status dictionary."""
        return {
            "service": self.get_service_name(),
            "status": "healthy",
            "engine_version": "TMVE-1.0.0",
            "db_connected": self.db_client is not None,
        }

    # -------------------------------------------------------------------------
    # In-Memory Registration Helpers (for Testing and Offline Seeding)
    # -------------------------------------------------------------------------

    def register_squad_record(
        self, player_id: UUID | str, record: dict[str, Any] | SquadMembership
    ) -> None:
        """Register a squad membership record for in-memory resolution."""
        pid = str(player_id)
        rec_dict = record.model_dump() if hasattr(record, "model_dump") else dict(record)
        self._in_memory_squads.setdefault(pid, []).append(rec_dict)

    def register_history_record(
        self, player_id: UUID | str, record: dict[str, Any] | PlayerTeamHistory
    ) -> None:
        """Register a player team history record for in-memory resolution."""
        pid = str(player_id)
        rec_dict = record.model_dump() if hasattr(record, "model_dump") else dict(record)
        self._in_memory_history.setdefault(pid, []).append(rec_dict)

    def register_appearances(self, player_id: UUID | str, appearances: int) -> None:
        """Register verified match appearance count for a player."""
        if appearances < 0:
            raise ValueError("verified_appearances cannot be negative")
        self._in_memory_appearances[str(player_id)] = appearances

    def register_verification_record(
        self, player_id: UUID | str, record: dict[str, Any] | VerificationRecord
    ) -> None:
        """Register an evidence verification record for a player."""
        pid = str(player_id)
        rec_dict = record.model_dump() if hasattr(record, "model_dump") else dict(record)
        self._in_memory_verifications.setdefault(pid, []).append(rec_dict)

    def register_negative_evaluation(
        self, player_id: UUID | str, eval_data: dict[str, Any]
    ) -> None:
        """Register pre-computed negative verification parameters for a player."""
        self._in_memory_negative_evaluations[str(player_id)] = eval_data

    def register_rr_team_id(self, team_id: UUID | str) -> None:
        """Register a UUID/str designating Rajasthan Royals franchise."""
        self._rr_team_ids.add(str(team_id))

    # -------------------------------------------------------------------------
    # Core Domain Logic Methods
    # -------------------------------------------------------------------------

    def evaluate_negative_verification(
        self,
        player_id: UUID,
        career_years: list[int],
        squad_coverage: dict[int, bool],
        scorecard_coverage: dict[int, bool],
        has_tier1_2_source: bool,
        human_reviewed: bool,
        has_conflicts: bool = False,
    ) -> tuple[bool, RRRelationshipState, list[str]]:
        """Evaluate the 7 mandatory conditions for TRD §4.5 Negative Verification Protocol.

        A player may be classified NO_VERIFIED_RR_RELATIONSHIP ONLY when ALL 7
        conditions are satisfied:
        1. Historical coverage scope across covered seasons exists
        2. Career window overlaps with active RR competition years
        3. Squad-list coverage consulted and complete for overlapping career years
        4. Scorecard coverage consulted and complete for overlapping career years
        5. At least one tier-1 or tier-2 source consulted
        6. Zero conflicting records detected
        7. Human review completed and verified

        Returns:
            tuple[bool, RRRelationshipState, list[str]]:
                (negative_verification_met, relationship_state, reason_codes)
        """
        failed_reasons: list[str] = []

        # Gate 1: Historical coverage scope across covered seasons
        if not squad_coverage or not scorecard_coverage:
            failed_reasons.append("MISSING_HISTORICAL_SCOPE")

        # Gate 2: Career window overlaps with active RR competition years
        overlapping_years = sorted([y for y in career_years if y in RR_ACTIVE_SEASONS])
        if not overlapping_years:
            failed_reasons.append("NO_CAREER_WINDOW_OVERLAP")

        # Gate 3: Squad-list coverage consulted for all overlapping career years
        if overlapping_years:
            missing_squad = [y for y in overlapping_years if not squad_coverage.get(y, False)]
            if missing_squad:
                failed_reasons.append("INCOMPLETE_SQUAD_COVERAGE")

        # Gate 4: Scorecard coverage consulted for all overlapping career years
        if overlapping_years:
            missing_scorecards = [
                y for y in overlapping_years if not scorecard_coverage.get(y, False)
            ]
            if missing_scorecards:
                failed_reasons.append("INCOMPLETE_SCORECARD_COVERAGE")

        # Gate 5: At least one tier-1 or tier-2 source consulted
        if not has_tier1_2_source:
            failed_reasons.append("LACKS_TIER1_OR_TIER2_SOURCE")

        # Gate 6: Zero conflicting records detected
        if has_conflicts:
            failed_reasons.append("CONFLICTING_RECORDS_DETECTED")

        # Gate 7: Human review completed
        if not human_reviewed:
            failed_reasons.append("HUMAN_REVIEW_NOT_COMPLETED")

        if not failed_reasons:
            return (
                True,
                RRRelationshipState.NO_VERIFIED_RR_RELATIONSHIP,
                ["NEGATIVE_PROTOCOL_PASSED"],
            )

        return (
            False,
            RRRelationshipState.RR_RELATIONSHIP_UNKNOWN,
            failed_reasons,
        )

    def resolve_negative_verification(
        self,
        player_id: UUID,
        active_years: list[int],
    ) -> tuple[bool, RRRelationshipState, list[str]]:
        """Convenience alias for negative verification evaluating recorded or default coverage."""
        eval_data = self._in_memory_negative_evaluations.get(str(player_id))
        if eval_data:
            return self.evaluate_negative_verification(
                player_id=player_id,
                career_years=eval_data.get("career_years", active_years),
                squad_coverage=eval_data.get("squad_coverage", {}),
                scorecard_coverage=eval_data.get("scorecard_coverage", {}),
                has_tier1_2_source=eval_data.get("has_tier1_2_source", False),
                human_reviewed=eval_data.get("human_reviewed", False),
                has_conflicts=eval_data.get("has_conflicts", False),
            )
        return (
            False,
            RRRelationshipState.RR_RELATIONSHIP_UNKNOWN,
            ["MISSING_HISTORICAL_SCOPE", "HUMAN_REVIEW_NOT_COMPLETED"],
        )

    def resolve_relationship_state(
        self,
        player_id: UUID,
        verified_appearances: int,
        squad_records: list[Any],
        history_records: list[Any] | None = None,
    ) -> RRRelationshipState:
        """Resolve Dimension 1 relationship state between a player and Rajasthan Royals.

        Rules:
        - If conflicting records exist: return RR_RELATIONSHIP_UNKNOWN.
        - If verified appearances >= 1: return HISTORICAL_RR_APPEARANCE.
        - If verified appearances == 0:
          * If genuine squad inclusion: return HISTORICAL_RR_SQUAD_ONLY.
          * If prior loan/trade/release association: return PREVIOUSLY_ASSOCIATED.
        - If records are incomplete or missing: return RR_RELATIONSHIP_UNKNOWN.
          NEVER infer non-membership from dataset absence!
        """
        if verified_appearances < 0:
            raise ValueError("verified_appearances must be >= 0")

        hist_records = history_records or []

        # Check for evidence conflicts in records
        for r in squad_records:
            if (
                _get_val(r, "conflict", False) is True
                or _get_val(r, "verification_status") == "CONFLICT"
            ):
                return RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
        for r in hist_records:
            if (
                _get_val(r, "conflict", False) is True
                or _get_val(r, "verification_status") == "CONFLICT"
            ):
                return RRRelationshipState.RR_RELATIONSHIP_UNKNOWN

        if verified_appearances >= 1:
            return RRRelationshipState.HISTORICAL_RR_APPEARANCE

        # verified_appearances == 0
        has_squad_inclusion = False
        has_prior_association = False

        for r in squad_records:
            ctype = _get_val(r, "contract_type", "")
            role = _get_val(r, "role", "")
            if ctype in SQUAD_INCLUSION_CONTRACT_TYPES or role in {
                "Player",
                "Captain",
                "Vice-Captain",
                "Reserve",
                "Injury Replacement",
            }:
                has_squad_inclusion = True
            elif ctype in {"Trade", "Released", "Loan"}:
                has_prior_association = True

        for r in hist_records:
            atype = _get_val(r, "association_type", "")
            if atype in {"Squad", "Played", "Retained"}:
                has_squad_inclusion = True
            elif atype in ASSOCIATION_TYPES_PRIOR:
                has_prior_association = True

        if has_squad_inclusion:
            # MANDATORY GUARDRAIL: A player in the squad who has 0 verified match appearances
            # MUST be classified as HISTORICAL_RR_SQUAD_ONLY, retaining verified appearances = 0
            # and receiving ZERO invented batting/bowling statistics!
            return RRRelationshipState.HISTORICAL_RR_SQUAD_ONLY

        if has_prior_association:
            return RRRelationshipState.PREVIOUSLY_ASSOCIATED

        if squad_records:
            return RRRelationshipState.HISTORICAL_RR_SQUAD_ONLY

        # Incomplete Record Base: missing records default strictly to UNKNOWN
        return RRRelationshipState.RR_RELATIONSHIP_UNKNOWN

    def resolve_current_membership(
        self,
        player_id: UUID,
        as_of_date: date,
        squad_records: list[Any],
    ) -> RRCurrentState:
        """Resolve Dimension 2 current squad membership state relative to Rajasthan Royals.

        Rules:
        - CURRENT: Verified active squad membership covering as_of_date (is_active_squad=True).
        - NOT_CURRENT: Confirmed past association without active current contract (is_active_squad=False,
          contract_type='Released', or all known contracts expired before as_of_date).
        - UNKNOWN: Incomplete, missing, or unverified current squad status.
        """
        if not squad_records:
            return RRCurrentState.UNKNOWN

        has_active = False
        has_inactive = False
        all_unspecified = True

        for r in squad_records:
            is_active = _get_val(r, "is_active_squad")
            ctype = _get_val(r, "contract_type")
            end_date = _get_val(r, "end_date")
            start_date = _get_val(r, "start_date")

            if is_active is True:
                if (end_date and as_of_date > end_date) or (start_date and as_of_date < start_date):
                    has_inactive = True
                else:
                    has_active = True
                all_unspecified = False
            elif is_active is False or ctype == "Released" or (end_date and as_of_date > end_date):
                has_inactive = True
                all_unspecified = False
            elif start_date and end_date and start_date <= as_of_date <= end_date:
                has_active = True
                all_unspecified = False

        if has_active:
            return RRCurrentState.CURRENT

        if has_inactive:
            return RRCurrentState.NOT_CURRENT

        if all_unspecified:
            return RRCurrentState.UNKNOWN

        return RRCurrentState.UNKNOWN

    def verify_player_membership(
        self,
        player_id: UUID | TMVERequestContract,
        as_of_date: date | None = None,
        *,
        squad_records: list[Any] | None = None,
        history_records: list[Any] | None = None,
        appearances: int | None = None,
        verification_records: list[Any] | None = None,
        negative_verification_data: dict[str, Any] | None = None,
        other_ipl_teams: list[str] | None = None,
    ) -> TMVEOutputContract:
        """Verify player membership across Dimension 1 and 2, producing TMVEOutputContract.

        Enforces all TRD §4.3, §4.4, and §4.5 constraints:
        - Separates squad inclusion from match appearances
        - Preserves zero appearances for squad-only members
        - Conflicting evidence forces RR_RELATIONSHIP_UNKNOWN and review_status="REVIEW_REQUIRED"
        - Missing evidence never infers non-membership (yields RR_RELATIONSHIP_UNKNOWN)
        - Only full 7-gate satisfaction yields NO_VERIFIED_RR_RELATIONSHIP
        """
        if isinstance(player_id, TMVERequestContract):
            req_date = player_id.as_of_date
            target_pid: UUID = player_id.player_id
            if as_of_date is None:
                as_of_date = req_date
        else:
            target_pid = player_id

        if as_of_date is None:
            as_of_date = date.today()

        pid_str = str(target_pid)

        # 1. Fetch squad records
        all_squads: list[dict[str, Any]] = []
        if squad_records is not None:
            all_squads.extend(
                [r.model_dump() if hasattr(r, "model_dump") else dict(r) for r in squad_records]
            )
        else:
            all_squads.extend(self._in_memory_squads.get(pid_str, []))
            if self.db_client is not None:
                try:
                    res = (
                        self.db_client.table("squad_memberships")
                        .select("*")
                        .eq("player_id", pid_str)
                        .execute()
                    )
                    all_squads.extend(getattr(res, "data", []) or [])
                except Exception:
                    pass

        # 2. Fetch history records
        all_hist: list[dict[str, Any]] = []
        if history_records is not None:
            all_hist.extend(
                [r.model_dump() if hasattr(r, "model_dump") else dict(r) for r in history_records]
            )
        else:
            all_hist.extend(self._in_memory_history.get(pid_str, []))
            if self.db_client is not None:
                try:
                    res = (
                        self.db_client.table("player_team_history")
                        .select("*")
                        .eq("player_id", pid_str)
                        .execute()
                    )
                    all_hist.extend(getattr(res, "data", []) or [])
                except Exception:
                    pass

        # 3. Fetch verification records
        all_verifs: list[dict[str, Any]] = []
        if verification_records is not None:
            all_verifs.extend(
                [
                    r.model_dump() if hasattr(r, "model_dump") else dict(r)
                    for r in verification_records
                ]
            )
        else:
            all_verifs.extend(self._in_memory_verifications.get(pid_str, []))
            if self.db_client is not None:
                try:
                    res = (
                        self.db_client.table("verification_records")
                        .select("*")
                        .eq("subject_id", pid_str)
                        .execute()
                    )
                    all_verifs.extend(getattr(res, "data", []) or [])
                except Exception:
                    pass

        # 4. Fetch negative verification data if any
        neg_data = negative_verification_data or self._in_memory_negative_evaluations.get(pid_str)

        # 5. Distinguish RR records from other teams
        rr_squads: list[dict[str, Any]] = []
        rr_history: list[dict[str, Any]] = []
        detected_other_teams: set[str] = set()

        if other_ipl_teams:
            detected_other_teams.update(other_ipl_teams)

        for s in all_squads:
            tname = _get_val(s, "team_name")
            tid = str(_get_val(s, "team_id", ""))
            if tname in {RR_CANONICAL_NAME, RR_SHORT_CODE} or (
                tid and tid in self._rr_team_ids
            ):
                rr_squads.append(s)
            elif tname:
                detected_other_teams.add(str(tname))
            elif not tid:
                # Default unspecified team to RR in local context
                rr_squads.append(s)

        for h in all_hist:
            tname = _get_val(h, "team_name")
            tid = str(_get_val(h, "team_id", ""))
            if tname in {RR_CANONICAL_NAME, RR_SHORT_CODE} or (
                tid and tid in self._rr_team_ids
            ):
                rr_history.append(h)
            elif tname:
                detected_other_teams.add(str(tname))
            elif not tid:
                rr_history.append(h)

        # 6. Resolve appearances
        verified_appearances = 0
        if appearances is not None:
            verified_appearances = appearances
        elif pid_str in self._in_memory_appearances:
            verified_appearances = self._in_memory_appearances[pid_str]
        else:
            # Sum appearances from RR history records if recorded
            hist_apps = [
                _get_val(h, "appearances", 0)
                for h in rr_history
                if _get_val(h, "appearances") is not None
            ]
            if hist_apps:
                verified_appearances = sum(hist_apps)

        # 7. Conflict detection
        has_conflicts = False
        conflict_reasons: list[str] = []

        for v in all_verifs:
            if _get_val(v, "verification_status") == "CONFLICT":
                has_conflicts = True
                conflict_reasons.append("CONFLICTING_VERIFICATION_RECORDS")
            if _get_val(v, "conflict", False) is True:
                has_conflicts = True
                conflict_reasons.append("CONFLICTING_EVIDENCE_FLAG")

        for r in all_squads + all_hist:
            if _get_val(r, "conflict", False) is True:
                has_conflicts = True
                conflict_reasons.append("CONFLICTING_MEMBERSHIP_RECORD")

        if neg_data and neg_data.get("has_conflicts", False):
            has_conflicts = True
            conflict_reasons.append("CONFLICTING_RECORDS_DETECTED")

        # 8. Relationship state resolution
        relationship_state: RRRelationshipState
        review_status = "CLEAR"
        review_reason_codes: list[str] = []
        negative_verification_met = False
        membership_confidence: float | None = None

        if has_conflicts:
            # MANDATORY GUARDRAIL: Any conflict forces RR_RELATIONSHIP_UNKNOWN
            # and sets review_status = "REVIEW_REQUIRED" with reason codes.
            relationship_state = RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
            review_status = "REVIEW_REQUIRED"
            review_reason_codes = list(dict.fromkeys(conflict_reasons)) or [
                "CONFLICTING_EVIDENCE"
            ]
            membership_confidence = None
        else:
            resolved_rel = self.resolve_relationship_state(
                player_id=target_pid,
                verified_appearances=verified_appearances,
                squad_records=rr_squads,
                history_records=rr_history,
            )

            if resolved_rel == RRRelationshipState.HISTORICAL_RR_APPEARANCE:
                relationship_state = resolved_rel
                review_status = "CLEAR"
                membership_confidence = 1.0
            elif resolved_rel == RRRelationshipState.HISTORICAL_RR_SQUAD_ONLY:
                # Squad inclusion with 0 verified appearances
                relationship_state = resolved_rel
                review_status = "CLEAR"
                verified_appearances = 0
                membership_confidence = 1.0
            elif resolved_rel == RRRelationshipState.PREVIOUSLY_ASSOCIATED:
                relationship_state = resolved_rel
                review_status = "CLEAR"
                membership_confidence = 0.95
            else:
                # UNKNOWN - evaluate negative verification protocol if evidence supplied
                if neg_data is not None:
                    (
                        neg_met,
                        neg_state,
                        neg_reasons,
                    ) = self.evaluate_negative_verification(
                        player_id=target_pid,
                        career_years=neg_data.get("career_years", []),
                        squad_coverage=neg_data.get("squad_coverage", {}),
                        scorecard_coverage=neg_data.get("scorecard_coverage", {}),
                        has_tier1_2_source=neg_data.get("has_tier1_2_source", False),
                        human_reviewed=neg_data.get("human_reviewed", False),
                        has_conflicts=neg_data.get("has_conflicts", False),
                    )
                    relationship_state = neg_state
                    negative_verification_met = neg_met
                    if neg_met:
                        review_status = "CLEAR"
                        review_reason_codes = ["NEGATIVE_PROTOCOL_PASSED"]
                        membership_confidence = 1.0
                    else:
                        membership_confidence = None
                        if "CONFLICTING_RECORDS_DETECTED" in neg_reasons or (
                            "HUMAN_REVIEW_NOT_COMPLETED" in neg_reasons
                            and not any(
                                r in neg_reasons
                                for r in ["MISSING_HISTORICAL_SCOPE", "NO_CAREER_WINDOW_OVERLAP"]
                            )
                        ):
                            review_status = "REVIEW_REQUIRED"
                        else:
                            review_status = "CLEAR"
                        review_reason_codes = neg_reasons
                else:
                    # Incomplete record base: absent from records defaults strictly to UNKNOWN
                    # NEVER infer non-membership from dataset absence!
                    relationship_state = RRRelationshipState.RR_RELATIONSHIP_UNKNOWN
                    review_status = "CLEAR"
                    membership_confidence = None

        # 9. Current membership resolution
        rr_current_state = self.resolve_current_membership(
            player_id=target_pid,
            as_of_date=as_of_date,
            squad_records=rr_squads,
        )

        # 10. Extract RR season years
        rr_seasons_set: set[str] = set()
        for r in rr_squads:
            s_year = _get_val(r, "season_year")
            if s_year is not None:
                rr_seasons_set.add(str(s_year))
        for r in rr_history:
            s_year = _get_val(r, "season_year")
            if s_year is not None:
                rr_seasons_set.add(str(s_year))
        rr_seasons = sorted(rr_seasons_set)

        # 11. Extract verification record IDs
        evidence_ids: list[UUID] = []
        for v in all_verifs:
            vid = _get_val(v, "verification_id")
            if vid is not None:
                with suppress(ValueError):
                    evidence_ids.append(UUID(str(vid)))

        return TMVEOutputContract(
            contract_version="TMVE-1.0.0",
            player_id=target_pid,
            as_of_date=as_of_date,
            rr_relationship_state=relationship_state,
            rr_current_state=rr_current_state,
            rr_seasons=rr_seasons,
            other_ipl_teams=sorted(detected_other_teams),
            verified_rr_appearances=verified_appearances,
            evidence_verification_ids=evidence_ids,
            verification_date=as_of_date,
            membership_confidence=membership_confidence,
            negative_verification_met=negative_verification_met,
            review_status=review_status,
            review_reason_codes=review_reason_codes,
        )


__all__ = [
    "TeamMembershipVerificationEngine",
    "RR_CANONICAL_NAME",
    "RR_SHORT_CODE",
    "RR_ACTIVE_SEASONS",
    "RR_SUSPENDED_SEASONS",
    "RR_FUTURE_SEASONS",
    "SQUAD_INCLUSION_CONTRACT_TYPES",
    "ASSOCIATION_TYPES_PRIOR",
]
