"""Convertisseur page Notion → HTML."""

from __future__ import annotations

from typing import Any

from packages.ep_core.notion import NotionFetcher, page_title

from .blocks import BlockRenderer


class PageConverter:
    def __init__(self, fetcher: NotionFetcher | None = None):
        self.fetcher = fetcher
        self._title_cache: dict[str, str] = {}

    def resolve_title(self, page_id: str) -> str:
        if page_id in self._title_cache:
            return self._title_cache[page_id]
        title = page_id.replace("-", "")[:8]
        if self.fetcher is not None:
            try:
                page = self.fetcher.get_page(page_id)
                title = page_title(page) or title
            except Exception:
                pass
        self._title_cache[page_id] = title
        return title

    def render_html(
        self,
        page: dict[str, Any],
        blocks: list[dict[str, Any]],
        *,
        include_title: bool = False,
    ) -> str:
        renderer = BlockRenderer(resolve_title=self.resolve_title)
        body = renderer.render_blocks(blocks)
        if include_title:
            title = page_title(page)
            if title:
                body = f"<h1>{title}</h1>{body}"
        return body
