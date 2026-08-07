"""Corrige les fils d'Ariane HTML exportés (segment « Éditions Particulières »)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from extract.html.crumb_legacy import fix_tree  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "roots",
        nargs="*",
        type=Path,
        help="Dossiers à parcourir (défaut : export/site du Drive)",
    )
    args = parser.parse_args()

    if args.roots:
        roots = args.roots
    else:
        from packages.ep_core.paths import resolve_path

        export_site = resolve_path("export_site")
        roots = [
            export_site / "manuel",
            export_site / "dictionnaire",
            export_site / "arrets",
        ]

    total = 0
    for root in roots:
        if not root.exists():
            print(f"ignoré (absent) : {root}")
            continue
        n = fix_tree(root)
        total += n
        print(f"{n} fichier(s) corrigé(s) : {root}")

    print(f"Total : {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
