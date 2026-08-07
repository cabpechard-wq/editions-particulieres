"""Noms de fichiers horodatés."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


def sanitize_filename(title: str, max_len: int = 120) -> str:
    title = (title or "sans-titre").strip()
    title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title)
    title = re.sub(r"\s+", " ", title).strip(" .")
    return (title or "sans-titre")[:max_len]


def timestamp_prefix(when: datetime | None = None) -> str:
    return (when or datetime.now()).strftime("%Y%m%d%H%M%S")


def stamped_stem(name: str, *, when: datetime | None = None) -> str:
    base = sanitize_filename((name or "").strip() or "Export")
    if len(base) >= 14 and base[:14].isdigit() and (len(base) == 14 or base[14:17] == " - "):
        return base
    return f"{timestamp_prefix(when)} - {base}"


def stamped_path(
    out_dir: Path,
    name: str,
    *,
    ext: str = ".docx",
    when: datetime | None = None,
) -> Path:
    if not ext.startswith("."):
        ext = f".{ext}"
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = stamped_stem(name, when=when)
    candidate = out_dir / f"{stem}{ext}"
    if not candidate.exists():
        return candidate
    n = 2
    while True:
        alt = out_dir / f"{stem}-{n}{ext}"
        if not alt.exists():
            return alt
        n += 1
