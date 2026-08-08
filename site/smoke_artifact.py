"""Smoke tests sur l'artefact local site/dist/site (pré-déploiement CI).

Usage :
  python site/smoke_artifact.py
  python site/smoke_artifact.py --root site/dist/site
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parent
DEFAULT_ROOT = SITE_ROOT / "dist" / "site"

OVH_POISON = re.compile(r"Site en construction|OVHcloud|/__ovh/", re.I)


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def ok(msg: str) -> None:
    print(f"OK: {msg}")


def require_file(path: Path, *, min_size: int = 200) -> None:
    if not path.is_file():
        fail(f"fichier manquant : {path}")
    if path.stat().st_size < min_size:
        fail(f"fichier trop petit ({path.stat().st_size} o) : {path}")


def check_html_not_ovh(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if OVH_POISON.search(text):
        fail(f"page OVH « site en construction » : {path}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = p.parse_args(argv)
    root = args.root.resolve()

    if not root.is_dir():
        fail(f"racine absente : {root} (lance build_site / build_assets)")

    # Pages marketing / commerce
    for rel in (
        "index.html",
        "checkout/index.html",
        "merci/index.html",
        "membre/index.html",
        "demo/index.html",
        "flipcards/index.html",
        "flipcards/app.html",
        "bibliotheque/index.html",
        "ressources/index.html",
        "exercices/index.html",
        "cgv/index.html",
        "mentions-legales/index.html",
        "site.css",
        "site-nav.js",
        "site-search.js",
        "site-tts.js",
        "site-theme.js",
        "auth.js",
        "search-index.json",
    ):
        require_file(root / rel)

    ok("pages + assets de base présents")

    # Contenu pédagogique
    for section in ("manuel", "dictionnaire", "arrets"):
        index = root / section / "index.html"
        require_file(index, min_size=400)
        check_html_not_ovh(index)

    manuel_pages = list((root / "manuel").rglob("index.html"))
    if len(manuel_pages) < 10:
        fail(f"manuel trop mince ({len(manuel_pages)} pages HTML, attendu >= 10)")
    ok(f"manuel : {len(manuel_pages)} pages")

    arrets_fiches = [
        p
        for p in (root / "arrets").rglob("index.html")
        if p.parent.resolve() != (root / "arrets").resolve()
    ]
    if len(arrets_fiches) < 50:
        fail(f"arrêts trop minces ({len(arrets_fiches)} fiches, attendu >= 50)")
    ok(f"arrêts : {len(arrets_fiches)} fiches")

    # Index recherche
    idx = json.loads((root / "search-index.json").read_text(encoding="utf-8"))
    docs = idx.get("docs") or []
    counts = idx.get("counts") or {}
    if len(docs) < 100:
        fail(f"search-index trop petit ({len(docs)} docs)")
    if int(counts.get("manuel") or 0) < 5:
        fail("search-index : peu de cours")
    if int(counts.get("dictionnaire") or 0) < 50:
        fail("search-index : peu d'entrées dictionnaire")
    ok(
        f"search-index : {len(docs)} docs "
        f"(cours {counts.get('manuel')}, dico {counts.get('dictionnaire')}, "
        f"arrets {counts.get('arrets')})"
    )

    # Auth + Stripe dans l'artefact
    auth_js = (root / "auth.js").read_text(encoding="utf-8", errors="ignore")
    if "workers.dev" not in auth_js and "http" not in auth_js:
        fail("auth.js sans URL API")
    if "__AUTH_API__" in auth_js:
        print("WARN: auth.js contient encore __AUTH_API__ (repli Worker)")
    ok("auth.js OK")

    checkout = (root / "checkout" / "index.html").read_text(
        encoding="utf-8", errors="ignore"
    )
    if "buy.stripe.com" not in checkout:
        fail("checkout sans Payment Links Stripe")
    ok("checkout Stripe OK")

    # Démo vs pack membres
    demo = root / "demo" / "index.html"
    app = root / "flipcards" / "app.html"
    demo_html = demo.read_text(encoding="utf-8", errors="ignore")
    slides = len(re.findall(r'class="card-slide"', demo_html))
    if slides == 0:
        slides = len(re.findall(r"data-index=", demo_html))
    if slides and slides > 12:
        fail(f"démo trop large ({slides} slides)")
    if demo.stat().st_size >= app.stat().st_size * 0.85:
        fail("démo presque aussi grosse que le pack membres")
    ok(f"démo limitée ({slides or '?'} slides / {demo.stat().st_size} o)")

    if "flipcards_ok" not in app.read_text(encoding="utf-8", errors="ignore"):
        fail("garde session absente de flipcards/app.html")
    ok("garde flipcards présente")

    print("SMOKE ARTIFACT OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
