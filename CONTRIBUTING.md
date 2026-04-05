# Contributing

Thanks for contributing to EU5MinerMCP.

## Scope

Keep this repository thin over the core `eu5miner` library.

- Put parser, VFS, and domain-model logic in `eu5miner`, not here.
- Prefer small, typed, test-backed changes.
- Keep the default workflow buildable without a local EU5 install.

## Setup

Recommended setup:

```powershell
.\scripts\setup-centralized-uv.ps1
```

One-off setup:

```powershell
uv sync --extra dev
```

## Validation

Run these before opening a pull request:

```powershell
uv run pytest
uv run ruff check .
uv run mypy src
uv build
```

## Pull Requests

- Describe the user-visible change and why it belongs in the MCP repo.
- Mention any dependency or contract changes with `eu5miner`.
- Include the validation commands you ran.