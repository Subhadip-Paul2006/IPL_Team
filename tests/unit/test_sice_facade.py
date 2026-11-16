"""Unit tests for SICE Master Facade, Contracts, and Domain Exceptions.

Verifies:
- SICEEngine ServiceBoundary implementation, health check, and subsystem wiring.
- Pydantic v2 data contracts, validators, extra="forbid", NaN/Inf rejection, and bounds.
- SICE domain exception hierarchy and error code propagation.
- Backwards compatibility with Phase 1B prototype imports.
"""

from datetime import date
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.contracts.sice import (
    AnalyticalRecommendation,
    CandidateRankingStatus,
    CandidateReplacementEvaluation,
    DimensionAdvantage,
    DimensionComparisonResult,
    DimensionStatus,
    LineupEvaluationResult,
    LineupType,
    RankedCandidateContract,
    RankingBoardOutputContract,
    RecommendationLabel,
    RecommendationState,
    ReplacementComparisonOutputContract,
    ReplacementComparisonRequest,
    RosterStatus,
    RunType,
    SICEContractVersion,
    SICEOutputContract,
    SquadBalanceDimensions,
    UncertaintyFlag,
)
from src.contracts.team_builder import UserTeam
from src.core.exceptions import RRPlatformError
from src.services.base import ServiceBoundary
from src.sice import (
    DatabaseEnvironmentGuardError,
    GateFailureError,
    IncompleteRosterError,
    RankedCandidate,
    RankingDeterminismError,
    RankingResult,
    RepositoryMode,
    RoleCompatibilityError,
    SafetyReviewInterceptionError,
    ScorecardGranularityError,
    SICEEngine,
    SICEError,
    SiceRankingEngine,
    SICERepository,
    SquadConstraintViolationError,
)

# ==============================================================================
# 1. ServiceBoundary & Facade Tests
# ==============================================================================


def test_sice_engine_inheritance_and_service_name() -> None:
    """Verify SICEEngine inherits from ServiceBoundary and returns canonical service name."""
    engine = SICEEngine()
    assert isinstance(engine, ServiceBoundary)
    assert engine.get_service_name() == "squad_intelligence_comparison_engine"


def test_sice_engine_health_check_defaults() -> None:
    """Verify SICEEngine health_check reports healthy status with uninitialized subsystems."""
    engine = SICEEngine(default_seed=123)
    health = engine.health_check()

    assert health["service"] == "squad_intelligence_comparison_engine"
    assert health["status"] == "healthy"
    assert health["default_seed"] == 123
    assert health["subsystems"] == {
        "ranking_engine": "uninitialized",
        "composition_engine": "uninitialized",
        "replacement_engine": "uninitialized",
        "team_builder": "uninitialized",
        "repository": "uninitialized",
    }


def test_sice_engine_subsystem_injection_and_properties() -> None:
    """Verify injected subsystems are exposed via properties and reflected in health_check."""
    mock_ranking = MagicMock()
    mock_composition = MagicMock()
    mock_replacement = MagicMock()
    mock_builder = MagicMock()
    mock_repo = MagicMock()

    engine = SICEEngine(
        ranking_engine=mock_ranking,
        composition_engine=mock_composition,
        replacement_engine=mock_replacement,
        team_builder=mock_builder,
        repository=mock_repo,
    )

    assert engine.ranking_engine is mock_ranking
    assert engine.composition_engine is mock_composition
    assert engine.replacement_engine is mock_replacement
    assert engine.team_builder is mock_builder
    assert engine.repository is mock_repo

    health = engine.health_check()
    assert health["subsystems"] == {
        "ranking_engine": "ready",
        "composition_engine": "ready",
        "replacement_engine": "ready",
        "team_builder": "ready",
        "repository": "ready",
    }


def test_sice_engine_method_stubs_without_injection() -> None:
    """Verify methods raise NotImplementedError when subsystems are not wired."""
    engine = SICEEngine()
    dummy_uuid = uuid4()

    # evaluate_squad requires UUID
    with pytest.raises(NotImplementedError, match="Squad composition engine not yet wired"):
        engine.evaluate_squad(dummy_uuid)

    # compare_replacement requires ReplacementComparisonRequest
    req = ReplacementComparisonRequest(
        incumbent_player_id=dummy_uuid,
        target_season_id=dummy_uuid,
        evaluation_date=date(2027, 4, 1),
    )
    with pytest.raises(NotImplementedError, match="Replacement engine not yet wired"):
        engine.compare_replacement(req)

    # run_ranking
    with pytest.raises(NotImplementedError, match="Ranking engine refactor not yet wired"):
        engine.run_ranking(config_version="RK-1.0.0")


def test_sice_engine_method_stubs_input_validation() -> None:
    """Verify method stubs enforce strict input types before attempting delegation."""
    engine = SICEEngine()

    with pytest.raises(TypeError, match="team_id must be a UUID instance"):
        engine.evaluate_squad("not-a-uuid")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="request must be a ReplacementComparisonRequest instance"):
        engine.compare_replacement({"invalid": "dict"})  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="config_version must be a non-empty string"):
        engine.run_ranking(config_version="")


def test_sice_engine_delegation_when_wired() -> None:
    """Verify SICEEngine delegates method calls to injected subsystems."""
    mock_comp = MagicMock()
    mock_comp.evaluate_squad.return_value = "mock_squad_output"

    mock_repl = MagicMock()
    mock_repl.compare_replacement.return_value = "mock_replacement_output"

    mock_rank = MagicMock()
    mock_rank.run_ranking.return_value = "mock_ranking_output"

    engine = SICEEngine(
        composition_engine=mock_comp,
        replacement_engine=mock_repl,
        ranking_engine=mock_rank,
    )

    t_id = uuid4()
    assert engine.evaluate_squad(t_id, context={"test": 1}) == "mock_squad_output"
    mock_comp.evaluate_squad.assert_called_once_with(t_id, context={"test": 1})

    req = ReplacementComparisonRequest(
        incumbent_player_id=t_id,
        target_season_id=t_id,
        evaluation_date=date(2027, 4, 1),
    )
    assert engine.compare_replacement(req) == "mock_replacement_output"
    mock_repl.compare_replacement.assert_called_once_with(req)

    assert engine.run_ranking(config_version="RK-1.0.0", seed=42) == "mock_ranking_output"
    mock_rank.run_ranking.assert_called_once_with(
        config_version="RK-1.0.0",
        candidate_pool=None,
        seed=42,
    )


