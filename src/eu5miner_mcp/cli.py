"""CLI entrypoint for the first read-only MCP tool slice."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from eu5miner_mcp.server import build_server, build_startup_message


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eu5miner-mcp")
    parser.add_argument(
        "--describe",
        action="store_true",
        help="Print the current read-only MCP server tool surface.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    server = build_server()
    print(build_startup_message(server))

    if args.describe:
        for descriptor in server.describe_tools():
            print(f"- {descriptor.name}: {descriptor.description}")

    return 0
