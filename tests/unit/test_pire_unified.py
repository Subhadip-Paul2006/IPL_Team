"""Unit tests for the Unified PIRE Player Identity Resolution Engine.

Part of Track B — Phase 2 Unified Database & PIRE.
Tests the 4-tier waterfall, source-scoped identities, collision detection,
anti-merge invariant enforcement, human review queue, all 7 known player collisions,
and adversarial scenarios from TEST_SECURITY_PLAN.md §2.
"""

from __future__ import annotations

import difflib
from typing import Any

import pytest
from src.pire.alias_registry import clean_name
from src.pire.models import IdentityStatus, ResolutionTier
from src.pire.resolver import UnifiedPIRE

# =============================================================================
# The 7 Known Player Collisions from Phase 1B & Organizer Dataset
# =============================================================================

KNOWN_7_COLLISIONS: list[dict[str, Any]] = [
    {
        "name": "Abdul Samad",
        "pid1": "7446",
        "team1": "Sunrisers Hyderabad",
        "comp1": "IPL",
        "pid2": "6922",
        "team2": "Jammu & Kashmir",
        "comp2": "SMAT",
    },
    {
        "name": "Bashir Ahmad",
        "pid1": "39479",
        "team1": "Speen Ghar Tigers",
        "comp1": "Shpageeza Cricket League",
        "pid2": "29833",
        "team2": "Amo Sharks",
        "comp2": "Kabul Premier League",
    },
    {
        "name": "Basil Hameed",
        "pid1": "8638",
        "team1": "United Arab Emirates",
        "comp1": "International T20",
        "pid2": "39444",
        "team2": "Kerala",
        "comp2": "Syed Mushtaq Ali Trophy",
    },
    {
        "name": "Haider Ali",
        "pid1": "7338",
        "team1": "Peshawar Zalmi",
        "comp1": "Pakistan Super League",
        "pid2": "28756",
        "team2": "Northern",
        "comp2": "National T20 Cup",
    },
    {
        "name": "Mohammad Ali",
        "pid1": "3083",
        "team1": "Multan Sultans",
        "comp1": "Pakistan Super League",
        "pid2": "20229",
        "team2": "Zarai Taraqiati Bank Limited",
        "comp2": "Patron's Trophy",
    },
    {
        "name": "Muhammad Farooq",
        "pid1": "27373",
        "team1": "Rawalkot Hawks",
        "comp1": "Kashmir Premier League",
        "pid2": "28978",
        "team2": "Gulf Giants",
        "comp2": "ILT20",
    },
    {
        "name": "Rashid Khan",
        "pid1": "4722",
        "team1": "Gujarat Titans",
        "comp1": "IPL",
        "pid2": "20172",
        "team2": "Abbottabad Falcons",
        "comp2": "Faysal Bank T20",
    },
]


@pytest.fixture
def pire() -> UnifiedPIRE:
    """Fixture initializing UnifiedPIRE with baseline established players."""
    engine = UnifiedPIRE()

    # Register established ground-truth players
    engine.register_player(
        canonical_player_id="P_SAMAD_SRH",
        canonical_name="Abdul Samad",
        source_id="organizer_pack",
        source_player_id="7446",
        teams={"Sunrisers Hyderabad", "SRH"},
        competitions={"IPL"},
    )
    engine.register_player(
        canonical_player_id="P_SAMAD_JKCA",
        canonical_name="Abdul Samad",
        source_id="organizer_pack",
        source_player_id="6922",
        teams={"Jammu & Kashmir", "JKCA"},
        competitions={"SMAT"},
    )
    # Mark the collision
    engine.players["P_SAMAD_SRH"].is_name_collision = True
    engine.players["P_SAMAD_SRH"].collision_sibling_ids = ["P_SAMAD_JKCA"]
    engine.players["P_SAMAD_JKCA"].is_name_collision = True
    engine.players["P_SAMAD_JKCA"].collision_sibling_ids = ["P_SAMAD_SRH"]

    # Non-collision players
    engine.register_player(
        canonical_player_id="P_SAMSON",
        canonical_name="Sanju Samson",
        source_id="organizer_pack",
        source_player_id="5001",
        external_hashes={"cricsheet": "c9d0e1f2"},
        teams={"Rajasthan Royals", "RR"},
        competitions={"IPL"},
    )
    engine.alias_registry.register_alias("P_SAMSON", "SV Samson", source_id="cricsheet")

    engine.register_player(
        canonical_player_id="P_JAISWAL",
        canonical_name="Yashasvi Jaiswal",
        source_id="organizer_pack",
        source_player_id="5002",
        teams={"Rajasthan Royals", "RR"},
        competitions={"IPL"},
    )
    return engine


