"""Player Profile Generator Service (Support Service B).

Generates standardized JSON and CSV exports from PlayerIntelligenceReport
embedding available source-provided license attribution and enforcing
strict confidentiality controls to prevent proprietary hackathon leakage (TRD §10.2, AC-20).
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from src.mie.contracts import PlayerIntelligenceReport


class ProfileGeneratorService:
    """Service B: Produces standardized JSON/CSV exports with legal attribution."""

    @classmethod
    def export_to_json(
        cls,
        report: PlayerIntelligenceReport,
        indent: int = 2,
        sanitize_internal_keys: bool = True,
    ) -> str:
        """Export PlayerIntelligenceReport to JSON with embedded licensing attribution."""
        data = report.model_dump(mode="json")

        if sanitize_internal_keys:
            # Enforce AC-20 confidentiality guard: strip any sensitive environment tokens
            cls._sanitize_payload(data)

        # Embed mandatory attribution and license header
        export_envelope = {
            "metadata": {
                "system": "Rajasthan Royals Squad Intelligence Platform",
                "export_version": "v2.2.0",
                "report_id": str(report.report_id),
                "generated_at": report.generated_at.isoformat(),
                "player_id": str(report.player_id) if report.player_id else None,
                "canonical_name": report.canonical_name,
                "overall_verification_status": report.verification.overall_status.value,
            },
            "legal_and_licensing": {
                "attribution_notices": report.provenance.attribution_notices,
                "licenses": report.provenance.licenses_observed,
                "disclaimer": "Analytical decision-support dossier for Rajasthan Royals scouting. Zero warranty.",
            },
            "player_intelligence": data,
        }

        return json.dumps(export_envelope, indent=indent, default=str)

    @classmethod
    def export_to_csv(cls, report: PlayerIntelligenceReport) -> str:
        """Export summary metrics from PlayerIntelligenceReport to structured CSV."""
        output = io.StringIO()
        writer = csv.writer(output)

        def write_row(row: list[Any]) -> None:
            writer.writerow([cls._spreadsheet_safe_cell(value) for value in row])

        # 1. Header & Licensing Notices
        write_row(["# RAJASTHAN ROYALS SQUAD INTELLIGENCE PLATFORM — EXPORT DOSSIER"])
        write_row(
            [f"# Report ID: {report.report_id} | Generated: {report.generated_at.isoformat()}"]
        )
        for notice in report.provenance.attribution_notices:
            write_row([f"# Legal: {notice}"])
        write_row([])

        # 2. Player Identification & Membership Summary
        write_row(["SECTION", "FIELD", "VALUE"])
        write_row(["IDENTIFICATION", "Canonical Name", report.canonical_name or "N/A"])
        write_row(
            ["IDENTIFICATION", "Player ID", str(report.player_id) if report.player_id else "N/A"]
        )
        write_row(["IDENTIFICATION", "Identity Status", report.verification.identity_status])
        write_row(
            ["MEMBERSHIP", "RR Relationship State", report.verification.rr_relationship_state.value]
        )
        write_row(["MEMBERSHIP", "RR Current State", report.verification.rr_current_state.value])
        write_row(
            [
                "ELIGIBILITY",
                "IPL Uncapped Eligibility",
                report.verification.ipl_uncapped_eligibility.value,
            ]
        )
        write_row(["ELIGIBILITY", "Capped Status", report.verification.player_capped_status.value])
        write_row(["CAREER", "Coverage State", report.verification.career_coverage_state.value])
        write_row(["VERIFICATION", "Overall Status", report.verification.overall_status.value])
        write_row(["VERIFICATION", "Review Required", str(report.is_review_required)])

        # 3. Performance Summary
        perf = (
            report.performance
            if isinstance(report.performance, dict)
            else (report.performance.model_dump(mode="json") if report.performance else {})
        )
        bat = perf.get("batting") or {}
        bowl = perf.get("bowling") or {}
        samples = perf.get("samples") or {}

        write_row(["PERFORMANCE", "Format", perf.get("format_tag", "T20")])
        write_row(["PERFORMANCE", "Matches Evaluated", samples.get("matches")])
        write_row(["PERFORMANCE", "Balls Faced", samples.get("balls_faced")])
        write_row(["PERFORMANCE", "Batting Runs", bat.get("runs")])
        write_row(["PERFORMANCE", "Batting Average", bat.get("batting_average", "N/A")])
        write_row(["PERFORMANCE", "Strike Rate", bat.get("strike_rate", "N/A")])
        write_row(["PERFORMANCE", "Legal Balls Bowled", samples.get("legal_balls_bowled")])
        write_row(["PERFORMANCE", "Wickets Taken", bowl.get("wickets_taken")])
        write_row(["PERFORMANCE", "Economy Rate", bowl.get("economy_rate", "N/A")])
        write_row(["PERFORMANCE", "Bowling Average", bowl.get("bowling_average", "N/A")])

        # 4. PVRE Assessment
        pvre = (
            report.pvre
            if isinstance(report.pvre, dict)
            else (report.pvre.model_dump(mode="json") if report.pvre else {})
        )
        write_row(["PVRE", "Research Mode", pvre.get("research_mode", "N/A")])
        write_row(["PVRE", "Route Status", pvre.get("route_status", "N/A")])
        rep_assess = pvre.get("replaceability_assessment") or {}
        write_row(["PVRE", "Replaceability Signal", rep_assess.get("replaceability_signal", "N/A")])

        # 5. Canonical CMIE context and nested provenance. Keep the JSON export fully
        # typed; CSV renders every scalar context value and every source trace.
        context = (
            report.context
            if isinstance(report.context, dict)
            else report.context.model_dump(mode="json")
        )
        write_row(["CMIE", "Timestamp", context.get("timestamp") or context.get("as_of_timestamp")])
        write_row(["CMIE", "Verification Status", context.get("verification_status")])
        write_row(["CMIE", "Execution Status", context.get("execution_status")])
        write_row(["CMIE", "Input Availability", context.get("input_availability")])
        write_row(["CMIE", "Execution Errors", json.dumps(context.get("execution_errors", []))])
        write_row(["CMIE", "Review Reasons", json.dumps(context.get("review_reasons", []))])
        write_row(["CMIE", "Source Record IDs", json.dumps(context.get("source_record_ids", []))])
        write_row(
            [
                "CMIE",
                "Conflicting Source Record IDs",
                json.dumps(context.get("conflicting_source_record_ids", [])),
            ]
        )
        context_matches = context.get("matches", context.get("match_contexts", [])) or []
        for index, match in enumerate(context_matches):
            for key, value in cls._flatten_context(match):
                write_row(["CMIE_MATCH", f"{index}:{key}", value])
        for index, trace in enumerate(report.provenance.cmie_source_traces):
            for key, value in trace.model_dump(mode="json").items():
                write_row(["CMIE_SOURCE_TRACE", f"{index}:{key}", value])
        for index, limitation in enumerate(context.get("limitations", [])):
            write_row(["CMIE_LIMITATION", str(index), limitation])

        # Preserve provider coverage and local record locators in both export formats.
        for category, state in sorted(report.data_availability.items()):
            write_row(["DATA_AVAILABILITY", category, state])
        coverage = report.data_coverage
        write_row(["DATA_COVERAGE", "Records Observed", coverage.records_observed])
        write_row(
            ["DATA_COVERAGE", "Competitions Covered", json.dumps(coverage.competitions_covered)]
        )
        write_row(["DATA_COVERAGE", "Seasons Covered", json.dumps(coverage.seasons_covered)])
        write_row(
            [
                "DATA_COVERAGE",
                "Missing Periods",
                json.dumps(coverage.missing_periods),
            ]
        )
        write_row(["DATA_COVERAGE", "Source Completeness", coverage.source_completeness])
        write_row(["DATA_COVERAGE", "Identity Certainty", coverage.identity_certainty])
        write_row(
            [
                "DATA_COVERAGE",
                "Unavailable Datasets",
                json.dumps(coverage.unavailable_datasets),
            ]
        )
        write_row(
            [
                "DATA_COVERAGE",
                "Last Ingestion Timestamp",
                coverage.last_ingestion_timestamp.isoformat()
                if coverage.last_ingestion_timestamp
                else None,
            ]
        )
        write_row(
            [
                "DATA_COVERAGE",
                "Derived Performance Source Record IDs",
                json.dumps([str(item) for item in coverage.derived_performance_source_record_ids]),
            ]
        )
        for index, record in enumerate(report.local_source_evidence):
            for key, value in sorted(record.items()):
                write_row(["LOCAL_SOURCE_EVIDENCE", f"{index}:{key}", value])

        return output.getvalue()

    @classmethod
    def _flatten_context(cls, value: Any, prefix: str = "") -> list[tuple[str, Any]]:
        """Flatten nested context into deterministic CSV key/value rows."""
        if isinstance(value, dict):
            rows: list[tuple[str, Any]] = []
            for key in sorted(value):
                child = f"{prefix}.{key}" if prefix else str(key)
                rows.extend(cls._flatten_context(value[key], child))
            return rows
        if isinstance(value, list):
            rows = []
            for index, child_value in enumerate(value):
                child = f"{prefix}[{index}]"
                rows.extend(cls._flatten_context(child_value, child))
            if not value:
                return [(prefix, "[]")]
            return rows
        if value is None or isinstance(value, (str, int, float, bool)):
            return [(prefix, value)]
        return [(prefix, json.dumps(value, default=str, sort_keys=True))]

    @staticmethod
    def _spreadsheet_safe_cell(value: Any) -> Any:
        """Prefix formula-like text while preserving numbers and ordinary strings."""
        if not isinstance(value, str):
            return value
        index = 0
        while index < len(value) and (
            value[index].isspace() or ord(value[index]) < 32 or ord(value[index]) == 127
        ):
            index += 1
        if index < len(value) and value[index] in "=+-@":
            return "'" + value
        return value

    @staticmethod
    def _sanitize_payload(obj: Any) -> None:
        """Recursively remove private hackathon secrets or internal file paths."""
        if isinstance(obj, dict):
            sensitive_keys = {
                "secret",
                "api_key",
                "api-key",
                "token",
                "credential",
                "password",
                "private_path",
                "private_key",
            }
            for k in list(obj.keys()):
                if any(s in k.lower() for s in sensitive_keys):
                    del obj[k]
                else:
                    ProfileGeneratorService._sanitize_payload(obj[k])
        elif isinstance(obj, list):
            for item in obj:
                ProfileGeneratorService._sanitize_payload(item)
