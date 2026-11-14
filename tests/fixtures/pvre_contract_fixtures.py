"""Synthetic test fixtures and builders for PVRE (Player Verification & Research Engine) contracts.

Author: Specialist Agent 1 (Contracts & Taxonomy Specialist)
Milestone: Phase 04B M1

==============================================================================
CRITICAL DOMAIN GUARDRAIL COMPLIANCE:
- R2 / AI_INSTRUCTIONS: NEVER fabricate or hallucinate statistics, players, or memberships.
- P1: Generating synthetic / mock player or match records is STRICTLY PROHIBITED
      in application data or production stores.
- NOTICE: The synthetic fixtures in this module are EXCLUSIVELY FOR OFFLINE
  UNIT & INTEGRATION TESTS. All synthetic names, entities, and values are
  strictly scoped test fixtures. NO REAL CRICKETER STATS OR IDENTITIES ARE
  FABRICATED OR REPRESENTED IN PRODUCTION DATA.
==============================================================================
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

import pytest
from src.contracts.pvre import (
    CareerCoverageState,
    CareerVerification,
    EvidenceSource,
    EvidenceTier,
    PlayerCappedStatus,
    PlayerResearchOutput,
    PlayerResearchRequest,
    PVREOutputContract,
    PVRERequestContract,
    PVREReviewDossierContract,
    PVREReviewStatus,
    PVREVerificationStatus,
    ReplaceabilitySignal,
    ReplacementCandidateEvidence,
    ReplacementResearchRequest,
    ResearchConflict,
    ResearchCoverage,
    ResearchMode,
    RouteStatus,
    SourceReliability,
    VerificationClaim,
)

# =============================================================================
# Canonical Deterministic UUID Constants for Test Scenarios
# =============================================================================

SYNTHETIC_RESEARCH_RUN_ID = UUID("11111111-1111-1111-1111-111111111111")
SYNTHETIC_TARGET_SEASON_ID = UUID("22222222-2222-2222-2222-222222222222")
SYNTHETIC_POLICY_ID = UUID("33333333-3333-3333-3333-333333333333")
SYNTHETIC_DOSSIER_ID = UUID("44444444-4444-4444-4444-444444444444")
SYNTHETIC_CLAIM_ID = UUID("55555555-5555-5555-5555-555555555555")
SYNTHETIC_CONFLICT_ID = UUID("66666666-6666-6666-6666-666666666666")
SYNTHETIC_VERIFICATION_ID = UUID("77777777-7777-7777-7777-777777777777")

# Scenario Players
SYNTHETIC_PLAYER_ID_SANJU = UUID("10000000-0000-0000-0000-000000000001")
SYNTHETIC_PLAYER_ID_SQUAD_ONLY = UUID("10000000-0000-0000-0000-000000000002")
SYNTHETIC_PLAYER_ID_UNCAPPED = UUID("10000000-0000-0000-0000-000000000003")
SYNTHETIC_PLAYER_ID_CAPPED_NON_RR = UUID("10000000-0000-0000-0000-000000000004")
SYNTHETIC_PLAYER_ID_COLLISION_A = UUID("10000000-0000-0000-0000-000000000005")
SYNTHETIC_PLAYER_ID_COLLISION_B = UUID("10000000-0000-0000-0000-000000000006")

DEFAULT_EVALUATION_DATE = date(2025, 3, 1)
DEFAULT_WINDOW_START = date(2022, 3, 1)
DEFAULT_WINDOW_END = date(2025, 3, 1)
DEFAULT_TIMESTAMP = datetime(2025, 3, 1, 12, 0, 0, tzinfo=UTC)


# =============================================================================
# Builder Functions: PVRERequestContract
# =============================================================================


def valid_pvre_request_dict(**overrides: Any) -> dict[str, Any]:
    """Return dictionary representation of a valid PVRERequestContract."""
    payload: dict[str, Any] = {
        "contract_version": "PVRE-2.2.0",
        "research_run_id": SYNTHETIC_RESEARCH_RUN_ID,
        "player_query": "Sanju Samson",
        "player_id": SYNTHETIC_PLAYER_ID_SANJU,
        "canonical_name": "Sanju Samson",
        "identity_status": "RESOLVED",
        "rr_relationship_state": "CURRENT_RR",
        "rr_current_state": "CURRENT",
        "player_capped_status": "CAPPED",
        "ipl_uncapped_eligibility": "VERIFIED_NOT_ELIGIBLE",
        "target_season_id": SYNTHETIC_TARGET_SEASON_ID,
        "evaluation_date": DEFAULT_EVALUATION_DATE,
        "research_window_years": 3,
        "force_refresh": False,
    }
    payload.update(overrides)
    return payload


def build_pvre_request(**overrides: Any) -> PVRERequestContract:
    """Build a valid PVRERequestContract instance."""
    return PVRERequestContract(**valid_pvre_request_dict(**overrides))


def build_mode_a_incumbent_request(**overrides: Any) -> PVRERequestContract:
    """Build a PVRERequestContract for a verified RR incumbent player (Mode A)."""
    return build_pvre_request(
        player_query="Sanju Samson",
        player_id=SYNTHETIC_PLAYER_ID_SANJU,
        canonical_name="Sanju Samson",
        identity_status="RESOLVED",
        rr_relationship_state="CURRENT_RR",
        rr_current_state="CURRENT",
        player_capped_status="CAPPED",
        ipl_uncapped_eligibility="VERIFIED_NOT_ELIGIBLE",
        **overrides,
    )


def build_mode_b_uncapped_request(**overrides: Any) -> PVRERequestContract:
    """Build a PVRERequestContract for a verified uncapped domestic candidate (Mode B)."""
    return build_pvre_request(
        player_query="Ashutosh Sharma",
        player_id=SYNTHETIC_PLAYER_ID_UNCAPPED,
        canonical_name="Ashutosh Sharma",
        identity_status="RESOLVED",
        rr_relationship_state="NO_VERIFIED_RR_RELATIONSHIP",
        rr_current_state="NOT_CURRENT",
        player_capped_status="UNCAPPED",
        ipl_uncapped_eligibility="VERIFIED_ELIGIBLE",
        **overrides,
    )


def build_review_required_request(**overrides: Any) -> PVRERequestContract:
    """Build a PVRERequestContract triggering human safety review."""
    return build_pvre_request(
        player_query="Amit Sharma",
        player_id=None,
        canonical_name="Amit Sharma",
        identity_status="UNRESOLVED",
        rr_relationship_state="RR_RELATIONSHIP_UNKNOWN",
        rr_current_state="UNKNOWN",
        player_capped_status="UNVERIFIED",
        ipl_uncapped_eligibility="NOT_ASSESSED",
        **overrides,
    )


def build_out_of_scope_request(**overrides: Any) -> PVRERequestContract:
    """Build a PVRERequestContract for a capped non-RR player."""
    return build_pvre_request(
        player_query="Virat Kohli",
        player_id=SYNTHETIC_PLAYER_ID_CAPPED_NON_RR,
        canonical_name="Virat Kohli",
        identity_status="RESOLVED",
        rr_relationship_state="NO_VERIFIED_RR_RELATIONSHIP",
        rr_current_state="NOT_CURRENT",
        player_capped_status="CAPPED",
        ipl_uncapped_eligibility="VERIFIED_NOT_ELIGIBLE",
        **overrides,
    )


# =============================================================================
# Builder Functions: PVREOutputContract (Authoritative 26 Fields)
# =============================================================================


def valid_pvre_output_dict(**overrides: Any) -> dict[str, Any]:
    """Return dictionary representation of a valid 26-field PVREOutputContract."""
    payload: dict[str, Any] = {
        # 1. Governance & Run Identification
        "contract_version": "PVRE-2.2.0",
        "research_run_id": SYNTHETIC_RESEARCH_RUN_ID,
        "player_id": SYNTHETIC_PLAYER_ID_SANJU,
        "canonical_name": "Sanju Samson",
        "identity_status": "RESOLVED",
        # 2. Routing & Mode Selection
        "research_mode": ResearchMode.MODE_A.value,
        "route_status": RouteStatus.ROUTED_RR_INCUMBENT.value,
        "evaluation_date": DEFAULT_EVALUATION_DATE,
        "target_season_id": SYNTHETIC_TARGET_SEASON_ID,
        # 3. Membership & Eligibility States
        "rr_relationship_state": "CURRENT_RR",
        "rr_current_state": "CURRENT",
        "player_capped_status": PlayerCappedStatus.CAPPED.value,
        "ipl_uncapped_eligibility": "VERIFIED_NOT_ELIGIBLE",
        # 4. Research Windows
        "research_window_start": DEFAULT_WINDOW_START,
        "research_window_end": DEFAULT_WINDOW_END,
        # 5. Career Coverage State
        "career_coverage_state": CareerCoverageState.COMPLETE_WITHIN_VERIFIED_SOURCES.value,
        # 6. Domain Profiles & Assessments
        "rr_historical_profile": {
            "seasons_active": ["2013", "2014", "2015", "2018", "2019", "2020", "2021", "2022", "2023", "2024"],
            "total_matches": 138,
            "total_runs": 3888,
            "strike_rate": 139.05,
            "squad_only_seasons": [],
        },
        "recent_global_performance": {
            "window_years": 3,
            "weighted_strike_rate": 145.2,
            "weighted_economy": None,
            "boundary_pct": 21.4,
            "dot_ball_pct": 32.1,
            "sample_indicators": {"matches": 42, "innings": 40, "balls_faced": 890, "wickets": 0},
            "gap_records": [],
        },
        "complete_career_profile": None,
        "replaceability_assessment": {
            "signal": ReplaceabilitySignal.RETAIN_SIGNAL.value,
            "signal_rationale": "High-impact wicketkeeper-batter captain; above benchmark across all phases.",
            "role_archetype": "TOP_ORDER_BATTER_WK",
            "confidence": 0.95,
        },
        # 7. Coverage, Provenance & Quality
        "competition_coverage": {
            "Indian Premier League": PVREVerificationStatus.VERIFIED.value,
            "Syed Mushtaq Ali Trophy": PVREVerificationStatus.VERIFIED.value,
        },
        "source_record_ids": [SYNTHETIC_CLAIM_ID, 101, 102],
        "verification_record_ids": [SYNTHETIC_VERIFICATION_ID, 201],
        "review_status": PVREReviewStatus.CLEAR.value,
        "review_reason_codes": [],
        "data_quality_summary": {
            "records_checked": 450,
            "anomalies_detected": 0,
            "scorecard_fallback_used": False,
        },
    }
    payload.update(overrides)
    return payload


def build_pvre_output(**overrides: Any) -> PVREOutputContract:
    """Build a valid 26-field PVREOutputContract instance."""
    return PVREOutputContract(**valid_pvre_output_dict(**overrides))


def build_mode_a_output(**overrides: Any) -> PVREOutputContract:
    """Build a Mode A PVREOutputContract for an incumbent."""
    return build_pvre_output(
        research_mode=ResearchMode.MODE_A.value,
        route_status=RouteStatus.ROUTED_RR_INCUMBENT.value,
        **overrides,
    )


def build_mode_b_output(**overrides: Any) -> PVREOutputContract:
    """Build a Mode B PVREOutputContract for an uncapped domestic candidate."""
    return build_pvre_output(
        player_id=SYNTHETIC_PLAYER_ID_UNCAPPED,
        canonical_name="Ashutosh Sharma",
        identity_status="RESOLVED",
        research_mode=ResearchMode.MODE_B.value,
        route_status=RouteStatus.ROUTED_UNCAPPED_CANDIDATE.value,
        rr_relationship_state="NO_VERIFIED_RR_RELATIONSHIP",
        rr_current_state="NOT_CURRENT",
        player_capped_status=PlayerCappedStatus.UNCAPPED.value,
        ipl_uncapped_eligibility="VERIFIED_ELIGIBLE",
        rr_historical_profile=None,
        recent_global_performance=None,
        complete_career_profile={
            "domestic_t20": {"matches": 28, "strike_rate": 182.4, "average": 31.5},
            "first_class": {"matches": 12, "runs": 650, "average": 34.2},
            "list_a": {"matches": 15, "runs": 480, "average": 37.0},
        },
        replaceability_assessment=None,
        competition_coverage={
            "Syed Mushtaq Ali Trophy": PVREVerificationStatus.VERIFIED.value,
            "Ranji Trophy": PVREVerificationStatus.NOT_COMPUTABLE.value,
        },
        **overrides,
    )


def build_review_required_output(**overrides: Any) -> PVREOutputContract:
    """Build a PVREOutputContract routed to safety review."""
    return build_pvre_output(
        player_id=None,
        canonical_name="Unknown Prospect",
        identity_status="UNRESOLVED",
        research_mode=ResearchMode.REVIEW_REQUIRED.value,
        route_status=RouteStatus.ROUTED_SAFETY_REVIEW.value,
        rr_relationship_state="RR_RELATIONSHIP_UNKNOWN",
        rr_current_state="UNKNOWN",
        player_capped_status=PlayerCappedStatus.UNVERIFIED.value,
        ipl_uncapped_eligibility="NOT_ASSESSED",
        career_coverage_state=CareerCoverageState.REVIEW_REQUIRED.value,
        rr_historical_profile=None,
        recent_global_performance=None,
        complete_career_profile=None,
        replaceability_assessment=None,
        review_status=PVREReviewStatus.REVIEW_REQUIRED.value,
        review_reason_codes=["UNKNOWN_PLAYER_NOT_IN_DATABASE"],
        **overrides,
    )


def build_out_of_scope_output(**overrides: Any) -> PVREOutputContract:
    """Build an Out of Scope PVREOutputContract for a capped non-RR player."""
    return build_pvre_output(
        player_id=SYNTHETIC_PLAYER_ID_CAPPED_NON_RR,
        canonical_name="Virat Kohli",
        identity_status="RESOLVED",
        research_mode=ResearchMode.OUT_OF_SCOPE.value,
        route_status=RouteStatus.ROUTED_OUT_OF_SCOPE.value,
        rr_relationship_state="NO_VERIFIED_RR_RELATIONSHIP",
        rr_current_state="NOT_CURRENT",
        player_capped_status=PlayerCappedStatus.CAPPED.value,
        ipl_uncapped_eligibility="VERIFIED_NOT_ELIGIBLE",
        rr_historical_profile=None,
        recent_global_performance=None,
        complete_career_profile=None,
        replaceability_assessment=None,
        **overrides,
    )


# =============================================================================
# Builder Functions: ReviewDossierContract
# =============================================================================


def valid_review_dossier_dict(**overrides: Any) -> dict[str, Any]:
    """Return dictionary representation of a valid ReviewDossierContract."""
    payload: dict[str, Any] = {
        "contract_version": "DOSSIER-1.0.0",
        "dossier_id": SYNTHETIC_DOSSIER_ID,
        "subject_type": "player_research",
        "subject_id": SYNTHETIC_PLAYER_ID_COLLISION_A,
        "review_status": PVREReviewStatus.REVIEW_REQUIRED.value,
        "review_reason_codes": ["COLLISION_MULTIPLE_IDENTITIES"],
        "unresolved_claims": [
            {
                "claim_field": "date_of_birth",
                "source_a": "cricsheet",
                "val_a": "2002-04-10",
                "source_b": "bcci_roster",
                "val_b": "2001-11-23",
            }
        ],
        "conflicting_source_ids": [SYNTHETIC_CLAIM_ID, 999],
        "missing_evidence": ["Official government birth certificate"],
        "recommended_manual_checks": ["Verify with BCCI registration desk"],
    }
    payload.update(overrides)
    return payload


def build_review_dossier(**overrides: Any) -> PVREReviewDossierContract:
    """Build a valid ReviewDossierContract instance."""
    return PVREReviewDossierContract(**valid_review_dossier_dict(**overrides))


# =============================================================================
# Builder Functions: ReplacementCandidateEvidence (ORIGINAL_REQUEST R4)
# =============================================================================


def valid_replacement_candidate_evidence_dict(**overrides: Any) -> dict[str, Any]:
    """Return dictionary representation of a valid ReplacementCandidateEvidence contract."""
    payload: dict[str, Any] = {
        "candidate_player_id": SYNTHETIC_PLAYER_ID_UNCAPPED,
        "canonical_name": "Ashutosh Sharma",
        "age_at_evaluation": 26.5,
        "primary_role": "FINISHER_BATTER",
        "secondary_role": "RIGHT_ARM_MEDIUM",
        "batting_hand": "RIGHT",
        "bowling_style": "RIGHT_ARM_MEDIUM",
        "ipl_uncapped_eligibility": "VERIFIED_ELIGIBLE",
        "verified_policy_id": SYNTHETIC_POLICY_ID,
        "domestic_t20_metrics": {
            "strike_rate": 182.4,
            "average": 31.5,
            "boundary_pct": 24.8,
            "dot_ball_pct": 28.2,
        },
        "first_class_metrics": {
            "matches": 12,
            "runs": 650,
            "average": 34.2,
        },
        "list_a_metrics": {
            "matches": 15,
            "runs": 480,
            "average": 37.0,
        },
        "sample_indicators": {
            "matches": 28,
            "innings": 25,
            "balls_faced": 340,
            "wickets": 4,
        },
        "evidence_tier": 1,
        "career_coverage_state": CareerCoverageState.COMPLETE_WITHIN_VERIFIED_SOURCES.value,
        "missing_competitions": [],
        "provenance_verification_ids": [SYNTHETIC_VERIFICATION_ID],
    }
    payload.update(overrides)
    return payload


def build_replacement_candidate_evidence(**overrides: Any) -> ReplacementCandidateEvidence:
    """Build a valid ReplacementCandidateEvidence contract."""
    return ReplacementCandidateEvidence(**valid_replacement_candidate_evidence_dict(**overrides))


# =============================================================================
# Builder Functions: Additional Typed Domain Contracts (ORIGINAL_REQUEST R1)
# =============================================================================


def build_player_research_request(**overrides: Any) -> PlayerResearchRequest:
    """Build a valid PlayerResearchRequest."""
    payload: dict[str, Any] = {
        "contract_version": "PVRE-2.2.0",
        "research_run_id": SYNTHETIC_RESEARCH_RUN_ID,
        "player_query": "Sanju Samson",
        "player_id": SYNTHETIC_PLAYER_ID_SANJU,
        "canonical_name": "Sanju Samson",
        "identity_status": "RESOLVED",
        "rr_relationship_state": "CURRENT_RR",
        "rr_current_state": "CURRENT",
        "player_capped_status": "CAPPED",
        "ipl_uncapped_eligibility": "VERIFIED_NOT_ELIGIBLE",
        "target_season_id": SYNTHETIC_TARGET_SEASON_ID,
        "evaluation_date": DEFAULT_EVALUATION_DATE,
        "research_window_years": 3,
        "force_refresh": False,
        "metadata": {"requester": "head_coach"},
    }
    payload.update(overrides)
    return PlayerResearchRequest(**payload)


def build_player_research_output(**overrides: Any) -> PlayerResearchOutput:
    """Build a valid PlayerResearchOutput."""
    return PlayerResearchOutput(**valid_pvre_output_dict(**overrides))


def build_replacement_research_request(**overrides: Any) -> ReplacementResearchRequest:
    """Build a valid ReplacementResearchRequest."""
    payload: dict[str, Any] = {
        "contract_version": "PVRE-2.2.0",
        "research_run_id": SYNTHETIC_RESEARCH_RUN_ID,
        "target_season_id": SYNTHETIC_TARGET_SEASON_ID,
        "evaluation_date": DEFAULT_EVALUATION_DATE,
        "target_role": "MIDDLE_ORDER_BATTER",
        "secondary_role": "SPIN_BOWLER",
        "batting_hand": "RIGHT",
        "bowling_style": "LEG_BREAK",
        "max_age": 27.0,
        "min_domestic_matches": 10,
        "must_be_uncapped": True,
        "candidate_pool_limit": 25,
        "force_refresh": False,
        "metadata": {"priority": "HIGH"},
    }
    payload.update(overrides)
    return ReplacementResearchRequest(**payload)


def build_verification_claim(**overrides: Any) -> VerificationClaim:
    """Build a valid VerificationClaim instance."""
    payload: dict[str, Any] = {
        "claim_id": SYNTHETIC_CLAIM_ID,
        "subject_id": SYNTHETIC_PLAYER_ID_SANJU,
        "canonical_name": "Sanju Samson",
        "claim_type": "DATE_OF_BIRTH",
        "claimed_value": "1994-11-11",
        "source_id": "cricsheet_ipl_male",
        "source_tier": EvidenceTier.TIER_2_COMMERCIAL.value,
        "retrieval_timestamp": DEFAULT_TIMESTAMP,
        "verification_status": PVREVerificationStatus.VERIFIED.value,
        "conflict_ids": [],
    }
    payload.update(overrides)
    return VerificationClaim(**payload)


def build_evidence_source(**overrides: Any) -> EvidenceSource:
    """Build a valid EvidenceSource instance."""
    payload: dict[str, Any] = {
        "source_id": "S1",
        "source_name": "Indian Premier League - CricSheet",
        "tier": EvidenceTier.TIER_2_COMMERCIAL.value,
        "reliability": SourceReliability.TIER_2_COMMERCIAL_ARCHIVE.value,
        "coverage_competitions": ["Indian Premier League"],
        "granularity": "BALL_BY_BALL",
        "balls_per_over_default": 6,
        "licence": "ODC-By v1.0",
        "is_active": True,
        "is_mockable": True,
    }
    payload.update(overrides)
    return EvidenceSource(**payload)


def build_research_conflict(**overrides: Any) -> ResearchConflict:
    """Build a valid ResearchConflict instance."""
    payload: dict[str, Any] = {
        "conflict_id": SYNTHETIC_CONFLICT_ID,
        "claim_type": "DATE_OF_BIRTH",
        "subject_name": "Amit Sharma",
        "subject_id": SYNTHETIC_PLAYER_ID_COLLISION_A,
        "primary_source_id": "S18A",
        "primary_value": "2003-05-15",
        "primary_tier": EvidenceTier.TIER_1_OFFICIAL.value,
        "conflicting_source_id": "S20A",
        "conflicting_value": "2002-11-20",
        "conflicting_tier": EvidenceTier.TIER_3_MEDIA.value,
        "detected_at": DEFAULT_TIMESTAMP,
        "resolution_status": "UNRESOLVED",
        "review_dossier_id": SYNTHETIC_DOSSIER_ID,
    }
    payload.update(overrides)
    return ResearchConflict(**payload)


def build_career_verification(**overrides: Any) -> CareerVerification:
    """Build a valid CareerVerification instance."""
    payload: dict[str, Any] = {
        "verification_id": SYNTHETIC_VERIFICATION_ID,
        "player_id": SYNTHETIC_PLAYER_ID_SANJU,
        "canonical_name": "Sanju Samson",
        "capped_status": PlayerCappedStatus.CAPPED.value,
        "senior_international_caps": 40,
        "youth_international_caps": 15,
        "ipl_appearances": 168,
        "rr_appearances": 138,
        "rr_squad_seasons": 11,
        "domestic_t20_appearances": 65,
        "first_class_appearances": 58,
        "list_a_appearances": 120,
        "coverage_state": CareerCoverageState.COMPLETE_WITHIN_VERIFIED_SOURCES.value,
        "verification_status": PVREVerificationStatus.VERIFIED.value,
        "verified_at": DEFAULT_TIMESTAMP,
    }
    payload.update(overrides)
    return CareerVerification(**payload)


def build_research_coverage(**overrides: Any) -> ResearchCoverage:
    """Build a valid ResearchCoverage instance."""
    payload: dict[str, Any] = {
        "evaluation_date": DEFAULT_EVALUATION_DATE,
        "coverage_state": CareerCoverageState.PARTIAL_COVERAGE.value,
        "competitions_searched": ["IPL", "SMAT", "Ranji Trophy"],
        "competitions_verified": ["IPL", "SMAT"],
        "competitions_unavailable": ["Ranji Trophy"],
        "missing_competitions": ["Ranji Trophy 2023-24"],
        "total_matches_indexed": 85,
        "date_range_start": DEFAULT_WINDOW_START,
        "date_range_end": DEFAULT_WINDOW_END,
    }
    payload.update(overrides)
    return ResearchCoverage(**payload)


# =============================================================================
# Pytest Fixtures
# =============================================================================


@pytest.fixture
def pvre_request_fixture() -> PVRERequestContract:
    """Fixture providing a default valid PVRERequestContract."""
    return build_pvre_request()


@pytest.fixture
def pvre_output_fixture() -> PVREOutputContract:
    """Fixture providing a default valid 26-field PVREOutputContract."""
    return build_pvre_output()


@pytest.fixture
def review_dossier_fixture() -> PVREReviewDossierContract:
    """Fixture providing a default ReviewDossierContract."""
    return build_review_dossier()


@pytest.fixture
def replacement_candidate_evidence_fixture() -> ReplacementCandidateEvidence:
    """Fixture providing a default ReplacementCandidateEvidence."""
    return build_replacement_candidate_evidence()