@pytest.fixture
def collision_engine() -> UnifiedPIRE:
    """Fixture populating UnifiedPIRE with all 7 real collision pairs via ingest_organizer_mappings."""
    engine = UnifiedPIRE()
    mappings: list[dict[str, str]] = []
    for c in KNOWN_7_COLLISIONS:
        mappings.append({
            "player_id": c["pid1"],
            "player_name": c["name"],
            "team_name": c["team1"],
            "comp_name": c["comp1"],
        })
        mappings.append({
            "player_id": c["pid2"],
            "player_name": c["name"],
            "team_name": c["team2"],
            "comp_name": c["comp2"],
        })

    engine.ingest_organizer_mappings(mappings)
    return engine


# =============================================================================
# 1. Baseline 4-Tier Resolution Tests
# =============================================================================


def test_tier_1_external_registry_lookup(pire: UnifiedPIRE) -> None:
    """Tier 1: Resolution using source_id and external_id (Confidence = 1.00)."""
    # Lookup by organizer source ID
    res1 = pire.resolve(
        raw_name="Any Name",
        source_id="organizer_pack",
        external_id="5001",
    )
    assert res1.status == IdentityStatus.RESOLVED
    assert res1.tier == ResolutionTier.TIER_1_CANONICAL_EXTERNAL_KEY
    assert res1.player_id == "P_SAMSON"
    assert res1.confidence == 1.00

    # Lookup by linked CricSheet hex hash
    res2 = pire.resolve(
        raw_name="S Samson",
        source_id="cricsheet",
        external_id="c9d0e1f2",
    )
    assert res2.status == IdentityStatus.RESOLVED
    assert res2.tier == ResolutionTier.TIER_1_CANONICAL_EXTERNAL_KEY
    assert res2.player_id == "P_SAMSON"
    assert res2.confidence == 1.00


def test_tier_2_exact_alias_match(pire: UnifiedPIRE) -> None:
    """Tier 2: Resolution using exact name match on non-collision player (Confidence = 0.95)."""
    res = pire.resolve(raw_name="Sanju Samson")
    assert res.status == IdentityStatus.RESOLVED
    assert res.tier == ResolutionTier.TIER_2_VERIFIED_ALIAS_EXACT
    assert res.player_id == "P_SAMSON"
    assert res.confidence == 0.95

    # Match registered secondary alias
    res_alias = pire.resolve(raw_name="SV Samson")
    assert res_alias.status == IdentityStatus.RESOLVED
    assert res_alias.tier == ResolutionTier.TIER_2_VERIFIED_ALIAS_EXACT
    assert res_alias.player_id == "P_SAMSON"


def test_tier_3_contextual_intersection_collision_disambiguation(pire: UnifiedPIRE) -> None:
    """Tier 3: Contextual intersection resolves name collisions (Confidence = 0.85)."""
    # Name "Abdul Samad" has 2 candidates. Providing context team 'SRH' disambiguates.
    res_srh = pire.resolve(
        raw_name="Abdul Samad",
        context_teams=["SRH"],
    )
    assert res_srh.status == IdentityStatus.RESOLVED
    assert res_srh.tier == ResolutionTier.TIER_3_CONTEXTUAL_INTERSECTION
    assert res_srh.player_id == "P_SAMAD_SRH"
    assert res_srh.confidence == 0.85

    # Context team 'JKCA' resolves to the other sibling
    res_jkca = pire.resolve(
        raw_name="Abdul Samad",
        context_teams=["Jammu & Kashmir"],
    )
    assert res_jkca.status == IdentityStatus.RESOLVED
    assert res_jkca.tier == ResolutionTier.TIER_3_CONTEXTUAL_INTERSECTION
    assert res_jkca.player_id == "P_SAMAD_JKCA"


def test_anti_merge_invariant_on_collision_without_context(pire: UnifiedPIRE) -> None:
    """Anti-Merge: Ambiguous name collision with NO context must NOT merge; must route to review queue."""
    res_ambiguous = pire.resolve(raw_name="Abdul Samad")
    assert res_ambiguous.status == IdentityStatus.UNRESOLVED
    assert res_ambiguous.tier == ResolutionTier.UNRESOLVED_DISPATCH
    assert res_ambiguous.needs_review is True

    # Review queue received the item
    pending = pire.review_queue.get_pending()
    assert len(pending) >= 1
    assert any(item.raw_name == "Abdul Samad" for item in pending)


def test_tier_4_fuzzy_with_corroboration(pire: UnifiedPIRE) -> None:
    """Tier 4: Fuzzy matching succeeds only when corroborated by context team/competition."""
    # Typo: "Yashasvi Jaiswall" with team "RR"
    res = pire.resolve(
        raw_name="Yashasvi Jaiswall",
        context_teams=["Rajasthan Royals"],
    )
    assert res.status == IdentityStatus.RESOLVED
    assert res.tier == ResolutionTier.TIER_4_FUZZY_CORROBORATED
    assert res.player_id == "P_JAISWAL"
    assert res.confidence >= 0.70


