"""Unit tests for PVRE competition discovery adapters and research source registry.

Part of Phase 04B — Player Verification & Research Engine (Milestone 2).
Validates:
1. Research source registry registration, retrieval, and evidence tier assignment
2. Dataset availability tracking (CoverageStatus) and DATASET_UNAVAILABLE hard invariant
3. The Hundred format awareness (balls_per_over = 5 vs standard 6)
4. Duplicate claim detection and multi-source conflict preservation
5. Scorecard vs BBB granularity handling and NOT_COMPUTABLE metrics
6. Deterministic offline execution (zero network calls)
"""

from __future__ import annotations

import socket
from typing import Any
from uuid import uuid4

import pytest
from src.contracts.pvre import (
    EvidenceSource,
    EvidenceTier,
    PVREVerificationStatus,
    SourceReliability,
    VerificationClaim,
)
from src.pvre.adapters import (
    BBLAdapter,
    CPLAdapter,
    DuleepTrophyAdapter,
    InternationalAdapter,
    IPLAdapter,
    JuniorDomesticAdapter,
    PSLAdapter,
    RanjiTrophyAdapter,
    SA20Adapter,
    SMATAdapter,
    TheHundredAdapter,
    VijayHazareAdapter,
    create_all_competition_adapters,
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
    STANDARD_EVIDENCE_SOURCES,
    T20_WORLD_CUP_COMPETITION_UUID,
    VHT_COMPETITION_UUID,
    VIJAY_MERCHANT_COMPETITION_UUID,
    VINOO_MANKAD_COMPETITION_UUID,
    CoverageStatus,
    ResearchSourceRegistry,
    create_default_registry,
    derive_competition_uuid,
    normalize_competition_name,
)

from tests.fixtures.pvre_adapter_fixtures import (
    DEFAULT_CLAIM_TIMESTAMP,
    MOCK_CONTRADICTORY_PLAYER_ID,
    MOCK_DOMESTIC_PROSPECT_ID,
    MOCK_SANJU_SAMSON_ID,
    MockContradictoryAdapter,
    MockDomesticAdapter,
    MockTheHundredAdapter,
    pvre_mock_adapter_registry,
)

# Reference fixture so pytest recognizes it
_ = pvre_mock_adapter_registry


# ==============================================================================
# 1. Source Registry & Evidence Tier Tests
# ==============================================================================