def test_sice_engine_create_default_wires_all_subsystems() -> None:
    """Verify SICEEngine.create_default() wires all subsystems into ready state."""
    engine = SICEEngine.create_default(default_seed=42)

    assert engine.ranking_engine is not None
    assert engine.composition_engine is not None
    assert engine.replacement_engine is not None
    assert engine.team_builder is not None
    assert engine.repository is not None

    health = engine.health_check()
    assert health["status"] == "healthy"
    assert health["subsystems"] == {
        "ranking_engine": "ready",
        "composition_engine": "ready",
        "replacement_engine": "ready",
        "team_builder": "ready",
        "repository": "ready",
    }


def test_sice_engine_default_facade_ranking_and_replacement() -> None:
    """Verify default SICEEngine executes ranking and replacement via facade without NotImplementedError."""
    engine = SICEEngine.create_default(default_seed=42)

    # Ranking via facade
    board = engine.run_ranking(config_version="RK-1.0.0", candidate_pool=[], seed=42)
    assert isinstance(board, RankingBoardOutputContract)
    assert board.contract_version == "RK-1.0.0"

    # Replacement via facade
    inc_id = uuid4()
    req = ReplacementComparisonRequest(
        incumbent_player_id=inc_id,
        target_season_id=uuid4(),
        evaluation_date=date(2027, 4, 1),
    )
    res = engine.compare_replacement(req)
    assert isinstance(res, ReplacementComparisonOutputContract)
    assert res.incumbent_player_id == inc_id


# ==============================================================================
# 2. Contract Instantiation & Validation Tests
# ==============================================================================


def test_ranked_candidate_contract_valid() -> None:
    """Verify valid RankedCandidateContract construction and serialization."""
    candidate_id = uuid4()
    candidate = RankedCandidateContract(
        rank=1,
        player_id=candidate_id,
        canonical_name="Vaibhav Suryavanshi",
        role="TOP_ORDER_BATTER",
        age_at_evaluation=16.0,
        score=92.5,
        score_ci_lower=88.0,
        score_ci_upper=96.0,
        top10_stability_pct=95.0,
        match_appearances=14,
        volume_total=420,
        volume_pressure=180,
        key_metric_raw=148.5,
        key_metric_shrunk=142.0,
        delta_metric=24.5,
        consistency_score=0.85,
        career_batting_average=45.2,
        career_batting_strike_rate=145.8,
        career_balls_faced=350,
        status=CandidateRankingStatus.TOP_10,
        uncertainty_flag=UncertaintyFlag.VERIFIED,
        format_tags=["DOMESTIC_T20"],
    )

    assert candidate.rank == 1
    assert candidate.player_id == candidate_id
    assert candidate.age_at_evaluation == 16.0
    assert candidate.career_batting_average == 45.2

    # Verify serialization
    data = candidate.model_dump()
    assert data["canonical_name"] == "Vaibhav Suryavanshi"
    assert data["rank"] == 1


def test_ranked_candidate_contract_nan_inf_rejection() -> None:
    """Verify NaN and Infinity are strictly rejected on float fields (Rule R1)."""
    cand_id = uuid4()
    base_kwargs = {
        "rank": 1,
        "player_id": cand_id,
        "canonical_name": "Test Player",
        "role": "BATTER",
        "age_at_evaluation": 20.0,
        "score": 80.0,
    }

    # NaN in score
    with pytest.raises(ValidationError, match="NaN or Infinity forbidden"):
        RankedCandidateContract(**{**base_kwargs, "score": float("nan")})

    # Infinity in score_ci_lower
    with pytest.raises(ValidationError, match="NaN or Infinity forbidden"):
        RankedCandidateContract(**{**base_kwargs, "score_ci_lower": float("inf")})

    # -Infinity in delta_metric
    with pytest.raises(ValidationError, match="NaN or Infinity forbidden"):
        RankedCandidateContract(**{**base_kwargs, "delta_metric": float("-inf")})


def test_string_nan_inf_rejection_across_contracts() -> None:
    """Verify string NaN/Inf representations ('nan', 'inf', etc.) are rejected (Rule R1)."""
    cand_id = uuid4()
    base_kwargs = {
        "rank": 1,
        "player_id": cand_id,
        "canonical_name": "Test Player",
        "role": "BATTER",
        "age_at_evaluation": 20.0,
        "score": 80.0,
    }

    # Test various string NaN / Inf representations in float fields
    for bad_str in [
        "nan",
        "NaN",
        "+nan",
        "-nan",
        "inf",
        "+inf",
        "-inf",
        "infinity",
        "+infinity",
        "-infinity",
    ]:
        with pytest.raises(ValidationError, match="NaN or Infinity forbidden"):
            RankedCandidateContract(**{**base_kwargs, "career_batting_average": bad_str})  # type: ignore[arg-type]

        with pytest.raises(ValidationError, match="NaN or Infinity forbidden"):
            RankedCandidateContract(**{**base_kwargs, "key_metric_raw": bad_str})  # type: ignore[arg-type]

    # Test string NaN in JSON deserialization
    cand = RankedCandidateContract(**base_kwargs)
    json_str = cand.model_dump_json().replace(
        '"career_batting_average":null', '"career_batting_average":"nan"'
    )
    with pytest.raises(ValidationError, match="NaN or Infinity forbidden"):
        RankedCandidateContract.model_validate_json(json_str)

    # Test string NaN/Inf in dictionary fields
    with pytest.raises(ValidationError, match="NaN or Infinity forbidden in DIM-01"):
        SquadBalanceDimensions(dimension_scores={"DIM-01": "nan"})  # type: ignore[arg-type]

    with pytest.raises(ValidationError, match="NaN or Infinity forbidden in death"):
        SquadBalanceDimensions(phase_coverage_status={"death": "inf"})  # type: ignore[arg-type]

    with pytest.raises(ValidationError, match="NaN or Infinity forbidden in role"):
        CandidateReplacementEvaluation(
            candidate_player_id=cand_id,
            canonical_name="Candidate A",
            age_at_evaluation=21.0,
            role_compatibility="FULL_COMPATIBILITY",
            recommendation_label=RecommendationState.ANALYTICAL_REPLACEMENT_CANDIDATE,
            similarity_scores={"role": "-inf"},  # type: ignore[arg-type]
        )


