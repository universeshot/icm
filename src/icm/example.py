#!/usr/bin/env python3
from __future__ import annotations

from .iteration import IterationEngine
from .models import Cog, CogGraph, Component
from .policy import PathPolicy
from .render import AsciiRenderer
from .store import JsonSnapshotStore
from .strategies import WeightedFeatureStrategy
from .system import CogSystem


def build_demo_system() -> CogSystem:
    system = CogSystem()
    system.register_strategy(WeightedFeatureStrategy(id="X"))

    system.add_component(Component(id="cA1", kind="rule"))
    system.add_component(Component(id="cA2", kind="data"))
    system.add_component(Component(id="cB1", kind="model"))
    system.add_component(Component(id="cC1", kind="rule"))

    system.add_cog(
        Cog(
            id="A",
            theme="Payments",
            scope=0.80,
            breadth=0.70,
            component_ids=["cA1", "cA2"],
            features={"directional_bias": 0.10},
        )
    )
    system.add_cog(
        Cog(
            id="B",
            theme="Settlement",
            scope=0.78,
            breadth=0.69,
            component_ids=["cB1"],
            features={"directional_bias": 0.00},
        )
    )
    system.add_cog(
        Cog(
            id="C",
            theme="Invoicing",
            scope=0.55,
            breadth=0.40,
            component_ids=["cC1"],
            features={"directional_bias": -0.05},
        )
    )

    system.add_graph(
        CogGraph(
            id="G1",
            base_cog_id="A",
            adjacent_order=["B"],
            layered_order=["C"],
        )
    )
    system.create_score_set(score_set_id="SS-X", strategy_id="X")
    return system


def run_demo() -> None:
    system = build_demo_system()
    engine = IterationEngine(system)
    renderer = AsciiRenderer(system)

    policy = PathPolicy(
        strategy_id="X",
        score_set_id="SS-X",
        direction_mode="directed",
        group_range=0.10,
        max_depth=4,
    )
    system.bind_graph_policy(graph_id="G1", policy=policy)

    engine.run_manual_reorder(graph_id="G1", policy=policy)
    print(renderer.render_graph("G1"))
    print()
    print(renderer.render_similarity(graph_id="G1", score_set_id="SS-X"))
    print()
    result = engine.build_chain(graph_id="G1", policy=policy)
    print(renderer.render_chain(result))
    print("Grouped neighbors:", result.grouped_neighbors)
    print()

    system.update_cog("C", scope=0.79, breadth=0.71)
    print("After updating Cog C (event-driven recompute + reorder):")
    print(renderer.render_graph("G1"))

    snapshot = system.snapshot(snapshot_id="demo-1", meta={"purpose": "iteration baseline"})
    JsonSnapshotStore.save("docs/snapshots/demo-1.json", snapshot)


if __name__ == "__main__":
    run_demo()
