"""Injecte site-tts.js dans les HTML exportés (manuel, etc.) qui n'ont pas encore le script."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TTS_MARK = "site-tts.js"
NAV_RE = re.compile(r'(<script\s+src="([^"]*)site-nav\.js[^"]*"></script>)', re.I)


def patch_tree(root: Path) -> int:
    if not root.exists():
        return 0
    n = 0
    for path in root.rglob("index.html"):
        text = path.read_text(encoding="utf-8")
        if TTS_MARK in text:
            continue
        if "manuel-prose" not in text and "dict-entries" not in text:
            continue
        m = NAV_RE.search(text)
        if not m:
            continue
        prefix = m.group(2)
        insert = f'<script src="{prefix}site-tts.js?v=6"></script>\n'
        text = text.replace(m.group(1), insert + m.group(1), 1)
        path.write_text(text, encoding="utf-8")
        n += 1
    return n


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+", type=Path)
    args = parser.parse_args()
    total = 0
    for root in args.roots:
        n = patch_tree(root)
        total += n
        print(f"{n} fichier(s) patché(s) : {root}")
    print(f"Total : {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
