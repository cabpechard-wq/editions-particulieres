"""Résolution des pages Notion pour l'export Word."""

from __future__ import annotations

import re
from typing import Any, Callable

from packages.ep_core.notion import NotionFetcher, page_title, property_plain
from packages.ep_core.notion.ids import to_uuid

_REF = re.compile(r"(\d+)")


def try_uuid(raw: str) -> str | None:
    try:
        return to_uuid(raw)
    except ValueError:
        return None


def page_reference(page: dict[str, Any]) -> str:
    props = page.get("properties") or {}
    lower = {k.lower(): k for k in props}
    for name in ("référence", "reference"):
        key = lower.get(name)
        if key:
            return property_plain(props[key]).strip()
    return ""


def _alnum_key(s: str) -> list:
    parts = _REF.split((s or "").strip())
    key: list = []
    for p in parts:
        if not p:
            continue
        if p.isdigit():
            key.append((0, int(p)))
        else:
            key.append((1, p.casefold()))
    return key


def sort_pages_by_reference(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(page: dict[str, Any]) -> tuple:
        ref = page_reference(page)
        title = (page_title(page) or "").casefold()
        return (0 if ref else 1, _alnum_key(ref), _alnum_key(title))

    return sorted(pages, key=key)


def find_pages_by_query(
    fetcher: NotionFetcher,
    database: str,
    query: str,
    *,
    exclude_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    exclude_ids = exclude_ids or set()
    q = (query or "").strip()
    if not q:
        return []

    pid = try_uuid(q)
    if pid:
        try:
            page = fetcher.get_page(pid)
        except Exception:
            return []
        if page["id"] in exclude_ids:
            return []
        return [page]

    needle = q.casefold()
    for page in fetcher.iter_database_pages(database):
        if page["id"] in exclude_ids:
            continue
        title = (page_title(page) or "").casefold()
        compact_id = page["id"].replace("-", "")
        if needle in title or needle in compact_id:
            return [page]
    return []


def load_notion_pages(
    fetcher: NotionFetcher,
    *,
    database: str,
    page_queries: list[str],
    limit: int | None,
    log: Callable[[str], None] | None = None,
    exclude_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    exclude_ids = exclude_ids or set()
    _log = log or (lambda _s: None)

    if page_queries:
        pages: list[dict[str, Any]] = []
        seen: set[str] = set()
        for q in page_queries:
            q = q.strip()
            if not q:
                continue
            found = find_pages_by_query(
                fetcher, database, q, exclude_ids=exclude_ids | seen
            )
            if not found:
                _log(f"  ? introuvable dans la base : {q!r}\n")
                continue
            for page in found:
                if page["id"] not in seen:
                    seen.add(page["id"])
                    pages.append(page)
        return pages

    pages = []
    for page in fetcher.iter_database_pages(database, limit=limit):
        if page["id"] in exclude_ids:
            continue
        pages.append(page)
    return pages


def filename_for_page(page: dict[str, Any], label: str) -> str:
    from packages.ep_core.naming import sanitize_filename

    ref = page_reference(page)
    if ref:
        return sanitize_filename(f"{ref} - {label}")
    return sanitize_filename(label)
