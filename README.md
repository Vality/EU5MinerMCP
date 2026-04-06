# EU5MinerMCP

EU5MinerMCP is an unofficial MCP application repo for exposing selected `eu5miner` capabilities through a thin server surface for Europa Universalis V installs and mods.

Release `0.5.0` is the first public preview release.

EU5MinerMCP is not affiliated with Paradox Interactive or the Europa Universalis franchise.

No game files, extracted assets, or other proprietary game content are included in this repository. The tool surface is intended to inspect a user's own local install and mod directories.

The current surface is intentionally narrow: the first real MCP slices wrap stable `eu5miner` inspection, VFS, entity-browsing, grouped helper, and mod workflow seams without duplicating parser or domain logic.

## Status

- The `0.5.x` line should be treated as a public preview rather than a stable `1.0` API.
- The current implementation is a typed MCP server shell over stable `eu5miner` inspection, VFS, entity-browsing, grouped helper, and mod workflow seams.
- The active registered tools are `inspect-install`, `list-files`, `list-systems`, `report-system`, `list-entity-systems`, `find-entity`, `describe-entity`, `list-entity-links`, `report-diplomacy-war-flow`, `report-diplomacy-graph`, `report-religion-links`, `plan-mod-update`, `apply-mod-update`, and `describe-server`.
- The CLI can still print the startup status line, describe the registered tools with `--describe`, and now serve the same registry over real stdio MCP transport with `--stdio`.
- MCP clients can now call `describe-server` to retrieve display, server, and package names, version, available transports, tool names and counts, write-tool names and counts, stdio instructions, and the live registered tool descriptors from the same shared registry the CLI and stdio transport use.
- The registry-backed runtime layer now fails fast if duplicate tool names, missing configured write tools, or mismatched `describe-server` descriptor ordering would otherwise publish inconsistent contract metadata.
- The grouped-helper seam now includes shipped diplomacy war-flow, diplomacy-graph, and religion link reports over representative install files only.
- Parsing, VFS, and domain logic should continue to live in the core `eu5miner` library.

The checked-in entity-browsing slice now depends on the current `eu5miner` mainline revision that includes the inspection entity seam.

The checked-in MCP repo now also reflects the completed step-2 grouped-helper breadth for the current preview line: `report-diplomacy-war-flow`, `report-diplomacy-graph`, and `report-religion-links` are the shipped helper-tool families, and that scope remains the explicit preview boundary for helper-specific MCP work. The current step-3 follow-on is coherence and release readiness: keep the full validation, build, and test gate green, keep docs truthful to the live registry, and avoid widening helper scope again before the next preview cut.

## Current Shell Behavior

The preview shell currently exposes a narrow tool registry:

- `describe-server`: describe the runtime metadata, transports, tool and write-tool counts, stdio instructions, confirmation requirements, and current registered MCP tool descriptors
- `inspect-install`: summarize discovered install roots and ordered content sources
- `list-files`: list merged visible files for one content phase and optional subpath
- `list-systems`: list the stable system reports exposed by the core inspection facade
- `report-system`: build a higher-level report for one supported system
- `list-entity-systems`: list the narrow browseable entity systems and their primary entity kinds
- `find-entity`: browse one supported entity system with an optional case-insensitive name filter
- `describe-entity`: return the summary, fields, and linked references for one named entity
- `list-entity-links`: return only the linked references for one named entity
- `report-diplomacy-war-flow`: build the core diplomacy war-flow helper report from representative install files
- `report-diplomacy-graph`: build the core diplomacy graph helper report from representative install files
- `report-religion-links`: build the core religion link helper report from representative install files
- `plan-mod-update`: plan a mod update and return both the formatted report and structured write metadata without applying changes
- `apply-mod-update`: apply a mod update and return both the formatted report and structured materialization result; requires `confirm=true` because it writes files under the target mod root

The entity-browsing slice is intentionally narrow. It wraps the core `eu5miner.inspection` browseable subset instead of inventing a generic graph API in the MCP layer, so the current real entity tools cover `economy` goods, `diplomacy` casus belli, `government` government types, `religion` religions, and `map` locations. For diplomacy, `describe-entity` and `list-entity-links` surface the same linked wargoal, peace-treaty, and country-interaction references already curated by the core inspection seam. The `list-entity-links` tool is only a convenience view over the same core reference list already returned by `describe-entity`; it does not introduce separate graph traversal behavior in the MCP layer.

The grouped-helper expansion stays similarly constrained. `report-diplomacy-war-flow`, `report-diplomacy-graph`, and `report-religion-links` read the representative install files already curated by `GameInstall.representative_files()`, then delegate report building to the stable grouped `eu5miner.domains.diplomacy` and `eu5miner.domains.religion` helper APIs. The MCP layer only shapes the tool contracts and serialization.

The mod workflow is also intentionally conservative at the MCP boundary: `plan-mod-update` remains the dry-run entrypoint, `apply-mod-update` requires an explicit `confirm=true` argument so hosted or interactive clients do not trigger writes accidentally, and `describe-server` exposes that same write-confirmation boundary together with the stdio startup instructions and active tool-name registry in a machine-readable form.

At this stage the package is best understood as a thin typed MCP-facing server and CLI entrypoint over a narrow inspection, entity-browsing, grouped-helper, runtime-description, and mod workflow surface, not as a broad production MCP integration.

## Development

This repository is stored under OneDrive, so the recommended setup is to keep the `uv` environment outside the synced tree.

Initialize or refresh the centralized environment with:

```powershell
.\scripts\setup-centralized-uv.ps1
```

That script points `UV_PROJECT_ENVIRONMENT` at `%USERPROFILE%\.venvs\EU5MinerMCP` and runs `uv sync --extra dev` there.

If you need a one-off local setup instead, install development dependencies with `uv`:

```powershell
uv sync --extra dev
```

Run the standard checks:

```powershell
$env:UV_PROJECT_ENVIRONMENT = "$env:USERPROFILE\.venvs\EU5MinerMCP"
uv run pytest
uv run ruff check .
uv run mypy src
uv build
```

## CLI

The package currently ships a thin preview CLI:

```powershell
eu5miner-mcp
eu5miner-mcp --describe
eu5miner-mcp --stdio
```

## Documentation

- Planning entrypoint: [ROADMAP.md](ROADMAP.md)
- Execution-ready specs: [documents/specs/README.md](documents/specs/README.md)
- Architecture notes: [documents/architecture.md](documents/architecture.md)
- Environment notes: [documents/development-environment.md](documents/development-environment.md)
