"""Smoke tests locaux du parcours commerce (gate HTML + config + Notion state)."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

COMMERCE = Path(__file__).resolve().parent
SITE = COMMERCE / "dist" / "site"
CFG = COMMERCE / "config.json"
STATE = COMMERCE / "notion_state.json"
PW_FILE = COMMERCE / ".members_password"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def ok(msg: str) -> None:
    print(f"OK: {msg}")


def main() -> int:
    errors = 0

    if not SITE.exists():
        fail("dist/site manquant — lance build_assets.py")

    demo = SITE / "demo" / "index.html"
    gate = SITE / "flipcards" / "index.html"
    app = SITE / "flipcards" / "app.html"
    for p in (demo, gate, app):
        if not p.exists():
            fail(f"fichier manquant {p}")
        if p.stat().st_size < 500:
            fail(f"fichier trop petit {p}")
    ok("artefacts demo + flipcards présents")

    if not PW_FILE.exists():
        fail("mot de passe membres manquant")
    password = PW_FILE.read_text(encoding="utf-8").strip()
    digest = hashlib.sha256(password.encode()).hexdigest()
    gate_html = gate.read_text(encoding="utf-8")
    if digest not in gate_html:
        fail("hash mot de passe absent du gate")
    ok("gate SHA-256 cohérent")

    app_html = app.read_text(encoding="utf-8")
    if "flipcards_ok" not in app_html:
        fail("garde session absente de app.html")
    ok("garde session injectée dans app.html")

    # Démo limitée : compter les slides si possible
    demo_html = demo.read_text(encoding="utf-8")
    slides = len(re.findall(r'class="card-slide"', demo_html))
    if slides == 0:
        slides = len(re.findall(r"data-index=", demo_html))
    if slides == 0:
        # fallback : fichier démo non vide et plus petit que le pack membres
        app = SITE / "flipcards" / "app.html"
        if demo.stat().st_size >= app.stat().st_size * 0.5:
            fail("démo trop volumineuse vs app complète")
        ok(f"démo présente ({demo.stat().st_size} octets, < app complète)")
    else:
        if slides > 12:
            fail(f"démo trop large ({slides} slides) — attendu ~8")
        ok(f"démo limitée ({slides} slides)")

    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))
    if not cfg.get("members_password"):
        fail("config.members_password vide")
    if not (cfg.get("notion") or {}).get("vitrine_page_id"):
        fail("notion vitrine manquante dans config")
    if not (cfg.get("notion") or {}).get("membre_page_id"):
        fail("notion membre manquant dans config")
    ok("config notion + password")

    if not STATE.exists():
        fail("notion_state.json manquant")
    ok("notion_state.json présent")

    # Checklist externe
    ls = cfg.get("lemonsqueezy") or {}
    sotion = cfg.get("sotion") or {}
    hosting = cfg.get("hosting") or {}

    pending = []
    ls = cfg.get("lemonsqueezy") or {}
    products_brief = COMMERCE / "lemonsqueezy_products.json"
    checkout_page = SITE / "checkout" / "index.html"
    if not (ls.get("monthly_checkout_url") or "").startswith("http"):
        if products_brief.exists() and checkout_page.exists():
            ok(
                "Lemon Squeezy : catalogue + page /checkout/ prets "
                "(URLs live apres LEMON_SQUEEZY_API_KEY)"
            )
        else:
            pending.append("Lemon Squeezy checkout URL (setup_lemonsqueezy.py + API key)")
    if not (cfg.get("demo_url") or "").startswith("http"):
        pending.append("Hébergement demo_url (deploy_netlify.py ou surge)")
    if not (cfg.get("flipcards_url") or "").startswith("http"):
        pending.append("Hébergement flipcards_url")
    if not (sotion.get("site_url") or "").startswith("http"):
        pending.append("Sotion/membre site_url (build_membre_gate.py)")

    print("---")
    if pending:
        print("PENDING (actions comptes externes) :")
        for p in pending:
            print(f"  - {p}")
        errors = 1
    else:
        ok("toutes les URLs externes renseignées")
        print(
            "E2E manuel restant : paiement test Lemon Squeezy -> acces membre -> "
            "ouverture flipcards -> resiliation -> coupure."
        )

    # Test logique révocation soft
    print("---")
    print(
        "Révocation soft : retirer le membre Sotion / changer "
        f"commerce/.members_password puis rebuild (build_assets.py) "
        f"coupe l'accès HTML même si le fichier a été bookmarké sans session."
    )
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
