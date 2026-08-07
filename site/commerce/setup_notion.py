"""Crée / met à jour la structure Notion vitrine + espace membre + base Abonnés.

Usage (depuis la racine du projet) :
  .\\.venv\\Scripts\\python.exe commerce\\setup_notion.py

Parent par défaut : page Grands arrêts
  https://app.notion.com/p/...-3b2a29ad9f788035a69afa4a5ee4e189
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from notion_client import Client
from notion_client.errors import APIResponseError

from _repo import COMMERCE, REPO_ROOT as ROOT
STATE_PATH = Path(__file__).resolve().parent / "notion_state.json"
DEFAULT_PARENT = "3b2a29ad9f788035a69afa4a5ee4e189"

# Placeholders mis à jour par host_html / Lemon Squeezy
PLACEHOLDER_CHECKOUT = "https://flipcards.lemonsqueezy.com/checkout/buy/REPLACE_ME"
PLACEHOLDER_FLIPCARDS = "https://members.example.com/flipcards/"  # remplacé après hébergement
PLACEHOLDER_DEMO = "https://members.example.com/demo/"


def to_uuid(raw: str) -> str:
    s = "".join(c for c in (raw or "") if c.isalnum()).lower()
    if len(s) != 32:
        raise ValueError(f"ID Notion invalide : {raw!r}")
    return f"{s[:8]}-{s[8:12]}-{s[12:16]}-{s[16:20]}-{s[20:]}"


def rich(text: str) -> list[dict]:
    return [{"type": "text", "text": {"content": text[:2000]}}]


def paragraph(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": rich(text)},
    }


def heading(text: str, level: int = 2) -> dict:
    key = f"heading_{level}"
    return {"object": "block", "type": key, key: {"rich_text": rich(text)}}


def bullet(text: str) -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": rich(text)},
    }


def callout(text: str, emoji: str = "💡") -> dict:
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": rich(text),
            "icon": {"type": "emoji", "emoji": emoji},
        },
    }


def divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def bookmark(url: str) -> dict:
    return {"object": "block", "type": "bookmark", "bookmark": {"url": url}}


def embed(url: str) -> dict:
    return {"object": "block", "type": "embed", "embed": {"url": url}}


def vitrine_children(*, checkout_url: str, demo_url: str) -> list[dict]:
    """Landing publique : abo + démo d'abord, membre ensuite."""
    return [
        callout(
            "Flipcards des grands arrêts du droit public et administratif — "
            "recto / verso pour réviser efficacement.",
            "🃏",
        ),
        heading("S’abonner", 2),
        bullet("Mensuel : 6,90 € / mois"),
        bullet("Annuel : 59 € / an (environ 2 mois offerts)"),
        paragraph(
            "Important : le paiement Stripe doit s’ouvrir dans un nouvel onglet "
            "(pas en embed Notion) — sinon le 3D Secure reste bloqué."
        ),
        bookmark(checkout_url),
        callout(
            "Après paiement, tu reçois l’accès à l’espace membre et aux flipcards complètes.",
            "✅",
        ),
        heading("Essayer la démo (gratuit)", 2),
        paragraph("8 cartes en accès libre — aucun compte requis :"),
        embed(demo_url),
        bookmark(demo_url),
        heading("Ce que tu obtiens avec l’abonnement", 2),
        bullet("Flipcards interactives sur les grands arrêts du droit public et administratif"),
        bullet("Recto = nom de l’arrêt · Verso = principe à retenir"),
        bullet("Filtres par thème / notions"),
        bullet("Mises à jour tant que l’abonnement est actif"),
        divider(),
        heading("Déjà abonné ?", 3),
        paragraph("Connecte-toi à l’espace membre (e-mail d’abonnement) — pas ici sur la vitrine."),
        heading("Prochainement", 3),
        bullet("Quiz et jeux de mémorisation"),
        bullet("Fiches d’actualité"),
        bullet("Manuel et méthodologie (éventuellement)"),
    ]


