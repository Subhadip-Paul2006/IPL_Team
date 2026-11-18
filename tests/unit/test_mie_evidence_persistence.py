"""Evidence persistence and cap verification regressions (PRD NFR-03, R13, R15, R18)."""

from __future__ import annotations

import csv
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import pytest
from src.contracts.cdcre import (
    AmbiguityStatus,
    CandidateDiscoveryResult,
    CandidatePlayerRecord,
)
from src.contracts.provenance import DataSource, SourceRecord, VerificationRecord
from src.contracts.pvre import PlayerCappedStatus, VerificationStatus
from src.database.client import SupabaseClientFactory
from src.mie.cap_status import CapSourceAuthority, CapStatusEvidenceVerifier
from src.mie.contracts import CappedStatusEvidence, PlayerIntelligenceRequest
from src.mie.data_provider import (
    LocalCricsheetProvider,
    PlayerMatchEvidence,
    SourcePayloadChangedError,
)
from src.mie.evidence_repository import (
    InMemoryEvidenceRepository,
    SupabaseEvidenceRepository,
)
from src.mie.orchestrator import MotherIntelligenceEngine
from src.mie.profile_gen import ProfileGeneratorService


def _fixture_archive(tmp_path: Path, suffix: str = "") -> tuple[Path, str, Path]:
    workspace = Path(__file__).resolve().parents[2]
    source_dir = workspace / "datasets" / "ipl_male_json"
    source_file = next(source_dir.glob("*.json"))
    payload = json.loads(source_file.read_text(encoding="utf-8"))
    registry = payload.get("info", {}).get("registry", {}).get("people", {})
    player_name = next(iter(registry), None)
    if player_name is None:
        player_name = next(iter(payload["info"]["players"].values()))[0]
    destination = tmp_path / f"ipl_male_json{suffix}"
    destination.mkdir()
    target = destination / source_file.name
    shutil.copy2(source_file, target)
    shutil.copy2(source_dir / "LICENSE.txt", destination / "LICENSE.txt")
    shutil.copy2(source_dir / "README.txt", destination / "README.txt")
    return tmp_path, player_name, target


class _FakeResponse:
    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data


class _FakeQuery:
    def __init__(self, client: _FakeSupabaseClient, table: str) -> None:
        self.client = client
        self.table_name = table
        self.action = "select"
        self.values: dict[str, Any] = {}
        self.filters: dict[str, str] = {}
        self.limit_count: int | None = None

    def select(self, _columns: str) -> _FakeQuery:
        self.action = "select"
        return self

    def eq(self, field: str, value: str) -> _FakeQuery:
        self.filters[field] = value
        return self

    def limit(self, _limit: int) -> _FakeQuery:
        self.limit_count = _limit
        return self

    def insert(self, values: dict[str, Any]) -> _FakeQuery:
        self.action = "insert"
        self.values = values
        return self

    def execute(self) -> _FakeResponse:
        rows = self.client.rows.setdefault(self.table_name, [])
        if self.action == "select":
            selected = [
                row
                for row in rows
                if all(str(row.get(key)) == value for key, value in self.filters.items())
            ]
            return _FakeResponse(
                selected[: self.limit_count] if self.limit_count is not None else selected
            )
        if self.table_name == "data_sources" and any(
            row["source_name"] == self.values["source_name"] for row in rows
        ):
            raise ValueError("uq_data_sources_name")
        if self.table_name == "source_records" and any(
            row["source_id"] == self.values["source_id"]
            and row["external_entity_id"] == self.values["external_entity_id"]
            and row["payload_sha256"] == self.values["payload_sha256"]
            for row in rows
        ):
            raise ValueError("uq_source_payload_hash")
        rows.append(self.values.copy())
        return _FakeResponse([self.values.copy()])


class _FakeSupabaseClient:
    def __init__(self) -> None:
        self.rows: dict[str, list[dict[str, Any]]] = {}

    def table(self, table_name: str) -> _FakeQuery:
        return _FakeQuery(self, table_name)


