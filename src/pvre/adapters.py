"""Competition Research & Discovery Adapters for PVRE.

Part of Phase 04B — Player Verification & Research Engine (Milestone 2).
Provides offline, deterministic competition adapters across supported tournaments
(IPL, SMAT, Ranji Trophy, Vijay Hazare Trophy, Duleep Trophy, BBL, PSL, CPL, SA20,
The Hundred, junior competitions, and international cricket).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from src.contracts.pvre import (
    EvidenceTier,
    PVREVerificationStatus,
    VerificationClaim,
)
from src.pvre.source_registry import (
    BBL_COMPETITION_UUID,
    CK_NAYUDU_COMPETITION_UUID,
    COOCH_BEHAR_COMPETITION_UUID,
    CPL_COMPETITION_UUID,
    CWC_COMPETITION_UUID,
    DULEEP_COMPETITION_UUID,
    HUNDRED_COMPETITION_UUID,
    IPL_COMPETITION_UUID,
    PSL_COMPETITION_UUID,
    RANJI_COMPETITION_UUID,
    SA20_COMPETITION_UUID,
    SMAT_COMPETITION_UUID,
    SUPPORTED_COMPETITIONS,
    T20_WORLD_CUP_COMPETITION_UUID,
    VHT_COMPETITION_UUID,
    VIJAY_MERCHANT_COMPETITION_UUID,
    VINOO_MANKAD_COMPETITION_UUID,
    CoverageStatus,
)

# ==============================================================================
# Base Competition Adapter Interface
# ==============================================================================


class BaseCompetitionAdapter(ABC):
    """Abstract base adapter for competition discovery and player research.

    Enforces deterministic offline execution, strict dataset availability tracking,
    balls-per-over format awareness, and scorecard vs BBB granularity isolation.
    """

    def __init__(
        self,
        dataset_path: Path | str | None = None,
        is_available: bool | None = None,
        initial_claims: list[VerificationClaim] | None = None,
    ) -> None:
        self._dataset_path = Path(dataset_path) if dataset_path else None
        self._custom_availability = is_available
        self._claims_cache: list[VerificationClaim] = list(initial_claims or [])

    @abstractmethod
    def get_competition_uuid(self) -> UUID:
        """Deterministic competition UUID."""
        ...

    @abstractmethod
    def get_competition_name(self) -> str:
        """Canonical competition name."""
        ...

    @abstractmethod
    def get_evidence_tier(self) -> EvidenceTier:
        """Evidence tier according to TRD §10 taxonomy."""
        ...

    def is_dataset_available(self) -> bool:
        """Check whether competition dataset is accessible in offline storage."""
        if self._custom_availability is not None:
            return self._custom_availability
        if self._dataset_path is not None:
            return self._dataset_path.exists()
        # Check default local lake path if registered in SUPPORTED_COMPETITIONS
        comp_name = self.get_competition_name()
        meta = SUPPORTED_COMPETITIONS.get(comp_name)
        if meta and meta.dataset_dir:
            return (Path("datasets") / meta.dataset_dir).exists()
        return False

    def set_dataset_available(self, is_available: bool) -> None:
        """Override dataset availability flag."""
        self._custom_availability = is_available

    @abstractmethod
    def get_format_tag(self) -> str:
        """Format tag: T20, First-Class, List A, 100-ball, ODI, T20I."""
        ...

    def get_balls_per_over(self) -> int:
        """Balls per over: 5 for The Hundred, 6 for standard cricket."""
        return 6

    def get_licence(self) -> str:
        """Dataset licence: ODC-By v1.0 or RESTRICTED."""
        comp_name = self.get_competition_name()
        meta = SUPPORTED_COMPETITIONS.get(comp_name)
        return meta.default_licence if meta else "RESTRICTED"

    def get_granularity(self) -> str:
        """Data granularity: BALL_BY_BALL or SCORECARD_ONLY."""
        comp_name = self.get_competition_name()
        meta = SUPPORTED_COMPETITIONS.get(comp_name)
        return meta.granularity if meta else "SCORECARD_ONLY"

    def add_claim(self, claim: VerificationClaim) -> None:
        """Add a verification claim to this adapter's offline cache."""
        self._claims_cache.append(claim)

    def fetch_player_claims(self, canonical_player_id_or_name: UUID | str) -> list[VerificationClaim]:
        """Retrieve verified player claims for this competition.

        Hard Invariant:
        If dataset is unavailable, returns empty claim list (never fabricated 0 stats).
        """
        if not self.is_dataset_available():
            return []

        search_key = (
            str(canonical_player_id_or_name).strip().lower()
            if not isinstance(canonical_player_id_or_name, UUID)
            else canonical_player_id_or_name
        )

        res: list[VerificationClaim] = []
        for claim in self._claims_cache:
            if isinstance(search_key, UUID):
                if claim.subject_id == search_key:
                    res.append(claim)
            else:
                if (
                    claim.canonical_name.strip().lower() == search_key
                    or (claim.subject_id and str(claim.subject_id).lower() == search_key)
                ):
                    res.append(claim)
        return res

    def fetch_player_summary(self, canonical_player_id_or_name: UUID | str) -> dict[str, Any]:
        """Retrieve high-level player performance summary for this competition.

        Hard Invariant:
        When dataset is unavailable, matches is None (never 0).
        """
        if not self.is_dataset_available():
            return {
                "competition_uuid": str(self.get_competition_uuid()),
                "competition_name": self.get_competition_name(),
                "format_tag": self.get_format_tag(),
                "balls_per_over": self.get_balls_per_over(),
                "coverage_status": CoverageStatus.DATASET_UNAVAILABLE.value,
                "matches": None,
                "innings": None,
                "runs": None,
                "wickets": None,
                "balls_faced": None,
                "balls_bowled": None,
                "granularity": self.get_granularity(),
            }

        claims = self.fetch_player_claims(canonical_player_id_or_name)
        if not claims:
            return {
                "competition_uuid": str(self.get_competition_uuid()),
                "competition_name": self.get_competition_name(),
                "format_tag": self.get_format_tag(),
                "balls_per_over": self.get_balls_per_over(),
                "coverage_status": CoverageStatus.NOT_ESTABLISHED.value,
                "matches": None,
                "innings": None,
                "runs": None,
                "wickets": None,
                "balls_faced": None,
                "balls_bowled": None,
                "granularity": self.get_granularity(),
            }

        # Aggregate summary from verified claims
        matches: int | None = None
        innings: int | None = None
        runs: int | None = None
        wickets: int | None = None
        balls_faced: int | None = None
        balls_bowled: int | None = None

        for c in claims:
            if c.claim_type == "matches_played" and isinstance(c.claimed_value, int):
                matches = c.claimed_value
            elif c.claim_type == "innings_batted" and isinstance(c.claimed_value, int):
                innings = c.claimed_value
            elif c.claim_type == "runs_scored" and isinstance(c.claimed_value, int):
                runs = c.claimed_value
            elif c.claim_type == "wickets_taken" and isinstance(c.claimed_value, int):
                wickets = c.claimed_value
            elif c.claim_type == "balls_faced" and isinstance(c.claimed_value, int):
                balls_faced = c.claimed_value
            elif c.claim_type == "balls_bowled" and isinstance(c.claimed_value, int):
                balls_bowled = c.claimed_value

        return {
            "competition_uuid": str(self.get_competition_uuid()),
            "competition_name": self.get_competition_name(),
            "format_tag": self.get_format_tag(),
            "balls_per_over": self.get_balls_per_over(),
            "coverage_status": CoverageStatus.VERIFIED_PARTICIPATION.value,
            "matches": matches,
            "innings": innings,
            "runs": runs,
            "wickets": wickets,
            "balls_faced": balls_faced,
            "balls_bowled": balls_bowled,
            "granularity": self.get_granularity(),
        }

    def get_delivery_metrics(self, canonical_player_id_or_name: UUID | str) -> dict[str, Any]:
        """Retrieve delivery-level analytics (e.g. dot %, control %).

        Emits SCORECARD_ONLY and returns NOT_COMPUTABLE when delivery logs are unavailable.
        """
        if not self.is_dataset_available():
            return {
                "coverage_status": CoverageStatus.DATASET_UNAVAILABLE.value,
                "granularity": self.get_granularity(),
                "dot_ball_percentage": PVREVerificationStatus.DATASET_UNAVAILABLE.value,
                "phase_economy": PVREVerificationStatus.DATASET_UNAVAILABLE.value,
            }

        if self.get_granularity() == "SCORECARD_ONLY":
            return {
                "coverage_status": CoverageStatus.VERIFIED_PARTICIPATION.value,
                "granularity": "SCORECARD_ONLY",
                "dot_ball_percentage": PVREVerificationStatus.NOT_COMPUTABLE.value,
                "phase_economy": PVREVerificationStatus.NOT_COMPUTABLE.value,
                "control_percentage": PVREVerificationStatus.NOT_COMPUTABLE.value,
                "boundary_percentage": PVREVerificationStatus.NOT_COMPUTABLE.value,
                "status": PVREVerificationStatus.NOT_COMPUTABLE.value,
            }

        # For BALL_BY_BALL datasets, return computability or placeholder
        return {
            "coverage_status": CoverageStatus.VERIFIED_PARTICIPATION.value,
            "granularity": "BALL_BY_BALL",
            "dot_ball_percentage": "COMPUTABLE",
            "phase_economy": "COMPUTABLE",
            "control_percentage": "COMPUTABLE",
            "status": PVREVerificationStatus.VERIFIED.value,
        }


