from __future__ import annotations

import asyncio
import json
import threading
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any, Literal, Protocol, TypeVar

from .store import CopycatStore

Viewport = Literal["desktop", "mobile"]
ExtractKind = Literal["links", "cssVariables", "computedStyles"]

MAX_WAIT_MS = 30_000
MAX_SELECTOR_LIMIT = 1_000
_RESERVED_ARTIFACT_PATHS = {"DESIGN.md", "metadata.json", "notes.md", "tokens.json"}
T = TypeVar("T")


class CaptureBackend(Protocol):
    def capture_screenshot(
        self,
        *,
        url: str,
        output_path: Path,
        viewport: str,
        full_page: bool,
        wait_ms: int,
    ) -> None: ...

    def capture_snapshot(self, *, url: str, viewport: str, wait_ms: int) -> dict[str, Any]: ...

    def capture_extract(
        self,
        *,
        url: str,
        kind: str,
        viewport: str,
        wait_ms: int,
        selector_limit: int,
    ) -> Any: ...


class CaptureService:
    def __init__(self, *, store: CopycatStore, backend: CaptureBackend | None = None) -> None:
        self.store = store
        self.backend = backend or PlaywrightCaptureBackend()

    def capture_screenshot(
        self,
        *,
        alias: str,
        url: str,
        path: str,
        viewport: Viewport = "desktop",
        full_page: bool = False,
        wait_ms: int = 1500,
    ) -> dict[str, Any]:
        _assert_wait_ms(wait_ms)
        output_path, relative_path = self.store.artifact_path(alias=alias, path=path)
        _assert_capture_path(relative_path, expected_prefix="screenshots/")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.backend.capture_screenshot(
            url=url,
            output_path=output_path,
            viewport=viewport,
            full_page=full_page,
            wait_ms=wait_ms,
        )
        profile = self.store.save(alias=alias, screenshots=[relative_path])
        return {"alias": alias, "url": url, "path": str(output_path), "relativePath": relative_path, "profile": profile}

    def capture_snapshot(
        self,
        *,
        alias: str,
        url: str,
        path: str,
        viewport: Viewport = "desktop",
        wait_ms: int = 1500,
    ) -> dict[str, Any]:
        _assert_wait_ms(wait_ms)
        output_path, relative_path = self.store.artifact_path(alias=alias, path=path)
        _assert_capture_path(relative_path, expected_prefix="evidence/")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.backend.capture_snapshot(url=url, viewport=viewport, wait_ms=wait_ms)
        output_path.write_text(f"{json.dumps(payload, indent=2)}\n", encoding="utf-8")
        profile = self.store.save(alias=alias, evidence=[relative_path])
        return {"alias": alias, "url": url, "path": str(output_path), "relativePath": relative_path, "profile": profile}

    def capture_extract(
        self,
        *,
        alias: str,
        url: str,
        path: str,
        kind: ExtractKind,
        viewport: Viewport = "desktop",
        wait_ms: int = 1500,
        selector_limit: int = 250,
    ) -> dict[str, Any]:
        _assert_wait_ms(wait_ms)
        _assert_selector_limit(selector_limit)
        output_path, relative_path = self.store.artifact_path(alias=alias, path=path)
        _assert_capture_path(relative_path, expected_prefix="evidence/")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.backend.capture_extract(
            url=url,
            kind=kind,
            viewport=viewport,
            wait_ms=wait_ms,
            selector_limit=selector_limit,
        )
        output_path.write_text(f"{json.dumps(payload, indent=2)}\n", encoding="utf-8")
        profile = self.store.save(alias=alias, evidence=[relative_path])
        return {"alias": alias, "url": url, "path": str(output_path), "relativePath": relative_path, "profile": profile}


def _assert_capture_path(relative_path: str, *, expected_prefix: str) -> None:
    if relative_path in _RESERVED_ARTIFACT_PATHS:
        raise ValueError(f'Artifact path "{relative_path}" is reserved')
    if not relative_path.startswith(expected_prefix):
        raise ValueError(f'Artifact path "{relative_path}" must be under {expected_prefix}')


def _assert_wait_ms(wait_ms: int) -> None:
    if wait_ms < 0 or wait_ms > MAX_WAIT_MS:
        raise ValueError(f"wait_ms must be between 0 and {MAX_WAIT_MS}")


def _assert_selector_limit(selector_limit: int) -> None:
    if selector_limit < 1 or selector_limit > MAX_SELECTOR_LIMIT:
        raise ValueError(f"selector_limit must be between 1 and {MAX_SELECTOR_LIMIT}")


