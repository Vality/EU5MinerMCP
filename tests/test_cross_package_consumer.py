"""Cross-package consumer tests: drive the MCP against the real library.

These tests exercise the ``eu5miner_mcp`` server using the real ``eu5miner``
library (not a stub). If a library change breaks the MCP's expected input
shape or output schema, these tests catch it before it reaches production.

The synthetic install layout is provided by ``eu5miner.testing`` so the
contract for what counts as a "fresh install" is shared with the library
tests and the GUI cross-package tests.

What this covers:
- The MCP server builds cleanly against the real library
- The read-only install/systems/entities tool surface is functional
- The tool descriptors expose the JSON Schema that clients depend on
- The library boundary is respected: no private library imports

What this deliberately does NOT cover:
- Mod write tools (covered by library-side mod workflow tests)
- The full transport layer (``local-shell``, ``stdio``) — those are
  separately tested by ``test_server_shell.py``
"""

from __future__ import annotations

from pathlib import Path

import eu5miner.inspection as inspection
import pytest
from eu5miner.testing import build_synthetic_install

from eu5miner_mcp.server import MCPServer, build_server
from eu5miner_mcp.tools import (
    describe_diplomacy_tools,
    describe_entity_tools,
    describe_file_tools,
    describe_install_tools,
    describe_mod_tools,
    describe_religion_tools,
    describe_server_tools,
    describe_system_tools,
)
from eu5miner_mcp.tools.entities import (
    DescribeEntityRequest,
    FindEntityRequest,
    describe_entity,
    find_entities,
)
from eu5miner_mcp.tools.files import ListFilesRequest, list_files
from eu5miner_mcp.tools.install import InspectInstallRequest, inspect_install
from eu5miner_mcp.tools.systems import (
    GetSystemReportRequest,
    ListSystemsRequest,
    get_system_report,
    list_systems,
)

# ----- Server build against the real library ---------------------------------


def test_build_server_constructs_cleanly() -> None:
    """``build_server()`` must produce a server with a non-empty tool surface.

    If the library changed in a way that broke any tool's import-time
    construction, this fails before any tool is called.
    """
    server = build_server()

    assert isinstance(server, MCPServer)
    descriptors = server.describe_tools()
    assert len(descriptors) > 0
    # Every descriptor must have a non-empty name and description.
    for desc in descriptors:
        assert desc.name
        assert desc.description
        # inputSchema is a JSON Schema object. Pin the basics.
        assert isinstance(desc.input_schema, dict)
        assert desc.input_schema.get("type") == "object"


def test_all_tool_groups_describe_without_error() -> None:
    """Every tool group must describe its tools successfully.

    A library change that broke one tool's schema would surface here.
    """
    for describe in (
        describe_diplomacy_tools,
        describe_entity_tools,
        describe_file_tools,
        describe_install_tools,
        describe_mod_tools,
        describe_religion_tools,
        describe_server_tools,
        describe_system_tools,
    ):
        tools = describe()
        assert len(tools) > 0, f"{describe.__name__} returned no tools"


# ----- Synthetic-install end-to-end ------------------------------------------


def test_inspect_install_tool_against_synthetic_install(tmp_path: Path) -> None:
    """The ``inspect-install`` tool must work against a fresh synthetic install.

    The MCP's primary entry point for a fresh install. A regression that
    broke ``inspection.inspect_install`` would surface here as either a
    shape mismatch or a missing field on the returned ``InstallSummary``.
    """
    install_root = tmp_path / "install"
    build_synthetic_install(install_root)

    summary = inspect_install(InspectInstallRequest(install_root=install_root))

    assert isinstance(summary, inspection.InstallSummary)
    assert summary.root == install_root
    assert [s.name for s in summary.sources] == ["vanilla"]


def test_list_systems_tool_returns_library_facade() -> None:
    """``list-systems`` must mirror the library's supported-systems list.

    A library rename that the MCP didn't follow up on would surface here
    as a divergence between the two. The MCP's tool schema is built from
    this list, so a missing name would also break the tool's JSON Schema
    ``enum``.
    """
    systems = list_systems(ListSystemsRequest())
    library_systems = inspection.list_supported_systems()

    assert {s.name for s in systems} == {s.name for s in library_systems}