class TestResearchSourceRegistry:
    """Tests for ResearchSourceRegistry source management and evidence tiering."""

    def test_default_registry_sources_count_and_ids(self) -> None:
        """Verify default registry is populated with all standard sources."""
        registry = create_default_registry()
        expected_ids = {
            "S1", "S2", "S3", "S4", "S5", "S13", "S14", "S15", "S16",
            "S18A", "S18B", "S18C", "S18D", "S18E", "S18F", "S18G", "S18H",
            "S19A", "S19B", "S20A",
        }
        sources = registry.list_sources()
        found_ids = {s.source_id for s in sources}
        assert expected_ids.issubset(found_ids)
        assert len(sources) == len(STANDARD_EVIDENCE_SOURCES)

    def test_evidence_tier_classification(self) -> None:
        """Verify evidence tier assignments strictly match TRD §10."""
        registry = create_default_registry()

        # Tier 1 Official: BCCI Scorecards (S18A..S18H)
        for s_id in ["S18A", "S18B", "S18C", "S18D", "S18E", "S18F", "S18G", "S18H"]:
            src = registry.get_source(s_id)
            assert src is not None
            assert src.tier == EvidenceTier.TIER_1_OFFICIAL
            assert src.reliability == SourceReliability.TIER_1_OFFICIAL
            assert src.licence == "RESTRICTED"

        # Tier 2 Commercial: CricSheet archives (S1..S5, S13..S16, S19A)
        for s_id in ["S1", "S2", "S3", "S4", "S5", "S13", "S14", "S15", "S16", "S19A"]:
            src = registry.get_source(s_id)
            assert src is not None
            assert src.tier == EvidenceTier.TIER_2_COMMERCIAL
            assert src.reliability == SourceReliability.TIER_2_COMMERCIAL_ARCHIVE
            assert src.licence == "ODC-By v1.0"

        # Tier 3 Media: Secondary profiles (S20A)
        s20a = registry.get_source("S20A")
        assert s20a is not None
        assert s20a.tier == EvidenceTier.TIER_3_MEDIA
        assert s20a.reliability == SourceReliability.TIER_3_COMMUNITY_SCRAPE

    def test_filter_sources_by_tier(self) -> None:
        """Verify list_sources filters accurately by EvidenceTier."""
        registry = create_default_registry()
        tier_1 = registry.list_sources(tier=EvidenceTier.TIER_1_OFFICIAL)
        assert all(s.tier == EvidenceTier.TIER_1_OFFICIAL for s in tier_1)
        assert len(tier_1) == 8  # S18A..S18H

        tier_2 = registry.list_sources(tier=EvidenceTier.TIER_2_COMMERCIAL)
        assert all(s.tier == EvidenceTier.TIER_2_COMMERCIAL for s in tier_2)
        assert len(tier_2) == 11  # S1..S5, S13..S16, S19A, S19B

        tier_3 = registry.list_sources(tier=EvidenceTier.TIER_3_MEDIA)
        assert all(s.tier == EvidenceTier.TIER_3_MEDIA for s in tier_3)
        assert len(tier_3) == 1  # S20A

    def test_filter_sources_by_competition(self) -> None:
        """Verify list_sources filters by competition name."""
        registry = create_default_registry()
        ipl_sources = registry.list_sources(competition="Indian Premier League")
        # S1 covers IPL, and S20A covers All Supported
        source_ids = {s.source_id for s in ipl_sources}
        assert "S1" in source_ids
        assert "S20A" in source_ids

    def test_register_and_get_custom_source(self) -> None:
        """Verify dynamic registration of custom evidence source."""
        registry = ResearchSourceRegistry()
        custom = EvidenceSource(
            source_id="CUSTOM_01",
            source_name="Custom Scouting Feed",
            tier=EvidenceTier.TIER_4_CROWDSOURCED,
            reliability=SourceReliability.TIER_4_MANUAL_ESTIMATE,
            coverage_competitions=["Ranji Trophy"],
            granularity="SCORECARD_ONLY",
            balls_per_over_default=6,
            licence="RESTRICTED",
        )
        registry.register_source(custom)
        retrieved = registry.get_source("CUSTOM_01")
        assert retrieved == custom
        assert registry.get_source("NON_EXISTENT") is None


# ==============================================================================
# 2. Dataset Availability & Hard Invariant Tests
# ==============================================================================


