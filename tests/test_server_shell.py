from __future__ import annotations

from pathlib import Path

import eu5miner.inspection as inspection
import pytest
from eu5miner import GameInstall

import eu5miner_mcp.tools.mods as mod_tools
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
    describe_mod_tools,
    describe_system_tools,
)
from eu5miner_mcp.tools.files import ListFilesRequest, list_files
from eu5miner_mcp.tools.install import InspectInstallRequest, inspect_install
from eu5miner_mcp.tools.systems import GetSystemReportRequest, list_systems


def test_build_startup_message_lists_real_tool_names() -> None:
    message = build_startup_message()

    assert "EU5MinerMCP server ready." in message
    assert "apply-mod-update" in message
    assert "inspect-install" in message
    assert "plan-mod-update" in message
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
        *describe_mod_tools(),
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


def test_plan_mod_update_wraps_core_planning_api(tmp_path: Path) -> None:
    install_root = _make_install_root(tmp_path / "install")
    mod_root = tmp_path / "my_mod"
    later_mod_root = tmp_path / "later_mod"
    override_path = Path("common") / "buildings" / "a.txt"
    blocked_path = Path("common") / "buildings" / "blocked.txt"

    _write_file(install_root / "game" / "in_game" / override_path, "vanilla\n")
    _write_file(later_mod_root / "in_game" / blocked_path, "late\n")

    update = mod_tools.plan_mod_update(
        mod_tools.PlanModUpdateRequest(
            install_root=install_root,
            mod_root=mod_root,
            later_mod_roots=(later_mod_root,),
            phase=inspection.ContentPhase.IN_GAME,
            subtree=Path("common") / "buildings",
            intended_paths=(blocked_path,),
            content_by_relative_path={override_path: "override = yes\n"},
        )
    )

    assert update.target_source_name == "my_mod"
    assert update.metadata_write.path == mod_root / ".metadata" / "metadata.json"
    assert update.replace_paths_to_add == ("game/in_game/common/buildings",)
    assert [write.relative_path for write in update.content_writes] == [override_path]
    assert len(update.warnings) == 1
    assert update.warnings[0].relative_path == blocked_path


def test_plan_mod_update_requires_paths_or_content(tmp_path: Path) -> None:
    install_root = _make_install_root(tmp_path / "install")

    with pytest.raises(
        ValueError,
        match="At least one intended_path or content_by_relative_path entry is required",
    ):
        mod_tools.plan_mod_update(
            mod_tools.PlanModUpdateRequest(
                install_root=install_root,
                mod_root=tmp_path / "my_mod",
                phase=inspection.ContentPhase.IN_GAME,
                subtree=Path("common") / "buildings",
            )
        )


def test_apply_mod_update_wraps_core_apply_api(tmp_path: Path) -> None:
    install_root = _make_install_root(tmp_path / "install")
    mod_root = tmp_path / "my_mod"
    override_path = Path("common") / "buildings" / "a.txt"

    _write_file(install_root / "game" / "in_game" / override_path, "vanilla\n")

    update = mod_tools.apply_mod_update(
        mod_tools.ApplyModUpdateRequest(
            install_root=install_root,
            mod_root=mod_root,
            phase=inspection.ContentPhase.IN_GAME,
            subtree=Path("common") / "buildings",
            content_by_relative_path={override_path: "override = yes\n"},
        )
    )

    assert update.plan.target_source_name == "my_mod"
    assert update.created_write_count == 2
    assert update.updated_write_count == 0
    assert update.unchanged_write_count == 0
    assert update.metadata_write.path == mod_root / ".metadata" / "metadata.json"
    assert update.content_writes[0].path == mod_root / "in_game" / override_path
    assert update.content_writes[0].path.read_text(encoding="utf-8") == "override = yes\n"


def test_apply_mod_update_respects_no_overwrite(tmp_path: Path) -> None:
    install_root = _make_install_root(tmp_path / "install")
    mod_root = tmp_path / "my_mod"
    override_path = Path("common") / "buildings" / "a.txt"

    _write_file(install_root / "game" / "in_game" / override_path, "vanilla\n")
    _write_file(mod_root / "in_game" / override_path, "old\n")

    with pytest.raises(FileExistsError, match="Refusing to overwrite existing file"):
        mod_tools.apply_mod_update(
            mod_tools.ApplyModUpdateRequest(
                install_root=install_root,
                mod_root=mod_root,
                phase=inspection.ContentPhase.IN_GAME,
                subtree=Path("common") / "buildings",
                content_by_relative_path={override_path: "override = yes\n"},
                overwrite=False,
            )
        )

    assert (mod_root / "in_game" / override_path).read_text(encoding="utf-8") == "old\n"