def test_ranked_candidate_contract_bounds_and_invariants() -> None:
    """Verify age, rank, and CI lower/upper bounds."""
    cand_id = uuid4()
    base_kwargs = {
        "rank": 1,
        "player_id": cand_id,
        "canonical_name": "Test Player",
        "role": "BATTER",
        "age_at_evaluation": 20.0,
        "score": 80.0,
    }

    # rank < 1 rejected
    with pytest.raises(ValidationError):
        RankedCandidateContract(**{**base_kwargs, "rank": 0})

    # age < 14 rejected
    with pytest.raises(ValidationError):
        RankedCandidateContract(**{**base_kwargs, "age_at_evaluation": 13.9})

    # age > 55 rejected
    with pytest.raises(ValidationError):
        RankedCandidateContract(**{**base_kwargs, "age_at_evaluation": 55.1})

    # score_ci_lower > score_ci_upper rejected
    with pytest.raises(
        ValidationError, match="score_ci_lower cannot be greater than score_ci_upper"
    ):
        RankedCandidateContract(**{**base_kwargs, "score_ci_lower": 90.0, "score_ci_upper": 85.0})

    # extra attribute rejected (extra="forbid")
    with pytest.raises(ValidationError):
        RankedCandidateContract(**{**base_kwargs, "illegal_extra_field": "breach"})


def test_ranking_board_output_contract_valid_and_validators() -> None:
    """Verify RankingBoardOutputContract structure and sha256/size validators."""
    config_id = uuid4()
    season_id = uuid4()
    sha256_hash = "a" * 64

    board = RankingBoardOutputContract(
        config_id=config_id,
        target_season_id=season_id,
        evaluation_date=date(2027, 4, 1),
        data_snapshot_sha256=sha256_hash,
        qualified_candidates_count=25,
        bootstrap_iterations=1000,
        seed=42,
    )

    assert board.data_snapshot_sha256 == sha256_hash
    assert board.qualified_candidates_count == 25
    assert board.contract_version == SICEContractVersion.RANKING_VERSION.value

    # Reject non-64 length sha256
    with pytest.raises(ValidationError):
        RankingBoardOutputContract(
            config_id=config_id,
            target_season_id=season_id,
            evaluation_date=date(2027, 4, 1),
            data_snapshot_sha256="tooshort",
            qualified_candidates_count=5,
        )

    # Reject non-hex sha256 of 64 chars
    with pytest.raises(ValidationError, match="valid 64-character hexadecimal SHA256 string"):
        RankingBoardOutputContract(
            config_id=config_id,
            target_season_id=season_id,
            evaluation_date=date(2027, 4, 1),
            data_snapshot_sha256="z" * 64,
            qualified_candidates_count=5,
        )


def test_ranking_board_top10_max_size() -> None:
    """Verify RankingBoardOutputContract enforces len(top10) <= 10."""
    candidates = [
        RankedCandidateContract(
            rank=i + 1,
            player_id=uuid4(),
            canonical_name=f"Player {i + 1}",
            role="BATTER",
            age_at_evaluation=21.0,
            score=80.0 - i,
        )
        for i in range(11)
    ]

    with pytest.raises(ValidationError, match="top10 list cannot contain more than 10 candidates"):
        RankingBoardOutputContract(
            config_id=uuid4(),
            target_season_id=uuid4(),
            evaluation_date=date(2027, 4, 1),
            data_snapshot_sha256="0" * 64,
            qualified_candidates_count=11,
            top10=candidates,
        )


def test_dimension_comparison_result_valid_and_nan_check() -> None:
    """Verify DimensionComparisonResult instantiation and validation."""
    dim = DimensionComparisonResult(
        dimension_id="D01",
        dimension_name="Base Scoring Rate",
        incumbent_value=135.2,
        candidate_value=152.4,
        delta=17.2,
        incumbent_sample=120,
        candidate_sample=95,
        advantage=DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE.value,
        confidence_interval_lower=10.5,
        confidence_interval_upper=23.9,
        computable=True,
        dimension_status=DimensionStatus.COMPUTED,
    )
    assert dim.dimension_id == "D01"
    assert dim.delta == 17.2

    # Reject NaN in delta
    with pytest.raises(ValidationError, match="NaN or Infinity forbidden"):
        DimensionComparisonResult(
            dimension_id="D01",
            dimension_name="Base Scoring Rate",
            delta=float("nan"),
        )

    # Reject CI lower > upper
    with pytest.raises(ValidationError, match="confidence_interval_lower cannot be greater than"):
        DimensionComparisonResult(
            dimension_id="D01",
            dimension_name="Base Scoring Rate",
            confidence_interval_lower=25.0,
            confidence_interval_upper=15.0,
        )


def test_candidate_replacement_evaluation_and_hd13() -> None:
    """Verify CandidateReplacementEvaluation and overseas_slot_liberated flag (HD-13)."""
    cand_id = uuid4()
    eval_res = CandidateReplacementEvaluation(
        candidate_player_id=cand_id,
        canonical_name="Domestic Candidate",
        age_at_evaluation=22.0,
        role_compatibility="DIRECT_ROLE_MATCH",
        recommendation_label=RecommendationState.ANALYTICAL_REPLACEMENT_CANDIDATE,
        confidence=0.92,
        overseas_slot_liberated=True,
    )

    assert eval_res.candidate_player_id == cand_id
    assert eval_res.overseas_slot_liberated is True
    assert eval_res.recommendation_label == RecommendationState.ANALYTICAL_REPLACEMENT_CANDIDATE

    # Confidence bounds [0, 1]
    with pytest.raises(ValidationError):
        CandidateReplacementEvaluation(
            candidate_player_id=cand_id,
            canonical_name="Domestic Candidate",
            age_at_evaluation=22.0,
            role_compatibility="MATCH",
            recommendation_label=RecommendationState.ANALYTICAL_REPLACEMENT_CANDIDATE,
            confidence=1.05,
        )