def _licensed_source(
    repo: InMemoryEvidenceRepository, license_status: str = "VERIFIED"
) -> DataSource:
    return repo.register_data_source(
        DataSource(
            source_name="Test authorized senior match archive",
            source_type="JSON Feed",
            license_type="ODC-By v1.0",
            license_status=license_status,
            license_evidence="fixture LICENSE.txt",
            update_cadence="test fixture",
            data_steward="test authority",
        )
    )


def _verified_cap_fixture(
    repo: InMemoryEvidenceRepository,
    player_id: UUID,
    *,
    subject_id: UUID | None = None,
    claim: dict[str, object] | None = None,
    license_status: str = "VERIFIED",
    retrieval_ts: datetime | None = None,
) -> tuple[SourceRecord, VerificationRecord, CapSourceAuthority]:
    source = _licensed_source(repo, license_status)
    record = repo.create_source_record(
        SourceRecord(
            source_id=source.source_id,
            external_entity_id="fixture/appearance.json",
            raw_payload={
                "cap_evidence": claim
                or {
                    "claim_type": "senior_international_appearance",
                    "player_id": str(player_id),
                    "competition": "ICC Cricket World Cup",
                    "appearance_confirmed": True,
                }
            },
            payload_sha256="a" * 64,
            processing_status="Parsed",
        )
    )
    verification = VerificationRecord(
        subject_type="career_participation",
        subject_id=subject_id or player_id,
        source_record_id=record.record_id,
        data_source_id=source.source_id,
        evidence_tier=2,
        license=source.license_type,
        verification_status="VERIFIED",
        source_provider="test-only registered authority",
        confidence=0.9,
        retrieval_ts=retrieval_ts or datetime.now(UTC),
    )
    repo.add_verification_record(verification)
    authority = CapSourceAuthority(
        authority_id="test-only-reviewed-authority",
        source_ids=frozenset({source.source_id}),
        senior_competitions=frozenset({"ICC Cricket World Cup", "ICC Men's T20 World Cup"}),
    )
    return record, verification, authority


def test_supabase_repository_persists_and_resolves_real_schema_ids() -> None:
    """Existing source table unique constraints make registration idempotent (NFR-03)."""
    repo = SupabaseEvidenceRepository(_FakeSupabaseClient())
    source = repo.register_data_source(
        DataSource(
            source_name="CricSheet fixture source",
            source_type="JSON Feed",
            license_type="ODC-By v1.0",
            license_status="VERIFIED",
            license_evidence="datasets/fixture/LICENSE.txt",
            update_cadence="snapshot",
            data_steward="CricSheet",
        )
    )
    source_again = repo.register_data_source(source.model_copy(update={"source_id": uuid4()}))
    assert source_again.source_id == source.source_id

    record = SourceRecord(
        source_id=source.source_id,
        external_entity_id="ipl_male_json/match.json",
        raw_payload={"info": {"season": 2024}},
        payload_sha256="b" * 64,
        processing_status="Parsed",
    )
    inserted = repo.create_source_record(record)
    repeated = repo.create_source_record(record.model_copy(update={"record_id": uuid4()}))
    assert inserted.record_id == repeated.record_id
    assert repo.get_source_record(inserted.record_id) == inserted
    assert inserted.payload_sha256 == "b" * 64


def test_local_ingestion_registers_source_and_is_idempotent(tmp_path: Path) -> None:
    """An unchanged read resolves to its actual repository record and original timestamp."""
    datasets_dir, name, _ = _fixture_archive(tmp_path)
    repo = InMemoryEvidenceRepository()
    provider = LocalCricsheetProvider(datasets_dir, evidence_repository=repo)
    candidate = provider.search_players(name).candidates[0]
    assert candidate.player_id is not None

    first = provider.player_matches(candidate.player_id)
    second = provider.player_matches(candidate.player_id)
    assert first and first[0].source_record_id is not None
    assert first[0].source_record_id == second[0].source_record_id
    assert first[0].ingestion_timestamp == second[0].ingestion_timestamp
    assert (
        first[0].source_record_key
        == f"ipl_male_json/{first[0].match['source_record_key'].split('/')[-1]}"
    )
    source_record = repo.get_source_record(first[0].source_record_id)
    assert source_record is not None
    assert source_record.payload_sha256 == first[0].payload_sha256
    assert source_record.processing_status == "Parsed"
    assert source_record.raw_payload


