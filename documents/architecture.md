# EU5MinerMCP Architecture

## Role

This repo owns the MCP server surface.

It should not become a second parser implementation.

## Boundaries

- `eu5miner`: discovery, VFS, typed domain adapters, reports, and mod-planning behavior
- `eu5miner_mcp`: protocol glue, serializers, tool registration, and request or response handling

## First Principle

Start with a read-only shell and a narrow tool set. The server should expose stable library seams rather than inventing parallel data-access logic.
