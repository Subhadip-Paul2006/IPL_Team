"""Synthetic test fixtures for TMVE (Team Membership Verification Engine).

Author: Agent E (Tests, Security and Integration Specialist)
Milestone: M5

==============================================================================
CRITICAL DOMAIN GUARDRAIL COMPLIANCE:
- R2: NEVER fabricate or hallucinate statistics, players, or memberships.
- P1: Generating synthetic / mock / hallucinated player or match records is
      STRICTLY PROHIBITED in application data or production stores.
- NOTICE: The synthetic fixtures in this module are EXCLUSIVELY FOR OFFLINE
  UNIT & INTEGRATION TESTS. All synthetic names, entities, and values are
  strictly scoped test fixtures. NO REAL CRICKETER STATS OR IDENTITIES ARE
  FABRICATED OR REPRESENTED IN PRODUCTION DATA.
==============================================================================
"""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID, uuid4

from src.contracts.competition import (
    Competition,
    PlayerTeamHistory,
    Season,
    SquadMembership,
    Team,
    TeamSeasonParticipation,
)
from src.contracts.eligibility import EligibilityPolicy
from src.contracts.player import Player
from src.contracts.provenance import DataSource, VerificationRecord
from src.contracts.tmve import (
    EligibilityStatus,
    RRCurrentState,
    RRRelationshipState,
)

# Canonical UUID constants for deterministic testing
RR_TEAM_ID = UUID("00000000-0000-0000-0000-000000000001")
IPL_COMPETITION_ID = UUID("00000000-0000-0000-0000-000000000002")
TIER1_SOURCE_ID = UUID("00000000-0000-0000-0000-000000000003")
TIER2_SOURCE_ID = UUID("00000000-0000-0000-0000-000000000004")

# RR Season Participation Windows Map (2008 - 2027)
RR_SEASON_PARTICIPATION_MAP: dict[str, dict[str, Any]] = {
    "2008": {"status": "PARTICIPATING", "verified": True, "tier": 1},
    "2009": {"status": "PARTICIPATING", "verified": True, "tier": 1},
    "2010": {"status": "PARTICIPATING", "verified": True, "tier": 1},
    "2011": {"status": "PARTICIPATING", "verified": True, "tier": 1},
    "2012": {"status": "PARTICIPATING", "verified": True, "tier": 1},
    "2013": {"status": "PARTICIPATING", "verified": True, "tier": 1},
    "2014": {"status": "PARTICIPATING", "verified": True, "tier": 1},
    "2015": {"status": "PARTICIPATING", "verified": True, "tier": 1},
    "2016": {"status": "SUSPENDED", "verified": True, "tier": 1},
    "2017": {"status": "SUSPENDED", "verified": True, "tier": 1},
    "2018": {"status": "PARTICIPATING", "verified": True, "tier": 1},
    "2019": {"status": "PARTICIPATING", "verified": True, "tier": 1},
    "2020": {"status": "PARTICIPATING", "verified": True, "tier": 1},
    "2021": {"status": "PARTICIPATING", "verified": True, "tier": 1},
    "2022": {"status": "PARTICIPATING", "verified": True, "tier": 1},
    "2023": {"status": "PARTICIPATING", "verified": True, "tier": 1},
    "2024": {"status": "PARTICIPATING", "verified": True, "tier": 1},
    "2025": {"status": "PARTICIPATING", "verified": True, "tier": 1},
    "2026": {"status": "PARTICIPATING", "verified": True, "tier": 1},
    "2027": {"status": "UNKNOWN", "verified": False, "tier": None},
}


def build_synthetic_rr_team() -> Team:
    """Build Rajasthan Royals Team entity contract."""
    return Team(
        team_id=RR_TEAM_ID,
        team_name="Rajasthan Royals",
        short_code="RR",
        is_active=True,
    )


def build_synthetic_ipl_competition() -> Competition:
    """Build Indian Premier League Competition entity contract."""
    return Competition(
        competition_id=IPL_COMPETITION_ID,
        name="Indian Premier League",
        competition_type="Domestic Franchise T20",
        governing_body="BCCI",
        country="India",
        match_overs=20,
        balls_per_over=6,
    )


