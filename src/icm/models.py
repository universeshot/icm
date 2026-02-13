from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Component:
    id: str
    kind: str
    payload: dict[str, Any] = field(default_factory=dict)
    feature_values: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    version: int = 1


@dataclass
class Cog:
    id: str
    theme: str
    breadth: float
    depth: float
    volume: float
    content: str = ""
    component_ids: list[str] = field(default_factory=list)
    features: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    scoring: "CogScoring" = field(default_factory=lambda: CogScoring())
    version: int = 1


@dataclass
class CogScoring:
    feature_techniques: dict[str, str] = field(default_factory=dict)
    feature_values: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    version: int = 1


@dataclass
class GraphNode:
    cog_id: str
    layer: int
    role: Literal["base", "adjacent", "layered"]


@dataclass
class CogGraph:
    id: str
    base_cog_id: str
    adjacent_order: list[str] = field(default_factory=list)
    layered_order: list[str] = field(default_factory=list)
    hidden_layers: set[int] = field(default_factory=set)
    context_hash: str = "default"
    version: int = 1

    @property
    def ordered_ids(self) -> list[str]:
        return [self.base_cog_id, *self.adjacent_order, *self.layered_order]

    def node_map(self) -> dict[str, GraphNode]:
        nodes: dict[str, GraphNode] = {
            self.base_cog_id: GraphNode(cog_id=self.base_cog_id, layer=0, role="base")
        }

        layer = 1
        for cog_id in self.adjacent_order:
            nodes[cog_id] = GraphNode(cog_id=cog_id, layer=layer, role="adjacent")
            layer += 1

        for cog_id in self.layered_order:
            nodes[cog_id] = GraphNode(cog_id=cog_id, layer=layer, role="layered")
            layer += 1

        return nodes


@dataclass(frozen=True)
class ScoreEntry:
    from_cog_id: str
    to_cog_id: str
    score: float
    vector: dict[str, float] = field(default_factory=dict)
    variance: float = 0.0
    strategy_id: str = "default"


@dataclass
class ScoreSet:
    id: str
    strategy_id: str
    context_hash: str = "default"
    version: int = 1
    entries: dict[tuple[str, str], ScoreEntry] = field(default_factory=dict)

    def set(self, entry: ScoreEntry) -> None:
        self.entries[(entry.from_cog_id, entry.to_cog_id)] = entry

    def get(self, from_cog_id: str, to_cog_id: str) -> ScoreEntry | None:
        return self.entries.get((from_cog_id, to_cog_id))

    def neighbors(self, from_cog_id: str) -> list[ScoreEntry]:
        result = [entry for (src, _), entry in self.entries.items() if src == from_cog_id]
        result.sort(key=lambda item: (-item.score, item.variance, item.to_cog_id))
        return result


@dataclass
class LineageOperation:
    op_type: str
    inputs: list[str]
    outputs: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Snapshot:
    id: str
    created_at: str = field(default_factory=utc_now_iso)
    meta: dict[str, Any] = field(default_factory=dict)
    cogs: dict[str, Cog] = field(default_factory=dict)
    components: dict[str, Component] = field(default_factory=dict)
    graphs: dict[str, CogGraph] = field(default_factory=dict)
    score_sets: dict[str, ScoreSet] = field(default_factory=dict)
    lineage: list[LineageOperation] = field(default_factory=list)