def test_anti_merge_invariant_fuzzy_without_corroboration_rejected(pire: UnifiedPIRE) -> None:
    """Anti-Merge: Fuzzy match without corroboration is strictly rejected (no silent merge)."""
    res = pire.resolve(
        raw_name="Yashasvi Jaiswall",
        context_teams=["Unrelated Team"],
    )
    assert res.status == IdentityStatus.UNRESOLVED
    assert res.tier == ResolutionTier.UNRESOLVED_DISPATCH
    assert res.needs_review is True


def test_link_cricsheet_hex_hash_collision_prevention(pire: UnifiedPIRE) -> None:
    """Test linking CricSheet hex hash prevents cross-source key collision."""
    # Link hash to Samson
    ok = pire.link_external_hash("P_SAMSON", "cricsheet", "hex_1234")
    assert ok is True

    # Attempt to link same hash to Jaiswal -> must be rejected and logged as conflict!
    ok_collision = pire.link_external_hash("P_JAISWAL", "cricsheet", "hex_1234")
    assert ok_collision is False
    conflicts = pire.review_queue.get_all_conflicts()
    assert any(c.conflict_type == "CROSS_SOURCE_KEY_COLLISION" for c in conflicts)


def test_human_review_queue_resolution_workflow(pire: UnifiedPIRE) -> None:
    """Test manual human review queue resolution."""
    res = pire.resolve(raw_name="Unknown New Player")
    assert res.needs_review is True

    pending = pire.review_queue.get_pending()
    item = [p for p in pending if p.raw_name == "Unknown New Player"][0]

    resolved_item = pire.review_queue.resolve_item(
        queue_id=item.queue_id,
        target_player_id="P_SAMSON",
        reviewer_id="lead_analyst_01",
        notes="Confirmed alias manually",
    )
    assert resolved_item is not None
    assert resolved_item.status == "RESOLVED"


def test_tier_3_disambiguates_when_both_team_and_comp_provided(pire: UnifiedPIRE) -> None:
    """Verify contextual intersection disambiguates identical names sharing a competition."""
    pire.register_player(
        canonical_player_id="P_HR_DC",
        canonical_name="Harshit Rana",
        teams={"Delhi Capitals", "DC"},
        competitions={"IPL"},
    )
    pire.register_player(
        canonical_player_id="P_HR_SRH",
        canonical_name="Harshit Rana",
        teams={"Sunrisers Hyderabad", "SRH"},
        competitions={"IPL"},
    )
    pire.players["P_HR_DC"].is_name_collision = True
    pire.players["P_HR_SRH"].is_name_collision = True

    # Resolving with DC + IPL must resolve to P_HR_DC, NOT trigger ambiguity!
    res = pire.resolve(
        raw_name="Harshit Rana",
        context_teams=["Delhi Capitals"],
        context_comp="IPL",
    )
    assert res.status == IdentityStatus.RESOLVED
    assert res.tier == ResolutionTier.TIER_3_CONTEXTUAL_INTERSECTION
    assert res.player_id == "P_HR_DC"

    # Resolving with SRH + IPL must resolve to P_HR_SRH
    res_srh = pire.resolve(
        raw_name="Harshit Rana",
        context_teams=["Sunrisers Hyderabad"],
        context_comp="IPL",
    )
    assert res_srh.status == IdentityStatus.RESOLVED
    assert res_srh.tier == ResolutionTier.TIER_3_CONTEXTUAL_INTERSECTION
    assert res_srh.player_id == "P_HR_SRH"


def test_tier_3_ambiguous_collision_never_assigns_concrete_candidate_id(pire: UnifiedPIRE) -> None:
    """Anti-Merge: When multiple candidates match context, player_id must NOT be a real player ID."""
    pire.register_player(
        canonical_player_id="P_CLONE_1",
        canonical_name="Clone Player",
        teams={"Rajasthan Royals"},
        competitions={"IPL"},
    )
    pire.register_player(
        canonical_player_id="P_CLONE_2",
        canonical_name="Clone Player",
        teams={"Rajasthan Royals"},
        competitions={"IPL"},
    )
    pire.players["P_CLONE_1"].is_name_collision = True
    pire.players["P_CLONE_2"].is_name_collision = True

    res = pire.resolve(
        raw_name="Clone Player",
        context_teams=["Rajasthan Royals"],
        context_comp="IPL",
    )
    assert res.status == IdentityStatus.UNRESOLVED
    assert res.tier == ResolutionTier.UNRESOLVED_DISPATCH
    assert res.player_id != "P_CLONE_1"
    assert res.player_id != "P_CLONE_2"
    assert res.player_id.startswith("unresolved_collision_")
    assert len(res.candidate_matches) == 2


