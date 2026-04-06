"""Serializer helpers for the current MCP tool slice."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, cast

from eu5miner import (
    AppliedModUpdate,
    AppliedModWrite,
    BlockedModEmission,
    ContentPhase,
    ModUpdateAdvisory,
    ModUpdateWarning,
    ModUpdateWrite,
    PlannedModUpdate,
)
from eu5miner.domains.diplomacy import (
    DiplomacyGraphReport,
    DiplomacyReferenceEdge,
    WarFlowReport,
    WarReferenceEdge,
)
from eu5miner.domains.religion import ReligionReferenceEdge, ReligionReport
from eu5miner.inspection import (
    EntityDetail,
    EntityReference,
    EntitySummary,
    EntitySystemInfo,
    InstallSummary,
    SystemInfo,
    SystemReport,
)
from eu5miner.vfs import MergedFile, SourceFile

from eu5miner_mcp.models import JSONValue, ToolDescriptor


class ServerRuntimeLike(Protocol):
    @property
    def display_name(self) -> str: ...

    @property
    def package_name(self) -> str: ...

    @property
    def server_name(self) -> str: ...

    @property
    def version(self) -> str: ...

    @property
    def transports(self) -> tuple[str, ...]: ...

    @property
    def tool_names(self) -> tuple[str, ...]: ...

    @property
    def write_tool_names(self) -> tuple[str, ...]: ...

    @property
    def tool_count(self) -> int: ...

    @property
    def write_tool_count(self) -> int: ...

    def build_stdio_instructions(self) -> str: ...


def serialize_status_message(
    message: str,
    *,
    tool_names: Sequence[str] = (),
) -> dict[str, JSONValue]:
    payload: dict[str, JSONValue] = {"status": message}
    if tool_names:
        payload["tools"] = list(tool_names)
    return payload


def serialize_server_description(
    runtime: ServerRuntimeLike,
    descriptors: Sequence[ToolDescriptor],
    *,
    status_message: str,
) -> dict[str, JSONValue]:
    descriptor_names = _validate_server_description_contract(runtime, descriptors)
    write_tool_names = set(runtime.write_tool_names)
    return {
        "status": status_message,
        "display_name": runtime.display_name,
        "package_name": runtime.package_name,
        "server_name": runtime.server_name,
        "version": runtime.version,
        "transports": list(runtime.transports),
        "tool_names": list(descriptor_names),
        "tool_count": runtime.tool_count,
        "write_tool_names": list(runtime.write_tool_names),
        "write_tool_count": runtime.write_tool_count,
        "stdio_instructions": runtime.build_stdio_instructions(),
        "tools": [
            {
                "name": descriptor.name,
                "description": descriptor.description,
                "requires_confirmation": descriptor.name in write_tool_names,
                "input_schema": cast(JSONValue, descriptor.input_schema),
            }
            for descriptor in descriptors
        ],
    }


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


def serialize_diplomacy_war_flow_report(
    report: WarFlowReport,
    *,
    representative_files: Sequence[tuple[str, Path]],
) -> dict[str, JSONValue]:
    return {
        "representative_files": [
            {"key": key, "path": str(path)} for key, path in representative_files
        ],
        "summary": {
            "casus_belli_wargoal_links": len(report.casus_belli_wargoal_links),
            "peace_treaty_casus_belli_links": len(report.peace_treaty_casus_belli_links),
            "peace_treaty_subject_type_links": len(report.peace_treaty_subject_type_links),
            "missing_wargoal_references": len(report.missing_wargoal_references),
            "missing_casus_belli_references": len(report.missing_casus_belli_references),
            "missing_subject_type_references": len(report.missing_subject_type_references),
        },
        "casus_belli_wargoal_links": [
            _serialize_war_reference_edge(edge) for edge in report.casus_belli_wargoal_links
        ],
        "peace_treaty_casus_belli_links": [
            _serialize_war_reference_edge(edge)
            for edge in report.peace_treaty_casus_belli_links
        ],
        "peace_treaty_subject_type_links": [
            _serialize_war_reference_edge(edge)
            for edge in report.peace_treaty_subject_type_links
        ],
        "missing_wargoal_references": list(report.missing_wargoal_references),
        "missing_casus_belli_references": list(report.missing_casus_belli_references),
        "missing_subject_type_references": list(report.missing_subject_type_references),
    }


def serialize_diplomacy_graph_report(
    report: DiplomacyGraphReport,
    *,
    representative_files: Sequence[tuple[str, Path]],
) -> dict[str, JSONValue]:
    return {
        "representative_files": [
            {"key": key, "path": str(path)} for key, path in representative_files
        ],
        "summary": {
            "peace_treaty_casus_belli_links": len(report.peace_treaty_casus_belli_links),
            "peace_treaty_subject_type_links": len(report.peace_treaty_subject_type_links),
            "country_interaction_casus_belli_links": len(
                report.country_interaction_casus_belli_links
            ),
            "country_interaction_subject_type_links": len(
                report.country_interaction_subject_type_links
            ),
            "country_interaction_links": len(report.country_interaction_links),
            "character_interaction_subject_type_links": len(
                report.character_interaction_subject_type_links
            ),
            "missing_casus_belli_references": len(report.missing_casus_belli_references),
            "missing_subject_type_references": len(report.missing_subject_type_references),
            "missing_country_interaction_references": len(
                report.missing_country_interaction_references
            ),
        },
        "peace_treaty_casus_belli_links": [
            _serialize_diplomacy_reference_edge(edge)
            for edge in report.peace_treaty_casus_belli_links
        ],
        "peace_treaty_subject_type_links": [
            _serialize_diplomacy_reference_edge(edge)
            for edge in report.peace_treaty_subject_type_links
        ],
        "country_interaction_casus_belli_links": [
            _serialize_diplomacy_reference_edge(edge)
            for edge in report.country_interaction_casus_belli_links
        ],
        "country_interaction_subject_type_links": [
            _serialize_diplomacy_reference_edge(edge)
            for edge in report.country_interaction_subject_type_links
        ],
        "country_interaction_links": [
            _serialize_diplomacy_reference_edge(edge)
            for edge in report.country_interaction_links
        ],
        "character_interaction_subject_type_links": [
            _serialize_diplomacy_reference_edge(edge)
            for edge in report.character_interaction_subject_type_links
        ],
        "missing_casus_belli_references": list(report.missing_casus_belli_references),
        "missing_subject_type_references": list(report.missing_subject_type_references),
        "missing_country_interaction_references": list(
            report.missing_country_interaction_references
        ),
    }


def serialize_religion_report(
    report: ReligionReport,
    *,
    representative_files: Sequence[tuple[str, Path]],
) -> dict[str, JSONValue]:
    return {
        "representative_files": [
            {"key": key, "path": str(path)} for key, path in representative_files
        ],
        "summary": {
            "religion_aspect_links": len(report.religion_aspect_links),
            "religion_faction_links": len(report.religion_faction_links),
            "religion_focus_links": len(report.religion_focus_links),
            "religion_school_links": len(report.religion_school_links),
            "religion_holy_site_links": len(report.religion_holy_site_links),
            "religion_figure_links": len(report.religion_figure_links),
            "missing_religious_faction_references": len(
                report.missing_religious_faction_references
            ),
            "missing_religious_focus_references": len(
                report.missing_religious_focus_references
            ),
            "missing_religious_school_references": len(
                report.missing_religious_school_references
            ),
        },
        "religion_aspect_links": [
            _serialize_religion_reference_edge(edge) for edge in report.religion_aspect_links
        ],
        "religion_faction_links": [
            _serialize_religion_reference_edge(edge) for edge in report.religion_faction_links
        ],
        "religion_focus_links": [
            _serialize_religion_reference_edge(edge) for edge in report.religion_focus_links
        ],
        "religion_school_links": [
            _serialize_religion_reference_edge(edge) for edge in report.religion_school_links
        ],
        "religion_holy_site_links": [
            _serialize_religion_reference_edge(edge)
            for edge in report.religion_holy_site_links
        ],
        "religion_figure_links": [
            _serialize_religion_reference_edge(edge) for edge in report.religion_figure_links
        ],
        "missing_religious_faction_references": list(
            report.missing_religious_faction_references
        ),
        "missing_religious_focus_references": list(
            report.missing_religious_focus_references
        ),
        "missing_religious_school_references": list(
            report.missing_religious_school_references
        ),
    }


def serialize_entity_system_list(
    systems: Sequence[EntitySystemInfo],
) -> dict[str, JSONValue]:
    return {
        "systems": [
            {
                "name": system.name,
                "description": system.description,
                "primary_entity_kind": system.primary_entity_kind,
            }
            for system in systems
        ]
    }


def serialize_entity_search_result(
    entities: Sequence[EntitySummary],
    *,
    system: str,
    total_count: int,
    limit: int,
    name_contains: str | None,
) -> dict[str, JSONValue]:
    payload: dict[str, JSONValue] = {
        "system": system,
        "total_count": total_count,
        "returned_count": len(entities),
        "limit": limit,
        "entities": [_serialize_entity_summary(entity) for entity in entities],
    }
    if name_contains is not None:
        payload["name_contains"] = name_contains
    return payload


def serialize_entity_detail(detail: EntityDetail) -> dict[str, JSONValue]:
    return {
        "summary": _serialize_entity_summary(detail.summary),
        "fields": [
            {"name": field.name, "value": _serialize_browse_value(field.value)}
            for field in detail.fields
        ],
        "references": [_serialize_entity_reference(reference) for reference in detail.references],
    }


def serialize_entity_links(detail: EntityDetail) -> dict[str, JSONValue]:
    return {
        "system": detail.summary.system,
        "entity_kind": detail.summary.entity_kind,
        "name": detail.summary.name,
        "reference_count": len(detail.references),
        "references": [_serialize_entity_reference(reference) for reference in detail.references],
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


def serialize_applied_mod_update(update: AppliedModUpdate) -> dict[str, JSONValue]:
    return {
        "target_source_name": update.plan.target_source_name,
        "phase": update.plan.phase.value,
        "relative_root": str(update.plan.relative_root),
        "root": str(update.plan.root),
        "has_blockers": update.plan.has_blockers,
        "replace_paths_to_add": list(update.plan.replace_paths_to_add),
        "summary": {
            "created_directories": len(update.created_directories),
            "created_writes": update.created_write_count,
            "updated_writes": update.updated_write_count,
            "unchanged_writes": update.unchanged_write_count,
            "blocked_intended_outputs": len(update.blocked_emissions),
            "warnings": len(update.warnings),
            "advisories": len(update.advisories),
        },
        "created_directories": [str(path) for path in update.created_directories],
        "blocked_emissions": [
            _serialize_blocked_emission(blocked) for blocked in update.blocked_emissions
        ],
        "warnings": [_serialize_mod_update_warning(warning) for warning in update.warnings],
        "advisories": [
            _serialize_mod_update_advisory(advisory) for advisory in update.advisories
        ],
        "metadata_write": _serialize_applied_mod_write(update.metadata_write),
        "content_writes": [
            _serialize_applied_mod_write(write) for write in update.content_writes
        ],
    }


def _serialize_entity_summary(summary: EntitySummary) -> dict[str, JSONValue]:
    payload: dict[str, JSONValue] = {
        "system": summary.system,
        "entity_kind": summary.entity_kind,
        "name": summary.name,
    }
    if summary.group is not None:
        payload["group"] = summary.group
    if summary.description is not None:
        payload["description"] = summary.description
    return payload


def _serialize_entity_reference(reference: EntityReference) -> dict[str, JSONValue]:
    return {
        "role": reference.role,
        "system": reference.system,
        "entity_kind": reference.entity_kind,
        "target_name": reference.target_name,
    }


def _serialize_war_reference_edge(edge: WarReferenceEdge) -> dict[str, JSONValue]:
    return {
        "source_name": edge.source_name,
        "referenced_names": list(edge.referenced_names),
    }


def _serialize_diplomacy_reference_edge(
    edge: DiplomacyReferenceEdge,
) -> dict[str, JSONValue]:
    return {
        "source_name": edge.source_name,
        "referenced_names": list(edge.referenced_names),
    }


def _serialize_religion_reference_edge(
    edge: ReligionReferenceEdge,
) -> dict[str, JSONValue]:
    return {
        "source_name": edge.source_name,
        "referenced_names": list(edge.referenced_names),
    }


def _serialize_browse_value(
    value: str | int | float | bool | tuple[str, ...],
) -> JSONValue:
    if isinstance(value, tuple):
        return list(value)
    return value


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


def _serialize_applied_mod_write(write: AppliedModWrite) -> dict[str, JSONValue]:
    payload: dict[str, JSONValue] = {
        "path": str(write.path),
        "kind": write.kind.value,
        "status": write.status.value,
    }
    if write.relative_path is not None:
        payload["relative_path"] = str(write.relative_path)
    if write.emission_kind is not None:
        payload["emission_kind"] = write.emission_kind.value
    return payload


def _display_subpath(subpath: Path) -> Path:
    return subpath if str(subpath) not in {"", "."} else Path(".")


def _validate_server_description_contract(
    runtime: ServerRuntimeLike,
    descriptors: Sequence[ToolDescriptor],
) -> tuple[str, ...]:
    if runtime.tool_count != len(runtime.tool_names):
        raise ValueError("Runtime tool_count does not match runtime tool_names")
    if runtime.write_tool_count != len(runtime.write_tool_names):
        raise ValueError(
            "Runtime write_tool_count does not match runtime write_tool_names"
        )

    descriptor_names = tuple(descriptor.name for descriptor in descriptors)
    duplicate_names = _find_duplicate_names(descriptor_names)
    if duplicate_names:
        raise ValueError(
            "Duplicate MCP tool names in descriptor registry: "
            + ", ".join(duplicate_names)
        )
    if descriptor_names != runtime.tool_names:
        raise ValueError("Server descriptor registry does not match runtime tool_names")

    missing_write_tool_names = [
        name for name in runtime.write_tool_names if name not in descriptor_names
    ]
    if missing_write_tool_names:
        raise ValueError(
            "Runtime write_tool_names are not present in descriptors: "
            + ", ".join(missing_write_tool_names)
        )

    return descriptor_names


def _find_duplicate_names(names: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for name in names:
        if name in seen and name not in duplicates:
            duplicates.append(name)
        seen.add(name)
    return tuple(duplicates)