# ==============================================================================
# Specific Competition Adapters
# ==============================================================================


class IPLAdapter(BaseCompetitionAdapter):
    """Indian Premier League (IPL) Competition Adapter."""

    def get_competition_uuid(self) -> UUID:
        return IPL_COMPETITION_UUID

    def get_competition_name(self) -> str:
        return "Indian Premier League"

    def get_evidence_tier(self) -> EvidenceTier:
        return EvidenceTier.TIER_2_COMMERCIAL

    def get_format_tag(self) -> str:
        return "T20"


class SMATAdapter(BaseCompetitionAdapter):
    """Syed Mushtaq Ali Trophy (SMAT) Competition Adapter."""

    def get_competition_uuid(self) -> UUID:
        return SMAT_COMPETITION_UUID

    def get_competition_name(self) -> str:
        return "Syed Mushtaq Ali Trophy"

    def get_evidence_tier(self) -> EvidenceTier:
        return EvidenceTier.TIER_2_COMMERCIAL

    def get_format_tag(self) -> str:
        return "T20"


class TheHundredAdapter(BaseCompetitionAdapter):
    """The Hundred Men's Competition Adapter.

    Critical rule: balls_per_over must strictly equal 5.
    """

    def get_competition_uuid(self) -> UUID:
        return HUNDRED_COMPETITION_UUID

    def get_competition_name(self) -> str:
        return "The Hundred Men's Competition"

    def get_evidence_tier(self) -> EvidenceTier:
        return EvidenceTier.TIER_2_COMMERCIAL

    def get_format_tag(self) -> str:
        return "100-ball"

    def get_balls_per_over(self) -> int:
        return 5


