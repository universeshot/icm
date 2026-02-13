# Cogs System (Phase 1)

Phase 1 focuses on:

1. Extendable data structure (`Cog`, `Component`, `CogGraph`, `ScoreSet`).
2. Namespace-aware per-cog feature scoring (`namespace -> feature -> technique/value`).
3. Pluggable per-cog feature techniques (`breadth`, `depth`, `volume`, and future features).
4. Namespace comparison toggles in similarity scoring.
5. Event/subscription-based score recomputation.
6. Manual and automated iteration mechanics.
7. ASCII rendering and JSON snapshot persistence.

Phase 1 intentionally does not implement automatic composition/decomposition yet.

## Module map

- `src/icm/models.py`: core entities and snapshots.
- `src/icm/events.py`: event bus.
- `src/icm/strategies.py`: pluggable similarity strategies.
- `src/icm/scoring.py`: pluggable per-feature calculation techniques.
- `src/icm/plugins.py`: simple plugin loader for feature techniques.
- `src/icm/sample_feature_plugin.py`: example plugin module.
- `src/icm/system.py`: orchestration, score-set lifecycle, policy binding.
- `src/icm/index.py`: pre-sorted neighbor index for traversal.
- `src/icm/policy.py`: deterministic path policy.
- `src/icm/iteration.py`: manual and automated iteration engine.
- `src/icm/render.py`: ASCII visual representation.
- `src/icm/store.py`: JSON snapshot store.
- `src/icm/example.py`: concrete runnable sample.

## Iteration capabilities

Manual:

1. Reorder graph against a score set (`run_manual_reorder`).
2. Swap adjacent/layered partitions (`run_manual_swap`).
3. Rebase and reorder (`run_manual_set_base`).
4. Build deterministic chains with seen-overlay (`build_chain`).

Automated:

1. Reorder + chain build loop (`run_auto`).
2. Optional base advancement between iterations.

## Event-driven updates

`CogSystem` subscribes to `cog.updated` and `scores.updated`:

1. Cog update recomputes affected score rows/columns for every compatible score set.
2. Cog update recomputes feature values from configured per-cog techniques.
3. Score-set update invalidates cached neighbor indexes.
4. If a graph is bound to a policy via `bind_graph_policy`, score updates auto-trigger graph reorder.

## Namespace scoring toggles

`WeightedFeatureStrategy` supports:

1. `feature_namespace_mode`:
   - `aggregate`: compare all selected features together.
   - `per_namespace`: compute per-namespace scores, then aggregate namespaces.
2. `namespace_presence_mode`:
   - `common`: only namespaces that both cogs expose.
   - `all`: union of namespaces, with missing features treated as zero.
3. `feature_presence_mode`:
   - `common`: only shared feature names within selected namespaces.
   - `all`: union of feature names within selected namespaces.

## Strategy presets

Preset helpers are available for `WeightedFeatureStrategy`:

1. `balanced_common_per_namespace`
2. `aggregate_common`
3. `aggregate_all_penalize_missing`
4. `shape_aware_per_namespace`

Register from a preset:

```python
system.register_weighted_strategy_preset(
    preset_id="shape_aware_per_namespace",
    strategy_id="X",
)
```

List available presets:

```python
print(system.available_strategy_presets())
```

## Plugin loader

Load plugin-provided feature techniques with:

```python
system.load_feature_plugin("icm.sample_feature_plugin", use_as_default=False)
# Or by file path:
system.load_feature_plugin("src/icm/sample_feature_plugin.py", use_as_default=False)
```

Supported plugin contracts:

1. `register_feature_techniques()` returning list/set/tuple/dict values of technique objects.
2. `FEATURE_TECHNIQUES` variable containing list/set/tuple/dict values.

## Quick start

```powershell
$env:PYTHONPATH='src'
$env:PYTHONDONTWRITEBYTECODE='1'
python -m icm.example
```

The example prints:

1. Graph view with layers and components.
2. Similarity view.
3. Traversal chain.
4. Event-driven reorder after a cog update.
5. Snapshot output at `docs/snapshots/demo-1.json`.
