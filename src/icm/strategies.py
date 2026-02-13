from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .models import Cog, ScoreEntry


class SimilarityStrategy(Protocol):
    id: str

    def score(self, source: Cog, target: Cog) -> ScoreEntry:
        ...


def _clamp_01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _relative_similarity(left: float, right: float) -> float:
    denom = max(abs(left), abs(right), 1.0)
    return _clamp_01(1.0 - (abs(left - right) / denom))


@dataclass
class WeightedFeatureStrategy:
    id: str = "weighted_default"
    theme_weight: float = 0.20
    breadth_weight: float = 0.30
    depth_weight: float = 0.25
    volume_weight: float = 0.25
    directional_bias_feature: str = "directional_bias"
    extra_feature_weights: dict[str, float] = field(default_factory=dict)

    def score(self, source: Cog, target: Cog) -> ScoreEntry:
        theme_score = 1.0 if source.theme == target.theme else 0.0
        breadth_score = _relative_similarity(source.breadth, target.breadth)
        depth_score = _relative_similarity(source.depth, target.depth)
        volume_score = _relative_similarity(source.volume, target.volume)

        vector: dict[str, float] = {
            "theme_match": theme_score,
            "breadth_similarity": breadth_score,
            "depth_similarity": depth_score,
            "volume_similarity": volume_score,
        }

        base_score = (
            self.theme_weight * theme_score
            + self.breadth_weight * breadth_score
            + self.depth_weight * depth_score
            + self.volume_weight * volume_score
        )

        weighted_extra = 0.0
        total_extra_weight = 0.0
        for feature, weight in self.extra_feature_weights.items():
            total_extra_weight += weight
            source_val = source.features.get(feature, 0.0)
            target_val = target.features.get(feature, 0.0)
            similarity = _clamp_01(1.0 - abs(source_val - target_val))
            vector[f"feature:{feature}"] = similarity
            weighted_extra += weight * similarity

        if total_extra_weight > 0:
            base_score = (base_score + weighted_extra) / (1.0 + total_extra_weight)

        source_bias = source.features.get(self.directional_bias_feature, 0.0)
        target_bias = target.features.get(self.directional_bias_feature, 0.0)
        directional_adjustment = (source_bias - target_bias) * 0.05
        vector["directional_adjustment"] = directional_adjustment

        final_score = _clamp_01(base_score + directional_adjustment)
        low = min(breadth_score, depth_score, volume_score)
        high = max(breadth_score, depth_score, volume_score)
        variance = high - low

        return ScoreEntry(
            from_cog_id=source.id,
            to_cog_id=target.id,
            score=final_score,
            vector=vector,
            variance=variance,
            strategy_id=self.id,
        )