def test_clean_name_handles_parentheses() -> None:
    """Verify clean_name removes parentheses and role annotations cleanly."""
    assert clean_name("Mohammad Imran(1)") == "mohammad imran 1"
    assert clean_name("MS Dhoni (c) & (wk)") == "ms dhoni c & wk"
    assert clean_name("James Lillywhite (jnr)") == "james lillywhite jnr"


# =============================================================================
# 2. Comprehensive 7 Known Player Collisions Test Suite
# =============================================================================


def test_ingest_all_7_known_player_collisions_flags_invariants(collision_engine: UnifiedPIRE) -> None:
    """Assert ingestion of all 7 collisions sets collision flags, siblings, and conflict logs."""
    assert len(collision_engine.players) == 14

    conflicts = collision_engine.review_queue.get_all_conflicts()
    conflict_names = {c.subject_name for c in conflicts}

    for col in KNOWN_7_COLLISIONS:
        name = col["name"]
        pid1 = col["pid1"]
        pid2 = col["pid2"]

        p1 = collision_engine.players[pid1]
        p2 = collision_engine.players[pid2]

        # Invariants: flagged as collision with sibling references
        assert p1.is_name_collision is True, f"{pid1} ({name}) not flagged as collision"
        assert p2.is_name_collision is True, f"{pid2} ({name}) not flagged as collision"
        assert pid2 in p1.collision_sibling_ids
        assert pid1 in p2.collision_sibling_ids

        # Alias registry tracks name as collision
        assert collision_engine.alias_registry.is_collision(name) is True

        # Conflict logged in review queue
        assert name in conflict_names


@pytest.mark.parametrize("col", KNOWN_7_COLLISIONS, ids=[c["name"] for c in KNOWN_7_COLLISIONS])
def test_all_7_collisions_anti_merge_without_context_routed_to_review(
    collision_engine: UnifiedPIRE,
    col: dict[str, Any],
) -> None:
    """Anti-Merge: Ambiguous name alone must NEVER auto-merge to either sibling."""
    name = col["name"]
    pid1 = col["pid1"]
    pid2 = col["pid2"]

    res = collision_engine.resolve(raw_name=name)

    assert res.status == IdentityStatus.UNRESOLVED
    assert res.tier == ResolutionTier.UNRESOLVED_DISPATCH
    assert res.confidence == 0.0
    assert res.needs_review is True

    # Critical anti-merge invariant: never bind to either concrete player ID
    assert res.player_id != pid1, f"Illegally auto-merged {name} to {pid1}"
    assert res.player_id != pid2, f"Illegally auto-merged {name} to {pid2}"

    # Staged in review queue
    pending = collision_engine.review_queue.get_pending()
    assert any(item.raw_name == name for item in pending)


@pytest.mark.parametrize("col", KNOWN_7_COLLISIONS, ids=[c["name"] for c in KNOWN_7_COLLISIONS])
def test_all_7_collisions_tier_3_disambiguates_to_sibling_1(
    collision_engine: UnifiedPIRE,
    col: dict[str, Any],
) -> None:
    """Tier 3: Contextual intersection with Team 1 deterministically resolves to Sibling 1."""
    name = col["name"]
    pid1 = col["pid1"]
    team1 = col["team1"]
    comp1 = col["comp1"]

    res = collision_engine.resolve(
        raw_name=name,
        context_teams=[team1],
        context_comp=comp1,
    )

    assert res.status == IdentityStatus.RESOLVED
    assert res.tier == ResolutionTier.TIER_3_CONTEXTUAL_INTERSECTION
    assert res.player_id == pid1
    assert res.confidence == 0.85


@pytest.mark.parametrize("col", KNOWN_7_COLLISIONS, ids=[c["name"] for c in KNOWN_7_COLLISIONS])
def test_all_7_collisions_tier_3_disambiguates_to_sibling_2(
    collision_engine: UnifiedPIRE,
    col: dict[str, Any],
) -> None:
    """Tier 3: Contextual intersection with Team 2 deterministically resolves to Sibling 2."""
    name = col["name"]
    pid2 = col["pid2"]
    team2 = col["team2"]
    comp2 = col["comp2"]

    res = collision_engine.resolve(
        raw_name=name,
        context_teams=[team2],
        context_comp=comp2,
    )

    assert res.status == IdentityStatus.RESOLVED
    assert res.tier == ResolutionTier.TIER_3_CONTEXTUAL_INTERSECTION
    assert res.player_id == pid2
    assert res.confidence == 0.85


