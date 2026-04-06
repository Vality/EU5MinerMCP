"""Official MCP SDK transport adapter over the internal typed tool registry."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any, cast

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, TextContent, Tool

from eu5miner_mcp.models import ToolResponse
from eu5miner_mcp.server import MCPServer, ServerRuntime, build_server, build_server_runtime


class MCPServerTransportAdapter:
    def __init__(self, server: MCPServer) -> None:
        self._server = server

    def describe_runtime(self) -> ServerRuntime:
        return build_server_runtime(self._server)

    def list_tools(self) -> list[Tool]:
        return [
            Tool(
                name=descriptor.name,
                description=descriptor.description,
                inputSchema=descriptor.input_schema,
            )
            for descriptor in self._server.describe_tools()
        ]

    def call_tool(
        self,
        name: str,
        arguments: Mapping[str, object] | None = None,
    ) -> CallToolResult:
        try:
            response = self._server.call_tool(name, arguments)
        except Exception as exc:
            return _error_result(exc)

        return _success_result(response)

    def build_sdk_server(self) -> Server[Any]:
        runtime = self.describe_runtime()
        sdk_server: Server[Any] = Server(
            runtime.server_name,
            version=runtime.version,
            instructions=runtime.build_stdio_instructions(),
        )

        async def handle_list_tools() -> list[Tool]:
            return self.list_tools()

        async def handle_call_tool(
            name: str,
            arguments: dict[str, object],
        ) -> CallToolResult:
            return self.call_tool(name, arguments)

        cast(Any, sdk_server).list_tools()(handle_list_tools)
        cast(Any, sdk_server).call_tool()(handle_call_tool)

        return sdk_server


async def serve_stdio(server: MCPServer | None = None) -> None:
    active_server = build_server() if server is None else server
    adapter = MCPServerTransportAdapter(active_server)
    sdk_server = adapter.build_sdk_server()

    async with stdio_server() as (read_stream, write_stream):
        await sdk_server.run(
            read_stream,
            write_stream,
            sdk_server.create_initialization_options(),
        )


def run_stdio_server(server: MCPServer | None = None) -> int:
    asyncio.run(serve_stdio(server))
    return 0


def _success_result(response: ToolResponse) -> CallToolResult:
    return CallToolResult(
        content=[TextContent(type="text", text=response.text)],
        structuredContent=dict(response.structured_content),
        isError=False,
    )


def _error_result(exc: Exception) -> CallToolResult:
    message = exc.args[0] if len(exc.args) == 1 and isinstance(exc.args[0], str) else str(exc)
    return CallToolResult(
        content=[TextContent(type="text", text=f"{type(exc).__name__}: {message}")],
        structuredContent={
            "error": message,
            "error_type": type(exc).__name__,
        },
        isError=True,
    )
