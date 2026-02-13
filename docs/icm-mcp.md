# ICM MCP Interface

This document defines the MCP-facing interface for the ICM runtime.

## Isolation model

Every MCP call is scoped by:

1. `manager_service`
2. `workspace_id`

The pair maps to an isolated runtime and storage root:

`data/icm/<manager_service>/<workspace_id>/...`

This gives clear ownership boundaries for mixed-use integrations and provides a direct path to future physical isolation (for example, separate containers or cloud services per manager/workspace).

## Runtime structure

Each isolated runtime contains:

1. `CogSystem` (core state and scoring)
2. `IterationEngine` (manual/auto traversal)
3. `AsciiRenderer` (human-readable diagnostics)
4. `active_snapshot_id` (current persisted state marker)

## MCP tool surface

Implemented through:

1. `src/icm/interfaces/mcp_server.py` (official MCP SDK `FastMCP` server)
2. `src/icm/interfaces/mcp_legacy.py` (backend runtime/service handlers reused by MCP tools)

1. `icm.runtime.info`
2. `icm.strategy.presets`
3. `icm.strategy.register_preset`
4. `icm.plugin.register_feature`
5. `icm.snapshot.save`
6. `icm.snapshot.load`
7. `icm.cog.compose`
8. `icm.cog.split`

All tools accept optional scope fields:

1. `manager_service` (default: `icm`)
2. `workspace_id` (default: `default`)

## Plugin registration via MCP

Use `icm.plugin.register_feature` with:

1. `plugin`: module path (e.g., `icm.scoring.sample_feature_plugin`) or file path.
2. `use_as_default`: whether new techniques become default for matching namespace/features.

## Snapshot management via MCP

1. `icm.snapshot.save` persists current runtime state.
2. `icm.snapshot.load` restores runtime state into the active isolated workspace.

For isolation safety, snapshot paths are runtime-relative only (no absolute paths).

## Composition and split via MCP

1. `icm.cog.compose` merges multiple source cogs into a new cog.
2. `icm.cog.split` creates new cogs from one source cog (`words` or `chars` mode).

Optional graph attachment:

1. `graph_id`
2. `bucket` (`adjacent` or `layered`)

## Running the MCP server

Install the official MCP SDK package (`mcp`) and run:

```powershell
$env:PYTHONPATH='src'
python -m icm.interfaces.mcp_server
```
