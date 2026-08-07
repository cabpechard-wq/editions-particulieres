"""Export local des flipcards (Nom + Verso) depuis la base Jurisprudence.

Usage (depuis la racine du projet) :
  python -m flipcards.export_matrice
  python -m flipcards.export_matrice --limit 10
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

FLIPCARDS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FLIPCARDS_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flipcards.notion_api import (  # noqa: E402
    NotionFetcher,
    make_notion_fetcher,
    page_title,
    property_plain,
)

OUT_DIR = FLIPCARDS_DIR / "matrices"
COLORS_PATH = OUT_DIR / "classifier_colors.json"
DEFAULT_DB_URL = "https://app.notion.com/p/39ba29ad9f7880229765cbea38ae793a"
DB_URL = os.getenv("NOTION_ARRETS_DATABASE_ID") or DEFAULT_DB_URL
DATE_PROP = "Date"
DATE_SORTS = [{"property": DATE_PROP, "direction": "ascending"}]

CORE_PROPS = ("Nom", "Verso")
# Classificateurs (filtres d'étude) + méta utiles
CLASSIFIER_PROPS = ("Thème", "Notions")
META_PROPS = (
    "Date",
    "Juridiction",
    "Formation de jugement",
    "Titre de la décision",
    "Référence",
    "Importance",
    "Thème",
    "Notions",
    "Objet",
    "Portée",
    "Considérant de principe",
)
# Rubriques de fiche d'arrêt (propriétés Notion ; repli JSON local si vide)
FICHE_KEYS = ("Faits", "Enjeu juridique", "Solution", "Perspective")
FICHE_PROP_ALIASES: dict[str, tuple[str, ...]] = {
    "Faits": ("Faits",),
    "Enjeu juridique": ("Enjeu juridique", "Enjeu"),
    "Solution": ("Solution",),
    "Perspective": ("Perspective", "Perspectives"),
}
EXPORT_PROPS = CORE_PROPS + META_PROPS
EXPORT_FIELDNAMES = ("id", "title", "url", *EXPORT_PROPS, *FICHE_KEYS)

_DATE_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")
_THEME_PREFIX_RE = re.compile(r"^\d+\s*[-–—]\s*(.+)$")


def format_theme_label(raw: str) -> str:
    bit = (raw or "").strip()
    if not bit:
        return ""
    m = _THEME_PREFIX_RE.match(bit)
    return m.group(1).strip() if m else bit


def fetch_classifier_colors(fetcher: NotionFetcher) -> dict[str, dict[str, str]]:
    """Couleurs Notion des options Thème (select) et Notions (multi_select)."""
    ds_id = fetcher.resolve_data_source_id(DB_URL)
    ds = fetcher.client.data_sources.retrieve(data_source_id=ds_id)
    fetcher._pause()
    props = ds.get("properties") or {}

    themes: dict[str, str] = {}
    notions: dict[str, str] = {}

    theme_prop = props.get("Thème") or {}
    theme_type = theme_prop.get("type") or ""
    theme_opts = (theme_prop.get(theme_type) or {}).get("options") or []
    for opt in theme_opts:
        name = (opt.get("name") or "").strip()
        color = (opt.get("color") or "default").strip() or "default"
        if not name:
            continue
        themes[name] = color
        label = format_theme_label(name)
        if label:
            themes[label] = color

    notions_prop = props.get("Notions") or {}
    notions_type = notions_prop.get("type") or ""
    notions_opts = (notions_prop.get(notions_type) or {}).get("options") or []
    for opt in notions_opts:
        name = (opt.get("name") or "").strip()
        color = (opt.get("color") or "default").strip() or "default"
        if name:
            notions[name] = color

    return {"themes": themes, "notions": notions}


def load_classifier_colors() -> dict[str, dict[str, str]]:
    if not COLORS_PATH.exists():
        return {"themes": {}, "notions": {}}
    try:
        data = json.loads(COLORS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"themes": {}, "notions": {}}
    return {
        "themes": dict(data.get("themes") or {}),
        "notions": dict(data.get("notions") or {}),
    }


def write_classifier_colors(colors: dict[str, dict[str, str]]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "database_url": DB_URL,
        "themes": colors.get("themes") or {},
        "notions": colors.get("notions") or {},
    }
    COLORS_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Écrit : {COLORS_PATH}")
    print(f"  thèmes colorés : {len(payload['themes'])}")
    print(f"  notions colorées : {len(payload['notions'])}")
    return COLORS_PATH


def parse_row_date(value: str) -> str | None:
    raw = (value or "").strip()
    if "→" in raw:
        raw = raw.split("→", 1)[0].strip()
    m = _DATE_PREFIX_RE.match(raw)
    return m.group(1) if m else None


def sort_rows_by_date(rows: list[dict]) -> list[dict]:
    def key(row: dict) -> tuple:
        d = parse_row_date(str(row.get(DATE_PROP) or ""))
        title = (row.get("Nom") or row.get("title") or "").casefold()
        if d:
            return (0, d, title)
        return (1, "9999-99-99", title)

    return sorted(rows, key=key)


def make_client(token: str) -> NotionFetcher:
    return make_notion_fetcher(token, pause_s=0.12)


def ensure_token(token: str | None = None) -> str:
    load_dotenv(PROJECT_ROOT / ".env")
    tok = token or os.getenv("NOTION_TOKEN")
    if not tok:
        raise ValueError("NOTION_TOKEN manquant (définis-le dans .env)")
    return tok


def _prop_by_names(props: dict, *names: str) -> str:
    """Lit une propriété Notion en testant plusieurs libellés (insensible à la casse)."""
    lower = {k.casefold(): k for k in props}
    for name in names:
        key = lower.get(name.casefold())
        if key:
            return property_plain(props[key]).strip()
    return ""


def _fiche_value(props: dict, canonical: str) -> str:
    return _prop_by_names(props, *FICHE_PROP_ALIASES.get(canonical, (canonical,)))


def _row_from_page(page: dict) -> dict[str, str]:
    props = page.get("properties") or {}
    row: dict[str, str] = {
        "id": page["id"],
        "title": page_title(page),
        "url": page.get("url") or "",
    }
    for name in EXPORT_PROPS:
        row[name] = property_plain(props[name]) if name in props else ""
    for name in FICHE_KEYS:
        row[name] = _fiche_value(props, name)
    if not (row.get("Nom") or "").strip():
        row["Nom"] = row.get("title") or ""
    return row


def _load_existing_fiche_bodies(stem: str) -> dict[str, dict[str, str]]:
    """Repli : conserve les rubriques déjà exportées (ancien corps de page → JSON local)."""
    path = OUT_DIR / f"{stem}.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    pages = data.get("pages")
    if not isinstance(pages, list):
        return {}
    out: dict[str, dict[str, str]] = {}
    for row in pages:
        if not isinstance(row, dict):
            continue
        pid = (row.get("id") or "").strip()
        if not pid:
            continue
        out[pid] = {k: (row.get(k) or "") for k in FICHE_KEYS}
    return out


def _merge_fiche_bodies(rows: list[dict[str, str]], stem: str) -> None:
    existing = _load_existing_fiche_bodies(stem)
    if not existing:
        return
    for row in rows:
        prev = existing.get((row.get("id") or "").strip())
        if not prev:
            continue
        for k in FICHE_KEYS:
            if not (row.get(k) or "").strip() and (prev.get(k) or "").strip():
                row[k] = prev[k]


def export_properties(
    fetcher: NotionFetcher, limit: int | None = None
) -> list[dict[str, str]]:
    pages = list(
        fetcher.iter_database_pages(
            DB_URL,
            limit=limit,
            sorts=DATE_SORTS,
        )
    )
    return sort_rows_by_date([_row_from_page(p) for p in pages])


def fetch_matrice_rows(
    *,
    limit: int | None = None,
    token: str | None = None,
) -> list[dict[str, str]]:
    fetcher = make_client(ensure_token(token))
    print("Export Nom / Verso (+ méta)…")
    rows = export_properties(fetcher, limit=limit)
    print(f"   {len(rows)} pages")
    return rows


def fetch_matrice_rows_for_export(
    *,
    page_query: str | None = None,
    limit: int | None = None,
    match_page_fn=None,
    token: str | None = None,
) -> list[dict[str, str]]:
    fetcher = make_client(ensure_token(token))
    prop_limit = None if page_query else limit

    print("Export Nom / Verso (+ méta)…")
    rows = export_properties(fetcher, limit=prop_limit)
    print(f"   {len(rows)} pages (scan)")

    if page_query:
        if match_page_fn is None:
            raise ValueError("match_page_fn requis avec page_query")
        rows = match_page_fn(rows, page_query)
        if not rows:
            return []
        print(f"   -> {len(rows)} fiche(s) après filtre --page")

    rows = sort_rows_by_date(rows)
    if limit is not None:
        rows = rows[: max(0, limit)]
    return rows


def write_outputs(
    rows: list[dict],
    stem: str,
    *,
    colors: dict[str, dict[str, str]] | None = None,
) -> Path:
    rows = sort_rows_by_date(rows)
    _merge_fiche_bodies(rows, stem)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = list(EXPORT_FIELDNAMES)

    csv_path = OUT_DIR / f"{stem}.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    if colors is None:
        colors = load_classifier_colors()
    else:
        write_classifier_colors(colors)

    json_path = OUT_DIR / f"{stem}.json"
    json_path.write_text(
        json.dumps(
            {
                "database": "Jurisprudence",
                "database_url": DB_URL,
                "kind": "flipcards",
                "count": len(rows),
                "properties": list(EXPORT_PROPS),
                "fiche_properties": list(FICHE_KEYS),
                "classifiers": list(CLASSIFIER_PROPS),
                "classifier_colors": colors,
                "pages": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    n = len(rows)
    print(f"\nÉcrit : {csv_path}")
    print(f"Écrit : {json_path}")
    for name in EXPORT_PROPS:
        filled = sum(1 for r in rows if (r.get(name) or "").strip())
        print(f"  {name}: {filled}/{n}")
    for name in FICHE_KEYS:
        filled = sum(1 for r in rows if (r.get(name) or "").strip())
        print(f"  fiche {name}: {filled}/{n}")
    return csv_path


def refresh_matrice(
    *,
    stem: str = "flipcards_matrice",
    limit: int | None = None,
    token: str | None = None,
) -> Path:
    fetcher = make_client(ensure_token(token))
    print("Export Nom / Verso (+ méta)…")
    rows = export_properties(fetcher, limit=limit)
    print(f"   {len(rows)} pages")
    print("Couleurs Thème / Notions…")
    colors = fetch_classifier_colors(fetcher)
    return write_outputs(rows, stem, colors=colors)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export flipcards Jurisprudence (Nom/Verso) → CSV/JSON"
    )
    parser.add_argument("--limit", type=int, help="Limiter le nombre de pages")
    parser.add_argument(
        "--stem",
        default="flipcards_matrice",
        help="Nom de fichier sans extension",
    )
    args = parser.parse_args(argv)

    try:
        refresh_matrice(stem=args.stem, limit=args.limit)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
