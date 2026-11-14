"""CPPAE (Complete Player Performance Analytics Engine) package (TRD §6)."""

from src.cppae.batting_engine import BattingEngine
from src.cppae.batting_performance import BatterPressureMetrics, BattingPerformanceEngine
from src.cppae.bowling_engine import BowlingEngine
from src.cppae.bowling_performance import BowlerPressureMetrics, BowlingPerformanceEngine
from src.cppae.calibration import (
    BootstrapResult,
    RolePrior,
    StatisticalCalibrationEngine,
)
from src.cppae.engine import CPPAEEngine
from src.cppae.fielding_engine import FieldingEngine
from src.cppae.match_contribution import MatchContributionEngine
from src.cppae.persistence import FeatureStorePublisher, OfflineFeatureStoreAdapter

__all__ = [
    # Facade
    "CPPAEEngine",
    # Specialist workstream engines
    "BattingEngine",
    "BowlingEngine",
    "FieldingEngine",
    "MatchContributionEngine",
    "StatisticalCalibrationEngine",
    "FeatureStorePublisher",
    "OfflineFeatureStoreAdapter",
    # Legacy & performance engines
    "BattingPerformanceEngine",
    "BatterPressureMetrics",
    "BowlingPerformanceEngine",
    "BowlerPressureMetrics",
    # Calibration dataclasses
    "RolePrior",
    "BootstrapResult",
]
