"""Vérifie le parcours public (auth Worker)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

COMMERCE = Path(__file__).resolve().parent
BASE = "https://cabpechard-wq.github.io/editions-particulieres"
CFG = json.loads((COMMERCE / "config.json").read_text(encoding="utf-8-sig"))


def fetch(path: str) -> str:
    url = f"{BASE}{path}"
    r = subprocess.run(
        ["curl.exe", "-fsSL", url],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if r.returncode != 0:
        raise SystemExit(f"FAIL fetch {url}: {r.stderr or r.stdout}")
    return r.stdout


def must(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL {msg}")
    print(f"OK  {msg}")


def main() -> int:
    home = fetch("/")
    must("membre" in home.lower(), "accueil lien membre")
    must("checkout" in home.lower(), "accueil lien checkout")

    checkout = fetch("/checkout/")
    stripe = CFG.get("stripe") or {}
    for key, label in (
        ("monthly_payment_link", "mensuel"),
        ("yearly_payment_link", "annuel"),
        ("test_payment_link", "test"),
    ):
        url = stripe.get(key) or ""
        must(bool(url) and url in checkout, f"checkout lien {label}")

    merci = fetch("/merci/")
    must("session_id" in merci, "merci exige session_id")
    must("flipcards_ok" not in merci or "set-password" in merci, "merci sans unlock gratuit")
    must("auth.js" in merci, "merci charge auth.js")

    membre = fetch("/membre/")
    must("/api/login" in membre or "api/login" in membre, "membre login API")
    must("forgot" in membre, "lien mot de passe oublie")

    auth_js = fetch("/auth.js")
    must("FLIPCARDS_AUTH" in auth_js, "auth.js present")
    api = ((CFG.get("auth") or {}).get("api_url") or "")
    if "EXAMPLE" in api:
        print("WARN auth.api_url encore EXAMPLE — deployer le Worker")
    else:
        must(api in auth_js, "auth.js pointe vers api_url")

    app = fetch("/flipcards/app.html")
    must("/api/me" in app or "api/me" in app, "garde flipcards /api/me")

    print()
    print("Flow front OK.")
    print("Suite : wrangler deploy + Stripe redirect session_id + migrate KV")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
