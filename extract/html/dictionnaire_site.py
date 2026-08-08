"""Export glossaire Notion → site /dictionnaire/."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Callable

from packages.ep_core.notion import page_title, property_plain

from extract.word.pages import page_reference

from .converter import PageConverter
from .dictionnaire_render import (
    FILTER_JS,
    _dedupe_slugs,
    build_manuel_title_map,
    letter_key,
    render_body,
    slugify,
    sort_entries,
)
from .manuel_tree import manuel_digits, pad_digits, path_segments_for
from .site_links import SiteLinkRegistry, relation_ids, render_relation_extras


def _norm(name: str) -> str:
    return (name or "").strip().casefold()


def _prop_text(props: dict[str, Any], *names: str) -> str:
    for name, prop in props.items():
        if _norm(name) in names:
            return property_plain(prop).strip()
    return ""


def manuel_roots_for(site_root: Path) -> list[Path]:
    roots = [site_root / "manuel"]
    try:
        from packages.ep_core.paths import resolve_path

        export_manuel = resolve_path("export_site") / "manuel"
        if export_manuel not in roots:
            roots.insert(0, export_manuel)
    except (KeyError, OSError):
        pass
    return roots


def manuel_href_for_page(
    fetcher,
    page_id: str,
    *,
    title_map: dict[str, str],
    resolve_title: Callable[[str], str],
) -> tuple[str | None, str]:
    title = resolve_title(page_id)
    try:
        page = fetcher.get_page(page_id)
    except Exception:
        return title_map.get(_norm_key(title)), title

    ref = page_reference(page)
    digits = manuel_digits(ref)
    if digits:
        segs = path_segments_for(pad_digits(digits))
        return "../manuel/" + "/".join(segs) + "/", page_title(page) or title

    from .dictionnaire_render import norm_title

    key = norm_title(page_title(page) or title)
    href = title_map.get(key)
    return href, page_title(page) or title


def _norm_key(s: str) -> str:
    from .dictionnaire_render import norm_title

    return norm_title(s)


def entries_from_units(
    units,
    fetcher,
    *,
    manuel_roots: list[Path],
    registry: SiteLinkRegistry | None = None,
) -> list[dict]:
    converter = PageConverter(fetcher)
    title_map = build_manuel_title_map(manuel_roots)
    entries: list[dict] = []
    prefix = "../"

    for unit in units:
        if unit.kind != "index" or unit.page is None:
            continue
        page = unit.page
        props = page.get("properties") or {}
        term = page_title(page) or unit.label
        definition = _prop_text(props, "définition", "definition")
        blocks = unit.blocks or []

        if definition:
            definition_html = f"<p>{html.escape(definition)}</p>"
        elif blocks:
            definition_html = converter.render_html(page, blocks, include_title=False)
        else:
            continue

        extras: list[str] = []

        manuel_links: list[str] = []
        for pid in relation_ids(props, "manuel"):
            href = None
            link_title = ""
            if registry is not None:
                target = registry.resolve(pid)
                if target and target.kind == "manuel":
                    href = registry.href(target, prefix=prefix)
                    link_title = target.title
            if not href:
                href, link_title = manuel_href_for_page(
                    fetcher,
                    pid,
                    title_map=title_map,
                    resolve_title=converter.resolve_title,
                )
            if href:
                if not link_title:
                    link_title = converter.resolve_title(pid)
                manuel_links.append(
                    f'<a href="{html.escape(href, quote=True)}">'
                    f"{html.escape(link_title)}</a>"
                )
        if manuel_links:
            extras.append(f'<p class="dict-extra">Cours : {" · ".join(manuel_links)}</p>')

        if registry is not None:
            jur = render_relation_extras(
                props,
                registry,
                keys=("jurisprudence",),
                prefix=prefix,
                resolve_title=converter.resolve_title,
                section=False,
            )
            if jur:
                extras.append(jur)

        entries.append(
            {
                "term": term,
                "definition_html": definition_html,
                "extras_html": "\n".join(extras),
                "slug": slugify(term),
                "letter": letter_key(term),
            }
        )

    sort_entries(entries)
    _dedupe_slugs(entries)
    return entries


def build_dictionnaire_site(
    entries: list[dict],
    *,
    templates: Path,
    site_root: Path,
    log: Callable[[str], None] | None = None,
) -> Path:
    _log = log or (lambda _s: None)
    if not entries:
        raise ValueError("Aucune entrée de glossaire.")

    tpl_path = templates / "dictionnaire.html"
    if not tpl_path.is_file():
        raise FileNotFoundError(f"Gabarit manquant : {tpl_path}")

    linked = sum(1 for e in entries if e["extras_html"])
    _log(f"   {linked}/{len(entries)} entrée(s) avec renvois Cours / Jurisprudence\n")

    tpl = tpl_path.read_text(encoding="utf-8")
    index_html, body_html = render_body(entries)
    page = (
        tpl.replace("{{ENTRY_COUNT}}", str(len(entries)))
        .replace("{{DICT_INDEX}}", index_html)
        .replace("{{DICT_BODY}}", body_html)
        .replace("{{FILTER_JS}}", FILTER_JS)
    )

    dst = site_root / "dictionnaire"
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "index.html").write_text(page, encoding="utf-8")
    _log(f"OK dictionnaire : {len(entries)} entrée(s) → {dst}\n")
    return dst