def test_squad_balance_dimensions_validation() -> None:
    """Verify SquadBalanceDimensions metrics and bounds."""
    balance = SquadBalanceDimensions(
        roster_capacity_status="ROSTER_VALID",
        squad_size=22,
        overseas_count=7,
        overseas_ratio=7 / 22,
        domestic_count=15,
        wicketkeeper_count=2,
        all_rounder_count=5,
        frontline_bowlers_count=5,
        pace_bowler_count=4,
        spin_bowler_count=3,
        batting_depth_index=68.5,
        lower_order_resilience=48.2,
    )
    assert balance.squad_size == 22
    assert balance.overseas_count == 7

    # Reject overseas_ratio > 1.0
    with pytest.raises(ValidationError):
        SquadBalanceDimensions(overseas_ratio=1.2)

    # Reject NaN in dimension_scores
    with pytest.raises(ValidationError, match="NaN or Infinity forbidden"):
        SquadBalanceDimensions(dimension_scores={"DIM-03": float("nan")})


def test_lineup_evaluation_result_validation() -> None:
    """Verify LineupEvaluationResult validates maximum 11 starting players."""
    p_ids = [uuid4() for _ in range(11)]
    lineup = LineupEvaluationResult(
        lineup_type=LineupType.TRADITIONAL_XI.value,
        starting_xi_player_ids=p_ids,
        batting_order=p_ids,
        overseas_count=4,
        is_valid_ipl_lineup=True,
    )
    assert len(lineup.starting_xi_player_ids) == 11

    # Starting XI > 11 rejected
    with pytest.raises(ValidationError, match="Starting XI cannot contain more than 11 players"):
        LineupEvaluationResult(
            starting_xi_player_ids=[uuid4() for _ in range(12)],
        )


def test_enum_field_strict_typing_rejection() -> None:
    """Verify contracts strictly reject invalid string inputs for Enum-typed fields."""
    # DimensionComparisonResult.advantage
    with pytest.raises(ValidationError):
        DimensionComparisonResult(
            dimension_id="D01",
            dimension_name="SR",
            advantage="INVALID_ADVANTAGE",  # type: ignore[arg-type]
        )

    # SquadBalanceDimensions.roster_capacity_status
    with pytest.raises(ValidationError):
        SquadBalanceDimensions(roster_capacity_status="INVALID_ROSTER_STATUS")  # type: ignore[arg-type]

    # LineupEvaluationResult.lineup_type
    with pytest.raises(ValidationError):
        LineupEvaluationResult(lineup_type="INVALID_LINEUP_TYPE")  # type: ignore[arg-type]

    # Valid enum instantiations and conversions
    dim = DimensionComparisonResult(
        dimension_id="D01",
        dimension_name="SR",
        advantage=DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE,
    )
    assert dim.advantage == DimensionAdvantage.SIGNIFICANT_CANDIDATE_ADVANTAGE

    squad = SquadBalanceDimensions(roster_capacity_status=RosterStatus.ROSTER_VALID)
    assert squad.roster_capacity_status == RosterStatus.ROSTER_VALID

    lineup = LineupEvaluationResult(lineup_type=LineupType.BAT_FIRST_IMPACT)
    assert lineup.lineup_type == LineupType.BAT_FIRST_IMPACT


def test_analytical_recommendation_validation() -> None:
    """Verify AnalyticalRecommendation instantiation, confidence bounds, and NaN rejection."""
    rec = AnalyticalRecommendation(
        statement="Player shows high boundary percentage and strong death overs economy.",
        evidence_metrics=["D03", "D08"],
        confidence=0.88,
        label="HIGH_CONFIDENCE_RECOMMENDATION",
    )
    assert rec.confidence == 0.88
    assert rec.label == "HIGH_CONFIDENCE_RECOMMENDATION"

    # Reject NaN in confidence
    with pytest.raises(ValidationError, match="NaN or Infinity forbidden"):
        AnalyticalRecommendation(
            statement="Invalid recommendation",
            confidence=float("nan"),
        )

    # Reject confidence out of bounds
    with pytest.raises(ValidationError):
        AnalyticalRecommendation(
            statement="Invalid recommendation",
            confidence=1.5,
        )


def test_replacement_comparison_output_contract_validation() -> None:
    """Verify ReplacementComparisonOutputContract instantiation, SHA-256, and enum types."""
    incumbent_id = uuid4()
    season_id = uuid4()
    sha256_hash = "c" * 64

    output = ReplacementComparisonOutputContract(
        incumbent_player_id=incumbent_id,
        incumbent_canonical_name="Shimron Hetmyer",
        incumbent_role="MIDDLE_ORDER_BATTER",
        replaceability_signal="POTENTIALLY_REPLACEABLE",
        evaluation_date=date(2027, 4, 1),
        target_season_id=season_id,
        recommended_action=RecommendationState.ANALYTICAL_REPLACEMENT_CANDIDATE,
        review_status="CLEAR",
        data_snapshot_sha256=sha256_hash,
        run_type=RunType.REPLACEMENT_EVALUATION,
        overseas_slot_liberated=True,
    )

    assert output.contract_version == SICEContractVersion.REPLACEMENT_VERSION.value
    assert output.overseas_slot_liberated is True
    assert output.run_type == RunType.REPLACEMENT_EVALUATION

    # Reject non-hex 64-char string
    with pytest.raises(ValidationError, match="valid 64-character hexadecimal SHA256 string"):
        ReplacementComparisonOutputContract(
            incumbent_player_id=incumbent_id,
            incumbent_canonical_name="Shimron Hetmyer",
            incumbent_role="MIDDLE_ORDER_BATTER",
            replaceability_signal="POTENTIALLY_REPLACEABLE",
            evaluation_date=date(2027, 4, 1),
            target_season_id=season_id,
            recommended_action=RecommendationState.ANALYTICAL_REPLACEMENT_CANDIDATE,
            data_snapshot_sha256="z" * 64,
        )


