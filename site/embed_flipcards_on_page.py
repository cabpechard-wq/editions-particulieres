"""Intègre l’HTML flipcards (embed) sur la page Notion Grands arrêts.

Prérequis : partager la page avec l’intégration « Projet GdN »
  Share → Invite → Projet GdN → Can edit

Usage :
  .\\.venv\\Scripts\\python.exe site\\embed_flipcards_on_page.py
  .\\.venv\\Scripts\\python.exe site\\embed_flipcards_on_page.py --full
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from notion_client.errors import APIResponseError

from _repo import REPO_ROOT as ROOT
SITE_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(SITE_ROOT))

from setup_notion import (  # noqa: E402
    bookmark,
    bullet,
    callout,
    divider,
    heading,
    make_client,
    paragraph,
    to_uuid,
)

DEFAULT_PAGE = "3b2a29ad9f788035a69afa4a5ee4e189"


def embed(url: str) -> dict:
    return {"object": "block", "type": "embed", "embed": {"url": url}}


def main() -> int:
    load_dotenv(ROOT / ".env")
    cfg = json.loads((SITE_ROOT / "config.json").read_text(encoding="utf-8-sig"))
    p = argparse.ArgumentParser()
    p.add_argument(
        "--page",
        default=os_env_page(),
        help="Page Notion cible (id ou URL)",
    )
    p.add_argument(
        "--full",
        action="store_true",
        help="Embed la version complète /flipcards/ (sinon démo publique)",
    )
    args = p.parse_args()

    demo = cfg.get("demo_url") or "https://cabpechard-wq.github.io/editions-particulieres/demo/"
    full = cfg.get("flipcards_url") or "https://cabpechard-wq.github.io/editions-particulieres/flipcards/"
    checkout = cfg.get("checkout_url") or ""
    membre = (cfg.get("sotion") or {}).get("site_url") or ""
    site = (cfg.get("notion") or {}).get("public_site_url") or "https://droit-public.notion.site"

    embed_url = full if args.full else demo
    page_id = to_uuid(args.page)
    client = make_client()

    try:
        client.pages.retrieve(page_id=page_id)
    except APIResponseError as e:
        print(
            "Page inaccessible pour l’intégration « Projet GdN ».\n"
            "Dans Notion, ouvre la page puis Share → Invite → « Projet GdN » "
            "(Can edit), puis relance ce script.\n"
            f"Détail : {e}",
            file=sys.stderr,
        )
        return 1

    children = [
        divider(),
        heading("Flipcards", 2),
        callout(
            "Flipcards interactives des grands arrêts du droit public et administratif "
            "(recto / verso). Utilise le mode plein écran si besoin.",
            "🃏",
        ),
        embed(embed_url),
        paragraph(
            "Si l’aperçu ne s’affiche pas, ouvre les flipcards dans un nouvel onglet :"
        ),
        bookmark(embed_url),
    ]
    if not args.full:
        children.extend(
            [
                heading("Version complète", 3),
                bullet(f"Accès abonnés : {full}"),
            ]
        )
        if membre:
            children.append(bullet(f"Espace membre : {membre}"))
        if checkout:
            children.append(bullet(f"S’abonner : {checkout}"))
    children.append(paragraph(f"Site public : {site}"))

    client.blocks.children.append(block_id=page_id, children=children)
    print(f"Embed ajouté sur {page_id}")
    print(f"  url={embed_url}")
    return 0


def os_env_page() -> str:
    import os

    return os.getenv("NOTION_EMBED_PAGE") or DEFAULT_PAGE


if __name__ == "__main__":
    raise SystemExit(main())