@pytest.mark.parametrize("col", KNOWN_7_COLLISIONS, ids=[c["name"] for c in KNOWN_7_COLLISIONS])
def test_all_7_collisions_ambiguous_context_matching_both_triggers_anti_merge(
    collision_engine: UnifiedPIRE,
    col: dict[str, Any],
) -> None:
    """Anti-Merge: When query context matches BOTH candidate siblings, PIRE must halt and generate unresolved ID."""
    name = col["name"]
    pid1 = col["pid1"]
    pid2 = col["pid2"]
    team1 = col["team1"]
    team2 = col["team2"]

    # Provide BOTH teams as context -> ambiguity!
    res = collision_engine.resolve(
        raw_name=name,
        context_teams=[team1, team2],
    )

    assert res.status == IdentityStatus.UNRESOLVED
    assert res.tier == ResolutionTier.UNRESOLVED_DISPATCH
    assert res.confidence == 0.0
    assert res.needs_review is True

    # Must produce unresolved_collision_<uuid>, not either concrete ID
    assert res.player_id.startswith("unresolved_collision_")
    assert res.player_id != pid1
    assert res.player_id != pid2
    assert len(res.candidate_matches) == 2


@pytest.mark.parametrize("col", KNOWN_7_COLLISIONS, ids=[c["name"] for c in KNOWN_7_COLLISIONS])
def test_all_7_collisions_unrelated_context_routes_to_human_review(
    collision_engine: UnifiedPIRE,
    col: dict[str, Any],
) -> None:
    """Anti-Merge: Contradictory / unrelated context must not match either candidate and must quarantine."""
    name = col["name"]
    pid1 = col["pid1"]
    pid2 = col["pid2"]

    res = collision_engine.resolve(
        raw_name=name,
        context_teams=["Antarctica Penguins"],
        context_comp="Global Exhibition Trophy",
    )

    assert res.status == IdentityStatus.UNRESOLVED
    assert res.tier == ResolutionTier.UNRESOLVED_DISPATCH
    assert res.needs_review is True
    assert res.player_id != pid1
    assert res.player_id != pid2


# =============================================================================
# 3. Source-Scoped Identity and Multi-Source Registry Linking Tests
# =============================================================================


def test_source_scoped_external_lookup_distinguishes_providers(pire: UnifiedPIRE) -> None:
    """Verify external_id lookups are strictly scoped by source_id/provider."""
    # Register Player A under provider "bcci" with ID "100"
    pire.register_player(
        canonical_player_id="P_BCCI_100",
        canonical_name="BCCI Player",
        source_id="bcci",
        source_player_id="100",
    )
    # Register Player B under provider "cricsheet" with identical ID "100"
    pire.register_player(
        canonical_player_id="P_CRIC_100",
        canonical_name="CricSheet Player",
        source_id="cricsheet",
        source_player_id="100",
    )

    # Scoped lookups resolve to respective players without cross-provider leakage
    res_bcci = pire.resolve(raw_name="Any", source_id="bcci", external_id="100")
    assert res_bcci.player_id == "P_BCCI_100"

    res_cric = pire.resolve(raw_name="Any", source_id="cricsheet", external_id="100")
    assert res_cric.player_id == "P_CRIC_100"


def test_alias_registry_normalization_and_scoped_lookup(pire: UnifiedPIRE) -> None:
    """Verify alias registry normalizes punctuation, case, whitespace, and respects source."""
    pid = "P_NORMALIZATION_TEST"
    pire.register_player(
        canonical_player_id=pid,
        canonical_name="Ravichandran Ashwin",
        teams={"Rajasthan Royals"},
        competitions={"IPL"},
    )
    pire.alias_registry.register_alias(pid, "R. Ashwin", source_id="bcci")
    pire.alias_registry.register_alias(pid, "R Ashwin", source_id="cricsheet")
    pire.alias_registry.register_alias(pid, "ashwin, r.", source_id="scorecard")

    # Scoped lookups
    assert pire.alias_registry.lookup_exact_scoped("r ashwin", "bcci") == pid
    assert pire.alias_registry.lookup_exact_scoped("R. Ashwin", "cricsheet") == pid

    # Candidates lookup covers all normalized variants
    candidates = pire.alias_registry.lookup_name_candidates("R. Ashwin")
    assert pid in candidates

    # Aliases tracking
    registered_aliases = pire.alias_registry.get_aliases_for_player(pid)
    assert len(registered_aliases) >= 3


# =============================================================================
# 4. Anti-Merge Invariants & Review Queue Exhaustive Tests
# =============================================================================


def test_tier_4_multiple_corroborated_fuzzy_matches_quarantine(pire: UnifiedPIRE) -> None:
    """Anti-Merge: When two distinct players meet Tier 4 fuzzy similarity and both corroborate, do NOT guess."""
    # Two distinct players with near-identical names on same team
    pire.register_player(
        canonical_player_id="P_RAMESH",
        canonical_name="Ramesh Sharma",
        teams={"Delhi Capitals"},
        competitions={"IPL"},
    )
    pire.register_player(
        canonical_player_id="P_RAMISH",
        canonical_name="Ramish Sharma",
        teams={"Delhi Capitals"},
        competitions={"IPL"},
    )

    # Input: "Ramsh Sharma" matches both with similarity >= 0.88 (ratio 0.96) and both on Delhi Capitals
    res = pire.resolve(
        raw_name="Ramsh Sharma",
        context_teams=["Delhi Capitals"],
        context_comp="IPL",
    )

    # Must NOT auto-merge to either player
    assert res.status == IdentityStatus.UNRESOLVED
    assert res.tier == ResolutionTier.UNRESOLVED_DISPATCH
    assert res.needs_review is True
    assert res.player_id.startswith("unresolved_fuzzy_")
    assert res.player_id != "P_RAMESH"
    assert res.player_id != "P_RAMISH"
    assert len(res.candidate_matches) == 2


