"""Fusionner un export HTML (Drive export_site) vers site/dist/site."""

from __future__ import annotations

import importlib.util
import json
import shutil
from collections.abc import Callable
from pathlib import Path

from packages.ep_core.paths import REPO_ROOT, resolve_path

from extract.html.crumb_legacy import fix_tree

# Registre GUI → sous-dossier export_site / dist
SITE_SECTIONS: dict[str, str] = {
    "manuel": "manuel",
    "index": "dictionnaire",
    "arrets": "arrets",
}


def _patch_tree(root: Path) -> int:
    path = REPO_ROOT / "scripts" / "patch_site_scripts.py"
    spec = importlib.util.spec_from_file_location("patch_site_scripts", path)
    if spec is None or spec.loader is None:
        return 0
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return int(mod.patch_tree(root))


def _rebuild_search_index(dist_site: Path, log: Callable[[str], None]) -> None:
    idx_path = REPO_ROOT / "site" / "build_search_index.py"
    spec = importlib.util.spec_from_file_location("build_search_index", idx_path)
    if spec is None or spec.loader is None:
        log("Index recherche : module introuvable\n")
        return
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    data = mod.build_index(dist_site)
    out = dist_site / "search-index.json"
    out.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    c = data["counts"]
    log(
        f"Index recherche : {len(data['docs'])} docs "
        f"(cours {c['manuel']}, dico {c['dictionnaire']}, arrets {c['arrets']})\n"
    )
    src_js = REPO_ROOT / "site" / "templates" / "site-search.js"
    if src_js.is_file():
        shutil.copy2(src_js, dist_site / "site-search.js")


def default_export_site() -> Path:
    try:
        return resolve_path("export_site")
    except (KeyError, OSError):
        return REPO_ROOT / "output" / "site"


def default_dist_site() -> Path:
    return REPO_ROOT / "site" / "dist" / "site"


def merge_section(
    section: str,
    *,
    export_site: Path | None = None,
    dist_site: Path | None = None,
    log: Callable[[str], None] = print,
) -> int:
    """Copie une section (manuel|dictionnaire|arrets) vers dist. 0 = OK."""
    export_site = Path(export_site or default_export_site())
    dist_site = Path(dist_site or default_dist_site())
    src = export_site / section
    dst = dist_site / section

    if not src.is_dir():
        log(f"  (absent) {src}\n")
        return 0

    if not dist_site.is_dir():
        log(
            f"Erreur : build site manquant ({dist_site}). "
            "Lancez d'abord .\\scripts\\build_site.ps1\n"
        )
        return 1

    n_fix = fix_tree(src)
    log(f"  fils d'Ariane : {n_fix} fichier(s) corrige(s) dans {section}/\n")

    if section in ("manuel", "dictionnaire"):
        n_patch = _patch_tree(src)
        log(f"  TTS : {n_patch} page(s) patchee(s) dans {section}/\n")

    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    log(f"  OK {src} -> {dst}\n")
    return 0


def merge_registres(
    registres: list[str],
    *,
    export_site: Path | None = None,
    dist_site: Path | None = None,
    log: Callable[[str], None] = print,
) -> int:
    """Fusionne les sections site correspondant aux registres GUI. 0 = OK."""
    sections: list[str] = []
    for reg in registres:
        folder = SITE_SECTIONS.get(reg)
        if folder and folder not in sections:
            sections.append(folder)

    if not sections:
        log(
            "Aucune section site a fusionner "
            "(choisir Cours, Glossaire ou Jurisprudence).\n"
        )
        return 0

    dist = Path(dist_site or default_dist_site())
    log(f"Fusion dist/site : {', '.join(sections)}\n")
    code = 0
    for section in sections:
        code = max(
            code,
            merge_section(
                section,
                export_site=export_site,
                dist_site=dist,
                log=log,
            ),
        )
    if code == 0 and dist.is_dir():
        try:
            _rebuild_search_index(dist, log)
        except Exception as e:
            log(f"Index recherche : echec ({e})\n")
    return code
