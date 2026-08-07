"""E2E local allégé : structure abonnes + templates auth présents."""

from __future__ import annotations

import json
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parent


def main() -> int:
    abonnes = json.loads((SITE_ROOT / "abonnes.json").read_text(encoding="utf-8-sig"))
    assert "antonin.pechard@gmail.com" in abonnes
    for name in (
        "auth.js",
        "merci.html",
        "membre.html",
        "membre-forgot.html",
        "membre-reset.html",
        "membre-compte.html",
    ):
        p = SITE_ROOT / "templates" / name
        assert p.exists(), p
    worker = SITE_ROOT / "worker" / "src" / "worker.js"
    assert worker.exists(), worker
    print("E2E structure auth OK")
    print("Migrer KV : python site/migrate_abonnes_to_kv.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
