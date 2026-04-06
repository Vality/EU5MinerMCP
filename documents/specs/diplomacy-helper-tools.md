# Diplomacy Helper Tools Over Stable Grouped Packages

## Status

This spec now tracks the shipped war-flow slice, its shipped diplomacy-graph follow-on, and the narrow pattern future helper-tool work should preserve.

## Objective

Define the first explicit step-2 MCP slices: add thin read-only diplomacy helper tools that consume the stable grouped-package helper surface in `eu5miner.domains.diplomacy` without turning this repo into a second graph or parser layer.

## Architectural Context

The current MCP surface is centered on `eu5miner.inspection`, entity browsing, VFS file listing, and mod workflows. That remains the baseline.

This slice is the first deliberate targeted expansion over a grouped package because core already exposes a stable diplomacy helper family that is richer than the current inspection facade and narrow enough to wrap directly.

Use only stable core seams that are already intended for downstream use:

- `eu5miner.GameInstall`
- `eu5miner.VirtualFilesystem`
- `eu5miner.ContentPhase`
- `eu5miner.domains.diplomacy`

Do not import internal core modules from `eu5miner.domains.diplomacy.*`.

## Scope

- add one MCP-local diplomacy tool module at `src/eu5miner_mcp/tools/diplomacy.py`
- load representative diplomacy files from the selected install through `GameInstall.representative_files()`
- parse those files through the grouped-package parser functions exposed by `eu5miner.domains.diplomacy`
- build the grouped-package helper outputs already exposed by core: `build_war_flow_catalog`, `build_war_flow_report`, `build_diplomacy_graph_catalog`, and `build_diplomacy_graph_report`
- register the shipped read-only tools: `report-diplomacy-war-flow` and `report-diplomacy-graph`
- add serializer helpers and contract tests for those tools without changing the existing write-tool confirmation boundary
- keep the slices limited to one concrete helper family and one explicit request schema before considering broader diplomacy-helper expansion

## Target Files

- `src/eu5miner_mcp/tools/diplomacy.py`
- `src/eu5miner_mcp/tools/__init__.py`
- `src/eu5miner_mcp/server.py`
- `src/eu5miner_mcp/serializers.py`
- `tests/test_server_shell.py`

## Tool Contract

### `report-diplomacy-war-flow`

Purpose: build the stable grouped-package war-flow helper report for one install.

Input schema:

- `install_root`: optional string or null, matching the existing install-backed tool pattern

No other arguments are required in these helper-tool slices.

Text response should include:

- helper name and representative-file provenance
- the representative file keys and resolved file paths used for the report
- explicit link listings for casus belli to wargoal, peace treaty to casus belli, and peace treaty to subject type relationships
- explicit missing-reference summaries for wargoals, casus belli, and subject types

Structured response should include:

- `representative_files` with key and resolved path entries
- `summary` object with link and missing-reference counts
- `casus_belli_wargoal_links`
- `peace_treaty_casus_belli_links`
- `peace_treaty_subject_type_links`
- `missing_wargoal_references`
- `missing_casus_belli_references`
- `missing_subject_type_references`

Each link entry should preserve the grouped-package edge shape as `source_name` plus `referenced_names`.

### `report-diplomacy-graph`

Purpose: build the stable grouped-package diplomacy-graph helper report for one install.

Input schema:

- `install_root`: optional string or null, matching the existing install-backed tool pattern

Text response should include:

- helper name and representative-file provenance
- the representative file keys and resolved file paths used for the report
- explicit link listings for peace treaty to casus belli, peace treaty to subject type, country interaction to casus belli, country interaction to subject type, country interaction to country interaction, and character interaction to subject type relationships
- explicit missing-reference summaries for casus belli, subject types, and country interactions

Structured response should include:

- `representative_files` with key and resolved path entries
- `summary` object with link and missing-reference counts
- `peace_treaty_casus_belli_links`
- `peace_treaty_subject_type_links`
- `country_interaction_casus_belli_links`
- `country_interaction_subject_type_links`
- `country_interaction_links`
- `character_interaction_subject_type_links`
- `missing_casus_belli_references`
- `missing_subject_type_references`
- `missing_country_interaction_references`

Each link entry should preserve the grouped-package edge shape as `source_name` plus `referenced_names`.

## Registry And Ordering

- register the diplomacy tools through the shared registry so `build_server_runtime()`, `build_startup_message()`, and `describe-server` all reflect them automatically
- keep the diplomacy tools read-only and outside `_WRITE_TOOL_NAMES`

## Implementation Notes

- keep grouped-package loading and report shaping inside `tools/diplomacy.py`; do not spread diplomacy-specific parsing across the CLI or server bootstrap
- serializer helpers should convert grouped-package dataclasses into MCP-friendly dictionaries without renaming the core relationship categories into a new local vocabulary
- no cross-request cache is required for these slices
- use synthetic install fixtures in tests rather than real EU5 content
- keep the tools read-only and intentionally separate from the existing entity-browsing and mod workflow contracts

## Out Of Scope

- new core-library APIs or grouped-package export changes
- arbitrary graph traversal or query languages in the MCP layer
- diplomacy helper tools for write workflows
- `mod_roots` support for these helper-tool slices
- additional diplomacy helper families beyond the shipped war-flow and diplomacy-graph reports
- helper tools for economy, government, religion, map, or other systems

## Acceptance Criteria

- the server registry includes `report-diplomacy-war-flow` and `report-diplomacy-graph` as read-only tools
- `eu5miner-mcp --describe` and `describe-server` expose the new tool names and descriptions through the shared runtime registry
- the tools accept only the documented `install_root` argument and reject unknown fields
- structured payloads include the explicit link arrays and missing-reference arrays listed above for both helper reports
- synthetic tests cover tool registration, input schemas, representative text output, and structured link entries with missing-reference coverage
- existing entity, system, mod, and runtime-description tools remain behaviorally unchanged

## Validation

- `uv run pytest`
- `uv run ruff check .`
- `uv run mypy src`
- `uv build`

## Sequencing Notes

This spec covers the first concrete step-2 slice after tool-contract consolidation and its one-tool diplomacy-graph follow-on. If future helper-tool work expands to other diplomacy helper families or other systems, follow this same narrow tool-by-tool pattern instead of inventing a generic helper-query abstraction up front.