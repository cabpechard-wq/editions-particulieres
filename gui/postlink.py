"""Postlink — à brancher (interface GUI déjà en place)."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Réécriture des liens inter-fiches (manifest.json).")
    parser.add_argument("--format", default="docx")
    parser.add_argument("--out", type=str, default="")
    parser.parse_args(argv)
    print("Postlink : disponible prochainement dans ce monorepo.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