def build_synthetic_seasons_and_participation(
    team_id: UUID = RR_TEAM_ID,
    competition_id: UUID = IPL_COMPETITION_ID,
) -> tuple[dict[str, Season], list[TeamSeasonParticipation]]:
    """Generate all IPL seasons (2008-2027) and RR participation records."""
    seasons: dict[str, Season] = {}
    participation_records: list[TeamSeasonParticipation] = []

    for year_str, meta in RR_SEASON_PARTICIPATION_MAP.items():
        year = int(year_str)
        s_id = uuid4()
        season = Season(
            season_id=s_id,
            competition_id=competition_id,
            season_year=year_str,
            start_date=date(year, 3, 20),
            end_date=date(year, 5, 30),
        )
        seasons[year_str] = season

        v_id = uuid4() if meta["verified"] else None
        v_status = "VERIFIED" if meta["verified"] else "UNVERIFIED"

        part = TeamSeasonParticipation(
            participation_id=uuid4(),
            team_id=team_id,
            season_id=s_id,
            participation_status=meta["status"],
            effective_start_date=date(year, 3, 20),
            effective_end_date=date(year, 5, 30),
            verification_id=v_id,
            verification_status=v_status,
            notes=f"Synthetic test participation record for season {year_str}",
        )
        participation_records.append(part)

    return seasons, participation_records


def build_synthetic_tier1_source() -> DataSource:
    """Build Tier-1 BCCI Official Source entity contract."""
    return DataSource(
        source_id=TIER1_SOURCE_ID,
        source_name="BCCI Official IPL Registry",
        source_type="REST API",
        license_type="Official",
        license_status="VERIFIED",
        license_evidence="Official BCCI Accreditation Agreement",
        update_cadence="Real-time",
        data_steward="BCCI Integrity & Operations",
    )


def build_synthetic_verification_record(
    subject_type: str,
    subject_id: UUID,
    evidence_tier: int = 1,
    verification_status: str = "VERIFIED",
    source_provider: str = "BCCI Official Registry",
) -> VerificationRecord:
    """Build a valid VerificationRecord satisfying DDL and contract invariants."""
    return VerificationRecord(
        verification_id=uuid4(),
        subject_type=subject_type,
        subject_id=subject_id,
        data_source_id=TIER1_SOURCE_ID if evidence_tier == 1 else TIER2_SOURCE_ID,
        evidence_tier=evidence_tier,
        source_provider=source_provider,
        verification_status=verification_status,
        confidence=1.0 if verification_status == "VERIFIED" else 0.5,
        notes=f"Tier-{evidence_tier} verification for {subject_type}",
    )


# ==============================================================================
# Domain Player Fixture Builders for Specific Scenarios
# ==============================================================================


def create_verified_rr_match_player(
    canonical_name: str = "Sanju Samson",
    appearances: int = 138,
    seasons: list[str] | None = None,
) -> dict[str, Any]:
    """Scenario 1: Verified Historical RR match player (appearances >= 1)."""
    p_id = uuid4()
    active_seasons = seasons or [
        "2013",
        "2014",
        "2015",
        "2018",
        "2019",
        "2020",
        "2021",
        "2022",
        "2023",
        "2024",
    ]

    player = Player(
        player_id=p_id,
        canonical_name=canonical_name,
        full_name=f"{canonical_name} (Synthetic Test Fixture)",
        date_of_birth=date(1994, 11, 11),
        nationality="India",
        primary_role="Wicketkeeper Batter",
        identity_status="RESOLVED",
    )

    squad_records: list[SquadMembership] = []
    history_records: list[PlayerTeamHistory] = []
    verification_ids: list[UUID] = []

    for s_year in active_seasons:
        s_id = uuid4()
        v_rec = build_synthetic_verification_record(
            subject_type="player_membership",
            subject_id=p_id,
            evidence_tier=1,
            verification_status="VERIFIED",
        )
        verification_ids.append(v_rec.verification_id)

        squad_records.append(
            SquadMembership(
                membership_id=uuid4(),
                player_id=p_id,
                team_id=RR_TEAM_ID,
                season_id=s_id,
                contract_type="Retained" if s_year != "2013" else "Auction Buy",
                is_active_squad=True,
                evidence_source_id=v_rec.verification_id,
            )
        )
        history_records.append(
            PlayerTeamHistory(
                history_id=uuid4(),
                player_id=p_id,
                team_id=RR_TEAM_ID,
                season_year=s_year,
                season_id=s_id,
                association_type="Played",
                appearances=appearances // len(active_seasons),
                provenance_id=v_rec.verification_id,
            )
        )

    return {
        "player": player,
        "player_id": p_id,
        "squad_records": squad_records,
        "history_records": history_records,
        "total_appearances": appearances,
        "active_seasons": active_seasons,
        "verification_ids": verification_ids,
        "expected_relationship_state": RRRelationshipState.HISTORICAL_RR_APPEARANCE,
        "expected_current_state": RRCurrentState.CURRENT,
    }