def test_sice_output_contract_draft_tolerance_hd09() -> None:
    """Verify HD-09 draft tolerance: squad_health_index must be None for incomplete draft squads."""
    team_id = uuid4()
    balance = SquadBalanceDimensions(squad_size=12, domestic_count=10, overseas_count=2)

    # Valid incomplete draft squad with squad_health_index = None
    output = SICEOutputContract(
        team_id=team_id,
        target_season="2027",
        squad_size=12,
        is_valid_ipl_roster=False,
        roster_status=RosterStatus.ROSTER_INCOMPLETE,
        squad_health_index=None,
        uncertainty_badge="DRAFT_EXPLORATION",
        balance_dimensions=balance,
    )
    assert output.squad_size == 12
    assert output.squad_health_index is None
    assert output.is_valid_ipl_roster is False

    # Illegal: squad_size < 18 with squad_health_index not None
    with pytest.raises(
        ValidationError, match="squad_health_index must be None for incomplete draft"
    ):
        SICEOutputContract(
            team_id=team_id,
            target_season="2027",
            squad_size=12,
            is_valid_ipl_roster=False,
            roster_status=RosterStatus.ROSTER_INCOMPLETE,
            squad_health_index=72.5,
            uncertainty_badge="DRAFT_EXPLORATION",
            balance_dimensions=balance,
        )


def test_sice_output_contract_complete_roster() -> None:
    """Verify valid complete 20-man squad evaluation."""
    team_id = uuid4()
    balance = SquadBalanceDimensions(squad_size=20, domestic_count=14, overseas_count=6)
    output = SICEOutputContract(
        team_id=team_id,
        target_season="2027",
        squad_size=20,
        is_valid_ipl_roster=True,
        roster_status=RosterStatus.ROSTER_VALID,
        squad_health_index=84.2,
        uncertainty_badge="OFFICIAL_CERTIFIED",
        balance_dimensions=balance,
    )
    assert output.is_valid_ipl_roster is True
    assert output.squad_health_index == 84.2


def test_sice_output_contract_draft_tolerance_hd09_roster_invariants() -> None:
    """Verify HD-09/HD-05 invariants: squad_size < 18 or > 25 cannot be valid IPL roster."""
    team_id = uuid4()
    balance = SquadBalanceDimensions(squad_size=16, domestic_count=12, overseas_count=4)

    # squad_size < 18 cannot have is_valid_ipl_roster=True
    with pytest.raises(ValidationError, match="cannot be certified as valid IPL roster"):
        SICEOutputContract(
            team_id=team_id,
            target_season="2027",
            squad_size=16,
            is_valid_ipl_roster=True,
            roster_status=RosterStatus.ROSTER_VALID,
            squad_health_index=None,
            uncertainty_badge="CERTIFIED",
            balance_dimensions=balance,
        )

    # squad_size > 25 cannot have is_valid_ipl_roster=True
    oversized_balance = SquadBalanceDimensions(squad_size=26, domestic_count=18, overseas_count=8)
    with pytest.raises(ValidationError, match="exceeds maximum IPL roster capacity"):
        SICEOutputContract(
            team_id=team_id,
            target_season="2027",
            squad_size=26,
            is_valid_ipl_roster=True,
            roster_status=RosterStatus.ROSTER_OVERSIZED,
            squad_health_index=None,
            uncertainty_badge="CERTIFIED",
            balance_dimensions=oversized_balance,
        )

    # squad_size > 25 is allowed in draft exploration when is_valid_ipl_roster=False
    oversized_draft = SICEOutputContract(
        team_id=team_id,
        target_season="2027",
        squad_size=26,
        is_valid_ipl_roster=False,
        roster_status=RosterStatus.ROSTER_OVERSIZED,
        squad_health_index=None,
        uncertainty_badge="DRAFT_EXPLORATION",
        balance_dimensions=oversized_balance,
    )
    assert oversized_draft.squad_size == 26
    assert oversized_draft.is_valid_ipl_roster is False
    assert oversized_draft.roster_status == RosterStatus.ROSTER_OVERSIZED


# ==============================================================================
# 3. Domain Exception Hierarchy Tests
# ==============================================================================


def test_sice_exceptions_hierarchy() -> None:
    """Verify all domain exceptions properly subclass RRPlatformError and SICEError."""
    err = SICEError("Base SICE error")
    assert isinstance(err, RRPlatformError)
    assert isinstance(err, Exception)

    constraint_err = SquadConstraintViolationError(
        "Overseas limit breach", violation_type="OVERSEAS_BREACH"
    )
    assert isinstance(constraint_err, SICEError)
    assert constraint_err.code == "SQUAD_CONSTRAINT_VIOLATION"
    assert constraint_err.details["violation_type"] == "OVERSEAS_BREACH"

    roster_err = IncompleteRosterError("Squad has only 14 players", squad_size=14)
    assert isinstance(roster_err, SquadConstraintViolationError)
    assert roster_err.details["squad_size"] == 14
    assert roster_err.details["violation_type"] == "ROSTER_INCOMPLETE"

    gate_err = GateFailureError("Strike rate below threshold", role_group="FINISHER", metric="B06")
    assert isinstance(gate_err, SICEError)
    assert gate_err.details["role_group"] == "FINISHER"
    assert gate_err.details["metric"] == "B06"

    det_err = RankingDeterminismError("Tiebreaker ambiguity on identical metrics")
    assert isinstance(det_err, SICEError)
    assert det_err.code == "RANKING_DETERMINISM_ERROR"

    safety_err = SafetyReviewInterceptionError("Upstream conflict detected", dossier_id="DOS-001")
    assert isinstance(safety_err, SICEError)
    assert safety_err.details["dossier_id"] == "DOS-001"

    sc_err = ScorecardGranularityError("Delivery ball-by-ball records absent")
    assert isinstance(sc_err, SICEError)
    assert sc_err.code == "SCORECARD_GRANULARITY_ERROR"

    role_err = RoleCompatibilityError(
        "Cannot replace spin bowler with pace bowler",
        incumbent_role="SPINNER",
        candidate_role="PACER",
    )
    assert isinstance(role_err, SICEError)
    assert role_err.details["incumbent_role"] == "SPINNER"
    assert role_err.details["candidate_role"] == "PACER"

    db_guard_err = DatabaseEnvironmentGuardError("Direct port 5432 network access blocked")
    assert isinstance(db_guard_err, RuntimeError)
    assert isinstance(db_guard_err, SICEError)
    assert isinstance(db_guard_err, RRPlatformError)


