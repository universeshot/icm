from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ..core.iteration import IterationEngine
from ..core.models import Cog, CogScoring, LineageOperation
from ..core.render import AsciiRenderer
from ..core.store import JsonSnapshotStore
from ..core.system import CogSystem


@dataclass(frozen=True)
class InteractionScope:
    manager_service: str = "icm"
    workspace_id: str = "default"

    @property
    def key(self) -> str:
        return f"{self.manager_service}:{self.workspace_id}"


@dataclass
class WorkspaceRuntime:
    scope: InteractionScope
    storage_root: Path
    system: CogSystem = field(default_factory=CogSystem)
    engine: IterationEngine = field(init=False)
    renderer: AsciiRenderer = field(init=False)
    active_snapshot_id: str | None = None

    def __post_init__(self) -> None:
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.engine = IterationEngine(self.system)
        self.renderer = AsciiRenderer(self.system)
        self.system.register_default_word_feature_techniques()


class ICMRuntimeRegistry:
    def __init__(self, data_root: str | Path = "data/icm") -> None:
        self.data_root = Path(data_root)
        self._runtimes: dict[str, WorkspaceRuntime] = {}

    def get_runtime(self, scope: InteractionScope) -> WorkspaceRuntime:
        cached = self._runtimes.get(scope.key)
        if cached is not None:
            return cached

        runtime = WorkspaceRuntime(
            scope=scope,
            storage_root=self.data_root / scope.manager_service / scope.workspace_id,
        )
        self._runtimes[scope.key] = runtime
        return runtime

    def known_scopes(self) -> list[dict[str, str]]:
        return [
            {"manager_service": runtime.scope.manager_service, "workspace_id": runtime.scope.workspace_id}
            for runtime in self._runtimes.values()
        ]


@dataclass(frozen=True)
class MCPToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]