def create_squad_only_reserve_player(
    canonical_name: str = "Synthetic Reserve Batter",
    squad_seasons: list[str] | None = None,
) -> dict[str, Any]:
    """Scenario 2: Historical Squad-Only reserve player (0 appearances, zero invented stats)."""
    p_id = uuid4()
    seasons = squad_seasons or ["2021", "2022"]

    player = Player(
        player_id=p_id,
        canonical_name=canonical_name,
        full_name=f"{canonical_name} (Synthetic Squad Only)",
        date_of_birth=date(2000, 4, 10),
        nationality="India",
        primary_role="Top-order Batter",
        identity_status="RESOLVED",
    )

    squad_records: list[SquadMembership] = []
    history_records: list[PlayerTeamHistory] = []
    verification_ids: list[UUID] = []

    for s_year in seasons:
        s_id = uuid4()
        v_rec = build_synthetic_verification_record(
            subject_type="player_membership",
            subject_id=p_id,
            evidence_tier=1,
            verification_status="VERIFIED",
        )
        verification_ids.append(v_rec.verification_id)

        squad_records.append(
            SquadMembership(
                membership_id=uuid4(),
                player_id=p_id,
                team_id=RR_TEAM_ID,
                season_id=s_id,
                contract_type="Auction Buy",
                is_active_squad=False,
                evidence_source_id=v_rec.verification_id,
            )
        )
        history_records.append(
            PlayerTeamHistory(
                history_id=uuid4(),
                player_id=p_id,
                team_id=RR_TEAM_ID,
                season_year=s_year,
                season_id=s_id,
                association_type="Squad",
                appearances=0,  # CRITICAL INVARIANT: strictly 0 appearances!
                provenance_id=v_rec.verification_id,
            )
        )

    return {
        "player": player,
        "player_id": p_id,
        "squad_records": squad_records,
        "history_records": history_records,
        "total_appearances": 0,
        "squad_seasons": seasons,
        "verification_ids": verification_ids,
        "expected_relationship_state": RRRelationshipState.HISTORICAL_RR_SQUAD_ONLY,
        "expected_current_state": RRCurrentState.NOT_CURRENT,
    }


def create_incomplete_base_player(
    canonical_name: str = "Synthetic Incomplete Record Prospect",
) -> dict[str, Any]:
    """Scenario 3: Player absent from incomplete record base (yields RR_RELATIONSHIP_UNKNOWN)."""
    p_id = uuid4()
    player = Player(
        player_id=p_id,
        canonical_name=canonical_name,
        nationality="India",
        primary_role="Pace Bowler",
        identity_status="RESOLVED",
    )
    return {
        "player": player,
        "player_id": p_id,
        "squad_records": [],
        "history_records": [],
        "evidence_base_complete": False,
        "missing_evidence": ["Official squad lists for 2018-2020 unavailable in local archive"],
        "expected_relationship_state": RRRelationshipState.RR_RELATIONSHIP_UNKNOWN,
        "expected_current_state": RRCurrentState.UNKNOWN,
    }


