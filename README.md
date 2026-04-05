# EU5MinerMCP

EU5MinerMCP is an unofficial MCP application repo for exposing selected `eu5miner` capabilities through a thin server surface for Europa Universalis V installs and mods.

Release `0.5.0` is the first public preview release.

EU5MinerMCP is not affiliated with Paradox Interactive or the Europa Universalis franchise.

No game files, extracted assets, or other proprietary game content are included in this repository. The tool surface is intended to inspect a user's own local install and mod directories.

The current surface is intentionally narrow: the first real read-only MCP slice wraps stable `eu5miner` inspection and VFS seams without duplicating parser or domain logic.

## Status

- The `0.5.x` line should be treated as a public preview rather than a stable `1.0` API.
- The current implementation is a local typed read-only MCP shell over stable `eu5miner` inspection and VFS seams.
- The active registered tools are `inspect-install`, `list-files`, `list-systems`, and `report-system`.
- The CLI currently prints the startup status line and can describe the registered tools with `--describe`.
- Full protocol transport, richer entity tools, and write-capable workflows are still future work.
- Parsing, VFS, and domain logic should continue to live in the core `eu5miner` library.

For the `0.5.0` preview line, the dependency is pinned directly to the released `EU5Miner` GitHub tag `v0.5.0` so the downstream MCP shell stays aligned to the first public core preview contract.

## Current Shell Behavior

The preview shell currently exposes a narrow read-only registry:

- `inspect-install`: summarize discovered install roots and ordered content sources
- `list-files`: list merged visible files for one content phase and optional subpath
- `list-systems`: list the stable system reports exposed by the core inspection facade
- `report-system`: build a higher-level report for one supported system

At this stage the package is best understood as a typed MCP-facing shell and CLI entrypoint over those read-only operations, not as a full transport-integrated production server.

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
```

## Documentation

- Planning entrypoint: [ROADMAP.md](ROADMAP.md)
- Execution-ready specs: [documents/specs/README.md](documents/specs/README.md)
- Architecture notes: [documents/architecture.md](documents/architecture.md)
- Environment notes: [documents/development-environment.md](documents/development-environment.md)
