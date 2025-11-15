"""Optional Playwright-backed renderer to execute JavaScript when crawling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

try:
    from playwright.async_api import (  # type: ignore
        TimeoutError as PlaywrightTimeoutError,
        async_playwright,
    )
except ImportError:  # Playwright is optional; crawler must handle absence.
    async_playwright = None  # type: ignore
    PlaywrightTimeoutError = Exception  # type: ignore[misc,assignment]


@dataclass
class RenderResult:
    """Result returned when a page is rendered with JavaScript enabled."""

    html: str
    navigated_urls: List[str]


class JSRenderer:
    """Lightweight async wrapper around Playwright for optional JS rendering."""

    def __init__(self) -> None:
        self._manager = None
        self._playwright = None
        self._browser = None
        self._context = None
        self._enabled = async_playwright is not None
        self.ready = False
        self.error: Optional[str] = None

    async def _cleanup(self) -> None:
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._manager:
            try:
                await self._manager.__aexit__(None, None, None)
            except Exception:  # noqa: BLE001
                pass
        self._context = None
        self._browser = None
        self._playwright = None
        self._manager = None
        self.ready = False

    async def __aenter__(self) -> "JSRenderer":
        if not self._enabled:
            return self
        self._manager = async_playwright()
        try:
            self._playwright = await self._manager.__aenter__()  # type: ignore[union-attr]
            self._browser = await self._playwright.chromium.launch(headless=True)  # type: ignore[union-attr]
            self._context = await self._browser.new_context(ignore_https_errors=True)  # type: ignore[union-attr]
            self.ready = True
        except Exception as exc:  # noqa: BLE001
            self.error = str(exc)
            await self._cleanup()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: D401, ANN001
        if not self._enabled:
            return
        await self._cleanup()

    async def render(self, url: str, timeout_ms: int = 8000) -> Optional[RenderResult]:
        """Render the URL in a headless browser and return the final DOM."""

        if not self.ready or self._context is None:
            return None

        page = await self._context.new_page()
        navigated: List[str] = []

        def _on_navigation(frame) -> None:  # noqa: ANN001
            frame_url = getattr(frame, "url", "")
            if frame_url:
                navigated.append(frame_url)

        page.on("framenavigated", _on_navigation)

        try:
            await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
        except PlaywrightTimeoutError:
            # Timeout is acceptable; we'll capture whatever DOM is available.
            pass
        except Exception:
            await page.close()
            return None

        try:
            html = await page.content()
        except Exception:
            html = ""

        await page.close()

        if not html:
            return None

        unique_urls = []
        for nav_url in navigated:
            if nav_url not in unique_urls:
                unique_urls.append(nav_url)

        return RenderResult(html=html, navigated_urls=unique_urls)
