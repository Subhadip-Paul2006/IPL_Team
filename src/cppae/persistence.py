"""CPPAE Feature Store Persistence and Publisher (TRD §6, §11 Entity 31 `derived_features`).

Transforms typed CPPAEOutput contracts into TRD Entity 31 `DerivedFeature` records
and provides an offline persistence adapter / mock database client to safeguard against
Docker or live PostgreSQL 18 operations.
"""

from typing import Any
from uuid import UUID, uuid4

from src.contracts.cppae import CPPAEOutput
from src.contracts.features import DerivedFeature


class FeatureStorePublisher:
    """Transforms and publishes CPPAEOutput profiles to TRD Entity 31 `derived_features`."""

    def __init__(self, model_version: str = "v2.1") -> None:
        self.model_version = model_version

    def build_derived_features(
        self,
        cppae_output: CPPAEOutput,
        source_provenance: UUID | None = None,
    ) -> list[DerivedFeature]:
        """Convert a complete CPPAEOutput instance into individual DerivedFeature rows."""
        features: list[DerivedFeature] = []
        pid = cppae_output.player_id
        fmt = cppae_output.format_tag
        win = cppae_output.window

        # Helper to create feature record
        def make_feat(
            group: str,
            name: str,
            val_num: float | int | None = None,
            val_text: str | None = None,
            val_json: dict[str, Any] | None = None,
            status: str = "DERIVED",
        ) -> DerivedFeature:
            return DerivedFeature(
                feature_id=uuid4(),
                player_id=pid,
                feature_group=group,
                feature_name=name,
                feature_value_numeric=float(val_num) if val_num is not None else None,
                feature_value_text=val_text,
                feature_value_json=val_json,
                calculation_window=win,
                format_tag=fmt,
                status=status,
                model_version=self.model_version,
                source_provenance=source_provenance,
            )

        # 1. Batting Features
        if cppae_output.batting:
            bat = cppae_output.batting
            features.append(make_feat("Batting", "runs", val_num=bat.runs, status="OBSERVED"))
            features.append(make_feat("Batting", "balls_faced", val_num=bat.balls_faced, status="OBSERVED"))
            features.append(make_feat("Batting", "innings", val_num=bat.innings, status="OBSERVED"))
            features.append(make_feat("Batting", "matches", val_num=bat.matches, status="OBSERVED"))
            features.append(make_feat("Batting", "fours", val_num=bat.fours, status="OBSERVED"))
            features.append(make_feat("Batting", "sixes", val_num=bat.sixes, status="OBSERVED"))
            features.append(make_feat("Batting", "boundaries", val_num=bat.boundaries, status="OBSERVED"))
            features.append(make_feat("Batting", "dot_balls", val_num=bat.dot_balls, status="OBSERVED"))

            # Derived batting rates (for The Hundred, status is DEFERRED per Decision 2)
            rate_status = "DEFERRED" if fmt == "HUNDRED" else "DERIVED"
            features.append(make_feat("Batting", "batting_average", val_num=bat.batting_average, status="DEFERRED" if fmt == "HUNDRED" else ("DERIVED" if bat.batting_average is not None else "NOT_COMPUTABLE")))
            features.append(make_feat("Batting", "strike_rate", val_num=bat.strike_rate, status="DEFERRED" if fmt == "HUNDRED" else ("DERIVED" if bat.strike_rate is not None else "NOT_COMPUTABLE")))
            features.append(make_feat("Batting", "boundary_pct", val_num=bat.boundary_pct, status="DEFERRED" if fmt == "HUNDRED" else ("DERIVED" if bat.boundary_pct is not None else "NOT_COMPUTABLE")))
            features.append(make_feat("Batting", "dot_pct", val_num=bat.dot_pct, status="DEFERRED" if fmt == "HUNDRED" else ("DERIVED" if bat.dot_pct is not None else "NOT_COMPUTABLE")))

            # BPPS
            features.append(make_feat("Clutch & Pressure", "bpps", val_num=bat.bpps, val_text=bat.profile_tag, status="MODEL_INFERRED"))

            # Phase and position splits as JSON features
            if bat.phase_splits:
                phase_dict = {k: v.model_dump() for k, v in bat.phase_splits.items()}
                features.append(make_feat("Batting", "phase_splits", val_json=phase_dict, status=rate_status))

            if bat.position_splits:
                pos_dict = {k: v.model_dump() for k, v in bat.position_splits.items()}
                features.append(make_feat("Batting", "position_splits", val_json=pos_dict, status=rate_status))

        # 2. Bowling Features
        if cppae_output.bowling:
            bowl = cppae_output.bowling
            features.append(make_feat("Bowling", "legal_balls_bowled", val_num=bowl.legal_balls_bowled, status="OBSERVED"))
            features.append(make_feat("Bowling", "overs_display", val_text=bowl.overs_display, status="DERIVED"))
            features.append(make_feat("Bowling", "runs_conceded", val_num=bowl.runs_conceded, status="OBSERVED"))
            features.append(make_feat("Bowling", "wickets_taken", val_num=bowl.wickets_taken, status="OBSERVED"))
            features.append(make_feat("Bowling", "dot_balls_bowled", val_num=bowl.dot_balls_bowled, status="OBSERVED"))

            rate_status = "DEFERRED" if fmt == "HUNDRED" else "DERIVED"
            features.append(make_feat("Bowling", "economy_rate", val_num=bowl.economy_rate, status="DEFERRED" if fmt == "HUNDRED" else ("DERIVED" if bowl.economy_rate is not None else "NOT_COMPUTABLE")))
            features.append(make_feat("Bowling", "bowling_average", val_num=bowl.bowling_average, status="DEFERRED" if fmt == "HUNDRED" else ("DERIVED" if bowl.bowling_average is not None else "NOT_COMPUTABLE")))
            features.append(make_feat("Bowling", "bowling_strike_rate", val_num=bowl.bowling_strike_rate, status="DEFERRED" if fmt == "HUNDRED" else ("DERIVED" if bowl.bowling_strike_rate is not None else "NOT_COMPUTABLE")))
            features.append(make_feat("Bowling", "dot_pct", val_num=bowl.dot_pct, status="DEFERRED" if fmt == "HUNDRED" else ("DERIVED" if bowl.dot_pct is not None else "NOT_COMPUTABLE")))

            # BWPS and HLES
            features.append(make_feat("Clutch & Pressure", "bwps", val_num=bowl.bwps, status="MODEL_INFERRED"))
            hles_status = "DERIVED" if (fmt in ("T20", "IT20", "IPL") and bowl.hles is not None) else "DEFERRED"
            features.append(make_feat("Clutch & Pressure", "hles", val_num=bowl.hles, status=hles_status))

            # Phase splits
            if bowl.phase_splits:
                bowl_phase_dict = {k: v.model_dump() for k, v in bowl.phase_splits.items()}
                features.append(make_feat("Bowling", "phase_splits", val_json=bowl_phase_dict, status=rate_status))

            # Matchups
            if bowl.batter_matchups:
                bm_dict = {k: v.model_dump() for k, v in bowl.batter_matchups.items()}
                features.append(make_feat("Matchup Matrix", "batter_matchups", val_json=bm_dict, status="DERIVED"))

            # Speed & line length
            if bowl.speed_summary:
                features.append(make_feat("Bowling", "speed_summary", val_json=bowl.speed_summary.model_dump(), status=bowl.speed_summary.status))
            if bowl.line_length_summary:
                features.append(make_feat("Bowling", "line_length_summary", val_json=bowl.line_length_summary.model_dump(), status=bowl.line_length_summary.status))

        # 3. Fielding & Wicketkeeping Features
        if cppae_output.fielding:
            fld = cppae_output.fielding
            features.append(make_feat("Fielding", "catches", val_num=fld.catches, status="OBSERVED"))
            features.append(make_feat("Fielding", "run_outs_total", val_num=fld.run_outs_total, status="OBSERVED"))
            features.append(make_feat("Fielding", "run_outs_direct", val_num=fld.run_outs_direct, status="OBSERVED"))
            features.append(make_feat("Fielding", "run_outs_assisted", val_num=fld.run_outs_assisted, status="OBSERVED"))
            features.append(make_feat("Fielding", "stumpings", val_num=fld.stumpings, status="OBSERVED"))
            features.append(make_feat("Fielding", "coverage_class", val_text=fld.coverage_class, status="OBSERVED"))

        if cppae_output.wicketkeeping:
            wk = cppae_output.wicketkeeping
            features.append(make_feat("Wicketkeeping", "wk_appearances", val_num=wk.appearances, status="OBSERVED"))
            features.append(make_feat("Wicketkeeping", "wk_catches", val_num=wk.catches, status="OBSERVED"))
            features.append(make_feat("Wicketkeeping", "wk_stumpings", val_num=wk.stumpings, status="OBSERVED"))
            features.append(make_feat("Wicketkeeping", "wk_dismissals_total", val_num=wk.dismissals_total, status="OBSERVED"))
            features.append(make_feat("Wicketkeeping", "wk_dismissals_per_appearance", val_num=wk.dismissals_per_appearance, status="DERIVED" if wk.dismissals_per_appearance is not None else "NOT_COMPUTABLE"))

        # 4. Match Contribution Features
        if cppae_output.match_contribution:
            mc = cppae_output.match_contribution
            features.append(make_feat("Squad Intelligence", "potm_awards", val_num=mc.player_of_match_awards, status="OBSERVED"))
            features.append(make_feat("Squad Intelligence", "batting_contribution_pct", val_num=mc.batting_contribution_pct, status="DERIVED" if mc.batting_contribution_pct is not None else "NOT_COMPUTABLE"))
            features.append(make_feat("Squad Intelligence", "bowling_wicket_share_pct", val_num=mc.bowling_wicket_share_pct, status="DERIVED" if mc.bowling_wicket_share_pct is not None else "NOT_COMPUTABLE"))
            features.append(make_feat("Squad Intelligence", "bowling_run_suppression_pct", val_num=mc.bowling_run_suppression_pct, status="DERIVED" if mc.bowling_run_suppression_pct is not None else "NOT_COMPUTABLE"))
            features.append(make_feat("Squad Intelligence", "additive_composite", val_num=mc.additive_composite, status="DERIVED" if mc.additive_composite is not None else "NOT_COMPUTABLE"))
            features.append(make_feat("Squad Intelligence", "situation_context", val_json=mc.situation_context, status="OBSERVED"))
            features.append(make_feat("Squad Intelligence", "win_loss_performance", val_json=mc.win_loss_performance, status="DERIVED"))

        # 5. Career Coverage Features
        samples = cppae_output.samples
        features.append(make_feat("Career Coverage", "sample_matches", val_num=samples.matches, status="OBSERVED"))
        features.append(make_feat("Career Coverage", "sample_balls_faced", val_num=samples.balls_faced, status="OBSERVED"))
        features.append(make_feat("Career Coverage", "sample_legal_balls_bowled", val_num=samples.legal_balls_bowled, status="OBSERVED"))

        return features