# ==============================================================================
# 4. Backwards Compatibility Tests
# ==============================================================================


def test_sice_backwards_compatibility_exports() -> None:
    """Verify legacy ranking engine and models remain importable from src.sice."""
    assert SiceRankingEngine is not None
    assert RankedCandidate is not None
    assert RankingResult is not None

    legacy_engine = SiceRankingEngine(seed=42)
    assert hasattr(legacy_engine, "rank_batters")
    assert hasattr(legacy_engine, "rank_bowlers")
    assert hasattr(legacy_engine, "run_match_level_bootstrap")
    assert RecommendationLabel is RecommendationState


# ==============================================================================
# 5. Expanded Facade Subsystem Integration Tests (Milestone 6)
# ==============================================================================


def test_sice_engine_rank_uncapped_candidates_delegation() -> None:
    """Verify rank_uncapped_candidates delegates cleanly to ranking_engine."""
    mock_rank = MagicMock()
    mock_rank.run_ranking.return_value = "mock_board"

    engine = SICEEngine(ranking_engine=mock_rank)
    res = engine.rank_uncapped_candidates(config_version="RK-1.0.0", candidate_pool=[], seed=10)

    assert res == "mock_board"
    mock_rank.run_ranking.assert_called_once_with(
        config_version="RK-1.0.0",
        candidate_pool=[],
        seed=10,
    )


def test_sice_engine_optimize_playing_xi_delegation() -> None:
    """Verify optimize_playing_xi delegates to composition engine and handles team_id lookup."""
    mock_comp = MagicMock()
    mock_comp.optimize_playing_xi.return_value = ["mock_lineup"]
    mock_repo = MagicMock()
    t_id = uuid4()
    mock_player = MagicMock()
    mock_repo.get_team_players.return_value = [mock_player]

    engine = SICEEngine(composition_engine=mock_comp, repository=mock_repo)

    # Calling with team_id fetches players from repository
    res = engine.optimize_playing_xi(team_id=t_id, enable_impact_player=True)
    assert res == ["mock_lineup"]
    mock_repo.get_team_players.assert_called_once_with(t_id)
    mock_comp.optimize_playing_xi.assert_called_once_with(
        players=[mock_player],
        player_metadata=None,
        enable_impact_player=True,
        seed=42,
        tactical_scenario="BALANCED",
    )

    # Calling without players or team_id raises ValueError
    with pytest.raises(ValueError, match="Either players list or team_id must be provided"):
        engine.optimize_playing_xi()

    # Calling without composition_engine raises NotImplementedError
    unwired = SICEEngine()
    with pytest.raises(NotImplementedError, match="Squad composition engine not yet wired"):
        unwired.optimize_playing_xi(team_id=t_id)