class TestDatasetAvailabilityTracking:
    """Tests dataset availability states and the DATASET_UNAVAILABLE hard invariant."""

    def test_missing_dataset_emits_dataset_unavailable(
        self, pvre_mock_adapter_registry: ResearchSourceRegistry
    ) -> None:
        """Hard Invariant: Missing datasets must strictly emit DATASET_UNAVAILABLE."""
        registry = pvre_mock_adapter_registry
        # In our mock fixture, VHT is configured with is_available=False
        cov_status = registry.get_coverage_status("Vijay Hazare Trophy")
        assert cov_status == CoverageStatus.DATASET_UNAVAILABLE

    def test_missing_dataset_never_infers_zero_appearances(self) -> None:
        """Hard Invariant: Missing dataset must NEVER return 0 appearances or non-participation."""
        missing_adapter = MockDomesticAdapter(
            competition_name="Vijay Hazare Trophy",
            is_available=False,
            granularity="SCORECARD_ONLY",
        )
        summary = missing_adapter.fetch_player_summary(MOCK_DOMESTIC_PROSPECT_ID)
        assert summary["coverage_status"] == CoverageStatus.DATASET_UNAVAILABLE.value
        assert summary["matches"] is None  # MUST BE None, NEVER 0
        assert summary["innings"] is None
        assert summary["runs"] is None
        assert summary["wickets"] is None
        assert summary["balls_faced"] is None
        assert summary["balls_bowled"] is None

        # fetch_player_claims must return empty list
        claims = missing_adapter.fetch_player_claims(MOCK_DOMESTIC_PROSPECT_ID)
        assert claims == []

    def test_verified_participation_coverage(
        self, pvre_mock_adapter_registry: ResearchSourceRegistry
    ) -> None:
        """Available dataset with verified claims emits VERIFIED_PARTICIPATION."""
        registry = pvre_mock_adapter_registry
        # Sanju Samson has verified claims in IPL in the mock fixture
        adapter = registry.get_adapter("Indian Premier League")
        assert adapter is not None
        sanju_claims = adapter.fetch_player_claims("Sanju Samson")
        registry.record_claims(sanju_claims)

        status = registry.get_coverage_status("Indian Premier League", "Sanju Samson")
        assert status == CoverageStatus.VERIFIED_PARTICIPATION

    def test_confirmed_non_participation_coverage(
        self, pvre_mock_adapter_registry: ResearchSourceRegistry
    ) -> None:
        """Available dataset with affirmative negative verification emits CONFIRMED_NON_PARTICIPATION."""
        registry = pvre_mock_adapter_registry
        # Inject an explicit confirmed_non_participation claim
        neg_claim = VerificationClaim(
            claim_id=uuid4(),
            subject_id=MOCK_DOMESTIC_PROSPECT_ID,
            canonical_name="Anukul Roy",
            claim_type="confirmed_non_participation",
            claimed_value="Big Bash League",
            source_id="S13",
            source_tier=EvidenceTier.TIER_2_COMMERCIAL,
            retrieval_timestamp=DEFAULT_CLAIM_TIMESTAMP,
            verification_status=PVREVerificationStatus.VERIFIED,
        )
        registry.record_claim(neg_claim)
        status = registry.get_coverage_status("Big Bash League", "Anukul Roy")
        assert status == CoverageStatus.CONFIRMED_NON_PARTICIPATION

    def test_not_established_when_available_but_no_player_claims(
        self, pvre_mock_adapter_registry: ResearchSourceRegistry
    ) -> None:
        """Available dataset without player claims emits NOT_ESTABLISHED."""
        registry = pvre_mock_adapter_registry
        status = registry.get_coverage_status("Big Bash League", "Unknown Player")
        assert status == CoverageStatus.NOT_ESTABLISHED

    def test_explicit_set_dataset_availability(self) -> None:
        """Verify dynamic toggling of dataset availability."""
        registry = create_default_registry()
        assert not registry.is_dataset_available("Ranji Trophy")
        registry.set_dataset_availability("Ranji Trophy", True)
        assert registry.is_dataset_available("Ranji Trophy")
        assert registry.is_dataset_available(RANJI_COMPETITION_UUID)

        registry.set_dataset_availability("Ranji Trophy", False)
        assert not registry.is_dataset_available("Ranji Trophy")


# ==============================================================================
# 3. Format Awareness: The Hundred (5 Balls / Over)
# ==============================================================================


class TestTheHundredFormatAwareness:
    """Tests balls_per_over format awareness for The Hundred vs standard cricket."""

    def test_the_hundred_balls_per_over_is_five(self) -> None:
        """Critical rule: The Hundred must strictly have balls_per_over = 5."""
        hundred = TheHundredAdapter()
        assert hundred.get_balls_per_over() == 5
        assert hundred.get_format_tag() == "100-ball"
        assert hundred.get_competition_name() == "The Hundred Men's Competition"
        assert hundred.get_competition_uuid() == HUNDRED_COMPETITION_UUID

    def test_mock_the_hundred_balls_per_over_is_five(self) -> None:
        """MockTheHundredAdapter also enforces balls_per_over = 5."""
        mock_hundred = MockTheHundredAdapter()
        assert mock_hundred.get_balls_per_over() == 5
        assert mock_hundred.get_format_tag() == "100-ball"

    def test_standard_competitions_have_six_balls_per_over(self) -> None:
        """All standard competitions have balls_per_over = 6."""
        standard_adapters = [
            IPLAdapter(),
            SMATAdapter(),
            RanjiTrophyAdapter(),
            VijayHazareAdapter(),
            DuleepTrophyAdapter(),
            BBLAdapter(),
            PSLAdapter(),
            CPLAdapter(),
            SA20Adapter(),
            JuniorDomesticAdapter(),
            InternationalAdapter(),
        ]
        for adapter in standard_adapters:
            assert adapter.get_balls_per_over() == 6, f"{adapter.get_competition_name()} must have 6 balls/over"


