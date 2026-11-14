"""Domain exception hierarchy for RR Squad Intelligence Platform."""

from typing import Any


class RRPlatformError(Exception):
    """Base exception for all RR Platform runtime and domain errors."""

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}

    def __str__(self) -> str:
        parts = [self.message]
        if self.code:
            parts.append(f"code={self.code}")
        if self.details:
            parts.append(f"details={self.details}")
        return " | ".join(parts)


class IdentityResolutionError(RRPlatformError):
    """Raised when PIRE identity resolution fails or encounters ambiguous candidates."""

    def __init__(
        self,
        message: str,
        code: str | None = "IDENTITY_RESOLUTION_ERROR",
        player_identifier: str | None = None,
        candidates: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        det = dict(details) if details else {}
        if player_identifier:
            det["player_identifier"] = player_identifier
        if candidates:
            det["candidates"] = candidates
        super().__init__(message, code=code, details=det)


class MembershipVerificationError(RRPlatformError):
    """Raised when TMVE team membership verification fails or violates verification rules."""

    def __init__(
        self,
        message: str,
        code: str | None = "MEMBERSHIP_VERIFICATION_ERROR",
        player_id: str | None = None,
        season: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        det = dict(details) if details else {}
        if player_id:
            det["player_id"] = player_id
        if season:
            det["season"] = season
        super().__init__(message, code=code, details=det)


class DataIngestionError(RRPlatformError):
    """Raised when ingestion of raw data sources fails or data is corrupted."""

    def __init__(
        self,
        message: str,
        code: str | None = "DATA_INGESTION_ERROR",
        source: str | None = None,
        record_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        det = dict(details) if details else {}
        if source:
            det["source"] = source
        if record_id:
            det["record_id"] = record_id
        super().__init__(message, code=code, details=det)


class ProvenanceError(RRPlatformError):
    """Raised when evidence verification or provenance tracking invariants fail."""

    def __init__(
        self,
        message: str,
        code: str | None = "PROVENANCE_ERROR",
        entity_type: str | None = None,
        entity_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        det = dict(details) if details else {}
        if entity_type:
            det["entity_type"] = entity_type
        if entity_id:
            det["entity_id"] = entity_id
        super().__init__(message, code=code, details=det)


class DataQualityError(RRPlatformError):
    """Raised when data quality validation or relational invariant checks fail."""

    def __init__(
        self,
        message: str,
        code: str | None = "DATA_QUALITY_ERROR",
        table_name: str | None = None,
        rule_violated: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        det = dict(details) if details else {}
        if table_name:
            det["table_name"] = table_name
        if rule_violated:
            det["rule_violated"] = rule_violated
        super().__init__(message, code=code, details=det)


class EligibilityError(RRPlatformError):
    """Raised when player eligibility rules, policies, or evaluations fail."""

    def __init__(
        self,
        message: str,
        code: str | None = "ELIGIBILITY_ERROR",
        player_id: str | None = None,
        policy_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        det = dict(details) if details else {}
        if player_id:
            det["player_id"] = player_id
        if policy_id:
            det["policy_id"] = policy_id
        super().__init__(message, code=code, details=det)


class ConfigurationError(RRPlatformError):
    """Raised when application configuration or required secrets are missing/invalid."""

    def __init__(
        self,
        message: str,
        code: str | None = "CONFIGURATION_ERROR",
        field_name: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        det = dict(details) if details else {}
        if field_name:
            det["field_name"] = field_name
        super().__init__(message, code=code, details=det)


class SupabaseConnectionError(RRPlatformError):
    """Raised when connecting to or communicating with Supabase fails."""

    def __init__(
        self,
        message: str,
        code: str | None = "SUPABASE_CONNECTION_ERROR",
        endpoint: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        det = dict(details) if details else {}
        if endpoint:
            det["endpoint"] = endpoint
        super().__init__(message, code=code, details=det)
