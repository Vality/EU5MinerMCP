# Diplomacy Helper Tools Over Stable Grouped Packages

## Status

This spec is now partially landed as the first concrete step-2 MCP expansion slice.

## Objective

Define the first explicit step-2 MCP slice: add thin read-only diplomacy helper tools that consume the stable grouped-package helper surface in `eu5miner.domains.diplomacy` without turning this repo into a second graph or parser layer.

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
- build the grouped-package helper outputs already exposed by core: `build_war_flow_catalog` and `build_war_flow_report`
- register one new read-only tool: `report-diplomacy-war-flow`
- add serializer helpers and contract tests for the tool without changing the existing write-tool confirmation boundary

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

No other arguments are required in this first slice.

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

The broader diplomacy-graph report remains a follow-on slice rather than part of this first implementation step.

## Registry And Ordering

- register the new diplomacy tool through the shared registry so `build_server_runtime()`, `build_startup_message()`, and `describe-server` all reflect it automatically
- keep the diplomacy tool read-only and outside `_WRITE_TOOL_NAMES`

## Implementation Notes

- keep grouped-package loading and report shaping inside `tools/diplomacy.py`; do not spread diplomacy-specific parsing across the CLI or server bootstrap
- serializer helpers should convert grouped-package dataclasses into MCP-friendly dictionaries without renaming the core relationship categories into a new local vocabulary
- no cross-request cache is required for this first slice
- use synthetic install fixtures in tests rather than real EU5 content

## Out Of Scope

- new core-library APIs or grouped-package export changes
- arbitrary graph traversal or query languages in the MCP layer
- diplomacy helper tools for write workflows
- `mod_roots` support for the first helper-tool slice
- broader diplomacy-graph helper tooling for later slices
- helper tools for economy, government, religion, map, or other systems

## Acceptance Criteria

- the server registry includes `report-diplomacy-war-flow` as a read-only tool
- `eu5miner-mcp --describe` and `describe-server` expose the new tool names and descriptions through the shared runtime registry
- the tool accepts only the documented `install_root` argument and rejects unknown fields
- structured payloads include the explicit link arrays and missing-reference arrays listed above
- synthetic tests cover tool registration, input schemas, representative text output, and structured link entries with missing-reference coverage
- existing entity, system, mod, and runtime-description tools remain behaviorally unchanged

## Validation

- `uv run pytest`
- `uv run ruff check .`
- `uv run mypy src`
- `uv build`

## Sequencing Notes

This spec is the first concrete step-2 slice after tool-contract consolidation. If future helper-tool work expands to the broader diplomacy graph or to other systems, follow this narrow war-flow pattern first instead of inventing a generic helper-query abstraction up front.