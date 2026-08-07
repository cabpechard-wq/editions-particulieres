"""CLI flipcards — rafraîchit Nom/Verso depuis Notion puis génère HTML + JSON."""

from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from pathlib import Path

from .cli_util import ensure_utf8_stdio, normalize_argv
from .export_matrice import OUT_DIR as MATRICES_DIR
from .export_matrice import (
    fetch_matrice_rows_for_export,
    refresh_matrice,
    sort_rows_by_date,
)
from .generator import (
    DEFAULT_MATRICE,
    DEFAULT_PAGE_TITLE,
    FlipcardGenerator,
    sanitize_filename,
)
from .ids import filename_card_row
from .naming import stamped_path

FLIPCARDS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FLIPCARDS_DIR.parent
DEFAULT_OUT = PROJECT_ROOT / "output"

FORMAT_CHOICES = ("both", "html", "json")


def load_matrice(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fp:
        return list(csv.DictReader(fp))


def match_page(rows: list[dict[str, str]], query: str) -> list[dict[str, str]]:
    q = (query or "").strip()
    if not q:
        return rows

    hex32 = re.search(r"([0-9a-fA-F]{32})", q.replace("-", ""))
    uuid = re.search(
        r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})",
        q,
    )
    needle_id = None
    if uuid:
        needle_id = uuid.group(1).lower()
    elif hex32:
        h = hex32.group(1).lower()
        needle_id = f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"

    hits = []
    q_low = q.lower()
    for row in rows:
        rid = (row.get("id") or "").lower()
        if needle_id and rid == needle_id:
            hits.append(row)
            continue
        url = (row.get("url") or "").lower()
        if q_low in url:
            hits.append(row)
            continue
        title = (row.get("title") or row.get("Nom") or "").lower()
        if q_low in title:
            hits.append(row)
            continue
    return hits


def plan_outputs(
    rows: list[dict[str, str]], out_dir: Path, ext: str
) -> list[tuple[dict[str, str], str, Path]]:
    planned: list[tuple[dict[str, str], str, Path]] = []
    for row in rows:
        title = (row.get("Nom") or row.get("title") or "sans-titre").strip()
        safe = filename_card_row(row)
        out_path = stamped_path(out_dir, safe, ext=ext)
        planned.append((row, title, out_path))
    return planned


def _refresh_before_export(matrice: Path) -> Path:
    resolved = matrice.resolve()
    matrices_root = MATRICES_DIR.resolve()
    try:
        resolved.relative_to(matrices_root)
    except ValueError as e:
        raise ValueError(
            f"Rafraîchissement Notion impossible hors de {MATRICES_DIR} "
            f"(matrice={matrice}). Utilise --offline ou -m flipcards/matrices/….csv"
        ) from e

    print(f"Rafraîchissement Notion -> {matrice.name} …")
    return refresh_matrice(stem=matrice.stem)


def _rows_from_notion(*, page: str | None, limit: int | None) -> list[dict[str, str]]:
    print("Rafraîchissement Notion (extrait) …")
    return fetch_matrice_rows_for_export(
        page_query=page,
        limit=limit,
        match_page_fn=match_page,
    )


