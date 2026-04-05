# Spec Index

These specs are the execution layer under `ROADMAP.md`.

## Current Status

The checked-in spec describes the baseline repo and server-shell work that has already landed.

## Landed Baseline Spec

- `read-only-server.md`: completed foundation for the launchable MCP shell, CLI entrypoint, and initial repo structure

Since that spec was written, the repo has moved beyond shell-only status and now exposes install, file, system, and mod workflow tools.

No new follow-on MCP spec is checked in yet.

The next spec for this repo should scope one concrete server or tool-surface refinement slice over the current implementation rather than reopening foundation work.

## Rules

- keep parsing and domain logic in `eu5miner`
- keep new MCP work thin over stable core library seams
- make hosted CI sufficient for the default workflow
