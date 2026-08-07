"""CLI extraction Notion → JSON (Google Drive)."""

from __future__ import annotations

import argparse
import sys

from .pull.index_export import export_index
from .pull.jurisprudence import export_jurisprudence
from .pull.manuel import export_manuel

COMMANDS = {
    "jurisprudence": export_jurisprudence,
    "manuel": export_manuel,
    "index": export_index,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extraction Notion → JSON (sortie Google Drive)"
    )
    parser.add_argument(
        "register",
        choices=[*COMMANDS.keys(), "all"],
        help="Registre à extraire",
    )
    parser.add_argument("--limit", type=int, help="Limiter le nombre de pages (test)")
    args = parser.parse_args(argv)

    targets = list(COMMANDS.keys()) if args.register == "all" else [args.register]

    try:
        for name in targets:
            print(f"\n=== {name} ===")
            COMMANDS[name](limit=args.limit)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrompu.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
