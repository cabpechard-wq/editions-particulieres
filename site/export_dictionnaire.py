"""Convertit glossaire.html (legacy) ou Notion → site /dictionnaire/.

Usage :
  python site/export_dictionnaire.py
  python site/export_dictionnaire.py --src chemin/glossaire.html
  python export_dictionnaire.py --out site/dist/site
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from extract.html.dictionnaire_render import build_manuel_title_map, parse_entries_from_html
from extract.html.dictionnaire_site import build_dictionnaire_site, manuel_roots_for

SITE_ROOT = Path(__file__).resolve().parent
TEMPLATES = SITE_ROOT / "templates"
SITE = SITE_ROOT / "dist" / "site"
HOST = SITE_ROOT / "host-repo"


def _default_glossaire_src() -> Path | None:
    """Cherche un glossaire.html local (Drive / output), sans chemin machine en dur."""
    candidates: list[Path] = []
    try:
        from packages.ep_core.paths import output_root, resolve_path

        candidates.append(resolve_path("export_index") / "glossaire.html")
        candidates.append(output_root() / "export" / "index" / "glossaire.html")
    except Exception:
        pass
    candidates.append(SITE_ROOT.parent / "output" / "glossaire.html")
    for path in candidates:
        if path.exists():
            return path
    return None


def build_from_html(src: Path, out_roots: list[Path], *, templates: Path = TEMPLATES) -> int:
    if not src.exists():
        raise SystemExit(f"Source introuvable : {src}")

    title_map: dict[str, str] = {}
    for root in out_roots:
        title_map.update(build_manuel_title_map(manuel_roots_for(root)))
    if not title_map:
        print("Attention : aucune page Cours trouvée pour résoudre les liens.")

    raw = src.read_text(encoding="utf-8")
    entries = parse_entries_from_html(raw, title_map)
    if not entries:
        raise SystemExit("Aucune entrée parsée.")

    linked = sum(1 for e in entries if e["extras_html"])
    print(f"Entrées avec lien(s) Cours : {linked}/{len(entries)} (map titres={len(title_map)})")

    for root in out_roots:
        if not root.exists():
            continue
        build_dictionnaire_site(entries, templates=templates, site_root=root)
        print(f"Écrit : {root / 'dictionnaire' / 'index.html'} ({len(entries)} entrées)")
    return len(entries)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, default=None, help="glossaire.html (legacy)")
    ap.add_argument("--out", type=Path, default=None, help="Racine site (défaut : dist + host-repo)")
    args = ap.parse_args()

    for root in (SITE, HOST):
        if root.exists():
            for asset in ("site.css", "site-nav.js", "site-tts.js", "site-theme.js"):
                src_a = TEMPLATES / asset
                if src_a.exists():
                    shutil.copy2(src_a, root / asset)
            themes_src = TEMPLATES / "themes"
            if themes_src.is_dir():
                themes_dst = root / "themes"
                if themes_dst.exists():
                    shutil.rmtree(themes_dst)
                shutil.copytree(themes_src, themes_dst)

    if args.src is not None:
        out_roots = [args.out] if args.out else [SITE, HOST]
        n = build_from_html(args.src, [r for r in out_roots if r])
        print(f"Dictionnaire juridique : {n} entrées.")
        return 0

    if args.out:
        from extract.html.__main__ import run_export
        from packages.ep_core.paths import REPO_ROOT

        templates = TEMPLATES
        try:
            from packages.ep_core.paths import resolve_path

            templates = resolve_path("templates_site")
        except (KeyError, OSError):
            pass
        return run_export(registre="index", out=args.out, templates=templates)

    src = _default_glossaire_src()
    if src is None:
        raise SystemExit(
            "Aucun glossaire.html trouvé. Passe --src chemin/glossaire.html "
            "ou exporte via Notion : python export_dictionnaire.py --out site/dist/site"
        )
    n = build_from_html(src, [r for r in (SITE, HOST) if r.exists()])
    print(f"Dictionnaire juridique : {n} entrées (depuis {src}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