def test_human_review_queue_full_lifecycle(pire: UnifiedPIRE) -> None:
    """Verify queue enqueue, count, pending retrieval, and resolution workflow."""
    queue = pire.review_queue
    initial_count = queue.pending_count

    item = queue.enqueue(
        raw_name="Mystery Spinner",
        source_id="trials",
        external_id="T_99",
        context_teams=["Rajasthan Royals"],
        candidate_ids=["P_SAMSON", "P_JAISWAL"],
        trigger_reason="Trialist unmapped candidate",
    )
    assert queue.pending_count == initial_count + 1
    assert item.status == "PENDING"

    resolved = queue.resolve_item(
        queue_id=item.queue_id,
        target_player_id="P_SAMSON",
        reviewer_id="head_coach",
        notes="Signed contract",
    )
    assert resolved is not None
    assert resolved.status == "RESOLVED"
    assert queue.pending_count == initial_count


# =============================================================================
# 5. Adversarial Collision Stress Scenarios from TEST_SECURITY_PLAN.md §2
# =============================================================================


def test_adversarial_scenario_1_the_sharma_matrix(pire: UnifiedPIRE) -> None:
    """Scenario 1: Common surname disambiguation across eras and teams (The Sharma Matrix)."""
    # Register the 4 Sharmas
    pire.register_player(
        canonical_player_id="P_MOHIT_SHARMA",
        canonical_name="Mohit Sharma",
        teams={"CSK", "Chennai Super Kings", "GT", "Gujarat Titans"},
        competitions={"IPL"},
    )
    pire.alias_registry.register_alias("P_MOHIT_SHARMA", "M Sharma", source_id="ipl")

    pire.register_player(
        canonical_player_id="P_SANDEEP_SHARMA",
        canonical_name="Sandeep Sharma",
        teams={"RR", "Rajasthan Royals", "PBKS"},
        competitions={"IPL"},
    )

    pire.register_player(
        canonical_player_id="P_MUKESH_SHARMA",
        canonical_name="Mukesh Sharma",
        teams={"Ranji Trophy", "Domestic XI"},
        competitions={"Ranji"},
    )
    pire.alias_registry.register_alias("P_MUKESH_SHARMA", "M Sharma", source_id="domestic")

    pire.register_player(
        canonical_player_id="P_ROHIT_SHARMA",
        canonical_name="Rohit Sharma",
        teams={"MI", "Mumbai Indians"},
        competitions={"IPL"},
    )

    # Mark M Sharma collision
    pire.players["P_MOHIT_SHARMA"].is_name_collision = True
    pire.players["P_MUKESH_SHARMA"].is_name_collision = True

    # Test 1.1: "M Sharma" in 2014 CSK context resolves to Mohit Sharma via Tier 3
    res_csk = pire.resolve(
        raw_name="M Sharma",
        context_teams=["Chennai Super Kings"],
        context_comp="IPL",
    )
    assert res_csk.status == IdentityStatus.RESOLVED
    assert res_csk.tier == ResolutionTier.TIER_3_CONTEXTUAL_INTERSECTION
    assert res_csk.player_id == "P_MOHIT_SHARMA"

    # Test 1.2: "Sharma" alone with no context must quarantine, NEVER auto-merge
    res_generic = pire.resolve(raw_name="Sharma")
    assert res_generic.status == IdentityStatus.UNRESOLVED
    assert res_generic.needs_review is True

    # Test 1.3: "Mukesh Sharma" in IPL context fails contextual match
    res_mukesh_ipl = pire.resolve(
        raw_name="Mukesh Sharma",
        context_teams=["Rajasthan Royals"],
        context_comp="IPL",
    )
    assert res_mukesh_ipl.status == IdentityStatus.UNRESOLVED
    assert res_mukesh_ipl.needs_review is True


