from __future__ import annotations

from pathlib import Path

import eu5miner.inspection as inspection
from eu5miner import GameInstall

import eu5miner_mcp.tools.systems as systems_tools
from eu5miner_mcp.__main__ import main as package_main
from eu5miner_mcp.cli import main
from eu5miner_mcp.models import ToolDescriptor
from eu5miner_mcp.serializers import serialize_status_message
from eu5miner_mcp.server import build_server, build_startup_message
from eu5miner_mcp.tools import (
    describe_entity_tools,
    describe_file_tools,
    describe_install_tools,
    describe_system_tools,
)
from eu5miner_mcp.tools.files import ListFilesRequest, list_files
from eu5miner_mcp.tools.install import InspectInstallRequest, inspect_install
from eu5miner_mcp.tools.systems import GetSystemReportRequest, list_systems


def test_build_startup_message_lists_real_tool_names() -> None:
    message = build_startup_message()

    assert "EU5MinerMCP read-only server ready." in message
    assert "inspect-install" in message
    assert "report-system" in message


def test_serialize_status_message_includes_tool_names() -> None:
    message = build_startup_message()
    payload = serialize_status_message(message, tool_names=("inspect-install", "list-systems"))

    assert payload == {
        "status": message,
        "tools": ["inspect-install", "list-systems"],
    }


def test_tool_descriptors_are_typed_and_non_empty() -> None:
    descriptors = (
        *describe_install_tools(),
        *describe_file_tools(),
        *describe_system_tools(),
        *describe_entity_tools(),
    )

    assert descriptors
    assert all(isinstance(descriptor, ToolDescriptor) for descriptor in descriptors)


def test_inspect_install_tool_uses_core_facade(tmp_path: Path) -> None:
    install_root = _make_install_root(tmp_path / "install")

    summary = inspect_install(InspectInstallRequest(install_root=install_root))

    assert summary.root == install_root
    assert [source.name for source in summary.sources] == ["vanilla"]


def test_list_files_reports_visible_vfs_entries(tmp_path: Path) -> None:
    install_root = _make_install_root(tmp_path / "install")
    mod_root = tmp_path / "sample_mod"

    _write_file(
        install_root / "game" / "in_game" / "gui" / "sample.gui",
        "vanilla_widget = yes\n",
    )
    _write_file(
        mod_root / "in_game" / "gui" / "sample.gui",
        "mod_widget = yes\n",
    )
    _write_file(
        mod_root / "in_game" / "gui" / "extra.gui",
        "mod_extra = yes\n",
    )

    listing = list_files(
        ListFilesRequest(
            install_root=install_root,
            phase=inspection.ContentPhase.IN_GAME,
            subpath=Path("gui"),
            mod_roots=(mod_root,),
        )
    )

    assert listing.total_count == 2
    assert [file.relative_path for file in listing.files] == [
        Path("gui") / "extra.gui",
        Path("gui") / "sample.gui",
    ]
    assert listing.files[-1].winner.source.name == "sample_mod"


def test_list_systems_returns_core_supported_systems() -> None:
    systems = list_systems()

    assert [system.name for system in systems] == [
        "economy",
        "diplomacy",
        "government",
        "religion",
        "interface",
        "map",
    ]


def test_get_system_report_delegates_to_core_facade(
    tmp_path: Path,
    monkeypatch,
) -> None:
    install_root = _make_install_root(tmp_path / "install")
    observed: dict[str, object] = {}
    expected_report = inspection.SystemReport(
        name="map",
        description="Map report",
        representative_keys=("map_default",),
        summary_lines=("locations: 1",),
    )

    def fake_get_system_report(
        install: GameInstall,
        system: str,
        *,
        language: str = "english",
    ) -> inspection.SystemReport:
        observed["install_root"] = install.root
        observed["system"] = system
        observed["language"] = language
        return expected_report

    monkeypatch.setattr(systems_tools.inspection, "get_system_report", fake_get_system_report)

    report = systems_tools.get_system_report(
        GetSystemReportRequest(
            install_root=install_root,
            system="map",
            language="french",
        )
    )

    assert report == expected_report
    assert observed == {
        "install_root": install_root,
        "system": "map",
        "language": "french",
    }


def test_server_dispatches_registered_tools(tmp_path: Path) -> None:
    install_root = _make_install_root(tmp_path / "install")
    _write_file(
        install_root / "game" / "in_game" / "gui" / "sample.gui",
        "widget = yes\n",
    )
    server = build_server()

    install_response = server.call_tool("inspect-install", {"install_root": str(install_root)})
    file_response = server.call_tool(
        "list-files",
        {
            "install_root": str(install_root),
            "phase": "in_game",
            "subpath": "gui",
        },
    )
    systems_response = server.call_tool("list-systems")

    assert install_response.structured_content["root"] == str(install_root)
    assert file_response.structured_content["total_count"] == 1
    assert systems_response.structured_content["systems"]


def test_cli_main_describe_prints_registered_tools(capsys) -> None:
    assert main(["--describe"]) == 0
    captured = capsys.readouterr()
    assert "EU5MinerMCP read-only server ready." in captured.out
    assert "inspect-install" in captured.out
    assert "list-systems" in captured.out


def test_package_main_describe_prints_registered_tools(capsys) -> None:
    assert package_main(["--describe"]) == 0
    captured = capsys.readouterr()
    assert "EU5MinerMCP read-only server ready." in captured.out
    assert "inspect-install" in captured.out
    assert "list-systems" in captured.out


def _make_install_root(install_root: Path) -> Path:
    game_dir = install_root / "game"
    for phase_name in ("loading_screen", "main_menu", "in_game"):
        (game_dir / phase_name).mkdir(parents=True, exist_ok=True)
    (game_dir / "dlc").mkdir(parents=True, exist_ok=True)
    (game_dir / "mod").mkdir(parents=True, exist_ok=True)
    return install_root


def _write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
