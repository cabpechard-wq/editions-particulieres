"""Résolution des chemins de sortie (Google Drive + dépôt)."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "config"


def _default_output_root() -> Path:
    env = (os.getenv("EP_OUTPUT_ROOT") or "").strip()
    if env:
        return Path(env)
    return Path("G:/Mon Drive/Editions Particulieres")


@lru_cache(maxsize=1)
def load_paths_config() -> dict:
    for name in ("paths.json", "paths.json.example"):
        path = CONFIG_DIR / name
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8-sig"))
    return {"output_root": str(_default_output_root()), "paths": {}}


def output_root() -> Path:
    cfg = load_paths_config()
    env = (os.getenv("EP_OUTPUT_ROOT") or "").strip()
    raw = env or str(cfg.get("output_root") or "")
    return Path(raw) if raw else _default_output_root()


def resolve_path(key: str) -> Path:
    cfg = load_paths_config()
    mapping = cfg.get("paths") or {}
    template = mapping.get(key)
    if not template:
        raise KeyError(f"Chemin inconnu dans config/paths.json : {key!r}")
    resolved = template.format(
        output_root=output_root().as_posix(),
        repo_root=REPO_ROOT.as_posix(),
    )
    return Path(resolved)


def ensure_output_dirs() -> None:
    """Crée l'arborescence de sortie sur Google Drive (idempotent)."""
    keys = (
        "export",
        "export_manuel",
        "export_fiches",
        "export_arrets",
        "export_arrets_a5",
        "export_formule",
        "export_methodo",
        "export_index",
        "export_site",
        "matrices_jurisprudence",
        "matrices_flipcards",
        "flipcards_output",
        "site_build",
    )
    for key in keys:
        resolve_path(key).mkdir(parents=True, exist_ok=True)