def test_payload_hash_change_after_index_fails_closed(tmp_path: Path) -> None:
    """The provider does not treat a modified file as the indexed snapshot."""
    datasets_dir, name, match_path = _fixture_archive(tmp_path)
    provider = LocalCricsheetProvider(datasets_dir)
    player_id = provider.search_players(name).candidates[0].player_id
    assert player_id is not None
    payload = json.loads(match_path.read_text(encoding="utf-8"))
    payload["info"]["city"] = "Changed after index"
    match_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SourcePayloadChangedError, match="changed after index"):
        provider.player_matches(player_id)


def test_payload_hash_change_since_previous_ingestion_fails_closed(tmp_path: Path) -> None:
    """A new process cannot silently accept changed bytes under the same relative key."""
    datasets_dir, name, match_path = _fixture_archive(tmp_path)
    repo = InMemoryEvidenceRepository()
    first_provider = LocalCricsheetProvider(datasets_dir, repo)
    player_id = first_provider.search_players(name).candidates[0].player_id
    assert player_id is not None
    original_records = first_provider.player_matches(player_id)
    assert original_records

    payload = json.loads(match_path.read_text(encoding="utf-8"))
    payload["info"]["city"] = "Changed between ingestions"
    match_path.write_text(json.dumps(payload), encoding="utf-8")
    second_provider = LocalCricsheetProvider(datasets_dir, repo)
    second_player_id = second_provider.search_players(name).candidates[0].player_id
    assert second_player_id == player_id
    with pytest.raises(SourcePayloadChangedError, match="Persisted Cricsheet digest changed"):
        second_provider.player_matches(player_id)


def test_name_only_candidate_has_no_canonical_identity(tmp_path: Path) -> None:
    """A display name without a Cricsheet registry key cannot mint a player UUID."""
    datasets_dir, name, match_path = _fixture_archive(tmp_path)
    payload = json.loads(match_path.read_text(encoding="utf-8"))
    payload["info"].pop("registry", None)
    match_path.write_text(json.dumps(payload), encoding="utf-8")
    provider = LocalCricsheetProvider(datasets_dir)
    result = provider.search_players(name)
    assert len(result.candidates) == 1
    assert result.candidates[0].player_id is None


def test_same_name_with_distinct_registry_keys_is_ambiguous(tmp_path: Path) -> None:
    """Separate stable source keys with identical names stay separate candidates (R15)."""
    datasets_dir, name, first_path = _fixture_archive(tmp_path)
    second_dir = tmp_path / "bbl_male_json"
    second_dir.mkdir()
    shutil.copy2(first_path.parent / "LICENSE.txt", second_dir / "LICENSE.txt")
    second_path = second_dir / first_path.name
    payload = json.loads(first_path.read_text(encoding="utf-8"))
    registry = payload.get("info", {}).get("registry", {}).get("people", {})
    for player_name in registry:
        registry[player_name] = "b" * 32
    second_path.write_text(json.dumps(payload), encoding="utf-8")
    provider = LocalCricsheetProvider(datasets_dir)
    result = provider.search_players(name)
    assert len(result.candidates) >= 2
    assert result.collision_detected


