"""SICE Domain Exception Hierarchy.

Authoritative domain exceptions for Squad Intelligence & Composition Engine (SICE),
inheriting from RRPlatformError in compliance with docs/TRD.md §8 and
reports/phase6-execution/PHASE6_SICE_READINESS_REPORT.md.
"""

from __future__ import annotations

from typing import Any

from src.core.exceptions import RRPlatformError


class SICEError(RRPlatformError):
    """Base exception for all SICE operations."""

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code or self.__class__.__name__, details=details)


class SquadConstraintViolationError(SICEError):
    """Raised when squad composition violates IPL tournament regulations or roster constraints."""

    def __init__(
        self,
        message: str,
        violation_type: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.violation_type = violation_type
        det = dict(details) if details else {}
        if violation_type:
            det["violation_type"] = violation_type
        super().__init__(message, code="SQUAD_CONSTRAINT_VIOLATION", details=det)


class IncompleteRosterError(SquadConstraintViolationError):
    """Raised when an incomplete draft squad (N < 18) is submitted for official certification."""

    def __init__(
        self,
        message: str,
        squad_size: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        det = dict(details) if details else {}
        det["squad_size"] = squad_size
        super().__init__(message, violation_type="ROSTER_INCOMPLETE", details=det)


class GateFailureError(SICEError):
    """Raised when candidate relevance gate check fails or gate thresholds are invalid."""

    def __init__(
        self,
        message: str,
        role_group: str | None = None,
        metric: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        det = dict(details) if details else {}
        if role_group:
            det["role_group"] = role_group
        if metric:
            det["metric"] = metric
        super().__init__(message, code="GATE_FAILURE", details=det)


class RankingDeterminismError(SICEError):
    """Raised when ranking tiebreakers fail to establish total ordering or uncalibrated seed is detected."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code="RANKING_DETERMINISM_ERROR", details=details)


class SafetyReviewInterceptionError(SICEError):
    """Raised when automated evaluation is halted due to upstream REVIEW_REQUIRED status."""

    def __init__(
        self,
        message: str,
        dossier_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        det = dict(details) if details else {}
        if dossier_id:
            det["dossier_id"] = dossier_id
        super().__init__(message, code="SAFETY_REVIEW_INTERCEPTION", details=det)


class ScorecardGranularityError(SICEError):
    """Raised when delivery-level calculations are attempted on scorecard-only data without fallback."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code="SCORECARD_GRANULARITY_ERROR", details=details)


class RoleCompatibilityError(SICEError):
    """Raised when incompatible role transition or replacement is evaluated."""

    def __init__(
        self,
        message: str,
        incumbent_role: str | None = None,
        candidate_role: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        det = dict(details) if details else {}
        if incumbent_role:
            det["incumbent_role"] = incumbent_role
        if candidate_role:
            det["candidate_role"] = candidate_role
        super().__init__(message, code="ROLE_COMPATIBILITY_ERROR", details=det)


class DatabaseEnvironmentGuardError(RuntimeError, SICEError):
    """Raised when unauthorized live database access on port 5432 is attempted during test execution."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = "DATABASE_ENVIRONMENT_GUARD_ERROR"
        self.details = details or {}
