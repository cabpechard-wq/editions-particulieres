"""Crée un hub SITE_ROOT Notion si la page Grands arrêts n'est pas partagée.

Essaie d'abord NOTION_COMMERCE_PARENT / page Grands arrêts.
Sinon crée sous une page déjà accessible à l'intégration, ou affiche
les instructions de partage.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from _repo import REPO_ROOT as ROOT
sys.path.insert(0, str(Path(__file__).resolve().parent))

from setup_notion import DEFAULT_PARENT, main as setup_main, make_client, to_uuid  # noqa: E402
from notion_client.errors import APIResponseError  # noqa: E402


def find_writable_parent(client) -> str | None:
    """Retourne un page_id déjà accessible (hors bases) pour y accrocher le hub."""
    resp = client.search(
        query="Flipcards SITE_ROOT hub",
        page_size=5,
        filter={"property": "object", "value": "page"},
    )
    for r in resp.get("results", []):
        if r.get("object") == "page":
            return r["id"]

    # Crée une page racine via une page accessible quelconque
    resp = client.search(page_size=20, filter={"property": "object", "value": "page"})
    for r in resp.get("results", []):
        parent = r.get("parent") or {}
        # Préfère une page hors database (workspace/page)
        if parent.get("type") in {"workspace", "page_id"}:
            return r["id"]
    # Dernier recours : n'importe quelle page accessible (enfant database ok pour API)
    for r in resp.get("results", []):
        if r.get("object") == "page":
            return r["id"]
    return None


def create_hub_under(client, parent_id: str) -> str:
    page = client.pages.create(
        parent={"type": "page_id", "page_id": parent_id},
        properties={
            "title": {
                "title": [
                    {
                        "type": "text",
                        "text": {"content": "Flipcards — Hub commercialisation"},
                    }
                ]
            }
        },
        children=[
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": (
                                    "Hub auto-créé car la page Grands arrêts n'était pas partagée "
                                    "avec l'intégration. Tu peux déplacer ces pages sous "
                                    "« Grands arrêts… » ensuite (Notion → Move to)."
                                )
                            },
                        }
                    ],
                    "icon": {"type": "emoji", "emoji": "📦"},
                },
            }
        ],
    )
    return page["id"]


def main() -> int:
    client = make_client()
    target = to_uuid(os.getenv("NOTION_COMMERCE_PARENT") or DEFAULT_PARENT)
    try:
        client.pages.retrieve(page_id=target)
        os.environ["NOTION_COMMERCE_PARENT"] = target
        return setup_main()
    except APIResponseError:
        print(
            "Page Grands arrêts non partagée avec l'intégration « Projet GdN ».\n"
            "Création d'un hub alternatif accessible…"
        )

    anchor = find_writable_parent(client)
    if not anchor:
        print(
            "Aucune page accessible. Dans Notion : Share sur la page Grands arrêts → "
            "invite l'intégration « Projet GdN » → puis relance "
            "python site/setup_notion.py",
            file=sys.stderr,
        )
        return 1

    try:
        hub_id = create_hub_under(client, anchor)
    except APIResponseError as e:
        # Certaines pages DB n'acceptent pas d'enfants libres
        print(f"Échec création sous {anchor}: {e}", file=sys.stderr)
        # Essayer workspace — souvent refusé
        try:
            page = client.pages.create(
                parent={"type": "workspace", "workspace": True},
                properties={
                    "title": {
                        "title": [
                            {
                                "type": "text",
                                "text": {"content": "Flipcards — Hub commercialisation"},
                            }
                        ]
                    }
                },
            )
            hub_id = page["id"]
        except APIResponseError as e2:
            print(
                f"Impossible de créer un hub ({e2}).\n"
                "Action manuelle requise : Share la page "
                "https://www.notion.so/3b2a29ad9f788035a69afa4a5ee4e189 "
                "avec l'intégration « Projet GdN », puis : "
                "python site/setup_notion.py",
                file=sys.stderr,
            )
            return 1

    os.environ["NOTION_COMMERCE_PARENT"] = hub_id
    print(f"Hub parent : https://www.notion.so/{hub_id.replace('-', '')}")
    return setup_main()


if __name__ == "__main__":
    raise SystemExit(main())
