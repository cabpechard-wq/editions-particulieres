"""Force After payment → redirect /merci/ sur tous les Payment Links connus.

Prérequis : STRIPE_SECRET_KEY dans .env (racine ou commerce/)

Usage :
  .\\.venv\\Scripts\\python.exe commerce\\update_stripe_redirects.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

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


def payment_link_id_from_url(url: str, links_by_url: dict[str, str]) -> str | None:
    url = (url or "").rstrip("/")
    if url in links_by_url:
        return links_by_url[url]
    # Match by path suffix (buy.stripe.com/XXXX)
    path = urlparse(url).path.strip("/")
    if not path:
        return None
    for full, plid in links_by_url.items():
        if urlparse(full).path.strip("/") == path:
            return plid
    return None


def main() -> int:
    load_dotenv(ROOT / ".env")
    load_dotenv(COMMERCE / ".env")
    key = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
    if not key:
        print("STRIPE_SECRET_KEY manquant dans .env", file=sys.stderr)
        return 2

    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
    merci = (cfg.get("merci_url") or "").strip()
    if not merci:
        base = (cfg.get("hosting") or {}).get("base_url") or (
            "https://cabpechard-wq.github.io/editions-particulieres"
        )
        merci = f"{base.rstrip('/')}/merci/"

    stripe = cfg.get("stripe") or {}
    wanted = {
        "monthly": stripe.get("monthly_payment_link") or "",
        "yearly": stripe.get("yearly_payment_link") or "",
        "test": stripe.get("test_payment_link") or "",
    }
    wanted = {k: v for k, v in wanted.items() if v.startswith("http")}
    if not wanted:
        raise SystemExit("Aucun payment link dans config.json")

    with httpx.Client(timeout=60.0) as client:
        listed = stripe_get(
            client, key, "/payment_links", {"active": "true", "limit": 100}
        )
        by_url: dict[str, str] = {}
        for link in listed.get("data") or []:
            u = (link.get("url") or "").rstrip("/")
            if u and link.get("id"):
                by_url[u] = link["id"]

        print(f"Redirect cible : {merci}")
        for label, url in wanted.items():
            plid = payment_link_id_from_url(url, by_url)
            if not plid:
                print(f"  [{label}] INTROUVABLE dans Stripe : {url}", file=sys.stderr)
                continue
            updated = stripe_post(
                client,
                key,
                f"/payment_links/{plid}",
                {
                    "after_completion[type]": "redirect",
                    "after_completion[redirect][url]": merci,
                },
            )
            ac = updated.get("after_completion") or {}
            print(
                f"  [{label}] {plid} → type={ac.get('type')} "
                f"url={(ac.get('redirect') or {}).get('url')}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
