"""Lightweight asynchronous web crawler for mapping site structure."""

from __future__ import annotations

import asyncio
from html.parser import HTMLParser
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import aiohttp

from modules.js_renderer import JSRenderer


class _StructureParser(HTMLParser):
    """Extract links, forms, and static asset references from HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.links: Set[str] = set()
        self.forms: List[Dict[str, str]] = []
        self.scripts: Set[str] = set()
        self.stylesheets: Set[str] = set()
        self.images: Set[str] = set()

    def handle_starttag(self, tag: str, attrs):  # type: ignore[override]
        attr_map = {name.lower(): value for name, value in attrs}
        if tag == "a":
            href = attr_map.get("href")
            if href:
                self.links.add(href)
        elif tag == "form":
            action = attr_map.get("action", "")
            method = attr_map.get("method", "GET").upper()
            self.forms.append({"action": action, "method": method})
        elif tag == "script":
            src = attr_map.get("src")
            if src:
                self.scripts.add(src)
        elif tag == "link":
            rel = attr_map.get("rel", "")
            href = attr_map.get("href")
            if href and "stylesheet" in rel.lower():
                self.stylesheets.add(href)
        elif tag == "img":
            src = attr_map.get("src")
            if src:
                self.images.add(src)


def _should_visit(link: str, base_netloc: str) -> bool:
    parsed = urlparse(link)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc and parsed.netloc != base_netloc:
        return False
    return True


async def crawl_site(
    session: aiohttp.ClientSession,
    base_url: str,
    max_pages: int = 30,
    max_depth: int = 2,
    timeout: int = 8,
    enable_js: bool = True,
) -> Dict[str, object]:
    """Breadth-first crawl to map internal links, forms, and static assets."""

    async def _crawl(renderer: Optional[JSRenderer]) -> Dict[str, object]:
        parsed_base = urlparse(base_url)
        resolved_base = base_url
        if not parsed_base.scheme:
            resolved_base = f"https://{base_url}"
            parsed_base = urlparse(resolved_base)

        if not parsed_base.netloc:
            return {}

        if not parsed_base.path:
            parsed_base = parsed_base._replace(path="/")
            resolved_base = parsed_base.geturl()

        visited: Set[str] = set()
        to_visit: asyncio.Queue = asyncio.Queue()
        await to_visit.put((resolved_base, 0))

        discovered_links: Set[str] = set()
        forms: List[Dict[str, str]] = []
        static_assets: Dict[str, Set[str]] = {
            "scripts": set(),
            "stylesheets": set(),
            "images": set(),
        }
        api_endpoints: Set[str] = set()
        js_rendered_pages = 0

        async def fetch(url: str) -> Optional[str]:
            try:
                async with session.get(url, timeout=timeout, ssl=False) as response:
                    content_type = response.headers.get("Content-Type", "")
                    if "text/html" not in content_type:
                        return None
                    return await response.text()
            except Exception:  # noqa: BLE001
                return None

        def _normalized_base(url: str) -> str:
            parsed = urlparse(url)
            if not parsed.path:
                parsed = parsed._replace(path="/")
            return parsed.geturl()

        while not to_visit.empty() and len(visited) < max_pages:
            current_url, depth = await to_visit.get()
            if current_url in visited:
                continue
            visited.add(current_url)

            html = await fetch(current_url)
            base_parser = _StructureParser()
            if html:
                base_parser.feed(html)

            has_meaningful_link = False
            base_for_join = _normalized_base(current_url)
            for link_candidate in base_parser.links:
                absolute_candidate = urljoin(base_for_join, link_candidate)
                if _should_visit(absolute_candidate, parsed_base.netloc) and absolute_candidate != current_url:
                    has_meaningful_link = True
                    break

            js_parser: Optional[_StructureParser] = None
            js_result = None
            if renderer and renderer.ready and (not html or not has_meaningful_link):
                js_result = await renderer.render(current_url, timeout_ms=timeout * 1000)
                if js_result and js_result.html:
                    js_parser = _StructureParser()
                    js_parser.feed(js_result.html)
                    html = js_result.html
                    js_rendered_pages += 1
                    for nav_url in js_result.navigated_urls:
                        if nav_url != current_url and _should_visit(nav_url, parsed_base.netloc):
                            discovered_links.add(nav_url)
                            if depth + 1 <= max_depth and nav_url not in visited:
                                await to_visit.put((nav_url, depth + 1))

            if not html:
                continue

            combined_links = set(base_parser.links)
            combined_forms = list(base_parser.forms)
            combined_assets = {
                "scripts": set(base_parser.scripts),
                "stylesheets": set(base_parser.stylesheets),
                "images": set(base_parser.images),
            }

            if js_parser:
                combined_links.update(js_parser.links)
                for form in js_parser.forms:
                    if form not in combined_forms:
                        combined_forms.append(form)
                combined_assets["scripts"].update(js_parser.scripts)
                combined_assets["stylesheets"].update(js_parser.stylesheets)
                combined_assets["images"].update(js_parser.images)

            for form in combined_forms:
                action = urljoin(current_url, form.get("action", "")) if form.get("action") else current_url
                form_entry = {"method": form.get("method", "GET"), "action": action}
                if form_entry not in forms:
                    forms.append(form_entry)
                if "/api/" in action or action.endswith(".json"):
                    api_endpoints.add(action)

            for asset_type, values in combined_assets.items():
                for rel_src in values:
                    static_assets[asset_type].add(urljoin(current_url, rel_src))

            for link in combined_links:
                absolute = urljoin(base_for_join, link)
                if not _should_visit(absolute, parsed_base.netloc):
                    continue
                discovered_links.add(absolute)
                if depth + 1 <= max_depth and absolute not in visited:
                    await to_visit.put((absolute, depth + 1))
                if "/api/" in absolute or absolute.endswith(".json"):
                    api_endpoints.add(absolute)

        return {
            "visited_count": len(visited),
            "pages": sorted(discovered_links)[:max_pages],
            "forms": forms,
            "static_assets": {key: sorted(list(values)) for key, values in static_assets.items()},
            "api_endpoints": sorted(list(api_endpoints)),
            "js_rendered_pages": js_rendered_pages,
            "js_enabled": bool(renderer and renderer.ready),
            "js_error": renderer.error if renderer and renderer.error else None,
        }

    if enable_js:
        async with JSRenderer() as renderer:
            return await _crawl(renderer)
    return await _crawl(None)