class PlaywrightCaptureBackend:
    def capture_screenshot(
        self,
        *,
        url: str,
        output_path: Path,
        viewport: str,
        full_page: bool,
        wait_ms: int,
    ) -> None:
        _run_async(
            lambda: self._capture_screenshot(
                url=url,
                output_path=output_path,
                viewport=viewport,
                full_page=full_page,
                wait_ms=wait_ms,
            )
        )

    def capture_snapshot(self, *, url: str, viewport: str, wait_ms: int) -> dict[str, Any]:
        return _run_async(lambda: self._capture_snapshot(url=url, viewport=viewport, wait_ms=wait_ms))

    def capture_extract(
        self,
        *,
        url: str,
        kind: str,
        viewport: str,
        wait_ms: int,
        selector_limit: int,
    ) -> Any:
        return _run_async(
            lambda: self._capture_extract(
                url=url,
                kind=kind,
                viewport=viewport,
                wait_ms=wait_ms,
                selector_limit=selector_limit,
            )
        )

    async def _capture_screenshot(
        self,
        *,
        url: str,
        output_path: Path,
        viewport: str,
        full_page: bool,
        wait_ms: int,
    ) -> None:
        async with _AsyncPage(url=url, viewport=viewport, wait_ms=wait_ms) as page:
            await page.screenshot(path=str(output_path), full_page=full_page)

    async def _capture_snapshot(self, *, url: str, viewport: str, wait_ms: int) -> dict[str, Any]:
        async with _AsyncPage(url=url, viewport=viewport, wait_ms=wait_ms) as page:
            return {
                "url": page.url,
                "title": await page.title(),
                "viewport": viewport,
                "elements": await page.evaluate(_SNAPSHOT_SCRIPT),
            }

    async def _capture_extract(
        self,
        *,
        url: str,
        kind: str,
        viewport: str,
        wait_ms: int,
        selector_limit: int,
    ) -> Any:
        async with _AsyncPage(url=url, viewport=viewport, wait_ms=wait_ms) as page:
            if kind == "links":
                return await page.evaluate(_LINKS_SCRIPT)
            if kind == "cssVariables":
                return await page.evaluate(_CSS_VARIABLES_SCRIPT)
            if kind == "computedStyles":
                return await page.evaluate(_computed_styles_script(selector_limit))
            raise ValueError(f"Unknown extract kind: {kind}")


def _run_async(coro_factory: Callable[[], Coroutine[Any, Any, T]]) -> T:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro_factory())

    results: list[T] = []
    errors: list[BaseException] = []

    def run() -> None:
        try:
            results.append(asyncio.run(coro_factory()))
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=run)
    thread.start()
    thread.join()
    if errors:
        raise errors[0]
    return results[0]


class _AsyncPage:
    def __init__(self, *, url: str, viewport: str, wait_ms: int) -> None:
        self.url = url
        self.viewport = viewport
        self.wait_ms = wait_ms
        self._async_playwright: Any = None
        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None
        self.page: Any = None

    async def __aenter__(self) -> Any:
        from playwright.async_api import async_playwright

        self._async_playwright = async_playwright()
        self._playwright = await self._async_playwright.start()
        self._browser = await self._playwright.chromium.launch()
        if self.viewport == "mobile":
            device = self._playwright.devices["iPhone 13"]
            self._context = await self._browser.new_context(**device)
        else:
            self._context = await self._browser.new_context(viewport={"width": 1440, "height": 1000})
        self.page = await self._context.new_page()
        await self.page.goto(self.url, wait_until="domcontentloaded")
        if self.wait_ms > 0:
            await self.page.wait_for_timeout(self.wait_ms)
        return self.page

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._context is not None:
            await self._context.close()
        if self._browser is not None:
            await self._browser.close()
        if self._playwright is not None:
            await self._playwright.stop()


_LINKS_SCRIPT = r"""
() => [...document.querySelectorAll('a[href]')].map((a) => {
  const r = a.getBoundingClientRect();
  const u = new URL(a.href);
  return {
    href: a.href,
    origin: u.origin,
    pathname: u.pathname,
    sameOrigin: u.origin === location.origin,
    text: (a.innerText || a.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 120),
    title: (a.getAttribute('title') || '').trim(),
    visible: r.width > 0 && r.height > 0,
    box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    inHeader: !!a.closest('header, nav'),
    inFooter: !!a.closest('footer')
  };
}).filter((link) => link.visible)
"""

_CSS_VARIABLES_SCRIPT = r"""
() => Object.fromEntries([...getComputedStyle(document.documentElement)]
  .filter((name) => name.startsWith('--'))
  .map((name) => [name, getComputedStyle(document.documentElement).getPropertyValue(name).trim()]))
"""

_SNAPSHOT_SCRIPT = r"""
() => [...document.querySelectorAll('body, header, nav, main, section, article, footer, h1, h2, h3, p, a, button, input, textarea, select')]
  .slice(0, 250)
  .map((el) => {
    const r = el.getBoundingClientRect();
    return {
      tag: el.tagName.toLowerCase(),
      role: el.getAttribute('role') || '',
      ariaLabel: el.getAttribute('aria-label') || '',
      text: (el.innerText || el.getAttribute('placeholder') || '').trim().replace(/\s+/g, ' ').slice(0, 120),
      box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]
    };
  })
"""


def _computed_styles_script(selector_limit: int) -> str:
    return rf"""
() => [...document.querySelectorAll('body, header, nav, main, section, article, footer, h1, h2, h3, p, a, button, input, textarea, select')]
  .slice(0, {selector_limit})
  .map((el) => {{
    const s = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return {{
      tag: el.tagName.toLowerCase(),
      text: (el.innerText || el.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 100),
      box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      color: s.color,
      backgroundColor: s.backgroundColor,
      fontFamily: s.fontFamily,
      fontSize: s.fontSize,
      fontWeight: s.fontWeight,
      lineHeight: s.lineHeight,
      letterSpacing: s.letterSpacing,
      margin: [s.marginTop, s.marginRight, s.marginBottom, s.marginLeft],
      padding: [s.paddingTop, s.paddingRight, s.paddingBottom, s.paddingLeft],
      border: s.border,
      borderRadius: s.borderRadius,
      boxShadow: s.boxShadow,
      transition: s.transition
    }};
  }})
"""