class BBLAdapter(BaseCompetitionAdapter):
    """Big Bash League (BBL) Competition Adapter."""

    def get_competition_uuid(self) -> UUID:
        return BBL_COMPETITION_UUID

    def get_competition_name(self) -> str:
        return "Big Bash League"

    def get_evidence_tier(self) -> EvidenceTier:
        return EvidenceTier.TIER_2_COMMERCIAL

    def get_format_tag(self) -> str:
        return "T20"


class PSLAdapter(BaseCompetitionAdapter):
    """Pakistan Super League (PSL) Competition Adapter."""

    def get_competition_uuid(self) -> UUID:
        return PSL_COMPETITION_UUID

    def get_competition_name(self) -> str:
        return "Pakistan Super League"

    def get_evidence_tier(self) -> EvidenceTier:
        return EvidenceTier.TIER_2_COMMERCIAL

    def get_format_tag(self) -> str:
        return "T20"


class CPLAdapter(BaseCompetitionAdapter):
    """Caribbean Premier League (CPL) Competition Adapter."""

    def get_competition_uuid(self) -> UUID:
        return CPL_COMPETITION_UUID

    def get_competition_name(self) -> str:
        return "Caribbean Premier League"

    def get_evidence_tier(self) -> EvidenceTier:
        return EvidenceTier.TIER_2_COMMERCIAL

    def get_format_tag(self) -> str:
        return "T20"


