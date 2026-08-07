"""Crée des Payment Links Stripe pour les abos mensuel/annuel.

Prérequis dans .env :
  STRIPE_SECRET_KEY=sk_live_...   (ou sk_test_...)

Lit commerce/config.json → stripe.monthly_product_id / yearly_product_id
Écrit les payment_link URLs et met à jour le checkout HTML via build_assets.

Usage :
  .\\.venv\\Scripts\\python.exe commerce\\setup_stripe_links.py
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
API = "https://api.stripe.com/v1"


def stripe_get(client: httpx.Client, key: str, path: str, params: dict | None = None) -> dict:
    r = client.get(f"{API}{path}", params=params or {}, auth=(key, ""))
    if r.status_code >= 400:
        raise SystemExit(f"Stripe GET {path} -> {r.status_code}: {r.text}")
    return r.json()


def stripe_post(client: httpx.Client, key: str, path: str, data: dict) -> dict:
    r = client.post(f"{API}{path}", data=data, auth=(key, ""))
    if r.status_code >= 400:
        raise SystemExit(f"Stripe POST {path} -> {r.status_code}: {r.text}")
    return r.json()


def default_recurring_price(client: httpx.Client, key: str, product_id: str) -> dict:
    data = stripe_get(
        client,
        key,
        "/prices",
        {"product": product_id, "active": "true", "type": "recurring", "limit": 10},
    )
    prices = data.get("data") or []
    if not prices:
        raise SystemExit(
            f"Aucun prix récurrent actif pour {product_id}. "
            "Crée un Price (abonnement) sur le produit dans Stripe."
        )
    # Préfère EUR
    for p in prices:
        if (p.get("currency") or "").lower() == "eur":
            return p
    return prices[0]


def ensure_payment_link(
    client: httpx.Client, key: str, *, price_id: str, label: str
) -> str:
    # Cherche un lien existant pour ce price
    existing = stripe_get(client, key, "/payment_links", {"active": "true", "limit": 100})
    for link in existing.get("data") or []:
        for item in link.get("line_items") or [] or []:
            pass
        # line_items not expanded in list — retrieve
    # Crée un lien dédié (idempotence soft via metadata)
    created = stripe_post(
        client,
        key,
        "/payment_links",
        {
            "line_items[0][price]": price_id,
            "line_items[0][quantity]": "1",
            "after_completion[type]": "redirect",
            "after_completion[redirect][url]": "https://cabpechard-wq.github.io/editions-particulieres/merci/?session_id={CHECKOUT_SESSION_ID}",
            "allow_promotion_codes": "true",
            "billing_address_collection": "auto",
            "metadata[flipcards]": label,
            "metadata[source]": "flipcards-jp",
            "custom_fields[0][key]": "cgv_accept",
            "custom_fields[0][type]": "checkbox",
            "custom_fields[0][label][type]": "custom",
            "custom_fields[0][label][custom]": "J'accepte les CGV et mentions légales",
            "custom_fields[0][optional]": "false",
        },
    )
    url = created.get("url") or ""
    if not url:
        raise SystemExit(f"Payment Link créé sans URL : {created}")
    print(f"{label}: {url}")
    return url


def main() -> int:
    load_dotenv(ROOT / ".env")
    load_dotenv(COMMERCE / ".env")
    key = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
    if not key:
        print(
            "STRIPE_SECRET_KEY manquant dans .env\n"
            "Sinon, colle manuellement dans config.json :\n"
            "  stripe.monthly_payment_link / stripe.yearly_payment_link\n"
            "  (Dashboard Stripe → Payment links)",
            file=sys.stderr,
        )
        return 2

    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
    stripe = cfg.setdefault("stripe", {})
    monthly_prod = stripe.get("monthly_product_id") or ""
    yearly_prod = stripe.get("yearly_product_id") or ""
    if not monthly_prod or not yearly_prod:
        raise SystemExit("stripe.monthly_product_id / yearly_product_id manquants")

    with httpx.Client(timeout=60.0) as client:
        m_price = default_recurring_price(client, key, monthly_prod)
        y_price = default_recurring_price(client, key, yearly_prod)
        stripe["monthly_price_id"] = m_price["id"]
        stripe["yearly_price_id"] = y_price["id"]
        print(
            f"prices monthly={m_price['id']} "
            f"({(m_price.get('unit_amount') or 0)/100} {m_price.get('currency')})"
        )
        print(
            f"prices yearly={y_price['id']} "
            f"({(y_price.get('unit_amount') or 0)/100} {y_price.get('currency')})"
        )

        # Si liens déjà fournis, ne pas recréer
        if not (stripe.get("monthly_payment_link") or "").startswith("http"):
            stripe["monthly_payment_link"] = ensure_payment_link(
                client, key, price_id=m_price["id"], label="monthly"
            )
        if not (stripe.get("yearly_payment_link") or "").startswith("http"):
            stripe["yearly_payment_link"] = ensure_payment_link(
                client, key, price_id=y_price["id"], label="yearly"
            )

    # Le checkout HTML lit aussi lemonsqueezy.* — on aligne les deux
    cfg.setdefault("lemonsqueezy", {})
    cfg["lemonsqueezy"]["monthly_checkout_url"] = stripe["monthly_payment_link"]
    cfg["lemonsqueezy"]["yearly_checkout_url"] = stripe["yearly_payment_link"]
    # CTA principal Notion = page checkout locale (boutons mensuel/annuel)
    base = (cfg.get("hosting") or {}).get("base_url") or "https://cabpechard-wq.github.io/editions-particulieres"
    cfg["checkout_url"] = f"{base.rstrip('/')}/checkout/"

    CFG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("config.json mis a jour")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