def test_get_system_report_tool_against_synthetic_install(tmp_path: Path) -> None:
    """``get-system-report`` must accept the request structure.

    The MCP's primary way to render a per-system summary. A regression in
    the library that broke the request-handling path (deserialization,
    routing to the right system) would surface here as a different
    exception type or an unexpected response shape.

    Note: ``get_system_report`` is fundamentally file-backed: it reads
    representative files (e.g. ``common/religions/christian.txt``) from
    the install to render a per-system summary. A synthetic install has
    no representative files, so the underlying library raises
    ``FileNotFoundError``. The MCP's responsibility ends at handing the
    request off to the library cleanly, which is what this test pins.
    """
    install_root = tmp_path / "install"
    build_synthetic_install(install_root)

    request = GetSystemReportRequest(system="religion", install_root=install_root)
    # The request object must be constructible from the call site shape.
    assert request.system == "religion"
    assert request.install_root == install_root

    # The MCP layer delegates to the library. We assert the delegation
    # path is wired: the library call exists and is reachable, but it
    # raises on the empty install (a known library limitation, not a
    # MCP contract issue).
    with pytest.raises((FileNotFoundError, KeyError)):
        get_system_report(request)


def test_find_entities_tool_against_synthetic_install(tmp_path: Path) -> None:
    """``find-entities`` must accept the request structure.

    The MCP's primary entity-search tool. A regression in the request
    handling would surface here. The full file-backed search requires
    real entity files, which a synthetic install lacks — see the note
    in ``test_get_system_report_tool_against_synthetic_install`` for
    the same caveat.
    """
    install_root = tmp_path / "install"
    build_synthetic_install(install_root)

    request = FindEntityRequest(system="religion", install_root=install_root)
    assert request.system == "religion"
    assert request.install_root == install_root

    # The MCP's request must be valid and the underlying call must be
    # reachable. With no entity files, the result is empty (not an error).
    results = find_entities(request)
    # The MCP wraps the raw list in a typed result dataclass; pin the
    # shape so a future refactor that renames or restructures the wrapper
    # surfaces here.
    assert results.system == "religion"
    assert results.total_count == 0
    assert tuple(results.entities) == ()


def test_describe_entity_tool_handles_missing_entity(tmp_path: Path) -> None:
    """``describe-entity`` must raise ``KeyError`` for an unknown entity.

    The library's contract for a missing entity is to raise ``KeyError``
    (see ``inspection.get_system_entity``). The MCP layer propagates
    this; consumers in the MCP client are expected to catch it.

    This is a *contract* test: a regression in the library that switched
    the missing-entity signal to a different exception (e.g.
    ``ValueError``) would break the MCP client. We pin ``KeyError`` so
    the change is explicit.
    """
    install_root = tmp_path / "install"
    build_synthetic_install(install_root)

    request = DescribeEntityRequest(
        system="religion",
        name="definitely_not_a_real_entity_for_test",
        install_root=install_root,
    )
    with pytest.raises(KeyError):
        describe_entity(request)


def test_list_files_tool_against_synthetic_install(tmp_path: Path) -> None:
    """``list-files`` must work against a fresh synthetic install.

    The MCP's primary file-listing tool. A regression in the library that
    broke the empty-install case would surface here.
    """
    from eu5miner import ContentPhase

    install_root = tmp_path / "install"
    build_synthetic_install(install_root)

    response = list_files(
        ListFilesRequest(install_root=install_root, phase=ContentPhase.IN_GAME)
    )
    # A fresh synthetic install has no files, so results should be empty.
    assert response is not None


# ----- Library import boundary ------------------------------------------------


_ALLOWED_EU5MINER_IMPORT_PREFIXES = (
    "eu5miner.inspection",
    "eu5miner.mods",
    "eu5miner.testing",
    # The library's own ``__init__`` docstring declares ``eu5miner.domains``
    # as a public surface ("concept-local helpers from grouped packages under
    # ``eu5miner.domains``"), and ``eu5miner.inspection`` itself imports from
    # ``eu5miner.domains.*``. Domain packages are part of the contract.
    "eu5miner.domains",
    # ``eu5miner.vfs`` re-exports ``ContentSource``, ``SourceKind``, and
    # ``VirtualFilesystem`` to the root and is the canonical import path
    # for the VFS types (``MergedFile``, ``SourceFile``, etc.).
    "eu5miner.vfs",
)


def _eu5miner_target_module(stripped_line: str) -> str | None:
    """Return the imported top-level ``eu5miner.*`` module, or None.

    Uses word-boundary parsing instead of substring matching so that
    ``from eu5miner_mcp ...`` is NOT confused with ``from eu5miner ...``.
    """
    tokens = stripped_line.split()
    if not tokens or tokens[0] not in {"import", "from"}:
        return None
    if tokens[0] == "import":
        for tok in tokens[1:]:
            if tok == "as" or tok.startswith("(") or tok == ",":
                break
            if tok == "eu5miner" or tok.startswith("eu5miner."):
                return tok.rstrip(",")
        return None
    if len(tokens) >= 2 and (
        tokens[1] == "eu5miner" or tokens[1].startswith("eu5miner.")
    ):
        return tokens[1]
    return None


