"""Mod workflow MCP tools over the stable core mod facade."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from eu5miner import (
    AppliedModUpdate,
    ContentPhase,
    GameInstall,
    PlannedModUpdate,
    VirtualFilesystem,
)
from eu5miner import (
    apply_mod_update as apply_core_mod_update,
)
from eu5miner import (
    format_mod_update_report as format_core_mod_update_report,
)
from eu5miner import (
    plan_mod_update as plan_core_mod_update,
)

from eu5miner_mcp.models import RegisteredTool, ToolDescriptor, ToolResponse
from eu5miner_mcp.serializers import (
    serialize_applied_mod_update,
    serialize_planned_mod_update,
)


@dataclass(frozen=True)
class PlanModUpdateRequest:
    phase: ContentPhase
    mod_root: Path
    subtree: Path
    install_root: Path | None = None
    later_mod_roots: tuple[Path, ...] = ()
    intended_paths: tuple[Path, ...] = ()
    content_by_relative_path: Mapping[Path, str] | None = None


@dataclass(frozen=True)
class ApplyModUpdateRequest:
    phase: ContentPhase
    mod_root: Path
    subtree: Path
    install_root: Path | None = None
    later_mod_roots: tuple[Path, ...] = ()
    intended_paths: tuple[Path, ...] = ()
    content_by_relative_path: Mapping[Path, str] | None = None
    overwrite: bool = True


def plan_mod_update(request: PlanModUpdateRequest) -> PlannedModUpdate:
    install = GameInstall.discover(request.install_root)
    vfs = VirtualFilesystem.from_install(
        install,
        mod_roots=[request.mod_root, *request.later_mod_roots],
    )
    content_mapping: dict[Path, str] = {}
    content_paths: list[Path] = []
    if request.content_by_relative_path is not None:
        for relative_path, content in request.content_by_relative_path.items():
            content_mapping[relative_path] = content
            content_paths.append(relative_path)
    intended_paths = _combine_intended_paths(request.intended_paths, tuple(content_paths))
    if not intended_paths:
        raise ValueError(
            "At least one intended_path or content_by_relative_path entry is required"
        )
    content_mapping_for_core: dict[str | Path, str] | None = None
    if content_mapping:
        content_mapping_for_core = {
            relative_path: content for relative_path, content in content_mapping.items()
        }

    return plan_core_mod_update(
        vfs,
        request.mod_root.name,
        request.phase,
        request.subtree,
        intended_relative_paths=intended_paths,
        content_by_relative_path=content_mapping_for_core,
    )


def apply_mod_update(request: ApplyModUpdateRequest) -> AppliedModUpdate:
    planned_update = plan_mod_update(
        PlanModUpdateRequest(
            phase=request.phase,
            mod_root=request.mod_root,
            subtree=request.subtree,
            install_root=request.install_root,
            later_mod_roots=request.later_mod_roots,
            intended_paths=request.intended_paths,
            content_by_relative_path=request.content_by_relative_path,
        )
    )
    return apply_core_mod_update(planned_update, overwrite=request.overwrite)


def describe_mod_tools() -> tuple[ToolDescriptor, ...]:
    return (_PLAN_MOD_UPDATE_TOOL.descriptor, _APPLY_MOD_UPDATE_TOOL.descriptor)


def get_mod_tools() -> tuple[RegisteredTool, ...]:
    return (_PLAN_MOD_UPDATE_TOOL, _APPLY_MOD_UPDATE_TOOL)


def _invoke_plan_mod_update(arguments: Mapping[str, object] | None = None) -> ToolResponse:
    request = _parse_plan_mod_update_request(arguments)
    update = plan_mod_update(request)
    return ToolResponse(
        text=format_core_mod_update_report(update),
        structured_content=serialize_planned_mod_update(update),
    )


def _invoke_apply_mod_update(arguments: Mapping[str, object] | None = None) -> ToolResponse:
    request = _parse_apply_mod_update_request(arguments)
    update = apply_mod_update(request)
    return ToolResponse(
        text=format_core_mod_update_report(update),
        structured_content=serialize_applied_mod_update(update),
    )


def _parse_plan_mod_update_request(
    arguments: Mapping[str, object] | None,
) -> PlanModUpdateRequest:
    mapping = arguments or {}
    return _build_plan_mod_update_request(mapping)


def _parse_apply_mod_update_request(
    arguments: Mapping[str, object] | None,
) -> ApplyModUpdateRequest:
    mapping = arguments or {}
    plan_request = _build_plan_mod_update_request(mapping)
    overwrite = _bool_value(mapping.get("overwrite", True), field_name="overwrite")
    return ApplyModUpdateRequest(
        phase=plan_request.phase,
        mod_root=plan_request.mod_root,
        subtree=plan_request.subtree,
        install_root=plan_request.install_root,
        later_mod_roots=plan_request.later_mod_roots,
        intended_paths=plan_request.intended_paths,
        content_by_relative_path=plan_request.content_by_relative_path,
        overwrite=overwrite,
    )


def _build_plan_mod_update_request(mapping: Mapping[str, object]) -> PlanModUpdateRequest:
    phase_value = mapping.get("phase")
    if not isinstance(phase_value, str):
        raise TypeError("phase must be one of loading_screen, main_menu, or in_game")
    return PlanModUpdateRequest(
        phase=ContentPhase(phase_value),
        mod_root=_required_path(mapping.get("mod_root"), field_name="mod_root"),
        subtree=_required_path(mapping.get("subtree"), field_name="subtree"),
        install_root=_optional_path(mapping.get("install_root")),
        later_mod_roots=_path_tuple(
            mapping.get("later_mod_roots"),
            field_name="later_mod_roots",
        ),
        intended_paths=_path_tuple(
            mapping.get("intended_paths"),
            field_name="intended_paths",
        ),
        content_by_relative_path=_path_text_mapping(mapping.get("content_by_relative_path")),
    )


def _combine_intended_paths(
    intended_paths: Sequence[Path],
    content_paths: Sequence[Path],
) -> tuple[Path, ...]:
    combined: list[Path] = []
    seen: set[Path] = set()
    for relative_path in (*intended_paths, *content_paths):
        if relative_path in seen:
            continue
        combined.append(relative_path)
        seen.add(relative_path)
    return tuple(combined)


def _optional_path(value: object) -> Path | None:
    if value is None:
        return None
    return _coerce_path(value)


def _required_path(value: object, *, field_name: str) -> Path:
    if value is None:
        raise TypeError(f"{field_name} must be a path-like string")
    return _coerce_path(value)


def _path_tuple(value: object, *, field_name: str) -> tuple[Path, ...]:
    if value is None:
        return ()
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise TypeError(f"{field_name} must be a sequence of path strings")
    return tuple(_coerce_path(item) for item in value)


def _path_text_mapping(value: object) -> dict[Path, str] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise TypeError(
            "content_by_relative_path must be an object mapping relative paths to strings"
        )

    content_mapping: dict[Path, str] = {}
    for key, item in value.items():
        relative_path = _coerce_path(key)
        if not isinstance(item, str):
            raise TypeError(
                "content_by_relative_path values must be strings keyed by relative path"
            )
        content_mapping[relative_path] = item
    return content_mapping


def _bool_value(value: object, *, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise TypeError(f"{field_name} must be a boolean")


def _coerce_path(value: object) -> Path:
    if isinstance(value, Path):
        return value
    if isinstance(value, str):
        return Path(value)
    raise TypeError(f"Expected a path-like string, got {type(value).__name__}")


_PLAN_MOD_UPDATE_TOOL = RegisteredTool(
    descriptor=ToolDescriptor(
        name="plan-mod-update",
        description="Plan a non-destructive mod update over the core mod workflow API.",
        input_schema={
            "type": "object",
            "properties": {
                "install_root": {
                    "type": ["string", "null"],
                    "description": "Optional explicit EU5 install root.",
                },
                "mod_root": {
                    "type": "string",
                    "description": "Target mod root that will receive the planned update.",
                },
                "later_mod_roots": {
                    "type": "array",
                    "description": "Optional later mod roots that can shadow the target mod.",
                    "items": {"type": "string"},
                },
                "phase": {
                    "type": "string",
                    "enum": [phase.value for phase in ContentPhase],
                },
                "subtree": {
                    "type": "string",
                    "description": "Phase-relative subtree to plan, for example common/buildings.",
                },
                "intended_paths": {
                    "type": "array",
                    "description": (
                        "Optional phase-relative intended output paths, used even when no content "
                        "string is supplied."
                    ),
                    "items": {"type": "string"},
                },
                "content_by_relative_path": {
                    "type": "object",
                    "description": (
                        "Optional mapping of phase-relative output paths to planned file content."
                    ),
                    "additionalProperties": {"type": "string"},
                },
            },
            "required": ["mod_root", "phase", "subtree"],
        },
    ),
    invoke=_invoke_plan_mod_update,
)


_APPLY_MOD_UPDATE_TOOL = RegisteredTool(
    descriptor=ToolDescriptor(
        name="apply-mod-update",
        description="Apply a planned mod update over the core mod workflow API.",
        input_schema={
            "type": "object",
            "properties": {
                "install_root": {
                    "type": ["string", "null"],
                    "description": "Optional explicit EU5 install root.",
                },
                "mod_root": {
                    "type": "string",
                    "description": "Target mod root that will receive the applied update.",
                },
                "later_mod_roots": {
                    "type": "array",
                    "description": "Optional later mod roots that can shadow the target mod.",
                    "items": {"type": "string"},
                },
                "phase": {
                    "type": "string",
                    "enum": [phase.value for phase in ContentPhase],
                },
                "subtree": {
                    "type": "string",
                    "description": "Phase-relative subtree to apply, for example common/buildings.",
                },
                "intended_paths": {
                    "type": "array",
                    "description": (
                        "Optional phase-relative intended output paths, used even when no content "
                        "string is supplied."
                    ),
                    "items": {"type": "string"},
                },
                "content_by_relative_path": {
                    "type": "object",
                    "description": (
                        "Optional mapping of phase-relative output paths to applied file content."
                    ),
                    "additionalProperties": {"type": "string"},
                },
                "overwrite": {
                    "type": "boolean",
                    "description": (
                        "Whether existing target files may be overwritten. Defaults to true."
                    ),
                },
            },
            "required": ["mod_root", "phase", "subtree"],
        },
    ),
    invoke=_invoke_apply_mod_update,
)