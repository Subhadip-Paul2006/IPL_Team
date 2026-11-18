"""Mock adapters and test fixtures for PVRE competition discovery and source research.

Part of Phase 04B — Player Verification & Research Engine (Milestone 2).
Provides deterministic, offline mock adapters for IPL, domestic tournaments (Ranji, SMAT, VHT),
overseas leagues (BBL, PSL, CPL, SA20), The Hundred (5 balls/over), and contradictory
claims for conflict testing. ZERO network requests.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from src.contracts.pvre import (
    EvidenceTier,
    PVREVerificationStatus,
    VerificationClaim,
)
from src.pvre.adapters import BaseCompetitionAdapter
from src.pvre.source_registry import (
    BBL_COMPETITION_UUID,
    HUNDRED_COMPETITION_UUID,
    IPL_COMPETITION_UUID,
    RANJI_COMPETITION_UUID,
    SMAT_COMPETITION_UUID,
    VHT_COMPETITION_UUID,
    ResearchSourceRegistry,
    create_default_registry,
)

# Deterministic Test Player UUIDs
MOCK_SANJU_SAMSON_ID = UUID("10000000-0000-0000-0000-000000000001")
MOCK_DOMESTIC_PROSPECT_ID = UUID("10000000-0000-0000-0000-000000000003")
MOCK_CONTRADICTORY_PLAYER_ID = UUID("10000000-0000-0000-0000-000000000007")

DEFAULT_CLAIM_TIMESTAMP = datetime(2025, 3, 1, 12, 0, 0, tzinfo=UTC)


# ==============================================================================
# 1. Mock IPL Adapter
# ==============================================================================


class MockIPLAdapter(BaseCompetitionAdapter):
    """Deterministic offline mock adapter for Indian Premier League."""

    def __init__(
        self,
        is_available: bool = True,
        initial_claims: list[VerificationClaim] | None = None,
    ) -> None:
        default_claims: list[VerificationClaim] = [
            VerificationClaim(
                claim_id=uuid4(),
                subject_id=MOCK_SANJU_SAMSON_ID,
                canonical_name="Sanju Samson",
                claim_type="matches_played",
                claimed_value=168,
                source_id="S1",
                source_tier=EvidenceTier.TIER_2_COMMERCIAL,
                retrieval_timestamp=DEFAULT_CLAIM_TIMESTAMP,
                verification_status=PVREVerificationStatus.VERIFIED,
            ),
            VerificationClaim(
                claim_id=uuid4(),
                subject_id=MOCK_SANJU_SAMSON_ID,
                canonical_name="Sanju Samson",
                claim_type="runs_scored",
                claimed_value=4419,
                source_id="S1",
                source_tier=EvidenceTier.TIER_2_COMMERCIAL,
                retrieval_timestamp=DEFAULT_CLAIM_TIMESTAMP,
                verification_status=PVREVerificationStatus.VERIFIED,
            ),
            VerificationClaim(
                claim_id=uuid4(),
                subject_id=MOCK_SANJU_SAMSON_ID,
                canonical_name="Sanju Samson",
                claim_type="competition_appearance",
                claimed_value="Indian Premier League 2024",
                source_id="S1",
                source_tier=EvidenceTier.TIER_2_COMMERCIAL,
                retrieval_timestamp=DEFAULT_CLAIM_TIMESTAMP,
                verification_status=PVREVerificationStatus.VERIFIED,
            ),
        ]
        claims = list(initial_claims or default_claims)
        super().__init__(is_available=is_available, initial_claims=claims)

    def get_competition_uuid(self) -> UUID:
        return IPL_COMPETITION_UUID

    def get_competition_name(self) -> str:
        return "Indian Premier League"

    def get_evidence_tier(self) -> EvidenceTier:
        return EvidenceTier.TIER_2_COMMERCIAL

    def get_format_tag(self) -> str:
        return "T20"


# ==============================================================================
# 2. Mock Domestic Adapter (Ranji, SMAT, VHT, Junior)
# ==============================================================================


class MockDomesticAdapter(BaseCompetitionAdapter):
    """Mock adapter supporting both available and missing dataset modes.

    Supports Ranji Trophy, SMAT, Vijay Hazare Trophy, and junior tournaments.
    When is_available=False, strictly outputs DATASET_UNAVAILABLE, never 0 stats.
    """

    def __init__(
        self,
        competition_name: str = "Ranji Trophy",
        competition_uuid: UUID | None = None,
        format_tag: str = "First-Class",
        granularity: str = "SCORECARD_ONLY",
        is_available: bool = True,
        initial_claims: list[VerificationClaim] | None = None,
    ) -> None:
        self._comp_name = competition_name
        self._format_tag = format_tag
        self._granularity = granularity

        if competition_uuid:
            self._comp_uuid = competition_uuid
        elif "ranji" in competition_name.lower():
            self._comp_uuid = RANJI_COMPETITION_UUID
        elif "mushtaq" in competition_name.lower() or "smat" in competition_name.lower():
            self._comp_uuid = SMAT_COMPETITION_UUID
        elif "hazare" in competition_name.lower() or "vht" in competition_name.lower():
            self._comp_uuid = VHT_COMPETITION_UUID
        else:
            self._comp_uuid = uuid4()

        default_claims: list[VerificationClaim] = []
        if is_available:
            default_claims.append(
                VerificationClaim(
                    claim_id=uuid4(),
                    subject_id=MOCK_DOMESTIC_PROSPECT_ID,
                    canonical_name="Anukul Roy",
                    claim_type="matches_played",
                    claimed_value=32,
                    source_id="S18A",
                    source_tier=EvidenceTier.TIER_1_OFFICIAL,
                    retrieval_timestamp=DEFAULT_CLAIM_TIMESTAMP,
                    verification_status=PVREVerificationStatus.VERIFIED,
                )
            )
            default_claims.append(
                VerificationClaim(
                    claim_id=uuid4(),
                    subject_id=MOCK_DOMESTIC_PROSPECT_ID,
                    canonical_name="Anukul Roy",
                    claim_type="runs_scored",
                    claimed_value=985,
                    source_id="S18A",
                    source_tier=EvidenceTier.TIER_1_OFFICIAL,
                    retrieval_timestamp=DEFAULT_CLAIM_TIMESTAMP,
                    verification_status=PVREVerificationStatus.VERIFIED,
                )
            )
            default_claims.append(
                VerificationClaim(
                    claim_id=uuid4(),
                    subject_id=MOCK_DOMESTIC_PROSPECT_ID,
                    canonical_name="Anukul Roy",
                    claim_type="competition_appearance",
                    claimed_value=competition_name,
                    source_id="S18A",
                    source_tier=EvidenceTier.TIER_1_OFFICIAL,
                    retrieval_timestamp=DEFAULT_CLAIM_TIMESTAMP,
                    verification_status=PVREVerificationStatus.VERIFIED,
                )
            )

        claims = list(initial_claims if initial_claims is not None else default_claims)
        super().__init__(is_available=is_available, initial_claims=claims)

    def get_competition_uuid(self) -> UUID:
        return self._comp_uuid

    def get_competition_name(self) -> str:
        return self._comp_name

    def get_evidence_tier(self) -> EvidenceTier:
        return EvidenceTier.TIER_1_OFFICIAL

    def get_format_tag(self) -> str:
        return self._format_tag

    def get_granularity(self) -> str:
        return self._granularity


# ==============================================================================
# 3. Mock Overseas Adapter (BBL, PSL, CPL, SA20)
# ==============================================================================


class MockOverseasAdapter(BaseCompetitionAdapter):
    """Mock adapter for foreign franchise leagues (BBL, PSL, CPL, SA20)."""

    def __init__(
        self,
        competition_name: str = "Big Bash League",
        competition_uuid: UUID = BBL_COMPETITION_UUID,
        is_available: bool = True,
        initial_claims: list[VerificationClaim] | None = None,
    ) -> None:
        self._comp_name = competition_name
        self._comp_uuid = competition_uuid
        super().__init__(is_available=is_available, initial_claims=initial_claims or [])

    def get_competition_uuid(self) -> UUID:
        return self._comp_uuid

    def get_competition_name(self) -> str:
        return self._comp_name

    def get_evidence_tier(self) -> EvidenceTier:
        return EvidenceTier.TIER_2_COMMERCIAL

    def get_format_tag(self) -> str:
        return "T20"


# ==============================================================================
# 4. Mock The Hundred Adapter (balls_per_over = 5)
# ==============================================================================


class MockTheHundredAdapter(BaseCompetitionAdapter):
    """Mock adapter for The Hundred Men's Competition enforcing balls_per_over=5."""

    def __init__(
        self,
        is_available: bool = True,
        initial_claims: list[VerificationClaim] | None = None,
    ) -> None:
        super().__init__(is_available=is_available, initial_claims=initial_claims or [])

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


