"""Liens Manuel → glossaire local (/dictionnaire/#slug)."""

from __future__ import annotations

import re
from typing import Any

from packages.ep_core.notion import NotionFetcher, page_title
from packages.ep_core.notion.ids import to_uuid

from .dictionnaire_render import slugify
from .manuel_tree import asset_prefix

_NOTION_LINK_RE = re.compile(
    r'<a\s+href="(https://(?:www\.|app\.)?notion\.(?:so|com)/[^"]+)"\s+rel="noopener">(.*?)</a>',
    re.I | re.S,
)


def build_glossary_slug_map(fetcher: NotionFetcher | None) -> dict[str, str]:
    """ID Notion (UUID ou compact) → slug d'entrée dictionnaire."""
    if fetcher is None:
        return {}
    try:
        from extract.pull._common import database_url

        db = database_url("index")
    except (ValueError, KeyError, OSError):
        return {}

    out: dict[str, str] = {}
    try:
        for page in fetcher.iter_database_pages(db):
            pid = (page.get("id") or "").lower()
            if not pid:
                continue
            term = (page_title(page) or "").strip()
            if not term:
                continue
            slug = slugify(term)
            out[pid] = slug
            out[pid.replace("-", "")] = slug
    except Exception:
        return out
    return out


def _slug_for_url(url: str, slug_map: dict[str, str]) -> str | None:
    try:
        pid = to_uuid(url).lower()
    except ValueError:
        return None
    return slug_map.get(pid) or slug_map.get(pid.replace("-", ""))


def rewrite_glossary_links(body: str, slug_map: dict[str, str], *, dict_prefix: str) -> str:
    if not slug_map or not body:
        return body

    prefix = dict_prefix if dict_prefix.endswith("/") else f"{dict_prefix}/"

    def repl(m: re.Match[str]) -> str:
        slug = _slug_for_url(m.group(1), slug_map)
        if not slug:
            return m.group(0)
        inner = m.group(2)
        return (
            f'<a class="dict-link" href="{prefix}dictionnaire/#{slug}">{inner}</a>'
        )

    return _NOTION_LINK_RE.sub(repl, body)


def dict_prefix_for_chapter(chapter: dict[str, Any]) -> str:
    return asset_prefix(len(chapter.get("segments") or []))


def dict_prefix_for_aside() -> str:
    return asset_prefix(2)