class SA20Adapter(BaseCompetitionAdapter):
    """SA20 Competition Adapter."""

    def get_competition_uuid(self) -> UUID:
        return SA20_COMPETITION_UUID

    def get_competition_name(self) -> str:
        return "SA20"

    def get_evidence_tier(self) -> EvidenceTier:
        return EvidenceTier.TIER_2_COMMERCIAL

    def get_format_tag(self) -> str:
        return "T20"


class RanjiTrophyAdapter(BaseCompetitionAdapter):
    """Ranji Trophy Competition Adapter (BCCI First-Class).

    Granularity: SCORECARD_ONLY. Delivery metrics return NOT_COMPUTABLE.
    """

    def get_competition_uuid(self) -> UUID:
        return RANJI_COMPETITION_UUID

    def get_competition_name(self) -> str:
        return "Ranji Trophy"

    def get_evidence_tier(self) -> EvidenceTier:
        return EvidenceTier.TIER_1_OFFICIAL

    def get_format_tag(self) -> str:
        return "First-Class"


class VijayHazareAdapter(BaseCompetitionAdapter):
    """Vijay Hazare Trophy Competition Adapter (BCCI List A).

    Granularity: SCORECARD_ONLY. Delivery metrics return NOT_COMPUTABLE.
    """

    def get_competition_uuid(self) -> UUID:
        return VHT_COMPETITION_UUID

    def get_competition_name(self) -> str:
        return "Vijay Hazare Trophy"

    def get_evidence_tier(self) -> EvidenceTier:
        return EvidenceTier.TIER_1_OFFICIAL

    def get_format_tag(self) -> str:
        return "List A"


class DuleepTrophyAdapter(BaseCompetitionAdapter):
    """Duleep Trophy Competition Adapter (BCCI Zonal First-Class).

    Granularity: SCORECARD_ONLY. Delivery metrics return NOT_COMPUTABLE.
    """

    def get_competition_uuid(self) -> UUID:
        return DULEEP_COMPETITION_UUID

    def get_competition_name(self) -> str:
        return "Duleep Trophy"

    def get_evidence_tier(self) -> EvidenceTier:
        return EvidenceTier.TIER_1_OFFICIAL

    def get_format_tag(self) -> str:
        return "First-Class"


