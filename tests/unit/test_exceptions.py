"""Unit tests for platform and domain exception hierarchy."""

from src.core.exceptions import (
    ConfigurationError,
    DataIngestionError,
    DataQualityError,
    EligibilityError,
    IdentityResolutionError,
    MembershipVerificationError,
    ProvenanceError,
    RRPlatformError,
    SupabaseConnectionError,
)

ALL_DOMAIN_EXCEPTIONS = [
    IdentityResolutionError,
    MembershipVerificationError,
    DataIngestionError,
    ProvenanceError,
    DataQualityError,
    EligibilityError,
    ConfigurationError,
    SupabaseConnectionError,
]


def test_base_exception_inheritance() -> None:
    """Verify that all domain exceptions inherit from RRPlatformError and Exception."""
    assert issubclass(RRPlatformError, Exception)
    for exc_cls in ALL_DOMAIN_EXCEPTIONS:
        assert issubclass(exc_cls, RRPlatformError)


def test_base_exception_attributes() -> None:
    """Verify message, code, and details formatting in base exception."""
    err = RRPlatformError("Base platform failure", code="PLATFORM_FAIL", details={"key": "val"})
    assert err.message == "Base platform failure"
    assert err.code == "PLATFORM_FAIL"
    assert err.details == {"key": "val"}
    err_str = str(err)
    assert "Base platform failure" in err_str
    assert "code=PLATFORM_FAIL" in err_str
    assert "details={'key': 'val'}" in err_str


def test_identity_resolution_error() -> None:
    """Verify IdentityResolutionError attributes and details dictionary."""
    err = IdentityResolutionError(
        "Candidate collision detected",
        player_identifier="Riyan Parag",
        candidates=["candidate_1", "candidate_2"],
    )
    assert "Candidate collision" in str(err)
    assert err.details["player_identifier"] == "Riyan Parag"
    assert len(err.details["candidates"]) == 2


def test_membership_verification_error() -> None:
    """Verify MembershipVerificationError attributes."""
    err = MembershipVerificationError(
        "Missing verified current squad participation",
        player_id="p-1234",
        season="2027",
    )
    assert err.details["player_id"] == "p-1234"
    assert err.details["season"] == "2027"


def test_data_ingestion_error() -> None:
    """Verify DataIngestionError attributes."""
    err = DataIngestionError("Corrupt payload checksum", source="cricsheet", record_id="rec-001")
    assert err.details["source"] == "cricsheet"
    assert err.details["record_id"] == "rec-001"


def test_provenance_error() -> None:
    """Verify ProvenanceError attributes."""
    err = ProvenanceError(
        "Missing tier 1 evidence", entity_type="player_identity", entity_id="ent-5"
    )
    assert err.details["entity_type"] == "player_identity"
    assert err.details["entity_id"] == "ent-5"


def test_data_quality_error() -> None:
    """Verify DataQualityError attributes."""
    err = DataQualityError("Total runs mismatch", table_name="deliveries", rule_violated="chk_runs")
    assert err.details["table_name"] == "deliveries"
    assert err.details["rule_violated"] == "chk_runs"


def test_eligibility_error() -> None:
    """Verify EligibilityError attributes."""
    err = EligibilityError("Policy evaluation failed", player_id="p-9", policy_id="pol-2")
    assert err.details["player_id"] == "p-9"
    assert err.details["policy_id"] == "pol-2"


def test_configuration_error() -> None:
    """Verify ConfigurationError attributes."""
    err = ConfigurationError("Missing mandatory URL", field_name="supabase_url")
    assert err.details["field_name"] == "supabase_url"


def test_supabase_connection_error() -> None:
    """Verify SupabaseConnectionError attributes."""
    err = SupabaseConnectionError("Connection timeout", endpoint="https://api.supabase.co")
    assert err.details["endpoint"] == "https://api.supabase.co"
