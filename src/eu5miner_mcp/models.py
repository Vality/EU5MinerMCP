"""Shared typed models for the MCP server surface."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

type JSONScalar = None | bool | int | float | str
type JSONValue = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]


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