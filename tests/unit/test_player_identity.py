"""Unit tests for PIRE player identity resolution and collision handling (Workstream C)."""

from src.pire.player_identity import PlayerIdentityResolver


def test_player_identity_resolution_and_collision_detection():
    """Verify name collisions (same name, distinct IDs) are disambiguated strictly by ID."""
    resolver = PlayerIdentityResolver()

    mappings = [
        {"player_id": "7446", "player_name": "Abdul Samad", "team_name": "SRH", "comp_name": "IPL 2022"},
        {"player_id": "6922", "player_name": "Abdul Samad", "team_name": "JKCA", "comp_name": "SMAT 2022"},
        {"player_id": "813", "player_name": "Jos Buttler", "team_name": "RR", "comp_name": "IPL 2022"},
    ]

    p11 = [
        {"player_id": "7446", "match_id": "M1", "is_played": "true"},
        {"player_id": "7446", "match_id": "M2", "is_played": "true"},
        {"player_id": "813", "match_id": "M1", "is_played": "true"},
    ]

    report = resolver.build_registry(mappings, p11)

    assert report.total_mappings_count == 3
    assert report.total_mapped_player_ids == 3
    assert report.total_unique_names == 2
    assert report.collision_names_count == 1
    assert "Abdul Samad" in report.collision_details
    assert sorted(report.collision_details["Abdul Samad"]) == ["6922", "7446"]

    # Verify canonical name tag for collisions
    p_7446 = resolver.get_player("7446")
    assert p_7446 is not None
    assert p_7446.is_name_collision is True
    assert p_7446.collision_sibling_ids == ["6922"]
    assert p_7446.match_appearances == 2
    assert "SRH" in resolver.get_canonical_name("7446")

    # Non-collision player has normal canonical name
    p_813 = resolver.get_player("813")
    assert p_813 is not None
    assert p_813.is_name_collision is False
    assert resolver.get_canonical_name("813") == "Jos Buttler"


def test_unmapped_player_creates_provisional_identity():
    """Verify unmapped player with match evidence receives PROVISIONAL status."""
    resolver = PlayerIdentityResolver()
    mappings = [{"player_id": "100", "player_name": "Known Player", "team_name": "T1", "comp_name": "C1"}]
    p11 = [{"player_id": "999", "match_id": "M1", "is_played": "true"}]

    report = resolver.build_registry(mappings, p11)
    assert "999" in report.unmapped_player_ids

    p_999 = resolver.get_player("999")
    assert p_999 is not None
    assert p_999.resolution_status == "PROVISIONAL"