def test_aliases_share_identity_only_when_source_registry_key_matches(tmp_path: Path) -> None:
    """A recorded alternate name joins only through its stable source registry key."""
    datasets_dir, name, first_path = _fixture_archive(tmp_path)
    first = LocalCricsheetProvider(datasets_dir)
    original = first.search_players(name).candidates[0]
    assert original.player_id is not None

    second_dir = tmp_path / "bbl_male_json"
    second_dir.mkdir()
    shutil.copy2(first_path.parent / "LICENSE.txt", second_dir / "LICENSE.txt")
    second_path = second_dir / first_path.name
    payload = json.loads(first_path.read_text(encoding="utf-8"))
    registry = payload["info"]["registry"]["people"]
    stable_id = registry.pop(name)
    alias = "Recorded Alternate Alias"
    registry[alias] = stable_id
    for team, names in payload["info"]["players"].items():
        payload["info"]["players"][team] = [alias if value == name else value for value in names]
    second_path.write_text(json.dumps(payload), encoding="utf-8")

    provider = LocalCricsheetProvider(datasets_dir)
    alias_result = provider.search_players(alias)
    assert len(alias_result.candidates) == 1
    assert alias_result.candidates[0].player_id == original.player_id


def test_verified_positive_cap_requires_registered_source_and_linked_verification() -> None:
    """A valid positive appearance may verify only through the configured test authority."""
    repo = InMemoryEvidenceRepository()
    player_id = uuid4()
    record, verification, authority = _verified_cap_fixture(repo, player_id)
    evidence = CappedStatusEvidence(
        status=PlayerCappedStatus.CAPPED,
        verification_status=VerificationStatus.VERIFIED,
        source_record_ids=[str(record.record_id)],
        verification_record_ids=[str(verification.verification_id)],
        provider_authority_id=authority.authority_id,
    )
    verifier = CapStatusEvidenceVerifier(repo, {authority.authority_id: authority})
    assert verifier.verify(player_id, evidence).status == PlayerCappedStatus.CAPPED


@pytest.mark.parametrize(
    ("mutate", "authority_registered"),
    [
        ("invalid_verification_id", True),
        ("wrong_identity", True),
        ("wrong_authority", False),
        ("missing_history", True),
        ("missing_source_record", True),
    ],
)
def test_untrusted_or_unlinked_cap_claims_remain_unknown(
    mutate: str, authority_registered: bool
) -> None:
    """Unknown providers, invalid IDs, identity mismatches, and missing history fail closed."""
    repo = InMemoryEvidenceRepository()
    player_id = uuid4()
    record, verification, authority = _verified_cap_fixture(
        repo,
        player_id,
        subject_id=uuid4() if mutate == "wrong_identity" else None,
        claim=(
            {"claim_type": "other", "player_id": str(player_id)}
            if mutate == "missing_history"
            else None
        ),
    )
    evidence = CappedStatusEvidence(
        status=PlayerCappedStatus.CAPPED,
        verification_status=VerificationStatus.VERIFIED,
        source_record_ids=[str(uuid4() if mutate == "missing_source_record" else record.record_id)],
        verification_record_ids=[
            str(uuid4() if mutate == "invalid_verification_id" else verification.verification_id)
        ],
        provider_authority_id=(
            "not-registered" if mutate == "wrong_authority" else authority.authority_id
        ),
    )
    authorities = {authority.authority_id: authority} if authority_registered else {}
    result = CapStatusEvidenceVerifier(repo, authorities).verify(player_id, evidence)
    assert result.status == PlayerCappedStatus.UNVERIFIED
    assert result.verification_status == VerificationStatus.UNKNOWN


def test_uncapped_requires_complete_current_coverage() -> None:
    """A positive appearance archive or partial coverage cannot verify uncapped status (R13)."""
    repo = InMemoryEvidenceRepository()
    player_id = uuid4()
    record, verification, authority = _verified_cap_fixture(repo, player_id)
    verifier = CapStatusEvidenceVerifier(repo, {authority.authority_id: authority})
    evidence = CappedStatusEvidence(
        status=PlayerCappedStatus.UNCAPPED,
        verification_status=VerificationStatus.VERIFIED,
        source_record_ids=[str(record.record_id)],
        verification_record_ids=[str(verification.verification_id)],
        provider_authority_id=authority.authority_id,
    )
    result = verifier.verify(player_id, evidence)
    assert result.status == PlayerCappedStatus.UNVERIFIED


