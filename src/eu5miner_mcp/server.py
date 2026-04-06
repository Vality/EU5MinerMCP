"""Thin typed MCP server surface over the core EU5Miner library."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

from eu5miner_mcp.models import RegisteredTool, ToolDescriptor, ToolResponse
from eu5miner_mcp.tools import (
    get_entity_tools,
    get_file_tools,
    get_install_tools,
    get_mod_tools,
    get_system_tools,
)

_PACKAGE_NAME = "eu5miner-mcp"
_SERVER_NAME = "eu5miner-mcp"
_SERVER_DISPLAY_NAME = "EU5MinerMCP"
_SUPPORTED_TRANSPORTS = ("local-shell", "stdio")


@dataclass(frozen=True)
class MCPServer:
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


ReadOnlyServer = MCPServer


@dataclass(frozen=True)
class ServerRuntime:
    display_name: str
    package_name: str
    server_name: str
    version: str
    transports: tuple[str, ...]
    tool_names: tuple[str, ...]

    @property
    def tool_count(self) -> int:
        return len(self.tool_names)

    def build_stdio_instructions(self) -> str:
        tool_names = ", ".join(self.tool_names)
        return (
            f"{self.display_name} {self.version} serves the current eu5miner-backed "
            f"tool registry over stdio. Available tools ({self.tool_count}): {tool_names}."
        )


def build_server() -> MCPServer:
    return MCPServer(
        tools=(
            *get_install_tools(),
            *get_file_tools(),
            *get_mod_tools(),
            *get_system_tools(),
            *get_entity_tools(),
        )
    )


def build_server_runtime(server: MCPServer | None = None) -> ServerRuntime:
    active_server = build_server() if server is None else server
    return ServerRuntime(
        display_name=_SERVER_DISPLAY_NAME,
        package_name=_PACKAGE_NAME,
        server_name=_SERVER_NAME,
        version=_resolve_package_version(),
        transports=_SUPPORTED_TRANSPORTS,
        tool_names=tuple(
            descriptor.name for descriptor in active_server.describe_tools()
        ),
    )


def build_startup_message(server: MCPServer | None = None) -> str:
    runtime = build_server_runtime(server)
    tool_names = ", ".join(runtime.tool_names)
    transports = ", ".join(runtime.transports)
    return (
        f"{runtime.display_name} {runtime.version} server ready. "
        f"Available transports: {transports}. "
        f"Tools ({runtime.tool_count}): {tool_names}."
    )


def run_server() -> str:
    return build_startup_message(build_server())


def _resolve_package_version() -> str:
    try:
        return package_version(_PACKAGE_NAME)
    except PackageNotFoundError:
        return "0+unknown"
