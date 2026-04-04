"""Minimal MCP server shell."""

from eu5miner import ContentPhase


def build_startup_message() -> str:
    return (
        "EU5MinerMCP placeholder server ready. "
        f"Core library available for phase {ContentPhase.IN_GAME.value}."
    )


def run_server() -> str:
    return build_startup_message()
