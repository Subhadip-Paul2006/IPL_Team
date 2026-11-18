"""Provenance Graph Assembly & Licensing Attribution Service (Support Service C).

Compiles source record links, verification records, provenance tiers, and embedded
source-provided license and attribution metadata in strict accordance with TRD §10.3 and AC-20.
"""

from __future__ import annotations

from collections.abc import Sequence

from src.contracts.cdcre import CandidateDiscoveryResult, CareerDataCoverage
from src.contracts.cmie import CMIEOutputContract
from src.contracts.pvre import PVREOutputContract
from src.contracts.tmve import EligibilityOutputContract, TMVEOutputContract
from src.mie.contracts import SourceTrace, UnifiedProvenanceGraph
from src.pire.models import ResolutionResult

BCCI_CITATION = (
    "Official match scorecards and youth registrations referenced under fair dealing "
    "from Board of Control for Cricket in India (BCCI) official archives."
)


class ProvenanceGraphBuilder:
    """Assembles unified provenance graph and verifies licensing obligations."""

    @staticmethod
    def build_provenance_graph(
        tmve_output: TMVEOutputContract | None = None,
        eligibility_output: EligibilityOutputContract | None = None,
        identity_output: ResolutionResult | None = None,
        candidate_discovery: CandidateDiscoveryResult | None = None,
        career_coverage: CareerDataCoverage | None = None,
        cmie_output: CMIEOutputContract | None = None,
        pvre_output: PVREOutputContract | None = None,
        extra_source_ids: Sequence[str | int] | None = None,
        extra_verification_ids: Sequence[str | int] | None = None,
        local_cricsheet_observed: bool = False,
    ) -> UnifiedProvenanceGraph:
        """Compile a deduplicated UnifiedProvenanceGraph from all engine outputs."""
        source_ids: set[str | int] = set(extra_source_ids or [])
        verification_ids: set[str | int] = set(extra_verification_ids or [])
        primary_sources: set[str] = set()
        attributions: list[str] = []
        licenses: set[str] = set()
        tiers_summary: dict[str, int] = {}

        # 1. Inspect TMVE evidence
        if tmve_output:
            for vid in getattr(tmve_output, "evidence_verification_ids", []):
                verification_ids.add(str(vid))
            primary_sources.add("Internal Franchise Database & Scorecards")

        if eligibility_output:
            if eligibility_output.verification_id:
                verification_ids.add(str(eligibility_output.verification_id))
            verification_ids.update(
                str(vid) for vid in eligibility_output.evidence_verification_ids
            )
            if eligibility_output.rule_source:
                primary_sources.add(eligibility_output.rule_source)

        if identity_output and identity_output.matched_source:
            primary_sources.add(identity_output.matched_source)

        if candidate_discovery:
            for candidate in candidate_discovery.candidates:
                if candidate.source_id:
                    primary_sources.add(candidate.source_id)

        if local_cricsheet_observed:
            primary_sources.add("Cricsheet local match archive")
            licenses.add("ODC-By v1.0")
            notices = (
                "Data derived from CricSheet (https://cricsheet.org), "
                "licensed under the Open Data Commons Attribution License (ODC-By v1.0)."
            )
            if notices not in attributions:
                attributions.append(notices)
            tiers_summary["TIER_4"] = tiers_summary.get("TIER_4", 0) + 1

        if career_coverage:
            for history in career_coverage.competitions_covered:
                if history.provenance_record_id:
                    source_ids.add(str(history.provenance_record_id))
            for gap in career_coverage.career_gaps:
                if gap.provenance_record_id:
                    source_ids.add(str(gap.provenance_record_id))

        cmie_traces: list[SourceTrace] = []
        # 2. Preserve canonical CMIE source traces, including nested weather/dew,
        # pitch proxy, venue, leverage, and fixture timing evidence.
        if cmie_output:
            source_ids.update(str(item) for item in getattr(cmie_output, "source_record_ids", []))
            for trace in ProvenanceGraphBuilder._source_traces(cmie_output):
                if trace not in cmie_traces:
                    cmie_traces.append(trace)
                if trace.provider:
                    primary_sources.add(trace.provider)
                attr_val = trace.attribution
                if trace.license_name:
                    licenses.add(trace.license_name)
                    attribution = attr_val or (
                        f"{trace.provider or 'Source'} ({trace.source_url or 'URL unavailable'}), "
                        f"licensed under {trace.license_name}"
                        + (f" ({trace.license_url})" if trace.license_url else "")
                        + "."
                    )
                    if attribution not in attributions:
                        attributions.append(attribution)
                elif attr_val and attr_val not in attributions:
                    attributions.append(attr_val)
                tier = trace.tier.value
                tiers_summary[tier] = tiers_summary.get(tier, 0) + 1

        # 3. Inspect PVRE research evidence
        if pvre_output:
            for sid in getattr(pvre_output, "source_record_ids", []):
                source_ids.add(str(sid))
            for vid in getattr(pvre_output, "verification_record_ids", []):
                verification_ids.add(str(vid))
            if getattr(pvre_output, "source_record_ids", []):
                primary_sources.add("PVRE source records")

        return UnifiedProvenanceGraph(
            total_sources_consulted=len(primary_sources),
            source_record_ids=sorted(source_ids, key=str),
            verification_record_ids=sorted(verification_ids, key=str),
            primary_sources=sorted(primary_sources),
            attribution_notices=attributions,
            licenses_observed=sorted(licenses),
            provenance_tiers_summary=tiers_summary,
            cmie_source_traces=cmie_traces,
        )

    @staticmethod
    def _source_traces(value: object) -> list[SourceTrace]:
        """Collect canonical traces recursively without manufacturing source IDs."""
        found: list[SourceTrace] = []

        def visit(item: object) -> None:
            if isinstance(item, SourceTrace):
                found.append(item)
            elif hasattr(type(item), "model_fields") and hasattr(item, "__dict__"):
                for field_value in vars(item).values():
                    visit(field_value)
            elif isinstance(item, dict):
                for field_value in item.values():
                    visit(field_value)
            elif isinstance(item, (list, tuple, set)):
                for field_value in item:
                    visit(field_value)

        visit(value)
        return found
