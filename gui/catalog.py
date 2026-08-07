"""Catalogue des fiches d'un registre (libellés pour listbox GUI)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packages.ep_core.notion import page_title
from packages.ep_core.paths import resolve_path
from packages.ep_core.registers import REGISTRE_LABELS, database_url_for_registre

from extract.pull._common import make_fetcher

REF_PROP = "Référence"
_ALNUM = re.compile(r"(\d+)")
_DATE_PREFIX = re.compile(r"^(\d{4}-\d{2}-\d{2})")


@dataclass(frozen=True)
class FicheEntry:
    id: str
    label: str


def _alnum_key(s: str) -> list:
    parts = _ALNUM.split((s or "").strip())
    key: list = []
    for p in parts:
        if not p:
            continue
        if p.isdigit():
            key.append((0, int(p)))
        else:
            key.append((1, p.casefold()))
    return key


def _page_reference(page: dict[str, Any]) -> str:
    props = page.get("properties") or {}
    lower = {k.lower(): k for k in props}
    for name in ("référence", "reference"):
        key = lower.get(name)
        if not key:
            continue
        prop = props[key]
        t = prop.get("type")
        val = prop.get(t)
        if t == "title":
            return "".join(x.get("plain_text", "") for x in (val or [])).strip()
        if t in {"rich_text", "text"}:
            return "".join(x.get("plain_text", "") for x in (val or [])).strip()
        if t in {"select", "status"}:
            return ((val or {}).get("name") or "").strip()
        if isinstance(val, str):
            return val.strip()
    return ""


def _sort_pages_by_reference(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(page: dict[str, Any]) -> tuple:
        ref = _page_reference(page)
        title = page_title(page).casefold()
        return (0 if ref else 1, _alnum_key(ref), _alnum_key(title))

    return sorted(pages, key=key)


def list_fiches(registre: str, *, offline_arrets: bool = True) -> list[FicheEntry]:
    if registre == "arrets":
        return _list_arrets(offline=offline_arrets)
    db = database_url_for_registre(registre)
    fetcher = make_fetcher()
    pages = list(fetcher.iter_database_pages(db))
    pages = _sort_pages_by_reference(pages)
    entries: list[FicheEntry] = []
    for page in pages:
        pid = page["id"]
        title = page_title(page) or pid[:8]
        ref = _page_reference(page)
        label = f"{ref} — {title}" if ref else title
        entries.append(FicheEntry(id=pid, label=label))
    return entries


def _jurisprudence_json_path() -> Path:
    return resolve_path("matrices_jurisprudence") / "jurisprudence.json"


def _list_arrets(*, offline: bool) -> list[FicheEntry]:
    json_path = _jurisprudence_json_path()
    if not offline or not json_path.is_file():
        from extract.pull.jurisprudence import export_jurisprudence

        export_jurisprudence(output=json_path)

    data = json.loads(json_path.read_text(encoding="utf-8"))
    pages = data.get("pages") or []
    entries: list[FicheEntry] = []

    def sort_key(page: dict[str, Any]) -> tuple:
        props = page.get("properties") or {}
        raw = props.get("Date")
        if isinstance(raw, dict):
            d = (raw.get("start") or "").strip()[:10]
        else:
            d = str(raw or "").strip()[:10]
            if "→" in d:
                d = d.split("→", 1)[0].strip()
        m = _DATE_PREFIX.match(d)
        date = m.group(1) if m else "9999-99-99"
        title = (page.get("title") or "").casefold()
        return (date, title)

    for page in sorted(pages, key=sort_key):
        pid = (page.get("id") or "").strip()
        nom = (page.get("title") or "sans-titre").strip()
        props = page.get("properties") or {}
        raw_date = props.get("Date")
        if isinstance(raw_date, dict):
            date = (raw_date.get("start") or "").strip()[:10]
        else:
            date = str(raw_date or "").strip()[:10]
        label = f"{date} — {nom}" if date else nom
        entries.append(FicheEntry(id=pid or nom, label=label))
    return entries


__all__ = ["FicheEntry", "REGISTRE_LABELS", "list_fiches"]
