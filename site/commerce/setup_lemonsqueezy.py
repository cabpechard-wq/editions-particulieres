"""Crée les produits abonnement Lemon Squeezy (mensuel + annuel) via API.

Prérequis : LEMON_SQUEEZY_API_KEY et LEMON_SQUEEZY_STORE_ID dans .env
  https://app.lemonsqueezy.com/settings/api

Usage :
  .\\.venv\\Scripts\\python.exe commerce\\setup_lemonsqueezy.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

from _repo import REPO_ROOT as ROOT
COMMERCE = Path(__file__).resolve().parent
CFG = COMMERCE / "config.json"
API = "https://api.lemonsqueezy.com/v1"


def headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
    }


def ls_request(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    api_key: str,
    json_body: dict | None = None,
) -> dict:
    r = client.request(method, f"{API}{path}", headers=headers(api_key), json=json_body)
    if r.status_code >= 400:
        raise SystemExit(f"Lemon Squeezy {method} {path} -> {r.status_code}: {r.text}")
    return r.json() if r.text else {}


def ensure_product(client: httpx.Client, *, api_key: str, store_id: str, name: str, description: str) -> str:
    # Liste produits existants
    data = ls_request(
        client,
        "GET",
        f"/products?filter[store_id]={store_id}",
        api_key=api_key,
    )
    for item in data.get("data") or []:
        if item.get("attributes", {}).get("name") == name:
            print(f"Produit existant : {name} ({item['id']})")
            return item["id"]

    created = ls_request(
        client,
        "POST",
        "/products",
        api_key=api_key,
        json_body={
            "data": {
                "type": "products",
                "attributes": {
                    "name": name,
                    "description": description,
                    "status": "published",
                },
                "relationships": {
                    "store": {"data": {"type": "stores", "id": str(store_id)}}
                },
            }
        },
    )
    pid = created["data"]["id"]
    print(f"Produit créé : {name} ({pid})")
    return pid


def ensure_variant(
    client: httpx.Client,
    *,
    api_key: str,
    product_id: str,
    name: str,
    price_cents: int,
    interval: str,
    interval_count: int = 1,
) -> tuple[str, str]:
    """Retourne (variant_id, share_url approximatif)."""
    data = ls_request(
        client,
        "GET",
        f"/variants?filter[product_id]={product_id}",
        api_key=api_key,
    )
    for item in data.get("data") or []:
        attrs = item.get("attributes") or {}
        if attrs.get("name") == name:
            print(f"Variante existante : {name} ({item['id']})")
            return item["id"], attrs.get("share_url") or ""

    # Lemon Squeezy crée souvent une variante Default à la création produit.
    # On met à jour la première si name=Default, sinon on crée.
    created = ls_request(
        client,
        "POST",
        "/variants",
        api_key=api_key,
        json_body={
            "data": {
                "type": "variants",
                "attributes": {
                    "name": name,
                    "price": price_cents,
                    "is_subscription": True,
                    "interval": interval,
                    "interval_count": interval_count,
                    "status": "published",
                },
                "relationships": {
                    "product": {"data": {"type": "products", "id": str(product_id)}}
                },
            }
        },
    )
    vid = created["data"]["id"]
    share = (created["data"].get("attributes") or {}).get("share_url") or ""
    print(f"Variante créée : {name} ({vid}) {share}")
    return vid, share


def pick_store(client: httpx.Client, api_key: str, store_id: str | None) -> tuple[str, str]:
    data = ls_request(client, "GET", "/stores", api_key=api_key)
    stores = data.get("data") or []
    if not stores:
        raise SystemExit("Aucun store Lemon Squeezy. Crée-en un dans le dashboard.")
    if store_id:
        for s in stores:
            if s["id"] == str(store_id):
                return s["id"], s["attributes"].get("slug") or ""
        raise SystemExit(f"Store {store_id} introuvable")
    s = stores[0]
    return s["id"], s["attributes"].get("slug") or ""


def main() -> int:
    load_dotenv(ROOT / ".env")
    load_dotenv(COMMERCE / ".env")
    api_key = (os.getenv("LEMON_SQUEEZY_API_KEY") or "").strip()
    if not api_key:
        print(
            "LEMON_SQUEEZY_API_KEY manquant.\n"
            "1) https://app.lemonsqueezy.com/settings/api → Create API key\n"
            "2) Ajoute dans .env : LEMON_SQUEEZY_API_KEY=...\n"
            "   optionnel : LEMON_SQUEEZY_STORE_ID=...\n"
            "3) Relance ce script.",
            file=sys.stderr,
        )
        # Écrit le brief produit pour config manuelle
        brief = COMMERCE / "lemonsqueezy_products.json"
        payload = {
            "products": [
                {
                    "name": "Flipcards GADA — Mensuel étudiants",
                    "price_eur": 6.90,
                    "interval": "month",
                    "description": "Accès abonnés aux flipcards GADA (grands arrêts).",
                },
                {
                    "name": "Flipcards GADA — Annuel étudiants",
                    "price_eur": 59.00,
                    "interval": "year",
                    "description": "Accès annuel abonnés aux flipcards GADA.",
                },
            ],
            "webhook_events": [
                "subscription_created",
                "subscription_updated",
                "subscription_cancelled",
                "subscription_expired",
            ],
        }
        brief.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Brief écrit : {brief}")
        return 2

    cfg = json.loads(CFG.read_text(encoding="utf-8")) if CFG.exists() else {}
    pricing = cfg.get("pricing") or {}
    monthly_cents = int(round(float(pricing.get("monthly_eur", 6.9)) * 100))
    yearly_cents = int(round(float(pricing.get("yearly_eur", 59)) * 100))

    with httpx.Client(timeout=60.0) as client:
        store_id, slug = pick_store(
            client, api_key, (os.getenv("LEMON_SQUEEZY_STORE_ID") or "").strip() or None
        )
        print(f"Store {store_id} slug={slug}")

        product_id = ensure_product(
            client,
            api_key=api_key,
            store_id=store_id,
            name="Flipcards GADA — Abonnement étudiants",
            description=(
                "<p>Accès aux flipcards interactives des grands arrêts du droit public et administratif "
                "(grands arrêts du droit public et administratif).</p>"
                "<p>Résiliable à tout moment. Accès coupé en fin de période.</p>"
            ),
        )

        monthly_id, monthly_url = ensure_variant(
            client,
            api_key=api_key,
            product_id=product_id,
            name="Mensuel",
            price_cents=monthly_cents,
            interval="month",
        )
        yearly_id, yearly_url = ensure_variant(
            client,
            api_key=api_key,
            product_id=product_id,
            name="Annuel",
            price_cents=yearly_cents,
            interval="year",
        )

        # Récupère URLs share à jour
        for vid, key in ((monthly_id, "monthly"), (yearly_id, "yearly")):
            v = ls_request(client, "GET", f"/variants/{vid}", api_key=api_key)
            share = (v.get("data") or {}).get("attributes", {}).get("share_url") or ""
            if key == "monthly":
                monthly_url = share or monthly_url
            else:
                yearly_url = share or yearly_url

    cfg.setdefault("lemonsqueezy", {})
    cfg["lemonsqueezy"].update(
        {
            "store_id": store_id,
            "store_slug": slug,
            "product_id": product_id,
            "monthly_variant_id": monthly_id,
            "yearly_variant_id": yearly_id,
            "monthly_checkout_url": monthly_url,
            "yearly_checkout_url": yearly_url,
        }
    )
    if monthly_url:
        cfg["checkout_url"] = monthly_url
    CFG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(cfg["lemonsqueezy"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
