# Cogs System (Phase 1)

Phase 1 focuses on:

1. Extendable data structure (`Cog`, `Component`, `CogGraph`, `ScoreSet`).
2. Event/subscription-based score recomputation.
3. Manual and automated iteration mechanics.
4. ASCII rendering and JSON snapshot persistence.

Phase 1 intentionally does not implement automatic composition/decomposition yet.

## Module map

- `src/icm/models.py`: core entities and snapshots.
- `src/icm/events.py`: event bus.
- `src/icm/strategies.py`: pluggable similarity strategies.
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
2. Score-set update invalidates cached neighbor indexes.
3. If a graph is bound to a policy via `bind_graph_policy`, score updates auto-trigger graph reorder.

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
