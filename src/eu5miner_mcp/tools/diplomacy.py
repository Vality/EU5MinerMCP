"""Read-only diplomacy helper MCP tools over stable core grouped-package seams."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from eu5miner import GameInstall
from eu5miner.domains.diplomacy import (
    DiplomacyGraphReport,
    DiplomacyReferenceEdge,
    WarFlowReport,
    WarReferenceEdge,
    build_diplomacy_graph_catalog,
    build_diplomacy_graph_report,
    build_war_flow_catalog,
    build_war_flow_report,
    parse_casus_belli_document,
    parse_character_interaction_document,
    parse_country_interaction_document,
    parse_peace_treaty_document,
    parse_subject_type_document,
    parse_wargoal_document,
)

from eu5miner_mcp.models import (
    RegisteredTool,
    ToolDescriptor,
    ToolResponse,
    closed_object_schema,
    reject_unknown_arguments,
)
from eu5miner_mcp.serializers import (
    serialize_diplomacy_graph_report,
    serialize_diplomacy_war_flow_report,
)

_CASUS_BELLI_KEYS = (
    "casus_belli_sample",
    "casus_belli_secondary_sample",
    "casus_belli_subject_sample",
    "casus_belli_religious_sample",
    "casus_belli_trade_sample",
)
_PEACE_TREATY_KEYS = (
    "peace_treaty_sample",
    "peace_treaty_secondary_sample",
    "peace_treaty_special_sample",
)
_SUBJECT_TYPE_KEYS = (
    "subject_type_sample",
    "subject_type_secondary_sample",
    "subject_type_colonial_sample",
    "subject_type_hre_sample",
    "subject_type_special_sample",
)
_COUNTRY_INTERACTION_KEYS = (
    "country_interaction_sample",
    "country_interaction_secondary_sample",
)
_CHARACTER_INTERACTION_KEYS = (
    "character_interaction_sample",
    "character_interaction_secondary_sample",
)
_WAR_FLOW_REPRESENTATIVE_KEYS = (
    *_CASUS_BELLI_KEYS,
    "wargoal_sample",
    *_PEACE_TREATY_KEYS,
    *_SUBJECT_TYPE_KEYS,
)
_DIPLOMACY_GRAPH_REPRESENTATIVE_KEYS = (
    *_WAR_FLOW_REPRESENTATIVE_KEYS,
    *_COUNTRY_INTERACTION_KEYS,
    *_CHARACTER_INTERACTION_KEYS,
)


@dataclass(frozen=True)
class ReportDiplomacyWarFlowRequest:
    install_root: Path | None = None


@dataclass(frozen=True)
class DiplomacyWarFlowResult:
    representative_files: tuple[tuple[str, Path], ...]
    report: WarFlowReport


@dataclass(frozen=True)
class ReportDiplomacyGraphRequest:
    install_root: Path | None = None


@dataclass(frozen=True)
class DiplomacyGraphResult:
    representative_files: tuple[tuple[str, Path], ...]
    report: DiplomacyGraphReport


def report_diplomacy_war_flow(
    request: ReportDiplomacyWarFlowRequest,
) -> DiplomacyWarFlowResult:
    install = GameInstall.discover(request.install_root)
    representative_files = _resolve_representative_files(
        install,
        _WAR_FLOW_REPRESENTATIVE_KEYS,
        tool_name="report-diplomacy-war-flow",
    )
    representative_lookup = dict(representative_files)
    report = build_war_flow_report(
        build_war_flow_catalog(
            casus_belli_documents=tuple(
                parse_casus_belli_document(_read_text(representative_lookup[key]))
                for key in _CASUS_BELLI_KEYS
            ),
            wargoal_documents=(
                parse_wargoal_document(_read_text(representative_lookup["wargoal_sample"])),
            ),
            peace_treaty_documents=tuple(
                parse_peace_treaty_document(_read_text(representative_lookup[key]))
                for key in _PEACE_TREATY_KEYS
            ),
            subject_type_documents=tuple(
                parse_subject_type_document(_read_text(representative_lookup[key]))
                for key in _SUBJECT_TYPE_KEYS
            ),
        )
    )
    return DiplomacyWarFlowResult(
        representative_files=representative_files,
        report=report,
    )


def report_diplomacy_graph(
    request: ReportDiplomacyGraphRequest,
) -> DiplomacyGraphResult:
    install = GameInstall.discover(request.install_root)
    representative_files = _resolve_representative_files(
        install,
        _DIPLOMACY_GRAPH_REPRESENTATIVE_KEYS,
        tool_name="report-diplomacy-graph",
    )
    representative_lookup = dict(representative_files)
    report = build_diplomacy_graph_report(
        build_diplomacy_graph_catalog(
            casus_belli_documents=tuple(
                parse_casus_belli_document(_read_text(representative_lookup[key]))
                for key in _CASUS_BELLI_KEYS
            ),
            wargoal_documents=(
                parse_wargoal_document(_read_text(representative_lookup["wargoal_sample"])),
            ),
            peace_treaty_documents=tuple(
                parse_peace_treaty_document(_read_text(representative_lookup[key]))
                for key in _PEACE_TREATY_KEYS
            ),
            subject_type_documents=tuple(
                parse_subject_type_document(_read_text(representative_lookup[key]))
                for key in _SUBJECT_TYPE_KEYS
            ),
            country_interaction_documents=tuple(
                parse_country_interaction_document(_read_text(representative_lookup[key]))
                for key in _COUNTRY_INTERACTION_KEYS
            ),
            character_interaction_documents=tuple(
                parse_character_interaction_document(_read_text(representative_lookup[key]))
                for key in _CHARACTER_INTERACTION_KEYS
            ),
        )
    )
    return DiplomacyGraphResult(
        representative_files=representative_files,
        report=report,
    )


def describe_diplomacy_tools() -> tuple[ToolDescriptor, ...]:
    return (
        _REPORT_DIPLOMACY_WAR_FLOW_TOOL.descriptor,
        _REPORT_DIPLOMACY_GRAPH_TOOL.descriptor,
    )


def get_diplomacy_tools() -> tuple[RegisteredTool, ...]:
    return (
        _REPORT_DIPLOMACY_WAR_FLOW_TOOL,
        _REPORT_DIPLOMACY_GRAPH_TOOL,
    )


def _invoke_report_diplomacy_war_flow(
    arguments: Mapping[str, object] | None = None,
) -> ToolResponse:
    request = _parse_report_diplomacy_war_flow_request(arguments)
    result = report_diplomacy_war_flow(request)
    lines = ["Diplomacy war-flow report from representative install files:"]
    lines.append("Representative files:")
    lines.extend(
        f"- {key}: {path}" for key, path in result.representative_files
    )
    lines.extend(
        _format_reference_edges(
            "Casus belli -> wargoal links",
            result.report.casus_belli_wargoal_links,
        )
    )
    lines.extend(
        _format_reference_edges(
            "Peace treaties -> casus belli links",
            result.report.peace_treaty_casus_belli_links,
        )
    )
    lines.extend(
        _format_reference_edges(
            "Peace treaties -> subject type links",
            result.report.peace_treaty_subject_type_links,
        )
    )
    lines.extend(
        _format_missing_references(
            "Missing wargoal references",
            result.report.missing_wargoal_references,
        )
    )
    lines.extend(
        _format_missing_references(
            "Missing casus belli references",
            result.report.missing_casus_belli_references,
        )
    )
    lines.extend(
        _format_missing_references(
            "Missing subject type references",
            result.report.missing_subject_type_references,
        )
    )
    return ToolResponse(
        text="\n".join(lines),
        structured_content=serialize_diplomacy_war_flow_report(
            result.report,
            representative_files=result.representative_files,
        ),
    )


def _invoke_report_diplomacy_graph(
    arguments: Mapping[str, object] | None = None,
) -> ToolResponse:
    request = _parse_report_diplomacy_graph_request(arguments)
    result = report_diplomacy_graph(request)
    lines = ["Diplomacy graph report from representative install files:"]
    lines.append("Representative files:")
    lines.extend(f"- {key}: {path}" for key, path in result.representative_files)
    lines.extend(
        _format_reference_edges(
            "Peace treaties -> casus belli links",
            result.report.peace_treaty_casus_belli_links,
        )
    )
    lines.extend(
        _format_reference_edges(
            "Peace treaties -> subject type links",
            result.report.peace_treaty_subject_type_links,
        )
    )
    lines.extend(
        _format_reference_edges(
            "Country interactions -> casus belli links",
            result.report.country_interaction_casus_belli_links,
        )
    )
    lines.extend(
        _format_reference_edges(
            "Country interactions -> subject type links",
            result.report.country_interaction_subject_type_links,
        )
    )
    lines.extend(
        _format_reference_edges(
            "Country interactions -> country interaction links",
            result.report.country_interaction_links,
        )
    )
    lines.extend(
        _format_reference_edges(
            "Character interactions -> subject type links",
            result.report.character_interaction_subject_type_links,
        )
    )
    lines.extend(
        _format_missing_references(
            "Missing casus belli references",
            result.report.missing_casus_belli_references,
        )
    )
    lines.extend(
        _format_missing_references(
            "Missing subject type references",
            result.report.missing_subject_type_references,
        )
    )
    lines.extend(
        _format_missing_references(
            "Missing country interaction references",
            result.report.missing_country_interaction_references,
        )
    )
    return ToolResponse(
        text="\n".join(lines),
        structured_content=serialize_diplomacy_graph_report(
            result.report,
            representative_files=result.representative_files,
        ),
    )


def _parse_report_diplomacy_war_flow_request(
    arguments: Mapping[str, object] | None,
) -> ReportDiplomacyWarFlowRequest:
    mapping = arguments or {}
    reject_unknown_arguments(
        mapping,
        tool_name="report-diplomacy-war-flow",
        allowed_fields={"install_root"},
    )
    return ReportDiplomacyWarFlowRequest(
        install_root=_optional_path(mapping.get("install_root")),
    )


def _parse_report_diplomacy_graph_request(
    arguments: Mapping[str, object] | None,
) -> ReportDiplomacyGraphRequest:
    mapping = arguments or {}
    reject_unknown_arguments(
        mapping,
        tool_name="report-diplomacy-graph",
        allowed_fields={"install_root"},
    )
    return ReportDiplomacyGraphRequest(
        install_root=_optional_path(mapping.get("install_root")),
    )


def _resolve_representative_files(
    install: GameInstall,
    keys: Sequence[str],
    *,
    tool_name: str,
) -> tuple[tuple[str, Path], ...]:
    representative_file_map = install.representative_files()
    representative_files = tuple((key, representative_file_map[key]) for key in keys)
    missing_files = [
        f"{key}={path}"
        for key, path in representative_files
        if not path.exists()
    ]
    if missing_files:
        raise FileNotFoundError(
            f"{tool_name} requires representative diplomacy files: "
            + ", ".join(missing_files)
        )
    return representative_files


def _format_reference_edges(
    title: str,
    edges: Sequence[WarReferenceEdge | DiplomacyReferenceEdge],
) -> list[str]:
    lines = [f"{title}:"]
    if not edges:
        lines.append("- (none)")
        return lines
    for edge in edges:
        lines.append(f"- {edge.source_name} -> {', '.join(edge.referenced_names)}")
    return lines


def _format_missing_references(title: str, references: Sequence[str]) -> list[str]:
    lines = [f"{title}:"]
    if not references:
        lines.append("- (none)")
        return lines
    lines.extend(f"- {reference}" for reference in references)
    return lines


def _optional_path(value: object) -> Path | None:
    if value is None:
        return None
    return _coerce_path(value)


def _coerce_path(value: object) -> Path:
    if isinstance(value, Path):
        return value
    if isinstance(value, str):
        return Path(value)
    raise TypeError(f"Expected a path-like string, got {type(value).__name__}")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


_REPORT_DIPLOMACY_WAR_FLOW_TOOL = RegisteredTool(
    descriptor=ToolDescriptor(
        name="report-diplomacy-war-flow",
        description=(
            "Build the diplomacy war-flow helper report over representative install "
            "files using the core grouped diplomacy package."
        ),
        input_schema=closed_object_schema(
            properties={
                "install_root": {
                    "type": ["string", "null"],
                    "description": "Optional explicit EU5 install root.",
                }
            }
        ),
    ),
    invoke=_invoke_report_diplomacy_war_flow,
)


_REPORT_DIPLOMACY_GRAPH_TOOL = RegisteredTool(
    descriptor=ToolDescriptor(
        name="report-diplomacy-graph",
        description=(
            "Build the diplomacy graph helper report over representative install "
            "files using the core grouped diplomacy package."
        ),
        input_schema=closed_object_schema(
            properties={
                "install_root": {
                    "type": ["string", "null"],
                    "description": "Optional explicit EU5 install root.",
                }
            }
        ),
    ),
    invoke=_invoke_report_diplomacy_graph,
)