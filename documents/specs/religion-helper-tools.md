# Religion Helper Tool Over Stable Grouped Packages

## Status

This spec tracks the shipped `report-religion-links` slice and the narrow helper-tool pattern it is expected to preserve.

## Objective

Add one thin read-only religion helper tool that consumes the stable grouped-package helper surface in `eu5miner.domains.religion` without turning this repo into a second parser or graph layer.

## Architectural Context

The current MCP surface remains centered on `eu5miner.inspection`, entity browsing, VFS file listing, the shipped diplomacy helper tools, runtime self-description, and mod workflows.

This slice stays deliberately as narrow as the diplomacy helper pattern and uses only stable downstream seams already intended for grouped-package consumers:

- `eu5miner.GameInstall`
- `eu5miner.domains.religion`

Do not import internal core modules from `eu5miner.domains.religion.*`.

## Scope

- add one MCP-local religion tool module at `src/eu5miner_mcp/tools/religion.py`
- load representative religion-family files from the selected install through `GameInstall.representative_files()`
- parse those files through the grouped-package parser functions exposed by `eu5miner.domains.religion`
- build grouped-package helper outputs through `build_religion_catalog` and `build_religion_report`
- register exactly one new read-only tool: `report-religion-links`
- add serializer helpers and contract tests for that tool without changing the existing write-tool confirmation boundary

## Target Files

- `src/eu5miner_mcp/tools/religion.py`
- `src/eu5miner_mcp/tools/__init__.py`
- `src/eu5miner_mcp/server.py`
- `src/eu5miner_mcp/serializers.py`
- `tests/test_server_shell.py`

## Tool Contract

### `report-religion-links`

Purpose: build the stable grouped-package religion link helper report for one install.

Input schema:

- `install_root`: optional string or null, matching the existing install-backed tool pattern

No other arguments are required in this helper-tool slice.

Representative keys:

- `religion_sample`
- `religion_secondary_sample`
- `religion_muslim_sample`
- `religion_tonal_sample`
- `religion_dharmic_sample`
- `religious_aspect_sample`
- `religious_aspect_secondary_sample`
- `religious_faction_sample`
- `religious_focus_sample`
- `religious_school_sample`
- `religious_school_secondary_sample`
- `religious_figure_sample`
- `religious_figure_secondary_sample`
- `holy_site_sample`
- `holy_site_secondary_sample`

Text response should include:

- helper name and representative-file provenance
- the representative file keys and resolved file paths used for the report
- explicit link listings for religion to aspect, faction, focus, school, holy site, and figure relationships
- explicit missing-reference summaries for religious factions, religious focuses, and religious schools

Structured response should include:

- `representative_files` with key and resolved path entries
- `summary` object with link counts and missing-reference counts
- `religion_aspect_links`
- `religion_faction_links`
- `religion_focus_links`
- `religion_school_links`
- `religion_holy_site_links`
- `religion_figure_links`
- `missing_religious_faction_references`
- `missing_religious_focus_references`
- `missing_religious_school_references`

Each link entry preserves the grouped-package edge shape as `source_name` plus `referenced_names`.

## Registry And Ordering

- register the religion tool through the shared registry so `build_server_runtime()`, startup messaging, and `describe-server` all reflect it automatically
- keep the religion tool read-only and outside `_WRITE_TOOL_NAMES`
- preserve the shipped ordering and behavior of existing install, file, system, entity, diplomacy, mod, and runtime-description tools

## Implementation Notes

- keep grouped-package loading and report shaping inside `tools/religion.py`; do not spread religion-specific parsing across the CLI or server bootstrap
- serializer helpers should convert grouped-package dataclasses into MCP-friendly dictionaries without renaming the core relationship categories into a new local vocabulary
- no cross-request cache is required for this slice
- use synthetic install fixtures in tests rather than real EU5 content
- keep the tool intentionally separate from the inspection-backed `religion` entity tools; this slice surfaces grouped-package relationship reports, not a wider browse API

## Out Of Scope

- new core-library APIs or grouped-package export changes
- holy-site-specific helper tools, holy-site drill-down tools, or a second religion helper tool in the same slice
- arbitrary graph traversal, search filters, or generic helper-query languages in the MCP layer
- `mod_roots` support for this helper-tool slice
- helper tools for economy, government, map, or other systems

## Acceptance Criteria

- the server registry includes `report-religion-links` as a read-only tool
- `eu5miner-mcp --describe` and `describe-server` expose the new tool name and description through the shared runtime registry
- the tool accepts only the documented `install_root` argument and rejects unknown fields
- structured payloads include the explicit link arrays and missing-reference arrays listed above
- synthetic tests cover tool registration, input schema, representative text output, and structured link entries with missing-reference coverage
- existing install, file, system, entity, diplomacy, mod, and runtime-description tools remain behaviorally unchanged

## Validation

- `uv run pytest`
- `uv run ruff check .`
- `uv run mypy src`
- `uv build`

## Sequencing Notes

Future helper-tool work should follow this same one-tool grouped-package pattern instead of inventing a generic helper-query abstraction up front.