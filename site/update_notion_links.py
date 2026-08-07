"""Met à jour les liens checkout / démo / flipcards dans les pages Notion SITE_ROOT."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from _repo import REPO_ROOT as ROOT
SITE_ROOT = Path(__file__).resolve().parent
STATE_PATH = SITE_ROOT / "notion_state.json"
CFG_PATH = SITE_ROOT / "config.json"

sys.path.insert(0, str(SITE_ROOT))
from setup_notion import (  # noqa: E402
    make_client,
    membre_children,
    vitrine_children,
)


def clear_children(client, block_id: str) -> None:
    cursor = None
    while True:
        kwargs = {"block_id": block_id, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        resp = client.blocks.children.list(**kwargs)
        for b in resp.get("results", []):
            try:
                client.blocks.delete(block_id=b["id"])
            except Exception:
                pass
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")


def replace_children(client, page_id: str, children: list[dict]) -> None:
    clear_children(client, page_id)
    rest = children
    while rest:
        chunk, rest = rest[:90], rest[90:]
        client.blocks.children.append(block_id=page_id, children=chunk)


def rename_page(client, page_id: str, title: str) -> None:
    client.pages.update(
        page_id=page_id,
        properties={
            "title": {"title": [{"type": "text", "text": {"content": title}}]},
        },
    )


def main() -> int:
    load_dotenv(ROOT / ".env")
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    cfg = json.loads(CFG_PATH.read_text(encoding="utf-8-sig"))
    client = make_client()

    checkout = (
        cfg.get("checkout_url")
        or cfg.get("lemonsqueezy", {}).get("monthly_checkout_url")
        or (cfg.get("stripe") or {}).get("monthly_payment_link")
        or "https://cabpechard-wq.github.io/editions-particulieres/checkout/"
    )
    demo = cfg.get("demo_url") or "https://cabpechard-wq.github.io/editions-particulieres/demo/"
    flipcards = cfg.get("flipcards_url") or "https://cabpechard-wq.github.io/editions-particulieres/flipcards/"
    password = cfg.get("members_password")
    membre_hub = (cfg.get("sotion") or {}).get("site_url")
    vitrine_public = (
        (cfg.get("notion") or {}).get("vitrine_public_url")
        or (cfg.get("notion") or {}).get("public_site_url")
        or "https://droit-public.notion.site"
    )

    vitrine_id = state["vitrine_page_id"]
    membre_id = state["membre_page_id"]

    rename_page(client, vitrine_id, "Accueil — Flipcards (démo & abonnement)")
    rename_page(client, membre_id, "Espace membre — Flipcards")

    replace_children(
        client,
        vitrine_id,
        vitrine_children(checkout_url=checkout, demo_url=demo),
    )
    replace_children(
        client,
        membre_id,
        membre_children(
            flipcards_url=flipcards,
            password=password,
            membre_hub_url=membre_hub,
            vitrine_url=vitrine_public,
            checkout_url=checkout,
        ),
    )

    # public_url de la vitrine (pour homepage Notion Sites)
    vit = client.pages.retrieve(page_id=vitrine_id)
    print("Pages Notion mises a jour (vitrine = landing demo+abo).")
    print(f"  checkout={checkout}")
    print(f"  demo={demo}")
    print(f"  flipcards={flipcards}")
    print(f"  vitrine_editor={(cfg.get('notion') or {}).get('vitrine_url')}")
    print(f"  vitrine_published={vit.get('public_url')}")
    print(
        "IMPORTANT: dans Notion Sites (droit-public.notion.site), "
        "definis la page d'accueil = « Accueil — Flipcards (démo & abonnement) », "
        "pas « Espace membre »."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
