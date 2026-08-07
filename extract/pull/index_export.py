"""Extraction base Index — propriétés uniquement."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from packages.ep_core.notion import extract_page_properties, page_title
from packages.ep_core.paths import resolve_path

from ._common import database_url, make_fetcher, write_json_export

TITLE_PROP = "Entrée"


def _sort_pages(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(page: dict[str, Any]) -> tuple:
        props = page.get("properties") or {}
        entry = str(props.get(TITLE_PROP) or page.get("title") or "").casefold()
        return (entry,)

    return sorted(pages, key=key)


def _collect_property_names(pages: list[dict[str, Any]]) -> list[str]:
    names: set[str] = set()
    for page in pages:
        names.update((page.get("properties") or {}).keys())
    return sorted(names, key=lambda s: (s != TITLE_PROP, s.lower()))


def export_index(
    *,
    limit: int | None = None,
    output: Path | None = None,
) -> Path:
    """Exporte toutes les propriétés (sans corps de page)."""
    fetcher = make_fetcher()
    db = database_url("index")
    out_path = output or (resolve_path("export_index") / "index.json")

    print(f"Index — lecture Notion ({db})…")
    raw_pages = list(
        fetcher.iter_database_pages(
            db,
            limit=limit,
            sorts=[{"property": TITLE_PROP, "direction": "ascending"}],
        )
    )
    print(f"  {len(raw_pages)} pages")

    pages: list[dict[str, Any]] = []
    for page in raw_pages:
        pages.append(
            {
                "id": page["id"],
                "url": page.get("url") or "",
                "title": page_title(page),
                "properties": extract_page_properties(page),
            }
        )

    pages = _sort_pages(pages)
    prop_names = _collect_property_names(pages)

    path = write_json_export(
        out_path,
        database="index",
        database_url=db,
        property_names=prop_names,
        pages=pages,
        includes_content=False,
    )
    print(f"Écrit : {path}")
    return path
