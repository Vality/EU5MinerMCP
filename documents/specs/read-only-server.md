# Spec: Read-Only MCP Shell

## Status

This baseline spec has already landed and is now superseded by the current main-branch tool surface.

The repo no longer stops at placeholder startup or placeholder tool descriptors. The live shell now registers real install, file, system, entity-browsing, and mod workflow tools over stable `eu5miner` library seams.

## Objective

Create the first launchable MCP server shell for the repo.

## In Scope

- server entrypoint
- placeholder startup message
- lightweight serializer surface
- placeholder tool modules organized by concern
- smoke tests for startup behavior

## Out Of Scope

- write-capable mod tools
- bespoke parser logic
- install-backed browsing that requires real game data

## Acceptance Criteria

- the server process starts cleanly
- the repo validates in hosted CI
- the shell proves the dependency on the core library