def test_server_dispatches_registered_tools(tmp_path: Path) -> None:
    install_root = _make_install_root(tmp_path / "install")
    _write_file(
        install_root / "game" / "in_game" / "gui" / "sample.gui",
        "widget = yes\n",
    )
    _write_file(
        install_root / "game" / "in_game" / "common" / "buildings" / "a.txt",
        "vanilla\n",
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
    plan_response = server.call_tool(
        "plan-mod-update",
        {
            "install_root": str(install_root),
            "mod_root": str(tmp_path / "my_mod"),
            "phase": "in_game",
            "subtree": "common/buildings",
            "content_by_relative_path": {"common/buildings/a.txt": "override = yes\n"},
        },
    )
    apply_response = server.call_tool(
        "apply-mod-update",
        {
            "install_root": str(install_root),
            "mod_root": str(tmp_path / "applied_mod"),
            "phase": "in_game",
            "subtree": "common/buildings",
            "content_by_relative_path": {"common/buildings/a.txt": "applied = yes\n"},
        },
    )
    systems_response = server.call_tool("list-systems")

    assert install_response.structured_content["root"] == str(install_root)
    assert file_response.structured_content["total_count"] == 1
    assert plan_response.structured_content["target_source_name"] == "my_mod"
    assert plan_response.structured_content["summary"] == {
        "intended_content_outputs": 1,
        "materialized_writes": 2,
        "metadata_writes": 1,
        "replace_path_additions": 1,
        "blocked_intended_outputs": 0,
        "warnings": 0,
        "advisories": 1,
    }
    assert plan_response.structured_content["content_writes"] == [
        {
            "path": str(tmp_path / "my_mod" / "in_game" / "common" / "buildings" / "a.txt"),
            "kind": "content",
            "content": "override = yes\n",
            "existed": False,
            "relative_path": str(Path("common") / "buildings" / "a.txt"),
            "emission_kind": "override",
        }
    ]
    assert "Planned mod update: my_mod" in plan_response.text
    assert apply_response.structured_content["target_source_name"] == "applied_mod"
    created_directories = apply_response.structured_content["created_directories"]
    assert apply_response.structured_content["summary"] == {
        "created_directories": len(created_directories),
        "created_writes": 2,
        "updated_writes": 0,
        "unchanged_writes": 0,
        "blocked_intended_outputs": 0,
        "warnings": 0,
        "advisories": 1,
    }
    assert str(tmp_path / "applied_mod" / ".metadata") in created_directories
    assert apply_response.structured_content["metadata_write"] == {
        "path": str(tmp_path / "applied_mod" / ".metadata" / "metadata.json"),
        "kind": "metadata",
        "status": "created",
    }
    assert apply_response.structured_content["content_writes"] == [
        {
            "path": str(
                tmp_path / "applied_mod" / "in_game" / "common" / "buildings" / "a.txt"
            ),
            "kind": "content",
            "status": "created",
            "relative_path": str(Path("common") / "buildings" / "a.txt"),
            "emission_kind": "override",
        }
    ]
    assert "Applied mod update: applied_mod" in apply_response.text
    assert systems_response.structured_content["systems"]


def test_cli_main_describe_prints_registered_tools(capsys) -> None:
    assert main(["--describe"]) == 0
    captured = capsys.readouterr()
    assert "EU5MinerMCP server ready." in captured.out
    assert "apply-mod-update" in captured.out
    assert "inspect-install" in captured.out
    assert "plan-mod-update" in captured.out
    assert "list-systems" in captured.out


def test_package_main_describe_prints_registered_tools(capsys) -> None:
    assert package_main(["--describe"]) == 0
    captured = capsys.readouterr()
    assert "EU5MinerMCP server ready." in captured.out
    assert "apply-mod-update" in captured.out
    assert "inspect-install" in captured.out
    assert "plan-mod-update" in captured.out
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
