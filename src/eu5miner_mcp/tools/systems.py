"""Read-only system-oriented MCP tools."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import eu5miner.inspection as inspection
from eu5miner import GameInstall

from eu5miner_mcp.models import RegisteredTool, ToolDescriptor, ToolResponse
from eu5miner_mcp.serializers import serialize_system_list, serialize_system_report


@dataclass(frozen=True)
class ListSystemsRequest:
    pass


@dataclass(frozen=True)
class GetSystemReportRequest:
    system: str
    install_root: Path | None = None
    language: str = "english"


def list_systems(_: ListSystemsRequest | None = None) -> tuple[inspection.SystemInfo, ...]:
    return inspection.list_supported_systems()


def get_system_report(request: GetSystemReportRequest) -> inspection.SystemReport:
    install = GameInstall.discover(request.install_root)
    return inspection.get_system_report(install, request.system, language=request.language)


def describe_system_tools() -> tuple[ToolDescriptor, ...]:
    return (_LIST_SYSTEMS_TOOL.descriptor, _REPORT_SYSTEM_TOOL.descriptor)


def get_system_tools() -> tuple[RegisteredTool, ...]:
    return (_LIST_SYSTEMS_TOOL, _REPORT_SYSTEM_TOOL)


def _invoke_list_systems(arguments: Mapping[str, object] | None = None) -> ToolResponse:
    if arguments:
        raise TypeError("list-systems does not accept arguments")
    systems = list_systems()
    lines = ["Supported system reports:"]
    lines.extend(f"- {system.name}: {system.description}" for system in systems)
    return ToolResponse(
        text="\n".join(lines),
        structured_content=serialize_system_list(systems),
    )


def _invoke_report_system(arguments: Mapping[str, object] | None = None) -> ToolResponse:
    request = _parse_get_system_report_request(arguments)
    report = get_system_report(request)
    return ToolResponse(
        text=inspection.format_system_report(report),
        structured_content=serialize_system_report(report),
    )


def _parse_get_system_report_request(
    arguments: Mapping[str, object] | None,
) -> GetSystemReportRequest:
    mapping = arguments or {}
    system = mapping.get("system")
    if not isinstance(system, str):
        raise TypeError("system must be a string")
    language = mapping.get("language", "english")
    if not isinstance(language, str):
        raise TypeError("language must be a string")
    install_root_value = mapping.get("install_root")
    install_root = None if install_root_value is None else _coerce_path(install_root_value)
    return GetSystemReportRequest(system=system, install_root=install_root, language=language)


def _coerce_path(value: object) -> Path:
    if isinstance(value, Path):
        return value
    if isinstance(value, str):
        return Path(value)
    raise TypeError(f"Expected a path-like string, got {type(value).__name__}")


_LIST_SYSTEMS_TOOL = RegisteredTool(
    descriptor=ToolDescriptor(
        name="list-systems",
        description="List the stable system reports exposed by the core inspection facade.",
        input_schema={"type": "object", "properties": {}},
    ),
    invoke=_invoke_list_systems,
)


_REPORT_SYSTEM_TOOL = RegisteredTool(
    descriptor=ToolDescriptor(
        name="report-system",
        description="Build a higher-level report for one supported system.",
        input_schema={
            "type": "object",
            "properties": {
                "install_root": {
                    "type": ["string", "null"],
                    "description": "Optional explicit EU5 install root.",
                },
                "system": {
                    "type": "string",
                    "enum": [info.name for info in inspection.list_supported_systems()],
                },
                "language": {
                    "type": "string",
                    "description": "Localization language used by language-sensitive reports.",
                },
            },
            "required": ["system"],
        },
    ),
    invoke=_invoke_report_system,
)