class ICMMCPServer:
    def __init__(self, registry: ICMRuntimeRegistry | None = None) -> None:
        self.registry = registry or ICMRuntimeRegistry()
        self._handlers: dict[str, Callable[[WorkspaceRuntime, dict[str, Any]], dict[str, Any]]] = {
            "icm.runtime.info": self._tool_runtime_info,
            "icm.strategy.presets": self._tool_strategy_presets,
            "icm.strategy.register_preset": self._tool_register_strategy_preset,
            "icm.plugin.register_feature": self._tool_register_feature_plugin,
            "icm.snapshot.save": self._tool_snapshot_save,
            "icm.snapshot.load": self._tool_snapshot_load,
            "icm.cog.compose": self._tool_cog_compose,
            "icm.cog.split": self._tool_cog_split,
        }
        self._tool_specs: list[MCPToolSpec] = [
            MCPToolSpec(
                name="icm.runtime.info",
                description="Get runtime ownership, storage root, and high-level counts.",
                input_schema={"type": "object", "properties": {}},
            ),
            MCPToolSpec(
                name="icm.strategy.presets",
                description="List available weighted strategy presets.",
                input_schema={"type": "object", "properties": {}},
            ),
            MCPToolSpec(
                name="icm.strategy.register_preset",
                description="Register a weighted strategy from a preset.",
                input_schema={
                    "type": "object",
                    "required": ["preset_id", "strategy_id"],
                    "properties": {
                        "preset_id": {"type": "string"},
                        "strategy_id": {"type": "string"},
                        "overrides": {"type": "object"},
                    },
                },
            ),
            MCPToolSpec(
                name="icm.plugin.register_feature",
                description="Register feature techniques from a plugin module/path.",
                input_schema={
                    "type": "object",
                    "required": ["plugin"],
                    "properties": {
                        "plugin": {"type": "string"},
                        "use_as_default": {"type": "boolean"},
                    },
                },
            ),
            MCPToolSpec(
                name="icm.snapshot.save",
                description="Persist the current runtime state to an isolated snapshot path.",
                input_schema={
                    "type": "object",
                    "required": ["snapshot_id"],
                    "properties": {
                        "snapshot_id": {"type": "string"},
                        "path": {"type": "string"},
                        "meta": {"type": "object"},
                    },
                },
            ),
            MCPToolSpec(
                name="icm.snapshot.load",
                description="Load a snapshot file into the current runtime.",
                input_schema={
                    "type": "object",
                    "required": ["path"],
                    "properties": {"path": {"type": "string"}, "reset_policies": {"type": "boolean"}},
                },
            ),
            MCPToolSpec(
                name="icm.cog.compose",
                description="Compose multiple cogs into a new cog.",
                input_schema={
                    "type": "object",
                    "required": ["cog_ids", "new_cog_id"],
                    "properties": {
                        "cog_ids": {"type": "array", "items": {"type": "string"}},
                        "new_cog_id": {"type": "string"},
                        "theme": {"type": "string"},
                        "graph_id": {"type": "string"},
                        "bucket": {"type": "string", "enum": ["adjacent", "layered"]},
                    },
                },
            ),
            MCPToolSpec(
                name="icm.cog.split",
                description="Split one cog into new cogs (word/char split).",
                input_schema={
                    "type": "object",
                    "required": ["cog_id"],
                    "properties": {
                        "cog_id": {"type": "string"},
                        "mode": {"type": "string", "enum": ["words", "chars"]},
                        "new_cog_prefix": {"type": "string"},
                        "max_items": {"type": "integer"},
                        "graph_id": {"type": "string"},
                        "bucket": {"type": "string", "enum": ["adjacent", "layered"]},
                    },
                },
            ),
        ]

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": spec.name, "description": spec.description, "input_schema": spec.input_schema}
            for spec in self._tool_specs
        ]

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(arguments or {})
        scope = InteractionScope(
            manager_service=str(payload.pop("manager_service", "icm")),
            workspace_id=str(payload.pop("workspace_id", "default")),
        )
        runtime = self.registry.get_runtime(scope)
        handler = self._handlers.get(name)
        if handler is None:
            known = ", ".join(sorted(self._handlers.keys()))
            raise ValueError(f"Unknown MCP tool: {name}. Known tools: {known}")
        return handler(runtime, payload)

    def _tool_runtime_info(self, runtime: WorkspaceRuntime, _: dict[str, Any]) -> dict[str, Any]:
        return {
            "manager_service": runtime.scope.manager_service,
            "workspace_id": runtime.scope.workspace_id,
            "storage_root": str(runtime.storage_root),
            "active_snapshot_id": runtime.active_snapshot_id,
            "counts": {
                "cogs": len(runtime.system.cogs),
                "components": len(runtime.system.components),
                "graphs": len(runtime.system.graphs),
                "score_sets": len(runtime.system.score_sets),
                "strategies": len(runtime.system.strategies),
                "feature_techniques": len(runtime.system.feature_techniques),
            },
        }

    @staticmethod
    def _tool_strategy_presets(runtime: WorkspaceRuntime, _: dict[str, Any]) -> dict[str, Any]:
        return {"presets": runtime.system.available_strategy_presets()}

    @staticmethod
    def _tool_register_strategy_preset(runtime: WorkspaceRuntime, payload: dict[str, Any]) -> dict[str, Any]:
        preset_id = str(payload["preset_id"])
        strategy_id = str(payload["strategy_id"])
        overrides = dict(payload.get("overrides", {}))
        strategy = runtime.system.register_weighted_strategy_preset(
            preset_id=preset_id,
            strategy_id=strategy_id,
            **overrides,
        )
        return {"strategy_id": strategy.id, "preset_id": preset_id}

    @staticmethod
    def _tool_register_feature_plugin(runtime: WorkspaceRuntime, payload: dict[str, Any]) -> dict[str, Any]:
        plugin = str(payload["plugin"])
        use_as_default = bool(payload.get("use_as_default", False))
        ids = runtime.system.load_feature_plugin(plugin, use_as_default=use_as_default)
        return {"plugin": plugin, "registered_technique_ids": ids, "use_as_default": use_as_default}

    def _tool_snapshot_save(self, runtime: WorkspaceRuntime, payload: dict[str, Any]) -> dict[str, Any]:
        snapshot_id = str(payload["snapshot_id"])
        path = str(payload.get("path", f"snapshots/{snapshot_id}.json"))
        meta = dict(payload.get("meta", {}))
        snapshot = runtime.system.snapshot(snapshot_id=snapshot_id, meta=meta)
        target = self._resolve_runtime_path(runtime, path)
        JsonSnapshotStore.save(target, snapshot)
        runtime.active_snapshot_id = snapshot.id
        return {"snapshot_id": snapshot.id, "path": str(target)}

    def _tool_snapshot_load(self, runtime: WorkspaceRuntime, payload: dict[str, Any]) -> dict[str, Any]:
        path = str(payload["path"])
        reset_policies = bool(payload.get("reset_policies", True))
        source = self._resolve_runtime_path(runtime, path)
        snapshot = JsonSnapshotStore.load(source)
        runtime.system.load_snapshot(snapshot, reset_policies=reset_policies)
        runtime.active_snapshot_id = snapshot.id
        return {
            "snapshot_id": snapshot.id,
            "path": str(source),
            "counts": {
                "cogs": len(runtime.system.cogs),
                "components": len(runtime.system.components),
                "graphs": len(runtime.system.graphs),
                "score_sets": len(runtime.system.score_sets),
            },
        }

    def _tool_cog_compose(self, runtime: WorkspaceRuntime, payload: dict[str, Any]) -> dict[str, Any]:
        cog_ids = [str(item) for item in payload["cog_ids"]]
        if len(cog_ids) < 2:
            raise ValueError("cog_ids must contain at least two ids for composition.")

        missing = [cog_id for cog_id in cog_ids if cog_id not in runtime.system.cogs]
        if missing:
            raise ValueError(f"Unknown cog ids for composition: {missing}")

        new_cog_id = str(payload["new_cog_id"])
        if new_cog_id in runtime.system.cogs:
            raise ValueError(f"New cog id already exists: {new_cog_id}")

        source_cogs = [runtime.system.cogs[cog_id] for cog_id in cog_ids]
        unique_themes: list[str] = []
        for cog in source_cogs:
            if cog.theme not in unique_themes:
                unique_themes.append(cog.theme)
        theme = str(payload.get("theme", " + ".join(unique_themes)))
        content = " ".join([cog.content for cog in source_cogs if cog.content.strip()])
        if not content:
            content = " ".join(unique_themes)

        component_ids: list[str] = []
        for cog in source_cogs:
            for component_id in cog.component_ids:
                if component_id not in component_ids:
                    component_ids.append(component_id)

        directional_bias_values = [float(cog.features.get("directional_bias", 0.0)) for cog in source_cogs]
        directional_bias = sum(directional_bias_values) / max(len(directional_bias_values), 1)
        inherited_techniques = deepcopy(source_cogs[0].scoring.feature_techniques)

        new_cog = Cog(
            id=new_cog_id,
            theme=theme,
            breadth=0.0,
            depth=0.0,
            volume=0.0,
            content=content,
            component_ids=component_ids,
            features={"directional_bias": directional_bias},
            scoring=CogScoring(feature_techniques=inherited_techniques),
        )
        runtime.system.add_cog(new_cog)
        self._attach_to_graph_if_requested(runtime, new_cog_id, payload)

        runtime.system.lineage.append(
            LineageOperation(
                op_type="compose",
                inputs=cog_ids,
                outputs=[new_cog_id],
                metadata={
                    "manager_service": runtime.scope.manager_service,
                    "workspace_id": runtime.scope.workspace_id,
                },
            )
        )

        return {
            "new_cog_id": new_cog_id,
            "source_cog_ids": cog_ids,
            "theme": theme,
            "component_count": len(component_ids),
        }

    def _tool_cog_split(self, runtime: WorkspaceRuntime, payload: dict[str, Any]) -> dict[str, Any]:
        source_cog_id = str(payload["cog_id"])
        source = runtime.system.cogs.get(source_cog_id)
        if source is None:
            raise ValueError(f"Unknown cog id: {source_cog_id}")

        mode = str(payload.get("mode", "words"))
        prefix = str(payload.get("new_cog_prefix", f"{source_cog_id}_split"))
        max_items = payload.get("max_items")
        max_count = int(max_items) if max_items is not None else None

        if mode == "words":
            tokens = re.findall(r"[A-Za-z]+", source.content or source.theme)
        elif mode == "chars":
            tokens = [char for char in (source.content or source.theme) if char.isalpha()]
        else:
            raise ValueError(f"Unsupported split mode: {mode}")

        if max_count is not None:
            tokens = tokens[:max_count]
        if not tokens:
            raise ValueError("No split tokens were produced from source cog.")

        created_ids: list[str] = []
        for index, token in enumerate(tokens, start=1):
            new_cog_id = f"{prefix}_{index}"
            if new_cog_id in runtime.system.cogs:
                raise ValueError(f"Split target id already exists: {new_cog_id}")

            child = Cog(
                id=new_cog_id,
                theme=source.theme,
                breadth=0.0,
                depth=0.0,
                volume=0.0,
                content=token,
                component_ids=[],
                features={"directional_bias": float(source.features.get("directional_bias", 0.0))},
                scoring=CogScoring(feature_techniques=deepcopy(source.scoring.feature_techniques)),
            )
            runtime.system.add_cog(child)
            self._attach_to_graph_if_requested(runtime, new_cog_id, payload)
            created_ids.append(new_cog_id)

        runtime.system.lineage.append(
            LineageOperation(
                op_type="split",
                inputs=[source_cog_id],
                outputs=created_ids,
                metadata={
                    "mode": mode,
                    "manager_service": runtime.scope.manager_service,
                    "workspace_id": runtime.scope.workspace_id,
                },
            )
        )

        return {
            "source_cog_id": source_cog_id,
            "mode": mode,
            "created_cog_ids": created_ids,
        }

    @staticmethod
    def _attach_to_graph_if_requested(
        runtime: WorkspaceRuntime,
        cog_id: str,
        payload: dict[str, Any],
    ) -> None:
        graph_id = payload.get("graph_id")
        if graph_id is None:
            return
        graph_id = str(graph_id)
        graph = runtime.system.graphs.get(graph_id)
        if graph is None:
            raise ValueError(f"Unknown graph id: {graph_id}")

        bucket = str(payload.get("bucket", "layered"))
        if bucket not in {"adjacent", "layered"}:
            raise ValueError("bucket must be either 'adjacent' or 'layered'.")

        if cog_id == graph.base_cog_id:
            return
        if cog_id in graph.adjacent_order:
            graph.adjacent_order.remove(cog_id)
        if cog_id in graph.layered_order:
            graph.layered_order.remove(cog_id)

        if bucket == "adjacent":
            graph.adjacent_order.append(cog_id)
        else:
            graph.layered_order.append(cog_id)
        graph.version += 1

    @staticmethod
    def _resolve_runtime_path(runtime: WorkspaceRuntime, user_path: str) -> Path:
        raw = Path(user_path)
        if raw.is_absolute():
            raise ValueError("Absolute paths are not allowed for isolated MCP snapshot operations.")

        resolved = (runtime.storage_root / raw).resolve()
        root = runtime.storage_root.resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError("Snapshot path escapes runtime storage root.") from exc
        return resolved
