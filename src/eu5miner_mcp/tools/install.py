"""Read-only install-oriented MCP tools."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import eu5miner.inspection as inspection

from eu5miner_mcp.models import RegisteredTool, ToolDescriptor, ToolResponse
from eu5miner_mcp.serializers import serialize_install_summary


@dataclass(frozen=True)
class InspectInstallRequest:
    install_root: Path | None = None
    mod_roots: tuple[Path, ...] = ()


def inspect_install(request: InspectInstallRequest) -> inspection.InstallSummary:
    return inspection.inspect_install(
        request.install_root,
        mod_roots=request.mod_roots or None,
    )


def describe_install_tools() -> tuple[ToolDescriptor, ...]:
    return (_INSPECT_INSTALL_TOOL.descriptor,)


def get_install_tools() -> tuple[RegisteredTool, ...]:
    return (_INSPECT_INSTALL_TOOL,)


def _invoke_inspect_install(arguments: Mapping[str, object] | None = None) -> ToolResponse:
    request = _parse_inspect_install_request(arguments)
    summary = inspect_install(request)
    return ToolResponse(
        text=inspection.format_install_summary(summary),
        structured_content=serialize_install_summary(summary),
    )


def _parse_inspect_install_request(
    arguments: Mapping[str, object] | None,
) -> InspectInstallRequest:
    mapping = arguments or {}
    return InspectInstallRequest(
        install_root=_optional_path(mapping.get("install_root")),
        mod_roots=_path_tuple(mapping.get("mod_roots")),
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


_INSPECT_INSTALL_TOOL = RegisteredTool(
    descriptor=ToolDescriptor(
        name="inspect-install",
        description="Summarize the discovered install roots and ordered content sources.",
        input_schema={
            "type": "object",
            "properties": {
                "install_root": {
                    "type": ["string", "null"],
                    "description": "Optional explicit EU5 install root.",
                },
                "mod_roots": {
                    "type": "array",
                    "description": "Optional extra mod roots layered after vanilla and DLC.",
                    "items": {"type": "string"},
                },
            },
        },
    ),
    invoke=_invoke_inspect_install,
)