# ==============================================================================
# 4. Duplicate Claims & Multi-Source Conflict Detection Tests
# ==============================================================================


class TestDuplicateAndConflictDetection:
    """Tests duplicate claim detection and multi-source conflict preservation."""

    def test_duplicate_claim_detection(self) -> None:
        """Ingesting identical claim from same source is detected as duplicate."""
        registry = ResearchSourceRegistry()
        claim = VerificationClaim(
            claim_id=uuid4(),
            subject_id=MOCK_SANJU_SAMSON_ID,
            canonical_name="Sanju Samson",
            claim_type="matches_played",
            claimed_value=168,
            source_id="S1",
            source_tier=EvidenceTier.TIER_2_COMMERCIAL,
            retrieval_timestamp=DEFAULT_CLAIM_TIMESTAMP,
            verification_status=PVREVerificationStatus.VERIFIED,
        )
        # First insertion: accepted
        accepted, conflict = registry.record_claim(claim)
        assert accepted is True
        assert conflict is None
        assert len(registry.get_claims(subject_id_or_name=MOCK_SANJU_SAMSON_ID)) == 1

        # Second insertion: detected as duplicate
        accepted2, conflict2 = registry.record_claim(claim)
        assert accepted2 is False
        assert conflict2 is None
        assert len(registry.get_claims(subject_id_or_name=MOCK_SANJU_SAMSON_ID)) == 1

    def test_dob_conflict_preservation(self) -> None:
        """DOB conflict creates ResearchConflict and marks both claims CONFLICT."""
        registry = ResearchSourceRegistry()
        claim_bcci = VerificationClaim(
            claim_id=uuid4(),
            subject_id=MOCK_CONTRADICTORY_PLAYER_ID,
            canonical_name="Conflict Player",
            claim_type="date_of_birth",
            claimed_value="2004-05-10",
            source_id="S18A_BCCI",
            source_tier=EvidenceTier.TIER_1_OFFICIAL,
            retrieval_timestamp=DEFAULT_CLAIM_TIMESTAMP,
            verification_status=PVREVerificationStatus.UNVERIFIED,
        )
        claim_media = VerificationClaim(
            claim_id=uuid4(),
            subject_id=MOCK_CONTRADICTORY_PLAYER_ID,
            canonical_name="Conflict Player",
            claim_type="date_of_birth",
            claimed_value="2003-11-22",
            source_id="S20A_MEDIA",
            source_tier=EvidenceTier.TIER_3_MEDIA,
            retrieval_timestamp=DEFAULT_CLAIM_TIMESTAMP,
            verification_status=PVREVerificationStatus.UNVERIFIED,
        )

        # Ingest BCCI claim
        registry.record_claim(claim_bcci)
        assert claim_bcci.verification_status == PVREVerificationStatus.UNVERIFIED

        # Ingest conflicting Media claim
        accepted, conflict = registry.record_claim(claim_media)
        assert accepted is True
        assert conflict is not None

        # Verify conflict attributes
        assert conflict.claim_type == "date_of_birth"
        assert conflict.subject_name == "Conflict Player"
        assert conflict.subject_id == MOCK_CONTRADICTORY_PLAYER_ID
        assert conflict.primary_source_id == "S18A_BCCI"
        assert conflict.primary_value == "2004-05-10"
        assert conflict.conflicting_source_id == "S20A_MEDIA"
        assert conflict.conflicting_value == "2003-11-22"
        assert conflict.resolution_status == "UNRESOLVED"

        # Verify BOTH claims mutated to status CONFLICT
        assert claim_bcci.verification_status == PVREVerificationStatus.CONFLICT
        assert claim_media.verification_status == PVREVerificationStatus.CONFLICT
        assert conflict.conflict_id in claim_bcci.conflict_ids
        assert conflict.conflict_id in claim_media.conflict_ids

        # Verify BOTH claims preserved in registry (never overwritten or averaged)
        claims = registry.get_claims(subject_id_or_name=MOCK_CONTRADICTORY_PLAYER_ID, claim_type="date_of_birth")
        assert len(claims) == 2
        values = {c.claimed_value for c in claims}
        assert values == {"2004-05-10", "2003-11-22"}

    def test_mock_contradictory_adapter_ingestion(self) -> None:
        """Verify MockContradictoryAdapter injects multiple conflicting claims."""
        registry = ResearchSourceRegistry()
        adapter = MockContradictoryAdapter()
        claims = adapter.fetch_player_claims(MOCK_CONTRADICTORY_PLAYER_ID)
        assert len(claims) == 4

        conflicts = registry.record_claims(claims)
        assert len(conflicts) == 2  # 1 DOB conflict + 1 runs_scored conflict

        unresolved = registry.get_conflicts(MOCK_CONTRADICTORY_PLAYER_ID, unresolved_only=True)
        assert len(unresolved) == 2
        conflict_types = {c.claim_type for c in unresolved}
        assert conflict_types == {"date_of_birth", "runs_scored"}


