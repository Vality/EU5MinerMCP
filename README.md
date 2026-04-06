# EU5MinerMCP

EU5MinerMCP is an unofficial MCP application repo for exposing selected `eu5miner` capabilities through a thin server surface for Europa Universalis V installs and mods.

Release `0.5.0` is the first public preview release.

EU5MinerMCP is not affiliated with Paradox Interactive or the Europa Universalis franchise.

No game files, extracted assets, or other proprietary game content are included in this repository. The tool surface is intended to inspect a user's own local install and mod directories.

The current surface is intentionally narrow: the first real MCP slices wrap stable `eu5miner` inspection, VFS, entity-browsing, and mod workflow seams without duplicating parser or domain logic.

## Status

- The `0.5.x` line should be treated as a public preview rather than a stable `1.0` API.
- The current implementation is a typed MCP server shell over stable `eu5miner` inspection, VFS, entity-browsing, and mod workflow seams.
- The active registered tools are `inspect-install`, `list-files`, `list-systems`, `report-system`, `list-entity-systems`, `find-entity`, `describe-entity`, `list-entity-links`, `plan-mod-update`, and `apply-mod-update`.
- The CLI can still print the startup status line, describe the registered tools with `--describe`, and now serve the same registry over real stdio MCP transport with `--stdio`.
- Broader cross-entity graph tooling is still future work.
- Parsing, VFS, and domain logic should continue to live in the core `eu5miner` library.

The checked-in entity-browsing slice now depends on the current `eu5miner` mainline revision that includes the inspection entity seam.

## Current Shell Behavior

The preview shell currently exposes a narrow tool registry:

- `inspect-install`: summarize discovered install roots and ordered content sources
- `list-files`: list merged visible files for one content phase and optional subpath
- `list-systems`: list the stable system reports exposed by the core inspection facade
- `report-system`: build a higher-level report for one supported system
- `list-entity-systems`: list the narrow browseable entity systems and their primary entity kinds
- `find-entity`: browse one supported entity system with an optional case-insensitive name filter
- `describe-entity`: return the summary, fields, and linked references for one named entity
- `list-entity-links`: return only the linked references for one named entity
- `plan-mod-update`: plan a mod update and return both the formatted report and structured write metadata without applying changes
- `apply-mod-update`: apply a mod update and return both the formatted report and structured materialization result; requires `confirm=true` because it writes files under the target mod root

The entity-browsing slice is intentionally narrow. It wraps the core `eu5miner.inspection` browseable subset instead of inventing a generic graph API in the MCP layer, so the current real entity tools cover `economy` goods, `government` government types, `religion` religions, and `map` locations. The `list-entity-links` tool is only a convenience view over the same core reference list already returned by `describe-entity`; it does not introduce separate graph traversal behavior in the MCP layer.

The mod workflow is also intentionally conservative at the MCP boundary: `plan-mod-update` remains the dry-run entrypoint, and `apply-mod-update` now requires an explicit `confirm=true` argument so hosted or interactive clients do not trigger writes accidentally.

At this stage the package is best understood as a thin typed MCP-facing server and CLI entrypoint over a narrow inspection, entity-browsing, and mod workflow surface, not as a broad production MCP integration.

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
