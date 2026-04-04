from eu5miner_mcp.cli import main
from eu5miner_mcp.serializers import serialize_status_message
from eu5miner_mcp.server import build_startup_message
from eu5miner_mcp.tools import (
    describe_entity_tools,
    describe_file_tools,
    describe_install_tools,
    describe_system_tools,
)


def test_build_startup_message_mentions_core_library_phase() -> None:
    message = build_startup_message()

    assert "EU5MinerMCP placeholder server ready." in message
    assert "in_game" in message


def test_serialize_status_message() -> None:
    message = build_startup_message()

    assert serialize_status_message(message) == {"status": message}


def test_placeholder_tool_groups_are_non_empty() -> None:
    assert describe_install_tools()
    assert describe_file_tools()
    assert describe_entity_tools()
    assert describe_system_tools()


def test_cli_main_returns_zero(capsys) -> None:
    assert main([]) == 0
    captured = capsys.readouterr()
    assert "EU5MinerMCP placeholder server ready." in captured.out
