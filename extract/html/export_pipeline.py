"""Pipeline d'export HTML — branché sur la GUI."""

from __future__ import annotations

import html as html_mod
import re
from pathlib import Path

from packages.ep_core.naming import sanitize_filename, stamped_path
from packages.ep_core.notion import page_title
from packages.ep_core.paths import REPO_ROOT, resolve_path

from extract.pull._common import load_env
from extract.word.export_pipeline import _collect_units

from .converter import PageConverter
from .arrets_site import build_arrets_site
from .dictionnaire_site import build_dictionnaire_site, entries_from_units, manuel_roots_for
from .manuel_links import (
    build_glossary_slug_map,
    dict_prefix_for_aside,
    dict_prefix_for_chapter,
    rewrite_glossary_links,
)
from .manuel_site import build_manuel_site
from .manuel_tree import classify_chapter
from extract.word.pages import page_reference


def _default_site_templates() -> Path:
    try:
        return Path(resolve_path("templates_site"))
    except (KeyError, OSError):
        return REPO_ROOT / "site" / "templates"


def resolve_site_root(out: Path) -> Path:
    out = Path(out)
    if (out / "index.html").is_file() or (out / "checkout").is_dir():
        return out
    try:
        return resolve_path("export_site")
    except (KeyError, OSError):
        site = out / "site"
        site.mkdir(parents=True, exist_ok=True)
        return site


def _flat_page_html(title: str, body: str) -> str:
    title_esc = html_mod.escape(title)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="fr">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        f"<title>{title_esc}</title>\n"
        "</head>\n"
        "<body>\n"
        f'<main class="legal-prose"><h1>{title_esc}</h1>{body}</main>\n'
        "</body>\n"
        "</html>\n"
    )


def _slugify(name: str) -> str:
    slug = sanitize_filename(name).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return slug or "page"


def _check_manuel_templates(templates: Path) -> str | None:
    for name in ("manuel-page.html", "manuel-sommaire.html"):
        if not (templates / name).is_file():
            return f"Gabarit manquant : {templates / name}"
    return None


def export_manuel_html(req, units, fetcher, templates: Path) -> tuple[int, list[Path]]:
    converter = PageConverter(fetcher)
    glossary_map = build_glossary_slug_map(fetcher)
    if glossary_map:
        req.log(f"Glossaire : {len(set(glossary_map.values()))} entrée(s) pour les liens Manuel\n")
    chapters: list[dict] = []
    aside: list[dict] = []
    skipped: list[str] = []

    for unit in units:
        if unit.kind != "manuel" or unit.page is None:
            continue
        title = page_title(unit.page) or unit.label
        ref = page_reference(unit.page)
        body = converter.render_html(unit.page, unit.blocks or [])
        chapter, aside_item, skip = classify_chapter(title=title, ref=ref, body=body)
        if skip:
            skipped.append(skip)
            continue
        if chapter:
            chapter["body"] = rewrite_glossary_links(
                chapter["body"],
                glossary_map,
                dict_prefix=dict_prefix_for_chapter(chapter),
            )
            chapters.append(chapter)
        if aside_item:
            aside_item["body"] = rewrite_glossary_links(
                aside_item["body"],
                glossary_map,
                dict_prefix=dict_prefix_for_aside(),
            )
            aside.append(aside_item)

    if not chapters and not aside:
        req.log("Aucune page manuel classée (réf. DP-XXX).\n")
        return 1, []

    site_root = resolve_site_root(Path(req.out))
    manuel_dir = build_manuel_site(
        chapters,
        aside,
        templates=templates,
        site_root=site_root,
        log=req.log,
    )
    req.log(f"OK manuel : {len(chapters)} chapitre(s) → {manuel_dir}\n")
    if aside:
        req.log(f"   {len(aside)} fiche(s) actualité → {manuel_dir / '_aside'}\n")
    if skipped:
        req.log(f"   {len(skipped)} ignorée(s)\n")
        for s in skipped[:8]:
            req.log(f"     - {s}\n")
    return 0, [manuel_dir / "index.html"]


def export_dictionnaire_html(req, units, fetcher, templates: Path) -> tuple[int, list[Path]]:
    site_root = resolve_site_root(Path(req.out))
    manuel_roots = manuel_roots_for(site_root)
    if not build_manuel_title_map_safe(manuel_roots):
        req.log(
            "Attention : aucune page Manuel trouvée — les liens « Manuel » seront limités.\n"
        )

    index_units = [u for u in units if u.kind == "index"]
    entries = entries_from_units(index_units, fetcher, manuel_roots=manuel_roots)
    if not entries:
        req.log("Aucune entrée glossaire (propriété Définition ou corps de page).\n")
        return 1, []

    try:
        dst = build_dictionnaire_site(
            entries,
            templates=templates,
            site_root=site_root,
            log=req.log,
        )
    except (FileNotFoundError, ValueError) as e:
        req.log(f"Erreur dictionnaire : {e}\n")
        return 1, []

    return 0, [dst / "index.html"]


