"""Registres Notion — ordre, libellés, résolution des bases."""

from __future__ import annotations

import os
from functools import lru_cache

from packages.ep_core.config import load_json

REGISTRE_ORDER = ("manuel", "fiches", "methodo", "formule", "index", "arrets")

REGISTRE_LABELS = {
    "manuel": "Cours",
    "fiches": "Fiches",
    "methodo": "Méthode",
    "formule": "Formule",
    "index": "Glossaire",
    "arrets": "Jurisprudence",
}

# Clé dans config/notion.json → registre GUI
REGISTRE_DB_KEY = {
    "manuel": "manuel",
    "fiches": "fiches",
    "methodo": "methodo",
    "formule": "formule",
    "index": "index",
    "arrets": "jurisprudence",
}

# Repli si config/notion.json incomplet (mêmes bases que l'ancien programme)
_FALLBACK_DB = {
    "manuel": "https://app.notion.com/p/395a29ad9f7880db98b6cfaef4ff154c",
    "fiches": "https://app.notion.com/p/3b0a29ad9f78806babfcea2e44be709a",
    "formule": "https://app.notion.com/p/39ea29ad9f78802c83e7dc691d065b83",
    "methodo": "https://app.notion.com/p/39ba29ad9f7880dab45edd71447ff8f2",
    "index": "https://app.notion.com/p/39aa29ad9f78804ca01de7cd41826df1",
    "jurisprudence": "https://app.notion.com/p/39ba29ad9f7880229765cbea38ae793a",
}

_ENV_DB = {
    "manuel": "NOTION_DATABASE_ID",
    "fiches": "NOTION_FICHES_DATABASE_ID",
    "formule": "NOTION_FORMULE_DATABASE_ID",
    "methodo": "NOTION_METHODO_DATABASE_ID",
    "index": "NOTION_INDEX_DATABASE_ID",
    "jurisprudence": "NOTION_ARRETS_DATABASE_ID",
}


@lru_cache(maxsize=1)
def notion_databases() -> dict[str, str]:
    cfg = load_json("notion.json")
    merged = dict(_FALLBACK_DB)
    for key, url in (cfg.get("databases") or {}).items():
        if (url or "").strip():
            merged[key] = url.strip()
    for key, env_name in _ENV_DB.items():
        val = (os.getenv(env_name) or "").strip()
        if val:
            merged[key] = val
    return merged


def database_url_for_registre(registre: str) -> str:
    if registre not in REGISTRE_DB_KEY:
        raise ValueError(f"Registre inconnu : {registre}")
    db_key = REGISTRE_DB_KEY[registre]
    url = notion_databases().get(db_key, "").strip()
    if not url:
        raise ValueError(
            f"Base Notion non configurée pour {REGISTRE_LABELS.get(registre, registre)} "
            f"(config/notion.json → databases.{db_key})."
        )
    return url
