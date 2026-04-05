# EU5MinerMCP

EU5MinerMCP is the dedicated MCP application repo for exposing `eu5miner` capabilities through a thin server surface.

The current surface is intentionally narrow: the first real read-only MCP slice wraps stable `eu5miner` inspection and VFS seams without duplicating parser or domain logic.

## Status

- The repo is scaffolded as a standalone Python application.
- The first real tool slice exposes install summary, merged file listing, supported systems, and system reports through an explicit typed server registry.
- Parsing, VFS, and domain logic should continue to live in the core `eu5miner` library.

For now the dependency resolves directly from the `EU5Miner` GitHub repo so CI can run before a package-registry release exists.

## Development

Initialize the centralized environment with:

```powershell
.\scripts\setup-centralized-uv.ps1
```

Run the standard checks:

```powershell
uv run pytest
uv run ruff check .
uv run mypy src
uv build
```

## Documentation

- Planning entrypoint: [ROADMAP.md](ROADMAP.md)
- Execution-ready specs: [documents/specs/README.md](documents/specs/README.md)
- Architecture notes: [documents/architecture.md](documents/architecture.md)
- Environment notes: [documents/development-environment.md](documents/development-environment.md)
