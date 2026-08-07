"""Numérotation hiérarchique des titres Notion (1. 1.1. 1.1.1. …)."""

from __future__ import annotations

from typing import Any

# Notion heading_1..3 → Word Heading 2..4 ; heading_4+ sans numéro
MAX_NUMBERED_HEADING_LEVEL = 3


class HeadingNumbering:
    """Compteurs pour ``heading_1`` … ``heading_3`` uniquement."""

    def __init__(self) -> None:
        self._counters = [0] * MAX_NUMBERED_HEADING_LEVEL

    def reset(self) -> None:
        self._counters = [0] * MAX_NUMBERED_HEADING_LEVEL

    def next(self, notion_level: int) -> str:
        """
        ``notion_level`` : 1..3 (``heading_1`` … ``heading_3``).

        Retourne un préfixe textuel du type « 1. », « 1.2. », « 1.2.3. ».
        """
        lvl = max(1, min(MAX_NUMBERED_HEADING_LEVEL, int(notion_level)))
        idx = lvl - 1
        for i in range(idx):
            if self._counters[i] == 0:
                self._counters[i] = 1
        self._counters[idx] += 1
        for i in range(idx + 1, MAX_NUMBERED_HEADING_LEVEL):
            self._counters[i] = 0
        parts = [str(self._counters[i]) for i in range(idx + 1)]
        return ".".join(parts) + ". "


def prefix_rich_text(
    rich_texts: list[dict[str, Any]], prefix: str
) -> list[dict[str, Any]]:
    """Préfixe textuel (numérotation) avant le rich text Notion d'un titre."""
    if not prefix:
        return list(rich_texts or [])
    head: dict[str, Any] = {
        "type": "text",
        "plain_text": prefix,
        "href": None,
        "annotations": {
            "bold": False,
            "italic": False,
            "underline": False,
            "strikethrough": False,
            "code": False,
            "color": "default",
        },
        "text": {"content": prefix, "link": None},
    }
    return [head, *(rich_texts or [])]
