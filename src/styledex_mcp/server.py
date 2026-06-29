from __future__ import annotations

import inspect
import os
from pathlib import Path
from typing import Annotated, Any, Literal, TypeAlias

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from .capture import CaptureService, ExtractKind, Viewport
from .store import AliasStatus, Confidence, MetadataPage, StyleDexStore


WaitMs: TypeAlias = Annotated[int, Field(ge=0, le=30_000)]
SelectorLimit: TypeAlias = Annotated[int, Field(ge=1, le=1_000)]


def default_root() -> Path:
    configured_root = os.environ.get("STYLEDEX_ROOT")
    if configured_root:
        return Path(configured_root).expanduser().resolve()

    root = Path("~/.styledex/designs").expanduser().resolve()
    legacy_root = Path(os.environ.get("STYLE_MIRROR_ROOT", "~/.style-mirror/designs")).expanduser().resolve()
    if not root.exists() and legacy_root.exists():
        return legacy_root
    return root


def create_mcp_server(store: StyleDexStore | None = None, capture_service: CaptureService | None = None) -> FastMCP:
    store = store or StyleDexStore(default_root())
    capture_service = capture_service or CaptureService(store=store)
    mcp = FastMCP("styledex")

    @mcp.tool()
    def styledex_list() -> dict[str, Any]:
        """List saved StyleDex aliases with metadata summaries."""
        return store.list()

    @mcp.tool()
    def styledex_get(alias: str) -> dict[str, Any]:
        """Read a saved StyleDex alias profile, metadata, tokens, notes, and artifact paths."""
        return dict(store.get(alias))

    @mcp.tool()
    def styledex_create(
        alias: str,
        sourceUrl: str,
        mode: Literal["create", "overwrite"] = "create",
    ) -> dict[str, Any]:
        """Create alias directories and return absolute alias paths plus relative suggested capture paths."""
        return store.create(alias=alias, source_url=sourceUrl, mode=mode)

    @mcp.tool()
    def styledex_capture_screenshot(
        alias: str,
        url: str,
        path: str,
        viewport: Viewport = "desktop",
        fullPage: bool = False,
        waitMs: WaitMs = 1500,
    ) -> dict[str, Any]:
        """Capture one screenshot with Playwright and register it under the alias. Path must be alias-relative under screenshots/."""
        return capture_service.capture_screenshot(
            alias=alias,
            url=url,
            path=path,
            viewport=viewport,
            full_page=fullPage,
            wait_ms=waitMs,
        )

    @mcp.tool()
    def styledex_capture_snapshot(
        alias: str,
        url: str,
        path: str,
        viewport: Viewport = "desktop",
        waitMs: WaitMs = 1500,
    ) -> dict[str, Any]:
        """Capture a lightweight DOM snapshot with Playwright and register it as evidence. Path must be alias-relative under evidence/."""
        return capture_service.capture_snapshot(alias=alias, url=url, path=path, viewport=viewport, wait_ms=waitMs)

    @mcp.tool()
    def styledex_capture_extract(
        alias: str,
        url: str,
        path: str,
        kind: ExtractKind,
        viewport: Viewport = "desktop",
        waitMs: WaitMs = 1500,
        selectorLimit: SelectorLimit = 250,
    ) -> dict[str, Any]:
        """Capture curated structured evidence. Path must be alias-relative under evidence/."""
        return capture_service.capture_extract(
            alias=alias,
            url=url,
            path=path,
            kind=kind,
            viewport=viewport,
            wait_ms=waitMs,
            selector_limit=selectorLimit,
        )

    @mcp.tool()
    def styledex_save(
        alias: str,
        design: str | None = None,
        tokens: Any | None = None,
        notes: str | None = None,
        screenshots: list[str] | None = None,
        evidence: list[str] | None = None,
        pages: list[MetadataPage] | None = None,
        status: AliasStatus | None = None,
        confidence: Confidence | None = None,
        caveats: list[str] | None = None,
        observedNoise: list[str] | None = None,
    ) -> dict[str, Any]:
        """Save profile artifacts, evidence references, explicit metadata fields, and validation for an alias."""
        metadata_patch = {
            key: value
            for key, value in {
                "status": status,
                "confidence": confidence,
                "caveats": caveats,
                "observedNoise": observedNoise,
            }.items()
            if value is not None
        }
        return dict(
            store.save(
                alias=alias,
                design=design,
                tokens=tokens,
                notes=notes,
                screenshots=screenshots,
                evidence=evidence,
                pages=pages,
                metadata_patch=metadata_patch,
            )
        )

    def styledex_rename(**kwargs: str) -> dict[str, Any]:
        return dict(store.rename(old_alias=kwargs["from"], new_alias=kwargs["to"]))

    setattr(
        styledex_rename,
        "__signature__",
        inspect.Signature(
            parameters=[
                inspect.Parameter(
                    "from_",
                    inspect.Parameter.KEYWORD_ONLY,
                    annotation=Annotated[str, Field(alias="from")],
                ),
                inspect.Parameter("to", inspect.Parameter.KEYWORD_ONLY, annotation=str),
            ],
            return_annotation=dict[str, Any],
        ),
    )
    mcp.tool(
        name="styledex_rename",
        description="Rename a StyleDex alias and update metadata. Refuses target collisions.",
    )(styledex_rename)

    @mcp.tool()
    def styledex_delete(alias: str) -> dict[str, Any]:
        """Delete a StyleDex alias directory immediately. No confirmation argument is required."""
        return store.delete(alias)

    return mcp


def main() -> None:
    create_mcp_server().run()


if __name__ == "__main__":
    main()