# ==============================================================================
# 5. Mock Contradictory Adapter (Conflict Injection)
# ==============================================================================


class MockContradictoryAdapter(BaseCompetitionAdapter):
    """Adapter injecting contradictory claims across DOB, match runs, and appearances.

    Used to test multi-source conflict preservation and REVIEW_REQUIRED safety traps.
    """

    def __init__(
        self,
        subject_name: str = "Conflict Player",
        subject_id: UUID = MOCK_CONTRADICTORY_PLAYER_ID,
        is_available: bool = True,
    ) -> None:
        self._subject_name = subject_name
        self._subject_id = subject_id

        # Pairs of contradictory claims
        claims: list[VerificationClaim] = [
            # DOB Conflict: BCCI roster vs Media profile
            VerificationClaim(
                claim_id=uuid4(),
                subject_id=subject_id,
                canonical_name=subject_name,
                claim_type="date_of_birth",
                claimed_value="2004-05-10",
                source_id="S18A_BCCI",
                source_tier=EvidenceTier.TIER_1_OFFICIAL,
                retrieval_timestamp=DEFAULT_CLAIM_TIMESTAMP,
                verification_status=PVREVerificationStatus.UNVERIFIED,
            ),
            VerificationClaim(
                claim_id=uuid4(),
                subject_id=subject_id,
                canonical_name=subject_name,
                claim_type="date_of_birth",
                claimed_value="2003-11-22",
                source_id="S20A_MEDIA",
                source_tier=EvidenceTier.TIER_3_MEDIA,
                retrieval_timestamp=DEFAULT_CLAIM_TIMESTAMP,
                verification_status=PVREVerificationStatus.UNVERIFIED,
            ),
            # Career Runs Conflict: CricSheet delivery ledger vs Official Scorecard
            VerificationClaim(
                claim_id=uuid4(),
                subject_id=subject_id,
                canonical_name=subject_name,
                claim_type="runs_scored",
                claimed_value=450,
                source_id="S5_CRICSHEET",
                source_tier=EvidenceTier.TIER_2_COMMERCIAL,
                retrieval_timestamp=DEFAULT_CLAIM_TIMESTAMP,
                verification_status=PVREVerificationStatus.UNVERIFIED,
            ),
            VerificationClaim(
                claim_id=uuid4(),
                subject_id=subject_id,
                canonical_name=subject_name,
                claim_type="runs_scored",
                claimed_value=495,
                source_id="S18B_BCCI_SCORECARD",
                source_tier=EvidenceTier.TIER_1_OFFICIAL,
                retrieval_timestamp=DEFAULT_CLAIM_TIMESTAMP,
                verification_status=PVREVerificationStatus.UNVERIFIED,
            ),
        ]
        super().__init__(is_available=is_available, initial_claims=claims)

    def get_competition_uuid(self) -> UUID:
        return UUID("20000000-0000-0000-0000-000000000099")

    def get_competition_name(self) -> str:
        return "Contradictory Research League"

    def get_evidence_tier(self) -> EvidenceTier:
        return EvidenceTier.TIER_1_OFFICIAL

    def get_format_tag(self) -> str:
        return "T20"


