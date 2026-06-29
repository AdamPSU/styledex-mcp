from __future__ import annotations

from pathlib import Path

import pytest
from mcp.server.fastmcp import FastMCP

from copycat.server import create_mcp_server, default_root
from copycat.store import CopycatStore


def test_creates_fastmcp_server(tmp_path: Path) -> None:
    server = create_mcp_server(CopycatStore(tmp_path))

    assert isinstance(server, FastMCP)


def test_default_root_prefers_copycat_env_then_default_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    copycat_root = tmp_path / "copycat" / "designs"

    monkeypatch.setenv("COPYCAT_ROOT", str(copycat_root))
    assert default_root() == copycat_root

    monkeypatch.delenv("COPYCAT_ROOT")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert default_root() == tmp_path / ".copycat" / "designs"


@pytest.mark.anyio
async def test_public_tool_contract_is_minimal(tmp_path: Path) -> None:
    server = create_mcp_server(CopycatStore(tmp_path))

    tools = await server.list_tools()

    assert {tool.name for tool in tools} == {
        "copycat_list",
        "copycat_get",
        "copycat_create",
        "copycat_capture_screenshot",
        "copycat_capture_snapshot",
        "copycat_capture_extract",
        "copycat_save",
        "copycat_rename",
        "copycat_delete",
    }


@pytest.mark.anyio
async def test_capture_tools_are_curated_not_generic_playwright(tmp_path: Path) -> None:
    server = create_mcp_server(CopycatStore(tmp_path))

    tools = await server.list_tools()
    tool_names = {tool.name for tool in tools}

    assert "copycat_playwright" not in tool_names
    assert "copycat_capture_seed" not in tool_names
    assert "copycat_capture_page" not in tool_names


@pytest.mark.anyio
async def test_rename_tool_uses_from_and_to_schema(tmp_path: Path) -> None:
    server = create_mcp_server(CopycatStore(tmp_path))

    tools = await server.list_tools()
    rename_tool = next(tool for tool in tools if tool.name == "copycat_rename")

    assert rename_tool.inputSchema["properties"].keys() == {"from", "to"}
    assert rename_tool.inputSchema["required"] == ["from", "to"]


@pytest.mark.anyio
async def test_rename_tool_accepts_from_argument(tmp_path: Path) -> None:
    store = CopycatStore(tmp_path)
    store.create(alias="linear", source_url="https://linear.app/")
    server = create_mcp_server(store)

    await server.call_tool("copycat_rename", {"from": "linear", "to": "renamed-linear"})

    with pytest.raises(FileNotFoundError, match="does not exist"):
        store.get("linear")
    assert store.get("renamed-linear")["metadata"]["alias"] == "renamed-linear"


@pytest.mark.anyio
async def test_save_tool_accepts_profile_metadata_and_evidence(tmp_path: Path) -> None:
    server = create_mcp_server(CopycatStore(tmp_path))

    tools = await server.list_tools()
    save_tool = next(tool for tool in tools if tool.name == "copycat_save")

    assert set(save_tool.inputSchema["properties"].keys()) >= {
        "alias",
        "design",
        "tokens",
        "notes",
        "screenshots",
        "evidence",
        "pages",
        "status",
        "confidence",
        "caveats",
        "observedNoise",
    }
    assert "metadataPatch" not in save_tool.inputSchema["properties"]


@pytest.mark.anyio
async def test_save_tool_updates_metadata_from_explicit_fields(tmp_path: Path) -> None:
    store = CopycatStore(tmp_path)
    store.create(alias="linear", source_url="https://linear.app/")
    server = create_mcp_server(store)

    await server.call_tool(
        "copycat_save",
        {
            "alias": "linear",
            "design": "# Linear\n",
            "tokens": {},
            "status": "captured",
            "confidence": "high",
            "caveats": ["Public pages only."],
            "observedNoise": ["No cookie banner observed."],
        },
    )

    metadata = store.get("linear")["metadata"]
    assert metadata["status"] == "captured"
    assert metadata["confidence"] == "high"
    assert metadata["caveats"] == ["Public pages only."]
    assert metadata["observedNoise"] == ["No cookie banner observed."]


@pytest.mark.anyio
async def test_capture_tools_bound_resource_knobs_in_schema(tmp_path: Path) -> None:
    server = create_mcp_server(CopycatStore(tmp_path))

    tools = await server.list_tools()
    screenshot_tool = next(tool for tool in tools if tool.name == "copycat_capture_screenshot")
    extract_tool = next(tool for tool in tools if tool.name == "copycat_capture_extract")

    assert screenshot_tool.inputSchema["properties"]["waitMs"] == {
        "default": 1500,
        "maximum": 30000,
        "minimum": 0,
        "title": "Waitms",
        "type": "integer",
    }
    assert extract_tool.inputSchema["properties"]["selectorLimit"] == {
        "default": 250,
        "maximum": 1000,
        "minimum": 1,
        "title": "Selectorlimit",
        "type": "integer",
    }
