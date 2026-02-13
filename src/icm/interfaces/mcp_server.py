from __future__ import annotations

from typing import Any

from .mcp_legacy import ICMRuntimeRegistry, ICMMCPServer

try:
    from mcp.server.fastmcp import FastMCP
except Exception:  # pragma: no cover - optional dependency
    FastMCP = None  # type: ignore[assignment]


def build_mcp_server(
    name: str = "ICM",
    registry: ICMRuntimeRegistry | None = None,
) -> Any:
    if FastMCP is None:
        raise RuntimeError(
            "The official MCP SDK is not installed. Install package 'mcp' to run the MCP server."
        )

    backend = ICMMCPServer(registry=registry)
    server = FastMCP(name)

    @server.tool(name="icm.runtime.info")
    def runtime_info(
        manager_service: str = "icm",
        workspace_id: str = "default",
    ) -> dict[str, Any]:
        return backend.call_tool(
            "icm.runtime.info",
            {"manager_service": manager_service, "workspace_id": workspace_id},
        )

    @server.tool(name="icm.strategy.presets")
    def strategy_presets(
        manager_service: str = "icm",
        workspace_id: str = "default",
    ) -> dict[str, Any]:
        return backend.call_tool(
            "icm.strategy.presets",
            {"manager_service": manager_service, "workspace_id": workspace_id},
        )

    @server.tool(name="icm.strategy.register_preset")
    def strategy_register_preset(
        preset_id: str,
        strategy_id: str,
        overrides: dict[str, Any] | None = None,
        manager_service: str = "icm",
        workspace_id: str = "default",
    ) -> dict[str, Any]:
        return backend.call_tool(
            "icm.strategy.register_preset",
            {
                "preset_id": preset_id,
                "strategy_id": strategy_id,
                "overrides": overrides or {},
                "manager_service": manager_service,
                "workspace_id": workspace_id,
            },
        )

    @server.tool(name="icm.plugin.register_feature")
    def plugin_register_feature(
        plugin: str,
        use_as_default: bool = False,
        manager_service: str = "icm",
        workspace_id: str = "default",
    ) -> dict[str, Any]:
        return backend.call_tool(
            "icm.plugin.register_feature",
            {
                "plugin": plugin,
                "use_as_default": use_as_default,
                "manager_service": manager_service,
                "workspace_id": workspace_id,
            },
        )

    @server.tool(name="icm.snapshot.save")
    def snapshot_save(
        snapshot_id: str,
        path: str | None = None,
        meta: dict[str, Any] | None = None,
        manager_service: str = "icm",
        workspace_id: str = "default",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "snapshot_id": snapshot_id,
            "meta": meta or {},
            "manager_service": manager_service,
            "workspace_id": workspace_id,
        }
        if path is not None:
            payload["path"] = path
        return backend.call_tool("icm.snapshot.save", payload)

    @server.tool(name="icm.snapshot.load")
    def snapshot_load(
        path: str,
        reset_policies: bool = True,
        manager_service: str = "icm",
        workspace_id: str = "default",
    ) -> dict[str, Any]:
        return backend.call_tool(
            "icm.snapshot.load",
            {
                "path": path,
                "reset_policies": reset_policies,
                "manager_service": manager_service,
                "workspace_id": workspace_id,
            },
        )

    @server.tool(name="icm.cog.compose")
    def cog_compose(
        cog_ids: list[str],
        new_cog_id: str,
        theme: str | None = None,
        graph_id: str | None = None,
        bucket: str | None = None,
        manager_service: str = "icm",
        workspace_id: str = "default",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "cog_ids": cog_ids,
            "new_cog_id": new_cog_id,
            "manager_service": manager_service,
            "workspace_id": workspace_id,
        }
        if theme is not None:
            payload["theme"] = theme
        if graph_id is not None:
            payload["graph_id"] = graph_id
        if bucket is not None:
            payload["bucket"] = bucket
        return backend.call_tool("icm.cog.compose", payload)

    @server.tool(name="icm.cog.split")
    def cog_split(
        cog_id: str,
        mode: str = "words",
        new_cog_prefix: str | None = None,
        max_items: int | None = None,
        graph_id: str | None = None,
        bucket: str | None = None,
        manager_service: str = "icm",
        workspace_id: str = "default",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "cog_id": cog_id,
            "mode": mode,
            "manager_service": manager_service,
            "workspace_id": workspace_id,
        }
        if new_cog_prefix is not None:
            payload["new_cog_prefix"] = new_cog_prefix
        if max_items is not None:
            payload["max_items"] = max_items
        if graph_id is not None:
            payload["graph_id"] = graph_id
        if bucket is not None:
            payload["bucket"] = bucket
        return backend.call_tool("icm.cog.split", payload)

    return server


def run_mcp_stdio_server(
    name: str = "ICM",
    registry: ICMRuntimeRegistry | None = None,
) -> None:
    server = build_mcp_server(name=name, registry=registry)
    try:
        server.run(transport="stdio")
    except TypeError:
        server.run()


if __name__ == "__main__":
    run_mcp_stdio_server()
