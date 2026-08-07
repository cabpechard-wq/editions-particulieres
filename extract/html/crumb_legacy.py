"""Retire le segment « Éditions Particulières » des fils d'Ariane HTML hérités."""

from __future__ import annotations

import re
from pathlib import Path

_LEGACY_CRUMB = re.compile(
    r"\s*<span>\s*Éditions Particulières\s*</span>\s*"
    r'<span class="sep">›</span>\s*',
    re.IGNORECASE,
)


def strip_legacy_crumb(html: str) -> str:
    return _LEGACY_CRUMB.sub("", html, count=1)


def fix_html_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    fixed = strip_legacy_crumb(text)
    if fixed == text:
        return False
    path.write_text(fixed, encoding="utf-8")
    return True


def fix_tree(root: Path, *, glob: str = "**/*.html") -> int:
    if not root.is_dir():
        return 0
    count = 0
    for path in root.glob(glob):
        if fix_html_file(path):
            count += 1
    return count
