# Agent Instructions

This file applies to any agentic coding tool working in this repository:
Claude Code, GitHub Copilot, Hermes, or any other assistant. It is not
specific to a single vendor.

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

```bash
uv run pytest
uv run ruff check .
uv run mypy src
uv build
```

## Tool-Specific Notes

- **Claude Code**: this file is auto-loaded when present. `AGENTS.md` is also recognized as a project-level instruction file.
- **GitHub Copilot**: this file is loaded by Copilot Coding Agent. `AGENTS.md` may also be picked up depending on the IDE.
- **Hermes**: this file is loaded by `hermes` when working in the repo directory. `AGENTS.md` is read for cross-agent conventions.