def test_sice_engine_team_builder_crud_delegation() -> None:
    """Verify Team Builder CRUD methods delegate to team_builder service and enforce wiring."""
    unwired = SICEEngine()
    t_id = uuid4()
    p_id = uuid4()

    # Verify NotImplementedError when unwired
    with pytest.raises(NotImplementedError, match="Team builder service not yet wired"):
        unwired.create_user_team("Test Team")
    with pytest.raises(NotImplementedError, match="Team builder service not yet wired"):
        unwired.get_user_team(t_id)
    with pytest.raises(NotImplementedError, match="Team builder service not yet wired"):
        unwired.update_user_team(t_id, team_name="New Name")
    with pytest.raises(NotImplementedError, match="Team builder service not yet wired"):
        unwired.delete_user_team(t_id)
    with pytest.raises(NotImplementedError, match="Team builder service not yet wired"):
        unwired.list_user_teams()
    with pytest.raises(NotImplementedError, match="Team builder service not yet wired"):
        unwired.add_player_to_team(t_id, p_id)
    with pytest.raises(NotImplementedError, match="Team builder service not yet wired"):
        unwired.update_player_in_team(t_id, p_id, batting_order=3)
    with pytest.raises(NotImplementedError, match="Team builder service not yet wired"):
        unwired.remove_player_from_team(t_id, p_id)
    with pytest.raises(NotImplementedError, match="Team builder service not yet wired"):
        unwired.get_team_players(t_id)
    with pytest.raises(NotImplementedError, match="Team builder service not yet wired"):
        unwired.validate_roster(t_id)

    # Verify delegation when wired
    mock_builder = MagicMock()
    mock_builder.create_team.return_value = "mock_team"
    mock_builder.get_team.return_value = "mock_team"
    mock_builder.update_team.return_value = "mock_team"
    mock_builder.delete_team.return_value = True
    mock_builder.list_teams.return_value = ["mock_team"]
    mock_builder.add_player.return_value = "mock_player"
    mock_builder.update_player.return_value = "mock_player"
    mock_builder.remove_player.return_value = True
    mock_builder.get_team_players.return_value = ["mock_player"]
    mock_builder.validate_roster.return_value = RosterStatus.ROSTER_VALID

    engine = SICEEngine(team_builder=mock_builder)

    assert engine.create_user_team("Team A", target_season="IPL 2027") == "mock_team"
    assert engine.create_team("Team A", target_season="IPL 2027") == "mock_team"
    mock_builder.create_team.assert_called_with(
        team_name="Team A",
        target_season="IPL 2027",
        created_by=None,
        notes=None,
        team_id=None,
    )

    assert engine.get_user_team(t_id) == "mock_team"
    assert engine.get_team(t_id) == "mock_team"
    mock_builder.get_team.assert_called_with(t_id)

    assert engine.update_user_team(t_id, team_name="Updated") == "mock_team"
    assert engine.update_team(t_id, team_name="Updated") == "mock_team"
    mock_builder.update_team.assert_called_with(
        team_id=t_id, team_name="Updated", target_season=None, notes=None
    )

    assert engine.delete_user_team(t_id) is True
    assert engine.delete_team(t_id) is True
    mock_builder.delete_team.assert_called_with(t_id)

    assert engine.list_user_teams() == ["mock_team"]
    assert engine.list_teams() == ["mock_team"]
    mock_builder.list_teams.assert_called_with(
        limit=100, offset=0, created_by=None, target_season=None
    )

    assert engine.add_player_to_team(t_id, p_id, assigned_role="Pace Bowler") == "mock_player"
    assert engine.add_player(t_id, p_id, assigned_role="Pace Bowler") == "mock_player"
    mock_builder.add_player.assert_called_with(
        team_id=t_id,
        player_id=p_id,
        assigned_role="Pace Bowler",
        batting_order=None,
        is_designated_wk=False,
        is_captain=False,
        allow_oversize=False,
    )

    assert engine.update_player_in_team(t_id, p_id, batting_order=4) == "mock_player"
    assert engine.update_player(t_id, p_id, batting_order=4) == "mock_player"
    mock_builder.update_player.assert_called_with(
        team_id=t_id,
        player_id=p_id,
        assigned_role=None,
        batting_order=4,
        is_designated_wk=None,
        is_captain=None,
    )

    assert engine.remove_player_from_team(t_id, p_id) is True
    assert engine.remove_player(t_id, p_id) is True
    mock_builder.remove_player.assert_called_with(team_id=t_id, player_id=p_id)

    assert engine.get_team_players(t_id) == ["mock_player"]
    mock_builder.get_team_players.assert_called_with(t_id)

    mock_builder.validate_roster.return_value = {
        "roster_status": RosterStatus.ROSTER_VALID,
        "is_valid_ipl_roster": True,
    }
    assert engine.validate_roster(t_id)["roster_status"] == RosterStatus.ROSTER_VALID
    mock_builder.validate_roster.assert_called_with(
        team_id=t_id, player_metadata=None, strict_official=False
    )


def test_sice_engine_create_default_end_to_end_subsystem_integration() -> None:
    """Verify SICEEngine.create_default() performs genuine end-to-end integration across all 5 subsystems."""
    engine = SICEEngine.create_default(default_seed=42)

    # 1. Team Builder CRUD via facade
    team = engine.create_user_team(
        team_name="Rajasthan Royals 2027 Facade Test Squad",
        target_season="IPL 2027",
        created_by="lead_scout",
    )
    assert team.team_id is not None
    assert team.team_name == "Rajasthan Royals 2027 Facade Test Squad"

    # Add players to the team
    player_id1 = uuid4()
    p1 = engine.add_player_to_team(
        team_id=team.team_id,
        player_id=player_id1,
        assigned_role="Top-order Batter",
        batting_order=1,
    )
    assert p1.user_team_id == team.team_id

    player_id2 = uuid4()
    p2 = engine.add_player_to_team(
        team_id=team.team_id,
        player_id=player_id2,
        assigned_role="Wicketkeeper Batter",
        batting_order=2,
        is_designated_wk=True,
    )
    assert p2.is_designated_wk is True

    # Retrieve players via facade
    roster = engine.get_team_players(team.team_id)
    assert len(roster) == 2

    # Validate draft roster status via facade
    validation_res = engine.validate_roster(team.team_id)
    assert validation_res["roster_status"] in (
        RosterStatus.ROSTER_UNDERSIZED,
        RosterStatus.ROSTER_INCOMPLETE,
    )

    # 2. Evaluate squad via facade
    eval_result = engine.evaluate_squad(team.team_id)
    assert isinstance(eval_result, SICEOutputContract)
    assert eval_result.team_id == team.team_id
    assert eval_result.squad_size == 2
    assert eval_result.is_valid_ipl_roster is False

    # 3. Optimize playing XI via facade
    lineups = engine.optimize_playing_xi(team_id=team.team_id)
    assert isinstance(lineups, list)
    assert len(lineups) >= 1
    # Squad size < 11 yields invalid lineup
    assert lineups[0].is_valid_ipl_lineup is False

    # 4. Rank uncapped candidates via facade
    rank_board = engine.rank_uncapped_candidates(
        config_version="RK-1.0.0",
        candidate_pool=[],
        seed=42,
    )
    assert isinstance(rank_board, RankingBoardOutputContract)
    assert rank_board.contract_version == "RK-1.0.0"

    # 5. Replacement evaluation via facade
    incumbent_id = uuid4()
    req = ReplacementComparisonRequest(
        incumbent_player_id=incumbent_id,
        target_season_id=uuid4(),
        evaluation_date=date(2027, 4, 1),
    )
    repl_res = engine.compare_replacement(req)
    assert isinstance(repl_res, ReplacementComparisonOutputContract)
    assert repl_res.incumbent_player_id == incumbent_id

    # 6. Delete team via facade
    deleted = engine.delete_user_team(team.team_id)
    assert deleted is True
    assert engine.get_user_team(team.team_id) is None


# ==============================================================================
# Suite 6: SICE Master Facade Database Guard & Offline Isolation Tests
# ==============================================================================


