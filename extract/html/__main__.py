"""CLI : python -m extract.html [--registre manuel|index] [--out chemin]"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from packages.ep_core.paths import REPO_ROOT

from .export_pipeline import run_html_pipeline
from gui.request import PipelineRequest


def run_export(
    *,
    registre: str,
    out: Path,
    limit: int | None = None,
    templates: Path | None = None,
) -> int:
    req = PipelineRequest(
        registres=[registre],
        out=Path(out),
        limit=limit,
        format="html",
        site_templates=templates,
    )
    code, paths = run_html_pipeline(req)
    for path in paths:
        print(path)
    return code


def main() -> int:
    load_dotenv(REPO_ROOT / ".env")
    p = argparse.ArgumentParser(description="Export Notion → HTML (manuel ou glossaire)")
    p.add_argument(
        "--registre",
        choices=("manuel", "index", "arrets"),
        default="manuel",
        help="manuel : sommaire + chapitres ; index : dictionnaire ; arrets : fiches jurisprudence",
    )
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
        registre=args.registre,
        out=Path(out),
        limit=args.limit,
        templates=Path(templates) if templates else None,
    )


if __name__ == "__main__":
    raise SystemExit(main())
