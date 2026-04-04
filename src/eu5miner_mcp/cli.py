"""CLI entrypoint for the placeholder MCP server shell."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from eu5miner_mcp.server import run_server


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eu5miner-mcp")
    parser.add_argument(
        "--describe",
        action="store_true",
        help="Print the current placeholder MCP server status.",
    )
    parser.parse_args(list(argv) if argv is not None else None)
    print(run_server())
    return 0