def create_verified_non_rr_player(
    canonical_name: str = "Synthetic Non-RR Domestic Star",
    career_years: list[int] | None = None,
) -> dict[str, Any]:
    """Scenario 4: Fully verified non-RR player meeting all 7 TRD §4.5 conditions.

    Conditions:
    1. Historical coverage scope: complete (2008-2015, 2018-2026 verified).
    2. Career window overlap: player active during 2021-2025.
    3. Squad-list coverage: official squad lists consulted for all active seasons.
    4. Scorecard coverage: official scorecards consulted, 0 RR matches.
    5. Source quality: Tier-1 BCCI source cited.
    6. Conflicting evidence: 0 conflicts detected.
    7. Human review: human review completed and approved.
    """
    p_id = uuid4()
    years = career_years or [2021, 2022, 2023, 2024, 2025]
    v_rec = build_synthetic_verification_record(
        subject_type="player_membership",
        subject_id=p_id,
        evidence_tier=1,
        verification_status="VERIFIED",
    )

    player = Player(
        player_id=p_id,
        canonical_name=canonical_name,
        date_of_birth=date(2003, 7, 21),
        nationality="India",
        primary_role="Spin Bowler",
        identity_status="RESOLVED",
    )

    return {
        "player": player,
        "player_id": p_id,
        "career_years": years,
        "historical_coverage_complete": True,
        "career_window_overlap": True,
        "squad_lists_consulted": True,
        "scorecard_coverage_consulted": True,
        "tier_1_or_2_source_cited": True,
        "conflict_free": True,
        "human_review_completed": True,
        "verification_id": v_rec.verification_id,
        "expected_relationship_state": RRRelationshipState.NO_VERIFIED_RR_RELATIONSHIP,
        "expected_negative_verification_met": True,
        "expected_review_status": "CLEAR",
    }


def create_contradictory_evidence_player(
    canonical_name: str = "Synthetic Contradictory Claim Player",
) -> dict[str, Any]:
    """Scenario 5: Ambiguous / conflicting squad claims -> REVIEW_REQUIRED dossier."""
    p_id = uuid4()
    player = Player(
        player_id=p_id,
        canonical_name=canonical_name,
        nationality="India",
        primary_role="Batting All-rounder",
        identity_status="RESOLVED",
    )

    # Claim A: Tier-3 media claim claiming RR squad 2022
    claim_a = {
        "source": "Third-party Cricket Blog",
        "tier": 3,
        "claim": "Included in RR 2022 reserve squad",
        "season": "2022",
    }
    # Claim B: Official BCCI squad release with no listing
    claim_b = {
        "source": "BCCI Official Gazette",
        "tier": 1,
        "claim": "Absent from RR 2022 official registered squad",
        "season": "2022",
    }

    return {
        "player": player,
        "player_id": p_id,
        "conflicting_claims": [claim_a, claim_b],
        "expected_relationship_state": RRRelationshipState.RR_RELATIONSHIP_UNKNOWN,
        "expected_review_status": "REVIEW_REQUIRED",
        "expected_reason_codes": ["CONFLICTING_MEMBERSHIP_CLAIMS"],
    }


def create_unassessed_player_for_2027(
    canonical_name: str = "Synthetic Unassessed Prospect 2027",
) -> dict[str, Any]:
    """Scenario 6: Unassessed player for 2027 season (NOT_ASSESSED, policy bound)."""
    p_id = uuid4()
    season_2027_id = uuid4()
    player = Player(
        player_id=p_id,
        canonical_name=canonical_name,
        nationality="India",
        primary_role="Top-order Batter",
        identity_status="RESOLVED",
    )

    return {
        "player": player,
        "player_id": p_id,
        "target_season_id": season_2027_id,
        "target_season_year": "2027",
        "expected_eligibility_status": EligibilityStatus.NOT_ASSESSED,
        "expected_verified": False,
        "expected_verification_id": None,
    }


def create_synthetic_eligibility_policy(
    season_id: UUID | None = None,
    version: int = 1,
    rule_source: str = "BCCI IPL 2027 Player Regulations §4",
    verified: bool = True,
) -> EligibilityPolicy:
    """Build a versioned EligibilityPolicy satisfying DDL invariants."""
    v_id = uuid4() if verified else None
    return EligibilityPolicy(
        policy_id=uuid4(),
        season_id=season_id or uuid4(),
        policy_version=version,
        effective_date=date(2026, 11, 1),
        expiry_date=date(2027, 6, 30),
        rule_source=rule_source,
        verified=verified,
        verification_id=v_id,
        policy_json={
            "uncapped_definition": "Has not played international cricket or BCCI central contract",
            "cooling_off_period_years": 5,
        },
        notes="Synthetic test eligibility policy",
    )
