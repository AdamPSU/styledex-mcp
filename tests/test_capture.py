from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from copycat.capture import CaptureService
from copycat.store import CopycatStore


class FakeCaptureBackend:
    def capture_screenshot(
        self,
        *,
        url: str,
        output_path: Path,
        viewport: str,
        full_page: bool,
        wait_ms: int,
    ) -> None:
        output_path.write_bytes(f"screenshot {url} {viewport} {full_page} {wait_ms}".encode())

    def capture_snapshot(self, *, url: str, viewport: str, wait_ms: int) -> dict[str, Any]:
        return {"url": url, "viewport": viewport, "waitMs": wait_ms, "tree": {"role": "document"}}

    def capture_extract(
        self,
        *,
        url: str,
        kind: str,
        viewport: str,
        wait_ms: int,
        selector_limit: int,
    ) -> Any:
        return {"url": url, "kind": kind, "viewport": viewport, "limit": selector_limit, "items": []}


@pytest.fixture()
def service(tmp_path: Path) -> CaptureService:
    store = CopycatStore(tmp_path)
    store.create(alias="linear", source_url="https://linear.app/")
    return CaptureService(store=store, backend=FakeCaptureBackend())


def test_capture_screenshot_writes_and_registers_screenshot(service: CaptureService) -> None:
    result = service.capture_screenshot(
        alias="linear",
        url="https://linear.app/",
        path="screenshots/desktop-fold.png",
        viewport="desktop",
        full_page=False,
        wait_ms=10,
    )

    assert result["relativePath"] == "screenshots/desktop-fold.png"
    assert Path(result["path"]).read_bytes().startswith(b"screenshot https://linear.app/")
    assert result["profile"]["metadata"]["files"]["screenshots"] == ["screenshots/desktop-fold.png"]


def test_capture_snapshot_writes_json_and_registers_evidence(service: CaptureService) -> None:
    result = service.capture_snapshot(
        alias="linear",
        url="https://linear.app/",
        path="evidence/desktop-snapshot.json",
        viewport="desktop",
        wait_ms=10,
    )

    payload = json.loads(Path(result["path"]).read_text())
    assert payload["tree"] == {"role": "document"}
    assert result["profile"]["metadata"]["files"]["evidence"] == ["evidence/desktop-snapshot.json"]


def test_capture_extract_writes_json_and_registers_evidence(service: CaptureService) -> None:
    result = service.capture_extract(
        alias="linear",
        url="https://linear.app/",
        path="evidence/link-candidates.json",
        kind="links",
        viewport="desktop",
        wait_ms=10,
        selector_limit=50,
    )

    payload = json.loads(Path(result["path"]).read_text())
    assert payload["kind"] == "links"
    assert payload["limit"] == 50
    assert result["profile"]["metadata"]["files"]["evidence"] == ["evidence/link-candidates.json"]


def test_capture_rejects_paths_outside_alias(service: CaptureService) -> None:
    with pytest.raises(ValueError, match="inside alias"):
        service.capture_screenshot(
            alias="linear",
            url="https://linear.app/",
            path="../outside.png",
            viewport="desktop",
            full_page=False,
            wait_ms=10,
        )


def test_capture_rejects_reserved_alias_files(service: CaptureService) -> None:
    with pytest.raises(ValueError, match="reserved"):
        service.capture_screenshot(
            alias="linear",
            url="https://linear.app/",
            path="metadata.json",
            viewport="desktop",
            full_page=False,
            wait_ms=10,
        )


def test_capture_restricts_screenshots_and_evidence_to_expected_directories(service: CaptureService) -> None:
    with pytest.raises(ValueError, match="screenshots/"):
        service.capture_screenshot(
            alias="linear",
            url="https://linear.app/",
            path="evidence/not-a-screenshot.png",
            viewport="desktop",
            full_page=False,
            wait_ms=10,
        )

    with pytest.raises(ValueError, match="evidence/"):
        service.capture_snapshot(
            alias="linear",
            url="https://linear.app/",
            path="screenshots/not-evidence.json",
            viewport="desktop",
            wait_ms=10,
        )


def test_capture_rejects_unbounded_resource_knobs(service: CaptureService) -> None:
    with pytest.raises(ValueError, match="wait_ms"):
        service.capture_snapshot(
            alias="linear",
            url="https://linear.app/",
            path="evidence/desktop-snapshot.json",
            viewport="desktop",
            wait_ms=-1,
        )

    with pytest.raises(ValueError, match="selector_limit"):
        service.capture_extract(
            alias="linear",
            url="https://linear.app/",
            path="evidence/link-candidates.json",
            kind="links",
            viewport="desktop",
            wait_ms=10,
            selector_limit=1001,
        )


@pytest.mark.anyio
async def test_real_capture_backend_works_inside_asyncio_loop(tmp_path: Path) -> None:
    store = CopycatStore(tmp_path)
    store.create(alias="async-site", source_url="data:text/html,<title>Async</title><main>Hello</main>")
    service = CaptureService(store=store)

    result = service.capture_snapshot(
        alias="async-site",
        url="data:text/html,<title>Async</title><main>Hello</main>",
        path="evidence/async-snapshot.json",
        viewport="desktop",
        wait_ms=0,
    )

    payload = json.loads(Path(result["path"]).read_text())
    assert payload["title"] == "Async"


@pytest.mark.anyio
async def test_real_screenshot_capture_works_inside_asyncio_loop(tmp_path: Path) -> None:
    store = CopycatStore(tmp_path)
    store.create(alias="async-site", source_url="data:text/html,<title>Async</title><main>Hello</main>")
    service = CaptureService(store=store)

    result = service.capture_screenshot(
        alias="async-site",
        url="data:text/html,<title>Async</title><main>Hello</main>",
        path="screenshots/async.png",
        viewport="desktop",
        full_page=False,
        wait_ms=0,
    )

    assert Path(result["path"]).read_bytes().startswith(b"\x89PNG")
