from __future__ import annotations

import inspect
import os
from pathlib import Path
from typing import Annotated, Any, Literal, TypeAlias

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from .capture import CaptureService, ExtractKind, Viewport
from .store import AliasStatus, Confidence, CopycatStore, MetadataPage


WaitMs: TypeAlias = Annotated[int, Field(ge=0, le=30_000)]
SelectorLimit: TypeAlias = Annotated[int, Field(ge=1, le=1_000)]


def default_root() -> Path:
    configured_root = os.environ.get("COPYCAT_ROOT")
    if configured_root:
        return Path(configured_root).expanduser().resolve()

    copycat_root = Path("~/.copycat/designs").expanduser().resolve()
    if copycat_root.exists():
        return copycat_root

    configured_legacy_root = os.environ.get("STYLE_MIRROR_ROOT")
    if configured_legacy_root:
        legacy_root = Path(configured_legacy_root).expanduser().resolve()
        if legacy_root.exists():
            return legacy_root

    legacy_root = Path("~/.style-mirror/designs").expanduser().resolve()
    if legacy_root.exists():
        return legacy_root

    return copycat_root


def create_mcp_server(store: CopycatStore | None = None, capture_service: CaptureService | None = None) -> FastMCP:
    store = store or CopycatStore(default_root())
    capture_service = capture_service or CaptureService(store=store)
    mcp = FastMCP("copycat")

    @mcp.tool()
    def copycat_list() -> dict[str, Any]:
        """List saved Copycat aliases when the user wants to browse available captured styles. Reads metadata from the Copycat library root: COPYCAT_ROOT when set, otherwise ~/.copycat/designs."""
        return store.list()

    @mcp.tool()
    def copycat_get(alias: str) -> dict[str, Any]:
        """Read an existing Copycat profile before applying, inspecting, or enriching a saved style. Returns DESIGN.md, tokens, notes, metadata, screenshots, and evidence stored under the alias directory in the Copycat library root."""
        return dict(store.get(alias))

    @mcp.tool()
    def copycat_create(
        alias: str,
        sourceUrl: str,
        mode: Literal["create", "overwrite"] = "create",
    ) -> dict[str, Any]:
        """Create a new Copycat alias before the first capture for a website. Stores the profile under COPYCAT_ROOT/<alias> when COPYCAT_ROOT is set, otherwise ~/.copycat/designs/<alias>, and returns exact paths plus suggested screenshot paths."""
        return store.create(alias=alias, source_url=sourceUrl, mode=mode)

    @mcp.tool()
    def copycat_capture_screenshot(
        alias: str,
        url: str,
        path: str,
        viewport: Viewport = "desktop",
        fullPage: bool = False,
        waitMs: WaitMs = 1500,
    ) -> dict[str, Any]:
        """Capture visual evidence when a page's layout, density, hierarchy, or responsive behavior matters. Saves a Playwright screenshot under the alias directory at an alias-relative screenshots/ path, such as screenshots/desktop-full.png."""
        return capture_service.capture_screenshot(
            alias=alias,
            url=url,
            path=path,
            viewport=viewport,
            full_page=fullPage,
            wait_ms=waitMs,
        )

    @mcp.tool()
    def copycat_capture_snapshot(
        alias: str,
        url: str,
        path: str,
        viewport: Viewport = "desktop",
        waitMs: WaitMs = 1500,
    ) -> dict[str, Any]:
        """Capture visible DOM structure when screenshots need supporting context about headings, landmarks, text snippets, and element boxes. Saves JSON evidence under the alias directory at an alias-relative evidence/ path."""
        return capture_service.capture_snapshot(alias=alias, url=url, path=path, viewport=viewport, wait_ms=waitMs)

    @mcp.tool()
    def copycat_capture_extract(
        alias: str,
        url: str,
        path: str,
        kind: ExtractKind,
        viewport: Viewport = "desktop",
        waitMs: WaitMs = 1500,
        selectorLimit: SelectorLimit = 250,
    ) -> dict[str, Any]:
        """Capture structured evidence when the design profile needs links, CSS variables, or computed styles grounded in rendered page data. Saves JSON under the alias directory at an alias-relative evidence/ path, including page-specific paths like evidence/pages/pricing/computed-styles.json."""
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
    def copycat_save(
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
        """Save or update the authored Copycat profile after capture or enrichment. Writes DESIGN.md, tokens.json, notes.md, metadata, and referenced artifact lists into the alias directory, then returns validation for the saved profile."""
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

    def copycat_rename(**kwargs: str) -> dict[str, Any]:
        return dict(store.rename(old_alias=kwargs["from"], new_alias=kwargs["to"]))

    setattr(
        copycat_rename,
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
        name="copycat_rename",
        description="Rename a saved Copycat alias when the user wants a clearer slug. Moves the alias directory within the Copycat library root, updates metadata, and refuses target collisions.",
    )(copycat_rename)

    @mcp.tool()
    def copycat_delete(alias: str) -> dict[str, Any]:
        """Delete a saved Copycat profile when the user explicitly wants it removed. Permanently removes the alias directory and its DESIGN.md, tokens, notes, screenshots, and evidence from the Copycat library root."""
        return store.delete(alias)

    return mcp


def main() -> None:
    create_mcp_server().run()


if __name__ == "__main__":
    main()
