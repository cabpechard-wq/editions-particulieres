"""Assemblage du manuel HTML (sommaire + chapitres imbriqués)."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Callable

from .manuel_tree import (
    build_breadcrumb_html,
    build_nav_tree_html,
    parent_digits,
    render_chapter_link,
    sort_key_ref,
)


def write_aside_readme(aside_dir: Path, aside_chapters: list[dict[str, Any]]) -> None:
    aside_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Fiches mises de côte — registre actualité",
        "",
        "Hors arborescence du manuel.",
        "",
    ]
    for ch in aside_chapters:
        lines.append(f"- {ch['title']} → `{ch['slug']}/`")
    (aside_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_site_assets(templates: Path, site_root: Path) -> None:
    site_root.mkdir(parents=True, exist_ok=True)
    for asset in ("site.css", "site-nav.js"):
        src = templates / asset
        if src.exists():
            shutil.copy2(src, site_root / asset)
    # auth.js est généré par build_membre_gate.py (URL API injectée) — ne pas l'écraser.


def build_manuel_site(
    chapters: list[dict[str, Any]],
    aside: list[dict[str, Any]],
    *,
    templates: Path,
    site_root: Path,
    log: Callable[[str], None] | None = None,
) -> Path:
    """Écrit site_root/manuel/ (+ _aside/). Retourne le dossier manuel."""
    _log = log or (lambda _s: None)
    manuel_dir = site_root / "manuel"
    aside_dir = manuel_dir / "_aside"

    chapters = sorted(chapters, key=lambda c: sort_key_ref(c["ref"]))
    by_digits = {c["digits"]: c for c in chapters}

    for ch in chapters:
        p = parent_digits(ch["digits"])
        if p and p not in by_digits and p != "000":
            _log(f"! Parent manquant pour {ch['ref']} (attendu DP-{p})\n")

    if manuel_dir.exists():
        shutil.rmtree(manuel_dir)
    manuel_dir.mkdir(parents=True, exist_ok=True)

    page_tpl = (templates / "manuel-page.html").read_text(encoding="utf-8")
    for i, ch in enumerate(chapters):
        prev_ch = chapters[i - 1] if i > 0 else None
        next_ch = chapters[i + 1] if i + 1 < len(chapters) else None
        from .manuel_tree import asset_prefix, rel_between

        prefix = asset_prefix(ch["depth"])
        nav = build_nav_tree_html(
            chapters, from_segs=ch["segments"], current_digits=ch["digits"]
        )
        crumb = build_breadcrumb_html(ch, by_digits)
        page = (
            page_tpl.replace("{{TITLE}}", ch["title_esc"])
            .replace("{{CRUMB_TRAIL}}", crumb)
            .replace("{{BODY}}", ch["body"])
            .replace("{{ASSET_PREFIX}}", prefix)
            .replace("{{NAV_TREE}}", nav)
            .replace("{{TOC_HREF}}", rel_between(ch["segments"], []))
            .replace(
                "{{PREV_LINK}}",
                render_chapter_link(prev_ch, kind="prev", from_segs=ch["segments"]),
            )
            .replace(
                "{{NEXT_LINK}}",
                render_chapter_link(next_ch, kind="next", from_segs=ch["segments"]),
            )
        )
        chapter_dir = manuel_dir.joinpath(*ch["segments"])
        chapter_dir.mkdir(parents=True, exist_ok=True)
        (chapter_dir / "index.html").write_text(page, encoding="utf-8")

    if aside:
        aside_tpl = page_tpl
        for ch in aside:
            from .manuel_tree import asset_prefix

            prefix = asset_prefix(2)
            page = (
                aside_tpl.replace("{{TITLE}}", ch["title_esc"])
                .replace(
                    "{{CRUMB_TRAIL}}",
                    f'    <a href="{prefix}index.html">Droit public et administratif</a>\n'
                    '    <span class="sep">›</span>\n'
                    f'    <a href="{prefix}bibliotheque/">Bibliothèque universitaire</a>\n'
                    '    <span class="sep">›</span>\n'
                    f'    <a href="../">Cours</a>\n'
                    '    <span class="sep">›</span>\n'
                    f'    <strong>{ch["title_esc"]}</strong>',
                )
                .replace("{{BODY}}", ch["body"])
                .replace("{{ASSET_PREFIX}}", prefix)
                .replace("{{NAV_TREE}}", "")
                .replace("{{TOC_HREF}}", "../")
                .replace("{{PREV_LINK}}", "")
                .replace("{{NEXT_LINK}}", "")
            )
            d = aside_dir / ch["slug"]
            d.mkdir(parents=True, exist_ok=True)
            (d / "index.html").write_text(page, encoding="utf-8")
        write_aside_readme(aside_dir, aside)

    sommaire_tpl = (templates / "manuel-sommaire.html").read_text(encoding="utf-8")
    nav_sommaire = build_nav_tree_html(chapters, from_segs=None, skip_root=True)
    sommaire = sommaire_tpl.replace("{{NAV_TREE}}", nav_sommaire).replace(
        "{{CHAPTER_COUNT}}", str(len(chapters))
    )
    (manuel_dir / "index.html").write_text(sommaire, encoding="utf-8")

    copy_site_assets(templates, site_root)
    return manuel_dir
