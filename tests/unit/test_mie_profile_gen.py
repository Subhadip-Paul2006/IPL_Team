"""Unit tests for Support Service B: Profile Generator (JSON & CSV Export).

Verifies AC-20 compliance:
1. Standardized JSON and CSV format generation.
2. Embedded mandatory legal attribution (ODC-By v1.0 and CC BY 4.0).
3. Confidentiality guard scrubbing proprietary tokens and secrets.
"""

from __future__ import annotations

import json

from src.mie.orchestrator import MotherIntelligenceEngine
from src.mie.profile_gen import ProfileGeneratorService


def test_export_to_json_structure_and_attribution() -> None:
    """Verify JSON export contains valid envelopes, metadata, and legal attribution."""
    mie = MotherIntelligenceEngine()
    report = mie.request_player_intelligence("Sanju Samson")

    json_str = mie.export_profile(report, format="json")
    parsed = json.loads(json_str)

    # 1. Structure
    assert "metadata" in parsed
    assert "legal_and_licensing" in parsed
    assert "player_intelligence" in parsed

    # 2. Metadata
    meta = parsed["metadata"]
    assert meta["system"] == "Rajasthan Royals Squad Intelligence Platform"
    assert meta["canonical_name"] == "Sanju Samson"

    # 3. Attribution (AC-20)
    legal = parsed["legal_and_licensing"]
    assert legal["attribution_notices"] == report.provenance.attribution_notices
    assert legal["licenses"] == report.provenance.licenses_observed


def test_export_to_csv_headers_and_content() -> None:
    """Verify CSV export contains header comments, legal notices, and structured rows."""
    mie = MotherIntelligenceEngine()
    report = mie.request_player_intelligence("Sanju Samson")

    csv_str = mie.export_profile(report, format="csv")

    assert "# RAJASTHAN ROYALS SQUAD INTELLIGENCE PLATFORM" in csv_str
    for notice in report.provenance.attribution_notices:
        assert notice in csv_str
    assert "IDENTIFICATION,Canonical Name,Sanju Samson" in csv_str
    assert "MEMBERSHIP,RR Relationship State," in csv_str
    assert "PERFORMANCE,Format,T20" in csv_str


def test_export_confidentiality_guard_scrubs_secrets() -> None:
    """Rule AC-20: Public exports must never leak proprietary hackathon secrets or keys."""
    mie = MotherIntelligenceEngine()
    report = mie.request_player_intelligence("Sanju Samson")

    # Inject mock internal secrets into raw dictionary to test sanitizer
    report_dict = report.model_dump(mode="json")
    report_dict["internal_api_key"] = "PRIVATE_RR_SECRET_TOKEN_999"
    report_dict["nested"] = {"user_password": "supersecretpassword"}

    ProfileGeneratorService._sanitize_payload(report_dict)

    assert "internal_api_key" not in report_dict
    assert "user_password" not in report_dict["nested"]
