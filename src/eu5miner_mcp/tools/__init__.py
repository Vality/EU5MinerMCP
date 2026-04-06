"""Typed MCP tool modules for the current preview slice."""

from eu5miner_mcp.tools.diplomacy import describe_diplomacy_tools, get_diplomacy_tools
from eu5miner_mcp.tools.entities import describe_entity_tools, get_entity_tools
from eu5miner_mcp.tools.files import describe_file_tools, get_file_tools
from eu5miner_mcp.tools.install import describe_install_tools, get_install_tools
from eu5miner_mcp.tools.mods import describe_mod_tools, get_mod_tools
from eu5miner_mcp.tools.religion import describe_religion_tools, get_religion_tools
from eu5miner_mcp.tools.server import describe_server_tools, get_server_tools
from eu5miner_mcp.tools.systems import describe_system_tools, get_system_tools

__all__ = [
    "describe_diplomacy_tools",
    "describe_entity_tools",
    "describe_file_tools",
    "describe_install_tools",
    "describe_mod_tools",
    "describe_religion_tools",
    "describe_server_tools",
    "describe_system_tools",
    "get_diplomacy_tools",
    "get_entity_tools",
    "get_file_tools",
    "get_install_tools",
    "get_mod_tools",
    "get_religion_tools",
    "get_server_tools",
    "get_system_tools",
]