@pytest.mark.parametrize("failure", ["license", "stale"])
def test_cap_evidence_requires_permitted_fresh_source(failure: str) -> None:
    """Unlicensed or stale rows are not trusted even when their IDs resolve."""
    from datetime import timedelta

    repo = InMemoryEvidenceRepository()
    player_id = uuid4()
    record, verification, authority = _verified_cap_fixture(
        repo,
        player_id,
        license_status="RESTRICTED" if failure == "license" else "VERIFIED",
        retrieval_ts=(datetime.now(UTC) - timedelta(days=500) if failure == "stale" else None),
    )
    evidence = CappedStatusEvidence(
        status=PlayerCappedStatus.CAPPED,
        verification_status=VerificationStatus.VERIFIED,
        source_record_ids=[str(record.record_id)],
        verification_record_ids=[str(verification.verification_id)],
        provider_authority_id=authority.authority_id,
    )
    result = CapStatusEvidenceVerifier(repo, {authority.authority_id: authority}).verify(
        player_id, evidence
    )
    assert result.status == PlayerCappedStatus.UNVERIFIED


def test_conflicting_cap_verification_is_preserved() -> None:
    """Existing conflict rows prevent a positive result and stay visibly conflicting."""
    repo = InMemoryEvidenceRepository()
    player_id = uuid4()
    record, verification, authority = _verified_cap_fixture(repo, player_id)
    conflict = VerificationRecord(
        subject_type="career_participation",
        subject_id=player_id,
        source_record_id=record.record_id,
        data_source_id=record.source_id,
        license="ODC-By v1.0",
        verification_status="CONFLICT",
    )
    repo.add_verification_record(conflict)
    evidence = CappedStatusEvidence(
        status=PlayerCappedStatus.CAPPED,
        verification_status=VerificationStatus.VERIFIED,
        source_record_ids=[str(record.record_id)],
        verification_record_ids=[str(verification.verification_id)],
        provider_authority_id=authority.authority_id,
    )
    result = CapStatusEvidenceVerifier(repo, {authority.authority_id: authority}).verify(
        player_id, evidence
    )
    assert result.verification_status == VerificationStatus.CONFLICT
    assert result.conflicting_source_ids


def test_injected_provider_cannot_self_assert_trusted_authority() -> None:
    """MIE has no production authority configured, so injected claims remain unverified."""
    player_id = uuid4()

    class OnePlayerProvider:
        def search_players(self, query: str) -> CandidateDiscoveryResult:
            return CandidateDiscoveryResult(
                raw_name_query=query,
                ambiguity_status=AmbiguityStatus.SINGLE_CORROBORATED,
                candidates=[
                    CandidatePlayerRecord(
                        player_id=player_id,
                        canonical_name="Example Player",
                        source_id="test-provider",
                    )
                ],
            )

        def player_matches(self, resolved_id: UUID) -> tuple[()]:
            del resolved_id
            return ()

        def availability(self) -> dict[str, str]:
            return {"provenance": "test fixture", "cap_status": "unavailable"}

        def player_coverage(
            self,
            resolved_id: UUID | None,
            evidence: tuple[PlayerMatchEvidence, ...],
        ) -> dict[str, object]:
            del resolved_id
            return {"records_observed": len(evidence), "source_completeness": "PARTIAL"}

    class ClaimingProvider:
        def assess(self, player_id: UUID) -> CappedStatusEvidence:
            del player_id
            return CappedStatusEvidence(
                status=PlayerCappedStatus.CAPPED,
                verification_status=VerificationStatus.VERIFIED,
                source_record_ids=[str(uuid4())],
                verification_record_ids=[str(uuid4())],
                provider_authority_id="self-asserted-provider-name",
            )

    report = MotherIntelligenceEngine(
        data_provider=OnePlayerProvider(), capped_status_provider=ClaimingProvider()
    ).request_player_intelligence("Example Player")
    assert report.player_id == player_id
    assert report.verification.player_capped_status == PlayerCappedStatus.UNVERIFIED


