"""Four-State Coverage Evaluator for CDCRE.

Part of Phase 04A — Career Discovery & Competition Research Engine (Milestone 4).
Implements the authoritative four-state coverage model adhering to TRD §5.3,
PostgreSQL 16 DDL constraint chk_coverage_status, and mandatory AC-11 invariant:
missing datasets MUST emit CoverageStatus.DATASET_UNAVAILABLE with appearances = None.
Never emit zero appearances (appearances = 0) or fabricate non-participation for missing datasets.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.cdcre.competition_registry import (
    derive_competition_uuid,
    derive_provenance_uuid,
    normalize_competition_name,
    normalize_format_tag,
    normalize_season_year,
)
from src.contracts.cdcre import (
    CareerDataCoverage,
    CompetitionHistoryRecord,
    CoverageStatus,
)


def evaluate_coverage(
    *args: Any,
    competition_id: UUID | None = None,
    season_year: str | None = None,
    has_dataset: bool | None = None,
    appearances: int | None = None,
    squad_member: bool = False,
    ambiguous: bool = False,
) -> CoverageStatus:
    """Evaluate tournament participation into the authoritative four-state model.

    Taxonomy:
    1. VERIFIED_PARTICIPATION: dataset exists and appearances > 0.
    2. DATASET_UNAVAILABLE: dataset is missing / unavailable (AC-11).
    3. NOT_ESTABLISHED: dataset exists, but appearances is None or ambiguous.
    4. CONFIRMED_NON_PARTICIPATION: dataset exists and complete, appearances == 0.

    Args:
        *args: Flexible positional arguments supporting either:
               (has_dataset, appearances, [squad_member, ambiguous]) or
               (competition_id, season_year, has_dataset, appearances).
        competition_id: Competition UUID identifier (optional).
        season_year: Season identifier (optional).
        has_dataset: Whether competition season dataset exists and is accessible.
        appearances: Verified match appearance count (None if unavailable/unknown).
        squad_member: Whether player was verified in squad/bench.
        ambiguous: Whether player identity or participation is ambiguous.

    Returns:
        Authoritative CoverageStatus enum value.

    Raises:
        ValueError: If appearances is negative.
    """
    _ = (competition_id, season_year, squad_member)

    # Unpack positional arguments if passed
    if len(args) == 4 and not isinstance(args[0], bool) and isinstance(args[2], bool):
        # (competition_id, season_year, has_dataset, appearances)
        has_dataset = args[2]
        appearances = args[3]
    elif len(args) >= 1 and isinstance(args[0], bool):
        # (has_dataset, [appearances, squad_member, ambiguous])
        has_dataset = args[0]
        if len(args) >= 2:
            appearances = args[1]
        if len(args) >= 3:
            _ = bool(args[2])
        if len(args) >= 4:
            ambiguous = bool(args[3])
    elif len(args) == 2 and isinstance(args[1], bool):
        # (competition_id, has_dataset)
        has_dataset = args[1]

    # Validate appearances
    if appearances is not None and appearances < 0:
        raise ValueError(f"appearances must be non-negative, got {appearances}")

    # Mandatory AC-11 Invariant: missing dataset ALWAYS produces DATASET_UNAVAILABLE
    if has_dataset is False:
        return CoverageStatus.DATASET_UNAVAILABLE

    if has_dataset is None:
        # If dataset status is not specified, infer from appearances
        if appearances is None:
            return CoverageStatus.DATASET_UNAVAILABLE
        has_dataset = True

    # Ambiguity check
    if ambiguous:
        return CoverageStatus.NOT_ESTABLISHED

    # Dataset exists (has_dataset is True)
    if appearances is None:
        return CoverageStatus.NOT_ESTABLISHED

    if appearances > 0:
        return CoverageStatus.VERIFIED_PARTICIPATION

    # appearances == 0
    return CoverageStatus.CONFIRMED_NON_PARTICIPATION


def evaluate_competition_coverage(
    competition_id: UUID,
    competition_name: str,
    season_year: str,
    has_dataset: bool,
    appearances: int | None,
    squad_member: bool = False,
    format_tag: str | None = None,
    balls_per_over: int | None = None,
    provenance_record_id: UUID | None = None,
    ambiguous: bool = False,
) -> CompetitionHistoryRecord:
    """Evaluate a competition season participation record adhering strictly to AC-11.

    MANDATORY AC-11 RULE:
    When has_dataset is False, the resulting record MUST have:
    - coverage_status = CoverageStatus.DATASET_UNAVAILABLE
    - appearances = None
    Zero appearances (appearances = 0) is NEVER emitted for missing datasets.

    Args:
        competition_id: UUID identifying the competition.
        competition_name: Display or canonical name of the competition.
        season_year: Competition season year (e.g. '2024', '2023/24').
        has_dataset: Boolean flag indicating if dataset is available.
        appearances: Observed match appearances, or None if missing.
        squad_member: Boolean flag indicating bench/squad membership.
        format_tag: Format tag ('T20', 'ODI', '100-ball', etc.).
        balls_per_over: Balls per over (5 for The Hundred, 6 for standard).
        provenance_record_id: UUID for data lineage audit trail.
        ambiguous: Whether status is ambiguous or conflicting.

    Returns:
        Validated CompetitionHistoryRecord domain contract.

    Raises:
        TypeError: If competition_id is not a valid UUID instance.
        ValueError: If appearances is negative.
    """
    if not isinstance(competition_id, UUID):
        try:
            competition_id = UUID(str(competition_id))
        except (ValueError, AttributeError) as exc:
            raise TypeError(
                f"competition_id must be a UUID instance, got {type(competition_id).__name__}: {competition_id!r}"
            ) from exc

    norm_comp_name = normalize_competition_name(competition_name)
    norm_season = normalize_season_year(season_year)

    # Balls per over & format tag resolution
    if balls_per_over is None:
        balls_per_over = 5 if ("The Hundred" in norm_comp_name or "Hundred" in norm_comp_name) else 6

    if format_tag is None:
        format_tag = normalize_format_tag(norm_comp_name, balls_per_over=balls_per_over)

    # Enforce AC-11 Invariant: missing dataset -> DATASET_UNAVAILABLE and appearances = None
    if not has_dataset:
        coverage_status = CoverageStatus.DATASET_UNAVAILABLE
        eval_appearances: int | None = None
    else:
        coverage_status = evaluate_coverage(
            has_dataset=True,
            appearances=appearances,
            squad_member=squad_member,
            ambiguous=ambiguous,
        )
        eval_appearances = appearances

    if provenance_record_id is None:
        provenance_record_id = derive_provenance_uuid(
            f"{norm_comp_name}:{norm_season}:{coverage_status.value}"
        )

    return CompetitionHistoryRecord(
        competition_id=competition_id,
        competition_name=norm_comp_name,
        season_year=norm_season,
        format_tag=format_tag,
        appearances=eval_appearances,
        coverage_status=coverage_status,
        balls_per_over=balls_per_over,
        provenance_record_id=provenance_record_id,
    )


def enrich_career_coverage(
    career_coverage: CareerDataCoverage,
    known_competitions: list[Any] | None = None,
    detect_gaps: bool = False,
    injuries: list[Any] | None = None,
    availability: list[Any] | None = None,
    team_affiliations: list[str] | None = None,
) -> CareerDataCoverage:
    """Enrich CareerDataCoverage by integrating known competitions and updating summary counts.

    Guarantees:
    - Integrates missing dataset records with DATASET_UNAVAILABLE and appearances = None (AC-11).
    - Recalculates coverage_summary accurately across all 4 CoverageStatus states.
    - Recalculates competitions_evaluated_count.
    - Recalculates the_hundred_appearances_deferred.
    - Preserves or optionally detects career gaps.

    Args:
        career_coverage: Existing CareerDataCoverage instance to enrich.
        known_competitions: Optional list of known competition records or specifications to integrate.
        detect_gaps: Whether to automatically detect career gaps if not already populated.
        injuries: Optional player injuries for gap corroboration.
        availability: Optional player availability records for gap corroboration.
        team_affiliations: Optional team affiliations for franchise suspension corroboration.

    Returns:
        Enriched and validated CareerDataCoverage instance.
    """
    # Clone existing records and enforce AC-11 on existing records
    records_by_key: dict[tuple[str, str], CompetitionHistoryRecord] = {}

    for rec in career_coverage.competitions_covered:
        clean_comp = normalize_competition_name(rec.competition_name)
        clean_season = normalize_season_year(rec.season_year)
        # AC-11 invariant check on existing records
        if rec.coverage_status == CoverageStatus.DATASET_UNAVAILABLE and rec.appearances is not None:
            rec = rec.model_copy(update={"appearances": None})
        records_by_key[(clean_comp, clean_season)] = rec

    # Integrate known competitions if provided
    if known_competitions:
        for item in known_competitions:
            if isinstance(item, CompetitionHistoryRecord):
                rec = item
                if rec.coverage_status == CoverageStatus.DATASET_UNAVAILABLE and rec.appearances is not None:
                    rec = rec.model_copy(update={"appearances": None})
            elif isinstance(item, dict):
                comp_id = item.get("competition_id")
                comp_name = item.get("competition_name", "Unknown Competition")
                if comp_id is None:
                    comp_id = derive_competition_uuid(comp_name)
                elif not isinstance(comp_id, UUID):
                    comp_id = UUID(str(comp_id))

                rec = evaluate_competition_coverage(
                    competition_id=comp_id,
                    competition_name=comp_name,
                    season_year=str(item.get("season_year", "Unknown")),
                    has_dataset=bool(item.get("has_dataset", False)),
                    appearances=item.get("appearances"),
                    squad_member=bool(item.get("squad_member", False)),
                    format_tag=item.get("format_tag"),
                    balls_per_over=item.get("balls_per_over"),
                    provenance_record_id=item.get("provenance_record_id"),
                    ambiguous=bool(item.get("ambiguous", False)),
                )
            else:
                continue

            key = (normalize_competition_name(rec.competition_name), normalize_season_year(rec.season_year))
            # If not already present, or if existing record is less informative
            if key not in records_by_key or (
                records_by_key[key].coverage_status in (CoverageStatus.DATASET_UNAVAILABLE, CoverageStatus.NOT_ESTABLISHED)
                and rec.coverage_status == CoverageStatus.VERIFIED_PARTICIPATION
            ):
                records_by_key[key] = rec

    # Order records deterministically
    sorted_records = sorted(
        records_by_key.values(),
        key=lambda r: (r.competition_name, r.season_year),
    )

    # Recalculate coverage summary
    summary: dict[CoverageStatus, int] = {
        CoverageStatus.VERIFIED_PARTICIPATION: 0,
        CoverageStatus.DATASET_UNAVAILABLE: 0,
        CoverageStatus.NOT_ESTABLISHED: 0,
        CoverageStatus.CONFIRMED_NON_PARTICIPATION: 0,
    }
    for r in sorted_records:
        summary[r.coverage_status] = summary.get(r.coverage_status, 0) + 1

    # Check The Hundred deferred appearances
    the_hundred_deferred = any(
        (r.balls_per_over == 5 or "hundred" in r.competition_name.lower())
        and (r.appearances is not None and r.appearances > 0)
        for r in sorted_records
    )

    # Resolve career gaps
    gaps = list(career_coverage.career_gaps)
    if not gaps and detect_gaps:
        # Import dynamically to avoid top-level coupling
        from src.cdcre.gap_detector import detect_career_gaps

        gaps = detect_career_gaps(
            player_id=career_coverage.canonical_player_id,
            history=sorted_records,
            injuries=injuries,
            availability=availability,
            team_affiliations=team_affiliations,
        )

    return CareerDataCoverage(
        canonical_player_id=career_coverage.canonical_player_id,
        competitions_evaluated_count=len(sorted_records),
        competitions_covered=sorted_records,
        coverage_summary=summary,
        career_gaps=gaps,
        the_hundred_appearances_deferred=the_hundred_deferred,
    )


class CoverageEvaluator:
    """Authoritative evaluator implementing the four-state tournament coverage model.

    Provides evaluation, competition history modeling with AC-11 compliance, and
    career coverage enrichment.
    """

    def evaluate(
        self,
        *args: Any,
        competition_id: UUID | None = None,
        season_year: str | None = None,
        has_dataset: bool | None = None,
        appearances: int | None = None,
        squad_member: bool = False,
        ambiguous: bool = False,
    ) -> CoverageStatus:
        """Evaluate four-state coverage status."""
        return evaluate_coverage(
            *args,
            competition_id=competition_id,
            season_year=season_year,
            has_dataset=has_dataset,
            appearances=appearances,
            squad_member=squad_member,
            ambiguous=ambiguous,
        )

    def evaluate_competition(
        self,
        competition_id: UUID,
        competition_name: str,
        season_year: str,
        has_dataset: bool,
        appearances: int | None,
        squad_member: bool = False,
        format_tag: str | None = None,
        balls_per_over: int | None = None,
        provenance_record_id: UUID | None = None,
        ambiguous: bool = False,
    ) -> CompetitionHistoryRecord:
        """Evaluate and construct CompetitionHistoryRecord adhering strictly to AC-11."""
        return evaluate_competition_coverage(
            competition_id=competition_id,
            competition_name=competition_name,
            season_year=season_year,
            has_dataset=has_dataset,
            appearances=appearances,
            squad_member=squad_member,
            format_tag=format_tag,
            balls_per_over=balls_per_over,
            provenance_record_id=provenance_record_id,
            ambiguous=ambiguous,
        )

    def enrich(
        self,
        career_coverage: CareerDataCoverage,
        known_competitions: list[Any] | None = None,
        detect_gaps: bool = False,
        injuries: list[Any] | None = None,
        availability: list[Any] | None = None,
        team_affiliations: list[str] | None = None,
    ) -> CareerDataCoverage:
        """Enrich CareerDataCoverage container."""
        return enrich_career_coverage(
            career_coverage=career_coverage,
            known_competitions=known_competitions,
            detect_gaps=detect_gaps,
            injuries=injuries,
            availability=availability,
            team_affiliations=team_affiliations,
        )


__all__ = [
    "CoverageEvaluator",
    "enrich_career_coverage",
    "evaluate_competition_coverage",
    "evaluate_coverage",
]