def test_adversarial_scenario_2_phonetic_transliteration_variants(pire: UnifiedPIRE) -> None:
    """Scenario 2: Phonetic & Transliteration Variants (Mohammad Shami Matrix)."""
    pid_shami = "P_SHAMI"
    pire.register_player(
        canonical_player_id=pid_shami,
        canonical_name="Mohammad Shami",
        source_id="organizer",
        source_player_id="94",
        external_hashes={"cricsheet": "5e9df532"},
        teams={"Gujarat Titans", "GT"},
        competitions={"IPL"},
        playing_role="Bowler",
        bowling_style="Right-arm fast",
        birth_year=1990,
    )
    pire.alias_registry.register_alias(pid_shami, "Shami Ahmed", source_id="cricinfo_historical")
    pire.alias_registry.register_alias(pid_shami, "Mohammed Shami", source_id="bcci")

    # Test 2.1: Tier 1 match using CricSheet hash 5e9df532
    res_t1 = pire.resolve(raw_name="Any", source_id="cricsheet", external_id="5e9df532")
    assert res_t1.status == IdentityStatus.RESOLVED
    assert res_t1.tier == ResolutionTier.TIER_1_CANONICAL_EXTERNAL_KEY
    assert res_t1.player_id == pid_shami
    assert res_t1.confidence == 1.00

    # Test 2.2: Tier 2 match using early career alias "Shami Ahmed"
    res_t2 = pire.resolve(raw_name="Shami Ahmed")
    assert res_t2.status == IdentityStatus.RESOLVED
    assert res_t2.tier == ResolutionTier.TIER_2_VERIFIED_ALIAS_EXACT
    assert res_t2.player_id == pid_shami
    assert res_t2.confidence == 0.95

    # Test 2.3: Tier 4 corroborated fuzzy match on "Muhammed Shamee"
    # difflib ratio for clean strings "muhammed shamee" vs "mohammad shami" is ~0.86
    # Let's test a transliteration with ratio >= 0.88: "Mohamad Shami"
    res_t4 = pire.resolve(
        raw_name="Mohamad Shami",
        context_teams=["Gujarat Titans"],
    )
    assert res_t4.status == IdentityStatus.RESOLVED
    assert res_t4.tier == ResolutionTier.TIER_4_FUZZY_CORROBORATED
    assert res_t4.player_id == pid_shami

    # Test 2.4: "Mohamad Shami" with uncorroborated context strictly rejected
    res_rejected = pire.resolve(
        raw_name="Mohamad Shami",
        context_teams=["Under-19 State Academy"],
    )
    assert res_rejected.status == IdentityStatus.UNRESOLVED
    assert res_rejected.needs_review is True


def test_adversarial_scenario_3_complex_abbreviations_and_particles(pire: UnifiedPIRE) -> None:
    """Scenario 3: Particle and punctuation normalization (AB de Villiers Matrix)."""
    pid_abd = "P_AB_DE_VILLIERS"
    pire.register_player(
        canonical_player_id=pid_abd,
        canonical_name="Abraham Benjamin de Villiers",
        teams={"Royal Challengers Bangalore", "RCB"},
        competitions={"IPL"},
    )
    pire.alias_registry.register_alias(pid_abd, "AB de Villiers", source_id="cricsheet")

    # Test 3.1: Normalization strips punctuation and spaces
    assert clean_name("de villiers,   a.b.") == "de villiers a b"
    assert clean_name("A.B. de Villiers") == "a b de villiers"

    # Match verified alias "AB de Villiers"
    res_alias = pire.resolve(raw_name="AB de Villiers")
    assert res_alias.status == IdentityStatus.RESOLVED
    assert res_alias.tier == ResolutionTier.TIER_2_VERIFIED_ALIAS_EXACT
    assert res_alias.player_id == pid_abd

    # Test 3.2: F de Villiers (Fanie de Villiers, 1990s) in IPL context must NOT merge
    pire.register_player(
        canonical_player_id="P_FANIE_DE_VILLIERS",
        canonical_name="Fanie de Villiers",
        teams={"South Africa"},
        competitions={"ODI"},
    )
    res_fanie = pire.resolve(
        raw_name="F de Villiers",
        context_teams=["Royal Challengers Bangalore"],
        context_comp="IPL",
    )
    assert res_fanie.status == IdentityStatus.UNRESOLVED
    assert res_fanie.player_id != pid_abd