def membre_children(*, flipcards_url: str, password: str | None, membre_hub_url: str | None = None, vitrine_url: str | None = None, checkout_url: str | None = None) -> list[dict]:
    blocks = [
        callout(
            "Espace réservé aux abonnés. Pas encore inscrit ? Retourne à la vitrine pour la démo et l’abonnement.",
            "🔒",
        ),
    ]
    if vitrine_url or checkout_url:
        blocks.append(heading("Pas encore abonné ?", 3))
        if checkout_url:
            blocks.append(bookmark(checkout_url))
        if vitrine_url:
            blocks.append(bookmark(vitrine_url))
    if membre_hub_url:
        blocks.extend(
            [
                heading("Connexion membre", 2),
                paragraph("Entre l’e-mail utilisé à l’abonnement :"),
                bookmark(membre_hub_url),
            ]
        )
    blocks.extend(
        [
            heading("Ouvrir les flipcards", 2),
            paragraph("Lien d’accès (ne pas partager hors abonnement) :"),
            bookmark(flipcards_url),
        ]
    )
    if password:
        blocks.extend(
            [
                paragraph(f"Mot de passe d’accès page flipcards : {password}"),
                callout(
                    "Ce mot de passe change si une fuite est détectée. "
                    "Il est réservé aux membres.",
                    "🔑",
                ),
            ]
        )
    blocks.extend(
        [
            heading("FAQ", 2),
            bullet("Comment résilier ? Depuis l’e-mail de reçu Lemon Squeezy → Manage subscription."),
            bullet("Accès coupé après résiliation : normal, dès la fin de la période payée."),
            bullet("Bug / carte manquante : note le nom de l’arrêt et contacte le support."),
            heading("Changelog", 2),
            bullet("v1 — Flipcards GADA 2026 (HTML)"),
            heading("Bientôt dans cet espace", 3),
            bullet("Quiz · jeux · actualité · (plus tard) manuel / méthodo"),
        ]
    )
    return blocks


def make_client() -> Client:
    load_dotenv(ROOT / ".env")
    token = (os.getenv("NOTION_TOKEN") or "").strip()
    if not token:
        raise SystemExit("NOTION_TOKEN manquant dans .env")
    verify = (os.getenv("NOTION_SSL_VERIFY") or "0").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }
    if verify:
        return Client(auth=token)
    import httpx

    return Client(auth=token, client=httpx.Client(verify=False, timeout=60.0))


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def create_page(client: Client, *, parent_id: str, title: str, children: list[dict]) -> str:
    # Notion API : max 100 children per request
    first, rest = children[:90], children[90:]
    page = client.pages.create(
        parent={"type": "page_id", "page_id": parent_id},
        properties={
            "title": {"title": [{"type": "text", "text": {"content": title}}]},
        },
        children=first,
    )
    page_id = page["id"]
    while rest:
        chunk, rest = rest[:90], rest[90:]
        client.blocks.children.append(block_id=page_id, children=chunk)
    return page_id


def create_subscribers_db(client: Client, *, parent_id: str) -> tuple[str, str]:
    """Retourne (database_id, data_source_id)."""
    db = client.databases.create(
        parent={"type": "page_id", "page_id": parent_id},
        title=[{"type": "text", "text": {"content": "Abonnés"}}],
        initial_data_source={
            "properties": {
                "Email": {"title": {}},
                "Statut": {
                    "select": {
                        "options": [
                            {"name": "actif", "color": "green"},
                            {"name": "essai", "color": "yellow"},
                            {"name": "résilié", "color": "red"},
                            {"name": "impayé", "color": "orange"},
                        ]
                    }
                },
                "Offre": {
                    "select": {
                        "options": [
                            {"name": "mensuel", "color": "blue"},
                            {"name": "annuel", "color": "purple"},
                        ]
                    }
                },
                "Depuis": {"date": {}},
                "Notes": {"rich_text": {}},
            }
        },
    )
    db_id = db["id"]
    sources = db.get("data_sources") or []
    ds_id = sources[0]["id"] if sources else db_id
    return db_id, ds_id


