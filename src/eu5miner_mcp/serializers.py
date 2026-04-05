"""Serializer helpers for the first real read-only MCP tool slice."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from eu5miner import ContentPhase
from eu5miner.inspection import InstallSummary, SystemInfo, SystemReport
from eu5miner.vfs import MergedFile, SourceFile

from eu5miner_mcp.models import JSONValue


def serialize_status_message(
    message: str,
    *,
    tool_names: Sequence[str] = (),
) -> dict[str, JSONValue]:
    payload: dict[str, JSONValue] = {"status": message}
    if tool_names:
        payload["tools"] = list(tool_names)
    return payload


def serialize_install_summary(summary: InstallSummary) -> dict[str, JSONValue]:
    return {
        "root": str(summary.root),
        "game_dir": str(summary.game_dir),
        "dlc_dir": str(summary.dlc_dir),
        "mod_dir": str(summary.mod_dir),
        "phase_roots": [
            {"phase": phase_root.phase.value, "path": str(phase_root.path)}
            for phase_root in summary.phase_roots
        ],
        "sources": [
            {
                "name": source.name,
                "kind": source.kind.value,
                "root": str(source.root),
                "priority": source.priority,
                "replace_paths": list(source.replace_paths),
            }
            for source in summary.sources
        ],
    }


def serialize_system_list(systems: Sequence[SystemInfo]) -> dict[str, JSONValue]:
    return {
        "systems": [
            {"name": system.name, "description": system.description}
            for system in systems
        ]
    }


def serialize_system_report(report: SystemReport) -> dict[str, JSONValue]:
    return {
        "name": report.name,
        "description": report.description,
        "representative_keys": list(report.representative_keys),
        "summary_lines": list(report.summary_lines),
    }


def serialize_file_listing(
    phase: ContentPhase,
    subpath: Path,
    merged_files: Sequence[MergedFile],
    *,
    total_count: int,
    limit: int,
) -> dict[str, JSONValue]:
    return {
        "phase": phase.value,
        "subpath": str(_display_subpath(subpath)),
        "total_count": total_count,
        "returned_count": len(merged_files),
        "limit": limit,
        "files": [
            {
                "relative_path": str(merged_file.relative_path),
                "winner": _serialize_source_file(merged_file.winner),
                "contributors": [
                    _serialize_source_file(contributor)
                    for contributor in merged_file.contributors
                ],
            }
            for merged_file in merged_files
        ],
    }


def _serialize_source_file(source_file: SourceFile) -> dict[str, JSONValue]:
    return {
        "source_name": source_file.source.name,
        "source_kind": source_file.source.kind.value,
        "absolute_path": str(source_file.absolute_path),
    }


def _display_subpath(subpath: Path) -> Path:
    return subpath if str(subpath) not in {"", "."} else Path(".")
