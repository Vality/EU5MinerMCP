# EU5MinerMCP Roadmap

This roadmap is intentionally narrow. The MCP repo should stay focused on server and tool-surface work, not on reimplementing library logic.

## Current Baseline

The current preview baseline now includes:

- repo and package alignment with the core library workflow
- a launchable typed MCP shell and CLI entrypoint
- registered install, file, system, and mod workflow tools over stable core seams
- a first targeted diplomacy helper tool over the grouped `eu5miner.domains.diplomacy` seam and representative install files
- a second targeted diplomacy helper tool over the same grouped diplomacy seam and representative install files
- a first targeted religion helper tool over the grouped `eu5miner.domains.religion` seam and representative install files
- a registry-backed `describe-server` self-description tool over the shared runtime metadata, stdio instructions, tool-name counts, and active tool descriptors
- read-only install inspection, merged-file listing, supported-system listing, and per-system reporting
- read-only diplomacy war-flow, diplomacy-graph, and religion link reporting over representative install files without MCP-local parser logic
- mod update planning and apply workflows surfaced through the MCP repo without duplicating parser or VFS logic

That means the next work should tighten and extend the shipped server surface, not restart repo or shell foundation work.

## Next Recommended Order

### 1. Tool Contract Consolidation

Goal: tighten the current tool surface before widening scope.

Use this slice for:

- clearer tool descriptors and argument expectations beyond the landed `describe-server` baseline
- more consistent response shaping across inspect, file, system, entity, and mod tools
- entity-browsing contract coverage that stays aligned with the core curated browseable subset instead of drifting when that subset changes
- registry-backed validation so runtime names, write-tool configuration, and exported descriptor lists cannot silently drift apart
- smaller contract refinements around the now-shipped runtime self-description payload rather than new server foundation work
- documentation that reflects the actual active tool registry

### 2. Grouped Helper Tools Over Stable Grouped Packages

Goal: make step 2 explicit as a thin MCP wrapper over the stable helper surfaces already curated in the core grouped packages.

Reference patterns: `documents/specs/diplomacy-helper-tools.md`, `documents/specs/religion-helper-tools.md`

Use this slice for:

- read-only grouped helper tools over `eu5miner.domains.diplomacy` and `eu5miner.domains.religion`
- thin install-backed loading through stable core seams such as `GameInstall` and grouped-package parsers and helper builders
- explicit machine-readable serializers for one concrete helper family before adding helper tools for other systems
- contract tests that keep tool names, schemas, and response shapes explicit

The first checked step-2 implementation slice in this category is `report-diplomacy-war-flow`, and it should remain the reference pattern for future helper-tool follow-ons.

The shipped narrow follow-ons in this category are `report-diplomacy-graph` and `report-religion-links`, each with the same thin install-loading and registry pattern as `report-diplomacy-war-flow`.

Boundary preserved by that shipped follow-on:

- add exactly one new read-only tool: `report-diplomacy-graph`
- accept only the existing optional `install_root` request argument
- load the fixed representative diplomacy file set already curated by `GameInstall.representative_files()` for war-flow inputs plus country and character interactions
- serialize only the diplomacy-graph edge categories and missing-reference categories already exposed by `eu5miner.domains.diplomacy.DiplomacyGraphReport`
- keep `report-diplomacy-war-flow` unchanged rather than merging both reports into one tool

Do not use this slice to invent ad hoc graph traversal, parser logic, or a broad helper-query framework in the MCP layer.

Boundary preserved by the shipped religion follow-on:

- add exactly one new read-only tool: `report-religion-links`
- accept only the existing optional `install_root` request argument
- load the fixed representative religion file set already curated by `GameInstall.representative_files()` across religion, religious aspect, religious faction, religious focus, religious school, religious figure, and holy site files
- serialize only the religion-link edge categories and missing-reference categories already exposed by `eu5miner.domains.religion.ReligionReport`
- keep the diplomacy tools unchanged rather than merging grouped helper families into one generic report tool

### 3. Server Boundary And Transport Readiness

Goal: keep the local shell easy to evolve into a fuller MCP server without promising more than is implemented.

Use this slice for:

- separation between local startup behavior, runtime self-description, and future transport concerns
- clearer server lifecycle boundaries
- tests that protect the current typed shell surface

### 4. Targeted Tool Expansion Only Where The Core Seam Exists

Goal: add new tools only when they are thin wrappers over an already-curated library surface.

Do not use this repo to invent parser or domain logic that belongs in `eu5miner`.

### 5. Mod Workflow Hardening

Goal: improve ergonomics and safety around the existing plan and apply workflows before taking on broader write scope.

## Rules

- parsing work stays in `eu5miner`
- transport and tool-surface work stays here
- the current tool registry is the baseline for follow-on work
- major follow-on slices should be backed by a spec in `documents/specs/`
