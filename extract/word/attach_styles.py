"""Ré-attache Editions_Particulieres.dotx sur les .docx déjà générés (lien natif Word)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from packages.ep_core.paths import resolve_path

from .styles_master import attach_master_styles, master_styles_path, relink_tree

REPO_ROOT = Path(__file__).resolve().parents[2]


def default_export_dir() -> Path:
    try:
        return resolve_path("export")
    except (KeyError, OSError):
        return REPO_ROOT / "output"


def main(argv: list[str] | None = None) -> int:
    default_master = master_styles_path()
    default_out = default_export_dir()

    parser = argparse.ArgumentParser(
        description=(
            "Attache le modèle Editions_Particulieres.dotx aux .docx existants "
            "et active « Mettre à jour automatiquement les styles » dans Word."
        )
    )
    parser.add_argument(
        "--out",
        "-o",
        type=Path,
        default=default_out,
        help=f"Dossier à parcourir (défaut : {default_out})",
    )
    parser.add_argument(
        "--master",
        "-t",
        type=Path,
        default=None,
        help=f"Modèle .dotx (défaut : {default_master})",
    )
    parser.add_argument(
        "--file",
        "-f",
        type=Path,
        action="append",
        default=[],
        help="Fichier .docx unique (répétable) ; sinon parcours --out",
    )
    args = parser.parse_args(argv)

    master = Path(args.master) if args.master else master_styles_path()
    if not master.exists():
        print(f"Erreur : modèle introuvable : {master}", file=sys.stderr)
        print("Génère-le : python -m extract.word.template", file=sys.stderr)
        return 1

    if args.file:
        for f in args.file:
            attach_master_styles(Path(f), master=master)
            print(f"OK {f}")
        return 0

    out = Path(args.out)
    if not out.exists():
        print(f"Dossier introuvable : {out}", file=sys.stderr)
        return 1

    done = relink_tree(out, master=master)
    print(f"{len(done)} fichier(s) attache(s) -> {master}")
    for path in done:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