class JuniorDomesticAdapter(BaseCompetitionAdapter):
    """BCCI Junior Domestic Tournaments Adapter (Cooch Behar, Vinoo Mankad, CK Nayudu, Vijay Merchant).

    Granularity: SCORECARD_ONLY. In junior scorecards, missing balls faced must stay None.
    """

    def __init__(
        self,
        competition_name: str = "Cooch Behar Trophy",
        competition_uuid: UUID | None = None,
        format_tag: str = "First-Class",
        dataset_path: Path | str | None = None,
        is_available: bool | None = None,
        initial_claims: list[VerificationClaim] | None = None,
    ) -> None:
        super().__init__(dataset_path, is_available, initial_claims)
        self._comp_name = competition_name
        self._format_tag = format_tag

        if competition_uuid:
            self._comp_uuid = competition_uuid
        elif "cooch" in competition_name.lower():
            self._comp_uuid = COOCH_BEHAR_COMPETITION_UUID
        elif "vinoo" in competition_name.lower():
            self._comp_uuid = VINOO_MANKAD_COMPETITION_UUID
        elif "ck nayudu" in competition_name.lower():
            self._comp_uuid = CK_NAYUDU_COMPETITION_UUID
        elif "merchant" in competition_name.lower():
            self._comp_uuid = VIJAY_MERCHANT_COMPETITION_UUID
        else:
            self._comp_uuid = uuid4()

    def get_competition_uuid(self) -> UUID:
        return self._comp_uuid

    def get_competition_name(self) -> str:
        return self._comp_name

    def get_evidence_tier(self) -> EvidenceTier:
        return EvidenceTier.TIER_1_OFFICIAL

    def get_format_tag(self) -> str:
        return self._format_tag


class InternationalAdapter(BaseCompetitionAdapter):
    """International Cricket Adapter (ICC CWC, T20 World Cup, Bilateral Tests/ODIs/T20Is)."""

    def __init__(
        self,
        competition_name: str = "ICC Men's T20 World Cup",
        competition_uuid: UUID | None = None,
        format_tag: str = "T20I",
        dataset_path: Path | str | None = None,
        is_available: bool | None = None,
        initial_claims: list[VerificationClaim] | None = None,
    ) -> None:
        super().__init__(dataset_path, is_available, initial_claims)
        self._comp_name = competition_name
        self._format_tag = format_tag
        if competition_uuid:
            self._comp_uuid = competition_uuid
        elif "t20" in competition_name.lower():
            self._comp_uuid = T20_WORLD_CUP_COMPETITION_UUID
        else:
            self._comp_uuid = CWC_COMPETITION_UUID

    def get_competition_uuid(self) -> UUID:
        return self._comp_uuid

    def get_competition_name(self) -> str:
        return self._comp_name

    def get_evidence_tier(self) -> EvidenceTier:
        return EvidenceTier.TIER_2_COMMERCIAL

    def get_format_tag(self) -> str:
        return self._format_tag


# ==============================================================================
# Helper Factory
# ==============================================================================


def create_all_competition_adapters() -> list[BaseCompetitionAdapter]:
    """Create standard instances of all core competition adapters."""
    return [
        IPLAdapter(),
        SMATAdapter(),
        TheHundredAdapter(),
        BBLAdapter(),
        PSLAdapter(),
        CPLAdapter(),
        SA20Adapter(),
        RanjiTrophyAdapter(),
        VijayHazareAdapter(),
        DuleepTrophyAdapter(),
        JuniorDomesticAdapter(competition_name="Cooch Behar Trophy", format_tag="First-Class"),
        JuniorDomesticAdapter(competition_name="Vinoo Mankad Trophy", format_tag="List A"),
        JuniorDomesticAdapter(competition_name="Col CK Nayudu Trophy", format_tag="First-Class"),
        JuniorDomesticAdapter(competition_name="Vijay Merchant Trophy", format_tag="First-Class"),
        InternationalAdapter(competition_name="ICC Men's T20 World Cup", format_tag="T20I"),
        InternationalAdapter(competition_name="ICC Cricket World Cup", format_tag="ODI"),
    ]


__all__ = [
    # Base
    "BaseCompetitionAdapter",
    # Specific Adapters
    "IPLAdapter",
    "SMATAdapter",
    "TheHundredAdapter",
    "BBLAdapter",
    "PSLAdapter",
    "CPLAdapter",
    "SA20Adapter",
    "RanjiTrophyAdapter",
    "VijayHazareAdapter",
    "DuleepTrophyAdapter",
    "JuniorDomesticAdapter",
    "InternationalAdapter",
    # Factory
    "create_all_competition_adapters",
]
