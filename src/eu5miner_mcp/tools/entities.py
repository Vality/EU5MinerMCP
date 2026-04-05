"""Placeholder entity-oriented MCP tool descriptors."""

from eu5miner_mcp.models import ToolDescriptor


def describe_entity_tools() -> tuple[ToolDescriptor, ...]:
    return (
        ToolDescriptor(
            name="find-entity",
            description="Placeholder entity lookup tool for a later slice.",
            input_schema={"type": "object", "properties": {}},
        ),
        ToolDescriptor(
            name="describe-entity",
            description="Placeholder entity detail tool for a later slice.",
            input_schema={"type": "object", "properties": {}},
        ),
        ToolDescriptor(
            name="list-entity-links",
            description="Placeholder entity link tool for a later slice.",
            input_schema={"type": "object", "properties": {}},
        ),
    )