# ==============================================================================
# 5. Scorecard vs BBB Granularity Tests
# ==============================================================================


class TestScorecardVsBBBGranularity:
    """Tests handling of SCORECARD_ONLY vs BALL_BY_BALL tournaments."""

    def test_scorecard_only_adapters_return_not_computable_for_delivery_metrics(self) -> None:
        """Ranji, VHT, Duleep adapters emit NOT_COMPUTABLE for ball-level metrics."""
        scorecard_adapters = [
            RanjiTrophyAdapter(is_available=True),
            VijayHazareAdapter(is_available=True),
            DuleepTrophyAdapter(is_available=True),
            JuniorDomesticAdapter(is_available=True),
        ]
        for adapter in scorecard_adapters:
            assert adapter.get_granularity() == "SCORECARD_ONLY"
            metrics = adapter.get_delivery_metrics("Test Player")
            assert metrics["granularity"] == "SCORECARD_ONLY"
            assert metrics["dot_ball_percentage"] == PVREVerificationStatus.NOT_COMPUTABLE.value
            assert metrics["phase_economy"] == PVREVerificationStatus.NOT_COMPUTABLE.value
            assert metrics["status"] == PVREVerificationStatus.NOT_COMPUTABLE.value

    def test_ball_by_ball_adapters_granularity(self) -> None:
        """IPL, SMAT, BBL, The Hundred adapters declare BALL_BY_BALL granularity."""
        bbb_adapters = [
            IPLAdapter(is_available=True),
            SMATAdapter(is_available=True),
            TheHundredAdapter(is_available=True),
            BBLAdapter(is_available=True),
            PSLAdapter(is_available=True),
            CPLAdapter(is_available=True),
            SA20Adapter(is_available=True),
        ]
        for adapter in bbb_adapters:
            assert adapter.get_granularity() == "BALL_BY_BALL"
            metrics = adapter.get_delivery_metrics("Test Player")
            assert metrics["granularity"] == "BALL_BY_BALL"
            assert metrics["dot_ball_percentage"] == "COMPUTABLE"


# ==============================================================================
# 6. Specific Competition Adapters Completeness Tests
# ==============================================================================


