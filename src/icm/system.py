from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from typing import Any

from .events import Event, EventBus
from .index import NeighborIndex
from .models import Cog, CogGraph, Component, LineageOperation, ScoreEntry, ScoreSet, Snapshot
from .policy import PathPolicy
from .strategies import SimilarityStrategy


class CogSystem:
    def __init__(self) -> None:
        self.event_bus = EventBus()
        self.components: dict[str, Component] = {}
        self.cogs: dict[str, Cog] = {}
        self.graphs: dict[str, CogGraph] = {}
        self.score_sets: dict[str, ScoreSet] = {}
        self.strategies: dict[str, SimilarityStrategy] = {}
        self.graph_policies: dict[str, PathPolicy] = {}
        self._neighbor_indexes: dict[tuple[str, str], NeighborIndex] = {}
        self.lineage: list[LineageOperation] = []
        self.event_bus.subscribe("cog.updated", self._on_cog_updated)
        self.event_bus.subscribe("scores.updated", self._on_scores_updated)

    def register_strategy(self, strategy: SimilarityStrategy) -> None:
        self.strategies[strategy.id] = strategy

    def add_component(self, component: Component) -> None:
        self.components[component.id] = component

    def add_cog(self, cog: Cog) -> None:
        self.cogs[cog.id] = cog
        self.event_bus.publish(Event(topic="cog.updated", payload={"cog_id": cog.id}))

    def update_cog(self, cog_id: str, **updates: Any) -> Cog:
        cog = self.cogs[cog_id]
        for key, value in updates.items():
            if not hasattr(cog, key):
                raise ValueError(f"Unsupported cog field: {key}")
            setattr(cog, key, value)
        cog.version += 1
        self.event_bus.publish(
            Event(topic="cog.updated", payload={"cog_id": cog.id, "version": cog.version})
        )
        return cog

    def add_graph(self, graph: CogGraph) -> None:
        all_ids = set(graph.ordered_ids)
        missing = [cog_id for cog_id in all_ids if cog_id not in self.cogs]
        if missing:
            raise ValueError(f"Graph references unknown cogs: {missing}")
        self.graphs[graph.id] = graph

    def bind_graph_policy(self, graph_id: str, policy: PathPolicy) -> None:
        if graph_id not in self.graphs:
            raise ValueError(f"Unknown graph: {graph_id}")
        if policy.score_set_id not in self.score_sets:
            raise ValueError(f"Unknown score set: {policy.score_set_id}")
        self.graph_policies[graph_id] = policy

    def create_score_set(
        self,
        score_set_id: str,
        strategy_id: str,
        context_hash: str = "default",
        cog_ids: list[str] | None = None,
    ) -> ScoreSet:
        if strategy_id not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy_id}")

        strategy = self.strategies[strategy_id]
        ids = cog_ids if cog_ids is not None else list(self.cogs.keys())
        score_set = ScoreSet(id=score_set_id, strategy_id=strategy_id, context_hash=context_hash)

        for from_cog_id in ids:
            for to_cog_id in ids:
                if from_cog_id == to_cog_id:
                    continue
                entry = strategy.score(self.cogs[from_cog_id], self.cogs[to_cog_id])
                score_set.set(
                    ScoreEntry(
                        from_cog_id=entry.from_cog_id,
                        to_cog_id=entry.to_cog_id,
                        score=entry.score,
                        vector=entry.vector,
                        variance=entry.variance,
                        strategy_id=strategy_id,
                    )
                )

        self.score_sets[score_set_id] = score_set
        self._neighbor_indexes.pop((score_set_id, "directed"), None)
        self._neighbor_indexes.pop((score_set_id, "symmetrized"), None)
        return score_set

    def _on_cog_updated(self, event: Event) -> None:
        cog_id = event.payload.get("cog_id")
        if cog_id is None:
            return

        for score_set in self.score_sets.values():
            if score_set.strategy_id not in self.strategies:
                continue
            strategy = self.strategies[score_set.strategy_id]
            ids = list(self.cogs.keys())
            for other_id in ids:
                if other_id == cog_id:
                    continue
                out_entry = strategy.score(self.cogs[cog_id], self.cogs[other_id])
                in_entry = strategy.score(self.cogs[other_id], self.cogs[cog_id])
                score_set.set(out_entry)
                score_set.set(in_entry)
            score_set.version += 1
            self._neighbor_indexes.pop((score_set.id, "directed"), None)
            self._neighbor_indexes.pop((score_set.id, "symmetrized"), None)
            self.event_bus.publish(
                Event(
                    topic="scores.updated",
                    payload={"score_set_id": score_set.id, "source_cog_id": cog_id},
                )
            )

    def _on_scores_updated(self, event: Event) -> None:
        score_set_id = event.payload.get("score_set_id")
        if score_set_id is None:
            return
        for graph_id, policy in self.graph_policies.items():
            if policy.score_set_id != score_set_id:
                continue
            self.reorder_graph(graph_id=graph_id, policy=policy)

    def neighbor_index(self, score_set_id: str, direction_mode: str) -> NeighborIndex:
        key = (score_set_id, direction_mode)
        cached = self._neighbor_indexes.get(key)
        if cached is not None:
            return cached
        if score_set_id not in self.score_sets:
            raise ValueError(f"Unknown score set: {score_set_id}")
        index = NeighborIndex(self.score_sets[score_set_id], direction_mode=direction_mode)
        self._neighbor_indexes[key] = index
        return index

    def reorder_graph(self, graph_id: str, policy: PathPolicy) -> CogGraph:
        graph = self.graphs[graph_id]
        index = self.neighbor_index(policy.score_set_id, policy.direction_mode)

        adjacent_scores = {
            cog_id: self._score_or_neg_inf(index, graph.base_cog_id, cog_id)
            for cog_id in graph.adjacent_order
        }
        layered_scores = {
            cog_id: self._score_or_neg_inf(index, graph.base_cog_id, cog_id)
            for cog_id in graph.layered_order
        }

        graph.adjacent_order.sort(key=lambda cog_id: (-adjacent_scores[cog_id], cog_id))
        graph.layered_order.sort(key=lambda cog_id: (-layered_scores[cog_id], cog_id))
        graph.version += 1

        self.lineage.append(
            LineageOperation(
                op_type="reorder",
                inputs=[graph.base_cog_id],
                outputs=graph.ordered_ids,
                metadata={
                    "graph_id": graph.id,
                    "score_set_id": policy.score_set_id,
                    "direction_mode": policy.direction_mode,
                },
            )
        )
        return graph

    def swap_adjacent_layered(self, graph_id: str) -> CogGraph:
        graph = self.graphs[graph_id]
        graph.adjacent_order, graph.layered_order = graph.layered_order, graph.adjacent_order
        graph.version += 1
        self.lineage.append(
            LineageOperation(
                op_type="swap_adjacent_layered",
                inputs=[],
                outputs=graph.ordered_ids,
                metadata={"graph_id": graph.id},
            )
        )
        return graph

    def set_graph_base(self, graph_id: str, new_base_cog_id: str) -> CogGraph:
        graph = self.graphs[graph_id]
        if new_base_cog_id not in graph.ordered_ids:
            raise ValueError(f"Base cog must already be in graph order: {new_base_cog_id}")

        all_ids = [cog_id for cog_id in graph.ordered_ids if cog_id != new_base_cog_id]
        graph.base_cog_id = new_base_cog_id
        split = len(graph.adjacent_order)
        graph.adjacent_order = all_ids[:split]
        graph.layered_order = all_ids[split:]
        graph.version += 1
        self.lineage.append(
            LineageOperation(
                op_type="set_base",
                inputs=[new_base_cog_id],
                outputs=graph.ordered_ids,
                metadata={"graph_id": graph.id},
            )
        )
        return graph

    def set_hidden_layers(self, graph_id: str, hidden_layers: set[int]) -> CogGraph:
        graph = self.graphs[graph_id]
        graph.hidden_layers = set(hidden_layers)
        graph.version += 1
        self.lineage.append(
            LineageOperation(
                op_type="set_hidden_layers",
                inputs=[],
                outputs=graph.ordered_ids,
                metadata={"graph_id": graph.id, "hidden_layers": sorted(hidden_layers)},
            )
        )
        return graph

    def snapshot(self, snapshot_id: str, meta: dict[str, Any] | None = None) -> Snapshot:
        return Snapshot(
            id=snapshot_id,
            meta=meta or {},
            cogs=deepcopy(self.cogs),
            components=deepcopy(self.components),
            graphs=deepcopy(self.graphs),
            score_sets=deepcopy(self.score_sets),
            lineage=deepcopy(self.lineage),
        )

    @staticmethod
    def snapshot_to_dict(snapshot: Snapshot) -> dict[str, Any]:
        return asdict(snapshot)

    @staticmethod
    def _score_or_neg_inf(index: NeighborIndex, from_cog_id: str, to_cog_id: str) -> float:
        for neighbor in index.neighbors(from_cog_id):
            if neighbor.to_cog_id == to_cog_id:
                return neighbor.score
        return float("-inf")
