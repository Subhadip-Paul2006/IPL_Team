"""Eligibility Policy Service (TRD §4.3, §11 Domain 8 - Milestone M3).

Manages season-bound eligibility policies, official BCCI/IPL source attribution,
and independent player eligibility evaluation adhering strictly to DDL invariants
and the default-to-NOT_ASSESSED rule.
"""

from __future__ import annotations

import contextlib
from datetime import date
from typing import Any
from uuid import UUID

from src.contracts.eligibility import EligibilityPolicy, PlayerEligibility
from src.contracts.tmve import EligibilityOutputContract, EligibilityStatus
from src.services.base import ServiceBoundary


class EligibilityPolicyService(ServiceBoundary):
    """Eligibility Policy Service managing season-bound rules and player eligibility evaluations."""

    def __init__(self, db_client: Any | None = None) -> None:
        """Initialize the Eligibility Policy Service with in-memory stores and optional DB client.

        Args:
            db_client: Optional database client (e.g. SupabaseClient or MockSupabaseClient).
        """
        self._db_client = db_client
        self._policies: dict[UUID, EligibilityPolicy] = {}
        self._player_eligibility: dict[tuple[UUID, UUID], PlayerEligibility] = {}

    def get_service_name(self) -> str:
        """Return the canonical service identifier."""
        return "eligibility_policy_service"

    def health_check(self) -> dict[str, Any]:
        """Perform service health inspection and return diagnostic status dictionary."""
        return {
            "service": self.get_service_name(),
            "status": "operational",
            "registered_policies_count": len(self._policies),
            "recorded_eligibility_count": len(self._player_eligibility),
            "db_connected": self._db_client is not None,
        }

    def reset(self) -> None:
        """Clear all in-memory policy and player eligibility registries."""
        self._policies.clear()
        self._player_eligibility.clear()

    def register_policy(
        self,
        season_id: UUID,
        policy_version: int,
        effective_date: date,
        rule_source: str,
        policy_json: dict[str, Any] | None = None,
        expiry_date: date | None = None,
        verified: bool = False,
        verification_id: UUID | None = None,
        notes: str | None = None,
        policy_id: UUID | None = None,
    ) -> EligibilityPolicy:
        """Register a versioned, season-bound eligibility policy.

        Validates all DDL invariants:
        - chk_policy_dates: expiry_date IS NULL OR expiry_date >= effective_date.
        - chk_policy_verified_evidence: NOT (verified = TRUE AND verification_id IS NULL).
        - uq_policy: UNIQUE (season_id, policy_version).

        Args:
            season_id: Target season UUID.
            policy_version: Policy version integer (>= 1).
            effective_date: Date from which the policy is effective.
            rule_source: Authoritative BCCI/IPL official source reference (max 200 chars).
            policy_json: Structured policy rule definition payload.
            expiry_date: Optional date after which policy expires.
            verified: Flag indicating whether policy has verified evidence provenance.
            verification_id: Optional verification record UUID (mandatory if verified=True).
            notes: Optional audit notes.
            policy_id: Optional policy UUID override.

        Returns:
            The registered EligibilityPolicy contract.

        Raises:
            ValueError: If any validation rule or DDL constraint is violated.
        """
        if isinstance(season_id, str):
            season_id = UUID(season_id)
        if policy_id is not None and isinstance(policy_id, str):
            policy_id = UUID(policy_id)
        if verification_id is not None and isinstance(verification_id, str):
            verification_id = UUID(verification_id)
        if isinstance(effective_date, str):
            effective_date = date.fromisoformat(effective_date)
        if expiry_date is not None and isinstance(expiry_date, str):
            expiry_date = date.fromisoformat(expiry_date)

        if not rule_source or not rule_source.strip():
            raise ValueError(
                "rule_source must be a non-empty string referencing an official BCCI/IPL source"
            )
        if len(rule_source.strip()) > 200:
            raise ValueError("rule_source cannot exceed 200 characters")

        if policy_version < 1:
            raise ValueError("policy_version must be >= 1")

        # Invariant chk_policy_dates
        if expiry_date is not None and expiry_date < effective_date:
            raise ValueError(
                "chk_policy_dates violation: expiry_date must be greater than or equal to effective_date"
            )

        # Invariant chk_policy_verified_evidence
        if verified and verification_id is None:
            raise ValueError(
                "chk_policy_verified_evidence violation: verification_id cannot be None when verified is True"
            )

        # Invariant uq_policy: unique (season_id, policy_version)
        for existing in self._policies.values():
            if existing.season_id == season_id and existing.policy_version == policy_version:
                if policy_id is not None and existing.policy_id == policy_id:
                    break
                raise ValueError(
                    f"uq_policy violation: Policy version {policy_version} already registered for season {season_id}"
                )

        policy_kwargs: dict[str, Any] = {
            "season_id": season_id,
            "policy_version": policy_version,
            "effective_date": effective_date,
            "rule_source": rule_source.strip(),
            "policy_json": policy_json if policy_json is not None else {},
            "expiry_date": expiry_date,
            "verified": verified,
            "verification_id": verification_id,
            "notes": notes,
        }
        if policy_id is not None:
            policy_kwargs["policy_id"] = policy_id

        policy = EligibilityPolicy(**policy_kwargs)
        self._policies[policy.policy_id] = policy

        if self._db_client is not None:
            row = {
                "policy_id": str(policy.policy_id),
                "season_id": str(policy.season_id),
                "policy_version": policy.policy_version,
                "effective_date": policy.effective_date.isoformat(),
                "expiry_date": policy.expiry_date.isoformat() if policy.expiry_date else None,
                "rule_source": policy.rule_source,
                "verified": policy.verified,
                "verification_id": str(policy.verification_id) if policy.verification_id else None,
                "policy_json": policy.policy_json,
                "notes": policy.notes,
            }
            with contextlib.suppress(Exception):
                self._db_client.table("eligibility_policies").insert(row).execute()

        return policy

    def get_policy_by_id(self, policy_id: UUID) -> EligibilityPolicy | None:
        """Retrieve a registered policy by its unique policy ID."""
        if isinstance(policy_id, str):
            policy_id = UUID(policy_id)
        if policy_id not in self._policies and self._db_client is not None:
            self._sync_policy_by_id_from_db(policy_id)
        return self._policies.get(policy_id)

    def list_policies_for_season(self, season_id: UUID) -> list[EligibilityPolicy]:
        """List all registered policies for a target season."""
        if isinstance(season_id, str):
            season_id = UUID(season_id)
        if self._db_client is not None:
            self._sync_policies_from_db(season_id)
        return [p for p in self._policies.values() if p.season_id == season_id]

    def get_effective_policy(self, season_id: UUID, as_of_date: date) -> EligibilityPolicy | None:
        """Retrieve the effective eligibility policy for a target season as of a specified date.

        A policy is effective if:
        effective_date <= as_of_date AND (expiry_date IS NULL OR as_of_date <= expiry_date).
        When multiple policy versions qualify, the highest policy_version (and latest effective_date)
        takes precedence.

        Args:
            season_id: Target season UUID.
            as_of_date: Evaluation date.

        Returns:
            The active EligibilityPolicy, or None if no valid policy is effective.
        """
        if isinstance(season_id, str):
            season_id = UUID(season_id)
        if isinstance(as_of_date, str):
            as_of_date = date.fromisoformat(as_of_date)

        if self._db_client is not None:
            self._sync_policies_from_db(season_id)

        matching: list[EligibilityPolicy] = []
        for policy in self._policies.values():
            if policy.season_id != season_id:
                continue
            if policy.effective_date <= as_of_date and (
                policy.expiry_date is None or as_of_date <= policy.expiry_date
            ):
                matching.append(policy)

        if not matching:
            return None

        # Sort descending by policy_version, then effective_date
        matching.sort(key=lambda p: (p.policy_version, p.effective_date), reverse=True)
        return matching[0]

    def record_player_eligibility(
        self,
        player_id: UUID,
        policy_id: UUID,
        status: EligibilityStatus | str,
        verified: bool = False,
        verification_id: UUID | None = None,
        notes: str | None = None,
        eligibility_id: UUID | None = None,
    ) -> PlayerEligibility:
        """Record or update a player's eligibility assessment under a specific policy.

        Validates all DDL invariants:
        - chk_eligibility_status: status must be one of VERIFIED_ELIGIBLE, VERIFIED_NOT_ELIGIBLE,
          ELIGIBILITY_UNVERIFIED, NOT_ASSESSED.
        - chk_eligibility_status_flag:
          * VERIFIED_ELIGIBLE and VERIFIED_NOT_ELIGIBLE require verified=True and verification_id is not None.
          * ELIGIBILITY_UNVERIFIED and NOT_ASSESSED require verified=False.
        - Foreign key integrity: policy_id must exist in registered policies.

        Args:
            player_id: Player canonical UUID.
            policy_id: Eligibility policy UUID.
            status: Eligibility status enum or valid string.
            verified: Verification flag.
            verification_id: Optional verification record UUID.
            notes: Optional audit notes.
            eligibility_id: Optional eligibility record UUID override.

        Returns:
            The recorded PlayerEligibility contract.

        Raises:
            ValueError: If any validation rule or DDL constraint is violated.
        """
        if isinstance(player_id, str):
            player_id = UUID(player_id)
        if isinstance(policy_id, str):
            policy_id = UUID(policy_id)
        if verification_id is not None and isinstance(verification_id, str):
            verification_id = UUID(verification_id)
        if eligibility_id is not None and isinstance(eligibility_id, str):
            eligibility_id = UUID(eligibility_id)

        # Normalize status
        if isinstance(status, str):
            try:
                status_enum = EligibilityStatus(status)
            except ValueError as err:
                raise ValueError(
                    f"chk_eligibility_status violation: Invalid status '{status}'"
                ) from err
        else:
            status_enum = status

        # Verify policy foreign key existence
        if policy_id not in self._policies and self._db_client is not None:
            self._sync_policy_by_id_from_db(policy_id)

        if policy_id not in self._policies:
            raise ValueError(
                f"Foreign key violation: Policy {policy_id} does not exist in registered policies"
            )

        # Invariant chk_eligibility_status_flag
        if status_enum in {
            EligibilityStatus.VERIFIED_ELIGIBLE,
            EligibilityStatus.VERIFIED_NOT_ELIGIBLE,
        }:
            if not verified:
                raise ValueError(
                    f"chk_eligibility_status_flag violation: Status {status_enum.value} requires verified=True"
                )
            if verification_id is None:
                raise ValueError(
                    f"chk_eligibility_status_flag violation: Status {status_enum.value} requires non-null verification_id"
                )
        elif status_enum in {
            EligibilityStatus.ELIGIBILITY_UNVERIFIED,
            EligibilityStatus.NOT_ASSESSED,
        }:
            if verified:
                raise ValueError(
                    f"chk_eligibility_status_flag violation: Status {status_enum.value} requires verified=False"
                )

        pe_kwargs: dict[str, Any] = {
            "player_id": player_id,
            "policy_id": policy_id,
            "eligibility_status": status_enum.value,
            "verified": verified,
            "verification_id": verification_id,
            "notes": notes,
        }
        if eligibility_id is not None:
            pe_kwargs["eligibility_id"] = eligibility_id

        record = PlayerEligibility(**pe_kwargs)
        self._player_eligibility[(player_id, policy_id)] = record

        if self._db_client is not None:
            row = {
                "eligibility_id": str(record.eligibility_id),
                "player_id": str(record.player_id),
                "policy_id": str(record.policy_id),
                "eligibility_status": record.eligibility_status,
                "verified": record.verified,
                "verification_id": str(record.verification_id) if record.verification_id else None,
                "notes": record.notes,
            }
            with contextlib.suppress(Exception):
                self._db_client.table("player_eligibility").insert(row).execute()

        return record

    def get_player_eligibility(
        self, player_id: UUID, policy_id: UUID
    ) -> PlayerEligibility | None:
        """Fetch recorded player eligibility by player ID and policy ID."""
        if isinstance(player_id, str):
            player_id = UUID(player_id)
        if isinstance(policy_id, str):
            policy_id = UUID(policy_id)

        key = (player_id, policy_id)
        if key not in self._player_eligibility and self._db_client is not None:
            self._sync_player_eligibility_from_db(player_id, policy_id)

        return self._player_eligibility.get(key)

    def evaluate_player_eligibility(
        self,
        player_id: UUID,
        season_id: UUID,
        as_of_date: date,
    ) -> EligibilityOutputContract:
        """Evaluate a player's competition eligibility for a target season as of a specified date.

        Defaulting Rule (Mandatory):
        Unknown or unassessed player eligibility MUST evaluate to NOT_ASSESSED.
        Eligibility is NEVER inferred from missing records, dataset absence, or assumptions.

        Args:
            player_id: Player canonical UUID.
            season_id: Target season UUID.
            as_of_date: Evaluation date.

        Returns:
            Authoritative EligibilityOutputContract.
        """
        if isinstance(player_id, str):
            player_id = UUID(player_id)
        if isinstance(season_id, str):
            season_id = UUID(season_id)
        if isinstance(as_of_date, str):
            as_of_date = date.fromisoformat(as_of_date)

        policy = self.get_effective_policy(season_id=season_id, as_of_date=as_of_date)
        if policy is None:
            return EligibilityOutputContract(
                player_id=player_id,
                target_season_id=season_id,
                eligibility_status=EligibilityStatus.NOT_ASSESSED,
                policy_id=None,
                policy_version=None,
                verified=False,
                verification_id=None,
                rule_source=None,
                evidence_verification_ids=[],
            )

        # Check player eligibility record
        key = (player_id, policy.policy_id)
        record = self._player_eligibility.get(key)
        if record is None and self._db_client is not None:
            record = self._sync_player_eligibility_from_db(player_id, policy.policy_id)

        if record is None:
            # Player is unassessed under this policy -> strictly default to NOT_ASSESSED
            return EligibilityOutputContract(
                player_id=player_id,
                target_season_id=season_id,
                eligibility_status=EligibilityStatus.NOT_ASSESSED,
                policy_id=policy.policy_id,
                policy_version=policy.policy_version,
                verified=False,
                verification_id=None,
                rule_source=policy.rule_source,
                evidence_verification_ids=[],
            )

        status_enum = EligibilityStatus(record.eligibility_status)
        evidence_ids: list[UUID] = []
        if record.verification_id is not None:
            evidence_ids.append(record.verification_id)

        return EligibilityOutputContract(
            player_id=player_id,
            target_season_id=season_id,
            eligibility_status=status_enum,
            policy_id=policy.policy_id,
            policy_version=policy.policy_version,
            verified=record.verified,
            verification_id=record.verification_id,
            rule_source=policy.rule_source,
            evidence_verification_ids=evidence_ids,
        )

    def _sync_policies_from_db(self, season_id: UUID) -> None:
        """Helper to fetch and cache policies for a season from DB client."""
        if self._db_client is None:
            return
        with contextlib.suppress(Exception):
            resp = (
                self._db_client.table("eligibility_policies")
                .select("*")
                .eq("season_id", str(season_id))
                .execute()
            )
            for row in getattr(resp, "data", []):
                pid = (
                    UUID(row["policy_id"])
                    if isinstance(row["policy_id"], str)
                    else row["policy_id"]
                )
                if pid not in self._policies:
                    pol = EligibilityPolicy(
                        policy_id=pid,
                        season_id=(
                            UUID(row["season_id"])
                            if isinstance(row["season_id"], str)
                            else row["season_id"]
                        ),
                        policy_version=row["policy_version"],
                        effective_date=(
                            date.fromisoformat(row["effective_date"])
                            if isinstance(row["effective_date"], str)
                            else row["effective_date"]
                        ),
                        expiry_date=(
                            date.fromisoformat(row["expiry_date"])
                            if isinstance(row.get("expiry_date"), str)
                            else row.get("expiry_date")
                        ),
                        rule_source=row["rule_source"],
                        verified=row.get("verified", False),
                        verification_id=(
                            UUID(row["verification_id"])
                            if row.get("verification_id")
                            and isinstance(row["verification_id"], str)
                            else row.get("verification_id")
                        ),
                        policy_json=row.get("policy_json"),
                        notes=row.get("notes"),
                    )
                    self._policies[pol.policy_id] = pol

    def _sync_policy_by_id_from_db(self, policy_id: UUID) -> None:
        """Helper to fetch and cache a policy by ID from DB client."""
        if self._db_client is None:
            return
        with contextlib.suppress(Exception):
            resp = (
                self._db_client.table("eligibility_policies")
                .select("*")
                .eq("policy_id", str(policy_id))
                .execute()
            )
            rows = getattr(resp, "data", [])
            if rows:
                row = rows[0]
                pid = (
                    UUID(row["policy_id"])
                    if isinstance(row["policy_id"], str)
                    else row["policy_id"]
                )
                pol = EligibilityPolicy(
                    policy_id=pid,
                    season_id=(
                        UUID(row["season_id"])
                        if isinstance(row["season_id"], str)
                        else row["season_id"]
                    ),
                    policy_version=row["policy_version"],
                    effective_date=(
                        date.fromisoformat(row["effective_date"])
                        if isinstance(row["effective_date"], str)
                        else row["effective_date"]
                    ),
                    expiry_date=(
                        date.fromisoformat(row["expiry_date"])
                        if isinstance(row.get("expiry_date"), str)
                        else row.get("expiry_date")
                    ),
                    rule_source=row["rule_source"],
                    verified=row.get("verified", False),
                    verification_id=(
                        UUID(row["verification_id"])
                        if row.get("verification_id")
                        and isinstance(row["verification_id"], str)
                        else row.get("verification_id")
                    ),
                    policy_json=row.get("policy_json"),
                    notes=row.get("notes"),
                )
                self._policies[pol.policy_id] = pol

    def _sync_player_eligibility_from_db(
        self, player_id: UUID, policy_id: UUID
    ) -> PlayerEligibility | None:
        """Helper to fetch and cache a player eligibility record from DB client."""
        if self._db_client is None:
            return None
        with contextlib.suppress(Exception):
            resp = (
                self._db_client.table("player_eligibility")
                .select("*")
                .eq("player_id", str(player_id))
                .eq("policy_id", str(policy_id))
                .execute()
            )
            rows = getattr(resp, "data", [])
            if rows:
                row = rows[0]
                eid = (
                    UUID(row["eligibility_id"])
                    if isinstance(row["eligibility_id"], str)
                    else row["eligibility_id"]
                )
                rec = PlayerEligibility(
                    eligibility_id=eid,
                    player_id=(
                        UUID(row["player_id"])
                        if isinstance(row["player_id"], str)
                        else row["player_id"]
                    ),
                    policy_id=(
                        UUID(row["policy_id"])
                        if isinstance(row["policy_id"], str)
                        else row["policy_id"]
                    ),
                    eligibility_status=row["eligibility_status"],
                    verified=row.get("verified", False),
                    verification_id=(
                        UUID(row["verification_id"])
                        if row.get("verification_id")
                        and isinstance(row["verification_id"], str)
                        else row.get("verification_id")
                    ),
                    notes=row.get("notes"),
                )
                self._player_eligibility[(rec.player_id, rec.policy_id)] = rec
                return rec
        return None
