from __future__ import annotations

from dataclasses import dataclass

from .models import ScoreEntry, ScoreSet


@dataclass(frozen=True)
class Neighbor:
    to_cog_id: str
    score: float
    variance: float
    strategy_id: str


class NeighborIndex:
    def __init__(self, score_set: ScoreSet, direction_mode: str = "directed") -> None:
        self.score_set_id = score_set.id
        self.direction_mode = direction_mode
        self.by_from: dict[str, list[Neighbor]] = {}
        if direction_mode == "directed":
            self._build_directed(score_set)
        elif direction_mode == "symmetrized":
            self._build_symmetrized(score_set)
        else:
            raise ValueError(f"Unsupported direction mode: {direction_mode}")

    def _build_directed(self, score_set: ScoreSet) -> None:
        by_from: dict[str, list[Neighbor]] = {}
        for entry in score_set.entries.values():
            by_from.setdefault(entry.from_cog_id, []).append(
                Neighbor(
                    to_cog_id=entry.to_cog_id,
                    score=entry.score,
                    variance=entry.variance,
                    strategy_id=entry.strategy_id,
                )
            )
        self.by_from = by_from
        self._sort_all()

    def _build_symmetrized(self, score_set: ScoreSet) -> None:
        pair_scores: dict[tuple[str, str], tuple[float, float, str]] = {}
        ids: set[str] = set()
        for entry in score_set.entries.values():
            ids.add(entry.from_cog_id)
            ids.add(entry.to_cog_id)
            pair = tuple(sorted((entry.from_cog_id, entry.to_cog_id)))
            current = pair_scores.get(pair)
            if current is None:
                pair_scores[pair] = (entry.score, entry.variance, entry.strategy_id)
            else:
                avg_score = (current[0] + entry.score) / 2.0
                avg_variance = (current[1] + entry.variance) / 2.0
                pair_scores[pair] = (avg_score, avg_variance, entry.strategy_id)

        by_from: dict[str, list[Neighbor]] = {cog_id: [] for cog_id in ids}
        for (left, right), (score, variance, strategy_id) in pair_scores.items():
            by_from.setdefault(left, []).append(
                Neighbor(to_cog_id=right, score=score, variance=variance, strategy_id=strategy_id)
            )
            by_from.setdefault(right, []).append(
                Neighbor(to_cog_id=left, score=score, variance=variance, strategy_id=strategy_id)
            )

        self.by_from = by_from
        self._sort_all()

    def _sort_all(self) -> None:
        for from_cog_id in self.by_from:
            self.by_from[from_cog_id].sort(key=lambda item: (-item.score, item.variance, item.to_cog_id))

    def neighbors(self, from_cog_id: str) -> list[Neighbor]:
        return list(self.by_from.get(from_cog_id, []))

    def top_unseen(
        self,
        from_cog_id: str,
        seen: set[str],
        min_score: float | None = None,
        allowed: set[str] | None = None,
    ) -> Neighbor | None:
        for neighbor in self.by_from.get(from_cog_id, []):
            if neighbor.to_cog_id in seen:
                continue
            if allowed is not None and neighbor.to_cog_id not in allowed:
                continue
            if min_score is not None and neighbor.score < min_score:
                continue
            return neighbor
        return None

    def range_group(
        self,
        from_cog_id: str,
        max_range: float,
        seen: set[str],
        min_score: float | None = None,
        allowed: set[str] | None = None,
    ) -> list[Neighbor]:
        items = self.by_from.get(from_cog_id, [])
        baseline: float | None = None
        grouped: list[Neighbor] = []
        for neighbor in items:
            if neighbor.to_cog_id in seen:
                continue
            if allowed is not None and neighbor.to_cog_id not in allowed:
                continue
            if min_score is not None and neighbor.score < min_score:
                continue
            if baseline is None:
                baseline = neighbor.score
            if abs(baseline - neighbor.score) <= max_range:
                grouped.append(neighbor)
            else:
                break
        return grouped

    @staticmethod
    def from_score_entries(
        score_set_id: str,
        strategy_id: str,
        entries: list[ScoreEntry],
        direction_mode: str = "directed",
    ) -> "NeighborIndex":
        score_set = ScoreSet(id=score_set_id, strategy_id=strategy_id)
        for entry in entries:
            score_set.set(entry)
        return NeighborIndex(score_set=score_set, direction_mode=direction_mode)