def append_nav_on_parent(
    client: Client,
    *,
    parent_id: str,
    vitrine_url: str,
    membre_url: str,
) -> None:
    try:
        client.blocks.children.append(
            block_id=parent_id,
            children=[
                divider(),
                heading("Commercialisation (étudiants)", 2),
                paragraph("Parcours abonnement — pages générées automatiquement :"),
                bullet(f"Vitrine / offre : {vitrine_url}"),
                bullet(f"Espace membre (à gate via Sotion) : {membre_url}"),
            ],
        )
    except APIResponseError as e:
        print(f"(nav parent non ajoutée : {e})", file=sys.stderr)


def page_url(page_id: str) -> str:
    compact = page_id.replace("-", "")
    return f"https://www.notion.so/{compact}"


def main() -> int:
    parent_raw = os.getenv("NOTION_COMMERCE_PARENT") or DEFAULT_PARENT
    parent_id = to_uuid(parent_raw)
    client = make_client()
    state = load_state()

    commerce_cfg = COMMERCE / "config.json"
    cfg = {}
    if commerce_cfg.exists():
        cfg = json.loads(commerce_cfg.read_text(encoding="utf-8-sig"))

    checkout = cfg.get("checkout_url") or PLACEHOLDER_CHECKOUT
    demo = cfg.get("demo_url") or PLACEHOLDER_DEMO
    flipcards = cfg.get("flipcards_url") or PLACEHOLDER_FLIPCARDS
    password = cfg.get("members_password")

    # Vérifie accès parent
    try:
        client.pages.retrieve(page_id=parent_id)
    except APIResponseError as e:
        print(
            f"Impossible d’accéder à la page parent {parent_id}.\n"
            f"Partage cette page avec l’intégration Notion (connexion {e}).",
            file=sys.stderr,
        )
        return 1

    if state.get("vitrine_page_id"):
        print(f"Vitrine déjà créée : {page_url(state['vitrine_page_id'])}")
        vitrine_id = state["vitrine_page_id"]
    else:
        vitrine_id = create_page(
            client,
            parent_id=parent_id,
            title="Accueil — Flipcards (démo & abonnement)",
            children=vitrine_children(checkout_url=checkout, demo_url=demo),
        )
        state["vitrine_page_id"] = vitrine_id
        print(f"Vitrine créée : {page_url(vitrine_id)}")

    if state.get("membre_page_id"):
        print(f"Espace membre déjà créé : {page_url(state['membre_page_id'])}")
        membre_id = state["membre_page_id"]
    else:
        membre_id = create_page(
            client,
            parent_id=parent_id,
            title="Espace membre — Flipcards",
            children=membre_children(flipcards_url=flipcards, password=password),
        )
        state["membre_page_id"] = membre_id
        print(f"Espace membre créé : {page_url(membre_id)}")

    if state.get("abonnes_db_id"):
        print(f"Base Abonnés déjà créée : {state['abonnes_db_id']}")
    else:
        db_id, ds_id = create_subscribers_db(client, parent_id=parent_id)
        state["abonnes_db_id"] = db_id
        state["abonnes_data_source_id"] = ds_id
        print(f"Base Abonnés créée : {db_id} (data_source={ds_id})")

    if not state.get("nav_appended"):
        append_nav_on_parent(
            client,
            parent_id=parent_id,
            vitrine_url=page_url(vitrine_id),
            membre_url=page_url(membre_id),
        )
        state["nav_appended"] = True

    state["parent_page_id"] = parent_id
    save_state(state)

    # Écrit aussi dans config pour les autres scripts
    cfg.setdefault("notion", {})
    cfg["notion"] = {
        "parent_page_id": parent_id,
        "vitrine_page_id": vitrine_id,
        "membre_page_id": membre_id,
        "abonnes_db_id": state.get("abonnes_db_id"),
        "abonnes_data_source_id": state.get("abonnes_data_source_id"),
        "vitrine_url": page_url(vitrine_id),
        "membre_url": page_url(membre_id),
    }
    commerce_cfg.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"État : {STATE_PATH}")
    print(f"Config : {commerce_cfg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
