# Spec Index

These specs are the execution layer under `ROADMAP.md`.

## Current Status

The checked-in specs describe the landed server-shell foundation and the shipped narrow grouped-helper slices.

The checked-in docs now also reflect the coordinated `0.6.0` preview surface after that shipped step-2 breadth. The current focus remains operational and release-oriented rather than another helper-surface expansion.

## Landed Baseline Spec

- `read-only-server.md`: completed foundation for the launchable MCP shell, CLI entrypoint, and initial repo structure
- `diplomacy-helper-tools.md`: shipped step-2 diplomacy helper slices for `report-diplomacy-war-flow` and `report-diplomacy-graph`
- `religion-helper-tools.md`: shipped step-2 religion helper slice for `report-religion-links`

Since those specs were written, the repo has moved beyond shell-only status and now exposes install, file, system, entity-browsing, diplomacy helper, mod workflow, and runtime self-description tools.

The current implementation also hardens the registry-backed self-description seam: runtime metadata, configured write-tool names, and exported `describe-server` descriptors are now expected to stay in lockstep rather than silently tolerating registry drift.

The first explicit step-2 expansion specs are now also implemented in deliberately narrow form: `diplomacy-helper-tools.md` tracks the shipped read-only war-flow and diplomacy-graph helper tools over the stable `eu5miner.domains.diplomacy` grouped package, and `religion-helper-tools.md` tracks the shipped read-only religion link helper tool over the stable `eu5miner.domains.religion` grouped package.

The checked-in repo now reflects both the narrow tool-contract baseline and the shipped step-2 grouped-helper breadth through diplomacy and religion. After the `0.6.0` preview cut, the next major phase is continued validation, build, test, and contract-readiness work over that surface.

That contract-consistency work also includes keeping the MCP entity-browsing surface synced to the core curated browseable subset rather than restating its system list independently; the current subset includes `economy`, `diplomacy`, `government`, `religion`, and `map`.

## Current Release-Readiness Focus

- keep the registry, docs, and validation gate aligned with the actual shipped `0.6.0` tool surface while release-readiness work proceeds
- keep future grouped helper specs as narrow as the shipped diplomacy and religion helper tools instead of widening into generic helper-query infrastructure

## Rules

- keep parsing and domain logic in `eu5miner`
- keep new MCP work thin over stable core library seams
- make hosted CI sufficient for the default workflow
