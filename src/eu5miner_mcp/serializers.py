"""Serializer helpers for the first real read-only MCP tool slice."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from eu5miner import (
    BlockedModEmission,
    ContentPhase,
    ModUpdateAdvisory,
    ModUpdateWarning,
    ModUpdateWrite,
    PlannedModUpdate,
)
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


def serialize_planned_mod_update(update: PlannedModUpdate) -> dict[str, JSONValue]:
    return {
        "target_source_name": update.target_source_name,
        "phase": update.phase.value,
        "relative_root": str(update.relative_root),
        "root": str(update.root),
        "has_blockers": update.has_blockers,
        "replace_paths_to_add": list(update.replace_paths_to_add),
        "summary": {
            "intended_content_outputs": update.intended_content_write_count,
            "materialized_writes": len(update.writes),
            "metadata_writes": 1,
            "replace_path_additions": len(update.replace_paths_to_add),
            "blocked_intended_outputs": len(update.blocked_emissions),
            "warnings": len(update.warnings),
            "advisories": len(update.advisories),
        },
        "blocked_emissions": [
            _serialize_blocked_emission(blocked) for blocked in update.blocked_emissions
        ],
        "warnings": [_serialize_mod_update_warning(warning) for warning in update.warnings],
        "advisories": [
            _serialize_mod_update_advisory(advisory) for advisory in update.advisories
        ],
        "metadata_write": _serialize_mod_update_write(update.metadata_write),
        "content_writes": [
            _serialize_mod_update_write(write) for write in update.content_writes
        ],
    }


def _serialize_source_file(source_file: SourceFile) -> dict[str, JSONValue]:
    return {
        "source_name": source_file.source.name,
        "source_kind": source_file.source.kind.value,
        "absolute_path": str(source_file.absolute_path),
    }


def _serialize_blocked_emission(blocked: BlockedModEmission) -> dict[str, JSONValue]:
    return {
        "relative_path": str(blocked.relative_path),
        "blocker_source_names": list(blocked.blocker_source_names),
        "blocker_reasons": list(blocked.blocker_reasons),
    }


def _serialize_mod_update_warning(warning: ModUpdateWarning) -> dict[str, JSONValue]:
    payload: dict[str, JSONValue] = {
        "kind": warning.kind.value,
        "message": warning.message,
        "blocker_source_names": list(warning.blocker_source_names),
    }
    if warning.relative_path is not None:
        payload["relative_path"] = str(warning.relative_path)
    return payload


def _serialize_mod_update_advisory(advisory: ModUpdateAdvisory) -> dict[str, JSONValue]:
    payload: dict[str, JSONValue] = {
        "kind": advisory.kind.value,
        "message": advisory.message,
    }
    if advisory.raw_path is not None:
        payload["raw_path"] = advisory.raw_path
    return payload


def _serialize_mod_update_write(write: ModUpdateWrite) -> dict[str, JSONValue]:
    payload: dict[str, JSONValue] = {
        "path": str(write.path),
        "kind": write.kind.value,
        "content": write.content,
        "existed": write.existed,
    }
    if write.relative_path is not None:
        payload["relative_path"] = str(write.relative_path)
    if write.emission_kind is not None:
        payload["emission_kind"] = write.emission_kind.value
    return payload


def _display_subpath(subpath: Path) -> Path:
    return subpath if str(subpath) not in {"", "."} else Path(".")
