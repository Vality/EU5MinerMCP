from __future__ import annotations

from pathlib import Path

import eu5miner.inspection as inspection
import pytest
from eu5miner import GameInstall
from mcp.types import CallToolResult, TextContent, Tool

import eu5miner_mcp.tools.entities as entity_tools
import eu5miner_mcp.tools.mods as mod_tools
import eu5miner_mcp.tools.systems as systems_tools
from eu5miner_mcp.__main__ import main as package_main
from eu5miner_mcp.cli import main
from eu5miner_mcp.models import ToolDescriptor
from eu5miner_mcp.serializers import (
    serialize_entity_detail,
    serialize_entity_links,
    serialize_status_message,
    serialize_system_list,
)
from eu5miner_mcp.server import build_server, build_server_runtime, build_startup_message
from eu5miner_mcp.tools import (
    describe_entity_tools,
    describe_file_tools,
    describe_install_tools,
    describe_mod_tools,
    describe_system_tools,
)
from eu5miner_mcp.tools.entities import DescribeEntityRequest, FindEntityRequest, find_entities
from eu5miner_mcp.tools.files import ListFilesRequest, list_files
from eu5miner_mcp.tools.install import InspectInstallRequest, inspect_install
from eu5miner_mcp.tools.systems import GetSystemReportRequest, list_systems
from eu5miner_mcp.transport import MCPServerTransportAdapter


def test_build_startup_message_lists_real_tool_names() -> None:
    message = build_startup_message()
    runtime = build_server_runtime()

    assert f"EU5MinerMCP {runtime.version} server ready." in message
    assert "Available transports: local-shell, stdio." in message
    assert f"Tools ({runtime.tool_count}):" in message
    assert "Write tools require explicit confirm=true: apply-mod-update." in message
    assert "apply-mod-update" in message
    assert "describe-entity" in message
    assert "find-entity" in message
    assert "inspect-install" in message
    assert "list-entity-systems" in message
    assert "list-entity-links" in message
    assert "plan-mod-update" in message
    assert "report-system" in message


def test_serialize_status_message_includes_tool_names() -> None:
    message = build_startup_message()
    payload = serialize_status_message(message, tool_names=("inspect-install", "list-systems"))

    assert payload == {
        "status": message,
        "tools": ["inspect-install", "list-systems"],
    }


def test_build_server_runtime_exposes_package_version_and_transports() -> None:
    runtime = build_server_runtime()

    assert runtime.display_name == "EU5MinerMCP"
    assert runtime.package_name == "eu5miner-mcp"
    assert runtime.server_name == "eu5miner-mcp"
    assert runtime.version
    assert runtime.transports == ("local-shell", "stdio")
    assert runtime.tool_count == len(runtime.tool_names)
    assert runtime.write_tool_names == ("apply-mod-update",)
    assert runtime.write_tool_count == 1
    assert runtime.tool_names[0] == "inspect-install"


def test_server_runtime_builds_stdio_instructions_from_registry() -> None:
    runtime = build_server_runtime()

    instructions = runtime.build_stdio_instructions()

    assert f"EU5MinerMCP {runtime.version}" in instructions
    assert f"Available tools ({runtime.tool_count}):" in instructions
    assert "Write tools require explicit confirm=true: apply-mod-update." in instructions
    assert "list-systems" in instructions
    assert "describe-entity" in instructions


def test_serialize_entity_detail_includes_fields_and_references() -> None:
    detail = inspection.EntityDetail(
        summary=inspection.EntitySummary(
            system="map",
            entity_kind="location",
            name="stockholm",
            group="province",
            description="capital_of=SWE; setup=yes",
        ),
        fields=(
            inspection.EntityField(name="hierarchy_path", value=("scandinavia", "province")),
            inspection.EntityField(name="has_location_setup", value=True),
        ),
        references=(
            inspection.EntityReference(
                role="capital_of",
                system="map",
                entity_kind="country",
                target_name="SWE",
            ),
        ),
    )

    payload = serialize_entity_detail(detail)

    assert payload == {
        "summary": {
            "system": "map",
            "entity_kind": "location",
            "name": "stockholm",
            "group": "province",
            "description": "capital_of=SWE; setup=yes",
        },
        "fields": [
            {"name": "hierarchy_path", "value": ["scandinavia", "province"]},
            {"name": "has_location_setup", "value": True},
        ],
        "references": [
            {
                "role": "capital_of",
                "system": "map",
                "entity_kind": "country",
                "target_name": "SWE",
            }
        ],
    }


