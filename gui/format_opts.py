"""Options de format de sortie (Word, HTML)."""

from __future__ import annotations

SUPPORTED_FORMATS = ("docx", "html")
IMPLEMENTED_FORMATS = ("docx", "html")

EXTENSIONS = {
    "docx": ".docx",
    "html": ".html",
}


def ext_for(fmt: str) -> str:
    fmt = (fmt or "docx").lower().strip()
    if fmt not in EXTENSIONS:
        raise ValueError(f"Format inconnu : {fmt!r}")
    return EXTENSIONS[fmt]


def ensure_format(fmt: str) -> str:
    fmt = (fmt or "docx").lower().strip()
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Format inconnu : {fmt!r}. Formats prévus : {', '.join(SUPPORTED_FORMATS)}."
        )
    if fmt not in IMPLEMENTED_FORMATS:
        raise ValueError(
            f"Format « {fmt} » pas encore disponible. "
            f"Pour l'instant : {', '.join(IMPLEMENTED_FORMATS)}."
        )
    return fmt
