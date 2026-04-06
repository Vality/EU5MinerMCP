"""Server self-description MCP tool over the shared runtime registry."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Protocol

from eu5miner_mcp.models import (
    RegisteredTool,
    ToolDescriptor,
    ToolResponse,
    closed_object_schema,
    reject_unknown_arguments,
)
from eu5miner_mcp.serializers import serialize_server_description


class ServerRuntimeLike(Protocol):
    @property
    def display_name(self) -> str: ...

    @property
    def package_name(self) -> str: ...

    @property
    def server_name(self) -> str: ...

    @property
    def version(self) -> str: ...

    @property
    def transports(self) -> tuple[str, ...]: ...

    @property
    def tool_names(self) -> tuple[str, ...]: ...

    @property
    def write_tool_names(self) -> tuple[str, ...]: ...

    @property
    def tool_count(self) -> int: ...

    @property
    def write_tool_count(self) -> int: ...

    def build_stdio_instructions(self) -> str: ...


def describe_server_tools() -> tuple[ToolDescriptor, ...]:
    return (_DESCRIBE_SERVER_TOOL_DESCRIPTOR,)


def get_server_tools(
    *,
    runtime_provider: Callable[[], ServerRuntimeLike],
    descriptor_provider: Callable[[], Sequence[ToolDescriptor]],
    status_message_provider: Callable[[], str],
) -> tuple[RegisteredTool, ...]:
    def _invoke_describe_server(arguments: Mapping[str, object] | None = None) -> ToolResponse:
        mapping = arguments or {}
        reject_unknown_arguments(
            mapping,
            tool_name="describe-server",
            allowed_fields=(),
        )
        runtime = runtime_provider()
        descriptors = tuple(descriptor_provider())
        status_message = status_message_provider()
        lines = [status_message]
        lines.append(f"Display name: {runtime.display_name}")
        lines.append(f"Server name: {runtime.server_name}")
        lines.append(f"Package: {runtime.package_name}")
        lines.append(f"Version: {runtime.version}")
        lines.append(f"Available transports: {', '.join(runtime.transports)}")
        lines.append(f"Stdio instructions: {runtime.build_stdio_instructions()}")
        lines.append(f"Registered tools ({runtime.tool_count}):")
        write_tool_names = set(runtime.write_tool_names)
        for descriptor in descriptors:
            suffix = " [confirm required]" if descriptor.name in write_tool_names else ""
            lines.append(f"- {descriptor.name}{suffix}: {descriptor.description}")
        lines.append(
            "Write tools requiring confirmation: "
            f"{', '.join(runtime.write_tool_names)}"
        )
        return ToolResponse(
            text="\n".join(lines),
            structured_content=serialize_server_description(
                runtime=runtime,
                descriptors=descriptors,
                status_message=status_message,
            ),
        )

    return (
        RegisteredTool(
            descriptor=_DESCRIBE_SERVER_TOOL_DESCRIPTOR,
            invoke=_invoke_describe_server,
        ),
    )


_DESCRIBE_SERVER_TOOL_DESCRIPTOR = ToolDescriptor(
    name="describe-server",
    description=(
        "Describe the current server runtime metadata and registered MCP tool registry."
    ),
    input_schema=closed_object_schema(),
)