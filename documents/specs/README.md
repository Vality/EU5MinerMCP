# Spec Index

These specs are the execution layer under `ROADMAP.md`.

## Current Status

The checked-in spec describes the baseline repo and server-shell work that has already landed.

## Landed Baseline Spec

- `read-only-server.md`: completed foundation for the launchable MCP shell, CLI entrypoint, and initial repo structure

Since that spec was written, the repo has moved beyond shell-only status and now exposes install, file, system, entity-browsing, mod workflow, and runtime self-description tools.

The current implementation also hardens the registry-backed self-description seam: runtime metadata, configured write-tool names, and exported `describe-server` descriptors are now expected to stay in lockstep rather than silently tolerating registry drift.

No new follow-on MCP spec is checked in yet.

The next spec for this repo should scope one concrete server or tool-surface refinement slice over the current implementation rather than reopening foundation work; the registry-backed self-description slice is already present and now includes explicit runtime names, counts, and stdio instructions, so the next focus should stay on contract consistency or another thin wrapper over an existing core seam.

## Rules

- keep parsing and domain logic in `eu5miner`
- keep new MCP work thin over stable core library seams
- make hosted CI sufficient for the default workflow