def test_sice_engine_create_default_database_mode_guard_rejection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify SICEEngine.create_default(mode=DATABASE) triggers DatabaseEnvironmentGuardError when unauthorized."""
    monkeypatch.delenv("SICE_AUTHORIZED_PG16_DB", raising=False)

    engine = SICEEngine.create_default(mode=RepositoryMode.DATABASE)
    assert engine.repository is not None
    assert engine.repository.mode == RepositoryMode.DATABASE

    # Attempting database operations without authorization must be intercepted
    with pytest.raises(DatabaseEnvironmentGuardError) as exc_info:
        engine.repository.begin()
    assert "rejected by PostgreSQL Environment Guard" in str(exc_info.value)
    assert exc_info.value.code == "DATABASE_ENVIRONMENT_GUARD_ERROR"

    with pytest.raises(DatabaseEnvironmentGuardError):
        engine.repository.execute_parameterized("SELECT 1")

    with pytest.raises(DatabaseEnvironmentGuardError):
        engine.repository.commit()

    with pytest.raises(DatabaseEnvironmentGuardError):
        engine.repository.rollback()


def test_sice_engine_create_default_database_mode_with_mock_client() -> None:
    """Verify SICEEngine.create_default(mode=DATABASE, db_client=mock) executes without external PostgreSQL."""
    mock_client = MagicMock()
    mock_client.execute.return_value = True

    engine = SICEEngine.create_default(mode=RepositoryMode.DATABASE, db_client=mock_client)
    assert engine.repository is not None
    assert engine.repository.mode == RepositoryMode.DATABASE

    # Lifecycle methods delegate to the injected db_client
    engine.repository.begin()
    mock_client.begin.assert_called_once()

    test_sql = "SELECT * FROM user_teams WHERE team_id = %s"
    test_params = (str(uuid4()),)
    res = engine.repository.execute_parameterized(test_sql, test_params)
    assert res is True
    mock_client.execute.assert_called_once_with(test_sql, test_params)

    engine.repository.commit()
    mock_client.commit.assert_called_once()


def test_sice_engine_create_default_with_custom_repository() -> None:
    """Verify SICEEngine.create_default(repository=custom) injects repository across all subsystems."""
    custom_repo = SICERepository(mode=RepositoryMode.IN_MEMORY)
    team = custom_repo.save_team(
        UserTeam(team_name="Custom Injected Squad", target_season="IPL 2027")
    )

    engine = SICEEngine.create_default(repository=custom_repo)

    assert engine.repository is custom_repo
    assert engine.team_builder is not None
    assert engine.team_builder.repository is custom_repo
    assert engine.ranking_engine is not None
    assert engine.ranking_engine.repository is custom_repo
    assert engine.composition_engine is not None
    assert engine.composition_engine.repository is custom_repo

    # Facade CRUD operates against custom repository
    retrieved = engine.get_user_team(team.team_id)
    assert retrieved is not None
    assert retrieved.team_name == "Custom Injected Squad"


def test_sice_engine_evaluate_alias() -> None:
    """Verify SICEEngine.evaluate is an authoritative alias producing identical output to evaluate_squad."""
    engine = SICEEngine.create_default(default_seed=42)
    team = engine.create_user_team(
        team_name="Evaluate Alias Test Squad",
        target_season="IPL 2027",
    )

    # 1. Evaluate via canonical evaluate_squad
    squad_res = engine.evaluate_squad(team.team_id)

    # 2. Evaluate via evaluate alias (TRD §8.2 notation)
    alias_res = engine.evaluate(team.team_id)

    assert isinstance(alias_res, SICEOutputContract)
    assert alias_res.team_id == squad_res.team_id
    assert alias_res.squad_size == squad_res.squad_size
    assert alias_res.squad_health_index == squad_res.squad_health_index
    assert alias_res.is_valid_ipl_roster == squad_res.is_valid_ipl_roster
    assert alias_res.contract_version == squad_res.contract_version

    # 3. Test with context dictionary
    context = {"analysis_mode": "DRAFT_EXPLORATION", "match_type": "IPL_T20"}
    alias_with_context = engine.evaluate(team.team_id, context=context)
    assert isinstance(alias_with_context, SICEOutputContract)
    assert alias_with_context.team_id == team.team_id

    # 4. Enforce UUID type check
    with pytest.raises(TypeError, match="team_id must be a UUID instance"):
        engine.evaluate("not-a-uuid")  # type: ignore[arg-type]


def test_sice_engine_disconnected_offline_graceful_handling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify SICEEngine operates fully offline with zero external PostgreSQL or network dependency."""
    monkeypatch.delenv("SICE_AUTHORIZED_PG16_DB", raising=False)

    engine = SICEEngine.create_default(default_seed=99)
    assert engine.repository is not None
    assert engine.repository.mode == RepositoryMode.IN_MEMORY

    # Health check confirms all subsystems ready in offline mode
    health = engine.health_check()
    assert health["status"] == "healthy"
    for subsystem_name, sub_status in health["subsystems"].items():
        assert sub_status == "ready", f"Subsystem {subsystem_name} not ready in offline mode"

    # End-to-end execution across all capabilities without network
    team = engine.create_user_team(team_name="Offline Safe Squad", target_season="IPL 2027")
    p1 = engine.add_player_to_team(
        team_id=team.team_id,
        player_id=uuid4(),
        assigned_role="Top-order Batter",
        batting_order=1,
    )
    assert p1.assigned_role == "Top-order Batter"

    # Evaluate squad
    eval_output = engine.evaluate(team.team_id)
    assert eval_output.team_id == team.team_id
    assert eval_output.squad_size == 1

    # Playing XI optimization
    lineups = engine.optimize_playing_xi(team_id=team.team_id)
    assert isinstance(lineups, list)
    assert len(lineups) >= 1

    # Uncapped candidate ranking
    rank_output = engine.rank_uncapped_candidates(candidate_pool=[], seed=99)
    assert rank_output.contract_version == "RK-1.0.0"

    # Replacement comparison
    req = ReplacementComparisonRequest(
        incumbent_player_id=uuid4(),
        target_season_id=uuid4(),
        evaluation_date=date(2027, 4, 1),
    )
    repl_output = engine.compare_replacement(req)
    assert repl_output.contract_version == "RE-1.0.0"
