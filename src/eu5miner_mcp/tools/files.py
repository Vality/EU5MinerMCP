"""Read-only file-oriented MCP tools."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from eu5miner import ContentPhase, GameInstall, VirtualFilesystem
from eu5miner.vfs import MergedFile

from eu5miner_mcp.models import RegisteredTool, ToolDescriptor, ToolResponse
from eu5miner_mcp.serializers import serialize_file_listing


@dataclass(frozen=True)
class ListFilesRequest:
    phase: ContentPhase
    install_root: Path | None = None
    subpath: Path = Path("")
    limit: int = 20
    mod_roots: tuple[Path, ...] = ()


@dataclass(frozen=True)
class FileListing:
    phase: ContentPhase
    subpath: Path
    limit: int
    total_count: int
    files: tuple[MergedFile, ...]


def list_files(request: ListFilesRequest) -> FileListing:
    install = GameInstall.discover(request.install_root)
    vfs = VirtualFilesystem.from_install(
        install,
        mod_roots=list(request.mod_roots) if request.mod_roots else None,
    )
    merged_files = vfs.merge_phase(request.phase, request.subpath)
    return FileListing(
        phase=request.phase,
        subpath=request.subpath,
        limit=request.limit,
        total_count=len(merged_files),
        files=tuple(merged_files[: request.limit]),
    )


def describe_file_tools() -> tuple[ToolDescriptor, ...]:
    return (_LIST_FILES_TOOL.descriptor,)


def get_file_tools() -> tuple[RegisteredTool, ...]:
    return (_LIST_FILES_TOOL,)


def _invoke_list_files(arguments: Mapping[str, object] | None = None) -> ToolResponse:
    request = _parse_list_files_request(arguments)
    listing = list_files(request)
    return ToolResponse(
        text=_format_file_listing(listing),
        structured_content=serialize_file_listing(
            listing.phase,
            listing.subpath,
            listing.files,
            total_count=listing.total_count,
            limit=listing.limit,
        ),
    )


def _format_file_listing(listing: FileListing) -> str:
    display_subpath = listing.subpath if str(listing.subpath) not in {"", "."} else Path(".")
    lines = [f"Merged files for phase={listing.phase.value} subpath={display_subpath}"]
    for merged_file in listing.files:
        contributors = ", ".join(
            f"{contributor.source.kind.value}:{contributor.source.name}"
            for contributor in merged_file.contributors
        )
        lines.append(
            f"- {merged_file.relative_path} "
            f"winner={merged_file.winner.source.kind.value}:{merged_file.winner.source.name} "
            f"contributors=[{contributors}]"
        )
    lines.append(f"Count: {listing.total_count}")
    return "\n".join(lines)


def _parse_list_files_request(arguments: Mapping[str, object] | None) -> ListFilesRequest:
    mapping = arguments or {}
    phase_value = mapping.get("phase")
    if not isinstance(phase_value, str):
        raise TypeError("phase must be one of loading_screen, main_menu, or in_game")
    limit_value = mapping.get("limit", 20)
    if not isinstance(limit_value, int):
        raise TypeError("limit must be an integer")
    return ListFilesRequest(
        phase=ContentPhase(phase_value),
        install_root=_optional_path(mapping.get("install_root")),
        subpath=_path_or_default(mapping.get("subpath")),
        limit=limit_value,
        mod_roots=_path_tuple(mapping.get("mod_roots")),
    )


def _optional_path(value: object) -> Path | None:
    if value is None:
        return None
    return _coerce_path(value)


def _path_or_default(value: object) -> Path:
    if value is None:
        return Path("")
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


_LIST_FILES_TOOL = RegisteredTool(
    descriptor=ToolDescriptor(
        name="list-files",
        description="List merged visible files for one content phase and optional subpath.",
        input_schema={
            "type": "object",
            "properties": {
                "install_root": {
                    "type": ["string", "null"],
                    "description": "Optional explicit EU5 install root.",
                },
                "phase": {
                    "type": "string",
                    "enum": [phase.value for phase in ContentPhase],
                },
                "subpath": {
                    "type": "string",
                    "description": "Optional relative subpath under the chosen phase.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of merged files to return.",
                },
                "mod_roots": {
                    "type": "array",
                    "description": "Optional extra mod roots layered after vanilla and DLC.",
                    "items": {"type": "string"},
                },
            },
            "required": ["phase"],
        },
    ),
    invoke=_invoke_list_files,
)