def test_serialize_entity_links_returns_link_only_payload() -> None:
    detail = inspection.EntityDetail(
        summary=inspection.EntitySummary(
            system="map",
            entity_kind="location",
            name="stockholm",
            group="province",
            description="capital_of=SWE; setup=yes",
        ),
        fields=(
            inspection.EntityField(name="hierarchy_path", value=("scandinavia", "province")),
        ),
        references=(
            inspection.EntityReference(
                role="capital_of",
                system="map",
                entity_kind="country",
                target_name="SWE",
            ),
        ),
    )

    payload = serialize_entity_links(detail)

    assert payload == {
        "system": "map",
        "entity_kind": "location",
        "name": "stockholm",
        "reference_count": 1,
        "references": [
            {
                "role": "capital_of",
                "system": "map",
                "entity_kind": "country",
                "target_name": "SWE",
            }
        ],
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
    assert all(descriptor.input_schema["type"] == "object" for descriptor in descriptors)
    assert all(
        descriptor.input_schema["additionalProperties"] is False
        for descriptor in descriptors
    )


def test_tool_descriptors_publish_runtime_argument_contracts() -> None:
    list_files_schema = describe_file_tools()[0].input_schema
    plan_schema, apply_schema = describe_mod_tools()
    report_schema = describe_system_tools()[1].input_schema
    find_entity_schema = describe_entity_tools()[1].input_schema

    assert list_files_schema["properties"]["limit"] == {
        "type": "integer",
        "minimum": 1,
        "default": 20,
        "description": "Maximum number of merged files to return.",
    }
    assert report_schema["properties"]["language"]["default"] == "english"
    assert find_entity_schema["properties"]["limit"]["minimum"] == 1
    assert find_entity_schema["properties"]["limit"]["default"] == 20
    assert plan_schema.input_schema["anyOf"] == [
        {"required": ["intended_paths"]},
        {"required": ["content_by_relative_path"]},
    ]
    assert plan_schema.input_schema["properties"]["intended_paths"]["minItems"] == 1
    assert (
        plan_schema.input_schema["properties"]["content_by_relative_path"]["minProperties"]
        == 1
    )
    assert apply_schema.input_schema["properties"]["overwrite"]["default"] is True
    assert apply_schema.input_schema["properties"]["confirm"] == {
        "type": "boolean",
        "default": False,
        "description": (
            "Required for live writes. Set to true after reviewing plan-mod-update "
            "output."
        ),
    }


def test_describe_entity_tools_expose_real_entity_browsing_slice() -> None:
    descriptor_names = [descriptor.name for descriptor in describe_entity_tools()]

    assert descriptor_names == [
        "list-entity-systems",
        "find-entity",
        "describe-entity",
        "list-entity-links",
    ]


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


def test_list_entity_systems_returns_core_supported_entity_systems() -> None:
    systems = entity_tools.list_entity_systems()

    assert [(system.name, system.primary_entity_kind) for system in systems] == [
        ("economy", "good"),
        ("government", "government_type"),
        ("religion", "religion"),
        ("map", "location"),
    ]


def test_find_entity_filters_summaries_for_synthetic_install(tmp_path: Path) -> None:
    install_root = _make_synthetic_entity_install(tmp_path / "fixture")

    result = find_entities(
        FindEntityRequest(
            install_root=install_root,
            system="economy",
            name_contains="ir",
            limit=5,
        )
    )

    assert result.system == "economy"
    assert result.name_contains == "ir"
    assert result.total_count == 1
    assert [summary.name for summary in result.entities] == ["iron"]
    assert result.entities[0].entity_kind == "good"
    assert result.entities[0].group == "raw_material"


def test_describe_entity_uses_mod_roots_for_synthetic_install(tmp_path: Path) -> None:
    install_root = _make_synthetic_entity_install(tmp_path / "fixture")
    mod_root = tmp_path / "economy_mod"
    _write_file(
        mod_root / "in_game" / "common" / "goods" / "zinc.txt",
        (
            "zinc = {\n"
            "    method = mining\n"
            "    category = raw_material\n"
            "    default_market_price = 5\n"
            "}\n"
        ),
    )

    summaries = find_entities(
        FindEntityRequest(
            install_root=install_root,
            system="economy",
            mod_roots=(mod_root,),
            name_contains="zin",
        )
    )
    detail = entity_tools.describe_entity(
        DescribeEntityRequest(
            install_root=install_root,
            system="economy",
            name="zinc",
            mod_roots=(mod_root,),
        )
    )

    assert [summary.name for summary in summaries.entities] == ["zinc"]
    assert detail.summary.name == "zinc"
    assert detail.summary.group == "raw_material"
    assert any(
        field.name == "default_market_price" and field.value == "5"
        for field in detail.fields
    )


def test_list_entity_links_reuses_describe_entity_references(tmp_path: Path) -> None:
    install_root = _make_synthetic_entity_install(tmp_path / "fixture")

    references = entity_tools.list_entity_links(
        DescribeEntityRequest(
            install_root=install_root,
            system="economy",
            name="iron",
        )
    )

    assert references == (
        inspection.EntityReference(
            role="demand_add",
            system="economy",
            entity_kind="good",
            target_name="grain",
        ),
    )


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


def test_list_files_requires_positive_limit() -> None:
    with pytest.raises(ValueError, match="limit must be at least 1"):
        build_server().call_tool(
            "list-files",
            {
                "phase": "in_game",
                "limit": 0,
            },
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


def test_apply_mod_update_requires_confirmation() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "apply-mod-update writes files under mod_root; review plan-mod-update "
            "first, then retry with confirm=true"
        ),
    ):
        build_server().call_tool(
            "apply-mod-update",
            {
                "mod_root": "my_mod",
                "phase": "in_game",
                "subtree": "common/buildings",
                "content_by_relative_path": {"common/buildings/a.txt": "override = yes\n"},
            },
        )


