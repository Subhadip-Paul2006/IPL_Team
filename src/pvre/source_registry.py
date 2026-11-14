"""Research Source Registry & Competition Provenance for PVRE.

Part of Phase 04B — Player Verification & Research Engine (Milestone 2).
Provides source registry, evidence-tier classification, competition provenance,
dataset availability tracking, duplicate claim detection, and conflict tracking
for the Rajasthan Royals squad intelligence platform.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4, uuid5

from src.contracts.pvre import (
    EvidenceSource,
    EvidenceTier,
    PVREVerificationStatus,
    ResearchConflict,
    SourceReliability,
    VerificationClaim,
)

# Deterministic namespace for PVRE competition UUIDs (derived from RFC 4122 DNS namespace)
PVRE_NAMESPACE = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

# ==============================================================================
# Authoritative Deterministic Competition UUIDs
# ==============================================================================

IPL_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000001")
SMAT_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000002")
HUNDRED_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000003")
BBL_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000004")
BPL_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000005")
PSL_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000006")
CPL_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000007")
SA20_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000008")
ILT20_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000009")
RANJI_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000010")
VHT_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000011")
DULEEP_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000012")
COOCH_BEHAR_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000013")
VINOO_MANKAD_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000014")
CK_NAYUDU_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000015")
VIJAY_MERCHANT_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000016")
T20_WORLD_CUP_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000017")
CWC_COMPETITION_UUID = UUID("20000000-0000-0000-0000-000000000018")
INTERNATIONAL_GENERAL_UUID = UUID("20000000-0000-0000-0000-000000000019")


# ==============================================================================
# Coverage Status Taxonomy (TRD §5.3, §10, chk_coverage_status)
# ==============================================================================


class CoverageStatus(StrEnum):
    """Authoritative four-state coverage model for player tournament participation.

    Strictly aligns with PostgreSQL 16 DDL constraint chk_coverage_status and CDCRE.
    """

    VERIFIED_PARTICIPATION = "VERIFIED_PARTICIPATION"
    DATASET_UNAVAILABLE = "DATASET_UNAVAILABLE"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"
    CONFIRMED_NON_PARTICIPATION = "CONFIRMED_NON_PARTICIPATION"


# ==============================================================================
# Competition Metadata Specification
# ==============================================================================


@dataclass(frozen=True)
class CompetitionMeta:
    """Metadata specification for a supported cricket competition."""

    competition_uuid: UUID
    canonical_name: str
    format_tag: str
    balls_per_over: int
    default_tier: EvidenceTier
    default_licence: str
    granularity: str
    dataset_dir: str | None = None


SUPPORTED_COMPETITIONS: dict[str, CompetitionMeta] = {
    "Indian Premier League": CompetitionMeta(
        competition_uuid=IPL_COMPETITION_UUID,
        canonical_name="Indian Premier League",
        format_tag="T20",
        balls_per_over=6,
        default_tier=EvidenceTier.TIER_2_COMMERCIAL,
        default_licence="ODC-By v1.0",
        granularity="BALL_BY_BALL",
        dataset_dir="ipl_male_json",
    ),
    "Syed Mushtaq Ali Trophy": CompetitionMeta(
        competition_uuid=SMAT_COMPETITION_UUID,
        canonical_name="Syed Mushtaq Ali Trophy",
        format_tag="T20",
        balls_per_over=6,
        default_tier=EvidenceTier.TIER_2_COMMERCIAL,
        default_licence="ODC-By v1.0",
        granularity="BALL_BY_BALL",
        dataset_dir="sma_json",
    ),
    "The Hundred Men's Competition": CompetitionMeta(
        competition_uuid=HUNDRED_COMPETITION_UUID,
        canonical_name="The Hundred Men's Competition",
        format_tag="100-ball",
        balls_per_over=5,
        default_tier=EvidenceTier.TIER_2_COMMERCIAL,
        default_licence="ODC-By v1.0",
        granularity="BALL_BY_BALL",
        dataset_dir="hnd_male_json",
    ),
    "Big Bash League": CompetitionMeta(
        competition_uuid=BBL_COMPETITION_UUID,
        canonical_name="Big Bash League",
        format_tag="T20",
        balls_per_over=6,
        default_tier=EvidenceTier.TIER_2_COMMERCIAL,
        default_licence="ODC-By v1.0",
        granularity="BALL_BY_BALL",
        dataset_dir="bbl_male_json",
    ),
    "Bangladesh Premier League": CompetitionMeta(
        competition_uuid=BPL_COMPETITION_UUID,
        canonical_name="Bangladesh Premier League",
        format_tag="T20",
        balls_per_over=6,
        default_tier=EvidenceTier.TIER_2_COMMERCIAL,
        default_licence="ODC-By v1.0",
        granularity="BALL_BY_BALL",
        dataset_dir="bpl_male_json",
    ),
    "Pakistan Super League": CompetitionMeta(
        competition_uuid=PSL_COMPETITION_UUID,
        canonical_name="Pakistan Super League",
        format_tag="T20",
        balls_per_over=6,
        default_tier=EvidenceTier.TIER_2_COMMERCIAL,
        default_licence="ODC-By v1.0",
        granularity="BALL_BY_BALL",
        dataset_dir="psl_male_json",
    ),
    "Caribbean Premier League": CompetitionMeta(
        competition_uuid=CPL_COMPETITION_UUID,
        canonical_name="Caribbean Premier League",
        format_tag="T20",
        balls_per_over=6,
        default_tier=EvidenceTier.TIER_2_COMMERCIAL,
        default_licence="ODC-By v1.0",
        granularity="BALL_BY_BALL",
        dataset_dir="cpl_male_json",
    ),
    "SA20": CompetitionMeta(
        competition_uuid=SA20_COMPETITION_UUID,
        canonical_name="SA20",
        format_tag="T20",
        balls_per_over=6,
        default_tier=EvidenceTier.TIER_2_COMMERCIAL,
        default_licence="ODC-By v1.0",
        granularity="BALL_BY_BALL",
        dataset_dir="sat_male_json",
    ),
    "Ranji Trophy": CompetitionMeta(
        competition_uuid=RANJI_COMPETITION_UUID,
        canonical_name="Ranji Trophy",
        format_tag="First-Class",
        balls_per_over=6,
        default_tier=EvidenceTier.TIER_1_OFFICIAL,
        default_licence="RESTRICTED",
        granularity="SCORECARD_ONLY",
        dataset_dir=None,
    ),
    "Vijay Hazare Trophy": CompetitionMeta(
        competition_uuid=VHT_COMPETITION_UUID,
        canonical_name="Vijay Hazare Trophy",
        format_tag="List A",
        balls_per_over=6,
        default_tier=EvidenceTier.TIER_1_OFFICIAL,
        default_licence="RESTRICTED",
        granularity="SCORECARD_ONLY",
        dataset_dir=None,
    ),
    "Duleep Trophy": CompetitionMeta(
        competition_uuid=DULEEP_COMPETITION_UUID,
        canonical_name="Duleep Trophy",
        format_tag="First-Class",
        balls_per_over=6,
        default_tier=EvidenceTier.TIER_1_OFFICIAL,
        default_licence="RESTRICTED",
        granularity="SCORECARD_ONLY",
        dataset_dir=None,
    ),
    "Cooch Behar Trophy": CompetitionMeta(
        competition_uuid=COOCH_BEHAR_COMPETITION_UUID,
        canonical_name="Cooch Behar Trophy",
        format_tag="First-Class",
        balls_per_over=6,
        default_tier=EvidenceTier.TIER_1_OFFICIAL,
        default_licence="RESTRICTED",
        granularity="SCORECARD_ONLY",
        dataset_dir=None,
    ),
    "Vinoo Mankad Trophy": CompetitionMeta(
        competition_uuid=VINOO_MANKAD_COMPETITION_UUID,
        canonical_name="Vinoo Mankad Trophy",
        format_tag="List A",
        balls_per_over=6,
        default_tier=EvidenceTier.TIER_1_OFFICIAL,
        default_licence="RESTRICTED",
        granularity="SCORECARD_ONLY",
        dataset_dir=None,
    ),
    "Col CK Nayudu Trophy": CompetitionMeta(
        competition_uuid=CK_NAYUDU_COMPETITION_UUID,
        canonical_name="Col CK Nayudu Trophy",
        format_tag="First-Class",
        balls_per_over=6,
        default_tier=EvidenceTier.TIER_1_OFFICIAL,
        default_licence="RESTRICTED",
        granularity="SCORECARD_ONLY",
        dataset_dir=None,
    ),
    "Vijay Merchant Trophy": CompetitionMeta(
        competition_uuid=VIJAY_MERCHANT_COMPETITION_UUID,
        canonical_name="Vijay Merchant Trophy",
        format_tag="First-Class",
        balls_per_over=6,
        default_tier=EvidenceTier.TIER_1_OFFICIAL,
        default_licence="RESTRICTED",
        granularity="SCORECARD_ONLY",
        dataset_dir=None,
    ),
    "ICC Men's T20 World Cup": CompetitionMeta(
        competition_uuid=T20_WORLD_CUP_COMPETITION_UUID,
        canonical_name="ICC Men's T20 World Cup",
        format_tag="T20I",
        balls_per_over=6,
        default_tier=EvidenceTier.TIER_2_COMMERCIAL,
        default_licence="ODC-By v1.0",
        granularity="BALL_BY_BALL",
        dataset_dir="icc_mens_t20_world_cup_male_json",
    ),
    "ICC Cricket World Cup": CompetitionMeta(
        competition_uuid=CWC_COMPETITION_UUID,
        canonical_name="ICC Cricket World Cup",
        format_tag="ODI",
        balls_per_over=6,
        default_tier=EvidenceTier.TIER_2_COMMERCIAL,
        default_licence="ODC-By v1.0",
        granularity="BALL_BY_BALL",
        dataset_dir="icc_mens_cricket_world_cup_male_json",
    ),
}

# Lookup map from UUID to CompetitionMeta
UUID_TO_COMPETITION_META: dict[UUID, CompetitionMeta] = {
    meta.competition_uuid: meta for meta in SUPPORTED_COMPETITIONS.values()
}

# Aliases for normalization
COMPETITION_ALIASES: dict[str, str] = {
    "ipl": "Indian Premier League",
    "indian premier league": "Indian Premier League",
    "smat": "Syed Mushtaq Ali Trophy",
    "syed mushtaq ali": "Syed Mushtaq Ali Trophy",
    "syed mushtaq ali trophy": "Syed Mushtaq Ali Trophy",
    "hundred": "The Hundred Men's Competition",
    "the hundred": "The Hundred Men's Competition",
    "the hundred men's competition": "The Hundred Men's Competition",
    "bbl": "Big Bash League",
    "big bash": "Big Bash League",
    "big bash league": "Big Bash League",
    "psl": "Pakistan Super League",
    "pakistan super league": "Pakistan Super League",
    "cpl": "Caribbean Premier League",
    "caribbean premier league": "Caribbean Premier League",
    "sa20": "SA20",
    "ranji": "Ranji Trophy",
    "ranji trophy": "Ranji Trophy",
    "vht": "Vijay Hazare Trophy",
    "vijay hazare": "Vijay Hazare Trophy",
    "vijay hazare trophy": "Vijay Hazare Trophy",
    "duleep": "Duleep Trophy",
    "duleep trophy": "Duleep Trophy",
    "cooch behar": "Cooch Behar Trophy",
    "cooch behar trophy": "Cooch Behar Trophy",
    "vinoo mankad": "Vinoo Mankad Trophy",
    "vinoo mankad trophy": "Vinoo Mankad Trophy",
    "ck nayudu": "Col CK Nayudu Trophy",
    "col ck nayudu": "Col CK Nayudu Trophy",
    "col ck nayudu trophy": "Col CK Nayudu Trophy",
    "vijay merchant": "Vijay Merchant Trophy",
    "vijay merchant trophy": "Vijay Merchant Trophy",
    "t20 world cup": "ICC Men's T20 World Cup",
    "icc men's t20 world cup": "ICC Men's T20 World Cup",
    "cricket world cup": "ICC Cricket World Cup",
    "icc cricket world cup": "ICC Cricket World Cup",
}


def normalize_competition_name(name: str) -> str:
    """Normalize raw competition strings to canonical name."""
    clean = name.strip()
    lower = clean.lower()
    return COMPETITION_ALIASES.get(lower, clean)


def derive_competition_uuid(name: str) -> UUID:
    """Return deterministic UUID for a competition name."""
    norm = normalize_competition_name(name)
    if norm in SUPPORTED_COMPETITIONS:
        return SUPPORTED_COMPETITIONS[norm].competition_uuid
    return uuid5(PVRE_NAMESPACE, f"competition:{norm.lower()}")


# ==============================================================================
# Standard Research Sources (TRD §10, DATA_SOURCE_REGISTER §1, §2.4)
# ==============================================================================


STANDARD_EVIDENCE_SOURCES: list[EvidenceSource] = [
    EvidenceSource(
        source_id="S1",
        source_name="Indian Premier League (CricSheet)",
        tier=EvidenceTier.TIER_2_COMMERCIAL,
        reliability=SourceReliability.TIER_2_COMMERCIAL_ARCHIVE,
        coverage_competitions=["Indian Premier League"],
        granularity="BALL_BY_BALL",
        balls_per_over_default=6,
        licence="ODC-By v1.0",
        is_active=True,
        is_mockable=True,
    ),
    EvidenceSource(
        source_id="S2",
        source_name="The Hundred (CricSheet)",
        tier=EvidenceTier.TIER_2_COMMERCIAL,
        reliability=SourceReliability.TIER_2_COMMERCIAL_ARCHIVE,
        coverage_competitions=["The Hundred Men's Competition"],
        granularity="BALL_BY_BALL",
        balls_per_over_default=5,
        licence="ODC-By v1.0",
        is_active=True,
        is_mockable=True,
    ),
    EvidenceSource(
        source_id="S3",
        source_name="ICC Men's Cricket World Cup (CricSheet)",
        tier=EvidenceTier.TIER_2_COMMERCIAL,
        reliability=SourceReliability.TIER_2_COMMERCIAL_ARCHIVE,
        coverage_competitions=["ICC Cricket World Cup"],
        granularity="BALL_BY_BALL",
        balls_per_over_default=6,
        licence="ODC-By v1.0",
        is_active=True,
        is_mockable=True,
    ),
    EvidenceSource(
        source_id="S4",
        source_name="ICC Men's T20 World Cup (CricSheet)",
        tier=EvidenceTier.TIER_2_COMMERCIAL,
        reliability=SourceReliability.TIER_2_COMMERCIAL_ARCHIVE,
        coverage_competitions=["ICC Men's T20 World Cup"],
        granularity="BALL_BY_BALL",
        balls_per_over_default=6,
        licence="ODC-By v1.0",
        is_active=True,
        is_mockable=True,
    ),
    EvidenceSource(
        source_id="S5",
        source_name="Syed Mushtaq Ali Trophy (CricSheet)",
        tier=EvidenceTier.TIER_2_COMMERCIAL,
        reliability=SourceReliability.TIER_2_COMMERCIAL_ARCHIVE,
        coverage_competitions=["Syed Mushtaq Ali Trophy"],
        granularity="BALL_BY_BALL",
        balls_per_over_default=6,
        licence="ODC-By v1.0",
        is_active=True,
        is_mockable=True,
    ),
    EvidenceSource(
        source_id="S13",
        source_name="Big Bash League (CricSheet)",
        tier=EvidenceTier.TIER_2_COMMERCIAL,
        reliability=SourceReliability.TIER_2_COMMERCIAL_ARCHIVE,
        coverage_competitions=["Big Bash League"],
        granularity="BALL_BY_BALL",
        balls_per_over_default=6,
        licence="ODC-By v1.0",
        is_active=True,
        is_mockable=True,
    ),
    EvidenceSource(
        source_id="S14",
        source_name="Pakistan Super League (CricSheet)",
        tier=EvidenceTier.TIER_2_COMMERCIAL,
        reliability=SourceReliability.TIER_2_COMMERCIAL_ARCHIVE,
        coverage_competitions=["Pakistan Super League"],
        granularity="BALL_BY_BALL",
        balls_per_over_default=6,
        licence="ODC-By v1.0",
        is_active=True,
        is_mockable=True,
    ),
    EvidenceSource(
        source_id="S15",
        source_name="Caribbean Premier League (CricSheet)",
        tier=EvidenceTier.TIER_2_COMMERCIAL,
        reliability=SourceReliability.TIER_2_COMMERCIAL_ARCHIVE,
        coverage_competitions=["Caribbean Premier League"],
        granularity="BALL_BY_BALL",
        balls_per_over_default=6,
        licence="ODC-By v1.0",
        is_active=True,
        is_mockable=True,
    ),
    EvidenceSource(
        source_id="S16",
        source_name="SA20 (CricSheet)",
        tier=EvidenceTier.TIER_2_COMMERCIAL,
        reliability=SourceReliability.TIER_2_COMMERCIAL_ARCHIVE,
        coverage_competitions=["SA20"],
        granularity="BALL_BY_BALL",
        balls_per_over_default=6,
        licence="ODC-By v1.0",
        is_active=True,
        is_mockable=True,
    ),
    EvidenceSource(
        source_id="S18A",
        source_name="BCCI Official Ranji Trophy Archive",
        tier=EvidenceTier.TIER_1_OFFICIAL,
        reliability=SourceReliability.TIER_1_OFFICIAL,
        coverage_competitions=["Ranji Trophy"],
        granularity="SCORECARD_ONLY",
        balls_per_over_default=6,
        licence="RESTRICTED",
        is_active=True,
        is_mockable=True,
    ),
    EvidenceSource(
        source_id="S18B",
        source_name="BCCI Official SMAT Archive",
        tier=EvidenceTier.TIER_1_OFFICIAL,
        reliability=SourceReliability.TIER_1_OFFICIAL,
        coverage_competitions=["Syed Mushtaq Ali Trophy"],
        granularity="SCORECARD_ONLY",
        balls_per_over_default=6,
        licence="RESTRICTED",
        is_active=True,
        is_mockable=True,
    ),
    EvidenceSource(
        source_id="S18C",
        source_name="BCCI Official Vijay Hazare Trophy Archive",
        tier=EvidenceTier.TIER_1_OFFICIAL,
        reliability=SourceReliability.TIER_1_OFFICIAL,
        coverage_competitions=["Vijay Hazare Trophy"],
        granularity="SCORECARD_ONLY",
        balls_per_over_default=6,
        licence="RESTRICTED",
        is_active=True,
        is_mockable=True,
    ),
    EvidenceSource(
        source_id="S18D",
        source_name="BCCI Official Duleep Trophy Archive",
        tier=EvidenceTier.TIER_1_OFFICIAL,
        reliability=SourceReliability.TIER_1_OFFICIAL,
        coverage_competitions=["Duleep Trophy"],
        granularity="SCORECARD_ONLY",
        balls_per_over_default=6,
        licence="RESTRICTED",
        is_active=True,
        is_mockable=True,
    ),
    EvidenceSource(
        source_id="S18E",
        source_name="BCCI Official Cooch Behar Trophy U-19 Archive",
        tier=EvidenceTier.TIER_1_OFFICIAL,
        reliability=SourceReliability.TIER_1_OFFICIAL,
        coverage_competitions=["Cooch Behar Trophy"],
        granularity="SCORECARD_ONLY",
        balls_per_over_default=6,
        licence="RESTRICTED",
        is_active=True,
        is_mockable=True,
    ),
    EvidenceSource(
        source_id="S18F",
        source_name="BCCI Official Vinoo Mankad Trophy U-19 Archive",
        tier=EvidenceTier.TIER_1_OFFICIAL,
        reliability=SourceReliability.TIER_1_OFFICIAL,
        coverage_competitions=["Vinoo Mankad Trophy"],
        granularity="SCORECARD_ONLY",
        balls_per_over_default=6,
        licence="RESTRICTED",
        is_active=True,
        is_mockable=True,
    ),
    EvidenceSource(
        source_id="S18G",
        source_name="BCCI Official Col CK Nayudu U-23/U-25 Archive",
        tier=EvidenceTier.TIER_1_OFFICIAL,
        reliability=SourceReliability.TIER_1_OFFICIAL,
        coverage_competitions=["Col CK Nayudu Trophy"],
        granularity="SCORECARD_ONLY",
        balls_per_over_default=6,
        licence="RESTRICTED",
        is_active=True,
        is_mockable=True,
    ),
    EvidenceSource(
        source_id="S18H",
        source_name="BCCI Official Vijay Merchant Trophy U-16 Archive",
        tier=EvidenceTier.TIER_1_OFFICIAL,
        reliability=SourceReliability.TIER_1_OFFICIAL,
        coverage_competitions=["Vijay Merchant Trophy"],
        granularity="SCORECARD_ONLY",
        balls_per_over_default=6,
        licence="RESTRICTED",
        is_active=True,
        is_mockable=True,
    ),
    EvidenceSource(
        source_id="S19A",
        source_name="CricSheet International Match Archive",
        tier=EvidenceTier.TIER_2_COMMERCIAL,
        reliability=SourceReliability.TIER_2_COMMERCIAL_ARCHIVE,
        coverage_competitions=["ICC Cricket World Cup", "ICC Men's T20 World Cup"],
        granularity="BALL_BY_BALL",
        balls_per_over_default=6,
        licence="ODC-By v1.0",
        is_active=True,
        is_mockable=True,
    ),
    EvidenceSource(
        source_id="S19B",
        source_name="ICC / ACC Youth International Match Archive",
        tier=EvidenceTier.TIER_2_COMMERCIAL,
        reliability=SourceReliability.TIER_2_COMMERCIAL_ARCHIVE,
        coverage_competitions=["Youth International"],
        granularity="SCORECARD_ONLY",
        balls_per_over_default=6,
        licence="RESTRICTED",
        is_active=True,
        is_mockable=True,
    ),
    EvidenceSource(
        source_id="S20A",
        source_name="Secondary Media Archive (ESPNcricinfo / Cricbuzz)",
        tier=EvidenceTier.TIER_3_MEDIA,
        reliability=SourceReliability.TIER_3_COMMUNITY_SCRAPE,
        coverage_competitions=["All Supported"],
        granularity="SCORECARD_ONLY",
        balls_per_over_default=6,
        licence="RESTRICTED",
        is_active=True,
        is_mockable=True,
    ),
]


# ==============================================================================
# ResearchSourceRegistry Implementation
# ==============================================================================


class ResearchSourceRegistry:
    """Central registry tracking evidence sources, competition adapters, and claims.

    Enforces:
    1. Dataset availability tracking (CoverageStatus)
    2. Missing datasets strictly marked DATASET_UNAVAILABLE (never 0 appearances)
    3. Duplicate claim detection
    4. Multi-source conflict preservation (never overwrite or average)
    """

    def __init__(self) -> None:
        self._sources: dict[str, EvidenceSource] = {}
        self._adapters: dict[str, Any] = {}
        self._claims: list[VerificationClaim] = []
        self._conflicts: list[ResearchConflict] = []
        self._dataset_availability: dict[str, bool] = {}

        # Default dataset availability from supported competition specs
        for meta in SUPPORTED_COMPETITIONS.values():
            # If dataset_dir is None, it defaults to unavailable unless explicitly loaded
            self._dataset_availability[meta.canonical_name] = meta.dataset_dir is not None

    # --------------------------------------------------------------------------
    # Source Management
    # --------------------------------------------------------------------------

    def register_source(self, source: EvidenceSource) -> None:
        """Register an evidence source into the registry."""
        self._sources[source.source_id] = source

    def get_source(self, source_id: str) -> EvidenceSource | None:
        """Retrieve source by source_id."""
        return self._sources.get(source_id)

    def list_sources(
        self,
        tier: EvidenceTier | str | None = None,
        competition: str | None = None,
    ) -> list[EvidenceSource]:
        """List registered sources filtered by tier and/or competition."""
        res = list(self._sources.values())
        if tier is not None:
            tier_val = tier.value if isinstance(tier, EvidenceTier) else str(tier)
            res = [s for s in res if (s.tier.value if isinstance(s.tier, EvidenceTier) else str(s.tier)) == tier_val]
        if competition is not None:
            norm_comp = normalize_competition_name(competition)
            res = [
                s
                for s in res
                if "All Supported" in s.coverage_competitions
                or any(normalize_competition_name(c) == norm_comp for c in s.coverage_competitions)
            ]
        return res

    # --------------------------------------------------------------------------
    # Adapter Management
    # --------------------------------------------------------------------------

    def register_adapter(self, adapter: Any) -> None:
        """Register a competition adapter into the registry."""
        comp_name = adapter.get_competition_name()
        norm_name = normalize_competition_name(comp_name)
        comp_uuid = str(adapter.get_competition_uuid())
        self._adapters[norm_name] = adapter
        self._adapters[comp_uuid] = adapter

        # Sync availability state from adapter
        self._dataset_availability[norm_name] = adapter.is_dataset_available()

    def get_adapter(self, competition: str | UUID) -> Any | None:
        """Retrieve adapter by canonical name or competition UUID."""
        if isinstance(competition, UUID):
            return self._adapters.get(str(competition))
        norm_name = normalize_competition_name(str(competition))
        return self._adapters.get(norm_name) or self._adapters.get(str(competition))

    # --------------------------------------------------------------------------
    # Dataset Availability Tracking
    # --------------------------------------------------------------------------

    def is_dataset_available(self, competition: str | UUID) -> bool:
        """Check if dataset is available for a competition."""
        if isinstance(competition, UUID):
            meta = UUID_TO_COMPETITION_META.get(competition)
            if meta:
                return self._dataset_availability.get(meta.canonical_name, False)
            return self._dataset_availability.get(str(competition), False)

        norm_name = normalize_competition_name(str(competition))
        return self._dataset_availability.get(norm_name, False)

    def set_dataset_availability(self, competition: str | UUID, is_available: bool) -> None:
        """Explicitly set dataset availability for a competition."""
        if isinstance(competition, UUID):
            meta = UUID_TO_COMPETITION_META.get(competition)
            if meta:
                self._dataset_availability[meta.canonical_name] = is_available
            self._dataset_availability[str(competition)] = is_available
        else:
            norm_name = normalize_competition_name(str(competition))
            self._dataset_availability[norm_name] = is_available

    def get_coverage_status(
        self,
        competition: str | UUID,
        player_id_or_name: UUID | str | None = None,
    ) -> CoverageStatus:
        """Evaluate coverage status for a competition and optional player.

        Hard Invariant:
        Missing datasets must strictly return DATASET_UNAVAILABLE.
        Never infer confirmed non-participation or 0 appearances when dataset is missing.
        """
        available = self.is_dataset_available(competition)
        if not available:
            return CoverageStatus.DATASET_UNAVAILABLE

        if player_id_or_name is None:
            return CoverageStatus.VERIFIED_PARTICIPATION

        # Look for player claims in this competition
        norm_comp = (
            UUID_TO_COMPETITION_META[competition].canonical_name
            if isinstance(competition, UUID) and competition in UUID_TO_COMPETITION_META
            else normalize_competition_name(str(competition))
        )

        relevant_claims = self.get_claims(subject_id_or_name=player_id_or_name)
        # Check if any claim establishes participation in this competition
        has_participation = False
        is_confirmed_non_participant = False

        for claim in relevant_claims:
            # Check competition claim types
            if claim.claim_type in ("competition_appearance", "squad_membership", "match_participation"):
                c_val = str(claim.claimed_value)
                if norm_comp.lower() in c_val.lower() and claim.verification_status in (
                    PVREVerificationStatus.VERIFIED,
                    "VERIFIED",
                ):
                    has_participation = True
            elif claim.claim_type == "confirmed_non_participation":
                c_val = str(claim.claimed_value)
                if norm_comp.lower() in c_val.lower():
                    is_confirmed_non_participant = True

        if has_participation:
            return CoverageStatus.VERIFIED_PARTICIPATION
        if is_confirmed_non_participant:
            return CoverageStatus.CONFIRMED_NON_PARTICIPATION
        return CoverageStatus.NOT_ESTABLISHED

    # --------------------------------------------------------------------------
    # Claim Ingestion, Duplicate Detection & Conflict Tracking
    # --------------------------------------------------------------------------

    def record_claim(self, claim: VerificationClaim) -> tuple[bool, ResearchConflict | None]:
        """Record an external claim, evaluating duplicate detection and conflict preservation.

        Returns:
            tuple[bool, ResearchConflict | None]:
                (True, None) if claim was ingested without conflict.
                (False, None) if claim was an exact duplicate of an existing claim.
                (True, conflict) if claim introduced a conflict (both claims preserved with status CONFLICT).
        """
        claim_sub_id = claim.subject_id
        claim_name = claim.canonical_name.strip().lower()

        # Check existing claims for duplicate or conflict
        for existing in self._claims:
            # Match subject identity
            subject_matches = False
            if claim_sub_id is not None and existing.subject_id is not None:
                subject_matches = claim_sub_id == existing.subject_id
            elif claim_name and existing.canonical_name.strip().lower() == claim_name:
                subject_matches = True

            if not subject_matches:
                continue

            # Match claim type (e.g. date_of_birth, runs, appearances)
            if existing.claim_type != claim.claim_type:
                continue

            # 1. Exact Duplicate Claim Detection
            if existing.claimed_value == claim.claimed_value and str(existing.source_id) == str(claim.source_id):
                return False, None

            # 2. Conflicting Claim Detection
            if existing.claimed_value != claim.claimed_value:
                # Disagreement detected: create conflict
                conflict_id = uuid4()
                now_utc = datetime.now(UTC)

                conflict = ResearchConflict(
                    conflict_id=conflict_id,
                    claim_type=claim.claim_type,
                    subject_name=claim.canonical_name,
                    subject_id=claim.subject_id,
                    primary_source_id=existing.source_id,
                    primary_value=existing.claimed_value,
                    primary_tier=existing.source_tier,
                    conflicting_source_id=claim.source_id,
                    conflicting_value=claim.claimed_value,
                    conflicting_tier=claim.source_tier,
                    detected_at=now_utc,
                    resolution_status="UNRESOLVED",
                )

                # Mutate both claims to preserve conflict status
                existing.verification_status = PVREVerificationStatus.CONFLICT
                if conflict_id not in existing.conflict_ids:
                    existing.conflict_ids.append(conflict_id)

                claim.verification_status = PVREVerificationStatus.CONFLICT
                if conflict_id not in claim.conflict_ids:
                    claim.conflict_ids.append(conflict_id)

                self._conflicts.append(conflict)
                self._claims.append(claim)
                return True, conflict

        # 3. New valid non-conflicting claim
        self._claims.append(claim)
        return True, None

    def record_claims(self, claims: list[VerificationClaim]) -> list[ResearchConflict]:
        """Record a batch of claims, returning all newly created conflicts."""
        conflicts: list[ResearchConflict] = []
        for claim in claims:
            _, conflict = self.record_claim(claim)
            if conflict is not None:
                conflicts.append(conflict)
        return conflicts

    def get_claims(
        self,
        subject_id_or_name: UUID | str | None = None,
        claim_type: str | None = None,
    ) -> list[VerificationClaim]:
        """Retrieve claims filtered by subject and/or claim_type."""
        res = list(self._claims)
        if subject_id_or_name is not None:
            if isinstance(subject_id_or_name, UUID):
                res = [c for c in res if c.subject_id == subject_id_or_name]
            else:
                name_clean = str(subject_id_or_name).strip().lower()
                res = [
                    c
                    for c in res
                    if (c.canonical_name.strip().lower() == name_clean or str(c.subject_id) == name_clean)
                ]
        if claim_type is not None:
            res = [c for c in res if c.claim_type == claim_type]
        return res

    def get_conflicts(
        self,
        subject_id_or_name: UUID | str | None = None,
        unresolved_only: bool = True,
    ) -> list[ResearchConflict]:
        """Retrieve conflicts filtered by subject and resolution status."""
        res = list(self._conflicts)
        if subject_id_or_name is not None:
            if isinstance(subject_id_or_name, UUID):
                res = [c for c in res if c.subject_id == subject_id_or_name]
            else:
                name_clean = str(subject_id_or_name).strip().lower()
                res = [
                    c
                    for c in res
                    if (c.subject_name.strip().lower() == name_clean or str(c.subject_id) == name_clean)
                ]
        if unresolved_only:
            res = [c for c in res if c.resolution_status == "UNRESOLVED"]
        return res


def create_default_registry() -> ResearchSourceRegistry:
    """Factory creating a ResearchSourceRegistry populated with all standard sources."""
    registry = ResearchSourceRegistry()
    for src in STANDARD_EVIDENCE_SOURCES:
        registry.register_source(src)
    return registry


__all__ = [
    # Constants
    "PVRE_NAMESPACE",
    "IPL_COMPETITION_UUID",
    "SMAT_COMPETITION_UUID",
    "HUNDRED_COMPETITION_UUID",
    "BBL_COMPETITION_UUID",
    "BPL_COMPETITION_UUID",
    "PSL_COMPETITION_UUID",
    "CPL_COMPETITION_UUID",
    "SA20_COMPETITION_UUID",
    "ILT20_COMPETITION_UUID",
    "RANJI_COMPETITION_UUID",
    "VHT_COMPETITION_UUID",
    "DULEEP_COMPETITION_UUID",
    "COOCH_BEHAR_COMPETITION_UUID",
    "VINOO_MANKAD_COMPETITION_UUID",
    "CK_NAYUDU_COMPETITION_UUID",
    "VIJAY_MERCHANT_COMPETITION_UUID",
    "T20_WORLD_CUP_COMPETITION_UUID",
    "CWC_COMPETITION_UUID",
    "INTERNATIONAL_GENERAL_UUID",
    "SUPPORTED_COMPETITIONS",
    "UUID_TO_COMPETITION_META",
    "STANDARD_EVIDENCE_SOURCES",
    # Enums & Classes
    "CoverageStatus",
    "CompetitionMeta",
    "ResearchSourceRegistry",
    # Functions
    "normalize_competition_name",
    "derive_competition_uuid",
    "create_default_registry",
]
