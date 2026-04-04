# Spec: Read-Only MCP Shell

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