def test_plan_mod_update_rejects_apply_only_arguments() -> None:
    with pytest.raises(
        TypeError,
        match="plan-mod-update got unexpected arguments: confirm, overwrite",
    ):
        build_server().call_tool(
            "plan-mod-update",
            {
                "mod_root": "my_mod",
                "phase": "in_game",
                "subtree": "common/buildings",
                "content_by_relative_path": {"common/buildings/a.txt": "override = yes\n"},
                "confirm": True,
                "overwrite": True,
            },
        )


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
    _write_file(
        install_root / "game" / "in_game" / "common" / "goods" / "goods.txt",
        (
            "iron = {\n"
            "    method = mining\n"
            "    category = raw_material\n"
            "    default_market_price = 3\n"
            "    demand_add = { grain = 0.2 }\n"
            "}\n"
            "grain = { method = farming category = food }\n"
        ),
    )
    _write_file(
        install_root / "game" / "in_game" / "common" / "prices" / "market.txt",
        "build_road = { gold = 10 }\n",
    )
    _write_file(
        install_root / "game" / "in_game" / "common" / "generic_actions" / "market.txt",
        "create_market = { type = owncountry select_trigger = { looking_for_a = market } }\n",
    )
    _write_file(
        install_root / "game" / "in_game" / "common" / "attribute_columns" / "market.txt",
        "market = { name = { widget = default_text_column } }\n",
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
            "confirm": True,
        },
    )
    systems_response = server.call_tool("list-systems")
    entity_systems_response = server.call_tool("list-entity-systems")
    find_entity_response = server.call_tool(
        "find-entity",
        {
            "install_root": str(install_root),
            "system": "economy",
            "name_contains": "ir",
        },
    )
    describe_entity_response = server.call_tool(
        "describe-entity",
        {
            "install_root": str(install_root),
            "system": "economy",
            "name": "iron",
        },
    )
    list_entity_links_response = server.call_tool(
        "list-entity-links",
        {
            "install_root": str(install_root),
            "system": "economy",
            "name": "iron",
        },
    )

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
    assert entity_systems_response.structured_content["systems"] == [
        {
            "name": "economy",
            "description": (
                "Browse goods definitions with market-facing fields and related good links."
            ),
            "primary_entity_kind": "good",
        },
        {
            "name": "government",
            "description": (
                "Browse government types with linked reforms, laws, and default estates."
            ),
            "primary_entity_kind": "government_type",
        },
        {
            "name": "religion",
            "description": (
                "Browse religions with linked aspects, factions, focuses, schools, figures, "
                "and holy sites."
            ),
            "primary_entity_kind": "religion",
        },
        {
            "name": "map",
            "description": (
                "Browse linked locations merged from map hierarchy and main-menu setup data."
            ),
            "primary_entity_kind": "location",
        },
    ]
    assert find_entity_response.structured_content == {
        "system": "economy",
        "name_contains": "ir",
        "total_count": 1,
        "returned_count": 1,
        "limit": 20,
        "entities": [
            {
                "system": "economy",
                "entity_kind": "good",
                "name": "iron",
                "group": "raw_material",
                "description": "method=mining; default_market_price=3",
            }
        ],
    }
    assert describe_entity_response.structured_content == {
        "summary": {
            "system": "economy",
            "entity_kind": "good",
            "name": "iron",
            "group": "raw_material",
            "description": "method=mining; default_market_price=3",
        },
        "fields": [
            {"name": "method", "value": "mining"},
            {"name": "category", "value": "raw_material"},
            {"name": "default_market_price", "value": "3"},
        ],
        "references": [
            {
                "role": "demand_add",
                "system": "economy",
                "entity_kind": "good",
                "target_name": "grain",
            }
        ],
    }
    assert "Entity: economy/good/iron" in describe_entity_response.text
    assert list_entity_links_response.structured_content == {
        "system": "economy",
        "entity_kind": "good",
        "name": "iron",
        "reference_count": 1,
        "references": [
            {
                "role": "demand_add",
                "system": "economy",
                "entity_kind": "good",
                "target_name": "grain",
            }
        ],
    }
    assert "Entity links: economy/good/iron" in list_entity_links_response.text


