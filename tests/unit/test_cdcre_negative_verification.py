"""Negative verification and protocol boundary test suite for CDCRE (Milestone M5).

Covers:
1. AC-10 Protocol Compliance: Rejection of invalid types and parameters.
2. PostgreSQL 16 DDL Strict Compliance: chk_subject_type enforcement in provenance.
3. AC-11 Mandatory Invariant: Missing datasets emit DATASET_UNAVAILABLE, never 0 or non-participation.
4. Non-existent player queries and zero-fabrication guarantees.
5. Contract immutability, extra-field prohibition, and type validation.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pydantic
import pytest
from src.cdcre.candidate_discovery import discover_candidates
from src.cdcre.career_retrieval import discover_career
from src.cdcre.coverage_evaluator import evaluate_coverage
from src.cdcre.engine import get_cdcre_engine
from src.cdcre.provenance import VALID_SUBJECT_TYPES, CDCREProvenanceService
from src.cdcre.repository import (
    PG16_AUTH_ENV_VAR,
    CDCRERepository,
    DatabaseEnvironmentGuardError,
    RepositoryMode,
)
from src.contracts.cdcre import (
    AmbiguityStatus,
    CDCREOutputContract,
    CoverageStatus,
)
from src.research.cdcre import research_player_profile

from tests.fixtures.cdcre_career_fixtures import (
    SYNTHETIC_NONEXISTENT_PLAYER_UUID,
)

# ==============================================================================
# 1. AC-10 Protocol Boundary Verification
# ==============================================================================


class TestAC10ProtocolBoundaries:
    """Verify strict parameter boundaries enforcing AC-10."""

    @pytest.mark.parametrize(
        "invalid_arg",
        [None, 12345, True, ["Sanju"], {"name": "Sanju"}, 3.14],
        ids=["None", "int", "bool", "list", "dict", "float"],
    )
    def test_discover_candidates_rejects_non_string_types(self, invalid_arg: Any) -> None:
        """discover_candidates strictly requires str and rejects all non-string inputs."""
        engine = get_cdcre_engine()
        with pytest.raises(TypeError, match="str"):
            discover_candidates(invalid_arg)
        with pytest.raises(TypeError, match="str"):
            engine.discover_candidates(invalid_arg)

    def test_discover_candidates_rejects_keyword_arguments(self) -> None:
        """discover_candidates must not accept player_id or other keyword arguments (AC-10)."""
        engine = get_cdcre_engine()
        with pytest.raises(TypeError, match="player_id"):
            engine.discover_candidates("Sanju Samson", player_id=uuid4())

    @pytest.mark.parametrize(
        "invalid_uuid",
        [None, "not-a-uuid", 12345, "a4cc73aa", ["40000000-0000-0000-0000-000000000001"]],
        ids=["None", "invalid-str", "int", "hex-str", "list"],
    )
    def test_discover_career_rejects_non_uuid_instances(self, invalid_uuid: Any) -> None:
        """discover_career strictly requires a valid UUID instance and rejects other types (AC-10)."""
        engine = get_cdcre_engine()
        with pytest.raises(TypeError, match="UUID"):
            discover_career(invalid_uuid)
        with pytest.raises(TypeError, match="UUID"):
            engine.discover_career(invalid_uuid)

    def test_research_player_profile_rejects_invalid_raw_name(self) -> None:
        """research_player_profile rejects non-string and whitespace-only queries."""
        with pytest.raises(TypeError, match="raw_name as str"):
            research_player_profile(12345)  # type: ignore[arg-type]

        with pytest.raises(ValueError, match="empty or whitespace"):
            research_player_profile("   ")

    def test_engine_research_player_rejects_missing_both_arguments(self) -> None:
        """engine.research_player must raise ValueError if neither name nor UUID is provided."""
        engine = get_cdcre_engine()
        with pytest.raises(ValueError, match="Either raw_name or canonical_player_id"):
            engine.research_player(raw_name=None, canonical_player_id=None)


# ==============================================================================
# 2. Strict DDL Compliance: chk_subject_type in Provenance
# ==============================================================================


class TestProvenanceDDLSubjectTypeCompliance:
    """Verify CDCREProvenanceService adheres strictly to PostgreSQL 16 chk_subject_type."""

    @pytest.mark.parametrize(
        "invalid_subject_type",
        [
            "salary_cap",
            "draft_pick",
            "social_media",
            "contract_valuation",
            "scouting_report",
            "random_claim",
            "",
            "unknown",
        ],
    )
    def test_unauthorized_subject_type_violates_chk_subject_type(
        self,
        invalid_subject_type: str,
    ) -> None:
        """Any subject_type outside the 6 allowed DDL values strictly raises ValueError."""
        prov = CDCREProvenanceService()
        dummy_id = str(uuid4())

        with pytest.raises(ValueError, match="chk_subject_type"):
            prov.record_verification(
                subject_type=invalid_subject_type,
                subject_id=dummy_id,
                evidence_tier=1,
                license_str="Official",
            )

    @pytest.mark.parametrize("valid_subject_type", sorted(VALID_SUBJECT_TYPES))
    def test_valid_subject_types_succeed(self, valid_subject_type: str) -> None:
        """All 6 valid PostgreSQL 16 subject types succeed without error."""
        prov = CDCREProvenanceService()
        dummy_id = str(uuid4())

        v_id = prov.record_verification(
            subject_type=valid_subject_type,
            subject_id=dummy_id,
            evidence_tier=1,
            license_str="CC-BY-4.0",
        )
        assert isinstance(v_id, str)
        # Verify valid UUID format
        assert UUID(v_id)

    def test_invalid_evidence_tier_rejected(self) -> None:
        """Evidence tier less than 1 raises ValueError."""
        prov = CDCREProvenanceService()
        dummy_id = str(uuid4())

        with pytest.raises(ValueError, match="evidence_tier"):
            prov.record_verification(
                subject_type="match_performance",
                subject_id=dummy_id,
                evidence_tier=0,
                license_str="Official",
            )


# ==============================================================================
# 3. AC-11 Mandatory Invariant: Missing Datasets
# ==============================================================================


class TestAC11MissingDatasetsNegativeVerification:
    """Verify missing datasets emit DATASET_UNAVAILABLE and never fabricate non-participation."""

    def test_missing_dataset_with_zero_appearances_emits_dataset_unavailable(self) -> None:
        """AC-11: has_dataset=False MUST override appearances=0 and emit DATASET_UNAVAILABLE."""
        status = evaluate_coverage(has_dataset=False, appearances=0)
        assert status == CoverageStatus.DATASET_UNAVAILABLE

    def test_missing_dataset_with_none_appearances_emits_dataset_unavailable(self) -> None:
        """AC-11: has_dataset=False with appearances=None emits DATASET_UNAVAILABLE."""
        status = evaluate_coverage(has_dataset=False, appearances=None)
        assert status == CoverageStatus.DATASET_UNAVAILABLE

    def test_negative_appearances_strictly_rejected(self) -> None:
        """Negative appearances value raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            evaluate_coverage(has_dataset=True, appearances=-1)


