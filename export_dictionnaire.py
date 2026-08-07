"""Point d'entrée : python export_dictionnaire.py [--out chemin] [--limit N]"""

from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from extract.html.__main__ import run_export
from packages.ep_core.paths import REPO_ROOT


def main() -> int:
    load_dotenv(REPO_ROOT / ".env")
    p = argparse.ArgumentParser(description="Export glossaire Notion → HTML site")
    p.add_argument("--out", type=Path, default=None, help="Dossier de sortie (défaut : export_site)")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--templates", type=Path, default=None, help="Gabarits site")
    args = p.parse_args()

    out = args.out
    if out is None:
        from packages.ep_core.paths import resolve_path

        out = resolve_path("export_site")

    templates = args.templates
    if templates is None:
        try:
            from packages.ep_core.paths import resolve_path

            templates = resolve_path("templates_site")
        except (KeyError, OSError):
            templates = REPO_ROOT / "site" / "templates"

    return run_export(
        registre="index",
        out=Path(out),
        limit=args.limit,
        templates=Path(templates) if templates else None,
    )


if __name__ == "__main__":
    raise SystemExit(main())