def test_transport_adapter_lists_sdk_tools_from_internal_registry() -> None:
    adapter = MCPServerTransportAdapter(build_server())

    tools = adapter.list_tools()

    assert tools
    assert all(isinstance(tool, Tool) for tool in tools)
    assert [tool.name for tool in tools] == [
        "inspect-install",
        "list-files",
        "plan-mod-update",
        "apply-mod-update",
        "list-systems",
        "report-system",
        "list-entity-systems",
        "find-entity",
        "describe-entity",
        "list-entity-links",
    ]
    assert tools[0].inputSchema == describe_install_tools()[0].input_schema


def test_transport_adapter_builds_versioned_sdk_initialization_metadata() -> None:
    adapter = MCPServerTransportAdapter(build_server())
    runtime = build_server_runtime()

    initialization_options = adapter.build_sdk_server().create_initialization_options()

    assert initialization_options.server_name == runtime.server_name
    assert initialization_options.server_version == runtime.version
    assert initialization_options.instructions == runtime.build_stdio_instructions()


def test_transport_adapter_wraps_tool_result_as_sdk_payload() -> None:
    adapter = MCPServerTransportAdapter(build_server())

    result = adapter.call_tool("list-systems")

    assert isinstance(result, CallToolResult)
    assert result.isError is False
    assert result.structuredContent == serialize_system_list(list_systems())
    assert result.content == [TextContent(type="text", text=result.content[0].text)]
    assert result.content[0].text.startswith("Supported system reports:\n")
    assert "- economy:" in result.content[0].text
    assert "- government:" in result.content[0].text
    assert "- map:" in result.content[0].text


def test_transport_adapter_returns_protocol_safe_tool_errors() -> None:
    adapter = MCPServerTransportAdapter(build_server())
    expected_error = (
        "Unknown tool 'missing-tool'. Valid tools: inspect-install, list-files, "
        "plan-mod-update, apply-mod-update, list-systems, report-system, "
        "list-entity-systems, find-entity, describe-entity, list-entity-links"
    )

    result = adapter.call_tool("missing-tool")

    assert result.isError is True
    assert result.structuredContent == {
        "error": expected_error,
        "error_type": "KeyError",
    }
    assert result.content == [
        TextContent(
            type="text",
            text=f"KeyError: {expected_error}",
        )
    ]


def test_transport_adapter_rejects_unexpected_tool_arguments() -> None:
    adapter = MCPServerTransportAdapter(build_server())

    result = adapter.call_tool("list-systems", {"unexpected": True})

    assert result.isError is True
    assert result.structuredContent == {
        "error": "list-systems got unexpected arguments: unexpected",
        "error_type": "TypeError",
    }
    assert result.content == [
        TextContent(
            type="text",
            text="TypeError: list-systems got unexpected arguments: unexpected",
        )
    ]


