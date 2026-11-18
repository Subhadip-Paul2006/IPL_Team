"""Typed read-only providers for the locally licensed Cricsheet snapshot.

The local snapshot is evidence of recorded match participation only. It is not a
complete identity registry, a source-record database, or a source for negative cap
status claims.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol
from uuid import UUID

from src.contracts.cdcre import (
    AmbiguityStatus,
    CandidateDiscoveryResult,
    CandidatePlayerRecord,
)
from src.contracts.cmie import InformationKind, ProvenanceTier, SourceTrace
from src.contracts.provenance import DataSource, SourceRecord
from src.contracts.pvre import PlayerCappedStatus, VerificationStatus
from src.ingestion.cricsheet_parser import CricSheetParser, derive_uuid
from src.mie.contracts import CappedStatusEvidence
from src.mie.evidence_repository import EvidenceRepository
from src.pire.alias_registry import clean_name


@dataclass(frozen=True)
class PlayerMatchEvidence:
    """One sourced local match snapshot with its parsed match and delivery rows."""

    match: dict[str, object]
    deliveries: tuple[dict[str, object], ...]
    source_record_key: str
    payload_sha256: str
    license: str = "UNVERIFIED"
    license_url: str | None = None
    attribution: str | None = None
    source_provider: str = "Cricsheet"
    source_url: str | None = None
    retrieved_at: datetime | None = None
    source_record_id: UUID | None = None
    ingestion_timestamp: datetime | None = None


class SourcePayloadChangedError(RuntimeError):
    """Raised when a file changes after the player index recorded its digest."""


class PlayerIntelligenceProvider(Protocol):
    """Read-only source for player identity and performance evidence."""

    def search_players(self, query: str) -> CandidateDiscoveryResult: ...

    def player_matches(self, player_id: UUID) -> tuple[PlayerMatchEvidence, ...]: ...

    def fixture_availability(self) -> str: ...

    def availability(self) -> dict[str, str]: ...

    def player_coverage(
        self, player_id: UUID | None, evidence: tuple[PlayerMatchEvidence, ...]
    ) -> dict[str, object]: ...


class CappedStatusProvider(Protocol):
    """Trusted internal boundary for cap decisions; callers cannot implement evidence."""

    def assess(self, player_id: UUID) -> CappedStatusEvidence: ...


class UnavailableCappedStatusProvider:
    """Fail-closed cap provider used until a permitted authority is configured."""

    def assess(self, player_id: UUID) -> CappedStatusEvidence:
        del player_id
        return CappedStatusEvidence(
            status=PlayerCappedStatus.UNVERIFIED,
            verification_status=VerificationStatus.UNKNOWN,
        )


class LocalCricsheetProvider:
    """Read-only provider over local Cricsheet files with optional durable provenance."""

    _shared_cache: dict[
        Path,
        tuple[
            dict[str, tuple[str, set[str], set[str]]],
            dict[UUID, list[Path]],
            dict[Path, str],
            dict[UUID, str],
        ],
    ] = {}

    def __init__(
        self,
        datasets_dir: Path | str | None = None,
        evidence_repository: EvidenceRepository | None = None,
    ) -> None:
        self.datasets_dir = Path(datasets_dir or Path(__file__).resolve().parents[2] / "datasets")
        self.parser = CricSheetParser()
        self.evidence_repository = evidence_repository
        self._players: dict[str, tuple[str, set[str], set[str]]] | None = None
        self._paths_by_player: dict[UUID, list[Path]] = defaultdict(list)
        self._indexed_hashes: dict[Path, str] = {}
        self._external_id_by_player: dict[UUID, str] = {}

    def _build_player_index(self) -> None:
        if self._players is not None:
            return
        cached = self._shared_cache.get(self.datasets_dir)
        if cached is not None:
            (
                self._players,
                self._paths_by_player,
                self._indexed_hashes,
                self._external_id_by_player,
            ) = cached
            return
        players: dict[str, tuple[str, set[str], set[str]]] = {}
        paths_by_player: dict[UUID, list[Path]] = defaultdict(list)
        for path in sorted(self.datasets_dir.glob("*_json/*.json")):
            try:
                raw_bytes = path.read_bytes()
                payload = json.loads(raw_bytes)
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(payload, dict):
                continue
            self._indexed_hashes[path] = hashlib.sha256(raw_bytes).hexdigest()
            info = payload.get("info", {})
            registry = info.get("registry", {}).get("people", {})
            player_lists = info.get("players", {})
            names = set(registry) | {
                str(name) for team_names in player_lists.values() for name in team_names
            }
            competition = path.parent.name
            for name in names:
                # Never merge name-only records across files: without a provider key,
                # the same display name can represent distinct players.
                external_id = str(registry.get(name) or f"unkeyed:{competition}:{path.stem}:{name}")
                player_id = derive_uuid("player", external_id)
                if not external_id.startswith("unkeyed:"):
                    self._external_id_by_player[player_id] = external_id
                current = players.get(external_id)
                if current is None:
                    players[external_id] = (name, {competition}, {name})
                else:
                    current[1].add(competition)
                    current[2].add(name)
                if path not in paths_by_player[player_id]:
                    paths_by_player[player_id].append(path)
        self._players = players
        self._paths_by_player = paths_by_player
        self._shared_cache[self.datasets_dir] = (
            players,
            paths_by_player,
            self._indexed_hashes,
            self._external_id_by_player,
        )

    def source_identity_key(self, player_id: UUID) -> str | None:
        """Return the actual Cricsheet registry key behind a source-keyed candidate."""
        self._build_player_index()
        return self._external_id_by_player.get(player_id)

    def search_players(self, query: str) -> CandidateDiscoveryResult:
        self._build_player_index()
        needle = clean_name(query)
        candidates: list[CandidatePlayerRecord] = []
        assert self._players is not None
        for external_id, (name, competitions, aliases) in sorted(self._players.items()):
            if needle and any(clean_name(alias) == needle for alias in aliases):
                candidates.append(
                    CandidatePlayerRecord(
                        # Name-derived identifiers do not establish a stable player identity.
                        player_id=(
                            None
                            if external_id.startswith("unkeyed:")
                            else derive_uuid("player", external_id)
                        ),
                        canonical_name=name,
                        source_id="cricsheet_local_odc_by",
                        competitions=sorted(competitions),
                    )
                )
        ambiguity = (
            AmbiguityStatus.NONE
            if not candidates
            else AmbiguityStatus.SINGLE_CORROBORATED
            if len(candidates) == 1
            else AmbiguityStatus.MULTIPLE
        )
        return CandidateDiscoveryResult(
            raw_name_query=query,
            ambiguity_status=ambiguity,
            candidates=candidates,
            collision_detected=len(candidates) > 1,
        )

    def player_matches(self, player_id: UUID) -> tuple[PlayerMatchEvidence, ...]:
        self._build_player_index()
        records: list[PlayerMatchEvidence] = []
        for path in self._paths_by_player.get(player_id, []):
            try:
                raw_bytes = path.read_bytes()
                payload = json.loads(raw_bytes)
                if not isinstance(payload, dict):
                    continue
                actual_sha256 = hashlib.sha256(raw_bytes).hexdigest()
                indexed_sha256 = self._indexed_hashes.get(path)
                if indexed_sha256 is None or actual_sha256 != indexed_sha256:
                    raise SourcePayloadChangedError(
                        f"Cricsheet payload changed after index: {path.parent.name}/{path.name}"
                    )
                parsed = self.parser.parse_json(payload, external_id=path.stem)
            except (OSError, json.JSONDecodeError, ValueError):
                continue
            if parsed.is_quarantined:
                continue
            match = parsed.match.model_dump(mode="json")
            raw_info = parsed.raw_payload.get("info", {}) or {}
            season_value = raw_info.get("season")
            if isinstance(season_value, list):
                season_label = "/".join(str(part) for part in season_value)
            elif season_value is None:
                season_label = None
            else:
                season_label = str(season_value)
            match.update(
                {
                    "match_id": str(parsed.match.match_id),
                    "match_date": parsed.match.match_date.isoformat(),
                    "venue_name": parsed.venue_name or None,
                    "venue": parsed.venue_name or None,
                    "city": raw_info.get("city") or None,
                    "competition_name": path.parent.name,
                    "season_label": season_label,
                    "source_record_key": f"{path.parent.name}/{path.name}",
                    "external_fixture_id": path.stem,
                    "source_provider": "Cricsheet",
                    "source_url": self._download_url(path.parent),
                    "format_tag": parsed.match.match_type.upper(),
                    "balls_per_innings": parsed.match.innings_balls_scheduled,
                }
            )
            deliveries: list[dict[str, object]] = []
            player_was_in_match = False
            innings_by_id = {str(innings.innings_id): innings for innings in parsed.innings}
            for delivery in parsed.deliveries:
                delivery_row: dict[str, object] = delivery.model_dump(mode="json")
                innings = innings_by_id.get(str(delivery.innings_id))
                extras_type = (
                    "wide"
                    if delivery.is_wide
                    else "overstep"
                    if delivery.is_noball
                    else "byes"
                    if delivery.is_bye
                    else "legbyes"
                    if delivery.is_legbye
                    else "None"
                )
                extras_value = (
                    max(delivery.runs_wides - 1, 0)
                    if delivery.is_wide
                    else max(delivery.runs_noballs - 1, 0)
                    if delivery.is_noball
                    else delivery.runs_byes
                    if delivery.is_bye
                    else delivery.runs_legbyes
                    if delivery.is_legbye
                    else 0
                )
                delivery_row["match_id"] = str(parsed.match.match_id)
                delivery_row["player_id"] = str(player_id)
                # CPPAE's established row API uses these aliases; canonical parser fields stay.
                delivery_row["striker_id"] = str(delivery.batter_id)
                delivery_row["runs"] = delivery.runs_batter
                delivery_row["extras_type"] = extras_type
                delivery_row["extras_2_runs"] = extras_value
                delivery_row["dismissed_player_id"] = (
                    str(delivery.player_out_id) if delivery.player_out_id else ""
                )
                delivery_row["dismissal_type"] = delivery.wicket_kind or ""
                delivery_row["innings"] = innings.innings_number if innings else 1
                delivery_row["batting_team_id"] = str(innings.batting_team_id) if innings else ""
                if str(delivery_row["batter_id"]) == str(player_id) or str(
                    delivery_row["bowler_id"]
                ) == str(player_id):
                    player_was_in_match = True
                deliveries.append(delivery_row)
            if not player_was_in_match:
                continue
            relative_key = f"{path.parent.name}/{path.name}"
            license_name = self._license_type(path.parent)
            license_url = self._license_url(path.parent)
            attribution = self._attribution_notice(path.parent)
            match.update(
                {
                    "license": license_name,
                    "license_url": license_url,
                    "attribution": attribution,
                    "payload_sha256": actual_sha256,
                }
            )
            source_trace = self._match_source_trace(
                relative_key=relative_key,
                external_fixture_id=path.stem,
                payload_sha256=actual_sha256,
                license_name=license_name,
                license_url=license_url,
                attribution=attribution,
                source_url=self._download_url(path.parent),
                retrieved_at=None,
            )
            match["fixture_source"] = source_trace.model_dump(mode="json")
            for delivery_record in deliveries:
                delivery_record["source_trace"] = source_trace.model_dump(mode="json")
            source_record: SourceRecord | None = None
            source = self._data_source(path.parent) if self.evidence_repository else None
            if source is not None and (
                source.license_status != "VERIFIED" or source.license_type != license_name
            ):
                source = None
            if source is not None and self.evidence_repository is not None:
                prior_records = self.evidence_repository.get_source_records_by_key(
                    source.source_id, relative_key
                )
                if any(
                    prior.payload_sha256.lower() != actual_sha256.lower() for prior in prior_records
                ):
                    raise SourcePayloadChangedError(
                        f"Persisted Cricsheet digest changed: {relative_key}"
                    )
                source_record = self.evidence_repository.create_source_record(
                    SourceRecord(
                        source_id=source.source_id,
                        external_entity_id=relative_key,
                        raw_payload=payload,
                        payload_sha256=actual_sha256,
                        processing_status="Parsed",
                        parsed_entity_type="cricsheet_match",
                    )
                )
            if source_record is not None and source_record.ingestion_timestamp is not None:
                source_trace = source_trace.model_copy(
                    update={"ingested_at": source_record.ingestion_timestamp}
                )
                match["fixture_source"] = source_trace.model_dump(mode="json")
                for delivery_record in deliveries:
                    delivery_record["source_trace"] = source_trace.model_dump(mode="json")
            match["source_record_key"] = relative_key
            match["payload_sha256"] = actual_sha256
            if (
                source_record is not None
                and self.evidence_repository is not None
                and self.evidence_repository.durable
            ):
                match["source_record_id"] = str(source_record.record_id)
            if source_record is not None and source_record.ingestion_timestamp is not None:
                match["ingested_at"] = source_record.ingestion_timestamp.isoformat()
            records.append(
                PlayerMatchEvidence(
                    match=match,
                    deliveries=tuple(deliveries),
                    source_record_key=relative_key,
                    payload_sha256=actual_sha256,
                    license=license_name,
                    license_url=license_url,
                    attribution=attribution,
                    source_provider="Cricsheet",
                    source_url=self._download_url(path.parent),
                    retrieved_at=None,
                    source_record_id=(source_record.record_id if source_record else None),
                    ingestion_timestamp=(
                        source_record.ingestion_timestamp if source_record else None
                    ),
                )
            )
        return tuple(records)

    def fixture_availability(self) -> str:
        """The local snapshot is always partial; absent files make it unavailable."""
        if not self.datasets_dir.is_dir() or not any(self.datasets_dir.glob("*_json/*.json")):
            return "UNAVAILABLE"
        return "PARTIAL"

    def _data_source(self, competition_dir: Path) -> DataSource | None:
        """Register the dataset only when its local license notice is present."""
        if self.evidence_repository is None:
            return None
        license_name = self._license_type(competition_dir)
        if license_name == "UNVERIFIED":
            return None
        source = DataSource(
            source_name=f"Cricsheet local: {competition_dir.name}",
            source_type="JSON Feed",
            base_url="https://cricsheet.org/downloads/",
            license_type=license_name,
            license_status="VERIFIED",
            license_evidence=f"{competition_dir.name}/LICENSE.txt",
            update_cadence="local snapshot",
            data_steward="Cricsheet",
        )
        return self.evidence_repository.register_data_source(source)

    @staticmethod
    def _license_type(competition_dir: Path) -> str:
        """Return the license title actually printed in this dataset's notice."""
        try:
            license_text = (competition_dir / "LICENSE.txt").read_text(encoding="utf-8")
        except OSError:
            return "UNVERIFIED"
        title = re.search(r"^#\s*(.+?)\s*$", license_text, flags=re.MULTILINE)
        if title is None:
            return "UNVERIFIED"
        label = title.group(1).strip()
        return label if "ODC" in label and "Attribution" in label else "UNVERIFIED"

    @staticmethod
    def _license_url(competition_dir: Path) -> str | None:
        """Return a license URL only when the actual LICENSE notice includes one."""
        try:
            text = (competition_dir / "LICENSE.txt").read_text(encoding="utf-8")
        except OSError:
            return None
        urls = re.findall(r"https?://[^\s)<>]+", text)
        return next((url.rstrip(".,;") for url in urls if "license" in url.lower()), None)

    @staticmethod
    def _attribution_notice(competition_dir: Path) -> str | None:
        """Preserve the dataset README's actual attribution statement, if present."""
        try:
            text = (competition_dir / "README.txt").read_text(encoding="utf-8")
        except OSError:
            return None
        match = re.search(
            r"(Match data is licensed for use under the Open Data Commons Attribution\s+License\.)",
            text,
            flags=re.IGNORECASE,
        )
        return re.sub(r"\s+", " ", match.group(1)).strip() if match else None

    @staticmethod
    def _download_url(competition_dir: Path) -> str | None:
        """Read the fixture archive URL from the dataset README, when available."""
        try:
            text = (competition_dir / "README.txt").read_text(encoding="utf-8")
        except OSError:
            return None
        match = re.search(r"https://cricsheet\.org/downloads/[^\s)]+\.zip", text)
        return match.group(0) if match else None

    @staticmethod
    def _match_source_trace(
        *,
        relative_key: str,
        external_fixture_id: str,
        payload_sha256: str,
        license_name: str,
        license_url: str | None,
        attribution: str | None,
        source_url: str | None,
        retrieved_at: datetime | None,
    ) -> SourceTrace:
        """Build a source trace from file and notice data, leaving unknown times unset."""
        available = bool(payload_sha256 or source_url)
        return SourceTrace(
            provider="Cricsheet",
            source_url=source_url,
            license_name=(license_name if license_name != "UNVERIFIED" else None),
            license_url=license_url,
            relative_source_record_key=relative_key,
            retrieved_at=retrieved_at,
            payload_sha256=payload_sha256,
            tier=(ProvenanceTier.THIRD_PARTY_ESTIMATE if available else ProvenanceTier.UNKNOWN),
            information_kind=(
                InformationKind.THIRD_PARTY_DATASET if available else InformationKind.UNKNOWN
            ),
            attribution=attribution,
            external_entity_id=external_fixture_id,
        )

    def player_coverage(
        self, player_id: UUID | None, evidence: tuple[PlayerMatchEvidence, ...]
    ) -> dict[str, object]:
        """Summarize observations without inferring unobserved periods as absences."""
        self._build_player_index()
        competitions = sorted(
            {
                str(record.match.get("competition_name"))
                for record in evidence
                if record.match.get("competition_name")
            }
        )
        seasons = sorted(
            {
                str(record.match.get("season_label"))
                for record in evidence
                if record.match.get("season_label") is not None
            }
        )
        timestamps = [
            record.ingestion_timestamp
            for record in evidence
            if record.ingestion_timestamp is not None
        ]
        has_player = player_id in self._paths_by_player if player_id else False
        return {
            "records_observed": len(evidence),
            "competitions_covered": competitions,
            "seasons_covered": seasons,
            "missing_periods": None,
            "source_completeness": "PARTIAL_SNAPSHOT",
            "identity_certainty": ("SOURCE_KEYED_UNVERIFIED" if has_player else "UNKNOWN"),
            "unavailable_datasets": [
                "Official scorecard-only matches",
                "Complete senior international appearance history",
                "Official squad and auction history",
                "Competition periods absent from the local snapshot",
            ],
            "last_ingestion_timestamp": max(timestamps) if timestamps else None,
            "derived_performance_source_record_ids": [
                record.source_record_id
                for record in evidence
                if record.source_record_id is not None
                and self.evidence_repository is not None
                and self.evidence_repository.durable
            ],
        }

    def availability(self) -> dict[str, str]:
        return {
            "provider": "local_cricsheet_snapshot",
            "identity": "Names with Cricsheet registry IDs are keyed; name-only records are file-scoped and may resolve ambiguously; aliases are limited to recorded names.",
            "performance": "Available for recorded batter/bowler deliveries in the local Cricsheet snapshot; no scorecard-only backfill.",
            "membership": "Match participation only; squad membership and auction history unavailable.",
            "provenance": (
                "Cricsheet relative keys, the local license notice, and SHA-256 available; "
                + (
                    "records are persisted through the configured provenance repository."
                    if self.evidence_repository and self.evidence_repository.durable
                    else "durable source_records are not configured."
                )
            ),
            "cap_status": "Unavailable; Cricsheet match snapshot is not treated as complete authoritative international appearance coverage.",
        }
