"""Extraction base Jurisprudence — propriétés uniquement."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from packages.ep_core.notion import extract_page_properties, page_title
from packages.ep_core.paths import resolve_path

from ._common import database_url, make_fetcher, write_json_export

EXCLUDE = {"Sources insuffisantes"}
DATE_PROP = "Date"
_DATE_PREFIX = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def _parse_date(value: Any) -> str | None:
    if isinstance(value, dict):
        raw = (value.get("start") or "").strip()
    else:
        raw = str(value or "").strip()
        if "→" in raw:
            raw = raw.split("→", 1)[0].strip()
    m = _DATE_PREFIX.match(raw)
    return m.group(1) if m else None


def _sort_pages(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(page: dict[str, Any]) -> tuple:
        props = page.get("properties") or {}
        d = _parse_date(props.get(DATE_PROP))
        title = (page.get("title") or "").casefold()
        if d:
            return (0, d, title)
        return (1, "9999-99-99", title)

    return sorted(pages, key=key)


def _collect_property_names(pages: list[dict[str, Any]]) -> list[str]:
    names: set[str] = set()
    for page in pages:
        names.update((page.get("properties") or {}).keys())
    ordered = sorted(names, key=lambda s: (s != "Nom", s.lower()))
    return ordered


def export_jurisprudence(
    *,
    limit: int | None = None,
    output: Path | None = None,
) -> Path:
    """Exporte toutes les propriétés sauf « Sources insuffisantes » (sans corps de page)."""
    fetcher = make_fetcher()
    db = database_url("jurisprudence")
    out_path = output or (resolve_path("matrices_jurisprudence") / "jurisprudence.json")

    print(f"Jurisprudence — lecture Notion ({db})…")
    raw_pages = list(
        fetcher.iter_database_pages(
            db,
            limit=limit,
            sorts=[{"property": DATE_PROP, "direction": "ascending"}],
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
                "properties": extract_page_properties(page, exclude=EXCLUDE),
            }
        )

    pages = _sort_pages(pages)
    prop_names = _collect_property_names(pages)

    path = write_json_export(
        out_path,
        database="jurisprudence",
        database_url=db,
        property_names=prop_names,
        pages=pages,
        excluded_properties=sorted(EXCLUDE),
        includes_content=False,
    )
    print(f"Écrit : {path}")
    return path