def test_cli_main_describe_prints_registered_tools(capsys) -> None:
    assert main(["--describe"]) == 0
    captured = capsys.readouterr()
    runtime = build_server_runtime()
    assert f"EU5MinerMCP {runtime.version} server ready." in captured.out
    assert "Server name: eu5miner-mcp" in captured.out
    assert f"Package version: {runtime.version}" in captured.out
    assert "Available transports: local-shell, stdio" in captured.out
    assert f"Registered tools ({runtime.tool_count}):" in captured.out
    assert "apply-mod-update" in captured.out
    assert "describe-entity" in captured.out
    assert "find-entity" in captured.out
    assert "inspect-install" in captured.out
    assert "list-entity-links" in captured.out
    assert "list-entity-systems" in captured.out
    assert "plan-mod-update" in captured.out
    assert "list-systems" in captured.out
    assert (
        "Write tools requiring confirmation: apply-mod-update (pass confirm=true "
        "after reviewing plan-mod-update output)"
        in captured.out
    )


def test_cli_main_stdio_does_not_print_to_stdout(capsys, monkeypatch) -> None:
    observed: dict[str, object] = {}

    def fake_run_stdio_server(server) -> int:
        observed["tool_names"] = [descriptor.name for descriptor in server.describe_tools()]
        return 0

    monkeypatch.setattr("eu5miner_mcp.cli.run_stdio_server", fake_run_stdio_server)

    assert main(["--stdio"]) == 0
    captured = capsys.readouterr()

    assert captured.out == ""
    assert observed["tool_names"] == [
        "inspect-install",
        "list-files",
        "plan-mod-update",
        "apply-mod-update",
        "list-systems",
        "report-system",
        "list-entity-systems",
        "find-entity",
        "describe-entity",
        "list-entity-links",
    ]


def test_package_main_describe_prints_registered_tools(capsys) -> None:
    assert package_main(["--describe"]) == 0
    captured = capsys.readouterr()
    runtime = build_server_runtime()
    assert f"EU5MinerMCP {runtime.version} server ready." in captured.out
    assert "Server name: eu5miner-mcp" in captured.out
    assert f"Package version: {runtime.version}" in captured.out
    assert "Available transports: local-shell, stdio" in captured.out
    assert f"Registered tools ({runtime.tool_count}):" in captured.out
    assert "apply-mod-update" in captured.out
    assert "describe-entity" in captured.out
    assert "find-entity" in captured.out
    assert "inspect-install" in captured.out
    assert "list-entity-links" in captured.out
    assert "list-entity-systems" in captured.out
    assert "plan-mod-update" in captured.out
    assert "list-systems" in captured.out
    assert (
        "Write tools requiring confirmation: apply-mod-update (pass confirm=true "
        "after reviewing plan-mod-update output)"
        in captured.out
    )


def test_package_main_stdio_does_not_print_to_stdout(capsys, monkeypatch) -> None:
    observed: dict[str, object] = {}

    def fake_run_stdio_server(server) -> int:
        observed["tool_names"] = [descriptor.name for descriptor in server.describe_tools()]
        return 0

    monkeypatch.setattr("eu5miner_mcp.cli.run_stdio_server", fake_run_stdio_server)

    assert package_main(["--stdio"]) == 0
    captured = capsys.readouterr()

    assert captured.out == ""
    assert observed["tool_names"] == [
        "inspect-install",
        "list-files",
        "plan-mod-update",
        "apply-mod-update",
        "list-systems",
        "report-system",
        "list-entity-systems",
        "find-entity",
        "describe-entity",
        "list-entity-links",
    ]


def _make_synthetic_entity_install(root: Path) -> Path:
    install_root = _make_install_root(root / "install")
    _write_file(
        install_root / "game" / "in_game" / "common" / "goods" / "goods.txt",
        (
            "iron = {\n"
            "    method = mining\n"
            "    category = raw_material\n"
            "    default_market_price = 3\n"
            "    demand_add = { grain = 0.2 }\n"
            "}\n"
            "grain = { method = farming category = food }\n"
        ),
    )
    _write_file(
        install_root / "game" / "in_game" / "common" / "prices" / "prices.txt",
        "build_road = { gold = 10 }\n",
    )
    _write_file(
        install_root / "game" / "in_game" / "common" / "generic_actions" / "actions.txt",
        "create_market = { type = owncountry select_trigger = { looking_for_a = market } }\n",
    )
    _write_file(
        install_root / "game" / "in_game" / "common" / "attribute_columns" / "columns.txt",
        "market = { name = { widget = default_text_column } }\n",
    )
    return install_root


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
