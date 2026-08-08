"""Smoke tests locaux du parcours commerce (gate + config) + artefact dist.

Usage :
  python site/test_commerce.py
  python site/test_commerce.py --skip-artifact   # config seule
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parent
SITE = SITE_ROOT / "dist" / "site"
CFG = SITE_ROOT / "config.json"
STATE = SITE_ROOT / "notion_state.json"
PW_FILE = SITE_ROOT / ".members_password"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def ok(msg: str) -> None:
    print(f"OK: {msg}")


def warn(msg: str) -> None:
    print(f"WARN: {msg}")


def check_config() -> int:
    """Retourne le nombre d'erreurs soft (pending URLs)."""
    if not CFG.is_file():
        fail("site/config.json manquant")

    cfg = json.loads(CFG.read_text(encoding="utf-8-sig"))

    if PW_FILE.is_file():
        password = PW_FILE.read_text(encoding="utf-8").strip()
        digest = hashlib.sha256(password.encode()).hexdigest()
        gate = SITE / "flipcards" / "index.html"
        if gate.is_file():
            if digest not in gate.read_text(encoding="utf-8", errors="ignore"):
                fail("hash mot de passe absent du gate flipcards")
            ok("gate SHA-256 coherent")
        if not cfg.get("members_password"):
            warn("config.members_password vide (fichier .members_password present)")
    else:
        warn(".members_password absent (OK en CI si gate non hashe localement)")

    notion = cfg.get("notion") or {}
    if not notion.get("vitrine_page_id"):
        warn("notion.vitrine_page_id vide")
    if not notion.get("membre_page_id"):
        warn("notion.membre_page_id vide")
    if STATE.is_file():
        ok("notion_state.json present")
    else:
        warn("notion_state.json absent")

    stripe = cfg.get("stripe") or {}
    ls = cfg.get("lemonsqueezy") or {}
    auth = cfg.get("auth") or {}
    pending: list[str] = []
    monthly = (stripe.get("monthly_payment_link") or "") or (
        ls.get("monthly_checkout_url") or ""
    )
    yearly = (stripe.get("yearly_payment_link") or "") or (
        ls.get("yearly_checkout_url") or ""
    )
    if not str(monthly).startswith("http"):
        pending.append("Stripe monthly_payment_link")
    if not str(yearly).startswith("http"):
        pending.append("Stripe yearly_payment_link")
    if not str(cfg.get("demo_url") or "").startswith("http"):
        pending.append("demo_url")
    if not str(cfg.get("flipcards_url") or "").startswith("http"):
        pending.append("flipcards_url")
    if not str(auth.get("api_url") or "").startswith("http"):
        pending.append("auth.api_url")

    if pending:
        print("PENDING (URLs) :")
        for item in pending:
            print(f"  - {item}")
        return 1

    ok("URLs externes renseignees")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--skip-artifact",
        action="store_true",
        help="Ne pas lancer smoke_artifact.py",
    )
    args = p.parse_args(argv)

    if not args.skip_artifact:
        if not SITE.is_dir():
            fail("dist/site manquant — lance build_assets / build_site")
        sys.path.insert(0, str(SITE_ROOT))
        from smoke_artifact import main as artifact_main

        code = artifact_main([])
        if code != 0:
            return code
    else:
        warn("smoke artefact ignore (--skip-artifact)")

    errors = check_config()
    print("---")
    print(
        "E2E manuel restant : paiement test Stripe -> /merci/ -> "
        "flipcards -> /membre/."
    )
    if errors:
        print("SMOKE COMMERCE : pending URLs")
    else:
        print("SMOKE COMMERCE OK")
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