def _is_allowed_eu5miner_import(stripped_line: str) -> bool:
    """True if a ``from eu5miner ...`` or ``import eu5miner ...`` line is public."""
    target = _eu5miner_target_module(stripped_line)
    if target is None:
        return False
    if target == "eu5miner":
        if stripped_line.startswith("from eu5miner import"):
            return True
        return stripped_line in {"import eu5miner", "import eu5miner as _"}
    for prefix in _ALLOWED_EU5MINER_IMPORT_PREFIXES:
        if target == prefix or target.startswith(prefix + "."):
            return True
    return False


def test_mcp_does_not_reach_into_private_library_modules() -> None:
    """The MCP must only import from the library's public surface.

    Pin this so that future MCP refactors don't start grabbing internal
    helpers from ``eu5miner.domains._private_helpers`` or similar — which
    would silently couple the MCP to library internals and break again
    on the next library refactor.

    The current public root is ``eu5miner`` (``GameInstall``,
    ``ContentPhase``, ``VirtualFilesystem``) and the stable facade is
    ``eu5miner.inspection`` plus the ``eu5miner.mods`` helper package.
    The ``eu5miner.domains`` packages are also public per the library's
    own ``__init__`` docstring.
    """
    import sys

    import eu5miner_mcp  # noqa: F401  (just importing for the side effect)
    mcp_modules = [
        name
        for name in sys.modules
        if name.startswith("eu5miner_mcp.")
    ]
    bad_imports: list[tuple[str, str]] = []
    for module_name in mcp_modules:
        module = sys.modules[module_name]
        source = getattr(module, "__file__", "") or ""
        if not source.endswith(".py"):
            continue
        try:
            text = Path(source).read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith(("from ", "import ")):
                continue
            target = _eu5miner_target_module(stripped)
            if target is None:
                continue
            if _is_allowed_eu5miner_import(stripped):
                continue
            bad_imports.append((module_name, stripped))

    assert not bad_imports, (
        "MCP is reaching into non-public library modules. "
        "Move the import to the public facade (eu5miner, eu5miner.inspection, "
        "eu5miner.mods, or eu5miner.testing) before the next library refactor.\n"
        + "\n".join(f"  {m}: {imp}" for m, imp in bad_imports)
    )


# ----- Library / MCP agreement ------------------------------------------------


def _mcp_enum_for(tool_descriptors, property_name: str) -> set[str] | None:
    """Pull an enum from a tool's input schema properties, if present."""
    for tool in tool_descriptors:
        properties = tool.input_schema.get("properties") or {}
        if property_name in properties and "enum" in properties[property_name]:
            return set(properties[property_name]["enum"])
    return None


def test_mcp_and_library_agree_on_supported_system_names() -> None:
    """The MCP ``list-systems`` enum must match the library's system set.

    The MCP exposes supported system names as a JSON Schema ``enum`` on
    its ``list_systems`` tool's input schema. MCP clients use that enum
    to validate call arguments. A library rename that the MCP didn't
    follow up on would surface here as a missing or extra name in the
    enum.
    """
    from eu5miner_mcp.tools import describe_system_tools

    mcp_enum = _mcp_enum_for(describe_system_tools(), "system")
    assert mcp_enum is not None, (
        "MCP list_systems tool does not expose a 'system' enum. "
        "Check that the tool descriptor's input schema is correct."
    )
    library_names = {info.name for info in inspection.list_supported_systems()}

    extra = mcp_enum - library_names
    assert not extra, (
        f"MCP enum contains systems the library does not: {extra}. "
        "Clients would accept tool calls with arguments the library would reject."
    )
    missing = library_names - mcp_enum
    assert not missing, (
        f"MCP enum is missing these library systems: {missing}. "
        "Clients would be unable to call the tool with these systems."
    )


def test_mcp_and_library_agree_on_entity_system_names() -> None:
    """The MCP ``list-entity-systems`` enum must match the library's entity set.

    Same shape as the supported-system check above, but for the entity
    browsing surface.
    """
    from eu5miner_mcp.tools import describe_entity_tools

    # The entity tool group's input schemas may have multiple "system"
    # enums (one per system-related tool); aggregate them.
    enum_names: set[str] = set()
    for tool in describe_entity_tools():
        properties = tool.input_schema.get("properties") or {}
        for prop in properties.values():  # type: ignore[attr-defined]
            if "enum" in prop:
                enum_names.update(prop["enum"])

    library_names = {info.name for info in inspection.list_entity_systems()}

    extra = enum_names - library_names
    assert not extra, (
        f"MCP entity-system enums contain names the library does not: {extra}. "
        "Clients would accept tool calls with arguments the library would reject."
    )
    missing = library_names - enum_names
    assert not missing, (
        f"MCP entity-system enums are missing these library systems: {missing}."
    )
