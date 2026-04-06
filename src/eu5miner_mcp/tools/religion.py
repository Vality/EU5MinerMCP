"""Read-only religion helper MCP tools over stable core grouped-package seams."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from eu5miner import GameInstall
from eu5miner.domains.religion import (
    ReligionReferenceEdge,
    ReligionReport,
    build_religion_catalog,
    build_religion_report,
    parse_holy_site_document,
    parse_religion_document,
    parse_religious_aspect_document,
    parse_religious_faction_document,
    parse_religious_figure_document,
    parse_religious_focus_document,
    parse_religious_school_document,
)

from eu5miner_mcp.models import (
    RegisteredTool,
    ToolDescriptor,
    ToolResponse,
    closed_object_schema,
    reject_unknown_arguments,
)
from eu5miner_mcp.serializers import serialize_religion_report

_RELIGION_KEYS = (
    "religion_sample",
    "religion_secondary_sample",
    "religion_muslim_sample",
    "religion_tonal_sample",
    "religion_dharmic_sample",
)
_RELIGIOUS_ASPECT_KEYS = (
    "religious_aspect_sample",
    "religious_aspect_secondary_sample",
)
_RELIGIOUS_SCHOOL_KEYS = (
    "religious_school_sample",
    "religious_school_secondary_sample",
)
_RELIGIOUS_FIGURE_KEYS = (
    "religious_figure_sample",
    "religious_figure_secondary_sample",
)
_HOLY_SITE_KEYS = (
    "holy_site_sample",
    "holy_site_secondary_sample",
)
_RELIGION_REPORT_REPRESENTATIVE_KEYS = (
    *_RELIGION_KEYS,
    *_RELIGIOUS_ASPECT_KEYS,
    "religious_faction_sample",
    "religious_focus_sample",
    *_RELIGIOUS_SCHOOL_KEYS,
    *_RELIGIOUS_FIGURE_KEYS,
    *_HOLY_SITE_KEYS,
)


@dataclass(frozen=True)
class ReportReligionLinksRequest:
    install_root: Path | None = None


@dataclass(frozen=True)
class ReligionLinksResult:
    representative_files: tuple[tuple[str, Path], ...]
    report: ReligionReport


def report_religion_links(
    request: ReportReligionLinksRequest,
) -> ReligionLinksResult:
    install = GameInstall.discover(request.install_root)
    representative_files = _resolve_representative_files(
        install,
        _RELIGION_REPORT_REPRESENTATIVE_KEYS,
        tool_name="report-religion-links",
    )
    representative_lookup = dict(representative_files)
    report = build_religion_report(
        build_religion_catalog(
            religion_documents=tuple(
                parse_religion_document(_read_text(representative_lookup[key]))
                for key in _RELIGION_KEYS
            ),
            religious_aspect_documents=tuple(
                parse_religious_aspect_document(_read_text(representative_lookup[key]))
                for key in _RELIGIOUS_ASPECT_KEYS
            ),
            religious_faction_documents=(
                parse_religious_faction_document(
                    _read_text(representative_lookup["religious_faction_sample"])
                ),
            ),
            religious_focus_documents=(
                parse_religious_focus_document(
                    _read_text(representative_lookup["religious_focus_sample"])
                ),
            ),
            religious_school_documents=tuple(
                parse_religious_school_document(_read_text(representative_lookup[key]))
                for key in _RELIGIOUS_SCHOOL_KEYS
            ),
            religious_figure_documents=tuple(
                parse_religious_figure_document(_read_text(representative_lookup[key]))
                for key in _RELIGIOUS_FIGURE_KEYS
            ),
            holy_site_documents=tuple(
                parse_holy_site_document(_read_text(representative_lookup[key]))
                for key in _HOLY_SITE_KEYS
            ),
        )
    )
    return ReligionLinksResult(
        representative_files=representative_files,
        report=report,
    )


def describe_religion_tools() -> tuple[ToolDescriptor, ...]:
    return (_REPORT_RELIGION_LINKS_TOOL.descriptor,)


def get_religion_tools() -> tuple[RegisteredTool, ...]:
    return (_REPORT_RELIGION_LINKS_TOOL,)


def _invoke_report_religion_links(
    arguments: Mapping[str, object] | None = None,
) -> ToolResponse:
    request = _parse_report_religion_links_request(arguments)
    result = report_religion_links(request)
    lines = ["Religion link report from representative install files:"]
    lines.append("Representative files:")
    lines.extend(f"- {key}: {path}" for key, path in result.representative_files)
    lines.extend(
        _format_reference_edges(
            "Religion -> aspect links",
            result.report.religion_aspect_links,
        )
    )
    lines.extend(
        _format_reference_edges(
            "Religion -> faction links",
            result.report.religion_faction_links,
        )
    )
    lines.extend(
        _format_reference_edges(
            "Religion -> focus links",
            result.report.religion_focus_links,
        )
    )
    lines.extend(
        _format_reference_edges(
            "Religion -> school links",
            result.report.religion_school_links,
        )
    )
    lines.extend(
        _format_reference_edges(
            "Religion -> holy site links",
            result.report.religion_holy_site_links,
        )
    )
    lines.extend(
        _format_reference_edges(
            "Religion -> figure links",
            result.report.religion_figure_links,
        )
    )
    lines.extend(
        _format_missing_references(
            "Missing religious faction references",
            result.report.missing_religious_faction_references,
        )
    )
    lines.extend(
        _format_missing_references(
            "Missing religious focus references",
            result.report.missing_religious_focus_references,
        )
    )
    lines.extend(
        _format_missing_references(
            "Missing religious school references",
            result.report.missing_religious_school_references,
        )
    )
    return ToolResponse(
        text="\n".join(lines),
        structured_content=serialize_religion_report(
            result.report,
            representative_files=result.representative_files,
        ),
    )


def _parse_report_religion_links_request(
    arguments: Mapping[str, object] | None,
) -> ReportReligionLinksRequest:
    mapping = arguments or {}
    reject_unknown_arguments(
        mapping,
        tool_name="report-religion-links",
        allowed_fields={"install_root"},
    )
    return ReportReligionLinksRequest(
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
            f"{tool_name} requires representative religion files: "
            + ", ".join(missing_files)
        )
    return representative_files


def _format_reference_edges(
    title: str,
    edges: Sequence[ReligionReferenceEdge],
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


_REPORT_RELIGION_LINKS_TOOL = RegisteredTool(
    descriptor=ToolDescriptor(
        name="report-religion-links",
        description=(
            "Build the religion link helper report over representative install "
            "files using the core grouped religion package."
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
    invoke=_invoke_report_religion_links,
)