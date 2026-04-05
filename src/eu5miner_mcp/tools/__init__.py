"""Typed MCP tool modules for the first read-only slice."""

from eu5miner_mcp.tools.entities import describe_entity_tools
from eu5miner_mcp.tools.files import describe_file_tools, get_file_tools
from eu5miner_mcp.tools.install import describe_install_tools, get_install_tools
from eu5miner_mcp.tools.systems import describe_system_tools, get_system_tools

__all__ = [
    "describe_entity_tools",
    "describe_file_tools",
    "describe_install_tools",
    "describe_system_tools",
    "get_file_tools",
    "get_install_tools",
    "get_system_tools",
]
