"""CLI entrypoint for the current MCP tool slice."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from eu5miner_mcp.server import build_server, build_startup_message
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

    if args.stdio:
        return run_stdio_server(server)

    print(build_startup_message(server))

    if args.describe:
        for descriptor in server.describe_tools():
            print(f"- {descriptor.name}: {descriptor.description}")

    return 0