def _formats(choice: str) -> list[str]:
    if choice == "both":
        return ["html", "json"]
    return [choice]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="flipcards",
        description=(
            "FLIPCARDS JP — rafraîchit Nom/Verso depuis Notion, puis génère "
            "HTML (flip) et/ou JSON mobile.\n"
            "  * 1 fichier combiné (défaut)\n"
            "  * 1 fichier par fiche : --no-combine"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--matrice",
        "-m",
        type=Path,
        default=DEFAULT_MATRICE,
        help=f"CSV source (défaut : {DEFAULT_MATRICE})",
    )
    p.add_argument(
        "--offline",
        action="store_true",
        help="Ne pas appeler Notion : utilise le CSV local tel quel.",
    )
    p.add_argument(
        "--page",
        help="Une fiche : URL, id Notion, ou fragment de titre (ex. Cachet).",
    )
    p.add_argument(
        "--limit",
        type=int,
        metavar="N",
        help="Nombre max de cartes.",
    )
    p.add_argument(
        "--no-combine",
        action="store_true",
        help="Un fichier par fiche (par défaut : un HTML/JSON combiné).",
    )
    p.add_argument(
        "--name",
        "-n",
        help=f"Nom du fichier (sans extension) en mode combiné. Défaut : {DEFAULT_PAGE_TITLE}.",
    )
    p.add_argument(
        "--out",
        "-o",
        type=Path,
        default=None,
        help=f"Dossier de sortie (défaut : {DEFAULT_OUT})",
    )
    p.add_argument(
        "--format",
        default="both",
        choices=list(FORMAT_CHOICES),
        help="Sortie : both (défaut), html, ou json.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    ensure_utf8_stdio()
    argv = normalize_argv(list(argv if argv is not None else sys.argv[1:]))
    args = build_parser().parse_args(argv)

    formats = _formats(args.format)
    combine = not bool(args.no_combine)
    out_dir = args.out or DEFAULT_OUT

    rows: list[dict[str, str]]

    if args.offline:
        if not args.matrice.exists():
            print(f"Erreur : matrice introuvable : {args.matrice}", file=sys.stderr)
            print(
                "Sans --offline, la matrice est rechargée depuis Notion. "
                "Sinon : python -m flipcards.export_matrice",
                file=sys.stderr,
            )
            return 1
        rows = load_matrice(args.matrice)
        if args.page:
            rows = match_page(rows, args.page)
            if not rows:
                print(f"Aucune fiche ne correspond à : {args.page!r}", file=sys.stderr)
                return 1
        rows = sort_rows_by_date(rows)
        if args.limit is not None:
            rows = rows[: max(0, args.limit)]
    else:
        try:
            if args.page or args.limit is not None:
                rows = _rows_from_notion(page=args.page, limit=args.limit)
                if args.page and not rows:
                    print(
                        f"Aucune fiche ne correspond à : {args.page!r}",
                        file=sys.stderr,
                    )
                    return 1
            else:
                args.matrice = _refresh_before_export(args.matrice)
                rows = load_matrice(args.matrice)
            rows = sort_rows_by_date(rows)
        except ValueError as e:
            print(f"Erreur : {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Erreur rafraîchissement Notion : {e}", file=sys.stderr)
            return 1

    if not rows:
        print("Aucune carte à traiter.")
        return 0

    if len(rows) > 1:
        print(f"Tri chronologique (Date, ancien -> recent) : {len(rows)} carte(s)")

    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    gen = FlipcardGenerator()
    written: list[Path] = []

    if combine:
        stem = sanitize_filename(args.name) if args.name else sanitize_filename(DEFAULT_PAGE_TITLE)
        print(f"Mode combiné -> {out_dir}  ({len(rows)} carte(s), {', '.join(formats)})")
        for fmt in formats:
            out_path = stamped_path(out_dir, stem, ext=f".{fmt}")
            try:
                if fmt == "html":
                    gen.convert_many_html(rows, out_path, title=stem)
                else:
                    gen.convert_many_json(rows, out_path)
            except Exception as e:
                print(f"Assemblage {fmt} x {e}", file=sys.stderr)
                return 1
            written.append(out_path)
            print(f"  -> {out_path.name}")
    else:
        print(
            f"Mode 1 fichier/carte -> {out_dir}  "
            f"({len(rows)} carte(s), {', '.join(formats)})"
        )
        ok = 0
        errors = 0
        for fmt in formats:
            planned = plan_outputs(rows, out_dir, f".{fmt}")
            total = len(planned)
            for i, (row, title, out_path) in enumerate(planned, 1):
                try:
                    if fmt == "html":
                        gen.convert_row_html(row, out_path)
                    else:
                        gen.convert_row_json(row, out_path)
                    written.append(out_path)
                    print(f"[{fmt} {i}/{total}] {title} -> {out_path.name}")
                    ok += 1
                except Exception as e:
                    errors += 1
                    print(f"[{fmt} {i}/{total}] {title} x {e}", file=sys.stderr)
        if errors and not ok:
            return 1

    elapsed = time.perf_counter() - t0
    print(
        f"Terminé : {len(rows)} carte(s), {len(written)} fichier(s), "
        f"{elapsed:.1f}s, sortie : {out_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
