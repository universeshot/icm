from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Cog, CogGraph, Component, LineageOperation, ScoreEntry, ScoreSet, Snapshot


class JsonSnapshotStore:
    @staticmethod
    def save(path: str | Path, snapshot: Snapshot) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        serializable = JsonSnapshotStore._to_serializable(snapshot)
        target.write_text(json.dumps(serializable, indent=2), encoding="utf-8")

    @staticmethod
    def load(path: str | Path) -> Snapshot:
        source = Path(path)
        raw = json.loads(source.read_text(encoding="utf-8"))

        cogs = {cog_id: Cog(**data) for cog_id, data in raw["cogs"].items()}
        components = {cid: Component(**data) for cid, data in raw["components"].items()}
        graphs = {
            graph_id: CogGraph(
                id=data["id"],
                base_cog_id=data["base_cog_id"],
                adjacent_order=list(data["adjacent_order"]),
                layered_order=list(data["layered_order"]),
                hidden_layers=set(data.get("hidden_layers", [])),
                context_hash=data.get("context_hash", "default"),
                version=data.get("version", 1),
            )
            for graph_id, data in raw["graphs"].items()
        }

        score_sets: dict[str, ScoreSet] = {}
        for score_set_id, data in raw["score_sets"].items():
            score_set = ScoreSet(
                id=data["id"],
                strategy_id=data["strategy_id"],
                context_hash=data.get("context_hash", "default"),
                version=data.get("version", 1),
            )
            for entry_data in data.get("entries", []):
                score_set.set(
                    ScoreEntry(
                        from_cog_id=entry_data["from_cog_id"],
                        to_cog_id=entry_data["to_cog_id"],
                        score=entry_data["score"],
                        vector=entry_data.get("vector", {}),
                        variance=entry_data.get("variance", 0.0),
                        strategy_id=entry_data.get("strategy_id", score_set.strategy_id),
                    )
                )
            score_sets[score_set_id] = score_set

        lineage = [
            LineageOperation(
                op_type=item["op_type"],
                inputs=list(item.get("inputs", [])),
                outputs=list(item.get("outputs", [])),
                metadata=item.get("metadata", {}),
            )
            for item in raw.get("lineage", [])
        ]

        return Snapshot(
            id=raw["id"],
            created_at=raw["created_at"],
            meta=raw.get("meta", {}),
            cogs=cogs,
            components=components,
            graphs=graphs,
            score_sets=score_sets,
            lineage=lineage,
        )

    @staticmethod
    def schema() -> dict[str, Any]:
        return {
            "id": "snapshot id",
            "created_at": "ISO-8601 UTC",
            "meta": {"version": "schema/application version", "notes": "optional"},
            "cogs": {"cog_id": {"id": "str", "theme": "str", "scope": "float", "breadth": "float"}},
            "components": {"component_id": {"id": "str", "kind": "str", "payload": "dict"}},
            "graphs": {
                "graph_id": {
                    "id": "str",
                    "base_cog_id": "str",
                    "adjacent_order": ["cog ids"],
                    "layered_order": ["cog ids"],
                    "hidden_layers": ["int layer"],
                    "context_hash": "str",
                }
            },
            "score_sets": {
                "score_set_id": {
                    "id": "str",
                    "strategy_id": "str",
                    "context_hash": "str",
                    "entries": ["ScoreEntry"],
                }
            },
            "lineage": [{"op_type": "str", "inputs": ["id"], "outputs": ["id"], "metadata": {}}],
        }

    @staticmethod
    def _to_serializable(snapshot: Snapshot) -> dict[str, Any]:
        return {
            "id": snapshot.id,
            "created_at": snapshot.created_at,
            "meta": snapshot.meta,
            "cogs": {cog_id: vars(cog) for cog_id, cog in snapshot.cogs.items()},
            "components": {component_id: vars(component) for component_id, component in snapshot.components.items()},
            "graphs": {
                graph_id: {
                    "id": graph.id,
                    "base_cog_id": graph.base_cog_id,
                    "adjacent_order": list(graph.adjacent_order),
                    "layered_order": list(graph.layered_order),
                    "hidden_layers": sorted(graph.hidden_layers),
                    "context_hash": graph.context_hash,
                    "version": graph.version,
                }
                for graph_id, graph in snapshot.graphs.items()
            },
            "score_sets": {
                score_set_id: {
                    "id": score_set.id,
                    "strategy_id": score_set.strategy_id,
                    "context_hash": score_set.context_hash,
                    "version": score_set.version,
                    "entries": [
                        {
                            "from_cog_id": entry.from_cog_id,
                            "to_cog_id": entry.to_cog_id,
                            "score": entry.score,
                            "vector": entry.vector,
                            "variance": entry.variance,
                            "strategy_id": entry.strategy_id,
                        }
                        for entry in score_set.entries.values()
                    ],
                }
                for score_set_id, score_set in snapshot.score_sets.items()
            },
            "lineage": [
                {
                    "op_type": op.op_type,
                    "inputs": op.inputs,
                    "outputs": op.outputs,
                    "metadata": op.metadata,
                }
                for op in snapshot.lineage
            ],
        }
