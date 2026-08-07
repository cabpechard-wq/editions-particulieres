"""Utilitaires communs d'extraction."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from packages.ep_core.config import load_json
from packages.ep_core.notion import make_notion_client
from packages.ep_core.paths import REPO_ROOT, ensure_output_dirs


def load_env() -> None:
    load_dotenv(REPO_ROOT / ".env")


def notion_token() -> str:
    load_env()
    token = (os.getenv("NOTION_TOKEN") or "").strip()
    if not token:
        raise ValueError("NOTION_TOKEN manquant — définis-le dans .env")
    return token


def database_url(key: str) -> str:
    cfg = load_json("notion.json")
    url = (cfg.get("databases") or {}).get(key) or ""
    if not url:
        env_map = {
            "manuel": "NOTION_DATABASE_ID",
            "jurisprudence": "NOTION_ARRETS_DATABASE_ID",
            "index": "NOTION_INDEX_DATABASE_ID",
        }
        env_key = env_map.get(key)
        if env_key:
            url = (os.getenv(env_key) or "").strip()
    if not url:
        raise ValueError(f"URL de base Notion introuvable pour {key!r}")
    return url


def write_json_export(
    path: Path,
    *,
    database: str,
    database_url: str,
    property_names: list[str],
    pages: list[dict[str, Any]],
    excluded_properties: list[str] | None = None,
    includes_content: bool = False,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "format": "json",
        "database": database,
        "database_url": database_url,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "count": len(pages),
        "properties": property_names,
        "excluded_properties": excluded_properties or [],
        "includes_content": includes_content,
        "pages": pages,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def make_fetcher(*, pause_s: float = 0.12):
    ensure_output_dirs()
    return make_notion_client(notion_token(), pause_s=pause_s)
