"""Post-traitement PDF — convertit les .docx existants via Microsoft Word."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from extract.pull._common import load_env

from .word_pdf import convert_tree


def main(argv: list[str] | None = None) -> int:
    load_env()
    from packages.ep_core.paths import resolve_path

    default_out = resolve_path("export")

    parser = argparse.ArgumentParser(
        description="Convertit les .docx en .pdf (post-traitement Word / pywin32)."
    )
    parser.add_argument(
        "--out",
        "-o",
        type=Path,
        default=default_out,
        help=f"Dossier à parcourir (défaut : {default_out})",
    )
    parser.add_argument(
        "--file",
        "-f",
        type=Path,
        action="append",
        default=[],
        help="Fichier .docx unique (répétable)",
    )
    args = parser.parse_args(argv)

    if args.file:
        from .word_pdf import convert_docx_list_to_pdf

        produced, errors = convert_docx_list_to_pdf(
            [Path(f) for f in args.file],
            log=print,
        )
    else:
        out = Path(args.out)
        if not out.exists():
            print(f"Dossier introuvable : {out}", file=sys.stderr)
            return 1
        produced, errors = convert_tree(out, log=print)

    print(f"{len(produced)} PDF créé(s), {errors} erreur(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