# ==============================================================================
# Pytest Fixtures
# ==============================================================================


@pytest.fixture
def pvre_mock_adapter_registry() -> ResearchSourceRegistry:
    """Pytest fixture injecting a populated ResearchSourceRegistry with mock adapters."""
    registry = create_default_registry()

    ipl_adapter = MockIPLAdapter(is_available=True)
    smat_adapter = MockDomesticAdapter(
        competition_name="Syed Mushtaq Ali Trophy",
        is_available=True,
        granularity="BALL_BY_BALL",
    )
    ranji_adapter = MockDomesticAdapter(
        competition_name="Ranji Trophy",
        is_available=True,
        granularity="SCORECARD_ONLY",
    )
    vht_missing_adapter = MockDomesticAdapter(
        competition_name="Vijay Hazare Trophy",
        is_available=False,
        granularity="SCORECARD_ONLY",
    )
    hundred_adapter = MockTheHundredAdapter(is_available=True)
    bbl_adapter = MockOverseasAdapter(
        competition_name="Big Bash League",
        is_available=True,
    )
    contradictory_adapter = MockContradictoryAdapter()

    registry.register_adapter(ipl_adapter)
    registry.register_adapter(smat_adapter)
    registry.register_adapter(ranji_adapter)
    registry.register_adapter(vht_missing_adapter)
    registry.register_adapter(hundred_adapter)
    registry.register_adapter(bbl_adapter)
    registry.register_adapter(contradictory_adapter)

    return registry


__all__ = [
    # Mock Adapters
    "MockIPLAdapter",
    "MockDomesticAdapter",
    "MockOverseasAdapter",
    "MockTheHundredAdapter",
    "MockContradictoryAdapter",
    # Constants
    "MOCK_SANJU_SAMSON_ID",
    "MOCK_DOMESTIC_PROSPECT_ID",
    "MOCK_CONTRADICTORY_PLAYER_ID",
    "DEFAULT_CLAIM_TIMESTAMP",
    # Fixtures
    "pvre_mock_adapter_registry",
]
