"""Chemins racine du monorepo (site/commerce est à 2 niveaux sous la racine)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMERCE = Path(__file__).resolve().parent
