"""Configure Sotion (instructions + état local). Sotion n'a pas d'API publique stable.

Remplit SITE_ROOT/config.json une fois les URLs connues, et met à jour Notion.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parent
CFG = SITE_ROOT / "config.json"
OUT = SITE_ROOT / "sotion_setup.txt"


def main() -> int:
    cfg = json.loads(CFG.read_text(encoding="utf-8-sig")) if CFG.exists() else {}
    notion = cfg.get("notion") or {}
    ls = cfg.get("lemonsqueezy") or {}

    lines = [
        "SOTION — configuration paywall (no-code)",
        "========================================",
        "",
        "1) Crée un compte : https://sotion.co / https://sotion.so",
        "2) New site → colle la page Notion VITRINE (publique) :",
        f"   {notion.get('vitrine_url', '(lancer setup_notion.py)')}",
        "3) Ajoute / lie aussi la page ESPACE MEMBRE :",
        f"   {notion.get('membre_url', '')}",
        "4) Access control → Paid membership → Lemon Squeezy",
        "   - Mensuel : " + (ls.get("monthly_checkout_url") or ls.get("monthly_variant_id") or "(setup_lemonsqueezy.py)"),
        "   - Annuel  : " + (ls.get("yearly_checkout_url") or ls.get("yearly_variant_id") or ""),
        "5) Gate UNIQUEMENT l'espace membre (vitrine reste publique).",
        "6) Custom domain optionnel plus tard.",
        "7) Copie l'URL Sotion du site et enregistre-la :",
        "   Édite SITE_ROOT/config.json → sotion.site_url",
        "   puis : python site/update_notion_links.py",
        "",
        "Test accès :",
        "- Sans abo → page membre bloquée / login Sotion",
        "- Avec abo Lemon Squeezy test → accès membre + lien flipcards",
        "- Résiliation → accès retiré après expiration",
        "",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT.read_text(encoding="utf-8").encode("ascii", "replace").decode("ascii"))

    # Si site_url déjà fourni, OK
    if (cfg.get("sotion") or {}).get("site_url"):
        print("sotion.site_url déjà renseigné.")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
