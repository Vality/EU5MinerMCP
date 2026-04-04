# Copilot Instructions

Use this repository as a typed Python MCP application built on top of the `eu5miner` library.

## Read First

Start with:

1. `README.md`
2. `AGENTS.md`
3. `ROADMAP.md`
4. `documents/specs/README.md`
5. `documents/development-environment.md`

## Working Norms

- Keep parser, VFS, and domain-model logic in the core `eu5miner` library.
- Prefer thin server and tool integrations over duplicating backend behavior.
- Keep work buildable and testable without a local EU5 install.

## Validation

Run these before closing substantial work:

```powershell
uv run pytest
uv run ruff check .
uv run mypy src
uv build
```
