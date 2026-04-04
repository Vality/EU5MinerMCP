# Development Environment

## Recommended Setup

This repo is intended to follow the same centralized `uv` pattern as the core library.

Use:

- `%USERPROFILE%\.venvs\EU5MinerMCP`

Bootstrap with:

```powershell
.\scripts\setup-centralized-uv.ps1
```

## Validation

Run these before closing substantial work:

```powershell
uv run pytest
uv run ruff check .
uv run mypy src
uv build
```

The repo should remain buildable without a local EU5 install.
