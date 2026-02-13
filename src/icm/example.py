#!/usr/bin/env python3
from __future__ import annotations

from .iteration import IterationEngine
from .models import Cog, CogGraph, CogScoring, Component
from .policy import PathPolicy
from .render import AsciiRenderer
from .store import JsonSnapshotStore
from .system import CogSystem


def build_demo_system() -> CogSystem:
    system = CogSystem()
    system.register_weighted_strategy_preset(
        preset_id="shape_aware_per_namespace",
        strategy_id="X",
    )
    system.register_default_word_feature_techniques()
    system.load_feature_plugin("icm.sample_feature_plugin", use_as_default=False)

    system.add_component(Component(id="cA1", kind="rule"))
    system.add_component(Component(id="cA2", kind="data"))
    system.add_component(Component(id="cB1", kind="model"))
    system.add_component(Component(id="cC1", kind="rule"))

    system.add_cog(
        Cog(
            id="A",
            theme="Payments",
            breadth=0.0,
            depth=0.0,
            volume=0.0,
            content="payments",
            component_ids=["cA1", "cA2"],
            features={"directional_bias": 0.10},
            scoring=CogScoring(
                feature_techniques={
                    "core": {
                        "breadth": "alpha_polar_breadth",
                        "depth": "letter_depth",
                        "volume": "letter_volume",
                    },
                    "shape": {
                        "unique_letters": "shape_unique_letters",
                        "vowel_ratio": "shape_vowel_ratio",
                    },
                }
            ),
        )
    )
    system.add_cog(
        Cog(
            id="B",
            theme="Settlement",
            breadth=0.0,
            depth=0.0,
            volume=0.0,
            content="settlement",
            component_ids=["cB1"],
            features={"directional_bias": 0.00},
            scoring=CogScoring(
                feature_techniques={
                    "core": {
                        "breadth": "alpha_polar_breadth",
                        "depth": "letter_depth",
                        "volume": "letter_volume",
                    },
                    "shape": {
                        "unique_letters": "shape_unique_letters",
                        "vowel_ratio": "shape_vowel_ratio",
                    },
                }
            ),
        )
    )
    system.add_cog(
        Cog(
            id="C",
            theme="Invoicing",
            breadth=0.0,
            depth=0.0,
            volume=0.0,
            content="invoicing",
            component_ids=["cC1"],
            features={"directional_bias": -0.05},
            scoring=CogScoring(
                feature_techniques={
                    "core": {
                        "breadth": "alpha_polar_breadth",
                        "depth": "letter_depth",
                        "volume": "letter_volume",
                    },
                }
            ),
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

    system.update_cog("C", content="invoicing pipeline")
    print("After updating Cog C content (event-driven feature recompute + reorder):")
    print(renderer.render_graph("G1"))

    snapshot = system.snapshot(snapshot_id="demo-1", meta={"purpose": "iteration baseline"})
    JsonSnapshotStore.save("docs/snapshots/demo-1.json", snapshot)


if __name__ == "__main__":
    run_demo()
