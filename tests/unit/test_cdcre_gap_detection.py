"""Unit tests for CDCRE Career Gap Detector and Classifier (Requirement R4).

Validates:
1. Chronological gap detection across tournament history (e.g., active 2015, next 2018 -> ['2016', '2017']).
2. Specific classification of Rajasthan Royals (RR) 2016-2017 absence as FRANCHISE_SUSPENSION
   (Supreme Court Order / Justice Lodha Committee).
3. FRANCHISE_SUSPENSION precedence over individual injury or NOC denial for RR IPL absence.
4. Non-RR player IPL absence is NOT classified as FRANCHISE_SUSPENSION.
5. RR player absence in non-IPL tournaments (e.g. BBL) is NOT classified as FRANCHISE_SUSPENSION.
6. Injury corroboration classified as INJURY.
7. NOC denial corroboration classified as NOC_DENIED.
8. Personal absence / unavailability classified as UNAVAILABLE.
9. Uncorroborated gaps default to UNEXPLAINED_GAP.
10. Multi-season consecutive and non-consecutive gap spans.
11. Standardized season year parsing (e.g. '2015', '2015/16', '2017/18').
12. Strict Pydantic v2 BaseContract invariants (extra='forbid', validate_assignment=True).
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.cdcre.gap_detector import (
    CareerGapDetector,
    detect_career_gaps,
    format_gap_season,
    parse_season_start_year,
)
from src.contracts.career import PlayerAvailability, PlayerInjury
from src.contracts.cdcre import (
    CareerGapRecord,
    CompetitionHistoryRecord,
    CoverageStatus,
    GapType,
)

from tests.fixtures.cdcre_contract_fixtures import (
    BBL_COMPETITION_UUID,
    SMAT_COMPETITION_UUID,
    SYNTHETIC_PLAYER_UUID_PRIMARY,
    build_synthetic_competition_history,
)


class TestSeasonYearParsingAndFormatting:
    """Test season string normalization and parsing."""

    def test_parse_single_year(self) -> None:
        """Parse standard 4-digit years."""
        assert parse_season_start_year("2015") == 2015
        assert parse_season_start_year(" 2024 ") == 2024

    def test_parse_slash_seasons(self) -> None:
        """Parse split season years with slashes."""
        assert parse_season_start_year("2015/16") == 2015
        assert parse_season_start_year("2023/2024") == 2023

    def test_parse_hyphen_seasons(self) -> None:
        """Parse season years with hyphens."""
        assert parse_season_start_year("2017-18") == 2017
        assert parse_season_start_year("2020-2021") == 2020

    def test_parse_invalid_or_empty(self) -> None:
        """Invalid strings return None without crashing."""
        assert parse_season_start_year("") is None
        assert parse_season_start_year("Unknown") is None
        assert parse_season_start_year(None) is None  # type: ignore[arg-type]

    def test_format_gap_season_matching_style(self) -> None:
        """format_gap_season preserves the format style of the template season."""
        assert format_gap_season(2016, "2015") == "2016"
        assert format_gap_season(2016, "2015/16") == "2016/17"
        assert format_gap_season(2016, "2015/2016") == "2016/2017"
        assert format_gap_season(2016, "2015-16") == "2016-17"


class TestChronologicalGapDetection:
    """Test detection of gaps between active tournament participation seasons."""

    def test_two_year_gap_detected(self) -> None:
        """Player active in 2015 and next in 2018 has a gap in ['2016', '2017']."""
        rec_2015 = build_synthetic_competition_history(
            season_year="2015",
            appearances=14,
            coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
        )
        rec_2018 = build_synthetic_competition_history(
            season_year="2018",
            appearances=12,
            coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
        )

        gaps = detect_career_gaps(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            history=[rec_2015, rec_2018],
        )

        assert len(gaps) == 1
        gap = gaps[0]
        assert gap.start_season == "2016"
        assert gap.end_season == "2017"
        assert gap.gap_seasons == ["2016", "2017"]
        assert gap.competition_name == "Indian Premier League"

    def test_single_year_gap_detected(self) -> None:
        """Player active in 2020 and next in 2022 has a single-year gap in ['2021']."""
        rec_2020 = build_synthetic_competition_history(
            season_year="2020",
            appearances=14,
            coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
        )
        rec_2022 = build_synthetic_competition_history(
            season_year="2022",
            appearances=14,
            coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
        )

        gaps = detect_career_gaps(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            history=[rec_2020, rec_2022],
        )

        assert len(gaps) == 1
        gap = gaps[0]
        assert gap.start_season == "2021"
        assert gap.end_season == "2021"
        assert gap.gap_seasons == ["2021"]

    def test_consecutive_years_no_gap(self) -> None:
        """Active participation in consecutive seasons produces zero gaps."""
        rec_2021 = build_synthetic_competition_history(season_year="2021", appearances=14)
        rec_2022 = build_synthetic_competition_history(season_year="2022", appearances=15)
        rec_2023 = build_synthetic_competition_history(season_year="2023", appearances=16)

        gaps = detect_career_gaps(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            history=[rec_2021, rec_2022, rec_2023],
        )
        assert len(gaps) == 0

    def test_single_season_no_gap(self) -> None:
        """A player with only one active season cannot have a career break."""
        rec_2021 = build_synthetic_competition_history(season_year="2021", appearances=14)
        gaps = detect_career_gaps(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            history=[rec_2021],
        )
        assert len(gaps) == 0

    def test_empty_history_returns_empty(self) -> None:
        """Empty history returns empty list."""
        gaps = detect_career_gaps(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            history=[],
        )
        assert gaps == []

    def test_multiple_non_consecutive_gaps(self) -> None:
        """Player with multiple distinct career gaps across career history."""
        rec_2013 = build_synthetic_competition_history(season_year="2013", appearances=10)
        rec_2015 = build_synthetic_competition_history(season_year="2015", appearances=12)
        rec_2018 = build_synthetic_competition_history(season_year="2018", appearances=14)
        rec_2021 = build_synthetic_competition_history(season_year="2021", appearances=14)

        gaps = detect_career_gaps(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            history=[rec_2013, rec_2015, rec_2018, rec_2021],
            team_affiliations=["Rajasthan Royals"],
        )

        assert len(gaps) == 3
        # Gap 1: 2014
        assert gaps[0].start_season == "2014"
        assert gaps[0].end_season == "2014"
        assert gaps[0].gap_seasons == ["2014"]

        # Gap 2: 2016-2017 (RR franchise suspension)
        assert gaps[1].start_season == "2016"
        assert gaps[1].end_season == "2017"
        assert gaps[1].gap_seasons == ["2016", "2017"]
        assert gaps[1].gap_type == GapType.FRANCHISE_SUSPENSION

        # Gap 3: 2019-2020
        assert gaps[2].start_season == "2019"
        assert gaps[2].end_season == "2020"
        assert gaps[2].gap_seasons == ["2019", "2020"]

    def test_split_season_year_format(self) -> None:
        """Detect gaps for tournaments with split season years like SMAT (2014/15 -> 2017/18)."""
        smat_id = SMAT_COMPETITION_UUID
        rec_1 = CompetitionHistoryRecord(
            competition_id=smat_id,
            competition_name="Syed Mushtaq Ali Trophy",
            season_year="2014/15",
            format_tag="T20",
            appearances=6,
            coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
            balls_per_over=6,
        )
        rec_2 = CompetitionHistoryRecord(
            competition_id=smat_id,
            competition_name="Syed Mushtaq Ali Trophy",
            season_year="2017/18",
            format_tag="T20",
            appearances=7,
            coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
            balls_per_over=6,
        )

        gaps = detect_career_gaps(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            history=[rec_1, rec_2],
        )

        assert len(gaps) == 1
        gap = gaps[0]
        assert gap.start_season == "2015/16"
        assert gap.end_season == "2016/17"
        assert gap.gap_seasons == ["2015/16", "2016/17"]
        assert gap.competition_name == "Syed Mushtaq Ali Trophy"


class TestFranchiseSuspensionClassification:
    """Rigorous tests for Rajasthan Royals 2016-2017 franchise suspension classification."""

    def test_rr_player_ipl_2016_2017_classified_as_franchise_suspension(self) -> None:
        """RR player absent from IPL in 2016-2017 is classified as FRANCHISE_SUSPENSION."""
        rec_2015 = build_synthetic_competition_history(season_year="2015", appearances=14)
        rec_2018 = build_synthetic_competition_history(season_year="2018", appearances=12)

        gaps = detect_career_gaps(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            history=[rec_2015, rec_2018],
            team_affiliations=["Rajasthan Royals"],
        )

        assert len(gaps) == 1
        gap = gaps[0]
        assert gap.gap_type == GapType.FRANCHISE_SUSPENSION
        assert gap.start_season == "2016"
        assert gap.end_season == "2017"
        assert gap.gap_seasons == ["2016", "2017"]
        assert "Rajasthan Royals franchise suspension" in (gap.evidence_notes or "")

    def test_rr_suspension_precedence_over_injury(self) -> None:
        """RR 2016-2017 absence takes precedence over injury evidence per requirement."""
        rec_2015 = build_synthetic_competition_history(season_year="2015", appearances=14)
        rec_2018 = build_synthetic_competition_history(season_year="2018", appearances=12)

        # Severe injury overlapping 2016
        injury = PlayerInjury(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            injury_date=date(2016, 3, 1),
            injury_type="Shoulder dislocation",
            severity="Severe",
            surgery_required=True,
            return_to_play_date=date(2016, 11, 1),
            medical_notes="Ruled out for season 2016",
        )

        gaps = detect_career_gaps(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            history=[rec_2015, rec_2018],
            injuries=[injury],
            team_affiliations=["Rajasthan Royals"],
        )

        assert len(gaps) == 1
        # Precedence: FRANCHISE_SUSPENSION, NOT INJURY!
        assert gaps[0].gap_type == GapType.FRANCHISE_SUSPENSION

    def test_rr_suspension_precedence_over_noc_denial(self) -> None:
        """RR 2016-2017 absence takes precedence over national board NOC denial."""
        rec_2015 = build_synthetic_competition_history(season_year="2015", appearances=14)
        rec_2018 = build_synthetic_competition_history(season_year="2018", appearances=12)

        noc_denied = PlayerAvailability(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            season_id=uuid4(),
            start_date=date(2016, 4, 1),
            end_date=date(2016, 5, 30),
            national_board_noc_status="DENIED",
            reason_for_unavailability="NOC denied by Cricket Australia",
        )

        gaps = detect_career_gaps(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            history=[rec_2015, rec_2018],
            availability=[noc_denied],
            team_affiliations=["Rajasthan Royals"],
        )

        assert len(gaps) == 1
        # Precedence: FRANCHISE_SUSPENSION, NOT NOC_DENIED!
        assert gaps[0].gap_type == GapType.FRANCHISE_SUSPENSION

    def test_non_rr_player_ipl_absence_not_classified_as_franchise_suspension(self) -> None:
        """Player affiliated strictly with Mumbai Indians is NOT classified as FRANCHISE_SUSPENSION."""
        rec_2015 = build_synthetic_competition_history(season_year="2015", appearances=14)
        rec_2018 = build_synthetic_competition_history(season_year="2018", appearances=12)

        gaps = detect_career_gaps(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            history=[rec_2015, rec_2018],
            team_affiliations=["Mumbai Indians"],  # Explicit non-RR affiliation
        )

        assert len(gaps) == 1
        # MI was not suspended! Must be UNEXPLAINED_GAP
        assert gaps[0].gap_type == GapType.UNEXPLAINED_GAP
        assert gaps[0].gap_type != GapType.FRANCHISE_SUSPENSION

    def test_rr_player_non_ipl_tournament_not_franchise_suspension(self) -> None:
        """Absence from Big Bash League during 2016-2017 is NOT FRANCHISE_SUSPENSION."""
        bbl_id = BBL_COMPETITION_UUID
        rec_2015 = CompetitionHistoryRecord(
            competition_id=bbl_id,
            competition_name="Big Bash League",
            season_year="2015",
            format_tag="T20",
            appearances=8,
            coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
            balls_per_over=6,
        )
        rec_2018 = CompetitionHistoryRecord(
            competition_id=bbl_id,
            competition_name="Big Bash League",
            season_year="2018",
            format_tag="T20",
            appearances=9,
            coverage_status=CoverageStatus.VERIFIED_PARTICIPATION,
            balls_per_over=6,
        )

        gaps = detect_career_gaps(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            history=[rec_2015, rec_2018],
            team_affiliations=["Rajasthan Royals"],
        )

        assert len(gaps) == 1
        # BBL was not suspended, only IPL RR
        assert gaps[0].gap_type == GapType.UNEXPLAINED_GAP


class TestEvidenceCorroboration:
    """Test injury, NOC denial, and personal availability corroboration."""

    def test_injury_corroboration(self) -> None:
        """Gap overlapping player injury is classified as INJURY."""
        rec_2019 = build_synthetic_competition_history(season_year="2019", appearances=14)
        rec_2022 = build_synthetic_competition_history(season_year="2022", appearances=14)

        injury = PlayerInjury(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            injury_date=date(2020, 2, 15),
            injury_type="ACL rupture",
            severity="Severe",
            surgery_required=True,
            recovery_time_days=270,
            return_to_play_date=date(2021, 10, 1),
            medical_notes="Ruled out for IPL 2020 and 2021",
        )

        gaps = detect_career_gaps(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            history=[rec_2019, rec_2022],
            injuries=[injury],
        )

        assert len(gaps) == 1
        gap = gaps[0]
        assert gap.gap_type == GapType.INJURY
        assert gap.start_season == "2020"
        assert gap.end_season == "2021"
        assert gap.gap_seasons == ["2020", "2021"]
        assert "Ruled out for IPL 2020" in (gap.evidence_notes or "")

    def test_noc_denied_corroboration(self) -> None:
        """Gap overlapping NOC denial is classified as NOC_DENIED."""
        rec_2018 = build_synthetic_competition_history(season_year="2018", appearances=14)
        rec_2020 = build_synthetic_competition_history(season_year="2020", appearances=14)

        noc_denied = PlayerAvailability(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            season_id=uuid4(),
            start_date=date(2019, 3, 1),
            end_date=date(2019, 6, 1),
            national_board_noc_status="DENIED",
            reason_for_unavailability="No NOC granted by ECB due to World Cup preparations",
        )

        gaps = detect_career_gaps(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            history=[rec_2018, rec_2020],
            availability=[noc_denied],
        )

        assert len(gaps) == 1
        gap = gaps[0]
        assert gap.gap_type == GapType.NOC_DENIED
        assert gap.start_season == "2019"
        assert gap.end_season == "2019"
        assert gap.gap_seasons == ["2019"]
        assert "World Cup preparations" in (gap.evidence_notes or "")

    def test_personal_unavailability_corroboration(self) -> None:
        """Gap overlapping personal reasons / unavailability is classified as UNAVAILABLE."""
        rec_2019 = build_synthetic_competition_history(season_year="2019", appearances=14)
        rec_2021 = build_synthetic_competition_history(season_year="2021", appearances=14)

        personal_unavail = PlayerAvailability(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            season_id=uuid4(),
            start_date=date(2020, 3, 1),
            end_date=date(2020, 11, 30),
            availability_status="PERSONAL_REASONS",
            reason_for_unavailability="Paternity leave and family commitments",
        )

        gaps = detect_career_gaps(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            history=[rec_2019, rec_2021],
            availability=[personal_unavail],
        )

        assert len(gaps) == 1
        gap = gaps[0]
        assert gap.gap_type == GapType.UNAVAILABLE
        assert gap.start_season == "2020"
        assert gap.end_season == "2020"
        assert "Paternity leave" in (gap.evidence_notes or "")

    def test_unexplained_gap_default(self) -> None:
        """Gap with no matching injury or availability records defaults to UNEXPLAINED_GAP."""
        rec_2018 = build_synthetic_competition_history(season_year="2018", appearances=14)
        rec_2020 = build_synthetic_competition_history(season_year="2020", appearances=14)

        gaps = detect_career_gaps(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            history=[rec_2018, rec_2020],
            injuries=[],
            availability=[],
        )

        assert len(gaps) == 1
        gap = gaps[0]
        assert gap.gap_type == GapType.UNEXPLAINED_GAP
        assert "Unexplained career gap" in (gap.evidence_notes or "")


class TestCareerGapDetectorClass:
    """Test CareerGapDetector OOP class wrapper methods."""

    def test_detector_class_usage(self) -> None:
        """CareerGapDetector instance operates with configured and override evidence."""
        rec_2015 = build_synthetic_competition_history(season_year="2015", appearances=14)
        rec_2018 = build_synthetic_competition_history(season_year="2018", appearances=14)

        detector = CareerGapDetector(team_affiliations=["Rajasthan Royals"])
        gaps = detector.detect_career_gaps(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            history=[rec_2015, rec_2018],
        )

        assert len(gaps) == 1
        assert gaps[0].gap_type == GapType.FRANCHISE_SUSPENSION


class TestCareerGapRecordContractInvariants:
    """Test Pydantic v2 BaseContract compliance on CareerGapRecord."""

    def test_forbids_extra_fields(self) -> None:
        """CareerGapRecord strictly forbids unauthorized extra fields."""
        with pytest.raises(ValidationError):
            CareerGapRecord(  # type: ignore[call-arg]
                player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
                start_season="2016",
                end_season="2017",
                gap_seasons=["2016", "2017"],
                gap_type=GapType.FRANCHISE_SUSPENSION,
                competition_name="Indian Premier League",
                unexpected_field="disallowed",
            )

    def test_validate_assignment(self) -> None:
        """CareerGapRecord validates assignment mutations."""
        gap = CareerGapRecord(
            player_id=SYNTHETIC_PLAYER_UUID_PRIMARY,
            start_season="2016",
            end_season="2017",
            gap_seasons=["2016", "2017"],
            gap_type=GapType.FRANCHISE_SUSPENSION,
            competition_name="Indian Premier League",
        )
        with pytest.raises(ValidationError):
            gap.gap_type = "INVALID_GAP_TYPE"  # type: ignore[assignment]
