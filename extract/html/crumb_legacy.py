"""Retire le segment « Éditions Particulières » des fils d'Ariane HTML hérités
et renomme les libellés « Manuel » → « Cours » sur les pages exportées."""

from __future__ import annotations

import re
from pathlib import Path

_LEGACY_CRUMB = re.compile(
    r"\s*<span>\s*Éditions Particulières\s*</span>\s*"
    r'<span class="sep">›</span>\s*',
    re.IGNORECASE,
)

_MANUEL_LABEL_REPLACEMENTS = (
    ("Manuel de Droit public et administratif", "Cours de Droit public et administratif"),
    (" — Manuel — ", " — Cours — "),
    ("Manuel — Droit", "Cours — Droit"),
    ('<p class="manuel-nav-heading">Manuel</p>', '<p class="manuel-nav-heading">Cours</p>'),
    ('aria-label="Navigation du manuel"', 'aria-label="Navigation du cours"'),
    ('aria-label="Sommaire du manuel"', 'aria-label="Sommaire du cours"'),
    (">Manuel</a>", ">Cours</a>"),
    (">Manuel</strong>", ">Cours</strong>"),
    ('<p class="dict-extra">Manuel :', '<p class="dict-extra">Cours :'),
)


def strip_legacy_crumb(html: str) -> str:
    return _LEGACY_CRUMB.sub("", html, count=1)


def rename_manuel_labels(html: str) -> str:
    for old, new in _MANUEL_LABEL_REPLACEMENTS:
        html = html.replace(old, new)
    return html


def fix_html_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    fixed = rename_manuel_labels(strip_legacy_crumb(text))
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
