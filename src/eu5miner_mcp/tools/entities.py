"""Entity-oriented MCP tools over the stable core inspection facade."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import eu5miner.inspection as inspection
from eu5miner import GameInstall

from eu5miner_mcp.models import RegisteredTool, ToolDescriptor, ToolResponse
from eu5miner_mcp.serializers import (
    serialize_entity_detail,
    serialize_entity_links,
    serialize_entity_search_result,
    serialize_entity_system_list,
)


@dataclass(frozen=True)
class FindEntityRequest:
    system: str
    install_root: Path | None = None
    name_contains: str | None = None
    limit: int = 20
    mod_roots: tuple[Path, ...] = ()


@dataclass(frozen=True)
class EntitySearchResult:
    system: str
    name_contains: str | None
    limit: int
    total_count: int
    entities: tuple[inspection.EntitySummary, ...]


@dataclass(frozen=True)
class DescribeEntityRequest:
    system: str
    name: str
    install_root: Path | None = None
    mod_roots: tuple[Path, ...] = ()


def list_entity_systems() -> tuple[inspection.EntitySystemInfo, ...]:
    return inspection.list_entity_systems()


def find_entities(request: FindEntityRequest) -> EntitySearchResult:
    install = GameInstall.discover(request.install_root)
    summaries = inspection.list_system_entities(
        install,
        request.system,
        mod_roots=request.mod_roots or None,
    )
    matched_summaries = tuple(
        summary
        for summary in summaries
        if request.name_contains is None
        or request.name_contains.casefold() in summary.name.casefold()
    )
    return EntitySearchResult(
        system=request.system,
        name_contains=request.name_contains,
        limit=request.limit,
        total_count=len(matched_summaries),
        entities=matched_summaries[: request.limit],
    )


def describe_entity(request: DescribeEntityRequest) -> inspection.EntityDetail:
    install = GameInstall.discover(request.install_root)
    return inspection.get_system_entity(
        install,
        request.system,
        request.name,
        mod_roots=request.mod_roots or None,
    )


def list_entity_links(
    request: DescribeEntityRequest,
) -> tuple[inspection.EntityReference, ...]:
    return describe_entity(request).references


def describe_entity_tools() -> tuple[ToolDescriptor, ...]:
    return (
        _LIST_ENTITY_SYSTEMS_TOOL.descriptor,
        _FIND_ENTITY_TOOL.descriptor,
        _DESCRIBE_ENTITY_TOOL.descriptor,
        _LIST_ENTITY_LINKS_TOOL.descriptor,
    )


def get_entity_tools() -> tuple[RegisteredTool, ...]:
    return (
        _LIST_ENTITY_SYSTEMS_TOOL,
        _FIND_ENTITY_TOOL,
        _DESCRIBE_ENTITY_TOOL,
        _LIST_ENTITY_LINKS_TOOL,
    )


def _invoke_list_entity_systems(arguments: Mapping[str, object] | None = None) -> ToolResponse:
    if arguments:
        raise TypeError("list-entity-systems does not accept arguments")
    systems = list_entity_systems()
    lines = ["Browsable entity systems:"]
    lines.extend(
        f"- {system.name}: primary={system.primary_entity_kind}; {system.description}"
        for system in systems
    )
    return ToolResponse(
        text="\n".join(lines),
        structured_content=serialize_entity_system_list(systems),
    )


def _invoke_find_entity(arguments: Mapping[str, object] | None = None) -> ToolResponse:
    request = _parse_find_entity_request(arguments)
    result = find_entities(request)
    lines = [
        f"Entities for system={result.system}"
        + (
            f" name_contains={result.name_contains!r}"
            if result.name_contains is not None
            else ""
        )
    ]
    lines.extend(_format_entity_summary(summary) for summary in result.entities)
    lines.append(f"Matched: {result.total_count}")
    return ToolResponse(
        text="\n".join(lines),
        structured_content=serialize_entity_search_result(
            result.entities,
            system=result.system,
            total_count=result.total_count,
            limit=result.limit,
            name_contains=result.name_contains,
        ),
    )


def _invoke_describe_entity(arguments: Mapping[str, object] | None = None) -> ToolResponse:
    request = _parse_describe_entity_request(arguments)
    detail = describe_entity(request)
    lines = [
        (
            f"Entity: {detail.summary.system}/{detail.summary.entity_kind}/"
            f"{detail.summary.name}"
        )
    ]
    if detail.summary.group is not None:
        lines.append(f"Group: {detail.summary.group}")
    if detail.summary.description is not None:
        lines.append(f"Description: {detail.summary.description}")
    lines.append("Fields:")
    lines.extend(
        f"- {field.name}: {_format_browse_value(field.value)}" for field in detail.fields
    )
    lines.append("References:")
    if detail.references:
        lines.extend(f"- {_format_entity_reference(reference)}" for reference in detail.references)
    else:
        lines.append("- (none)")
    return ToolResponse(
        text="\n".join(lines),
        structured_content=serialize_entity_detail(detail),
    )


def _invoke_list_entity_links(arguments: Mapping[str, object] | None = None) -> ToolResponse:
    request = _parse_describe_entity_request(arguments)
    detail = describe_entity(request)
    lines = [
        (
            f"Entity links: {detail.summary.system}/{detail.summary.entity_kind}/"
            f"{detail.summary.name}"
        )
    ]
    if detail.references:
        lines.extend(f"- {_format_entity_reference(reference)}" for reference in detail.references)
    else:
        lines.append("- (none)")
    return ToolResponse(
        text="\n".join(lines),
        structured_content=serialize_entity_links(detail),
    )


def _parse_find_entity_request(arguments: Mapping[str, object] | None) -> FindEntityRequest:
    mapping = arguments or {}
    system = mapping.get("system")
    if not isinstance(system, str):
        raise TypeError("system must be a string")
    name_contains_value = mapping.get("name_contains")
    if name_contains_value is not None and not isinstance(name_contains_value, str):
        raise TypeError("name_contains must be a string")
    limit_value = mapping.get("limit", 20)
    if not isinstance(limit_value, int):
        raise TypeError("limit must be an integer")
    if limit_value < 1:
        raise ValueError("limit must be at least 1")
    return FindEntityRequest(
        system=system,
        install_root=_optional_path(mapping.get("install_root")),
        name_contains=name_contains_value or None,
        limit=limit_value,
        mod_roots=_path_tuple(mapping.get("mod_roots")),
    )


def _parse_describe_entity_request(
    arguments: Mapping[str, object] | None,
) -> DescribeEntityRequest:
    mapping = arguments or {}
    system = mapping.get("system")
    if not isinstance(system, str):
        raise TypeError("system must be a string")
    name = mapping.get("name")
    if not isinstance(name, str):
        raise TypeError("name must be a string")
    return DescribeEntityRequest(
        system=system,
        name=name,
        install_root=_optional_path(mapping.get("install_root")),
        mod_roots=_path_tuple(mapping.get("mod_roots")),
    )


def _format_entity_summary(summary: inspection.EntitySummary) -> str:
    line = f"- {summary.name} [{summary.entity_kind}]"
    if summary.group is not None:
        line += f" group={summary.group}"
    if summary.description is not None:
        line += f" description={summary.description}"
    return line


def _format_browse_value(value: inspection.BrowseValue) -> str:
    if isinstance(value, tuple):
        return ", ".join(value)
    return str(value)


def _format_entity_reference(reference: inspection.EntityReference) -> str:
    return (
        f"{reference.role} -> {reference.system}/"
        f"{reference.entity_kind}/{reference.target_name}"
    )


def _optional_path(value: object) -> Path | None:
    if value is None:
        return None
    return _coerce_path(value)


def _path_tuple(value: object) -> tuple[Path, ...]:
    if value is None:
        return ()
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise TypeError("mod_roots must be a sequence of path strings")
    return tuple(_coerce_path(item) for item in value)


def _coerce_path(value: object) -> Path:
    if isinstance(value, Path):
        return value
    if isinstance(value, str):
        return Path(value)
    raise TypeError(f"Expected a path-like string, got {type(value).__name__}")


_ENTITY_LOOKUP_INPUT_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "install_root": {
            "type": ["string", "null"],
            "description": "Optional explicit EU5 install root.",
        },
        "system": {
            "type": "string",
            "enum": [system.name for system in inspection.list_entity_systems()],
        },
        "name": {
            "type": "string",
            "description": "Exact entity name within the chosen system.",
        },
        "mod_roots": {
            "type": "array",
            "description": "Optional extra mod roots layered after vanilla and DLC.",
            "items": {"type": "string"},
        },
    },
    "required": ["system", "name"],
}


_LIST_ENTITY_SYSTEMS_TOOL = RegisteredTool(
    descriptor=ToolDescriptor(
        name="list-entity-systems",
        description=(
            "List the browseable entity systems and their primary entity families from the "
            "core inspection facade."
        ),
        input_schema={"type": "object", "properties": {}},
    ),
    invoke=_invoke_list_entity_systems,
)


_FIND_ENTITY_TOOL = RegisteredTool(
    descriptor=ToolDescriptor(
        name="find-entity",
        description=(
            "Browse one entity system over the core inspection facade, with optional "
            "case-insensitive name filtering."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "install_root": {
                    "type": ["string", "null"],
                    "description": "Optional explicit EU5 install root.",
                },
                "system": {
                    "type": "string",
                    "enum": [system.name for system in inspection.list_entity_systems()],
                },
                "name_contains": {
                    "type": "string",
                    "description": "Optional case-insensitive substring filter for entity names.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of matching entity summaries to return.",
                },
                "mod_roots": {
                    "type": "array",
                    "description": "Optional extra mod roots layered after vanilla and DLC.",
                    "items": {"type": "string"},
                },
            },
            "required": ["system"],
        },
    ),
    invoke=_invoke_find_entity,
)


_DESCRIBE_ENTITY_TOOL = RegisteredTool(
    descriptor=ToolDescriptor(
        name="describe-entity",
        description=(
            "Return the summary, browsable fields, and linked references for one entity "
            "from the core inspection facade."
        ),
        input_schema=_ENTITY_LOOKUP_INPUT_SCHEMA,
    ),
    invoke=_invoke_describe_entity,
)


_LIST_ENTITY_LINKS_TOOL = RegisteredTool(
    descriptor=ToolDescriptor(
        name="list-entity-links",
        description=(
            "List the linked references for one entity by reusing the core reference "
            "list already exposed by describe-entity."
        ),
        input_schema=_ENTITY_LOOKUP_INPUT_SCHEMA,
    ),
    invoke=_invoke_list_entity_links,
)
