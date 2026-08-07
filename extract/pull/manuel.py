"""Extraction base Manuel — propriétés + contenu de page."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from packages.ep_core.notion import (
    extract_page_properties,
    page_title,
    serialize_block_tree,
)
from packages.ep_core.paths import resolve_path

from ._common import database_url, make_fetcher, write_json_export

REF_PROP = "Référence"
_ALNUM = re.compile(r"(\d+)")


def _alnum_key(s: str) -> list:
    parts = _ALNUM.split((s or "").strip())
    key: list = []
    for p in parts:
        if not p:
            continue
        if p.isdigit():
            key.append((0, int(p)))
        else:
            key.append((1, p.casefold()))
    return key


def _reference(props: dict[str, Any]) -> str:
    ref = props.get(REF_PROP) or props.get("Reference") or ""
    return str(ref).strip()


def _sort_pages(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(page: dict[str, Any]) -> tuple:
        ref = _reference(page.get("properties") or {})
        title = (page.get("title") or "").casefold()
        return (0 if ref else 1, _alnum_key(ref), _alnum_key(title))

    return sorted(pages, key=key)


def _collect_property_names(pages: list[dict[str, Any]]) -> list[str]:
    names: set[str] = set()
    for page in pages:
        names.update((page.get("properties") or {}).keys())
    return sorted(names, key=lambda s: (s != "Titre", s.lower()))


def export_manuel(
    *,
    limit: int | None = None,
    output: Path | None = None,
) -> Path:
    """Exporte toutes les propriétés + l'arbre de blocs de chaque page."""
    fetcher = make_fetcher()
    db = database_url("manuel")
    out_path = output or (resolve_path("export_manuel") / "manuel.json")

    print(f"Manuel — lecture Notion ({db})…")
    raw_pages = list(
        fetcher.iter_database_pages(
            db,
            limit=limit,
            sorts=[{"property": REF_PROP, "direction": "ascending"}],
        )
    )
    print(f"  {len(raw_pages)} pages")

    pages: list[dict[str, Any]] = []
    for i, page in enumerate(raw_pages, 1):
        title = page_title(page)
        print(f"  [{i}/{len(raw_pages)}] contenu {title[:60]!r}")
        blocks = fetcher.get_block_tree(page["id"])
        pages.append(
            {
                "id": page["id"],
                "url": page.get("url") or "",
                "title": title,
                "properties": extract_page_properties(page),
                "content": serialize_block_tree(blocks),
            }
        )

    pages = _sort_pages(pages)
    prop_names = _collect_property_names(pages)

    path = write_json_export(
        out_path,
        database="manuel",
        database_url=db,
        property_names=prop_names,
        pages=pages,
        includes_content=True,
    )
    print(f"Écrit : {path}")
    return path