class TestSpecificCompetitionAdapters:
    """Tests completeness and contracts for all supported competition adapters."""

    def test_create_all_competition_adapters_count(self) -> None:
        """Verify factory instantiates all 16 supported adapters."""
        adapters = create_all_competition_adapters()
        assert len(adapters) >= 12
        names = {a.get_competition_name() for a in adapters}
        expected = {
            "Indian Premier League",
            "Syed Mushtaq Ali Trophy",
            "The Hundred Men's Competition",
            "Big Bash League",
            "Pakistan Super League",
            "Caribbean Premier League",
            "SA20",
            "Ranji Trophy",
            "Vijay Hazare Trophy",
            "Duleep Trophy",
            "Cooch Behar Trophy",
            "Vinoo Mankad Trophy",
            "Col CK Nayudu Trophy",
            "Vijay Merchant Trophy",
            "ICC Men's T20 World Cup",
            "ICC Cricket World Cup",
        }
        assert expected.issubset(names)

    def test_deterministic_uuids_across_competitions(self) -> None:
        """Verify deterministic UUID mapping matches canonical values."""
        assert derive_competition_uuid("Indian Premier League") == IPL_COMPETITION_UUID
        assert derive_competition_uuid("Syed Mushtaq Ali Trophy") == SMAT_COMPETITION_UUID
        assert derive_competition_uuid("The Hundred Men's Competition") == HUNDRED_COMPETITION_UUID
        assert derive_competition_uuid("Big Bash League") == BBL_COMPETITION_UUID
        assert derive_competition_uuid("Pakistan Super League") == PSL_COMPETITION_UUID
        assert derive_competition_uuid("Caribbean Premier League") == CPL_COMPETITION_UUID
        assert derive_competition_uuid("SA20") == SA20_COMPETITION_UUID
        assert derive_competition_uuid("Ranji Trophy") == RANJI_COMPETITION_UUID
        assert derive_competition_uuid("Vijay Hazare Trophy") == VHT_COMPETITION_UUID
        assert derive_competition_uuid("Duleep Trophy") == DULEEP_COMPETITION_UUID
        assert derive_competition_uuid("Cooch Behar Trophy") == COOCH_BEHAR_COMPETITION_UUID
        assert derive_competition_uuid("Vinoo Mankad Trophy") == VINOO_MANKAD_COMPETITION_UUID
        assert derive_competition_uuid("Col CK Nayudu Trophy") == CK_NAYUDU_COMPETITION_UUID
        assert derive_competition_uuid("Vijay Merchant Trophy") == VIJAY_MERCHANT_COMPETITION_UUID
        assert derive_competition_uuid("ICC Men's T20 World Cup") == T20_WORLD_CUP_COMPETITION_UUID
        assert derive_competition_uuid("ICC Cricket World Cup") == CWC_COMPETITION_UUID

    def test_normalize_competition_names(self) -> None:
        """Verify normalization handles common shorthand aliases."""
        assert normalize_competition_name("ipl") == "Indian Premier League"
        assert normalize_competition_name("SMAT") == "Syed Mushtaq Ali Trophy"
        assert normalize_competition_name("The Hundred") == "The Hundred Men's Competition"
        assert normalize_competition_name("bbl") == "Big Bash League"
        assert normalize_competition_name("Ranji") == "Ranji Trophy"
        assert normalize_competition_name("VHT") == "Vijay Hazare Trophy"
        assert normalize_competition_name("Duleep") == "Duleep Trophy"


# ==============================================================================
# 7. Offline Determinism (0 Network Calls)
# ==============================================================================


class TestOfflineDeterminism:
    """Guarantees zero network calls during adapter execution."""

    def test_zero_network_calls_guaranteed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Monkeypatch socket.socket to fail if any external network call is made."""
        def guarded_socket(*args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("NETWORK CALL PROHIBITED: Adapters must operate strictly offline.")

        monkeypatch.setattr(socket, "socket", guarded_socket)

        # Execute registry creation, adapter claim fetching, and summaries
        registry = create_default_registry()
        adapters = create_all_competition_adapters()
        for adapter in adapters:
            registry.register_adapter(adapter)
            _ = adapter.is_dataset_available()
            _ = adapter.fetch_player_claims("Sanju Samson")
            _ = adapter.fetch_player_summary("Sanju Samson")
            _ = adapter.get_delivery_metrics("Sanju Samson")

        # Must succeed with 0 socket calls
        assert len(registry.list_sources()) > 0
