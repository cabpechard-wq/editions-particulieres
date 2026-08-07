"""Ajoute une case CGV obligatoire (custom_fields) sur les Payment Links Stripe.

Prérequis : STRIPE_SECRET_KEY dans .env

Usage :
  .\\.venv\\Scripts\\python.exe site\\update_stripe_cgv_consent.py
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
SITE_ROOT = Path(__file__).resolve().parent
CFG = SITE_ROOT / "config.json"
API = "https://api.stripe.com/v1"

# Label Stripe custom_fields : max 50 caractères
CGV_CHECKBOX_LABEL = "J'accepte les CGV et mentions légales"
CGV_FIELD_KEY = "cgv_accept"


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
    path = urlparse(url).path.strip("/")
    if not path:
        return None
    for full, plid in links_by_url.items():
        if urlparse(full).path.strip("/") == path:
            return plid
    return None


def cgv_custom_fields_payload() -> dict:
    """Case à cocher requise, non pré-cochée (comportement Stripe checkbox)."""
    return {
        "custom_fields[0][key]": CGV_FIELD_KEY,
        "custom_fields[0][type]": "checkbox",
        "custom_fields[0][label][type]": "custom",
        "custom_fields[0][label][custom]": CGV_CHECKBOX_LABEL,
        "custom_fields[0][optional]": "false",
    }


def main() -> int:
    load_dotenv(ROOT / ".env")
    load_dotenv(SITE_ROOT / ".env")
    key = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
    if not key:
        print("STRIPE_SECRET_KEY manquant dans .env", file=sys.stderr)
        return 2

    if len(CGV_CHECKBOX_LABEL) > 50:
        raise SystemExit("Label CGV > 50 caractères (limite Stripe)")

    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
    stripe = cfg.get("stripe") or {}
    wanted = {
        "monthly": stripe.get("monthly_payment_link") or "",
        "yearly": stripe.get("yearly_payment_link") or "",
        "test": stripe.get("test_payment_link") or "",
    }
    wanted = {k: v for k, v in wanted.items() if v.startswith("http")}
    if not wanted:
        raise SystemExit("Aucun payment link dans config.json")

    base = (cfg.get("hosting") or {}).get("base_url") or (
        "https://cabpechard-wq.github.io/editions-particulieres"
    )
    legal = {
        "cgv_url": f"{base.rstrip('/')}/cgv/",
        "mentions_url": f"{base.rstrip('/')}/mentions-legales/",
        "cgv_version": "2026-08-05",
        "stripe_field_key": CGV_FIELD_KEY,
        "stripe_field_label": CGV_CHECKBOX_LABEL,
    }
    cfg["legal"] = legal
    CFG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("config.json → legal:", legal)

    with httpx.Client(timeout=60.0) as client:
        listed = stripe_get(
            client, key, "/payment_links", {"active": "true", "limit": 100}
        )
        by_url: dict[str, str] = {}
        for link in listed.get("data") or []:
            u = (link.get("url") or "").rstrip("/")
            if u and link.get("id"):
                by_url[u] = link["id"]

        payload = cgv_custom_fields_payload()
        for label, url in wanted.items():
            plid = payment_link_id_from_url(url, by_url)
            if not plid:
                print(f"  [{label}] INTROUVABLE : {url}", file=sys.stderr)
                continue
            updated = stripe_post(
                client,
                key,
                f"/payment_links/{plid}",
                payload,
            )
            fields = updated.get("custom_fields") or []
            print(f"  [{label}] {plid} custom_fields={len(fields)}")
            for f in fields:
                print(
                    f"       key={f.get('key')} type={f.get('type')} "
                    f"optional={f.get('optional')}"
                )

    print("OK — case CGV obligatoire sur les Payment Links.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
