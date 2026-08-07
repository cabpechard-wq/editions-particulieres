"""Chemins racine du monorepo (site/ est à 1 niveau sous la racine)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = Path(__file__).resolve().parent
