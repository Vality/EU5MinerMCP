# Spec Index

These specs are the execution layer under `ROADMAP.md`.

## Current Status

The checked-in specs describe the landed server-shell foundation and the shipped narrow grouped-helper slices.

## Landed Baseline Spec

- `read-only-server.md`: completed foundation for the launchable MCP shell, CLI entrypoint, and initial repo structure
- `diplomacy-helper-tools.md`: shipped step-2 diplomacy helper slices for `report-diplomacy-war-flow` and `report-diplomacy-graph`
- `religion-helper-tools.md`: shipped step-2 religion helper slice for `report-religion-links`

Since those specs were written, the repo has moved beyond shell-only status and now exposes install, file, system, entity-browsing, diplomacy helper, mod workflow, and runtime self-description tools.

The current implementation also hardens the registry-backed self-description seam: runtime metadata, configured write-tool names, and exported `describe-server` descriptors are now expected to stay in lockstep rather than silently tolerating registry drift.

The first explicit step-2 expansion specs are now also implemented in deliberately narrow form: `diplomacy-helper-tools.md` tracks the shipped read-only war-flow and diplomacy-graph helper tools over the stable `eu5miner.domains.diplomacy` grouped package, and `religion-helper-tools.md` tracks the shipped read-only religion link helper tool over the stable `eu5miner.domains.religion` grouped package.

Step 1 in the roadmap still focuses on tool-contract consolidation, but the first checked step-2 slice is now explicit instead of remaining a generic future-expansion placeholder.

That contract-consistency work also includes keeping the MCP entity-browsing surface synced to the core curated browseable subset rather than restating its system list independently; the current subset includes `economy`, `diplomacy`, `government`, `religion`, and `map`.

## Next Follow-On Direction

- keep future step-2 slices as narrow as the shipped diplomacy and religion helper tools, instead of widening into generic helper-query infrastructure
- future grouped helper specs should follow the same fixed representative-file and grouped-package boundary used by `diplomacy-helper-tools.md` and `religion-helper-tools.md`

## Rules

- keep parsing and domain logic in `eu5miner`
- keep new MCP work thin over stable core library seams
- make hosted CI sufficient for the default workflow
