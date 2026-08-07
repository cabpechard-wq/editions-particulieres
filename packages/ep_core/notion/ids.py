"""Parse Notion URLs / IDs into UUID form."""

from __future__ import annotations

import re
from urllib.parse import unquote, urlparse

_HEX32 = re.compile(r"([0-9a-fA-F]{32})")
_UUID = re.compile(
    r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
)


def to_uuid(raw: str) -> str:
    """Normalize a Notion id or URL to dashed UUID."""
    s = unquote((raw or "").strip())
    if not s:
        raise ValueError("Identifiant Notion vide")

    m = _UUID.search(s)
    if m:
        return m.group(1).lower()

    m = _HEX32.search(s.replace("-", ""))
    if not m:
        path = urlparse(s).path if "://" in s else s
        compact = re.sub(r"[^0-9a-fA-F]", "", path)
        m = _HEX32.search(compact[-32:] if len(compact) >= 32 else compact)
    if not m:
        raise ValueError(f"Impossible d'extraire un ID Notion depuis : {raw!r}")

    h = m.group(1).lower()
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def page_url_from_id(page_id: str) -> str:
    return f"https://www.notion.so/{page_id.replace('-', '')}"
