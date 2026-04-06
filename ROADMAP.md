# EU5MinerMCP Roadmap

This roadmap is intentionally narrow. The MCP repo should stay focused on server and tool-surface work, not on reimplementing library logic.

## Current Baseline

The current preview baseline now includes:

- repo and package alignment with the core library workflow
- a launchable typed MCP shell and CLI entrypoint
- registered install, file, system, and mod workflow tools over stable core seams
- a registry-backed `describe-server` self-description tool over the shared runtime metadata, stdio instructions, tool-name counts, and active tool descriptors
- read-only install inspection, merged-file listing, supported-system listing, and per-system reporting
- mod update planning and apply workflows surfaced through the MCP repo without duplicating parser or VFS logic

That means the next work should tighten and extend the shipped server surface, not restart repo or shell foundation work.

## Next Recommended Order

### 1. Tool Contract Consolidation

Goal: tighten the current tool surface before widening scope.

Use this slice for:

- clearer tool descriptors and argument expectations beyond the landed `describe-server` baseline
- more consistent response shaping across inspect, file, system, entity, and mod tools
- smaller contract refinements around the now-shipped runtime self-description payload rather than new server foundation work
- documentation that reflects the actual active tool registry

### 2. Server Boundary And Transport Readiness

Goal: keep the local shell easy to evolve into a fuller MCP server without promising more than is implemented.

Use this slice for:

- separation between local startup behavior, runtime self-description, and future transport concerns
- clearer server lifecycle boundaries
- tests that protect the current typed shell surface

### 3. Targeted Tool Expansion Only Where The Core Seam Exists

Goal: add new tools only when they are thin wrappers over an already-curated library surface.

Do not use this repo to invent parser or domain logic that belongs in `eu5miner`.

### 4. Mod Workflow Hardening

Goal: improve ergonomics and safety around the existing plan and apply workflows before taking on broader write scope.

## Rules

- parsing work stays in `eu5miner`
- transport and tool-surface work stays here
- the current tool registry is the baseline for follow-on work
- major follow-on slices should be backed by a spec in `documents/specs/`
