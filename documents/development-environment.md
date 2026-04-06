# Development Environment

## Recommended Setup

This repo is intended to follow the same centralized `uv` pattern as the core library.

Use:

- `%USERPROFILE%\.venvs\EU5MinerMCP`

Bootstrap with:

```powershell
.\scripts\setup-centralized-uv.ps1
```

## Workspace Support

The repository includes workspace settings in `.vscode/settings.json` that:

- set `UV_PROJECT_ENVIRONMENT` for integrated terminals
- point VS Code at `~/.venvs` when searching for interpreters
- default the interpreter path to `%USERPROFILE%\.venvs\EU5MinerMCP\Scripts\python.exe`

## Local Core Alignment

`pyproject.toml` pins the published dependency to the core `v0.6.0` release tag and also uses `[tool.uv.sources]` to resolve `eu5miner` from `../EU5Miner` inside this multi-repo workspace.

That local source override keeps MCP validation aligned with whichever sibling core checkout is present in the multi-repo workspace, even though the published package metadata is pinned to the coordinated release tag.

## Validation

Run these before closing substantial work:

```powershell
uv run pytest
uv run ruff check .
uv run mypy src
uv build
```

The repo should remain buildable without a local EU5 install.