def export_arrets_html(req, units, templates: Path) -> tuple[int, list[Path]]:
    site_root = resolve_site_root(Path(req.out))
    arrets_pages = [u.page for u in units if u.kind == "arrets" and u.page]
    if not arrets_pages:
        req.log("Aucune fiche jurisprudence (propriétés Nom / Objet / fiche).\n")
        return 1, []

    try:
        dst = build_arrets_site(
            arrets_pages,
            templates=templates,
            site_root=site_root,
            log=req.log,
        )
    except (FileNotFoundError, ValueError) as e:
        req.log(f"Erreur arrêts : {e}\n")
        return 1, []

    return 0, [dst / "index.html"]


def build_manuel_title_map_safe(manuel_roots: list[Path]) -> dict:
    from .dictionnaire_render import build_manuel_title_map

    return build_manuel_title_map(manuel_roots)


def export_flat_html(req, units, fetcher) -> tuple[int, list[Path]]:
    converter = PageConverter(fetcher)
    out_dir = Path(req.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    produced: list[Path] = []
    errors = 0

    for i, unit in enumerate(units):
        if req.cancel():
            req.log("Annulé.\n")
            return (1 if errors else 130), produced
        if unit.page is None:
            continue
        title = page_title(unit.page) or unit.label
        req.log(f"  [{i + 1}/{len(units)}] {unit.kind} — {title}\n")
        try:
            body = converter.render_html(unit.page, unit.blocks or [], include_title=False)
            html_doc = _flat_page_html(title, body)
            sub = out_dir / unit.kind if unit.kind != "autre" else out_dir / "autre"
            sub.mkdir(parents=True, exist_ok=True)
            path = stamped_path(sub, _slugify(title), ext=".html")
            path.write_text(html_doc, encoding="utf-8")
            produced.append(path)
        except Exception as e:
            errors += 1
            req.log(f"  x {title} : {e}\n")

    if not produced:
        req.log("Aucun fichier HTML produit.\n")
        return 1, []
    req.log(f"OK {len(produced)} fichier(s) HTML\n")
    return (1 if errors else 0), produced


def run_html_pipeline(req) -> tuple[int, list[Path]]:
    load_env()
    if req.combine:
        req.log("Erreur : HTML combiné non pris en charge.\n")
        return 1, []

    units, code = _collect_units(req)
    if code != 0:
        return code, []

    from extract.pull._common import make_fetcher

    try:
        fetcher = make_fetcher()
    except Exception:
        fetcher = None

    templates = Path(req.site_templates) if req.site_templates else None
    has_autres = any(a.strip() for a in req.autres)
    has_manuel = "manuel" in req.registres and not has_autres
    has_index = "index" in req.registres and not has_autres
    has_arrets = "arrets" in req.registres and not has_autres

    if templates is None and (has_manuel or has_index or has_arrets):
        templates = _default_site_templates()

    produced: list[Path] = []
    exit_code = 0

    if has_manuel:
        if templates is None or not templates.is_dir():
            req.log("Erreur : gabarits site introuvables (manuel-page.html).\n")
            return 1, []
        err = _check_manuel_templates(templates)
        if err:
            req.log(f"Erreur : {err}\n")
            return 1, []
        manuel_units = [u for u in units if u.kind == "manuel"]
        req.log(f"{len(manuel_units)} page(s) → manuel HTML\n\n")
        code, paths = export_manuel_html(req, manuel_units, fetcher, templates)
        exit_code = max(exit_code, code)
        produced.extend(paths)

    if has_index:
        if templates is None or not templates.is_dir():
            req.log("Erreur : gabarits site introuvables (dictionnaire.html).\n")
            return 1, produced
        if not (templates / "dictionnaire.html").is_file():
            req.log(f"Erreur : gabarit manquant : {templates / 'dictionnaire.html'}\n")
            return 1, produced
        index_units = [u for u in units if u.kind == "index"]
        req.log(f"{len(index_units)} entrée(s) → dictionnaire HTML\n\n")
        code, paths = export_dictionnaire_html(req, index_units, fetcher, templates)
        exit_code = max(exit_code, code)
        produced.extend(paths)

    if has_arrets:
        if templates is None or not templates.is_dir():
            req.log("Erreur : gabarits site introuvables (arrets-*.html).\n")
            return 1, produced
        for name in ("arrets-index.html", "arrets-fiche.html"):
            if not (templates / name).is_file():
                req.log(f"Erreur : gabarit manquant : {templates / name}\n")
                return 1, produced
        arrets_units = [u for u in units if u.kind == "arrets"]
        req.log(f"{len(arrets_units)} fiche(s) → arrêts HTML\n\n")
        code, paths = export_arrets_html(req, arrets_units, templates)
        exit_code = max(exit_code, code)
        produced.extend(paths)

    site_kinds = {"manuel", "index", "arrets"}
    flat_units = [
        u
        for u in units
        if u.kind not in site_kinds or has_autres
    ]
    if has_autres:
        flat_units = units
    elif has_manuel or has_index or has_arrets:
        flat_units = [u for u in units if u.kind not in site_kinds]

    if flat_units:
        req.log(f"{len(flat_units)} fiche(s) → HTML plat\n\n")
        code, paths = export_flat_html(req, flat_units, fetcher)
        exit_code = max(exit_code, code)
        produced.extend(paths)

    if not produced:
        req.log("Aucun export HTML produit.\n")
        return 1, []

    return exit_code, produced
