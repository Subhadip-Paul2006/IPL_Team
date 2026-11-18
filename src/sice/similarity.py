"""Squad Intelligence & Composition Engine (SICE) — Similarity and Distance Models.

Provides mathematical similarity metrics and subspace distance routines for
player profile comparison:
- Tactical Cosine Similarity (directional alignment of performance and phase vectors)
- Gower Similarity Coefficient (mixed-data distance for continuous and categorical attributes)
- Subspace Weighted Euclidean Distance with Completeness Penalty Factor
- Regularized Mahalanobis Distance with Covariance Shrinkage (alpha = 0.20)
- Tactical Phase Deployment Similarity

Governing Specifications:
- reports/phase6-execution/PHASE6_SICE_READINESS_REPORT.md §7.3
- docs/DATA_DICTIONARY.md §10.3 & §11
- docs/TRD.md §8.3 & §8.4
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class AttributeSpec:
    """Specification of an attribute for mixed-type Gower similarity evaluation."""

    attr_type: str = "continuous"  # "continuous" | "categorical"
    weight: float = 1.0
    val_range: float | None = None  # R_k = max_k - min_k
    min_val: float | None = None
    max_val: float | None = None


DEFAULT_CRICKET_SPECS: dict[str, AttributeSpec] = {
    "strike_rate": AttributeSpec(
        attr_type="continuous", weight=1.5, val_range=180.0, min_val=60.0, max_val=240.0
    ),
    "batting_average": AttributeSpec(
        attr_type="continuous", weight=1.2, val_range=60.0, min_val=5.0, max_val=65.0
    ),
    "boundary_pct": AttributeSpec(
        attr_type="continuous", weight=1.0, val_range=40.0, min_val=0.0, max_val=40.0
    ),
    "dot_ball_pct": AttributeSpec(
        attr_type="continuous", weight=1.0, val_range=60.0, min_val=15.0, max_val=75.0
    ),
    "economy_rate": AttributeSpec(
        attr_type="continuous", weight=1.5, val_range=8.5, min_val=4.5, max_val=13.0
    ),
    "bowling_strike_rate": AttributeSpec(
        attr_type="continuous", weight=1.2, val_range=31.0, min_val=9.0, max_val=40.0
    ),
    "age": AttributeSpec(
        attr_type="continuous", weight=0.8, val_range=24.0, min_val=18.0, max_val=42.0
    ),
    "primary_role": AttributeSpec(attr_type="categorical", weight=1.5),
    "batting_hand": AttributeSpec(attr_type="categorical", weight=0.6),
    "bowling_style": AttributeSpec(attr_type="categorical", weight=1.0),
}


class SubspaceDistanceResult(tuple):
    """Result tuple of subspace weighted Euclidean distance calculation.

    Behaves as a 2-tuple (distance, similarity) while providing explicit attributes:
    - distance: penalized distance
    - similarity: mapped similarity in [0.0, 1.0]
    - penalty: completeness penalty factor
    """

    distance: float | None
    similarity: float
    penalty: float

    def __new__(
        cls,
        distance: float | None,
        similarity: float,
        penalty: float = 1.0,
    ) -> SubspaceDistanceResult:
        instance = super().__new__(cls, (distance, similarity))
        instance.distance = distance
        instance.similarity = similarity
        instance.penalty = penalty
        return instance


def cosine_similarity(
    vec1: Sequence[float | None] | dict[str, float | None],
    vec2: Sequence[float | None] | dict[str, float | None],
    keys: list[str] | None = None,
) -> float | None:
    """Calculate tactical cosine similarity between two numeric vectors.

    Supports both list and dict inputs with dynamic missing-value filtering.
    Enforces strict [0.0, 1.0] bounds and graceful handling of zero vectors.

    Args:
        vec1: First vector (list of floats/None or dict of floats/None).
        vec2: Second vector (list of floats/None or dict of floats/None).
        keys: Optional list of keys to extract when dicts are supplied.

    Returns:
        Cosine similarity in [0.0, 1.0], or 0.0 for zero vectors, or None if no overlap.

    Raises:
        ValueError: If list vector lengths do not match or values are NaN/Inf.
    """
    u_vals: list[float] = []
    v_vals: list[float] = []

    if isinstance(vec1, dict) and isinstance(vec2, dict):
        eval_keys = keys if keys is not None else [k for k in vec1 if k in vec2]
        if not eval_keys:
            return 0.0
        for k in eval_keys:
            u = vec1.get(k)
            v = vec2.get(k)
            if u is not None and v is not None:
                if math.isnan(u) or math.isnan(v) or math.isinf(u) or math.isinf(v):
                    raise ValueError(f"NaN or Inf encountered in vector key '{k}'")
                u_vals.append(float(u))
                v_vals.append(float(v))
    elif isinstance(vec1, (list, tuple)) and isinstance(vec2, (list, tuple)):
        if len(vec1) != len(vec2):
            raise ValueError(
                f"Vector dimensions must match: len(vec1)={len(vec1)} != len(vec2)={len(vec2)}"
            )
        for u, v in zip(vec1, vec2, strict=True):
            if u is not None and v is not None:
                if math.isnan(u) or math.isnan(v) or math.isinf(u) or math.isinf(v):
                    raise ValueError("NaN or Inf encountered in vector elements")
                u_vals.append(float(u))
                v_vals.append(float(v))
    else:
        raise TypeError(
            f"Unsupported vector types: {type(vec1).__name__} and {type(vec2).__name__}"
        )

    if not u_vals:
        return 0.0

    dot_product = sum(u * v for u, v in zip(u_vals, v_vals, strict=True))
    norm_u = math.sqrt(sum(u * u for u in u_vals))
    norm_v = math.sqrt(sum(v * v for v in v_vals))

    if norm_u <= 1e-9 or norm_v <= 1e-9:
        return 0.0

    cos_sim = dot_product / (norm_u * norm_v)
    return max(0.0, min(1.0, float(cos_sim)))


def gower_similarity(
    p1_attrs: dict[str, Any],
    p2_attrs: dict[str, Any],
    attribute_specs: dict[str, Any] | None = None,
) -> float | None:
    """Calculate Gower similarity coefficient over mixed continuous & categorical profiles.

    Missing values (None) are dynamically excluded from both numerator and denominator
    (delta_k = 0). Continuous attributes are normalized by domain range R_k.

    Args:
        p1_attrs: First entity's attributes.
        p2_attrs: Second entity's attributes.
        attribute_specs: Optional dictionary of AttributeSpec objects or ranges.

    Returns:
        Similarity score in [0.0, 1.0], or 0.0 if no valid overlapping attributes.
    """
    specs = attribute_specs or DEFAULT_CRICKET_SPECS
    all_keys = set(p1_attrs.keys()) | set(p2_attrs.keys())

    numerator = 0.0
    denominator = 0.0

    for k in all_keys:
        val1 = p1_attrs.get(k)
        val2 = p2_attrs.get(k)

        if val1 is None or val2 is None:
            continue

        spec_entry = specs.get(k)
        weight = 1.0
        val_range: float | None = None
        is_categorical = False

        if isinstance(spec_entry, AttributeSpec):
            weight = spec_entry.weight
            val_range = spec_entry.val_range
            is_categorical = spec_entry.attr_type == "categorical"
        elif isinstance(spec_entry, (int, float)):
            val_range = float(spec_entry)
        elif isinstance(val1, str) or isinstance(val2, str) or isinstance(val1, bool):
            is_categorical = True

        if is_categorical:
            sim_k = 1.0 if str(val1).strip().lower() == str(val2).strip().lower() else 0.0
        else:
            diff = abs(float(val1) - float(val2))
            if val_range is not None and val_range > 1e-9:
                sim_k = max(0.0, 1.0 - (diff / val_range))
            else:
                sim_k = 1.0 if diff <= 1e-9 else 0.0

        numerator += weight * sim_k
        denominator += weight

    if denominator <= 1e-9:
        return 0.0

    return max(0.0, min(1.0, float(numerator / denominator)))


def subspace_weighted_euclidean_distance(
    vec1: Mapping[str, float | None],
    vec2: Mapping[str, float | None],
    weights: Mapping[str, float] | None = None,
    std_devs: Mapping[str, float] | None = None,
    total_dimensions: int | None = None,
) -> SubspaceDistanceResult:
    """Calculate subspace weighted Euclidean distance with completeness penalty.

    When fewer dimensions than total_dimensions are mutually observed, a penalty
    factor (1 + 0.5 * (1 - |S|/d)) scales the distance.

    Args:
        vec1: First feature dictionary.
        vec2: Second feature dictionary.
        weights: Dimension weights.
        std_devs: Optional dimension standard deviations for z-score scaling.
        total_dimensions: Total dimension count d in full representation.

    Returns:
        SubspaceDistanceResult (penalized_distance, mapped_similarity).
    """
    valid_keys = [
        k for k in vec1 if k in vec2 and vec1.get(k) is not None and vec2.get(k) is not None
    ]

    s_size = len(valid_keys)
    w_map = weights or {}
    d = (
        total_dimensions
        if total_dimensions is not None
        else max(len(w_map), len(vec1), len(vec2), 1)
    )

    if s_size == 0:
        return SubspaceDistanceResult(None, 0.0, penalty=1.0)

    sum_weights = 0.0
    sum_weighted_sq_diff = 0.0

    for k in valid_keys:
        u = float(vec1[k])  # type: ignore[arg-type]
        v = float(vec2[k])  # type: ignore[arg-type]
        w = float(w_map.get(k, 1.0))
        sigma = float(std_devs.get(k, 1.0)) if std_devs and k in std_devs else 1.0
        if sigma <= 1e-9:
            sigma = 1.0

        diff = (u - v) / sigma
        sum_weighted_sq_diff += w * (diff**2)
        sum_weights += w

    if sum_weights <= 1e-9:
        return SubspaceDistanceResult(None, 0.0, penalty=1.0)

    base_dist = math.sqrt(sum_weighted_sq_diff / sum_weights)

    completeness_ratio = min(1.0, s_size / float(d)) if d > 0 else 1.0
    penalty = 1.0 + 0.5 * (1.0 - completeness_ratio)
    penalized_dist = base_dist * penalty
    similarity = 1.0 / (1.0 + penalized_dist)

    return SubspaceDistanceResult(penalized_dist, similarity, penalty)


def tactical_phase_similarity(
    p1_phase_balls: dict[str, int],
    p2_phase_balls: dict[str, int],
) -> float | None:
    """Calculate tactical phase deployment similarity using cosine alignment.

    Args:
        p1_phase_balls: Balls bowled/faced across phases ("powerplay", "middle", "death").
        p2_phase_balls: Second player's balls across phases.

    Returns:
        Cosine similarity in [0.0, 1.0].
    """
    phases = ["powerplay", "middle", "death"]
    v1 = [float(p1_phase_balls.get(p, 0)) for p in phases]
    v2 = [float(p2_phase_balls.get(p, 0)) for p in phases]
    return cosine_similarity(v1, v2)


def regularized_mahalanobis_distance(
    u: np.ndarray | list[float],
    v: np.ndarray | list[float],
    cov_matrix: np.ndarray | list[list[float]],
    alpha: float = 0.20,
) -> float:
    """Calculate regularized Mahalanobis distance with covariance shrinkage.

    Covariance is regularized via Ledoit-Wolf style shrinkage:
    Sigma_reg = (1 - alpha) * Sigma + alpha * diag(Sigma).

    Args:
        u: First vector.
        v: Second vector.
        cov_matrix: Covariance matrix.
        alpha: Shrinkage intensity in [0.0, 1.0].

    Returns:
        Regularized Mahalanobis distance >= 0.0.
    """
    arr_u = np.asarray(u, dtype=float)
    arr_v = np.asarray(v, dtype=float)
    cov = np.asarray(cov_matrix, dtype=float)

    if arr_u.shape != arr_v.shape:
        raise ValueError(
            f"Vector shapes must match: arr_u.shape={arr_u.shape} != arr_v.shape={arr_v.shape}"
        )
    if cov.shape != (arr_u.shape[0], arr_u.shape[0]):
        raise ValueError(
            f"Covariance shape {cov.shape} must match vector length ({arr_u.shape[0]}, {arr_u.shape[0]})"
        )

    diag_cov = np.diag(np.diag(cov))
    cov_reg = (1.0 - alpha) * cov + alpha * diag_cov

    try:
        inv_cov = np.linalg.pinv(cov_reg)
    except np.linalg.LinAlgError:
        inv_cov = np.eye(arr_u.shape[0])

    diff = arr_u - arr_v
    sq_dist = float(diff @ inv_cov @ diff)
    return float(math.sqrt(max(0.0, sq_dist)))


class SimilarityCalculator:
    """Service class encapsulating similarity and distance routines."""

    def __init__(self, specs: dict[str, AttributeSpec] | None = None) -> None:
        self.specs = specs or DEFAULT_CRICKET_SPECS

    def compute_cosine(
        self,
        v1: Sequence[float | None] | dict[str, float | None],
        v2: Sequence[float | None] | dict[str, float | None],
        keys: list[str] | None = None,
    ) -> float | None:
        return cosine_similarity(v1, v2, keys=keys)

    def compute_gower(
        self,
        p1: dict[str, Any],
        p2: dict[str, Any],
        specs: dict[str, Any] | None = None,
    ) -> float | None:
        return gower_similarity(p1, p2, attribute_specs=specs or self.specs)

    def compute_subspace_euclidean(
        self,
        v1: Mapping[str, float | None],
        v2: Mapping[str, float | None],
        weights: Mapping[str, float] | None = None,
        std_devs: Mapping[str, float] | None = None,
        total_dimensions: int | None = None,
    ) -> SubspaceDistanceResult:
        return subspace_weighted_euclidean_distance(
            v1, v2, weights=weights, std_devs=std_devs, total_dimensions=total_dimensions
        )

    def compute_tactical_phase(
        self,
        p1_phase: dict[str, int],
        p2_phase: dict[str, int],
    ) -> float | None:
        return tactical_phase_similarity(p1_phase, p2_phase)

    def compute_all_similarities(
        self,
        incumbent_profile: dict[str, Any],
        candidate_profile: dict[str, Any],
    ) -> dict[str, float]:
        """Compute aggregate similarity metrics dictionary for replacement contracts."""
        scores: dict[str, float] = {}

        # Gower mixed similarity
        gower_sim = self.compute_gower(incumbent_profile, candidate_profile)
        if gower_sim is not None:
            scores["gower_similarity"] = round(gower_sim, 4)

        # Tactical phase similarity if available
        inc_phase = incumbent_profile.get("phase_balls")
        cand_phase = candidate_profile.get("phase_balls")
        if isinstance(inc_phase, dict) and isinstance(cand_phase, dict):
            phase_sim = self.compute_tactical_phase(inc_phase, cand_phase)
            if phase_sim is not None:
                scores["tactical_phase_similarity"] = round(phase_sim, 4)

        # Euclidean similarity over continuous metrics
        cont_keys = [
            "strike_rate",
            "batting_average",
            "boundary_pct",
            "economy_rate",
            "bowling_strike_rate",
        ]
        v1 = {k: incumbent_profile.get(k) for k in cont_keys if k in incumbent_profile}
        v2 = {k: candidate_profile.get(k) for k in cont_keys if k in candidate_profile}
        if v1 and v2:
            res = self.compute_subspace_euclidean(v1, v2, total_dimensions=len(cont_keys))
            if res.distance is not None:
                scores["euclidean_similarity"] = round(res.similarity, 4)

        return scores
