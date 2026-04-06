"""Shared typed models for the MCP server surface."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

type JSONScalar = None | bool | int | float | str
type JSONValue = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]
type JSONSchema = dict[str, object]


def closed_object_schema(
    *,
    properties: Mapping[str, object] | None = None,
    required: Sequence[str] = (),
    any_of: Sequence[Mapping[str, object]] = (),
) -> JSONSchema:
    schema: JSONSchema = {
        "type": "object",
        "properties": dict(properties or {}),
        "additionalProperties": False,
    }
    if required:
        schema["required"] = list(required)
    if any_of:
        schema["anyOf"] = [dict(item) for item in any_of]
    return schema


def reject_unknown_arguments(
    arguments: Mapping[str, object],
    *,
    tool_name: str,
    allowed_fields: Collection[str],
) -> None:
    unexpected_fields = sorted(set(arguments) - set(allowed_fields))
    if unexpected_fields:
        unexpected_field_list = ", ".join(unexpected_fields)
        raise TypeError(f"{tool_name} got unexpected arguments: {unexpected_field_list}")


@dataclass(frozen=True)
class ToolResponse:
    text: str
    structured_content: dict[str, JSONValue]


class ToolInvoker(Protocol):
    def __call__(self, arguments: Mapping[str, object] | None = None) -> ToolResponse: ...


@dataclass(frozen=True)
class ToolDescriptor:
    name: str
    description: str
    input_schema: dict[str, object]


@dataclass(frozen=True)
class RegisteredTool:
    descriptor: ToolDescriptor
    invoke: ToolInvoker
