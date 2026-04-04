# EU5MinerMCP Agent Guide

## Purpose

This repository is for the MCP server application that sits on top of the core `eu5miner` library.

Agents working here should optimize for:

- keeping parser, VFS, and domain logic in `eu5miner`
- thin, typed server or tool wrappers in this repo
- small, test-backed changes that validate without a local EU5 install by default

## Start Here

Read these documents first:

1. `README.md`
2. `ROADMAP.md`
3. `documents/specs/README.md`
4. `documents/architecture.md`
5. `documents/development-environment.md`

## Working Norms

- Use the core library as the source of truth for data access.
- Keep the MCP surface thin and explicit.
- Prefer read-only inspection tools before write workflows.
- Keep hosted CI sufficient for the default workflow.
