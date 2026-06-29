from __future__ import annotations

from pathlib import Path

import pytest
from mcp.server.fastmcp import FastMCP

from styledex_mcp.server import create_mcp_server, default_root
from styledex_mcp.store import StyleDexStore


def test_creates_fastmcp_server(tmp_path: Path) -> None:
    server = create_mcp_server(StyleDexStore(tmp_path))

    assert isinstance(server, FastMCP)


def test_default_root_prefers_styledex_env_then_legacy_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    styledex_root = tmp_path / "styledex" / "designs"
    legacy_root = tmp_path / "style-mirror" / "designs"

    monkeypatch.setenv("STYLEDEX_ROOT", str(styledex_root))
    monkeypatch.setenv("STYLE_MIRROR_ROOT", str(legacy_root))
    assert default_root() == styledex_root

    monkeypatch.delenv("STYLEDEX_ROOT")
    legacy_root.mkdir(parents=True)
    assert default_root() == legacy_root


@pytest.mark.anyio
async def test_public_tool_contract_is_minimal(tmp_path: Path) -> None:
    server = create_mcp_server(StyleDexStore(tmp_path))

    tools = await server.list_tools()

    assert {tool.name for tool in tools} == {
        "styledex_list",
        "styledex_get",
        "styledex_create",
        "styledex_capture_screenshot",
        "styledex_capture_snapshot",
        "styledex_capture_extract",
        "styledex_save",
        "styledex_rename",
        "styledex_delete",
    }


@pytest.mark.anyio
async def test_capture_tools_are_curated_not_generic_playwright(tmp_path: Path) -> None:
    server = create_mcp_server(StyleDexStore(tmp_path))

    tools = await server.list_tools()
    tool_names = {tool.name for tool in tools}

    assert "styledex_playwright" not in tool_names
    assert "styledex_capture_seed" not in tool_names
    assert "styledex_capture_page" not in tool_names


@pytest.mark.anyio
async def test_rename_tool_uses_from_and_to_schema(tmp_path: Path) -> None:
    server = create_mcp_server(StyleDexStore(tmp_path))

    tools = await server.list_tools()
    rename_tool = next(tool for tool in tools if tool.name == "styledex_rename")

    assert rename_tool.inputSchema["properties"].keys() == {"from", "to"}
    assert rename_tool.inputSchema["required"] == ["from", "to"]


@pytest.mark.anyio
async def test_rename_tool_accepts_from_argument(tmp_path: Path) -> None:
    store = StyleDexStore(tmp_path)
    store.create(alias="linear", source_url="https://linear.app/")
    server = create_mcp_server(store)

    await server.call_tool("styledex_rename", {"from": "linear", "to": "renamed-linear"})

    with pytest.raises(FileNotFoundError, match="does not exist"):
        store.get("linear")
    assert store.get("renamed-linear")["metadata"]["alias"] == "renamed-linear"


@pytest.mark.anyio
async def test_save_tool_accepts_profile_metadata_and_evidence(tmp_path: Path) -> None:
    server = create_mcp_server(StyleDexStore(tmp_path))

    tools = await server.list_tools()
    save_tool = next(tool for tool in tools if tool.name == "styledex_save")

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
    store = StyleDexStore(tmp_path)
    store.create(alias="linear", source_url="https://linear.app/")
    server = create_mcp_server(store)

    await server.call_tool(
        "styledex_save",
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
    server = create_mcp_server(StyleDexStore(tmp_path))

    tools = await server.list_tools()
    screenshot_tool = next(tool for tool in tools if tool.name == "styledex_capture_screenshot")
    extract_tool = next(tool for tool in tools if tool.name == "styledex_capture_extract")

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
