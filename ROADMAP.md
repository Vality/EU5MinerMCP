# EU5MinerMCP Roadmap

This roadmap is intentionally narrow. The MCP repo should stay focused on server and tool-surface work, not on reimplementing library logic.

## Current Order

### 1. Foundation And Repo Alignment

Goal: establish the repo, package, CI, docs, and server entrypoint.

### 2. Read-Only MCP Shell

Goal: start a minimal server shell that can expose placeholder status over stable `eu5miner` imports.

### 3. Read-Only Tool Surface

Goal: add install, file, entity, and report lookup tools backed by the library.

### 4. Write And Planning Workflows

Goal: only after the library seam is stable enough, add mod-planning and write-capable tools.

## Rules

- parsing work stays in `eu5miner`
- transport and tool-surface work stays here
- major feature slices should be backed by a spec in `documents/specs/`
