from __future__ import annotations

from dataclasses import dataclass, field

from .index import Neighbor
from .policy import PathPolicy
from .system import CogSystem


@dataclass
class IterationResult:
    graph_id: str
    chain: list[str]
    grouped_neighbors: dict[str, list[str]] = field(default_factory=dict)
    metadata: dict[str, str] = field(default_factory=dict)


class IterationEngine:
    def __init__(self, system: CogSystem) -> None:
        self.system = system

    def build_chain(
        self,
        graph_id: str,
        policy: PathPolicy,
        start_cog_id: str | None = None,
        initial_seen: set[str] | None = None,
    ) -> IterationResult:
        graph = self.system.graphs[graph_id]
        index = self.system.neighbor_index(policy.score_set_id, policy.direction_mode)

        start_id = start_cog_id or graph.base_cog_id
        allowed = self._allowed_nodes(graph_id, policy)
        seen = set(initial_seen or set())
        chain: list[str] = []
        grouped: dict[str, list[str]] = {}

        if start_id in allowed:
            chain.append(start_id)
            seen.add(start_id)

        current = start_id
        depth = 1
        while True:
            if policy.max_depth is not None and depth >= policy.max_depth:
                break

            if policy.group_range is not None:
                group = index.range_group(
                    from_cog_id=current,
                    max_range=policy.group_range,
                    seen=seen if policy.unseen_only else set(),
                    min_score=policy.min_score,
                    allowed=allowed,
                )
                if not group:
                    break
                selected = group[0]
                grouped[current] = [item.to_cog_id for item in group]
            else:
                selected = index.top_unseen(
                    from_cog_id=current,
                    seen=seen if policy.unseen_only else set(),
                    min_score=policy.min_score,
                    allowed=allowed,
                )
                if selected is None:
                    break

            chain.append(selected.to_cog_id)
            seen.add(selected.to_cog_id)
            current = selected.to_cog_id
            depth += 1

        return IterationResult(graph_id=graph_id, chain=chain, grouped_neighbors=grouped)

    def run_manual_reorder(self, graph_id: str, policy: PathPolicy) -> None:
        self.system.reorder_graph(graph_id=graph_id, policy=policy)

    def run_manual_swap(self, graph_id: str) -> None:
        self.system.swap_adjacent_layered(graph_id=graph_id)

    def run_manual_set_base(self, graph_id: str, new_base_cog_id: str, policy: PathPolicy) -> None:
        self.system.set_graph_base(graph_id=graph_id, new_base_cog_id=new_base_cog_id)
        self.system.reorder_graph(graph_id=graph_id, policy=policy)

    def run_auto(
        self,
        graph_id: str,
        policy: PathPolicy,
        iterations: int = 1,
        advance_base: bool = False,
    ) -> list[IterationResult]:
        results: list[IterationResult] = []
        for step in range(iterations):
            self.system.reorder_graph(graph_id=graph_id, policy=policy)
            result = self.build_chain(graph_id=graph_id, policy=policy)
            result.metadata["iteration"] = str(step + 1)
            results.append(result)

            if advance_base and len(result.chain) > 1:
                next_base = result.chain[1]
                self.system.set_graph_base(graph_id=graph_id, new_base_cog_id=next_base)

        return results

    def equivalent_group(
        self,
        from_cog_id: str,
        policy: PathPolicy,
        seen: set[str] | None = None,
        allowed: set[str] | None = None,
    ) -> list[Neighbor]:
        index = self.system.neighbor_index(policy.score_set_id, policy.direction_mode)
        baseline = index.top_unseen(
            from_cog_id=from_cog_id,
            seen=seen or set(),
            min_score=policy.min_score,
            allowed=allowed,
        )
        if baseline is None:
            return []

        epsilon = policy.equivalence_epsilon
        group: list[Neighbor] = []
        for neighbor in index.neighbors(from_cog_id):
            if seen and neighbor.to_cog_id in seen:
                continue
            if allowed is not None and neighbor.to_cog_id not in allowed:
                continue
            if policy.min_score is not None and neighbor.score < policy.min_score:
                continue
            if abs(baseline.score - neighbor.score) <= epsilon:
                group.append(neighbor)
            else:
                break
        return group

    def _allowed_nodes(self, graph_id: str, policy: PathPolicy) -> set[str]:
        graph = self.system.graphs[graph_id]
        nodes = graph.node_map()
        if policy.include_hidden_layers:
            return set(nodes.keys())
        return {cog_id for cog_id, node in nodes.items() if node.layer not in graph.hidden_layers}