def test_adversarial_scenario_4_sibling_pairs_pathan_and_pandya(pire: UnifiedPIRE) -> None:
    """Scenario 4: Brother pairs sharing initials, teams, or competitions (Pathan & Pandya)."""
    # 1. The Pathan Brothers (Different Teams in 2008 IPL)
    pid_yusuf = "P_YUSUF_PATHAN"
    pid_irfan = "P_IRFAN_PATHAN"

    pire.register_player(
        canonical_player_id=pid_yusuf,
        canonical_name="Yusuf Pathan",
        teams={"Rajasthan Royals", "RR"},
        competitions={"IPL"},
    )
    pire.register_player(
        canonical_player_id=pid_irfan,
        canonical_name="Irfan Pathan",
        teams={"Kings XI Punjab", "KXIP"},
        competitions={"IPL"},
    )
    pire.alias_registry.register_alias(pid_yusuf, "Pathan", source_id="ipl")
    pire.alias_registry.register_alias(pid_irfan, "Pathan", source_id="ipl")
    pire.players[pid_yusuf].is_name_collision = True
    pire.players[pid_irfan].is_name_collision = True

    # Yusuf in RR batting context
    res_yusuf = pire.resolve(raw_name="Pathan", context_teams=["Rajasthan Royals"])
    assert res_yusuf.status == IdentityStatus.RESOLVED
    assert res_yusuf.player_id == pid_yusuf

    # Irfan in KXIP bowling context
    res_irfan = pire.resolve(raw_name="Pathan", context_teams=["Kings XI Punjab"])
    assert res_irfan.status == IdentityStatus.RESOLVED
    assert res_irfan.player_id == pid_irfan

    # 2. The Pandya Brothers (SAME team: Mumbai Indians in 2019!)
    pid_hardik = "P_HARDIK_PANDYA"
    pid_krunal = "P_KRUNAL_PANDYA"

    pire.register_player(
        canonical_player_id=pid_hardik,
        canonical_name="Hardik Pandya",
        teams={"Mumbai Indians", "MI"},
        competitions={"IPL"},
    )
    pire.register_player(
        canonical_player_id=pid_krunal,
        canonical_name="Krunal Pandya",
        teams={"Mumbai Indians", "MI"},
        competitions={"IPL"},
    )
    pire.alias_registry.register_alias(pid_hardik, "Pandya", source_id="ipl")
    pire.alias_registry.register_alias(pid_krunal, "Pandya", source_id="ipl")
    pire.players[pid_hardik].is_name_collision = True
    pire.players[pid_krunal].is_name_collision = True

    # When query gives "Pandya" + "Mumbai Indians", BOTH match!
    # Anti-merge rule: PIRE MUST NOT GUESS! Must halt and return unresolved collision!
    res_pandya = pire.resolve(raw_name="Pandya", context_teams=["Mumbai Indians"])
    assert res_pandya.status == IdentityStatus.UNRESOLVED
    assert res_pandya.tier == ResolutionTier.UNRESOLVED_DISPATCH
    assert res_pandya.needs_review is True
    assert res_pandya.player_id != pid_hardik
    assert res_pandya.player_id != pid_krunal
    assert res_pandya.player_id.startswith("unresolved_collision_")
    assert len(res_pandya.candidate_matches) == 2


def test_adversarial_scenario_5_external_hash_hijacking(pire: UnifiedPIRE) -> None:
    """Scenario 5: Attempting to bind an existing external hash to a second player is blocked."""
    pid_legit = "P_LEGIT_ROHIT"
    pid_imposter = "P_IMPOSTER_ROHIT"

    pire.register_player(
        canonical_player_id=pid_legit,
        canonical_name="Rohit Sharma",
        source_id="organizer",
        source_player_id="126",
    )
    pire.register_player(
        canonical_player_id=pid_imposter,
        canonical_name="Rohit Sharma Imposter",
        source_id="unverified",
        source_player_id="9999",
    )

    # 1. Bind legitimate CricSheet hash
    ok_first = pire.link_external_hash(pid_legit, "cricsheet", "hash_rohit_313e6178")
    assert ok_first is True

    # 2. Imposter attempts to link same hash -> Rejected!
    ok_hijack = pire.link_external_hash(pid_imposter, "cricsheet", "hash_rohit_313e6178")
    assert ok_hijack is False

    # 3. Assert conflict recorded with audit evidence
    conflicts = pire.review_queue.get_all_conflicts()
    collision_conflicts = [c for c in conflicts if c.conflict_type == "CROSS_SOURCE_KEY_COLLISION"]
    assert len(collision_conflicts) >= 1
    assert collision_conflicts[0].evidence["hash"] == "hash_rohit_313e6178"

    # 4. Lookup for hash still resolves to original legitimate player
    res = pire.resolve(raw_name="Any", source_id="cricsheet", external_id="hash_rohit_313e6178")
    assert res.player_id == pid_legit


def test_adversarial_scenario_6_borderline_similarity_quarantine(pire: UnifiedPIRE) -> None:
    """Scenario 6: Low-confidence fuzzy match (< 0.88) must quarantine without false merge."""
    # "Sanju Sam" vs "Sanju Samson":
    # SequenceMatcher ratio is ~0.77 (< 0.88 threshold)
    sim = difflib.SequenceMatcher(None, clean_name("Sanju Sam"), clean_name("Sanju Samson")).ratio()
    assert sim < 0.88, f"Unexpected high similarity {sim}"

    res = pire.resolve(
        raw_name="Sanju Sam",
        context_teams=["Rajasthan Royals"],
    )

    # Must NOT auto-resolve to Samson
    assert res.status == IdentityStatus.UNRESOLVED
    assert res.tier == ResolutionTier.UNRESOLVED_DISPATCH
    assert res.needs_review is True
    assert res.player_id != "P_SAMSON"
