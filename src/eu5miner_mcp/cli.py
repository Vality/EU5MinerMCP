"""CLI entrypoint for the current MCP tool slice."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from eu5miner_mcp.server import build_server, build_server_runtime, build_startup_message
from eu5miner_mcp.transport import run_stdio_server


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eu5miner-mcp")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--describe",
        action="store_true",
        help="Print the current MCP server tool surface.",
    )
    mode_group.add_argument(
        "--stdio",
        action="store_true",
        help="Serve the MCP tool surface over stdio.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    server = build_server()
    runtime = build_server_runtime(server)

    if args.stdio:
        return run_stdio_server(server)

    print(build_startup_message(server))

    if args.describe:
        print(f"Server name: {runtime.server_name}")
        print(f"Package version: {runtime.version}")
        print(f"Available transports: {', '.join(runtime.transports)}")
        print(f"Registered tools ({runtime.tool_count}):")
        for descriptor in server.describe_tools():
            print(f"- {descriptor.name}: {descriptor.description}")
        print(
            "Write tools requiring confirmation: "
            f"{', '.join(runtime.write_tool_names)} (pass confirm=true after reviewing "
            "plan-mod-update output)"
        )

    return 0