# ==============================================================================
# 4. Non-Existent Player Queries & Zero Fabrication
# ==============================================================================


class TestNonExistentPlayerZeroFabrication:
    """Verify nonexistent players produce clean empty results with zero fabricated records."""

    def test_discover_career_nonexistent_uuid_returns_empty_coverage(self) -> None:
        """Querying career for an unknown UUID returns 0 appearances and no fabricated records."""
        engine = get_cdcre_engine()
        career = engine.discover_career(SYNTHETIC_NONEXISTENT_PLAYER_UUID)

        assert career.canonical_player_id == SYNTHETIC_NONEXISTENT_PLAYER_UUID
        assert career.competitions_evaluated_count == 0
        assert len(career.competitions_covered) == 0
        assert len(career.career_gaps) == 0

    def test_discover_candidates_unknown_name_returns_none(self) -> None:
        """Querying candidates for a non-existent player name returns AmbiguityStatus.NONE."""
        engine = get_cdcre_engine()
        result = engine.discover_candidates("NonExistentPlayer_XYZ_999")

        assert result.ambiguity_status == AmbiguityStatus.NONE
        assert result.collision_detected is False
        assert len(result.candidates) == 0

    def test_research_player_profile_unknown_player_returns_no_candidates(self) -> None:
        """research_player_profile for unknown player returns NO_CANDIDATES_FOUND."""
        result = research_player_profile("CompletelyUnknownPlayer_ZZZ")

        assert isinstance(result, CDCREOutputContract)
        assert result.candidate_discovery is not None
        assert result.candidate_discovery.ambiguity_status == AmbiguityStatus.NONE
        assert result.career_coverage is None
        assert result.metadata["status"] == "NO_CANDIDATES_FOUND"