class OfflineFeatureStoreAdapter:
    """In-memory offline database adapter and mock client for TRD Entity 31 persistence.

    Guarantees full isolation from Docker and live PostgreSQL 18.
    """

    def __init__(self) -> None:
        self._features_by_id: dict[UUID, DerivedFeature] = {}
        self._features_by_player: dict[UUID, list[DerivedFeature]] = {}

    def insert_feature(self, feature: DerivedFeature) -> None:
        """Insert or replace a DerivedFeature record."""
        self._features_by_id[feature.feature_id] = feature
        if feature.player_id not in self._features_by_player:
            self._features_by_player[feature.player_id] = []
        # Filter existing feature with same group and name in same format/window
        self._features_by_player[feature.player_id] = [
            f for f in self._features_by_player[feature.player_id]
            if not (f.feature_group == feature.feature_group and f.feature_name == feature.feature_name and f.format_tag == feature.format_tag and f.calculation_window == feature.calculation_window)
        ]
        self._features_by_player[feature.player_id].append(feature)

    def insert_features_batch(self, features: list[DerivedFeature]) -> int:
        """Insert a batch of features transactionally."""
        for f in features:
            self.insert_feature(f)
        return len(features)

    def get_features_by_player(
        self,
        player_id: UUID,
        feature_group: str | None = None,
        format_tag: str | None = None,
    ) -> list[DerivedFeature]:
        """Query features for a player with optional group and format filters."""
        feats = self._features_by_player.get(player_id, [])
        if feature_group:
            feats = [f for f in feats if f.feature_group == feature_group]
        if format_tag:
            feats = [f for f in feats if f.format_tag == format_tag]
        return feats

    def count(self) -> int:
        """Total records in the mock derived_features store."""
        return len(self._features_by_id)

    def clear(self) -> None:
        """Reset the mock store."""
        self._features_by_id.clear()
        self._features_by_player.clear()
