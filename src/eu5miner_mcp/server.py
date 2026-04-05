"""Thin read-only MCP server surface over the core EU5Miner library."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from eu5miner_mcp.models import RegisteredTool, ToolDescriptor, ToolResponse
from eu5miner_mcp.tools import get_file_tools, get_install_tools, get_system_tools


@dataclass(frozen=True)
class ReadOnlyServer:
    tools: tuple[RegisteredTool, ...]

    def describe_tools(self) -> tuple[ToolDescriptor, ...]:
        return tuple(tool.descriptor for tool in self.tools)

    def call_tool(
        self,
        name: str,
        arguments: Mapping[str, object] | None = None,
    ) -> ToolResponse:
        for tool in self.tools:
            if tool.descriptor.name == name:
                return tool.invoke(arguments)

        valid_names = ", ".join(descriptor.name for descriptor in self.describe_tools())
        raise KeyError(f"Unknown tool '{name}'. Valid tools: {valid_names}")


def build_server() -> ReadOnlyServer:
    return ReadOnlyServer(
        tools=(
            *get_install_tools(),
            *get_file_tools(),
            *get_system_tools(),
        )
    )


def build_startup_message(server: ReadOnlyServer | None = None) -> str:
    active_server = build_server() if server is None else server
    tool_names = ", ".join(descriptor.name for descriptor in active_server.describe_tools())
    return f"EU5MinerMCP read-only server ready. Tools: {tool_names}."


def run_server() -> str:
    return build_startup_message(build_server())
