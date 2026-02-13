from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol

from ..core.models import Cog, ScoreEntry


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


def _weighted_average(pairs: list[tuple[float, float]]) -> float:
    if not pairs:
        return 0.0
    total_weight = sum(weight for _, weight in pairs)
    if total_weight <= 0.0:
        return 0.0
    return sum(value * weight for value, weight in pairs) / total_weight


def _normalize_namespaced_values(cog: Cog) -> dict[str, dict[str, float]]:
    raw = cog.scoring.feature_values
    normalized: dict[str, dict[str, float]] = {}

    if raw:
        raw_values = list(raw.values())
        if raw_values and all(isinstance(item, (int, float)) for item in raw_values):
            normalized["core"] = {feature: float(value) for feature, value in raw.items()}  # type: ignore[arg-type]
        else:
            for namespace, feature_values in raw.items():
                if not isinstance(feature_values, dict):
                    continue
                normalized[namespace] = {
                    feature: float(value) for feature, value in feature_values.items()
                }

    core = normalized.setdefault("core", {})
    core.setdefault("breadth", float(cog.breadth))
    core.setdefault("depth", float(cog.depth))
    core.setdefault("volume", float(cog.volume))
    return normalized


@dataclass
class WeightedFeatureStrategy:
    id: str = "weighted_default"
    theme_weight: float = 0.20
    breadth_weight: float = 1.0
    depth_weight: float = 1.0
    volume_weight: float = 1.0
    feature_namespace_mode: Literal["aggregate", "per_namespace"] = "aggregate"
    namespace_presence_mode: Literal["all", "common"] = "common"
    feature_presence_mode: Literal["all", "common"] = "common"
    namespace_weights: dict[str, float] = field(default_factory=dict)
    feature_weights: dict[str, float] = field(default_factory=dict)
    directional_bias_feature: str = "directional_bias"
    extra_feature_weights: dict[str, float] = field(default_factory=dict)

    def score(self, source: Cog, target: Cog) -> ScoreEntry:
        theme_score = 1.0 if source.theme == target.theme else 0.0
        source_ns = _normalize_namespaced_values(source)
        target_ns = _normalize_namespaced_values(target)
        namespace_ids = self._selected_namespaces(source_ns, target_ns)

        vector: dict[str, float] = {"theme_match": theme_score}
        namespace_scores: list[tuple[float, float]] = []
        aggregate_pairs: list[tuple[float, float]] = []
        feature_similarities: list[float] = []

        for namespace in namespace_ids:
            left = source_ns.get(namespace, {})
            right = target_ns.get(namespace, {})
            feature_ids = self._selected_features(left, right)
            feature_pairs: list[tuple[float, float]] = []
            for feature_name in feature_ids:
                left_value = float(left.get(feature_name, 0.0))
                right_value = float(right.get(feature_name, 0.0))
                similarity = _relative_similarity(left_value, right_value)
                feature_key = f"{namespace}.{feature_name}"
                vector[f"feature:{feature_key}"] = similarity
                feature_similarities.append(similarity)
                weight = self._feature_weight(namespace, feature_name)
                feature_pairs.append((similarity, weight))
                namespace_weight = self.namespace_weights.get(namespace, 1.0)
                aggregate_pairs.append((similarity, weight * namespace_weight))

            namespace_score = _weighted_average(feature_pairs)
            vector[f"namespace:{namespace}"] = namespace_score
            namespace_weight = self.namespace_weights.get(namespace, 1.0)
            namespace_scores.append((namespace_score, namespace_weight))

        if self.feature_namespace_mode == "per_namespace":
            feature_score = _weighted_average(namespace_scores)
        else:
            feature_score = _weighted_average(aggregate_pairs)

        # Legacy explicit core weights remain available for core comparisons.
        core_breadth = vector.get("feature:core.breadth", _relative_similarity(source.breadth, target.breadth))
        core_depth = vector.get("feature:core.depth", _relative_similarity(source.depth, target.depth))
        core_volume = vector.get("feature:core.volume", _relative_similarity(source.volume, target.volume))
        vector["breadth_similarity"] = core_breadth
        vector["depth_similarity"] = core_depth
        vector["volume_similarity"] = core_volume

        base_score = (
            self.theme_weight * theme_score
            + ((1.0 - self.theme_weight) * feature_score)
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
        variance = 0.0
        if feature_similarities:
            variance = max(feature_similarities) - min(feature_similarities)

        return ScoreEntry(
            from_cog_id=source.id,
            to_cog_id=target.id,
            score=final_score,
            vector=vector,
            variance=variance,
            strategy_id=self.id,
        )

    def _selected_namespaces(
        self,
        source_values: dict[str, dict[str, float]],
        target_values: dict[str, dict[str, float]],
    ) -> list[str]:
        source_namespaces = set(source_values.keys())
        target_namespaces = set(target_values.keys())
        if self.namespace_presence_mode == "common":
            selected = source_namespaces.intersection(target_namespaces)
        else:
            selected = source_namespaces.union(target_namespaces)
        return sorted(selected)

    def _selected_features(
        self,
        source_features: dict[str, float],
        target_features: dict[str, float],
    ) -> list[str]:
        source_names = set(source_features.keys())
        target_names = set(target_features.keys())
        if self.feature_presence_mode == "common":
            selected = source_names.intersection(target_names)
        else:
            selected = source_names.union(target_names)
        return sorted(selected)

    def _feature_weight(self, namespace: str, feature_name: str) -> float:
        namespaced_key = f"{namespace}.{feature_name}"
        if namespaced_key in self.feature_weights:
            return self.feature_weights[namespaced_key]
        if namespace == "core":
            if feature_name == "breadth":
                return self.breadth_weight
            if feature_name == "depth":
                return self.depth_weight
            if feature_name == "volume":
                return self.volume_weight
        return self.feature_weights.get(feature_name, 1.0)
