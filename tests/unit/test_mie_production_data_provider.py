"""Production provider contract coverage (PRD AC-10/11/24, Rules R2/R13/R18)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from src.contracts.cdcre import (
    AmbiguityStatus,
    CandidateDiscoveryResult,
    CandidatePlayerRecord,
)
from src.contracts.pvre import PlayerCappedStatus, VerificationStatus
from src.mie.contracts import CappedStatusEvidence, PlayerIntelligenceRequest
from src.mie.data_provider import LocalCricsheetProvider, UnavailableCappedStatusProvider
from src.mie.orchestrator import MotherIntelligenceEngine


class StubProvider:
    """Deterministic provider fixture for MIE route outcome tests."""

    def __init__(self, candidates: list[CandidatePlayerRecord]) -> None:
        self.candidates = candidates

    def search_players(self, query: str) -> CandidateDiscoveryResult:
        return CandidateDiscoveryResult(
            raw_name_query=query,
            ambiguity_status=(
                AmbiguityStatus.NONE
                if not self.candidates
                else AmbiguityStatus.SINGLE_CORROBORATED
                if len(self.candidates) == 1
                else AmbiguityStatus.MULTIPLE
            ),
            candidates=self.candidates,
            collision_detected=len(self.candidates) > 1,
        )

    def player_matches(self, player_id: UUID) -> tuple[()]:
        del player_id
        return ()

    def availability(self) -> dict[str, str]:
        return {
            "identity": "fixture",
            "performance": "no records",
            "cap_status": "unavailable",
        }


class ConflictingCapProvider:
    """Trusted-provider fixture representing conflicting upstream appearance records."""

    def assess(self, player_id: UUID) -> CappedStatusEvidence:
        del player_id
        return CappedStatusEvidence(
            status=PlayerCappedStatus.UNVERIFIED,
            verification_status=VerificationStatus.CONFLICT,
            conflicting_source_ids=["source-a", "source-b"],
        )


def _single_snapshot(tmp_path: Path) -> tuple[Path, str]:
    """Copy one actual licensed local match payload for isolated provider tests."""
    workspace = Path(__file__).resolve().parents[2]
    source_dir = workspace / "datasets" / "ipl_male_json"
    source_path = next(source_dir.glob("*.json"))
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    info = payload["info"]
    player_name = next(iter(info.get("registry", {}).get("people", {})), None)
    if player_name is None:
        player_name = next(iter(info["players"].values()))[0]
    destination = tmp_path / "ipl_male_json"
    destination.mkdir()
    shutil.copy2(source_path, destination / source_path.name)
    shutil.copy2(source_dir / "LICENSE.txt", destination / "LICENSE.txt")
    shutil.copy2(source_dir / "README.txt", destination / "README.txt")
    return tmp_path, player_name


def test_local_provider_reads_actual_licensed_match_snapshot(tmp_path: Path) -> None:
    """A permitted local fixture yields a stable identity and traceable delivery records."""
    datasets_dir, player_name = _single_snapshot(tmp_path)
    provider = LocalCricsheetProvider(datasets_dir)

    result = provider.search_players(player_name)
    assert len(result.candidates) == 1
    player_id = result.candidates[0].player_id
    assert player_id is not None

    matches = provider.player_matches(player_id)
    assert matches
    assert all(record.payload_sha256 for record in matches)
    # Preserve the exact notice title. The notice provides no license URL or
    # retrieval timestamp, so neither value is inferred.
    assert all(record.license == "ODC Attribution License (ODC-By)" for record in matches)
    assert all(record.license_url is None and record.retrieved_at is None for record in matches)
    assert all(record.source_provider == "Cricsheet" for record in matches)
    assert all(
        record.source_url == "https://cricsheet.org/downloads/ipl_male_json.zip"
        for record in matches
    )
    assert all(record.match["external_fixture_id"] for record in matches)
    assert all(record.match["source_record_key"] == record.source_record_key for record in matches)
    assert all(record.match["payload_sha256"] == record.payload_sha256 for record in matches)
    assert matches[0].match["fixture_source"]["payload_sha256"] == matches[0].payload_sha256
    assert any(record.deliveries for record in matches)
    assert any("striker_id" in row and "runs" in row for row in matches[0].deliveries)
    assert matches[0].match["match_id"]


def test_unknown_and_multiple_provider_results_remain_unresolved() -> None:
    """Unknown and ambiguous local evidence never yields a resolved player identity."""
    empty_mie = MotherIntelligenceEngine(
        data_provider=StubProvider([]),  # type: ignore[arg-type]
    )
    unknown = empty_mie.request_player_intelligence("No Such Player")
    assert unknown.player_id is None
    assert unknown.identity["status"] == "UNRESOLVED"

    candidates = [
        CandidatePlayerRecord(
            player_id=uuid4(), canonical_name="Alex Example", source_id="fixture"
        ),
        CandidatePlayerRecord(
            player_id=uuid4(), canonical_name="Alex Example", source_id="fixture"
        ),
    ]
    ambiguous_mie = MotherIntelligenceEngine(
        data_provider=StubProvider(candidates),  # type: ignore[arg-type]
    )
    ambiguous = ambiguous_mie.request_player_intelligence("Alex Example")
    assert ambiguous.player_id is None
    assert ambiguous.candidate_discovery is not None
    assert ambiguous.candidate_discovery.collision_detected
    assert ambiguous.is_review_required


def test_normal_mie_search_uses_local_provider_and_reports_partial_evidence(
    tmp_path: Path,
) -> None:
    """The ordinary MIE request path retrieves evidence without mock_data."""
    datasets_dir, player_name = _single_snapshot(tmp_path)
    provider = LocalCricsheetProvider(datasets_dir)
    mie = MotherIntelligenceEngine(data_provider=provider)

    report = mie.request_player_intelligence(player_name)

    assert report.player_id is not None
    assert report.identity["status"] == "RESOLVED"
    assert report.local_source_evidence
    assert report.local_source_evidence[0]["license"] == "ODC Attribution License (ODC-By)"
    assert report.local_source_evidence[0]["license_url"] is None
    assert report.local_source_evidence[0]["source_provider"] == "Cricsheet"
    assert report.context.input_availability.value == "PARTIAL"
    assert report.context.execution_status.value in {"SUCCESS", "PARTIAL"}
    assert report.context.verification_status.value == "UNVERIFIED"
    assert report.context.matches
    assert report.context.matches[0].fixture_source.payload_sha256
    venue = report.context.matches[0].venue
    if venue.name is not None:
        assert venue.field_sources["name"].source_record_key == (
            report.context.matches[0].fixture_source.source_record_key
        )
    if venue.city is not None:
        assert venue.field_sources["city"].source_record_key == (
            report.context.matches[0].fixture_source.source_record_key
        )
    assert report.context.matches[0].venue.latitude is None
    assert report.context.matches[0].venue.longitude is None
    assert not report.context.matches[0].venue.boundary_size_meters
    pitch = report.context.matches[0].pitch
    assert pitch.reported_description is None
    assert pitch.soil_type is None
    assert pitch.grass_coverage is None
    assert pitch.reported_moisture is None
    assert pitch.reported_surface_state is None
    if pitch.proxy_metrics:
        assert pitch.proxy_source.tier.value == "MODEL_INFERRED"
    assert (
        report.performance.samples.delivery_events_faced
        + report.performance.samples.delivery_events_bowled
        > 0
    )
    assert "Cricsheet" in " ".join(report.provenance.primary_sources)
    assert any(
        "Open Data Commons Attribution License" in note
        for note in report.provenance.attribution_notices
    )
    assert report.data_availability["cap_status"].startswith("Unavailable")
    assert "file-scoped" in report.data_availability["identity"]
    assert report.verification.player_capped_status == PlayerCappedStatus.UNVERIFIED
    csv_export = mie.export_profile(report, format="csv")
    assert "LOCAL_SOURCE_EVIDENCE" in csv_export
    assert report.local_source_evidence[0]["payload_sha256"] in csv_export
    assert "ODC Attribution License (ODC-By)" in csv_export
    assert "PARTIAL" in csv_export
    json_export = mie.export_profile(report, format="json")
    assert "local_source_evidence" in json_export


def test_missing_performance_and_cap_sources_stay_unavailable() -> None:
    """A found identity without match rows keeps empty samples and unknown cap status."""
    candidate = CandidatePlayerRecord(
        player_id=uuid4(), canonical_name="Known Without Matches", source_id="fixture"
    )
    mie = MotherIntelligenceEngine(data_provider=StubProvider([candidate]))  # type: ignore[arg-type]
    report = mie.request_player_intelligence("Known Without Matches")

    assert report.player_id == candidate.player_id
    assert report.local_source_evidence == []
    assert report.performance.samples.matches == 0
    assert report.verification.player_capped_status == PlayerCappedStatus.UNVERIFIED
    assert "Verified international cap status and source record" in (
        report.safety_dossier.missing_evidence
    )


def test_inbound_request_cannot_assert_verified_cap_status() -> None:
    """Callers cannot promote status/source IDs to verified evidence (R13)."""
    evidence = CappedStatusEvidence(
        status=PlayerCappedStatus.UNCAPPED,
        verification_status=VerificationStatus.VERIFIED,
        source_record_ids=["caller-controlled-id"],
    )
    with pytest.raises(ValueError, match="trusted internal provider"):
        PlayerIntelligenceRequest(player_query="Example", capped_status_evidence=evidence)


def test_missing_capped_status_provider_fails_closed() -> None:
    """No configured authority returns unresolved evidence, never uncapped."""
    evidence = UnavailableCappedStatusProvider().assess(uuid4())
    assert evidence.status == PlayerCappedStatus.UNVERIFIED
    assert evidence.verification_status == VerificationStatus.UNKNOWN
    assert evidence.source_record_ids == []


def test_conflicting_internal_cap_evidence_requires_review() -> None:
    """Conflicting source-backed cap claims are preserved and escalated for review."""
    candidate = CandidatePlayerRecord(
        player_id=uuid4(), canonical_name="Conflicted Player", source_id="fixture"
    )
    mie = MotherIntelligenceEngine(
        data_provider=StubProvider([candidate]),  # type: ignore[arg-type]
        capped_status_provider=ConflictingCapProvider(),  # type: ignore[arg-type]
    )
    report = mie.request_player_intelligence("Conflicted Player")

    assert report.is_review_required
    assert "CAP_STATUS_CONFLICT" in report.safety_dossier.review_reason_codes
    assert report.safety_dossier.unresolved_claims[0]["conflicting_source_ids"] == [
        "source-a",
        "source-b",
    ]
