"""Chargement de la configuration (Notion, commerce, chemins)."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "config"


def load_json(name: str) -> dict:
    for candidate in (CONFIG_DIR / name, CONFIG_DIR / f"{name}.example"):
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8-sig"))
    return {}
