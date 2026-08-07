"""Affiche la commande curl pour migrer abonnes.json → Worker KV (admin-migrate)."""

from __future__ import annotations

import json
from pathlib import Path

COMMERCE = Path(__file__).resolve().parent


def main() -> int:
    cfg = json.loads((COMMERCE / "config.json").read_text(encoding="utf-8-sig"))
    api = ((cfg.get("auth") or {}).get("api_url") or "").rstrip("/")
    abonnes = json.loads((COMMERCE / "abonnes.json").read_text(encoding="utf-8-sig"))
    print("Après wrangler deploy + AUTH_SECRET :")
    print()
    for email, row in sorted(abonnes.items()):
        if email.endswith(".local"):
            continue
        pw = row.get("password") or "CHANGE_ME"
        statut = row.get("statut") or "actif"
        print(
            f'curl -sS -X POST {api}/api/admin-migrate -H "Content-Type: application/json" '
            f'-d "{{\\"admin_secret\\":\\"YOUR_AUTH_SECRET\\",\\"email\\":\\"{email}\\",'
            f'\\"password\\":\\"{pw}\\",\\"status\\":\\"{statut}\\"}}"'
        )
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
