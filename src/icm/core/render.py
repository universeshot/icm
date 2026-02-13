from __future__ import annotations

from .iteration import IterationResult
from .models import CogGraph
from .system import CogSystem


class AsciiRenderer:
    def __init__(self, system: CogSystem) -> None:
        self.system = system

    def render_graph(self, graph_id: str, show_components: bool = True) -> str:
        graph = self.system.graphs[graph_id]
        nodes = graph.node_map()

        lines: list[str] = []
        lines.append(f"CogGraph {graph.id}")
        lines.append(f"  Base: {graph.base_cog_id}")
        lines.append(f"  Hidden layers: {sorted(graph.hidden_layers)}")
        lines.append("")

        for cog_id in graph.ordered_ids:
            node = nodes[cog_id]
            cog = self.system.cogs[cog_id]
            marker = "B" if node.role == "base" else ("A" if node.role == "adjacent" else "L")
            lines.append(
                f"[{marker}] Layer {node.layer:02d} | Cog {cog_id} | theme={cog.theme} "
                f"breadth={cog.breadth:.3f} depth={cog.depth:.3f} volume={cog.volume:.3f}"
            )
            if show_components:
                for component_id in cog.component_ids:
                    component = self.system.components.get(component_id)
                    if component is None:
                        lines.append(f"      - {component_id} (missing)")
                    else:
                        lines.append(f"      - {component.id} ({component.kind})")
        return "\n".join(lines)

    def render_similarity(self, graph_id: str, score_set_id: str, direction_mode: str = "directed") -> str:
        graph: CogGraph = self.system.graphs[graph_id]
        index = self.system.neighbor_index(score_set_id=score_set_id, direction_mode=direction_mode)

        lines: list[str] = []
        lines.append(f"Similarity view score_set={score_set_id} mode={direction_mode}")
        for from_cog_id in graph.ordered_ids:
            neighbors = index.neighbors(from_cog_id)
            formatted = ", ".join([f"{n.to_cog_id}:{n.score:.3f}" for n in neighbors])
            lines.append(f"  {from_cog_id} -> [{formatted}]")
        return "\n".join(lines)

    def render_chain(self, result: IterationResult) -> str:
        if not result.chain:
            return f"Iteration result graph={result.graph_id}: <empty chain>"
        return f"Iteration result graph={result.graph_id}: " + " -> ".join(result.chain)