def test_caller_supplied_fake_cap_evidence_is_rejected() -> None:
    """A request cannot inject status or database record identifiers (R13)."""
    fake = CappedStatusEvidence(
        status=PlayerCappedStatus.UNCAPPED,
        verification_status=VerificationStatus.VERIFIED,
        source_record_ids=[str(uuid4())],
        verification_record_ids=[str(uuid4())],
        provider_authority_id="caller",
    )
    with pytest.raises(ValueError, match="trusted internal provider"):
        PlayerIntelligenceRequest(player_query="Example", capped_status_evidence=fake)


def test_normal_search_exports_persisted_provenance_and_coverage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ordinary search uses local evidence and exports repository IDs and gaps (AC-10)."""
    from src.cmie.weather_service import WeatherService

    def reject_weather(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise AssertionError("offline MIE search must not call the weather provider")

    monkeypatch.setattr(WeatherService, "_fetch_open_meteo_data", reject_weather)
    datasets_dir, name, _ = _fixture_archive(tmp_path)
    repository = SupabaseEvidenceRepository(_FakeSupabaseClient())
    provider = LocalCricsheetProvider(datasets_dir, repository)
    mie = MotherIntelligenceEngine(
        data_provider=provider,
    )
    report = mie.request_player_intelligence(name)
    assert report.player_id is not None
    assert report.local_source_evidence
    assert report.context.matches
    match_rec = report.context.matches[0]
    assert match_rec.venue is not None
    evidence_id = report.local_source_evidence[0]["source_record_id"]
    source_key = provider.source_identity_key(report.player_id)
    assert source_key is not None
    assert mie.pire.resolver.external_id_index[("cricsheet_local_odc_by", source_key)] == str(
        report.player_id
    )
    assert evidence_id in {str(item) for item in report.provenance.source_record_ids}
    assert report.provenance.attribution_notices
    assert report.data_coverage.records_observed > 0
    assert report.data_coverage.source_completeness == "PARTIAL_SNAPSHOT"
    assert report.data_coverage.missing_periods is None
    assert report.data_coverage.derived_performance_source_record_ids

    json_export = ProfileGeneratorService.export_to_json(report)
    csv_export = ProfileGeneratorService.export_to_csv(report)
    assert evidence_id in json_export
    assert "ODC Attribution License (ODC-By)" in json_export
    assert evidence_id in csv_export
    assert "DATA_COVERAGE,Source Completeness,PARTIAL_SNAPSHOT" in csv_export
    assert list(csv.reader(csv_export.splitlines()))


def test_actual_mie_local_evidence_remains_partial_without_database() -> None:
    """Default MIE search does not pretend in-process evidence is durable."""
    mie = MotherIntelligenceEngine()
    assert mie.evidence_repository is None
    assert (
        "durable source_records are not configured"
        in mie.data_provider.availability()["provenance"]
    )


def test_application_persistence_requires_explicit_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The ordinary app path avoids database clients unless the setting is enabled."""
    from app.streamlit_app import _load_services

    settings = SimpleNamespace(mie_evidence_persistence_enabled=False)
    monkeypatch.setattr("src.config.settings.get_settings", lambda: settings)
    monkeypatch.setattr(
        SupabaseClientFactory,
        "create_client_service",
        lambda _self: (_ for _ in ()).throw(AssertionError("database must stay offline")),
    )
    offline_services = _load_services()
    assert offline_services["mie"].evidence_repository is None

    enabled_settings = SimpleNamespace(
        mie_evidence_persistence_enabled=True,
        supabase_url="https://example.invalid",
        supabase_service_role_key="test-key",
    )
    monkeypatch.setattr("src.config.settings.get_settings", lambda: enabled_settings)
    client = _FakeSupabaseClient()
    monkeypatch.setattr(SupabaseClientFactory, "create_client_service", lambda _self: client)
    persistent_services = _load_services()
    assert isinstance(persistent_services["mie"].evidence_repository, SupabaseEvidenceRepository)