# ==============================================================================
# 5. Pydantic v2 Contract Invariants
# ==============================================================================


class TestPydanticContractInvariants:
    """Verify Pydantic v2 strict schema validation and immutability."""

    def test_contract_extra_fields_forbidden(self) -> None:
        """Attempting to inject undeclared extra fields raises ValidationError."""
        with pytest.raises(pydantic.ValidationError):
            CDCREOutputContract(
                candidate_discovery=None,
                career_coverage=None,
                injected_adversarial_field="payload",  # type: ignore[call-arg]
            )

    def test_contract_assignment_validation(self) -> None:
        """Mutating fields with incompatible types raises ValidationError."""
        contract = CDCREOutputContract(
            candidate_discovery=None,
            career_coverage=None,
            metadata={},
        )
        with pytest.raises(pydantic.ValidationError):
            contract.metadata = "not-a-dict"  # type: ignore[assignment]


# ==============================================================================
# 6. Repository Negative Verification & Security Invariants
# ==============================================================================


class TestRepositorySecurityAndGuardBoundaries:
    """Verify repository SQL injection interception and environment guard boundaries."""

    @pytest.mark.parametrize(
        "hostile_vector",
        [
            "SELECT * FROM player_competition_history WHERE player_id = '1' OR '1'='1'",
            "SELECT * FROM player_competition_history WHERE season = '2024' OR 1=1",
            "SELECT * FROM player_competition_history WHERE season = '2024' OR 42=42",
            "SELECT * FROM player_competition_history WHERE season = '2024' AND 1=1",
            "SELECT * FROM player_competition_history WHERE season = '2024' AND 99=99",
            "SELECT * FROM player_competition_history; DROP TABLE player_competition_history;",
            "SELECT * FROM player_competition_history; DELETE FROM player_competition_history;",
            "SELECT * FROM player_competition_history; TRUNCATE player_competition_history;",
            "SELECT * FROM player_competition_history; UPDATE player_competition_history SET appearances = 0;",
            "SELECT * FROM player_competition_history; INSERT INTO player_competition_history VALUES ('fake');",
            "SELECT * FROM player_competition_history; ALTER TABLE player_competition_history DROP COLUMN appearances;",
            "SELECT * FROM player_competition_history; CREATE TABLE hostile (id int);",
            "SELECT * FROM player_competition_history; EXEC sp_help;",
            "SELECT * FROM player_competition_history; EXECUTE sp_help;",
            "EXEC sp_executesql 'SELECT 1'",
            "EXECUTE master..xp_cmdshell 'dir'",
            "SELECT * FROM player_competition_history --",
            "SELECT * FROM player_competition_history UNION SELECT * FROM users",
        ],
    )
    def test_unparameterized_injection_vector_rejected(self, hostile_vector: str) -> None:
        """Unparameterized query containing malicious SQL syntax raises ValueError."""
        repo = CDCRERepository()
        with pytest.raises(ValueError, match="SQL Injection vector detected"):
            repo.execute_parameterized(hostile_vector, params=None)

    def test_parameterized_query_safely_binds_adversarial_strings(self) -> None:
        """Parameterized queries allow adversarial strings safely without executing injection."""
        repo = CDCRERepository()
        adversarial_str = "'; DROP TABLE player_competition_history; --"
        res = repo.execute_parameterized(
            "SELECT * FROM player_competition_history WHERE player_name = $1",
            (adversarial_str,),
        )
        assert res is True

    @pytest.mark.parametrize(
        "method_name",
        [
            "get_by_player_id",
            "get_by_history_id",
            "delete_record",
            "delete_by_player_id",
        ],
    )
    def test_unauthorized_database_mode_guards_data_methods(
        self,
        monkeypatch: pytest.MonkeyPatch,
        method_name: str,
    ) -> None:
        """Calling database-mode methods without environment authorization raises DatabaseEnvironmentGuardError."""
        monkeypatch.delenv(PG16_AUTH_ENV_VAR, raising=False)
        repo = CDCRERepository(mode=RepositoryMode.DATABASE, db_client=None)

        target_method = getattr(repo, method_name)
        with pytest.raises(DatabaseEnvironmentGuardError, match="PostgreSQL Environment Guard"):
            target_method(uuid4())
