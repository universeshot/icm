from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .strategies import WeightedFeatureStrategy


@dataclass(frozen=True)
class StrategyPreset:
    id: str
    description: str
    defaults: dict[str, Any]


WEIGHTED_STRATEGY_PRESETS: dict[str, StrategyPreset] = {
    "balanced_common_per_namespace": StrategyPreset(
        id="balanced_common_per_namespace",
        description=(
            "Per-namespace scoring, compare only common namespaces/features, "
            "balanced for stable deterministic traversal."
        ),
        defaults={
            "feature_namespace_mode": "per_namespace",
            "namespace_presence_mode": "common",
            "feature_presence_mode": "common",
            "theme_weight": 0.20,
            "namespace_weights": {"core": 1.0},
        },
    ),
    "aggregate_common": StrategyPreset(
        id="aggregate_common",
        description=(
            "Aggregate scoring across common namespaces/features only; "
            "useful when you want one collapsed feature surface."
        ),
        defaults={
            "feature_namespace_mode": "aggregate",
            "namespace_presence_mode": "common",
            "feature_presence_mode": "common",
            "theme_weight": 0.20,
            "namespace_weights": {"core": 1.0},
        },
    ),
    "aggregate_all_penalize_missing": StrategyPreset(
        id="aggregate_all_penalize_missing",
        description=(
            "Aggregate scoring over union of namespaces/features, treating missing "
            "feature values as zero to penalize asymmetry."
        ),
        defaults={
            "feature_namespace_mode": "aggregate",
            "namespace_presence_mode": "all",
            "feature_presence_mode": "all",
            "theme_weight": 0.20,
            "namespace_weights": {"core": 1.0},
        },
    ),
    "shape_aware_per_namespace": StrategyPreset(
        id="shape_aware_per_namespace",
        description=(
            "Per-namespace common comparison with additional weight on shape namespace."
        ),
        defaults={
            "feature_namespace_mode": "per_namespace",
            "namespace_presence_mode": "common",
            "feature_presence_mode": "common",
            "theme_weight": 0.20,
            "namespace_weights": {"core": 1.0, "shape": 0.5},
        },
    ),
}


def list_weighted_strategy_presets() -> dict[str, str]:
    return {preset_id: preset.description for preset_id, preset in WEIGHTED_STRATEGY_PRESETS.items()}


def build_weighted_strategy_from_preset(
    preset_id: str,
    strategy_id: str | None = None,
    **overrides: Any,
) -> WeightedFeatureStrategy:
    preset = WEIGHTED_STRATEGY_PRESETS.get(preset_id)
    if preset is None:
        known = ", ".join(sorted(WEIGHTED_STRATEGY_PRESETS.keys()))
        raise ValueError(f"Unknown strategy preset: {preset_id}. Known presets: {known}")

    config = dict(preset.defaults)
    config.update(overrides)
    config["id"] = strategy_id or config.get("id") or preset_id
    return WeightedFeatureStrategy(**config)
