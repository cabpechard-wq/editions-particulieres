"""Export fiches jurisprudence → site /arrets/."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .arrets_render import (
    FILTER_JS,
    _dedupe_slugs,
    entry_from_page,
    render_index_body,
)
from .site_links import SiteLinkRegistry


def build_arrets_site(
    pages: list[dict[str, Any]],
    *,
    templates: Path,
    site_root: Path,
    registry: SiteLinkRegistry | None = None,
    resolve_title: Callable[[str], str] | None = None,
    log: Callable[[str], None] | None = None,
) -> Path:
    _log = log or (lambda _s: None)
    entries: list[dict] = []
    for page in pages:
        entry = entry_from_page(
            page,
            registry=registry,
            resolve_title=resolve_title,
            asset_prefix="../../",
        )
        if entry:
            entries.append(entry)

    if not entries:
        raise ValueError("Aucune fiche jurisprudence exportable.")

    entries.sort(key=lambda e: (e.get("date_sort") or "", e["title"]), reverse=True)
    _dedupe_slugs(entries)

    index_tpl = templates / "arrets-index.html"
    fiche_tpl = templates / "arrets-fiche.html"
    if not index_tpl.is_file() or not fiche_tpl.is_file():
        raise FileNotFoundError("Gabarits arrets-index.html / arrets-fiche.html manquants")

    arrets_dir = site_root / "arrets"
    if arrets_dir.exists():
        import shutil

        shutil.rmtree(arrets_dir)
    arrets_dir.mkdir(parents=True, exist_ok=True)

    filters_html, list_html = render_index_body(entries)
    index_page = (
        index_tpl.read_text(encoding="utf-8")
        .replace("{{ENTRY_COUNT}}", str(len(entries)))
        .replace("{{ARRETS_FILTERS}}", filters_html)
        .replace("{{ARRETS_LIST}}", list_html)
        .replace("{{FILTER_JS}}", FILTER_JS)
    )
    (arrets_dir / "index.html").write_text(index_page, encoding="utf-8")

    fiche_tpl_text = fiche_tpl.read_text(encoding="utf-8")
    for entry in entries:
        slug_dir = arrets_dir / entry["slug"]
        slug_dir.mkdir(parents=True, exist_ok=True)
        page = (
            fiche_tpl_text.replace("{{TITLE}}", entry["title"])
            .replace("{{BODY}}", entry["body_html"])
            .replace("{{ASSET_PREFIX}}", "../../")
        )
        (slug_dir / "index.html").write_text(page, encoding="utf-8")

    linked = sum(1 for e in entries if "dict-extra" in (e.get("body_html") or ""))
    _log(f"OK arrêts : {len(entries)} fiche(s) → {arrets_dir}\n")
    if registry is not None:
        _log(f"   {linked}/{len(entries)} fiche(s) avec renvois Cours / Index\n")
    return arrets_dir
